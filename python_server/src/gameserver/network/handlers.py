"""Message handlers — central registry of all message type handlers.

Each handler is an async function that receives a parsed GameMessage
and the sender UID, and returns an optional response dict.

This module is the single place where handler logic lives. To add
a new message handler:

1. Write the handler function below (grouped by category).
2. Register it in :func:`register_all_handlers` at the bottom.

The handler signature is::

    async def handle_xyz(message: GameMessage, sender_uid: int) -> dict | None:
        ...

Returning a dict sends it back to the sender as a JSON response.
Returning None means no response to the sender (fire-and-forget).
"""

from __future__ import annotations

import logging
import time
import asyncio
from collections import deque
from typing import Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from gameserver.main import Services

from gameserver.models.messages import GameMessage, MapSaveRequest
from gameserver.models.attack import AttackPhase, Attack

log = logging.getLogger(__name__)

# ===================================================================
# Global counters
# ===================================================================

_next_cid: int = 1  # Critter ID counter
_next_wid: int = 1  # Wave ID counter

# Module-level reference set by register_all_handlers()
_services: Optional[Services] = None


def _svc() -> Services:
    """Get the Services container. Raises if not initialized."""
    assert _services is not None, "handlers: services not initialized"
    return _services


# ===================================================================
# Connection / Keepalive
# ===================================================================

async def handle_ping(message: GameMessage, sender_uid: int) -> dict:
    """Simple ping handler to keep connections alive.
    
    iOS Safari and other mobile browsers can aggressively close
    inactive WebSocket connections. This handler allows clients
    to send a keepalive ping.
    """
    log.info("Ping received from uid=%d", sender_uid)
    return {"type": "pong", "timestamp": time.time()}


# ===================================================================
# Map validation helpers
# ===================================================================

def _has_path_from_spawn_to_castle(tiles: dict[str, str]) -> bool:
    """Check if there's a path from any spawnpoint to the castle.
    
    Uses the centralized pathfinding logic from hex_pathfinding module.
    
    Args:
        tiles: Dict of {"q,r": "tile_type"} where tile_type is 'castle', 'spawnpoint', etc.
    
    Returns:
        True if at least one path exists, False otherwise.
    """
    from gameserver.engine.hex_pathfinding import find_path_from_spawn_to_castle
    return find_path_from_spawn_to_castle(tiles) is not None


# ===================================================================
# Empire queries
# ===================================================================

async def handle_summary_request(
    message: GameMessage, sender_uid: int,
) -> Optional[dict[str, Any]]:
    """Handle ``summary_request`` — return full empire overview.

    Equivalent to the Java ``SummaryRequest`` → ``SummaryResponse`` flow
    that passes through the GameEngine.

    The response contains resources, citizens, buildings, research,
    structures, effects, artefacts, and life status.
    """
    svc = _svc()
    # Use sender_uid from the authenticated session.
    # For unauthenticated (guest) connections, fall back to the
    # ``sender`` field in the message — this allows debug / test access.
    # Once auth is fully implemented, only sender_uid should be trusted.
    target_uid = sender_uid if sender_uid > 0 else message.sender
    empire = svc.empire_service.get(target_uid)
    if empire is None:
        return {
            "type": "summary_response",
            "error": f"No empire found for uid {target_uid}",
        }

    return _build_empire_summary(empire, target_uid)


async def handle_item_request(
    message: GameMessage, sender_uid: int,
) -> Optional[dict[str, Any]]:
    """Handle ``item_request`` — return available buildings, research & structures.

    Returns all buildings/knowledge/structures whose prerequisites are satisfied
    by the empire's completed items.
    """
    svc = _svc()
    target_uid = sender_uid if sender_uid > 0 else message.sender
    empire = svc.empire_service.get(target_uid)
    if empire is None:
        return {
            "type": "item_response",
            "buildings": {},
            "knowledge": {},
            "structures": {},
        }

    # Completed items = buildings done + knowledge done + artefacts owned
    completed: set[str] = set()
    for iid, remaining in empire.buildings.items():
        if remaining <= 0:
            completed.add(iid)
    for iid, remaining in empire.knowledge.items():
        if remaining <= 0:
            completed.add(iid)
    completed.update(empire.artefacts)

    from gameserver.models.items import ItemType
    up = svc.upgrade_provider

    buildings = {}
    for item in up.available_items(ItemType.BUILDING, completed):
        buildings[item.iid] = {
            "name": item.name,
            "description": item.description,
            "effort": item.effort,
            "costs": dict(item.costs),
            "requirements": list(item.requirements),
            "effects": dict(item.effects),
        }

    knowledge = {}
    for item in up.available_items(ItemType.KNOWLEDGE, completed):
        knowledge[item.iid] = {
            "name": item.name,
            "description": item.description,
            "effort": item.effort,
            "costs": dict(item.costs),
            "requirements": list(item.requirements),
            "effects": dict(item.effects),
        }

    # Structures (towers) — available based on research
    structures = {}
    for item in up.available_items(ItemType.STRUCTURE, completed):
        structures[item.iid] = {
            "name": item.name,
            "description": item.description,
            "damage": item.damage,
            "range": item.range,
            "reload_time_ms": item.reload_time_ms,
            "shot_speed": item.shot_speed,
            "shot_type": item.shot_type,
            "sprite": item.sprite,
            "requirements": list(item.requirements),
            "effects": dict(item.effects),
        }

    # Critters — available based on research
    critters = {}
    for item in up.available_items(ItemType.CRITTER, completed):
        critters[item.iid] = {
            "name": item.name,
            "requirements": list(item.requirements),
        }

    return {
        "type": "item_response",
        "buildings": buildings,
        "knowledge": knowledge,
        "structures": structures,
        "critters": critters,
    }


async def handle_military_request(
    message: GameMessage, sender_uid: int,
) -> Optional[dict[str, Any]]:
    """Handle ``military_request`` — return armies and attack status.
    
    Can query own armies or another empire's armies (for debug/testing).
    Use ``uid`` parameter to specify a different empire, or defaults to sender_uid.
    """
    svc = _svc()
    # Allow override via message.uid for debug/test access
    target_uid = sender_uid if sender_uid > 0 else getattr(message, "uid", 0) or 0
    empire = svc.empire_service.get(target_uid)
    if empire is None:
        return {
            "type": "military_response",
            "error": f"No empire found for uid {target_uid}",
        }

    armies = []
    for army in empire.armies:
        # Build waves list with details
        waves = []
        for wave in army.waves:
            waves.append({
                "wave_id": wave.wave_id,
                "iid": wave.iid,
                "slots": wave.slots,
            })
        
        armies.append({
            "aid": army.aid,
            "name": army.name,
            "waves": waves,
        })

    # Get available critters based on completed research
    completed: set[str] = set()
    for iid, remaining in empire.knowledge.items():
        if remaining <= 0:
            completed.add(iid)
    
    available_critters = []
    for critter in svc.upgrade_provider.available_critters(completed):
        available_critters.append({
            "iid": critter.iid,
            "name": critter.name,
        })

    # Ongoing attacks
    def _attack_dto(a):
        return {
            "attack_id": a.attack_id,
            "attacker_uid": a.attacker_uid,
            "defender_uid": a.defender_uid,
            "army_aid": a.army_aid,
            "phase": a.phase.value,
            "eta_seconds": round(a.eta_seconds, 1),
            "total_eta_seconds": round(a.total_eta_seconds, 1),
            "siege_remaining_seconds": round(a.siege_remaining_seconds, 1),
            "total_siege_seconds": round(a.total_siege_seconds, 1),
        }

    incoming = [_attack_dto(a) for a in svc.attack_service.get_incoming(target_uid)]
    outgoing = [_attack_dto(a) for a in svc.attack_service.get_outgoing(target_uid)]

    return {
        "type": "military_response",
        "armies": armies,
        "attacks_incoming": incoming,
        "attacks_outgoing": outgoing,
        "available_critters": available_critters,
    }


# ===================================================================
# Building / Research
# ===================================================================

async def handle_new_item(
    message: GameMessage, sender_uid: int,
) -> Optional[dict[str, Any]]:
    """Handle ``new_item`` — start building or researching an item.
    
    Sends push notification (build_response) to client without request_id.
    Returns build_queue and research_queue so UI can update immediately.
    """
    svc = _svc()
    iid = getattr(message, "iid", "")
    target_uid = sender_uid if sender_uid > 0 else message.sender
    empire = svc.empire_service.get(target_uid)
    if empire is None:
        return {
            "type": "build_response",
            "success": False,
            "iid": iid,
            "error": "No empire found",
            "build_queue": "",
            "research_queue": "",
        }

    error = svc.empire_service.build_item(empire, iid)
    if error:
        log.info("new_item failed uid=%d iid=%s: %s", target_uid, iid, error)
        return {
            "type": "build_response",
            "success": False,
            "iid": iid,
            "error": error,
            "build_queue": empire.build_queue,
            "research_queue": empire.research_queue,
        }

    log.info("new_item success uid=%d iid=%s", target_uid, iid)
    return {
        "type": "build_response",
        "success": True,
        "iid": iid,
        "error": "",
        "build_queue": empire.build_queue,
        "research_queue": empire.research_queue,
    }


async def handle_new_structure(
    message: GameMessage, sender_uid: int,
) -> Optional[dict[str, Any]]:
    """Handle ``new_structure`` — place a tower on the map.

    TODO: Implement in EmpireService.place_structure().
    """
    log.info("new_structure from uid=%d (not yet implemented)", sender_uid)
    return None


async def handle_delete_structure(
    message: GameMessage, sender_uid: int,
) -> Optional[dict[str, Any]]:
    """Handle ``delete_structure`` — remove a tower from the map.

    TODO: Implement in EmpireService.remove_structure().
    """
    log.info("delete_structure from uid=%d (not yet implemented)", sender_uid)
    return None


# ===================================================================
# Citizens
# ===================================================================

