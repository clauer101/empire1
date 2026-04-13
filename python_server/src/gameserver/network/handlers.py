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
from typing import Any, Callable, Iterable, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from gameserver.main import Services

from gameserver.models.messages import GameMessage, MapSaveRequest
from gameserver.models.attack import AttackPhase, Attack
from gameserver.util import effects as fx

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

def _tile_type(v) -> str:
    """Extract tile type from a string or dict tile value."""
    return v if isinstance(v, str) else v.get('type', 'empty')


def _tile_select(v, item_default: str = 'first') -> str:
    """Return per-tile select override, or fall back to the item-level default."""
    if isinstance(v, dict):
        return v.get('select', item_default)
    return item_default


def _has_path_from_spawn_to_castle(tiles) -> bool:
    """Check if there's a path from any spawnpoint to the castle.

    Uses the centralized pathfinding logic from hex_pathfinding module.

    Args:
        tiles: Dict of {"q,r": tile_value} where tile_value is a type string
               or a dict {"type": ..., "select": ...}.

    Returns:
        True if at least one path exists, False otherwise.
    """
    from gameserver.engine.hex_pathfinding import find_path_from_spawn_to_castle
    normalized = {k: _tile_type(v) for k, v in tiles.items()}
    return find_path_from_spawn_to_castle(normalized) is not None


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
            "image": item.image,
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
            "image": item.image,
        }

    # Structures (towers) — available based on research
    structures = {}
    for item in up.available_items(ItemType.STRUCTURE, completed):
        structures[item.iid] = {
            "name": item.name,
            "description": item.description,
            "costs": dict(item.costs),
            "damage": item.damage,
            "range": item.range,
            "reload_time_ms": item.reload_time_ms,
            "shot_speed": item.shot_speed,
            "shot_type": item.shot_type,
            "select": item.select,
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
            "health": item.health,
            "speed": item.speed,
            "armour": item.armour,
            "damage": item.critter_damage,
            "slots": item.slots,
            "is_boss": item.is_boss,
        }

    # Full catalog — ALL items regardless of requirements, used by client
    # for "Required for" reverse-dependency mapping across the entire tech tree.
    catalog = {}
    for item in up.items.values():
        entry: dict[str, Any] = {
            "name": item.name,
            "item_type": item.item_type.value,
            "requirements": list(item.requirements),
        }
        if item.item_type == ItemType.STRUCTURE:
            entry.update({
                "damage": item.damage,
                "range": item.range,
                "reload_time_ms": item.reload_time_ms,
                "costs": dict(item.costs),
                "effects": dict(item.effects),
                "description": item.description,
                "sprite": item.sprite,
                "select": item.select,
            })
        elif item.item_type == ItemType.CRITTER:
            entry.update({
                "health": item.health,
                "speed": item.speed,
                "armour": item.armour,
                "damage": item.critter_damage,
                "slots": item.slots,
                "is_boss": item.is_boss,
            })
        elif item.item_type == ItemType.KNOWLEDGE:
            entry.update({
                "effort": item.effort,
                "effects": dict(item.effects),
                "description": item.description,
                "image": item.image,
            })
        elif item.item_type == ItemType.BUILDING:
            entry.update({
                "effort": item.effort,
                "costs": dict(item.costs),
                "effects": dict(item.effects),
                "description": item.description,
                "image": item.image,
            })
        catalog[item.iid] = entry

    return {
        "type": "item_response",
        "buildings": buildings,
        "knowledge": knowledge,
        "structures": structures,
        "critters": critters,
        "catalog": catalog,
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
                "next_slot_price": round(svc.empire_service._critter_slot_price(wave.slots + 1), 2),
            })
        
        army_wave_count = len(army.waves)
        armies.append({
            "aid": army.aid,
            "name": army.name,
            "waves": waves,
            "next_wave_price": round(svc.empire_service._wave_price(army_wave_count + 1), 2),
        })

    # Get available critters based on completed research AND buildings
    completed: set[str] = set()
    for iid, remaining in empire.buildings.items():
        if remaining <= 0:
            completed.add(iid)
    for iid, remaining in empire.knowledge.items():
        if remaining <= 0:
            completed.add(iid)
    
    available_critters = []
    for critter in svc.upgrade_provider.available_critters(completed):
        available_critters.append({
            "iid": critter.iid,
            "name": critter.name,
            "slots": critter.slots,
            "health": critter.health,
            "armour": critter.armour,
            "speed": critter.speed,
            "time_between_ms": critter.time_between_ms,
            "is_boss": critter.is_boss,
            "animation": critter.animation,
            "sprite": critter.sprite,
        })

    # Sprite lookup for all critters (including locked) so the frontend
    # can render sprites for critters already placed in waves.
    from gameserver.models.items import ItemType as _ItemType2
    critter_sprites = {
        c.iid: {"sprite": c.sprite, "animation": c.animation}
        for c in svc.upgrade_provider.get_by_type(_ItemType2.CRITTER)
    } if svc.upgrade_provider else {}

    # Ongoing attacks
    _uid_to_username: dict[int, str] = {}
    if svc.database is not None:
        for _urow in await svc.database.list_users():
            _uid_to_username[_urow["uid"]] = _urow["username"]

    def _attack_dto(a):
        _att_emp = svc.empire_service.get(a.attacker_uid)
        _army_name = ""
        if _att_emp:
            for _arm in _att_emp.armies:
                if _arm.aid == a.army_aid:
                    _army_name = _arm.name
                    break
        return {
            "attack_id": a.attack_id,
            "attacker_uid": a.attacker_uid,
            "defender_uid": a.defender_uid,
            "army_aid": a.army_aid,
            "army_name": _army_name,
            "attacker_username": _uid_to_username.get(a.attacker_uid, ""),
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
        "critter_sprites": critter_sprites,
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


async def handle_set_structure_select(
    message: GameMessage, sender_uid: int,
) -> Optional[dict[str, Any]]:
    """Update targeting strategy for a tower.

    Updates the live BattleState structure immediately (if a battle is active)
    and persists the value into empire.hex_map so it survives the next save.
    Only the defender (map owner) is allowed to change targeting.
    """
    select_val = getattr(message, 'select', 'first')
    if select_val not in ('first', 'last', 'random'):
        return None
    hex_q = getattr(message, 'hex_q', 0)
    hex_r = getattr(message, 'hex_r', 0)

    # Only the defender may change tower targeting.
    # Active battles are keyed by defender_uid, so this lookup implicitly
    # verifies that sender_uid is the defender.
    battle = _active_battles.get(sender_uid)
    # Also reject if a battle is active for this map but sender is NOT the defender.
    # (An attacker's uid would not be a key in _active_battles for their own attack.)
    # Additionally guard the hex_map persistence below so only the map owner is updated.
    svc = _svc()
    empire = svc.empire_service.get(sender_uid)
    if empire is None or empire.hex_map is None:
        log.warning("set_structure_select: sender %d has no empire/map — rejected", sender_uid)
        return None
    if battle:
        for s in battle.structures.values():
            if s.position.q == hex_q and s.position.r == hex_r:
                s.select = select_val
                break

    # Persist to hex_map so next battle starts with the correct select
    tile_key = f"{hex_q},{hex_r}"
    tile_val = empire.hex_map.get(tile_key)
    if tile_val is not None:
        tile_type = _tile_type(tile_val)
        if select_val == 'first':
            empire.hex_map[tile_key] = tile_type
        else:
            empire.hex_map[tile_key] = {'type': tile_type, 'select': select_val}

    return None  # fire-and-forget


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
    
    # Get globally unique army ID
    new_aid = svc.empire_service.next_army_id()
    
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
                    "critter_slot_cost": item.slots if item else 1,
                    "next_critter_ms": max(0.0, w.next_critter_ms),
                }
                break

    # Resolve attacker username from DB
    attacker_username = ""
    if svc.database is not None:
        for _urow3 in await svc.database.list_users():
            if _urow3["uid"] == attack.attacker_uid:
                attacker_username = _urow3["username"]
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
        "attacker_army_name": attacking_army.name if attacking_army else "",
        "attacker_username": attacker_username,
        "time_since_start_s": time_since_start_s,
        "wave_info": wave_info,
        "defender_era": svc.empire_service.get_current_era(defender_empire),
    }
    
    if svc.server:
        await svc.server.send_to(observer_uid, status_msg)


