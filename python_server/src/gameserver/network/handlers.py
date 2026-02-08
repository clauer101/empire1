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

log = logging.getLogger(__name__)

# Module-level reference set by register_all_handlers()
_services: Optional[Services] = None


def _svc() -> Services:
    """Get the Services container. Raises if not initialized."""
    assert _services is not None, "handlers: services not initialized"
    return _services


# ===================================================================
# Map validation helpers
# ===================================================================

def _has_path_from_spawn_to_castle(tiles: dict[str, str]) -> bool:
    """Check if there's a path from any spawnpoint to the castle.
    
    Can only traverse spawnpoint, path, and castle tiles via 6-connected hex neighbors.
    
    Args:
        tiles: Dict of {"q,r": "tile_type"} where tile_type is 'castle', 'spawnpoint', etc.
    
    Returns:
        True if at least one path exists, False otherwise.
    """
    # Find castle and spawnpoints
    castle_key: Optional[str] = None
    spawn_keys: list[str] = []
    
    for key, tile_type in tiles.items():
        if tile_type == 'castle':
            castle_key = key
        elif tile_type == 'spawnpoint':
            spawn_keys.append(key)
    
    # Must have both
    if not castle_key or not spawn_keys:
        return False
    
    # Parse key to coordinates
    def key_to_coords(k: str) -> tuple[int, int]:
        q, r = k.split(',')
        return int(q), int(r)
    
    # Hex neighbors in axial coordinates
    def hex_neighbors(q: int, r: int) -> list[tuple[int, int]]:
        return [
            (q + 1, r),
            (q + 1, r - 1),
            (q, r - 1),
            (q - 1, r),
            (q - 1, r + 1),
            (q, r + 1),
        ]
    
    def coords_to_key(q: int, r: int) -> str:
        return f"{q},{r}"
    
    castle_q, castle_r = key_to_coords(castle_key)
    
    # BFS from each spawnpoint
    for spawn_key in spawn_keys:
        spawn_q, spawn_r = key_to_coords(spawn_key)
        
        queue: deque[tuple[int, int]] = deque([(spawn_q, spawn_r)])
        visited: set[tuple[int, int]] = {(spawn_q, spawn_r)}
        
        while queue:
            q, r = queue.popleft()
            
            # Reached castle?
            if (q, r) == (castle_q, castle_r):
                return True
            
            # Explore neighbors
            for nq, nr in hex_neighbors(q, r):
                if (nq, nr) not in visited:
                    key = coords_to_key(nq, nr)
                    tile_type = tiles.get(key)
                    
                    # Only traverse through passable tiles
                    if tile_type in ('spawnpoint', 'path', 'castle'):
                        visited.add((nq, nr))
                        queue.append((nq, nr))
    
    return False


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

    return {
        "type": "summary_response",
        "uid": empire.uid,
        "name": empire.name,
        "resources": {k: round(v, 2) for k, v in empire.resources.items()},
        "citizens": dict(empire.citizens),
        "citizen_price": svc.empire_service._citizen_price(sum(empire.citizens.values()) + 1),
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
    }


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
            "requirements": list(item.requirements),
            "effects": dict(item.effects),
        }

    return {
        "type": "item_response",
        "buildings": buildings,
        "knowledge": knowledge,
        "structures": structures,
    }


async def handle_military_request(
    message: GameMessage, sender_uid: int,
) -> Optional[dict[str, Any]]:
    """Handle ``military_request`` — return armies and attack status.

    TODO: Implement once ArmyService and AttackService are complete.
    """
    svc = _svc()
    empire = svc.empire_service.get(sender_uid)
    if empire is None:
        return {
            "type": "military_response",
            "error": f"No empire found for uid {sender_uid}",
        }

    armies = []
    for army in empire.armies:
        armies.append({
            "aid": army.aid,
            "name": army.name,
            "direction": army.direction.value,
            "wave_count": len(army.waves),
        })

    return {
        "type": "military_response",
        "armies": armies,
        "attacks_incoming": [],  # TODO: from AttackService
        "attacks_outgoing": [],  # TODO: from AttackService
        "available_critters": [],  # TODO: from UpgradeProvider
    }


# ===================================================================
# Building / Research
# ===================================================================