async def handle_citizen_upgrade(
    message: GameMessage, sender_uid: int,
) -> Optional[dict[str, Any]]:
    """Handle ``citizen_upgrade`` — add one citizen.
    
    Sends push notification (citizen_upgrade_response) to client without request_id.
    """
    svc = _svc()
    log.info("citizen_upgrade request from uid=%d", sender_uid)
    empire = svc.empire_service.get(sender_uid)
    if empire is None:
        log.warning("citizen_upgrade failed: no empire found for uid=%d", sender_uid)
        return {
            "type": "citizen_upgrade_response",
            "success": False,
            "error": "Empire not found",
        }
    error = svc.empire_service.upgrade_citizen(empire)
    if error:
        log.info("citizen_upgrade failed uid=%d: %s", sender_uid, error)
        return {
            "type": "citizen_upgrade_response",
            "success": False,
            "error": error,
        }
    log.info("citizen_upgrade success uid=%d", sender_uid)
    return {
        "type": "citizen_upgrade_response",
        "success": True,
        "citizens": dict(empire.citizens),
    }


async def handle_change_citizen(
    message: GameMessage, sender_uid: int,
) -> Optional[dict[str, Any]]:
    """Handle ``change_citizen`` — redistribute citizens among roles.
    
    Sends push notification (change_citizen_response) to client without request_id.
    """
    svc = _svc()
    log.info("change_citizen request from uid=%d", sender_uid)
    empire = svc.empire_service.get(sender_uid)
    if empire is None:
        log.warning("change_citizen failed: no empire found for uid=%d", sender_uid)
        return {
            "type": "change_citizen_response",
            "success": False,
            "error": "Empire not found",
        }
    
    citizens = getattr(message, "citizens", {})
    error = svc.empire_service.change_citizens(empire, citizens)
    if error:
        log.info("change_citizen failed uid=%d: %s", sender_uid, error)
        return {
            "type": "change_citizen_response",
            "success": False,
            "error": error,
        }
    
    log.info("change_citizen success uid=%d: %s", sender_uid, citizens)
    return {
        "type": "change_citizen_response",
        "success": True,
        "citizens": dict(empire.citizens),
    }


# ===================================================================
# Military / Army
# ===================================================================

async def handle_new_army(
    message: GameMessage, sender_uid: int,
) -> Optional[dict[str, Any]]:
    """Handle ``new_army`` — create a new army.
    
    Creates a new Army with no waves and adds it to the empire.
    """
    from gameserver.models.army import Army
    
    svc = _svc()
    name = getattr(message, "name", "").strip()
    target_uid = sender_uid if sender_uid > 0 else message.sender
    empire = svc.empire_service.get(target_uid)
    
    if empire is None:
        log.warning("new_army failed: no empire found for uid=%d", target_uid)
        return {
            "type": "new_army_response",
            "success": False,
            "error": "No empire found",
        }
    
    if not name:
        log.info("new_army failed uid=%d: name is empty", target_uid)
        return {
            "type": "new_army_response",
            "success": False,
            "error": "Army name cannot be empty",
        }
    
    # Calculate cost based on number of existing armies
    army_count = len(empire.armies)
    army_price = svc.empire_service._army_price(army_count + 1)
    
    # Check if player has enough gold
    current_gold = empire.resources.get('gold', 0.0)
    if current_gold < army_price:
        return {
            "type": "new_army_response",
            "success": False,
            "error": f"Not enough gold (need {army_price:.1f}, have {current_gold:.1f})",
        }
    
    # Deduct gold
    empire.resources['gold'] -= army_price
    
    # Find next available army ID
    max_aid = max([a.aid for a in empire.armies], default=0)
    new_aid = max_aid + 1
    
    # Create new army with no waves
    new_army = Army(
        aid=new_aid,
        uid=target_uid,
        name=name,
        waves=[],
    )
    
    # Add to empire
    empire.armies.append(new_army)
    
    log.info("new_army success uid=%d aid=%d name=%s for %.1f gold", target_uid, new_aid, name, army_price)
    return {
        "type": "new_army_response",
        "success": True,
        "aid": new_aid,
        "name": name,
        "cost": round(army_price, 2),
    }


async def handle_new_attack(
    message: GameMessage, sender_uid: int,
) -> Optional[dict[str, Any]]:
    """Handle ``new_attack_request`` — launch an attack.

    Resolves the defender by ``target_uid`` (direct UID) or
    ``opponent_name`` (empire name lookup, legacy).  Validates army,
    deducts no gold yet, and creates the Attack via AttackService.
    """
    svc = _svc()
    target_uid = sender_uid if sender_uid > 0 else message.sender

    # Resolve defender: prefer target_uid, fall back to opponent_name for legacy
    defender_uid_raw = getattr(message, "target_uid", 0) or 0
    opponent_name = getattr(message, "opponent_name", "") or ""
    army_aid = getattr(message, "army_aid", 0) or 0

    log.debug("[new_attack] uid=%d target_uid=%r opponent_name=%r army_aid=%r",
              target_uid, defender_uid_raw, opponent_name, army_aid)

    if defender_uid_raw:
        defender_uid = defender_uid_raw
    elif opponent_name.strip():
        defender = svc.empire_service.find_by_name(opponent_name.strip())
        if defender is None:
            available_empires = [e.name for e in svc.empire_service.all_empires.values()]
            log.warning("[new_attack] FAIL uid=%d: empire %r not found (available: %s)",
                     target_uid, opponent_name, available_empires)
            return {
                "type": "attack_response",
                "success": False,
                "error": f"Empire '{opponent_name.strip()}' not found",
                "_debug": f"Available empires: {available_empires}",
            }
        defender_uid = defender.uid
    else:
        log.warning("[new_attack] FAIL uid=%d: No target (target_uid=%d, opponent_name=%r, army_aid=%d)",
                    target_uid, defender_uid_raw, opponent_name, army_aid)
        return {
            "type": "attack_response",
            "success": False,
            "error": "No target specified (provide target_uid or opponent_name)",
            "_debug": f"Input: target_uid={defender_uid_raw}, opponent_name={opponent_name!r}, army_aid={army_aid}",
        }

    result = svc.attack_service.start_attack(
        attacker_uid=target_uid,
        defender_uid=defender_uid,
        army_aid=army_aid,
        empire_service=svc.empire_service,
    )

    if isinstance(result, str):
        log.warning("[new_attack] FAIL uid=%d: %s", target_uid, result)
        return {
            "type": "attack_response",
            "success": False,
            "error": result,
            "_debug": f"start_attack validation failed (attacker={target_uid}, defender={defender_uid}, army={army_aid})",
        }

    # result is an Attack object
    log.info("[new_attack] SUCCESS uid=%d → defender=%d army=%d attack_id=%d ETA=%.1fs total=%.1fs",
             target_uid, defender_uid, army_aid, result.attack_id, result.eta_seconds, result.total_eta_seconds)
    return {
        "type": "attack_response",
        "success": True,
        "attack_id": result.attack_id,
        "defender_uid": defender_uid,
        "attacker_uid": target_uid,
        "army_aid": army_aid,
        "eta_seconds": round(result.eta_seconds, 1),
        "total_eta_seconds": round(result.total_eta_seconds, 1),
        "total_siege_seconds": round(result.total_siege_seconds, 1),
        "_debug": f"Attack {result.attack_id} created: {target_uid}→{defender_uid} (army {army_aid}, phase={result.phase.value})",
    }


async def handle_change_army(
    message: GameMessage, sender_uid: int,
) -> Optional[dict[str, Any]]:
    """Handle ``change_army`` — rename an army.
    
    Updates the name of an existing army owned by the sender.
    """
    svc = _svc()
    aid = getattr(message, "aid", 0)
    name = getattr(message, "name", "").strip()
    target_uid = sender_uid if sender_uid > 0 else message.sender
    empire = svc.empire_service.get(target_uid)
    
    if empire is None:
        log.warning("change_army failed: no empire found for uid=%d", target_uid)
        return {
            "type": "change_army_response",
            "success": False,
            "error": "No empire found",
        }
    
    # Find the army by aid
    army = None
    for a in empire.armies:
        if a.aid == aid:
            army = a
            break
    
    if army is None:
        log.warning("change_army failed uid=%d: army aid=%d not found", target_uid, aid)
        return {
            "type": "change_army_response",
            "success": False,
            "error": f"Army {aid} not found",
        }
    
    if not name:
        log.info("change_army failed uid=%d aid=%d: name is empty", target_uid, aid)
        return {
            "type": "change_army_response",
            "success": False,
            "error": "Army name cannot be empty",
        }
    
    # Update the name
    old_name = army.name
    army.name = name
    
    log.info("change_army success uid=%d aid=%d: '%s' → '%s'", target_uid, aid, old_name, name)
    return {
        "type": "change_army_response",
        "success": True,
        "aid": aid,
        "name": name,
    }


async def handle_new_wave(
    message: GameMessage, sender_uid: int,
) -> Optional[dict[str, Any]]:
    """Handle ``new_wave`` — add a critter wave to an army.
    
    Creates a new wave with SLAVE critters (5 slots).
    The server always decides the critter type.
    """
    from gameserver.models.army import CritterWave
    
    svc = _svc()
    aid = getattr(message, "aid", 0)
    target_uid = sender_uid if sender_uid > 0 else message.sender
    empire = svc.empire_service.get(target_uid)
    
    if empire is None:
        log.warning("new_wave failed: no empire found for uid=%d", target_uid)
        return {
            "type": "new_wave_response",
            "success": False,
            "error": "No empire found",
        }
    
    # Find the army by aid
    army = None
    for a in empire.armies:
        if a.aid == aid:
            army = a
            break
    
    if army is None:
        log.warning("new_wave failed uid=%d: army aid=%d not found", target_uid, aid)
        return {
            "type": "new_wave_response",
            "success": False,
            "error": f"Army {aid} not found",
        }
    
    # Create new wave with iid and slots (no concrete critters)
    global _next_wid
    new_wave = CritterWave(
        wave_id=_next_wid,
        iid="SLAVE",
        slots=1,
    )
    _next_wid += 1
    
    # Add to army
    army.waves.append(new_wave)
    
    log.info("new_wave success uid=%d aid=%d wave_id=%d with 1 SLAVE slot", target_uid, aid, new_wave.wave_id)
    return {
        "type": "new_wave_response",
        "success": True,
        "aid": aid,
        "wave_id": new_wave.wave_id,
        "critter_iid": new_wave.iid,
        "slots": new_wave.slots,
        "wave_count": len(army.waves),
    }