async def _send_battle_setup_to_observer(attack: Attack, observer_uid: int) -> None:
    """Send battle_setup message to initialize the battle view.
    
    This includes the defender's map, structures, and paths.
    """
    from gameserver.engine.hex_pathfinding import find_path_from_spawn_to_castle
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

    tiles = defender_empire.hex_map

    # Compute path using the canonical pathfinder (traverses empty, path, spawnpoint, castle)
    normalized = {k: _tile_type(v) for k, v in tiles.items()}
    computed_path = find_path_from_spawn_to_castle(normalized)
    hex_path = computed_path if computed_path else []
    
    # ── Get structures ───────────────────────────────────
    # Load structures from hex_map tiles and create Structure objects
    structures_dict = {}
    if defender_empire.structures:
        structures_dict = dict(defender_empire.structures)
    
    # Also load structures from hex_map tiles (for backwards compatibility)
    from gameserver.models.structure import Structure, structure_from_item
    from gameserver.models.hex import HexCoord
    structure_sid = 1
    items_dict = svc.upgrade_provider.items if svc.upgrade_provider else {}
    for tile_key, tile_val in tiles.items():
        # Check if tile_type is a structure (not path, castle, etc.)
        tile_type = _tile_type(tile_val)
        if tile_type not in ("empty", "path", "spawnpoint", "castle", "blocked", "void"):
            # This is a structure tile, load stats from item provider
            item = items_dict.get(tile_type)
            if item:
                # Parse q,r from key "q,r"
                q, r = map(int, tile_key.split(","))
                # Create Structure object with stats from item config
                structure = structure_from_item(
                    sid=structure_sid, iid=tile_type, position=HexCoord(q, r),
                    item=item, select_override=_tile_select(tile_val, getattr(item, "select", "first")),
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
                "select": s.select,
            }
            for s in structures_dict.values()
        ],
        "path": [{"q": h.q, "r": h.r} for h in hex_path],
    }
    
    if svc.server:
        await svc.server.send_to(observer_uid, setup_msg)
        log.info("_send_battle_setup: sent to uid=%d (attack_id=%d)", observer_uid, attack.attack_id)


def _evict_observer_from_all(
    uid: int,
    all_attacks: "Iterable[Attack]",
    active_battles: "dict[int, BattleState]",
    exclude_attack_id: "int | None" = None,
) -> None:
    """Remove *uid* from every attack's ``_observers`` set and every active
    ``BattleState.observer_uids`` set, except for the attack identified by
    *exclude_attack_id* (the one the user is about to subscribe to).

    This guarantees that each UID is subscribed to at most one battle at a time
    — new subscriptions silently replace old ones.
    """
    for a in all_attacks:
        if a.attack_id == exclude_attack_id:
            continue
        if hasattr(a, '_observers') and uid in a._observers:
            a._observers.discard(uid)
            log.debug("_evict_observer_from_all: uid=%d removed from attack %d observers", uid, a.attack_id)

    for defender_uid, battle in active_battles.items():
        if exclude_attack_id is not None and battle.attack_id == exclude_attack_id:
            continue
        if uid in battle.observer_uids:
            battle.observer_uids.discard(uid)
            log.debug("_evict_observer_from_all: uid=%d removed from battle bid=%d observer_uids", uid, battle.bid)


