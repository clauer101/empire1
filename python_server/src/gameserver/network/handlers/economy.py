"""Economy handlers — Strangler Fig domain module.

Contains empire summary, item/structure/citizen/upgrade/map/tile handlers.
"""
from __future__ import annotations

import logging
from typing import Any, Optional

from gameserver.models.messages import GameMessage, MapSaveRequest

log = logging.getLogger(__name__)


def _svc() -> Any:
    from gameserver.network.handlers._core import _svc as _core_svc
    return _core_svc()


def _tile_type(v: Any) -> str:
    from gameserver.network.handlers._core import _tile_type as _core_tile_type
    return _core_tile_type(v)


def _tile_select(v: Any, item_default: str = 'first') -> str:
    from gameserver.network.handlers._core import _tile_select as _core_tile_select
    return _core_tile_select(v, item_default)


def _has_path_from_spawn_to_castle(tiles: Any) -> bool:
    from gameserver.network.handlers._core import _has_path_from_spawn_to_castle as _core_hpfsc
    return _core_hpfsc(tiles)


def _get_active_battles() -> Any:
    from gameserver.network.handlers._core import _active_battles
    return _active_battles


def _sync_battle_structures(battle: Any, tiles: dict[str, Any], items_dict: dict[str, Any]) -> list[int]:
    from gameserver.network.handlers.battle_task import _sync_battle_structures as _bss
    return _bss(battle, tiles, items_dict)


async def handle_summary_request(
    message: GameMessage, sender_uid: int,
) -> Optional[dict[str, Any]]:
    """Handle ``summary_request`` — return full empire overview.

    Equivalent to the Java ``SummaryRequest`` → ``SummaryResponse`` flow
    that passes through the GameEngine.

    The response contains resources, citizens, buildings, research,
    structures, effects, artefacts, and life status.
    """
    from gameserver.network.handlers.auth import _build_empire_summary
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
            "era": item.era,
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
            "era": item.era,
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
            "era": item.era,
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
            "era": item.era,
        }

    # Full catalog — ALL items regardless of requirements, used by client
    # for "Required for" reverse-dependency mapping across the entire tech tree.
    catalog = {}
    for item in up.items.values():
        entry: dict[str, Any] = {
            "name": item.name,
            "item_type": item.item_type.value,
            "requirements": list(item.requirements),
            "era": item.era,
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
        elif item.item_type == ItemType.ARTEFACT:
            entry.update({
                "effects": dict(item.effects),
                "description": item.description,
                "type": item.subtype or 'normal',
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
    battle = _get_active_battles().get(sender_uid)
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


async def handle_upgrade_structure(
    message: GameMessage, sender_uid: int,
) -> Optional[dict[str, Any]]:
    """Handle ``upgrade_structure`` — upgrade a tower on the map.

    TODO: Check requirements & resources, replace structure with upgrade.
    """
    log.info("upgrade_structure from uid=%d (not yet implemented)", sender_uid)
    return None


async def handle_increase_life(
    message: GameMessage, sender_uid: int,
) -> Optional[dict[str, Any]]:
    """Handle ``increase_life`` — increase max life by 1.

    TODO: Check culture cost (progressive), check life cap from effects.
    """
    log.info("increase_life from uid=%d (not yet implemented)", sender_uid)
    return None


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
    _active_battles = _get_active_battles()
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
        path_data: list[list[int]] = [[c.q, c.r] for c in battle.critter_path]
    else:
        from gameserver.engine.hex_pathfinding import find_path_from_spawn_to_castle
        computed_path = find_path_from_spawn_to_castle({k: _tile_type(v) for k, v in tiles.items()})
        path_data = [[c.q, c.r] for c in computed_path] if computed_path else []

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


async def handle_buy_item_upgrade(
    iid: str, stat: str, sender_uid: int,
) -> dict[str, Any]:
    """Buy one level of a stat upgrade for a tower or critter type."""
    svc = _svc()
    empire = svc.empire_service.get(sender_uid)
    if empire is None:
        return {"success": False, "error": f"No empire found for uid {sender_uid}"}

    # Validate stat
    valid_structure_stats = {"damage", "range", "reload", "effect_duration", "effect_value"}
    valid_critter_stats   = {"health", "speed", "armour"}
    item = svc.upgrade_provider.items.get(iid) if svc.upgrade_provider else None
    if item is None:
        return {"success": False, "error": f"Unknown item: {iid}"}

    from gameserver.models.items import ItemType
    if item.item_type == ItemType.STRUCTURE:
        valid_stats = valid_structure_stats
    elif item.item_type == ItemType.CRITTER:
        valid_stats = valid_critter_stats
    else:
        return {"success": False, "error": f"Item {iid} is not upgradeable"}

    if stat not in valid_stats:
        return {"success": False, "error": f"Invalid stat '{stat}' for {iid} (valid: {sorted(valid_stats)})"}

    price = svc.empire_service._item_upgrade_price(empire, iid, stat)
    current_gold = empire.resources.get("gold", 0.0)
    if current_gold < price:
        return {"success": False, "error": f"Not enough gold (need {price:.1f}, have {current_gold:.1f})"}

    empire.resources["gold"] -= price
    iid_upgrades = empire.item_upgrades.setdefault(iid, {})
    iid_upgrades[stat] = iid_upgrades.get(stat, 0) + 1
    new_level = iid_upgrades[stat]
    next_price = svc.empire_service._item_upgrade_price(empire, iid, stat)

    log.info("Item upgrade: uid=%d iid=%s stat=%s → level %d for %.1f gold", sender_uid, iid, stat, new_level, price)

    return {
        "success": True,
        "iid": iid,
        "stat": stat,
        "new_level": new_level,
        "cost": round(price, 2),
        "gold": round(empire.resources.get("gold", 0.0), 2),
        "next_price": round(next_price, 2),
        "item_upgrades": dict(empire.item_upgrades),
    }