async def handle_new_item(
    message: GameMessage, sender_uid: int,
) -> Optional[dict[str, Any]]:
    """Handle ``new_item`` — start building or researching an item."""
    svc = _svc()
    iid = getattr(message, "iid", "")
    target_uid = sender_uid if sender_uid > 0 else message.sender
    empire = svc.empire_service.get(target_uid)
    if empire is None:
        return {"type": "item_response_error", "error": "No empire found"}

    error = svc.empire_service.build_item(empire, iid)
    if error:
        log.info("new_item failed uid=%d iid=%s: %s", target_uid, iid, error)
        return {"type": "build_response", "success": False, "iid": iid, "error": error}

    log.info("new_item success uid=%d iid=%s", target_uid, iid)
    return {"type": "build_response", "success": True, "iid": iid, "error": ""}


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
    """Handle ``citizen_upgrade`` — add one citizen (fire-and-forget).

    Fire-and-forget: no response sent to client.
    """
    svc = _svc()
    log.info("citizen_upgrade request from uid=%d", sender_uid)
    empire = svc.empire_service.get(sender_uid)
    if empire is None:
        log.warning("citizen_upgrade failed: no empire found for uid=%d", sender_uid)
        return None
    error = svc.empire_service.upgrade_citizen(empire)
    if error:
        log.info("citizen_upgrade failed uid=%d: %s", sender_uid, error)
        return None
    log.info("citizen_upgrade success uid=%d", sender_uid)
    return None


async def handle_change_citizen(
    message: GameMessage, sender_uid: int,
) -> Optional[dict[str, Any]]:
    """Handle ``change_citizen`` — redistribute citizens among roles (fire-and-forget).
    
    Fire-and-forget: no response sent to client.
    """
    svc = _svc()
    log.info("change_citizen request from uid=%d", sender_uid)
    empire = svc.empire_service.get(sender_uid)
    if empire is None:
        log.warning("change_citizen failed: no empire found for uid=%d", sender_uid)
        return None
    
    citizens = getattr(message, "citizens", {})
    error = svc.empire_service.change_citizens(empire, citizens)
    if error:
        log.info("change_citizen failed uid=%d: %s", sender_uid, error)
        return None
    
    log.info("change_citizen success uid=%d: %s", sender_uid, citizens)
    return None


# ===================================================================
# Military / Army
# ===================================================================

async def handle_new_army(
    message: GameMessage, sender_uid: int,
) -> Optional[dict[str, Any]]:
    """Handle ``new_army`` — create a new army.

    TODO: Implement in ArmyService.create_army().
    """
    log.info("new_army from uid=%d (not yet implemented)", sender_uid)
    return None


async def handle_new_attack(
    message: GameMessage, sender_uid: int,
) -> Optional[dict[str, Any]]:
    """Handle ``new_attack_request`` — launch an attack.

    TODO: Implement in AttackService.start_attack().
    """
    log.info("new_attack_request from uid=%d (not yet implemented)", sender_uid)
    return None


async def handle_change_army(
    message: GameMessage, sender_uid: int,
) -> Optional[dict[str, Any]]:
    """Handle ``change_army`` — rename army or change direction.

    TODO: Validate army not in battle/travelling, update name + direction.
    """
    log.info("change_army from uid=%d (not yet implemented)", sender_uid)
    return None


async def handle_new_wave(
    message: GameMessage, sender_uid: int,
) -> Optional[dict[str, Any]]:
    """Handle ``new_wave`` — add a critter wave to an army.

    TODO: Check max waves, gold cost for extra slots, boss uniqueness.
    """
    log.info("new_wave from uid=%d (not yet implemented)", sender_uid)
    return None


async def handle_change_wave(
    message: GameMessage, sender_uid: int,
) -> Optional[dict[str, Any]]:
    """Handle ``change_wave`` — change critter type of an existing wave.

    TODO: Validate army not in battle, swap IID on wave number.
    """
    log.info("change_wave from uid=%d (not yet implemented)", sender_uid)
    return None


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

async def handle_battle_register(
    message: GameMessage, sender_uid: int,
) -> Optional[dict[str, Any]]:
    """Handle ``battle_register`` — register as battle observer.

    TODO: Register sender as observer of the battle for given UID.
    """
    log.info("battle_register from uid=%d (not yet implemented)", sender_uid)
    return None