async def handle_battle_register(
    message: GameMessage, sender_uid: int,
) -> Optional[dict[str, Any]]:
    """Handle ``battle_register`` — register as battle observer.
    
    Client subscribes to battle updates for attacks they're involved in.
    """
    target_uid = getattr(message, "target_uid", None)
    attack_id = getattr(message, "attack_id", None)
    if target_uid is None:
        log.warning("battle_register: missing target_uid")
        return {"type": "error", "message": "Missing target_uid"}
    
    svc = _svc()
    
    # Find attack involving this target_uid (either as attacker or defender)
    attack_svc = svc.attack_service
    attack = None
    
    ACTIVE_PHASES = {"in_siege", "in_battle"}

    # If a specific attack_id is provided, use it directly
    if attack_id is not None:
        for a in attack_svc.get_incoming(sender_uid):
            if a.attack_id == attack_id:
                attack = a
                break
        if not attack:
            for a in attack_svc.get_outgoing(sender_uid):
                if a.attack_id == attack_id:
                    attack = a
                    break

    # Fallback: pick by target_uid
    if not attack:
        # Check if sender is attacker
        for a in attack_svc.get_outgoing(sender_uid):
            if a.defender_uid == target_uid:
                if attack is None or a.phase.value in ACTIVE_PHASES:
                    attack = a

        # Check if sender is defender
        if not attack:
            for a in attack_svc.get_incoming(sender_uid):
                if a.attacker_uid == target_uid or a.defender_uid == sender_uid:
                    if attack is None or a.phase.value in ACTIVE_PHASES:
                        attack = a
    
    if not attack:
        log.warning("battle_register: no attack found for uid=%d target=%d", sender_uid, target_uid)
        return {"type": "error", "message": "No active attack found"}

    # Evict sender_uid from all other subscriptions before registering the new one.
    # This ensures each UID is observing at most one attack / battle at a time.
    _evict_observer_from_all(sender_uid, attack_svc.get_all_attacks(), _active_battles, exclude_attack_id=attack.attack_id)

    # Register observer
    if not hasattr(attack, '_observers'):
        attack._observers = set()
    attack._observers.add(sender_uid)

    # Also add to the active BattleState so _broadcast() delivers updates
    battle = _active_battles.get(attack.defender_uid)
    if battle:
        battle.observer_uids.add(sender_uid)

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
            # Also remove from active BattleState
            battle = _active_battles.get(attack.defender_uid)
            if battle:
                battle.observer_uids.discard(sender_uid)
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
        _att_emp = svc.empire_service.get(a.attacker_uid)
        _army_name = ""
        if _att_emp:
            for _arm in _att_emp.armies:
                if _arm.aid == a.army_aid:
                    _army_name = _arm.name
                    break
        return {
            "attack_id": a.attack_id,
            "attacker_uid": a.attacker_uid,
            "defender_uid": a.defender_uid,
            "army_aid": a.army_aid,
            "army_name": _army_name,
            "attacker_username": "",  # resolved client-side from empires list
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
        "base_build_speed": svc.empire_service._base_build_speed,
        "base_research_speed": svc.empire_service._base_research_speed,
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
        "travel_time_seconds": round(max(1.0, svc.attack_service._era_travel_offset(empire) + empire.get_effect("travel_offset", 0.0)), 0),
        "current_era": svc.empire_service.get_current_era(empire),
    }