async def handle_change_wave(
    message: GameMessage, sender_uid: int,
) -> Optional[dict[str, Any]]:
    """Handle ``change_wave`` — modify critter type or count in an existing wave.
    
    Supports changing:
    - critter_iid: replace critter type in the wave
    - slots: number of critter slots in the wave
    
    The wave contains only metadata (iid, slots), not concrete critters.
    """
    svc = _svc()
    aid = getattr(message, "aid", 0)
    wave_number = getattr(message, "wave_number", 0)
    critter_iid = getattr(message, "critter_iid", "").strip()
    slots = getattr(message, "slots", None)
    target_uid = sender_uid if sender_uid > 0 else message.sender
    empire = svc.empire_service.get(target_uid)
    
    if empire is None:
        log.warning("change_wave failed: no empire found for uid=%d", target_uid)
        return {
            "type": "change_wave_response",
            "success": False,
            "error": "No empire found",
        }
    
    # Find the army by aid
    army = None
    for a in empire.armies:
        if a.aid == aid:
            army = a
            break
    
    if army is None:
        log.warning("change_wave failed uid=%d: army aid=%d not found", target_uid, aid)
        return {
            "type": "change_wave_response",
            "success": False,
            "error": f"Army {aid} not found",
        }
    
    # Find the wave by wave_number (0-indexed)
    if wave_number < 0 or wave_number >= len(army.waves):
        log.warning("change_wave failed uid=%d aid=%d: wave_number=%d out of range", 
                    target_uid, aid, wave_number)
        return {
            "type": "change_wave_response",
            "success": False,
            "error": f"Wave {wave_number} not found",
        }
    
    wave = army.waves[wave_number]
    
    # Change critter type if provided
    if critter_iid:
        wave.iid = critter_iid
        log.info("change_wave: updated wave %d critter type to %s", wave_number, critter_iid)
    
    # Update slots if provided
    if slots is not None and slots > 0:
        old_slots = wave.slots
        wave.slots = slots
        log.info("change_wave: updated wave %d slots from %d to %d", wave_number, old_slots, slots)
    
    log.info("change_wave success uid=%d aid=%d wave=%d critter_iid=%s slots=%d", 
             target_uid, aid, wave_number, wave.iid, wave.slots)
    return {
        "type": "change_wave_response",
        "success": True,
        "aid": aid,
        "wave_number": wave_number,
        "critter_iid": wave.iid,
        "slots": wave.slots,
    }


async def handle_end_siege(
    message: GameMessage, sender_uid: int,
) -> Optional[dict[str, Any]]:
    """Handle ``end_siege`` — end the ongoing siege on sender's empire.

    TODO: Call empire.end_siege().
    """
    log.info("end_siege from uid=%d (not yet implemented)", sender_uid)
    return None


# ===================================================================
# Structures (additional)
# ===================================================================

async def handle_upgrade_structure(
    message: GameMessage, sender_uid: int,
) -> Optional[dict[str, Any]]:
    """Handle ``upgrade_structure`` — upgrade a tower on the map.

    TODO: Check requirements & resources, replace structure with upgrade.
    """
    log.info("upgrade_structure from uid=%d (not yet implemented)", sender_uid)
    return None


# ===================================================================
# Life
# ===================================================================

async def handle_increase_life(
    message: GameMessage, sender_uid: int,
) -> Optional[dict[str, Any]]:
    """Handle ``increase_life`` — increase max life by 1.

    TODO: Check culture cost (progressive), check life cap from effects.
    """
    log.info("increase_life from uid=%d (not yet implemented)", sender_uid)
    return None


# ===================================================================
# Battle
# ===================================================================

async def _send_battle_state_to_observer(attack: Attack, observer_uid: int) -> None:
    """Send current battle state to an observer.
    
    This sends status updates during IN_SIEGE and IN_BATTLE phases.
    """
    svc = _svc()
    
    # Get defender and attacker empires
    defender_empire = svc.empire_service.get(attack.defender_uid)
    attacker_empire = svc.empire_service.get(attack.attacker_uid)
    
    if not defender_empire or not attacker_empire:
        return
    
    # Get attacking army
    attacking_army = None
    for army in attacker_empire.armies:
        if army.aid == attack.army_aid:
            attacking_army = army
            break
    
    if not attacking_army:
        return
    
    # Prepare wave information
    waves_info = []
    for i, wave in enumerate(attacking_army.waves):
        waves_info.append({
            "wave_id": wave.wave_id,  # Use actualwave_id from wave object, not index
            "critter_iid": wave.iid,
            "slots": wave.slots,
        })
    
    # Get battle state (if battle is running)
    battle = _active_battles.get(attack.defender_uid)
       
    # Determine phase-specific timing and status text
    if attack.phase == AttackPhase.IN_SIEGE:
        time_since_start_s = -attack.siege_remaining_seconds  # Negative = countdown to battle start
    elif attack.phase == AttackPhase.IN_BATTLE and battle:
        time_since_start_s = battle.elapsed_ms / 1000.0
    else:
        # TRAVELLING, FINISHED, or IN_BATTLE without active battle
        time_since_start_s = 0
    status = attack.phase.value
    
    # Build wave_info for first unstarted wave
    svc_items = svc.upgrade_provider.items if svc.upgrade_provider else {}
    wave_info = None
    if attacking_army and attacking_army.waves:
        total_waves = len(attacking_army.waves)
        for i, w in enumerate(attacking_army.waves):
            if w.num_critters_spawned == 0:
                item = svc_items.get(w.iid)
                critter_name = item.name if item else w.iid
                wave_info = {
                    "wave_index": i + 1,
                    "total_waves": total_waves,
                    "iid": w.iid,
                    "critter_name": critter_name,
                    "slots": w.slots,
                    "next_critter_ms": max(0.0, w.next_critter_ms),
                }
                break

    # Send battle status update
    status_msg = {
        "type": "battle_status",
        "attack_id": attack.attack_id,
        "phase": status,
        "defender_uid": attack.defender_uid,
        "defender_name": defender_empire.name,
        "attacker_uid": attack.attacker_uid,
        "attacker_name": attacker_empire.name,
        "time_since_start_s": time_since_start_s,
        "wave_info": wave_info,
    }
    
    if svc.server:
        await svc.server.send_to(observer_uid, status_msg)


async def _send_battle_setup_to_observer(attack: Attack, observer_uid: int) -> None:
    """Send battle_setup message to initialize the battle view.
    
    This includes the defender's map, structures, and paths.
    """
    from gameserver.engine.battle_service import find_hex_path
    from gameserver.models.hex import HexCoord
    
    svc = _svc()
    
    # Get defender empire (owner of the map)
    defender_empire = svc.empire_service.get(attack.defender_uid)
    if not defender_empire:
        log.warning("_send_battle_setup: defender %d not found", attack.defender_uid)
        return
    
    if not defender_empire.hex_map:
        log.warning("_send_battle_setup: defender %d has no map", attack.defender_uid)
        return
    
    # ── Parse map to find spawn and castle ──────────────
    tiles = defender_empire.hex_map
    spawn_pos: tuple[int, int] | None = None
    castle_pos: tuple[int, int] | None = None
    passable: set[tuple[int, int]] = set()
    
    for key, tile_type in tiles.items():
        q, r = map(int, key.split(","))
        if tile_type in ("spawnpoint", "path", "castle"):
            passable.add((q, r))
        if tile_type == "spawnpoint" and spawn_pos is None:
            spawn_pos = (q, r)
        elif tile_type == "castle":
            castle_pos = (q, r)
    
    # Calculate path
    hex_path = []
    if spawn_pos and castle_pos:
        hex_path = find_hex_path(spawn_pos, castle_pos, passable)
    
    # ── Get structures ───────────────────────────────────
    # Load structures from hex_map tiles and create Structure objects
    structures_dict = {}
    if defender_empire.structures:
        structures_dict = dict(defender_empire.structures)
    
    # Also load structures from hex_map tiles (for backwards compatibility)
    from gameserver.models.structure import Structure
    from gameserver.models.hex import HexCoord
    structure_sid = 1
    items_dict = svc.upgrade_provider.items if svc.upgrade_provider else {}
    for tile_key, tile_type in tiles.items():
        # Check if tile_type is a structure (not path, castle, etc.)
        if tile_type not in ("empty", "path", "spawnpoint", "castle", "blocked", "void"):
            # This is a structure tile, load stats from item provider
            item = items_dict.get(tile_type)
            if item:
                # Parse q,r from key "q,r"
                q, r = map(int, tile_key.split(","))
                # Create Structure object with stats from item config
                structure = Structure(
                    sid=structure_sid,
                    iid=tile_type,
                    position=HexCoord(q, r),
                    damage=getattr(item, "damage", 1.0),
                    range=getattr(item, "range", 1),
                    reload_time_ms=getattr(item, "reload_time", 2000.0),
                    shot_speed=getattr(item, "shot_speed", 1.0),
                    shot_type=getattr(item, "shot_type", "normal"),
                    shot_sprite=getattr(item, "shot_sprite", ""),
                    effects=getattr(item, "effects", {}),
                )
                structures_dict[structure_sid] = structure
                structure_sid += 1
                log.debug("[_send_battle_setup] Loaded structure sid=%d iid=%s at (%d,%d)",
                         structure.sid, structure.iid, q, r)
    
    # ── Send battle_setup ────────────────────────────────
    setup_msg = {
        "type": "battle_setup",
        "bid": attack.attack_id,
        "defender_uid": attack.defender_uid,
        "attacker_uid": attack.attacker_uid,
        "tiles": tiles,
        "structures": [
            {
                "sid": s.sid,
                "iid": s.iid,
                "q": s.position.q,
                "r": s.position.r,
                "damage": s.damage,
                "range": s.range,
            }
            for s in structures_dict.values()
        ],
        "path": [{"q": h.q, "r": h.r} for h in hex_path],
    }
    
    if svc.server:
        await svc.server.send_to(observer_uid, setup_msg)
        log.info("_send_battle_setup: sent to uid=%d (attack_id=%d)", observer_uid, attack.attack_id)