async def handle_battle_unregister(
    message: GameMessage, sender_uid: int,
) -> Optional[dict[str, Any]]:
    """Handle ``battle_unregister`` — unregister from battle observation.

    TODO: Remove sender from battle observer list.
    """
    log.info("battle_unregister from uid=%d (not yet implemented)", sender_uid)
    return None


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
    """Handle ``auth_request`` — authenticate a player."""
    svc = _svc()
    username = getattr(message, "username", "")
    password = getattr(message, "password", "")

    uid = await svc.auth_service.login(username, password)
    if uid is not None:
        return {
            "type": "auth_response",
            "success": True,
            "uid": uid,
            "reason": "",
        }
    return {
        "type": "auth_response",
        "success": False,
        "uid": 0,
        "reason": "Invalid username or password",
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
    
    return {
        "type": "map_save_response",
        "success": True,
    }


# ===================================================================
# Battle Test
# ===================================================================

_active_battles: dict[int, bool] = {}  # uid → is_active


async def handle_battle_request(
    message: GameMessage, sender_uid: int,
) -> Optional[dict[str, Any]]:
    """Start a battle simulation: move critters from spawnpoint to castle."""
    svc = _svc()
    target_uid = sender_uid if sender_uid > 0 else message.sender
    empire = svc.empire_service.get(target_uid)
    
    if empire is None:
        return {
            "type": "battle_test_response",
            "success": False,
            "error": f"No empire found for uid {target_uid}",
        }
    
    if not empire.hex_map:
        return {
            "type": "battle_test_response",
            "success": False,
            "error": "No map configured",
        }
    
    # Start battle simulation
    _active_battles[target_uid] = True
    asyncio.create_task(_simulate_battle(target_uid, empire.hex_map))
    
    return {
        "type": "battle_response",
        "success": True,
    }


async def _simulate_battle(uid: int, tiles: dict[str, str]) -> None:
    """Simulate critter movement from spawn to castle over 10 seconds."""
    svc = _svc()
    
    # Find spawn and castle
    spawn_pos, castle_pos = None, None
    for key, tile_type in tiles.items():
        q, r = map(int, key.split(','))
        if tile_type == 'spawnpoint' and spawn_pos is None:
            spawn_pos = (q, r)
        elif tile_type == 'castle':
            castle_pos = (q, r)
    
    if not spawn_pos or not castle_pos:
        return
    
    # Build path via BFS
    path = _find_path(spawn_pos, castle_pos, tiles)
    if not path:
        return
    
    # Animate along path for ~10 seconds (250 ticks at 25 Hz)
    tick_duration = 0.04  # 25 Hz
    total_ticks = 250
    path_length = len(path) - 1
    
    for tick in range(total_ticks):
        if not _active_battles.get(uid):
            break
        
        # Calculate progress (0.0 to 1.0)
        progress = tick / total_ticks
        path_index = int(progress * path_length)
        path_index = min(path_index, path_length)
        
        q, r = path[path_index]
        update_msg = {
            "type": "battle_update",
            "position": {"q": q, "r": r},
            "active": True,
        }
        
        # Broadcast to this client
        if svc.server:
            await svc.server.send_to(uid, update_msg)
        
        await asyncio.sleep(tick_duration)
    
    # End message
    final_msg = {
        "type": "battle_update",
        "position": {"q": castle_pos[0], "r": castle_pos[1]},
        "active": False,
    }
    if svc.server:
        await svc.server.send_to(uid, final_msg)
    
    _active_battles.pop(uid, None)


def _find_path(start: tuple[int, int], end: tuple[int, int], tiles: dict[str, str]) -> list[tuple[int, int]]:
    """BFS to find path from start to end through passable tiles."""
    from collections import deque
    
    queue = deque([(start, [start])])
    visited = {start}
    
    def hex_neighbors(q: int, r: int) -> list[tuple[int, int]]:
        return [
            (q + 1, r),
            (q + 1, r - 1),
            (q, r - 1),
            (q - 1, r),
            (q - 1, r + 1),
            (q, r + 1),
        ]
    
    while queue:
        (q, r), path = queue.popleft()
        
        if (q, r) == end:
            return path
        
        for nq, nr in hex_neighbors(q, r):
            if (nq, nr) not in visited:
                key = f"{nq},{nr}"
                tile_type = tiles.get(key)
                if tile_type in ('spawnpoint', 'path', 'castle'):
                    visited.add((nq, nr))
                    queue.append(((nq, nr), path + [(nq, nr)]))
    
    return []


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

    # -- Battle ----------------------------------------------------------
    router.register("battle_request", handle_battle_request)

    registered = router.registered_types
    log.info("Registered %d message handlers: %s", len(registered), ", ".join(registered))