def _create_empire_for_new_user(uid: int, username: str, empire_name: str) -> None:
    """Create and register a fresh Empire for a newly signed-up user.

    Starting resources and max_life are taken from game_config so that
    changes to game.yaml are reflected without touching handler code.
    Called by both the WebSocket handler and the REST signup endpoint.
    """
    from gameserver.models.empire import Empire
    svc = _svc()
    starting_res = dict(svc.game_config.starting_resources) if svc.game_config else {"gold": 0.0, "culture": 0.0, "life": 10.0}
    starting_max_life = svc.game_config.starting_max_life if svc.game_config else 10.0
    empire = Empire(
        uid=uid,
        name=empire_name or f"{username}'s Empire",
        buildings={"INIT": 0.0},
        resources=starting_res,
        max_life=starting_max_life,
        hex_map={
            "0,0": "castle",
            "0,1": "spawnpoint",
            "1,0": "empty",
        },
    )
    svc.empire_service.register(empire)


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
        _create_empire_for_new_user(result, username, empire_name)
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

    # Compute and return the path so the client never needs to pathfind itself
    from gameserver.engine.hex_pathfinding import find_path_from_spawn_to_castle
    normalized = {k: _tile_type(v) for k, v in hex_map.items()}
    computed_path = find_path_from_spawn_to_castle(normalized)
    path_data = [[c.q, c.r] for c in computed_path] if computed_path else None

    return {
        "type": "map_load_response",
        "tiles": hex_map,
        "path": path_data,
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
    
    # Safety guard: reject if sender is currently observing someone else's battle.
    # This prevents accidental (or malicious) overwrite of the sender's own map
    # with foreign tile data loaded during spectating.
    for _b in _active_battles.values():
        if (
            sender_uid in _b.observer_uids
            and _b.defender is not None
            and _b.defender.uid != sender_uid
        ):
            log.warning(
                "[map_save] Rejected: uid=%d is currently observing battle bid=%d (defender=%d)",
                sender_uid, _b.bid, _b.defender.uid,
            )
            return {
                "type": "map_save_response",
                "success": False,
                "error": "Cannot save map while spectating another battle",
            }

    # Get tiles from typed message model
    raw_tiles = message.tiles or {}

    # Normalize: accept both {"0,0": "type"} and {"0,0": {"type": ..., "select": ...}}
    # Per-tile select overrides are kept when they differ from the default "first".
    tiles = {}
    for k, v in raw_tiles.items():
        if isinstance(v, dict):
            tile_type = v.get('type', 'empty')
            select_val = v.get('select', 'first')
            tiles[k] = {'type': tile_type, 'select': select_val} if select_val != 'first' else tile_type
        else:
            tiles[k] = v

    # -- Validation --------------------------------------------------
    type_counts: dict[str, int] = {}
    for v in tiles.values():
        t = _tile_type(v)
        type_counts[t] = type_counts.get(t, 0) + 1

    castle_count = type_counts.get('castle', 0)
    spawnpoint_count = type_counts.get('spawnpoint', 0)
    errors: list[str] = []

    if castle_count > 1:
        errors.append(
            f"Map must contain at most 1 castle (found {castle_count})"
        )
    if castle_count == 0:
        errors.append("Kein Castle platziert")
    if spawnpoint_count == 0:
        errors.append("Kein Spawnpoint platziert")

    # Void tiles must not be overwritten
    old_tiles_for_void = empire.hex_map or {}
    for tile_key, tile_val in tiles.items():
        if _tile_type(tile_val) != 'void' and _tile_type(old_tiles_for_void.get(tile_key, '')) == 'void':
            errors.append(f"Cannot place '{_tile_type(tile_val)}' on a void tile at {tile_key}")
            break
    
    # Check path connectivity (only when both castle and spawnpoint exist)
    if not errors and not _has_path_from_spawn_to_castle(tiles):
        errors.append("Weg verbaut – kein Pfad vom Spawnpoint zum Castle")

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

    # -- Reject new structures on the active critter path during battle --
    battle = _active_battles.get(target_uid)
    if battle is not None and battle.critter_path:
        path_keys = {f"{c.q},{c.r}" for c in battle.critter_path}
        old_tiles = empire.hex_map or {}
        from gameserver.models.items import ItemType as _ItemType
        structure_iids_check = {
            item.iid
            for item in svc.upgrade_provider.get_by_type(_ItemType.STRUCTURE)
        }
        for tile_key, tile_val in tiles.items():
            tile_type = _tile_type(tile_val)
            if tile_key in path_keys and tile_type in structure_iids_check:
                old_type = _tile_type(old_tiles.get(tile_key, ''))
                if old_type != tile_type:
                    return {
                        "type": "map_save_response",
                        "success": False,
                        "error": f"Cannot place tower on active critter path at {tile_key}",
                    }

    # -- Structure cost check ----------------------------------------
    from gameserver.models.items import ItemType as _ItemType
    structure_iids = {
        item.iid
        for item in svc.upgrade_provider.get_by_type(_ItemType.STRUCTURE)
    }
    old_tiles = empire.hex_map or {}
    total_gold_cost = 0.0
    for tile_key, tile_val in tiles.items():
        tile_type = _tile_type(tile_val)
        if tile_type in structure_iids:
            old_type = _tile_type(old_tiles.get(tile_key, ''))
            if old_type != tile_type:
                # New or changed structure tile — charge placement cost
                item = svc.upgrade_provider.get(tile_type)
                if item:
                    total_gold_cost += item.costs.get("gold", 0.0)
    if total_gold_cost > 0:
        current_gold = empire.resources.get("gold", 0.0)
        if current_gold < total_gold_cost:
            return {
                "type": "map_save_response",
                "success": False,
                "error": f"Not enough gold (need {total_gold_cost:.0f}, have {current_gold:.0f})",
            }
        empire.resources["gold"] -= total_gold_cost
        log.info(
            "Empire %d: deducted %.0f gold for new structure placement",
            target_uid, total_gold_cost,
        )

    # -- Sell refund: structures removed in this save ----------------
    cfg = svc.empire_service._gc if hasattr(svc.empire_service, '_gc') else None
    base_refund = getattr(cfg, 'tower_sell_refund', 0.3) if cfg else 0.3
    refund_modifier = empire.get_effect("tower_sell_refund_modifier", 0.0)
    refund_rate = base_refund * (1.0 + refund_modifier)
    total_refund = 0.0
    for tile_key, old_val in old_tiles.items():
        old_type = _tile_type(old_val)
        if old_type in structure_iids:
            new_type = _tile_type(tiles.get(tile_key, 'empty'))
            if new_type != old_type:
                # Structure was removed or replaced — refund for removal
                item = svc.upgrade_provider.get(old_type)
                if item:
                    total_refund += item.costs.get("gold", 0.0) * refund_rate
    if total_refund > 0:
        empire.resources["gold"] = empire.resources.get("gold", 0.0) + total_refund
        log.info(
            "Empire %d: refunded %.0f gold for sold structures (rate=%.0f%%)",
            target_uid, total_refund, refund_rate * 100,
        )

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
                        "select": s.select,
                    }
                    for s in battle.structures.values()
                ],
            }
            if svc.server:
                import asyncio
                for uid in battle.observer_uids:
                    asyncio.create_task(svc.server.send_to(uid, structure_update_msg))

    # Return the path for the client to display.
    # During an active battle the critter path is fixed — return battle.critter_path
    # so the displayed path never changes while critters are moving.
    # Outside of battle, recompute from the saved tiles.
    if battle is not None and battle.critter_path:
        path_data = [[c.q, c.r] for c in battle.critter_path]
    else:
        from gameserver.engine.hex_pathfinding import find_path_from_spawn_to_castle
        computed_path = find_path_from_spawn_to_castle({k: _tile_type(v) for k, v in tiles.items()})
        path_data = [[c.q, c.r] for c in computed_path] if computed_path else None

    return {
        "type": "map_save_response",
        "success": True,
        "path": path_data,
        "tiles": empire.hex_map,
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
    
    # Calculate cost based on waves in this specific army
    wave_price = svc.empire_service._wave_price(len(army.waves) + 1)
    
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
    from gameserver.models.structure import Structure, structure_from_item
    from gameserver.models.hex import HexCoord

    NON_STRUCTURE = {"empty", "path", "spawnpoint", "castle", "blocked", "void"}

    # Build lookup: (q, r) → existing Structure
    pos_to_struct: dict[tuple[int, int], Structure] = {
        (s.position.q, s.position.r): s for s in battle.structures.values()
    }

    # Build lookup: (q, r) → tile_value for all structure tiles in new map
    new_pos_types: dict[tuple[int, int], tuple[str, str]] = {}
    for tile_key, tile_val in tiles.items():
        tile_type = _tile_type(tile_val)
        if tile_type not in NON_STRUCTURE:
            q, r = map(int, tile_key.split(","))
            new_pos_types[(q, r)] = (tile_type, _tile_select(tile_val))

    # Remove structures whose tile was removed or replaced
    sids_to_remove = [
        s.sid for s in battle.structures.values()
        if (s.position.q, s.position.r) not in new_pos_types
           or new_pos_types[(s.position.q, s.position.r)][0] != s.iid
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

    for (q, r), (tile_type, tile_select) in new_pos_types.items():
        if (q, r) in existing_pos:
            continue  # Already present and correct iid
        item = items_dict.get(tile_type)
        if not item:
            continue
        structure = structure_from_item(
            sid=next_sid, iid=tile_type, position=HexCoord(q, r),
            item=item, select_override=tile_select,
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
    5. Logs AI_ATTACK outcome and adapts AI parameters (if AI-initiated)
    6. Cleans up the battle from active battles
    """
    svc = _svc()
    _summary_sent = False

    try:
        await battle_svc.run_battle(battle, send_fn, broadcast_interval_ms)
    except asyncio.TimeoutError:
        import traceback
        log.error("[battle] bid=%d asyncio.TimeoutError (unexpected): %s", bid, traceback.format_exc())
        battle.defender_won = True
        battle.is_finished = True
        try:
            await battle_svc.send_summary(battle, send_fn, loot={})
            _summary_sent = True
        except Exception:
            pass
    except Exception:
        import traceback
        log.error("Battle loop crashed: %s", traceback.format_exc())

        # ── Crash recovery ────────────────────────────────────────────────
        # Treat crash as defender win so the attacker doesn't get stuck.
        battle.defender_won = True
        battle.is_finished = True

        # Reset the attacking army waves so the attacker can re-use it
        # (only for human players — AI armies are cleaned up below anyway).
        from gameserver.engine.ai_service import AI_UID as _AI_UID
        if battle.army is not None and (battle.attacker is None or battle.attacker.uid != _AI_UID):
            for wave in battle.army.waves:
                wave.num_critters_spawned = 0
                wave.next_critter_ms = 0
            log.info("[battle] bid=%d army '%s' reset after crash", bid, battle.army.name)

        # Best-effort summary to connected clients
        try:
            await battle_svc.send_summary(battle, send_fn, loot={})
            _summary_sent = True
        except Exception:
            pass

    # ── Post-battle cleanup (runs whether crashed or not) ─────────────────
    try:
        log.info("[battle] bid=%d complete: attacker_wins=%s", bid, not battle.defender_won)

        loot: dict = {}
        if battle.defender_won is False:
            loot = _compute_and_apply_loot(battle, svc)
            await battle_svc.send_summary(battle, send_fn, loot)
        elif not _summary_sent:
            # Normal defender-win path (no loot to send)
            await battle_svc.send_summary(battle, send_fn, loot={})

        from gameserver.models.attack import AttackPhase
        attack = svc.attack_service.get(battle.attack_id)
        if attack:
            attack.phase = AttackPhase.FINISHED
            log.info("[battle] Attack %d marked as FINISHED (bid=%d)", battle.attack_id, bid)
        else:
            log.warning("[battle] Could not find attack_id=%d to mark FINISHED (bid=%d)", battle.attack_id, bid)

        # ── Reset army waves so attacker can re-use the army ─────────────
        from gameserver.engine.ai_service import AI_UID
        if battle.army is not None and (battle.attacker is None or battle.attacker.uid != AI_UID):
            for wave in battle.army.waves:
                wave.num_critters_spawned = 0
                wave.next_critter_ms = 0
            log.info("[battle] bid=%d army '%s' waves reset after battle end", bid, battle.army.name)

        if (svc.ai_service is not None
                and battle.attacker is not None
                and battle.attacker.uid == AI_UID
                and battle.attack_id is not None):
            svc.ai_service.on_battle_result(battle.attack_id, battle)

        if svc.ai_service is not None:
            svc.ai_service.cleanup_inactive_armies(svc.empire_service, svc.attack_service)

        # ── Save replay + send notification messages ─────────────────
        if battle.recorder is not None:
            saved_path = battle.recorder.save()
            replay_key = battle.recorder.replay_key
            if saved_path and svc.database:
                def_name  = battle.defender.name if battle.defender else "?"
                atk_name  = battle.attacker.name if battle.attacker else "?"
                army_name = battle.army.name if battle.army else "?"
                num_waves = len(battle.army.waves) if battle.army and battle.army.waves else 0
                dur_s = battle.elapsed_ms / 1000
                dur_m, dur_sec = int(dur_s // 60), int(dur_s % 60)
                dur_str = f"{dur_m}m {dur_sec}s" if dur_m > 0 else f"{dur_sec}s"
                defender_won = bool(battle.defender_won)

                # Attacker gains summary (skip for AI attacker uid=0)
                gains_lines = ""
                if battle.attacker and battle.attacker.uid != 0:
                    gains = battle.attacker_gains.get(battle.attacker.uid, {})
                    if gains:
                        parts = ", ".join(f"+{int(v)} {k}" for k, v in gains.items() if v > 0)
                        if parts:
                            gains_lines = f"💰 Captured: {parts}\n"

                # Loot lines (culture + knowledge stolen)
                loot_atk_lines = ""
                loot_def_lines = ""
                if loot:
                    culture_stolen = loot.get("culture", 0.0)
                    knowledge_loot = loot.get("knowledge")
                    if culture_stolen > 0:
                        loot_atk_lines += f"🎭 Stolen culture:    +{culture_stolen:.1f}\n"
                        loot_def_lines += f"🎭 Culture stolen:    -{culture_stolen:.1f}\n"
                    if knowledge_loot:
                        k_name = knowledge_loot.get("name", knowledge_loot.get("iid", "?"))
                        k_pct  = knowledge_loot.get("pct", 0.0) * 100
                        loot_atk_lines += f"📚 Stolen knowledge: {k_name} ({k_pct:.0f}%)\n"
                        loot_def_lines += f"📚 Knowledge stolen: {k_name} ({k_pct:.0f}%)\n"

                # ── Defender message ──────────────────────────────────────
                def_result = "🛡 You Won!" if defender_won else "💀 You Lost!"
                def_body = (
                    f"{def_result}\n"
                    f"────────────────────\n"
                    f"⚔ Attacker:  {atk_name}\n"
                    f"📋 Army:      {army_name} ({num_waves} waves)\n"
                    f"────────────────────\n"
                    f"🐛 Spawned:   {battle.critters_spawned}\n"
                    f"💀 Killed:    {battle.critters_killed}\n"
                    f"🏰 Reached:   {battle.critters_reached}\n"
                    f"🗼 Towers:    {len(battle.structures)}\n"
                    f"💰 Earned:    +{int(battle.defender_gold_earned)} gold\n"
                    f"{loot_def_lines}"
                    f"⏱ Duration:  {dur_str}\n"
                    f"────────────────────\n"
                    f"▶ Replay: #replay/{replay_key}"
                )

                # ── Attacker message ──────────────────────────────────────
                atk_result = "⚔ You Won!" if not defender_won else "💀 You Lost!"
                atk_body = (
                    f"{atk_result}\n"
                    f"────────────────────\n"
                    f"🛡 Defender:  {def_name}\n"
                    f"📋 Army:      {army_name} ({num_waves} waves)\n"
                    f"────────────────────\n"
                    f"🐛 Spawned:   {battle.critters_spawned}\n"
                    f"💀 Killed:    {battle.critters_killed}\n"
                    f"🏰 Reached:   {battle.critters_reached}\n"
                    f"{gains_lines}"
                    f"{loot_atk_lines}"
                    f"⏱ Duration:  {dur_str}\n"
                    f"────────────────────\n"
                    f"▶ Replay: #replay/{replay_key}"
                )

                if battle.defender:
                    await svc.database.send_message(0, battle.defender.uid, def_body)
                if battle.attacker and battle.attacker.uid != 0:
                    await svc.database.send_message(0, battle.attacker.uid, atk_body)

    except Exception:
        import traceback
        log.error("[battle] bid=%d post-battle cleanup crashed: %s", bid, traceback.format_exc())
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
        # Credit attacker: reduce remaining research effort for the stolen item.
        # The attacker may not have the item in their knowledge dict yet (that's
        # why it was stealable); initialise it to full effort then subtract gain.
        attacker_remaining = attacker.knowledge.get(chosen_iid, effort)
        attacker.knowledge[chosen_iid] = max(0.0, attacker_remaining - gain)
        # Penalise defender: stolen effort is added back on top of what remains.
        # If already completed (remaining=0), this re-opens it.
        current_remaining = defender.knowledge.get(chosen_iid, 0.0)
        defender.knowledge[chosen_iid] = current_remaining + gain
        loot["knowledge"] = {
            "iid": chosen_iid,
            "name": item.name if item else chosen_iid,
            "pct": round(pct * 100, 1),
            "amount": round(gain, 1),
        }
        log.info(
            "[LOOT] Knowledge stolen from uid=%d: %s (%.1f%% of effort %.0f = %.1f) "
            "— attacker uid=%d remaining %.1f, defender remaining now %.1f",
            defender.uid, chosen_iid, pct * 100, effort, gain,
            attacker.uid, attacker.knowledge[chosen_iid], defender.knowledge[chosen_iid],
        )
    
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


def _create_item_completed_handler() -> Callable:
    """Push an item_completed message to the owning player when a build/research finishes."""
    async def _async_item_completed(event: "ItemCompleted") -> None:
        svc = _svc()
        if svc.server:
            await svc.server.send_to(event.empire_uid, {
                "type": "item_completed",
                "iid": event.iid,
            })
            log.debug("[push] item_completed iid=%s uid=%d", event.iid, event.empire_uid)

    def _on_item_completed(event: "ItemCompleted") -> None:
        import asyncio
        asyncio.create_task(_async_item_completed(event))

    return _on_item_completed


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


def _abort_battle_setup(attack_id: int, army=None) -> None:
    """Mark an attack FINISHED when battle creation fails.

    Ensures the attack is never left dangling in IN_BATTLE when the battle
    loop never starts (e.g. defender has no map, no valid path).
    Also resets army waves so the attacker can reuse the army.
    """
    from gameserver.models.attack import AttackPhase
    svc = _svc()
    attack = svc.attack_service.get(attack_id)
    if attack:
        attack.phase = AttackPhase.FINISHED
        log.warning(
            "[battle:abort] attack_id=%d marked FINISHED because battle setup failed",
            attack_id,
        )
    if army is not None:
        for wave in army.waves:
            wave.num_critters_spawned = 0
            wave.next_critter_ms = 0
        log.info("[battle:abort] army waves reset for attack_id=%d", attack_id)


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
            _abort_battle_setup(attack_id)
            return
        
        attacking_army = None
        for army in attacker_empire.armies:
            if army.aid == army_aid:
                attacking_army = army
                break
        
        if attacking_army is None:
            log.error("[battle:start_requested] FAIL: army %d not found for attacker %d",
                      army_aid, attacker_uid)
            _abort_battle_setup(attack_id)
            return
        
        # Get defender's empire, map, structures
        defender_empire = svc.empire_service.get(defender_uid)
        if defender_empire is None:
            log.error("[battle:start_requested] FAIL: defender %d not found", defender_uid)
            _abort_battle_setup(attack_id, attacking_army)
            return
        
        if not defender_empire.hex_map:
            log.error("[battle:start_requested] FAIL: defender %d has no map", defender_uid)
            _abort_battle_setup(attack_id, attacking_army)
            return
        
        # ── Find path from spawnpoint to castle ──────────────
        from gameserver.engine.hex_pathfinding import find_path_from_spawn_to_castle
        tiles = defender_empire.hex_map
        critter_path = find_path_from_spawn_to_castle(tiles)
        
        if not critter_path:
            log.error("[battle:start_requested] FAIL: defender %d map has no valid path",
                      defender_uid)
            _abort_battle_setup(attack_id, attacking_army)
            return
        
        # ── Get defender's structures ────────────────────────
        # Load structures from hex_map tiles and create Structure objects
        structures_dict = {}
        if defender_empire.structures:
            structures_dict = dict(defender_empire.structures)
        
        # Also load structures from hex_map tiles (for backwards compatibility)
        from gameserver.models.structure import Structure, structure_from_item
        from gameserver.models.hex import HexCoord
        structure_sid = 1
        items_dict = svc.upgrade_provider.items if svc.upgrade_provider else {}
        for tile_key, tile_val in tiles.items():
            # Check if tile_type is a structure (not path, castle, etc.)
            tile_type = _tile_type(tile_val)
            if tile_type not in ("empty", "path", "spawnpoint", "castle", "blocked", "void"):
                # This is a structure tile, load stats from item provider
                item = items_dict.get(tile_type)
                if item:
                    # Parse q,r from key "q,r"
                    q, r = map(int, tile_key.split(","))
                    # Create Structure object with stats from item config
                    structure = structure_from_item(
                        sid=structure_sid, iid=tile_type, position=HexCoord(q, r),
                        item=item, select_override=_tile_select(tile_val, getattr(item, "select", "first")),
                    )
                    structures_dict[structure_sid] = structure
                    structure_sid += 1
                    log.debug("[battle:start_requested] Loaded structure sid=%d iid=%s at (%d,%d)",
                             structure.sid, structure.iid, q, r)

        # ── Create BattleState ───────────────────────────────
        bid = _next_bid
        _next_bid += 1
        # Include any observers already registered before battle started
        attack = next(
            (a for a in svc.attack_service.get_all_attacks() if a.attack_id == attack_id),
            None,
        )
        pre_registered = getattr(attack, '_observers', set())
        battle = BattleState(
            bid=bid,
            defender=defender_empire,
            attacker=attacker_empire,
            attack_id=attack_id,
            army=attacking_army,
            structures=structures_dict,
            observer_uids={attacker_uid, defender_uid} | pre_registered,
            critter_path=critter_path,
        )
        
        # Register battle in active battles dictionary
        _active_battles[defender_uid] = battle
        
        # ── Attach replay recorder ──────────────────────────
        from gameserver.persistence.replay import ReplayRecorder
        battle.recorder = ReplayRecorder(bid, defender_uid=defender_uid,
                                         attacker_uid=attacker_uid)
        
        log.info("[battle:start_requested] SUCCESS: battle %d created (attacker=%d, defender=%d)",
                 bid, attacker_uid, defender_uid)
        
        # ── Send battle_setup to both players ────────────────
        setup_msg = {
            "type": "battle_setup",
            "bid": bid,
            "replay_key": battle.recorder.replay_key,
            "defender_uid": defender_uid,
            "attacker_uid": attacker_uid,
            "defender_name": defender_empire.name if defender_empire else "",
            "attacker_name": attacker_empire.name if attacker_empire else "",
            "attacker_army_name": attacking_army.name if attacking_army else "",
            "tiles": tiles,  # Defender's hex map
            "structures": [
                {
                    "sid": s.sid,
                    "iid": s.iid,
                    "q": s.position.q,
                    "r": s.position.r,
                    "damage": s.damage,
                    "range": s.range,
                    "select": s.select,
                }
                for s in structures_dict.values()
            ],
            "path": [{"q": h.q, "r": h.r} for h in critter_path],            
        }
        
        if svc.server:
            await svc.server.send_to(attacker_uid, setup_msg)
            await svc.server.send_to(defender_uid, setup_msg)
        
        # Record setup for replay
        battle.recorder.record(0, setup_msg)
        
        # ── Initialise wave timers ────────────────────────────────────────
        # Wave i starts at i × initial_wave_delay_ms. First wave (i=0) spawns
        # immediately; subsequent waves are staggered by initial_wave_delay_ms.
        # Defender's wave_delay_offset effect adds extra delay to every wave.
        _initial_delay_ms = svc.game_config.initial_wave_delay_ms
        _wave_delay_offset_ms = (
            defender_empire.get_effect(fx.WAVE_DELAY_OFFSET, 0.0)
            if defender_empire else 0.0
        )
        log.info("[battle:wave_timers] defender=%d wave_delay_offset=%.0fms initial_delay=%.0fms",
                 defender_uid, _wave_delay_offset_ms, _initial_delay_ms)
        for _i, _wave in enumerate(attacking_army.waves):
            _wave.next_critter_ms = int(_i * _initial_delay_ms) + (_i + 1) * _wave_delay_offset_ms
            _wave.num_critters_spawned = 0  # reset spawn count on battle start
            log.info("[battle:wave_timers] wave[%d] next_critter_ms=%.0f", _i, _wave.next_critter_ms)

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
        _abort_battle_setup(attack_id)
        return
    
    attacking_army = None
    for army in attacker_empire.armies:
        if army.aid == army_aid:
            attacking_army = army
            break
    
    if attacking_army is None:
        log.error("[battle:start_requested] FAIL: army %d not found for attacker %d",
                  army_aid, attacker_uid)
        _abort_battle_setup(attack_id)
        return
    
    # Get defender's empire, map, structures
    defender_empire = svc.empire_service.get(defender_uid)
    if defender_empire is None:
        log.error("[battle:start_requested] FAIL: defender %d not found", defender_uid)
        _abort_battle_setup(attack_id, attacking_army)
        return
    
    if not defender_empire.hex_map:
        log.error("[battle:start_requested] FAIL: defender %d has no map", defender_uid)
        _abort_battle_setup(attack_id, attacking_army)
        return
    
    # ── Find path from spawnpoint to castle ──────────────
    from gameserver.engine.hex_pathfinding import find_path_from_spawn_to_castle
    tiles = defender_empire.hex_map
    critter_path = find_path_from_spawn_to_castle(tiles)
    
    if not critter_path:
        log.error("[battle:start_requested] FAIL: defender %d map has no valid path",
                  defender_uid)
        _abort_battle_setup(attack_id, attacking_army)
        return
    
    # ── Get defender's structures ────────────────────────
    # Load structures from hex_map tiles and create Structure objects
    structures_dict = {}
    if defender_empire.structures:
        structures_dict = dict(defender_empire.structures)
    
    # Also load structures from hex_map tiles (for backwards compatibility)
    from gameserver.models.structure import Structure, structure_from_item
    from gameserver.models.hex import HexCoord
    structure_sid = 1
    items_dict = svc.upgrade_provider.items if svc.upgrade_provider else {}
    for tile_key, tile_val in tiles.items():
        # Check if tile_type is a structure (not path, castle, etc.)
        tile_type = _tile_type(tile_val)
        if tile_type not in ("empty", "path", "spawnpoint", "castle", "blocked", "void"):
            # This is a structure tile, load stats from item provider
            item = items_dict.get(tile_type)
            if item:
                # Parse q,r from key "q,r"
                q, r = map(int, tile_key.split(","))
                # Create Structure object with stats from item config
                structure = structure_from_item(
                    sid=structure_sid, iid=tile_type, position=HexCoord(q, r),
                    item=item, select_override=_tile_select(tile_val, getattr(item, "select", "first")),
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
                "select": s.select,
            }
            for s in structures_dict.values()
        ],
        "path":  [{"q": h.q, "r": h.r} for h in critter_path],
    }
    
    if svc.server:
        await svc.server.send_to(attacker_uid, setup_msg)
        await svc.server.send_to(defender_uid, setup_msg)
    
    # ── Initialise wave timers ────────────────────────────────────────
    # Wave i starts at (i+1) × initial_wave_delay_ms.
    # Defender's wave_delay_offset effect adds extra delay to every wave.
    _initial_delay_ms = svc.game_config.initial_wave_delay_ms
    _wave_delay_offset_ms = (
        defender_empire.get_effect(fx.WAVE_DELAY_OFFSET, 0.0)
        if defender_empire else 0.0
    )
    for _i, _wave in enumerate(attacking_army.waves):
        _wave.next_critter_ms = int((_i + 1) * _initial_delay_ms) + _wave_delay_offset_ms
        _wave.num_critters_spawned = 0  # reset spawn count on battle start

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
    router.register("set_structure_select", handle_set_structure_select)

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
    from gameserver.util.events import BattleStartRequested, AttackPhaseChanged, BattleObserverBroadcast, ItemCompleted
    if services.event_bus:
        services.event_bus.on(BattleStartRequested, _create_battle_start_handler())
        services.event_bus.on(AttackPhaseChanged, _create_attack_phase_handler())
        services.event_bus.on(BattleObserverBroadcast, _create_battle_observer_broadcast_handler())
        services.event_bus.on(ItemCompleted, _create_item_completed_handler())

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
