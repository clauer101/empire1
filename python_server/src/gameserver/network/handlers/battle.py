"""Battle handlers — Strangler Fig domain module.

Contains battle register/unregister/next_wave handlers and all battle task helpers.
"""
from __future__ import annotations

import logging
from typing import Any, Iterable, Optional, TYPE_CHECKING

__all__ = [
    # public handlers
    "handle_battle_register",
    "handle_battle_unregister",
    "handle_battle_next_wave",
    # private names explicitly exported for importers
    "_evict_observer_from_all",
    "_apply_artefact_steal",
    "_compute_and_apply_loot",
    "_sync_battle_structures",
    "_run_battle_task",
    "_create_item_completed_handler",
    "_create_attack_phase_handler",
    "_create_spy_arrived_handler",
    "_create_battle_observer_broadcast_handler",
    "_abort_battle_setup",
    "_create_battle_start_handler",
    "_sync_battle_structures",
]

if TYPE_CHECKING:
    from gameserver.main import Services
    from gameserver.models.battle import BattleState
    from gameserver.models.attack import Attack

from gameserver.models.attack import AttackPhase
from gameserver.models.messages import GameMessage

log = logging.getLogger(__name__)


def _svc() -> "Services":
    from gameserver.network.handlers._core import _svc as _core_svc
    return _core_svc()


def _tile_type(v: Any) -> str:
    from gameserver.network.handlers._core import _tile_type as _core_tile_type
    return _core_tile_type(v)


def _tile_select(v: Any, item_default: str = 'first') -> str:
    from gameserver.network.handlers._core import _tile_select as _core_tile_select
    return _core_tile_select(v, item_default)


def _get_active_battles() -> "dict[int, BattleState]":
    from gameserver.network.handlers._core import _active_battles
    return _active_battles