async def handle_battle_register(
    message: GameMessage, sender_uid: int,
) -> Optional[dict[str, Any]]:
    """Handle ``battle_register`` — register as battle observer.
    
    Client subscribes to battle updates for attacks they're involved in.
    """
    target_uid = getattr(message, "target_uid", None)
    if target_uid is None:
        log.warning("battle_register: missing target_uid")
        return {"type": "error", "message": "Missing target_uid"}
    
    svc = _svc()
    
    # Find attack involving this target_uid (either as attacker or defender)
    attack_svc = svc.attack_service
    attack = None
    
    # Check if sender is attacker
    for a in attack_svc.get_outgoing(sender_uid):
        if a.defender_uid == target_uid:
            attack = a
            break
    
    # Check if sender is defender
    if not attack:
        for a in attack_svc.get_incoming(sender_uid):
            if a.attacker_uid == target_uid or a.defender_uid == sender_uid:
                attack = a
                break
    
    if not attack:
        log.warning("battle_register: no attack found for uid=%d target=%d", sender_uid, target_uid)
        return {"type": "error", "message": "No active attack found"}
    
    # Register observer
    if not hasattr(attack, '_observers'):
        attack._observers = set()
    attack._observers.add(sender_uid)
    
    log.info("battle_register: uid=%d registered for attack %d (phase=%s)", 
             sender_uid, attack.attack_id, attack.phase.value)
    
    # Send battle_setup to initialize the map view
    await _send_battle_setup_to_observer(attack, sender_uid)
    
    # Send initial state immediately
    await _send_battle_state_to_observer(attack, sender_uid)
    
    return {"type": "battle_register_ack", "attack_id": attack.attack_id}


async def handle_battle_unregister(
    message: GameMessage, sender_uid: int,
) -> Optional[dict[str, Any]]:
    """Handle ``battle_unregister`` — unregister from battle observation.
    
    Client unsubscribes from battle updates.
    """
    target_uid = getattr(message, "target_uid", None)
    if target_uid is None:
        log.warning("battle_unregister: missing target_uid")
        return {"type": "error", "message": "Missing target_uid"}
    
    svc = _svc()
    attack_svc = svc.attack_service
    
    # Find attack and remove observer
    for attack in attack_svc.get_all_attacks():
        if hasattr(attack, '_observers') and sender_uid in attack._observers:
            attack._observers.remove(sender_uid)
            log.info("battle_unregister: uid=%d unregistered from attack %d", 
                     sender_uid, attack.attack_id)
            return {"type": "battle_unregister_ack"}
    
    log.warning("battle_unregister: uid=%d not registered for any attack", sender_uid)
    return {"type": "battle_unregister_ack"}


async def handle_battle_next_wave(
    message: GameMessage, sender_uid: int,
) -> Optional[dict[str, Any]]:
    """Handle ``battle_next_wave_request`` — trigger next wave in battle.

    TODO: Call battle.next_wave_requested(), return wave preview.
    """
    log.info("battle_next_wave from uid=%d (not yet implemented)", sender_uid)
    return None


# ===================================================================
# Social / Messaging
# ===================================================================

async def handle_notification_request(
    message: GameMessage, sender_uid: int,
) -> Optional[dict[str, Any]]:
    """Handle ``notification_request`` — fetch pending notification.

    TODO: Return pending notification or fallback to summary_request.
    """
    log.info("notification_request from uid=%d (not yet implemented)", sender_uid)
    return None


async def handle_user_message(
    message: GameMessage, sender_uid: int,
) -> Optional[dict[str, Any]]:
    """Handle ``user_message`` — send a private message to another player.

    TODO: Store message in DB with sender, receiver, body, timestamp.
    """
    log.info("user_message from uid=%d (not yet implemented)", sender_uid)
    return None


async def handle_timeline_request(
    message: GameMessage, sender_uid: int,
) -> Optional[dict[str, Any]]:
    """Handle ``timeline_request`` — fetch mailbox / message history.

    TODO: Mark messages read, return last 25 messages (max 10 days).
    """
    log.info("timeline_request from uid=%d (not yet implemented)", sender_uid)
    return None


# ===================================================================
# User Info / Hall of Fame
# ===================================================================

async def handle_userinfo_request(
    message: GameMessage, sender_uid: int,
) -> Optional[dict[str, Any]]:
    """Handle ``userinfo_request`` — return info about players.

    TODO: Return UserInfo (TAI, currBuilding, citizens, etc.) for requested UIDs.
    """
    log.info("userinfo_request from uid=%d (not yet implemented)", sender_uid)
    return None


async def handle_hall_of_fame(
    message: GameMessage, sender_uid: int,
) -> Optional[dict[str, Any]]:
    """Handle ``hall_of_fame_request`` — return rankings and trophies.

    TODO: Load ranking, winners, prosperity, defense god, treasure hunter, world wonder.
    """
    log.info("hall_of_fame_request from uid=%d (not yet implemented)", sender_uid)
    return None


# ===================================================================
# Preferences
# ===================================================================

async def handle_preferences_request(
    message: GameMessage, sender_uid: int,
) -> Optional[dict[str, Any]]:
    """Handle ``preferences_request`` — return player preferences.

    TODO: Load e-mail/statement from DB.
    """
    log.info("preferences_request from uid=%d (not yet implemented)", sender_uid)
    return None


async def handle_change_preferences(
    message: GameMessage, sender_uid: int,
) -> Optional[dict[str, Any]]:
    """Handle ``change_preferences`` — update player profile.

    TODO: Update statement + e-mail in DB.
    """
    log.info("change_preferences from uid=%d (not yet implemented)", sender_uid)
    return None


# ===================================================================
# Auth / Account
# ===================================================================

async def handle_auth_request(
    message: GameMessage, sender_uid: int,
) -> Optional[dict[str, Any]]:
    """Handle ``auth_request`` — authenticate a player.

    On successful auth the response includes ``session_state`` so
    the client knows which subscriptions to restore (e.g. battle
    observer registrations that were lost during a reconnect).
    """
    svc = _svc()
    username = getattr(message, "username", "")
    password = getattr(message, "password", "")

    uid = await svc.auth_service.login(username, password)
    if uid is not None:
        # Gather restorable session state for the reconnecting client
        session_state = _build_session_state(uid)
        
        # Fetch summary immediately so client has fresh state after login
        empire = svc.empire_service.get(uid)
        summary_data = _build_empire_summary(empire, uid) if empire else None
        
        return {
            "type": "auth_response",
            "success": True,
            "uid": uid,
            "reason": "",
            "session_state": session_state,
            "summary": summary_data,
        }
    return {
        "type": "auth_response",
        "success": False,
        "uid": 0,
        "reason": "Invalid username or password",
    }


def _build_session_state(uid: int) -> dict[str, Any]:
    """Build a dict describing restorable session state for *uid*.

    Includes:
    - ``active_battles``: list of attack IDs the user is involved in
      (so the client can re-register as observer).
    - ``has_active_siege``: whether the user is under siege.
    """
    svc = _svc()
    attack_svc = svc.attack_service

    active_battles: list[dict[str, Any]] = []
    for a in attack_svc.get_incoming(uid):
        active_battles.append({
            "attack_id": a.attack_id,
            "role": "defender",
            "phase": a.phase.value if hasattr(a.phase, "value") else str(a.phase),
        })
    for a in attack_svc.get_outgoing(uid):
        active_battles.append({
            "attack_id": a.attack_id,
            "role": "attacker",
            "phase": a.phase.value if hasattr(a.phase, "value") else str(a.phase),
        })

    return {
        "active_battles": active_battles,
    }


def _build_empire_summary(empire, uid: int) -> dict[str, Any]:
    """Build a complete empire summary for a given UID.
    
    Used by both handle_summary_request() and handle_auth_request().
    Returns the full empire state including resources, buildings, research,
    structures, and ongoing attacks.
    """
    svc = _svc()
    
    # Active builds: buildings with remaining effort > 0
    active_buildings = {
        iid: round(remaining, 1)
        for iid, remaining in empire.buildings.items()
        if remaining > 0
    }
    completed_buildings = [
        iid for iid, remaining in empire.buildings.items()
        if remaining <= 0
    ]

    # Active research: knowledge with remaining effort > 0
    active_research = {
        iid: round(remaining, 1)
        for iid, remaining in empire.knowledge.items()
        if remaining > 0
    }
    completed_research = [
        iid for iid, remaining in empire.knowledge.items()
        if remaining <= 0
    ]

    # Structures summary
    structures_list = []
    for sid, s in empire.structures.items():
        structures_list.append({
            "sid": sid,
            "iid": s.iid,
            "position": {"q": s.position.q, "r": s.position.r},
            "damage": s.damage,
            "range": s.range,
        })

    # Ongoing attacks
    def _attack_dto(a):
        return {
            "attack_id": a.attack_id,
            "attacker_uid": a.attacker_uid,
            "defender_uid": a.defender_uid,
            "army_aid": a.army_aid,
            "phase": a.phase.value,
            "eta_seconds": round(a.eta_seconds, 1),
            "total_eta_seconds": round(a.total_eta_seconds, 1),
            "siege_remaining_seconds": round(a.siege_remaining_seconds, 1),
            "total_siege_seconds": round(a.total_siege_seconds, 1),
        }

    attacks_incoming = [_attack_dto(a) for a in svc.attack_service.get_incoming(uid)]
    attacks_outgoing = [_attack_dto(a) for a in svc.attack_service.get_outgoing(uid)]

    # Count purchased tiles (non-void tiles in hex_map)
    hex_map = getattr(empire, 'hex_map', {}) or {}
    purchased_tile_count = sum(1 for tile_type in hex_map.values() if tile_type != 'void')
    next_tile_price = svc.empire_service._tile_price(purchased_tile_count + 1)
    
    next_citizen_price = svc.empire_service._citizen_price(sum(empire.citizens.values()) + 1)
    
    # Count armies
    army_count = len(empire.armies)
    next_army_price = svc.empire_service._army_price(army_count + 1)
    
    # Count total waves across all armies
    total_waves = sum(len(army.waves) for army in empire.armies)
    next_wave_price = svc.empire_service._wave_price(total_waves + 1)
    # Critter slot price is wave-specific (based on slots in that wave)
    # Show base price for first slot as reference
    base_critter_slot_price = svc.empire_service._critter_slot_price(1)

    return {
        "type": "summary_response",
        "uid": empire.uid,
        "name": empire.name,
        "resources": {k: round(v, 2) for k, v in empire.resources.items()},
        "citizens": dict(empire.citizens),
        "citizen_price": round(next_citizen_price, 2),
        "tile_price": round(next_tile_price, 2),
        "army_price": round(next_army_price, 2),
        "wave_price": round(next_wave_price, 2),
        "critter_slot_price": round(base_critter_slot_price, 2),
        "citizen_effect": svc.empire_service._citizen_effect,
        "base_gold": svc.empire_service._base_gold,
        "base_culture": svc.empire_service._base_culture,
        "max_life": empire.max_life,
        "effects": dict(empire.effects),
        "artefacts": list(empire.artefacts),
        "buildings": dict(empire.buildings),  # iid -> remaining effort
        "knowledge": dict(empire.knowledge),  # iid -> remaining effort
        "active_buildings": active_buildings,
        "completed_buildings": completed_buildings,
        "active_research": active_research,
        "completed_research": completed_research,
        "build_queue": empire.build_queue,
        "research_queue": empire.research_queue,
        "structures": structures_list,
        "army_count": len(empire.armies),
        "spy_count": len(empire.spies),
        "attacks_incoming": attacks_incoming,
        "attacks_outgoing": attacks_outgoing,
    }