async def _send_battle_state_to_observer(attack: "Attack", observer_uid: int) -> None:
    """Send current battle state to an observer.

    When a live BattleState exists, triggers a broadcast to all observers so the
    caller receives an up-to-date battle_update with all critters and all armies.
    Falls back to a lightweight battle_status for siege phase.
    """
    svc = _svc()
    assert svc.empire_service is not None

    _active_battles = _get_active_battles()
    battle = _active_battles.get(attack.defender_uid)

    # In-battle: trigger a real broadcast from BattleService so the observer
    # immediately receives a battle_update with the full critter pool.
    if battle is not None and not battle.is_finished and attack.phase == AttackPhase.IN_BATTLE:
        from gameserver.engine.battle_service import BattleService
        items = svc.upgrade_provider.items if svc.upgrade_provider else {}
        battle_svc = BattleService(items=items, gc=svc.empire_service._gc if svc.empire_service else None)

        async def _send_fn(uid: int, data: dict[str, Any]) -> bool:
            if svc.server:
                return bool(await svc.server.send_to(uid, data))
            return False

        # Temporarily add observer so _broadcast delivers to them
        battle.observer_uids.add(observer_uid)
        await battle_svc._broadcast(battle, _send_fn)
        return

    # Siege phase or no active battle: send a lightweight status message
    defender_empire = svc.empire_service.get(attack.defender_uid)
    attacker_empire = svc.empire_service.get(attack.attacker_uid)

    if not defender_empire or not attacker_empire:
        return

    attacking_army = None
    for army in attacker_empire.armies:
        if army.aid == attack.army_aid:
            attacking_army = army
            break

    if not attacking_army:
        return

    if attack.phase == AttackPhase.IN_SIEGE:
        time_since_start_s = -attack.siege_remaining_seconds
    elif attack.phase == AttackPhase.IN_BATTLE and battle:
        time_since_start_s = battle.elapsed_ms / 1000.0
    else:
        time_since_start_s = 0

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

    attacker_username = ""
    if svc.database is not None:
        for _urow3 in await svc.database.list_users():
            if _urow3["uid"] == attack.attacker_uid:
                attacker_username = _urow3["username"]
                break

    status_msg = {
        "type": "battle_status",
        "attack_id": attack.attack_id,
        "phase": attack.phase.value,
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


async def _send_battle_setup_to_observer(attack: "Attack", observer_uid: int) -> None:
    """Send battle_setup message to initialize the battle view.

    If an active BattleState exists for the defender, uses its data (all attacker armies).
    Otherwise falls back to building setup from the defender's map directly.
    """
    from gameserver.engine.hex_pathfinding import find_path_from_spawn_to_castle
    from gameserver.models.hex import HexCoord

    svc = _svc()
    assert svc.empire_service is not None

    # Prefer the live BattleState — it has all armies and the canonical structures
    _active_battles = _get_active_battles()
    battle = _active_battles.get(attack.defender_uid)
    if battle is not None and not battle.is_finished:
        setup_msg = {
            "type": "battle_setup",
            "bid": battle.bid,
            "replay_key": battle.recorder.replay_key if battle.recorder else "",
            "defender_uid": attack.defender_uid,
            "attacker_uid": battle.attacker_uids[0] if battle.attacker_uids else attack.attacker_uid,
            "attacker_uids": list(battle.attacker_uids),
            "defender_name": battle.defender.name if battle.defender else "",
            "attacker_name": (svc.empire_service.get(battle.attacker_uids[0]).name
                              if battle.attacker_uids and svc.empire_service else ""),
            "tiles": battle.defender.hex_map if battle.defender else {},
            "structures": [
                {"sid": s.sid, "iid": s.iid, "q": s.position.q, "r": s.position.r,
                 "damage": s.damage, "range": s.range, "select": s.select}
                for s in battle.structures.values()
            ],
            "path": [{"q": h.q, "r": h.r} for h in battle.critter_path],
        }
        if svc.server:
            await svc.server.send_to(observer_uid, setup_msg)
            log.info("_send_battle_setup: sent to uid=%d (battle bid=%d, %d attackers)",
                     observer_uid, battle.bid, len(battle.attacker_uids))
        return

    # Fallback: no active battle yet (still in siege) — build from defender map
    defender_empire = svc.empire_service.get(attack.defender_uid)
    if not defender_empire:
        log.warning("_send_battle_setup: defender %d not found", attack.defender_uid)
        return

    if not defender_empire.hex_map:
        log.warning("_send_battle_setup: defender %d has no map", attack.defender_uid)
        return

    tiles = defender_empire.hex_map
    normalized = {k: _tile_type(v) for k, v in tiles.items()}
    computed_path = find_path_from_spawn_to_castle(normalized)
    hex_path = computed_path if computed_path else []

    structures_dict = {}
    if defender_empire.structures:
        structures_dict = dict(defender_empire.structures)

    from gameserver.models.structure import structure_from_item
    structure_sid = 1
    items_dict = svc.upgrade_provider.items if svc.upgrade_provider else {}
    for tile_key, tile_val in tiles.items():
        tile_type = _tile_type(tile_val)
        if tile_type not in ("empty", "path", "spawnpoint", "castle", "blocked", "void"):
            item = items_dict.get(tile_type)
            if item:
                q, r = map(int, tile_key.split(","))
                structure = structure_from_item(
                    sid=structure_sid, iid=tile_type, position=HexCoord(q, r),
                    item=item, select_override=_tile_select(tile_val, getattr(item, "select", "first")),
                )
                structures_dict[structure_sid] = structure
                structure_sid += 1
                log.debug("[_send_battle_setup] Loaded structure sid=%d iid=%s at (%d,%d)",
                         structure.sid, structure.iid, q, r)

    setup_msg = {
        "type": "battle_setup",
        "bid": attack.attack_id,
        "defender_uid": attack.defender_uid,
        "attacker_uid": attack.attacker_uid,
        "attacker_uids": [attack.attacker_uid],
        "tiles": tiles,
        "structures": [
            {"sid": s.sid, "iid": s.iid, "q": s.position.q, "r": s.position.r,
             "damage": s.damage, "range": s.range, "select": s.select}
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
        if exclude_attack_id is not None and exclude_attack_id in battle.attack_ids:
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
    assert svc.attack_service is not None
    _active_battles = _get_active_battles()

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

    # Register observer (dynamic attribute on Attack)
    if not hasattr(attack, '_observers'):
        setattr(attack, '_observers', set())
    getattr(attack, '_observers').add(sender_uid)

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
    _active_battles = _get_active_battles()
    attack_svc = svc.attack_service
    assert attack_svc is not None

    # Find attack and remove observer
    for attack in attack_svc.get_all_attacks():
        observers = getattr(attack, '_observers', None)
        if observers is not None and sender_uid in observers:
            observers.remove(sender_uid)
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


# Re-export task functions from battle_task for callers that import from this module
from gameserver.network.handlers.battle_task import (  # noqa: F401, E402
    _sync_battle_structures,
    _run_battle_task,
    _apply_artefact_steal,
    _compute_and_apply_loot,
    _create_item_completed_handler,
    _create_attack_phase_handler,
    _create_spy_arrived_handler,
    _create_battle_observer_broadcast_handler,
    _abort_battle_setup,
    _create_battle_start_handler,
)