async def handle_signup(
    message: GameMessage, sender_uid: int,
) -> Optional[dict[str, Any]]:
    """Handle ``signup`` — create a new account."""
    svc = _svc()
    username = getattr(message, "username", "")
    password = getattr(message, "password", "")
    email = getattr(message, "email", "")
    empire_name = getattr(message, "empire_name", "")

    result = await svc.auth_service.signup(username, password, email, empire_name)
    if isinstance(result, int):
        log.info("Signup success: user=%s uid=%d", username, result)
        # Create empire for the new user — INIT is auto-completed (effort 0)
        from gameserver.models.empire import Empire
        empire = Empire(
            uid=result,
            name=empire_name or f"{username}'s Empire",
            buildings={"INIT": 0.0},
        )
        svc.empire_service.register(empire)
        return {
            "type": "signup_response",
            "success": True,
            "uid": result,
            "reason": "",
        }
    # result is an error string
    log.info("Signup failed: user=%s reason=%s", username, result)
    return {
        "type": "signup_response",
        "success": False,
        "uid": 0,
        "reason": result,
    }


async def handle_create_empire(
    message: GameMessage, sender_uid: int,
) -> Optional[dict[str, Any]]:
    """Handle ``create_empire`` — create a fresh empire for a UID.

    TODO: Create Empire object, register in EmpireService.
    """
    log.info("create_empire from uid=%d (not yet implemented)", sender_uid)
    return None


# ===================================================================
# Map (Composer) requests
# ===================================================================

async def handle_map_load_request(
    message: GameMessage, sender_uid: int,
) -> Optional[dict[str, Any]]:
    """Load the hex map for the current empire."""
    svc = _svc()
    target_uid = sender_uid if sender_uid > 0 else message.sender
    empire = svc.empire_service.get(target_uid)
    
    if empire is None:
        return {
            "type": "map_load_response",
            "tiles": {},
            "error": f"No empire found for uid {target_uid}",
        }
    
    # Get hex_map from Empire object (or use empty dict if not present)
    hex_map = getattr(empire, 'hex_map', {}) or {}
    
    return {
        "type": "map_load_response",
        "tiles": hex_map,
    }


async def handle_map_save_request(
    message: MapSaveRequest, sender_uid: int,
) -> Optional[dict[str, Any]]:
    """Save the hex map for the current empire.
    
    The map data is stored in the empire object. It will be persisted
    automatically during the next regular state save (e.g., on shutdown).
    """
    svc = _svc()
    target_uid = sender_uid if sender_uid > 0 else message.sender
    empire = svc.empire_service.get(target_uid)
    
    if empire is None:
        log.warning(f"Map save failed: No empire found for uid {target_uid}")
        return {
            "type": "map_save_response",
            "success": False,
            "error": f"No empire found for uid {target_uid}",
        }
    
    # Get tiles from typed message model
    raw_tiles = message.tiles or {}
    
    # Normalize: accept both {"0,0": "type"} and {"0,0": {"type": "type"}}
    tiles = {}
    for k, v in raw_tiles.items():
        if isinstance(v, dict):
            tiles[k] = v.get('type', 'empty')
        else:
            tiles[k] = v

    # -- Validation --------------------------------------------------
    type_counts: dict[str, int] = {}
    for tile_type in tiles.values():
        type_counts[tile_type] = type_counts.get(tile_type, 0) + 1

    castle_count = type_counts.get('castle', 0)
    spawnpoint_count = type_counts.get('spawnpoint', 0)
    errors: list[str] = []

    if castle_count != 1:
        errors.append(
            f"Map must contain exactly 1 castle (found {castle_count})"
        )
    if spawnpoint_count < 1:
        errors.append("Map must contain at least 1 spawnpoint")
    
    # Check path connectivity (only if basic requirements are met)
    if not errors and not _has_path_from_spawn_to_castle(tiles):
        errors.append("No passable path found from spawnpoint to castle")

    if errors:
        log.warning(
            "Map validation failed for %s (uid=%s): %s",
            empire.name, target_uid, "; ".join(errors),
        )
        return {
            "type": "map_save_response",
            "success": False,
            "error": "; ".join(errors),
        }

    # -- Persist -----------------------------------------------------
    tile_count = len(tiles)
    empire.hex_map = tiles
    log.info(f"Map saved for empire {empire.name} (uid={target_uid}): {tile_count} tiles")

    # ── Sync structures into active battle (if one is running) ──────
    battle = _active_battles.get(target_uid)
    if battle is not None:
        items_dict = svc.upgrade_provider.items if svc.upgrade_provider else {}
        new_sids = _sync_battle_structures(battle, tiles, items_dict)
        if new_sids:
            log.info("[map_save] Synced %d new/changed structures into active battle bid=%d",
                     len(new_sids), battle.bid)
            # Broadcast updated structure list to all observers
            structure_update_msg = {
                "type": "structure_update",
                "bid": battle.bid,
                "structures": [
                    {
                        "sid": s.sid,
                        "iid": s.iid,
                        "q": s.position.q,
                        "r": s.position.r,
                        "damage": s.damage,
                        "range": s.range,
                    }
                    for s in battle.structures.values()
                ],
            }
            if svc.server:
                import asyncio
                for uid in battle.observer_uids:
                    asyncio.create_task(svc.server.send_to(uid, structure_update_msg))

    return {
        "type": "map_save_response",
        "success": True,
    }


async def handle_buy_tile_request(
    message: GameMessage, sender_uid: int,
) -> Optional[dict[str, Any]]:
    """Buy a void tile and convert it to empty land.
    
    Cost: TBD (currently free)
    """
    svc = _svc()
    target_uid = sender_uid if sender_uid > 0 else message.sender
    empire = svc.empire_service.get(target_uid)
    
    if empire is None:
        return {
            "type": "buy_tile_response",
            "success": False,
            "error": f"No empire found for uid {target_uid}",
        }
    
    q = getattr(message, 'q', None)
    r = getattr(message, 'r', None)
    
    if q is None or r is None:
        return {
            "type": "buy_tile_response",
            "success": False,
            "error": "Missing tile coordinates (q, r)",
        }
    
    hex_map = getattr(empire, 'hex_map', {}) or {}
    tile_key = f"{q},{r}"
    
    # Check if tile exists and is void
    current_type = hex_map.get(tile_key, 'void')
    if current_type != 'void':
        return {
            "type": "buy_tile_response",
            "success": False,
            "error": f"Tile {tile_key} is not a void tile (current type: {current_type})",
        }
    
    # Calculate cost based on number of already purchased tiles
    purchased_tile_count = sum(1 for tile_type in hex_map.values() if tile_type != 'void')
    tile_price = svc.empire_service._tile_price(purchased_tile_count + 1)
    
    # Check if player has enough gold
    current_gold = empire.resources.get('gold', 0.0)
    if current_gold < tile_price:
        return {
            "type": "buy_tile_response",
            "success": False,
            "error": f"Not enough gold (need {tile_price:.1f}, have {current_gold:.1f})",
        }
    
    # Deduct gold
    empire.resources['gold'] -= tile_price
    
    # Convert void tile to empty land
    hex_map[tile_key] = 'empty'
    empire.hex_map = hex_map
    
    log.info(f"Tile {tile_key} purchased by empire {empire.name} (uid={target_uid}) for {tile_price:.1f} gold")
    
    return {
        "type": "buy_tile_response",
        "success": True,
        "tile_key": tile_key,
        "new_type": "empty",
        "cost": round(tile_price, 2),
    }


async def handle_buy_wave_request(
    message: GameMessage, sender_uid: int,
) -> Optional[dict[str, Any]]:
    """Buy a new wave for an army with gold.
    
    Cost based on total number of waves across all armies.
    """
    from gameserver.models.army import CritterWave
    
    svc = _svc()
    target_uid = sender_uid if sender_uid > 0 else message.sender
    empire = svc.empire_service.get(target_uid)
    
    if empire is None:
        return {
            "type": "buy_wave_response",
            "success": False,
            "error": f"No empire found for uid {target_uid}",
        }
    
    aid = getattr(message, 'aid', None)
    if aid is None:
        return {
            "type": "buy_wave_response",
            "success": False,
            "error": "Missing army ID (aid)",
        }
    
    # Find the army
    army = None
    for a in empire.armies:
        if a.aid == aid:
            army = a
            break
    
    if army is None:
        return {
            "type": "buy_wave_response",
            "success": False,
            "error": f"Army {aid} not found",
        }
    
    # Calculate cost based on total waves across all armies
    total_waves = sum(len(a.waves) for a in empire.armies)
    wave_price = svc.empire_service._wave_price(total_waves + 1)
    
    # Check if player has enough gold
    current_gold = empire.resources.get('gold', 0.0)
    if current_gold < wave_price:
        return {
            "type": "buy_wave_response",
            "success": False,
            "error": f"Not enough gold (need {wave_price:.1f}, have {current_gold:.1f})",
        }
    
    # Deduct gold
    empire.resources['gold'] -= wave_price
    
    # Create new wave with default critter (SLAVE) and 1 slot
    global _next_wid
    new_wave = CritterWave(
        wave_id=_next_wid,
        iid="SLAVE",
        slots=1,
    )
    _next_wid += 1
    
    # Add to army
    army.waves.append(new_wave)
    
    log.info(f"Wave purchased for army {aid} by empire {empire.name} (uid={target_uid}) for {wave_price:.1f} gold")
    
    return {
        "type": "buy_wave_response",
        "success": True,
        "aid": aid,
        "wave_id": new_wave.wave_id,
        "cost": round(wave_price, 2),
        "wave_count": len(army.waves),
    }


async def handle_buy_critter_slot_request(
    message: GameMessage, sender_uid: int,
) -> Optional[dict[str, Any]]:
    """Buy an additional critter slot for a wave with gold.
    
    Cost based on total number of critter slots across all waves.
    """
    svc = _svc()
    target_uid = sender_uid if sender_uid > 0 else message.sender
    empire = svc.empire_service.get(target_uid)
    
    if empire is None:
        return {
            "type": "buy_critter_slot_response",
            "success": False,
            "error": f"No empire found for uid {target_uid}",
        }
    
    aid = getattr(message, 'aid', None)
    wave_number = getattr(message, 'wave_number', None)
    
    if aid is None or wave_number is None:
        return {
            "type": "buy_critter_slot_response",
            "success": False,
            "error": "Missing army ID (aid) or wave number",
        }
    
    # Find the army
    army = None
    for a in empire.armies:
        if a.aid == aid:
            army = a
            break
    
    if army is None:
        return {
            "type": "buy_critter_slot_response",
            "success": False,
            "error": f"Army {aid} not found",
        }
    
    # Find the wave
    if wave_number < 0 or wave_number >= len(army.waves):
        return {
            "type": "buy_critter_slot_response",
            "success": False,
            "error": f"Wave {wave_number} not found",
        }
    
    wave = army.waves[wave_number]
    
    # Calculate cost based on slots in this specific wave only
    slot_price = svc.empire_service._critter_slot_price(wave.slots + 1)
    
    # Check if player has enough gold
    current_gold = empire.resources.get('gold', 0.0)
    if current_gold < slot_price:
        return {
            "type": "buy_critter_slot_response",
            "success": False,
            "error": f"Not enough gold (need {slot_price:.1f}, have {current_gold:.1f})",
        }
    
    # Deduct gold
    empire.resources['gold'] -= slot_price
    
    # Increase slot count
    old_slots = wave.slots
    wave.slots += 1
    
    log.info(f"Critter slot purchased for army {aid} wave {wave_number} by empire {empire.name} (uid={target_uid}) for {slot_price:.1f} gold (slots: {old_slots} → {wave.slots})")
    
    return {
        "type": "buy_critter_slot_response",
        "success": True,
        "aid": aid,
        "wave_number": wave_number,
        "new_slots": wave.slots,
        "cost": round(slot_price, 2),
    }


# ===================================================================
# Battle (event-based, Java-style architecture)
# ===================================================================

_active_battles: dict[int, "BattleState"] = {}  # uid → BattleState
_next_bid: int = 1


def _sync_battle_structures(battle: "BattleState", tiles: dict, items_dict: dict) -> list[int]:
    """Sync battle.structures from the current tile map.

    Adds towers that were placed after battle started, removes towers that
    were demolished, and leaves untouched towers (same iid at same position)
    intact so their reload timers and targeting state survive.

    Returns list of newly added SIDs.
    """
    from gameserver.models.structure import Structure
    from gameserver.models.hex import HexCoord

    NON_STRUCTURE = {"empty", "path", "spawnpoint", "castle", "blocked", "void"}

    # Build lookup: (q, r) → existing Structure
    pos_to_struct: dict[tuple[int, int], Structure] = {
        (s.position.q, s.position.r): s for s in battle.structures.values()
    }

    # Build lookup: (q, r) → tile_type for all structure tiles in new map
    new_pos_types: dict[tuple[int, int], str] = {}
    for tile_key, tile_type in tiles.items():
        if tile_type not in NON_STRUCTURE:
            q, r = map(int, tile_key.split(","))
            new_pos_types[(q, r)] = tile_type

    # Remove structures whose tile was removed or replaced
    sids_to_remove = [
        s.sid for s in battle.structures.values()
        if (s.position.q, s.position.r) not in new_pos_types
           or new_pos_types[(s.position.q, s.position.r)] != s.iid
    ]
    for sid in sids_to_remove:
        s = battle.structures.pop(sid)
        log.info("[sync_structures] Removed structure sid=%d iid=%s at (%d,%d)",
                 s.sid, s.iid, s.position.q, s.position.r)

    # Add new structures (positions not yet in battle or replaced above)
    existing_pos: set[tuple[int, int]] = {
        (s.position.q, s.position.r) for s in battle.structures.values()
    }
    next_sid = max(battle.structures.keys(), default=0) + 1
    new_sids: list[int] = []

    for (q, r), tile_type in new_pos_types.items():
        if (q, r) in existing_pos:
            continue  # Already present and correct iid
        item = items_dict.get(tile_type)
        if not item:
            continue
        structure = Structure(
            sid=next_sid,
            iid=tile_type,
            position=HexCoord(q, r),
            damage=getattr(item, "damage", 1.0),
            range=getattr(item, "range", 1),
            reload_time_ms=getattr(item, "reload_time", 2000.0),
            shot_speed=getattr(item, "shot_speed", 1.0),
            shot_type=getattr(item, "shot_type", "normal"),
            shot_sprite=getattr(item, "shot_sprite", ""),
            effects=getattr(item, "effects", {}),
        )
        battle.structures[next_sid] = structure
        new_sids.append(next_sid)
        log.info("[sync_structures] Added structure sid=%d iid=%s at (%d,%d)",
                 next_sid, tile_type, q, r)
        next_sid += 1

    return new_sids


async def _run_battle_task(bid: int, battle: "BattleState", battle_svc: "BattleService", send_fn, broadcast_interval_ms: float = 250.0) -> None:
    """Wrapper for the async battle loop with cleanup and resource transfer.
    
    After battle completes:
    1. Computes loot (if defender lost)
    2. Applies resource transfers to empires
    3. Sends battle_summary with loot info
    4. Marks the attack as FINISHED
    5. Cleans up the battle from active battles
    """
    svc = _svc()
    
    try:
        await battle_svc.run_battle(battle, send_fn, broadcast_interval_ms)
        
        # Battle finished - compute loot and apply resource transfers
        log.info("[battle] bid=%d complete: attacker_wins=%s", bid, not battle.defender_won)
        
        # Compute and apply loot if defender lost
        loot: dict = {}
        if battle.defender_won is False:
            loot = _compute_and_apply_loot(battle, svc)
        
        # Send battle summary with loot info
        await battle_svc.send_summary(battle, send_fn, loot)
        
        # Mark attack as FINISHED so it gets removed from _attacks list
        from gameserver.models.attack import AttackPhase
        attack = svc.attack_service.get(bid)
        if attack:
            attack.phase = AttackPhase.FINISHED
            log.info("[battle] Attack %d marked as FINISHED", bid)
        
    except Exception:
        import traceback
        log.error("Battle loop crashed: %s", traceback.format_exc())
    finally:
        _active_battles.pop(battle.defender.uid, None)


def _compute_and_apply_loot(battle: "BattleState", svc) -> dict:
    """Compute and apply loot on defender loss.
    
    Returns a loot dict with details of what was stolen:
    {
        "knowledge": {"iid": str, "name": str, "pct": float, "amount": float} | None,
        "culture": float,
        "artefact": str | None,
    }
    """
    import random as _random
    
    defender = battle.defender
    attacker = battle.attacker
    if not defender or not attacker:
        return {}
    
    cfg = svc.game_config
    items = svc.upgrade_provider.items if svc.upgrade_provider else {}
    
    loot: dict = {"knowledge": None, "culture": 0.0, "artefact": None, "life_restored": 0.0}
    
    # ── 1. Knowledge theft ───────────────────────────────────────────────
    # Find knowledge defender has (in any state) that attacker doesn't have yet
    stealable_iids = [
        iid for iid in defender.knowledge
        if iid not in attacker.knowledge
    ]
    if stealable_iids:
        chosen_iid = _random.choice(stealable_iids)
        item = items.get(chosen_iid)
        effort = item.effort if item else 0.0
        min_pct = getattr(cfg, 'min_lose_knowledge', 0.03) if cfg else 0.03
        max_pct = getattr(cfg, 'max_lose_knowledge', 0.15) if cfg else 0.15
        pct = _random.uniform(min_pct, max_pct)
        gain = effort * pct
        # Credit attacker with culture (only in resources, NOT in attacker_gains
        # — it is displayed separately via loot["knowledge"]).
        attacker.resources["culture"] = attacker.resources.get("culture", 0.0) + gain
        loot["knowledge"] = {
            "iid": chosen_iid,
            "name": item.name if item else chosen_iid,
            "pct": round(pct * 100, 1),
            "amount": round(gain, 1),
        }
        log.info("[LOOT] Knowledge stolen from uid=%d: %s (%.1f%% of effort %.0f = %.1f culture)",
                 defender.uid, chosen_iid, pct * 100, effort, gain)
    
    # ── 2. Culture theft ────────────────────────────────────────────────
    min_c = getattr(cfg, 'min_lose_culture', 0.01) if cfg else 0.01
    max_c = getattr(cfg, 'max_lose_culture', 0.05) if cfg else 0.05
    pct_culture = _random.uniform(min_c, max_c)
    culture_pool = defender.resources.get("culture", 0.0)
    culture_stolen = round(culture_pool * pct_culture, 2)
    if culture_stolen > 0:
        defender.resources["culture"] = max(0.0, culture_pool - culture_stolen)
        attacker.resources["culture"] = attacker.resources.get("culture", 0.0) + culture_stolen
        battle.defender_losses["culture"] = (
            battle.defender_losses.get("culture", 0.0) + culture_stolen
        )
        loot["culture"] = culture_stolen
        log.info("[LOOT] Culture stolen from uid=%d: %.1f (%.1f%%)",
                 defender.uid, culture_stolen, pct_culture * 100)
    
    # ── 3. Artefact steal ───────────────────────────────────────────────
    artefact_chance = getattr(cfg, 'artefact_steal_chance', 0.33) if cfg else 0.33
    if defender.artefacts and _random.random() < artefact_chance:
        stolen_artefact = _random.choice(defender.artefacts)
        defender.artefacts.remove(stolen_artefact)
        attacker.artefacts.append(stolen_artefact)
        loot["artefact"] = stolen_artefact
        log.info("[LOOT] Artefact stolen from uid=%d: %s", defender.uid, stolen_artefact)

    # ── 4. Restore life after loss ──────────────────────────────────────
    from gameserver.util.effects import RESTORE_LIFE_AFTER_LOSS_OFFSET
    base_restore = getattr(cfg, 'restore_life_after_loss_offset', 1.0) if cfg else 1.0
    effect_restore = defender.effects.get(RESTORE_LIFE_AFTER_LOSS_OFFSET, 0.0)
    total_restore = base_restore + effect_restore
    current_life = defender.resources.get("life", 0.0)
    max_life = getattr(defender, 'max_life', 10.0)
    life_restored = min(total_restore, max(0.0, max_life - current_life))
    if life_restored > 0:
        defender.resources["life"] = current_life + life_restored
        loot["life_restored"] = round(life_restored, 2)
        log.info("[LOOT] Life restored to uid=%d: %.2f (base=%.1f + effect=%.1f)",
                 defender.uid, life_restored, base_restore, effect_restore)

    return loot


def _create_attack_phase_handler() -> Callable:
    """Create a handler for AttackPhaseChanged events.
    
    Broadcasts the phase update as a push message to interested clients.
    """
    async def _async_phase_changed(event: "AttackPhaseChanged") -> None:
        """Async: broadcast phase change and immediately push battle_status to observers."""
        svc = _svc()

        attacker_uid = event.attacker_uid
        defender_uid = event.defender_uid

        push_msg = {
            "type": "attack_phase_changed",
            "attack_id": event.attack_id,
            "attacker_uid": event.attacker_uid,
            "defender_uid": event.defender_uid,
            "army_aid": event.army_aid,
            "new_phase": event.new_phase,
        }

        if svc.server:
            await svc.server.send_to(attacker_uid, push_msg)
            await svc.server.send_to(defender_uid, push_msg)
            log.debug("[push] Sent attack_phase_changed: id=%d phase=%s to uids=%d,%d",
                      event.attack_id, event.new_phase, attacker_uid, defender_uid)

        # Immediately push battle_status (with wave_info) to all registered observers
        # so they don't have to wait up to 1 s for the next periodic tick.
        attack = None
        for a in svc.attack_service.get_all_attacks():
            if a.attack_id == event.attack_id:
                attack = a
                break
        if attack and hasattr(attack, '_observers') and attack._observers:
            for observer_uid in list(attack._observers):
                try:
                    await _send_battle_state_to_observer(attack, observer_uid)
                except Exception as exc:
                    log.exception("Failed to push battle_status on phase change to uid=%d: %s",
                                  observer_uid, exc)

    def _on_attack_phase_changed(event: "AttackPhaseChanged") -> None:
        """Sync handler that broadcasts phase change to clients."""
        import asyncio
        asyncio.create_task(_async_phase_changed(event))
    
    return _on_attack_phase_changed


def _create_battle_observer_broadcast_handler() -> Callable:
    """Create a handler for BattleObserverBroadcast events.
    
    Broadcasts battle status to all registered observers.
    """
    async def _async_broadcast_to_observers(event: "BattleObserverBroadcast") -> None:
        """Async wrapper for broadcasting to observers."""
        svc = _svc()
        attack_svc = svc.attack_service
        
        # Find attack by ID
        attack = None
        for a in attack_svc.get_all_attacks():
            if a.attack_id == event.attack_id:
                attack = a
                break
        
        if not attack:
            return
        
        # Get observers (if any)
        if not hasattr(attack, '_observers') or not attack._observers:
            return
        
        # Send status update to each observer
        for observer_uid in list(attack._observers):
            try:
                await _send_battle_state_to_observer(attack, observer_uid)
            except Exception as e:
                log.exception("Failed to send battle status to observer %d: %s", 
                             observer_uid, e)
    
    def _on_battle_observer_broadcast(event: "BattleObserverBroadcast") -> None:
        """Sync handler that schedules the async broadcast task."""
        asyncio.create_task(_async_broadcast_to_observers(event))
    
    return _on_battle_observer_broadcast


def _create_battle_start_handler() -> Callable:
    """Create a handler for BattleStartRequested events.
    
    Returns a sync function that schedules the async battle creation task.
    """
    async def _async_create_battle(event: "BattleStartRequested") -> None:
        """Async wrapper for the actual battle creation logic."""
        from gameserver.engine.battle_service import BattleService, find_hex_path
        from gameserver.models.battle import BattleState
        
        global _next_bid
        
        svc = _svc()
        attacker_uid = event.attacker_uid
        defender_uid = event.defender_uid
        army_aid = event.army_aid
        attack_id = event.attack_id
        
        log.info("[battle:start_requested] attack_id=%d attacker=%d defender=%d army=%d",
                 attack_id, attacker_uid, defender_uid, army_aid)
        
        # Get attacker's army
        attacker_empire = svc.empire_service.get(attacker_uid)
        if attacker_empire is None:
            log.error("[battle:start_requested] FAIL: attacker %d not found", attacker_uid)
            return
        
        attacking_army = None
        for army in attacker_empire.armies:
            if army.aid == army_aid:
                attacking_army = army
                break
        
        if attacking_army is None:
            log.error("[battle:start_requested] FAIL: army %d not found for attacker %d",
                      army_aid, attacker_uid)
            return
        
        # Get defender's empire, map, structures
        defender_empire = svc.empire_service.get(defender_uid)
        if defender_empire is None:
            log.error("[battle:start_requested] FAIL: defender %d not found", defender_uid)
            return
        
        if not defender_empire.hex_map:
            log.error("[battle:start_requested] FAIL: defender %d has no map", defender_uid)
            return
        
        # ── Find path from spawnpoint to castle ──────────────
        from gameserver.engine.hex_pathfinding import find_path_from_spawn_to_castle
        tiles = defender_empire.hex_map
        critter_path = find_path_from_spawn_to_castle(tiles)
        
        if not critter_path:
            log.error("[battle:start_requested] FAIL: defender %d map has no valid path",
                      defender_uid)
            return
        
        # ── Get defender's structures ────────────────────────
        # Load structures from hex_map tiles and create Structure objects
        structures_dict = {}
        if defender_empire.structures:
            structures_dict = dict(defender_empire.structures)
        
        # Also load structures from hex_map tiles (for backwards compatibility)
        from gameserver.models.structure import Structure
        from gameserver.models.hex import HexCoord
        structure_sid = 1
        items_dict = svc.upgrade_provider.items if svc.upgrade_provider else {}
        for tile_key, tile_type in tiles.items():
            # Check if tile_type is a structure (not path, castle, etc.)
            if tile_type not in ("empty", "path", "spawnpoint", "castle", "blocked", "void"):
                # This is a structure tile, load stats from item provider
                item = items_dict.get(tile_type)
                if item:
                    # Parse q,r from key "q,r"
                    q, r = map(int, tile_key.split(","))
                    # Create Structure object with stats from item config
                    structure = Structure(
                        sid=structure_sid,
                        iid=tile_type,
                        position=HexCoord(q, r),
                        damage=getattr(item, "damage", 1.0),
                        range=getattr(item, "range", 1),
                        reload_time_ms=getattr(item, "reload_time", 2000.0),
                        shot_speed=getattr(item, "shot_speed", 1.0),
                        shot_type=getattr(item, "shot_type", "normal"),
                        shot_sprite=getattr(item, "shot_sprite", ""),
                        effects=getattr(item, "effects", {}),
                    )
                    structures_dict[structure_sid] = structure
                    structure_sid += 1
                    log.debug("[battle:start_requested] Loaded structure sid=%d iid=%s at (%d,%d)",
                             structure.sid, structure.iid, q, r)
        
        # ── Create BattleState ───────────────────────────────
        bid = _next_bid
        _next_bid += 1
        battle = BattleState(
            bid=bid,
            defender=defender_empire,
            attacker=attacker_empire,
            attack_id=attack_id,
            army=attacking_army,
            structures=structures_dict,
            observer_uids={attacker_uid, defender_uid},
            critter_path=critter_path,
        )
        
        # Register battle in active battles dictionary
        _active_battles[defender_uid] = battle
        
        log.info("[battle:start_requested] SUCCESS: battle %d created (attacker=%d, defender=%d)",
                 bid, attacker_uid, defender_uid)
        
        # ── Send battle_setup to both players ────────────────
        setup_msg = {
            "type": "battle_setup",
            "bid": bid,
            "defender_uid": defender_uid,
            "attacker_uid": attacker_uid,
            "tiles": tiles,  # Defender's hex map
            "structures": [
                {
                    "sid": s.sid,
                    "iid": s.iid,
                    "q": s.position.q,
                    "r": s.position.r,
                    "damage": s.damage,
                    "range": s.range,
                }
                for s in structures_dict.values()
            ],
            "path": [{"q": h.q, "r": h.r} for h in critter_path],            
        }
        
        if svc.server:
            await svc.server.send_to(attacker_uid, setup_msg)
            await svc.server.send_to(defender_uid, setup_msg)
        
        # ── Launch battle loop ───────────────────────────────
        items = svc.upgrade_provider.items if svc.upgrade_provider else {}
        battle_svc = BattleService(items=items)
        
        # Get broadcast interval from game config (default 250ms)
        broadcast_interval_ms = 250.0
        if svc.game_config and hasattr(svc.game_config, 'broadcast_interval_ms'):
            broadcast_interval_ms = svc.game_config.broadcast_interval_ms
        
        async def send_fn(uid: int, data: dict) -> bool:
            if svc.server:
                return await svc.server.send_to(uid, data)
            return False
        
        asyncio.create_task(_run_battle_task(bid, battle, battle_svc, send_fn, broadcast_interval_ms))
    
    # Return a sync handler that schedules the async task
    def sync_handler(event: "BattleStartRequested") -> None:
        asyncio.create_task(_async_create_battle(event))
    
    return sync_handler


async def _on_battle_start_requested(event: "BattleStartRequested") -> None:
    """Event handler: Create and start a battle when an attack transitions to IN_BATTLE.
    
    Called when an attack enters the IN_BATTLE phase after siege completes.
    Builds the battle state from attack data and launches the battle simulation loop.
    
    Args:
        event: BattleStartRequested event with attack_id, attacker_uid, defender_uid, army_aid
    """
    from gameserver.engine.battle_service import BattleService, find_hex_path
    from gameserver.models.battle import BattleState
    
    global _next_bid
    
    svc = _svc()
    attacker_uid = event.attacker_uid
    defender_uid = event.defender_uid
    army_aid = event.army_aid
    attack_id = event.attack_id
    
    log.info("[battle:start_requested] attack_id=%d attacker=%d defender=%d army=%d",
             attack_id, attacker_uid, defender_uid, army_aid)
    
    # Get attacker's army
    attacker_empire = svc.empire_service.get(attacker_uid)
    if attacker_empire is None:
        log.error("[battle:start_requested] FAIL: attacker %d not found", attacker_uid)
        return
    
    attacking_army = None
    for army in attacker_empire.armies:
        if army.aid == army_aid:
            attacking_army = army
            break
    
    if attacking_army is None:
        log.error("[battle:start_requested] FAIL: army %d not found for attacker %d",
                  army_aid, attacker_uid)
        return
    
    # Get defender's empire, map, structures
    defender_empire = svc.empire_service.get(defender_uid)
    if defender_empire is None:
        log.error("[battle:start_requested] FAIL: defender %d not found", defender_uid)
        return
    
    if not defender_empire.hex_map:
        log.error("[battle:start_requested] FAIL: defender %d has no map", defender_uid)
        return
    
    # ── Find path from spawnpoint to castle ──────────────
    from gameserver.engine.hex_pathfinding import find_path_from_spawn_to_castle
    tiles = defender_empire.hex_map
    critter_path = find_path_from_spawn_to_castle(tiles)
    
    if not critter_path:
        log.error("[battle:start_requested] FAIL: defender %d map has no valid path",
                  defender_uid)
        return
    
    # ── Get defender's structures ────────────────────────
    # Load structures from hex_map tiles and create Structure objects
    structures_dict = {}
    if defender_empire.structures:
        structures_dict = dict(defender_empire.structures)
    
    # Also load structures from hex_map tiles (for backwards compatibility)
    from gameserver.models.structure import Structure
    from gameserver.models.hex import HexCoord
    structure_sid = 1
    items_dict = svc.upgrade_provider.items if svc.upgrade_provider else {}
    for tile_key, tile_type in tiles.items():
        # Check if tile_type is a structure (not path, castle, etc.)
        if tile_type not in ("empty", "path", "spawnpoint", "castle", "blocked", "void"):
            # This is a structure tile, load stats from item provider
            item = items_dict.get(tile_type)
            if item:
                # Parse q,r from key "q,r"
                q, r = map(int, tile_key.split(","))
                # Create Structure object with stats from item config
                structure = Structure(
                    sid=structure_sid,
                    iid=tile_type,
                    position=HexCoord(q, r),
                    damage=getattr(item, "damage", 1.0),
                    range=getattr(item, "range", 1),
                    reload_time_ms=getattr(item, "reload_time", 2000.0),
                    shot_speed=getattr(item, "shot_speed", 1.0),
                    shot_type=getattr(item, "shot_type", "normal"),
                    shot_sprite=getattr(item, "shot_sprite", ""),
                    effects=getattr(item, "effects", {}),
                )
                structures_dict[structure_sid] = structure
                structure_sid += 1
                log.debug("[battle:start_requested] Loaded structure sid=%d iid=%s at (%d,%d)",
                         structure.sid, structure.iid, q, r)
    
    # ── Create BattleState ───────────────────────────────
    bid = _next_bid
    _next_bid += 1
    
    battle = BattleState(
        bid=bid,
        defender=defender_empire,
        attacker=attacker_empire,
        army=attacking_army,
        structures=structures_dict,
        observer_uids={attacker_uid, defender_uid},
        critter_path=critter_path,
    )
    
    log.info("[battle:start_requested] SUCCESS: battle %d created (attacker=%d, defender=%d)",
             bid, attacker_uid, defender_uid)
    
    # ── Send battle_setup to both players ────────────────
    setup_msg = {
        "type": "battle_setup",
        "bid": bid,
        "defender_uid": defender_uid,
        "attacker_uid": attacker_uid,
        "tiles": tiles,  # Defender's hex map
        "structures": [
            {
                "sid": s.sid,
                "iid": s.iid,
                "q": s.position.q,
                "r": s.position.r,
                "damage": s.damage,
                "range": s.range,
            }
            for s in structures_dict.values()
        ],
        "path":  [{"q": h.q, "r": h.r} for h in critter_path],
    }
    
    if svc.server:
        await svc.server.send_to(attacker_uid, setup_msg)
        await svc.server.send_to(defender_uid, setup_msg)
    
    # ── Launch battle loop ───────────────────────────────
    items = svc.upgrade_provider.items if svc.upgrade_provider else {}
    battle_svc = BattleService(items=items)
    
    # Get broadcast interval from game config (default 250ms)
    broadcast_interval_ms = 250.0
    if svc.game_config and hasattr(svc.game_config, 'broadcast_interval_ms'):
        broadcast_interval_ms = svc.game_config.broadcast_interval_ms
    
    async def send_fn(uid: int, data: dict) -> bool:
        if svc.server:
            return await svc.server.send_to(uid, data)
        return False
    
    asyncio.create_task(_run_battle_task(bid, battle, battle_svc, send_fn, broadcast_interval_ms))


# ===================================================================
# Registration — THE central place to add all handlers
# ===================================================================

def register_all_handlers(services: Services) -> None:
    """Register all message handlers on the router.

    Called once during startup from ``main.py``.
    To add a new handler, add a ``router.register(...)`` line below.

    Args:
        services: Fully initialized Services container.
    """
    global _services
    _services = services

    router = services.router

    # -- Connection / Keepalive ------------------------------------------
    router.register("ping", handle_ping)

    # -- Empire queries --------------------------------------------------
    router.register("summary_request", handle_summary_request)
    router.register("item_request", handle_item_request)
    router.register("military_request", handle_military_request)

    # -- Map (Composer) --------------------------------------------------
    router.register("map_load_request", handle_map_load_request)
    router.register("map_save_request", handle_map_save_request)

    # -- Building / Research (fire-and-forget) ---------------------------
    router.register("new_item", handle_new_item)
    router.register("new_structure", handle_new_structure)
    router.register("delete_structure", handle_delete_structure)
    router.register("upgrade_structure", handle_upgrade_structure)

    # -- Citizens / Life (fire-and-forget) -------------------------------
    router.register("citizen_upgrade", handle_citizen_upgrade)
    router.register("change_citizen", handle_change_citizen)
    router.register("increase_life", handle_increase_life)

    # -- Military (fire-and-forget) --------------------------------------
    router.register("new_army", handle_new_army)
    router.register("new_attack_request", handle_new_attack)
    router.register("change_army", handle_change_army)
    router.register("new_wave", handle_new_wave)
    router.register("change_wave", handle_change_wave)
    router.register("end_siege", handle_end_siege)

    # -- Battle ----------------------------------------------------------
    router.register("battle_register", handle_battle_register)
    router.register("battle_unregister", handle_battle_unregister)
    router.register("battle_next_wave_request", handle_battle_next_wave)

    # -- Battle event handlers (internal) --------------------------------
    from gameserver.util.events import BattleStartRequested, AttackPhaseChanged, BattleObserverBroadcast
    if services.event_bus:
        services.event_bus.on(BattleStartRequested, _create_battle_start_handler())
        services.event_bus.on(AttackPhaseChanged, _create_attack_phase_handler())
        services.event_bus.on(BattleObserverBroadcast, _create_battle_observer_broadcast_handler())

    # -- Social / Messaging ----------------------------------------------
    router.register("notification_request", handle_notification_request)
    router.register("user_message", handle_user_message)
    router.register("timeline_request", handle_timeline_request)

    # -- User Info / Hall of Fame ----------------------------------------
    router.register("userinfo_request", handle_userinfo_request)
    router.register("hall_of_fame_request", handle_hall_of_fame)

    # -- Preferences -----------------------------------------------------
    router.register("preferences_request", handle_preferences_request)
    router.register("change_preferences", handle_change_preferences)

    # -- Auth / Account --------------------------------------------------
    router.register("auth_request", handle_auth_request)
    router.register("signup", handle_signup)
    router.register("create_empire", handle_create_empire)

    registered = router.registered_types
    log.info("Registered %d message handlers: %s", len(registered), ", ".join(registered))
