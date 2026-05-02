"""Battle handlers — Strangler Fig domain module.

Contains battle register/unregister/next_wave handlers and all battle task helpers.
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any, Callable, Iterable, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from gameserver.engine.battle_service import BattleService
    from gameserver.models.battle import BattleState
    from gameserver.models.attack import Attack
    from gameserver.util.events import (
        AttackPhaseChanged,
        BattleObserverBroadcast,
        BattleStartRequested,
        ItemCompleted,
        SpyArrived,
    )

from gameserver.models.attack import AttackPhase
from gameserver.models.messages import GameMessage
from gameserver.util import effects as fx

log = logging.getLogger(__name__)


def _svc():
    from gameserver.network.handlers._core import _svc as _core_svc
    return _core_svc()


def _tile_type(v) -> str:
    from gameserver.network.handlers._core import _tile_type as _core_tile_type
    return _core_tile_type(v)


def _tile_select(v, item_default: str = 'first') -> str:
    from gameserver.network.handlers._core import _tile_select as _core_tile_select
    return _core_tile_select(v, item_default)


def _get_active_battles() -> "dict[int, BattleState]":
    from gameserver.network.handlers._core import _active_battles
    return _active_battles


async def _send_battle_state_to_observer(attack: "Attack", observer_uid: int) -> None:
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
            "wave_id": wave.wave_id,  # Use actual wave_id from wave object, not index
            "critter_iid": wave.iid,
            "slots": wave.slots,
        })

    # Get battle state (if battle is running)
    _active_battles = _get_active_battles()
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


async def _send_battle_setup_to_observer(attack: "Attack", observer_uid: int) -> None:
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
    from gameserver.models.structure import structure_from_item
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
    _active_battles = _get_active_battles()
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


def _sync_battle_structures(battle: "BattleState", tiles: dict, items_dict: dict) -> list[int]:
    """Sync battle.structures from the current tile map.

    Adds towers that were placed after battle started, removes towers that
    were demolished, and leaves untouched towers (same iid at same position)
    intact so their reload timers and targeting state survive.

    Returns list of newly added SIDs.
    """
    from gameserver.models.structure import structure_from_item
    from gameserver.models.hex import HexCoord

    NON_STRUCTURE = {"empty", "path", "spawnpoint", "castle", "blocked", "void"}

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
        attacker_won = battle.defender_won is False
        if attacker_won:
            loot = _compute_and_apply_loot(battle, svc)
        stolen_artefact = _apply_artefact_steal(battle, svc, attacker_won)
        if stolen_artefact:
            loot["artefact"] = stolen_artefact
        if attacker_won or stolen_artefact:
            await battle_svc.send_summary(battle, send_fn, loot)
        elif not _summary_sent:
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
            if not saved_path:
                log.warning("[battle] bid=%d replay not saved — sending inbox messages anyway", bid)
            if svc.database:
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

                # Loot lines (culture + knowledge + artefact stolen — always from defender)
                loot_atk_lines = ""
                loot_def_lines = ""
                if loot:
                    culture_stolen = loot.get("culture", 0.0)
                    knowledge_loot = loot.get("knowledge")
                    artefact_stolen = loot.get("artefact")
                    if culture_stolen > 0:
                        loot_atk_lines += f"🎭 Stolen culture:    +{culture_stolen:.1f}\n"
                        loot_def_lines += f"🎭 Culture stolen:    -{culture_stolen:.1f}\n"
                    if knowledge_loot:
                        k_name = knowledge_loot.get("name", knowledge_loot.get("iid", "?"))
                        k_pct  = knowledge_loot.get("pct", 0.0)
                        loot_atk_lines += f"📚 Stolen knowledge: {k_name} ({k_pct:.0f}%)\n"
                        loot_def_lines += f"📚 Knowledge stolen: {k_name} ({k_pct:.0f}%)\n"
                    if artefact_stolen:
                        art_item = svc.upgrade_provider.items.get(artefact_stolen) if svc.upgrade_provider else None
                        art_name = art_item.name if art_item else artefact_stolen
                        loot_atk_lines += f"✨ Stolen artefact:  {art_name}\n"
                        loot_def_lines += f"✨ Artefact stolen:  {art_name}\n"

                # ── Defender message ──────────────────────────────────────
                def_result = "🛡 You Won!" if defender_won else "🛡 You Lost!"
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
                atk_result = "⚔ You Won!" if not defender_won else "⚔ You Lost!"
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
        _get_active_battles().pop(battle.defender.uid, None)


def _apply_artefact_steal(battle: "BattleState", svc, attacker_won: bool) -> "str | None":
    """Roll per-artefact steal after a battle. AI attackers never steal artefacts.

    Returns the stolen artefact iid or None.
    """
    import random as _random
    from gameserver.engine.ai_service import AI_UID as _AI_UID

    if not battle.attacker or not battle.defender:
        return None
    if battle.attacker.uid == _AI_UID:
        return None
    thief  = battle.attacker
    victim = battle.defender

    cfg = svc.game_config
    if attacker_won:
        chance = getattr(cfg, 'base_artifact_steal_victory', 0.5) if cfg else 0.5
    else:
        chance = getattr(cfg, 'base_artifact_steal_defeat', 0.05) if cfg else 0.05

    stolen = None
    for artefact in list(victim.artefacts):
        roll = _random.random()
        if roll < chance:
            victim.artefacts.remove(artefact)
            thief.artefacts.append(artefact)
            stolen = artefact
            log.info("[LOOT] Artefact stolen: %s  thief uid=%d  victim uid=%d  roll=%.3f < chance=%.2f (attacker_won=%s)",
                     artefact, thief.uid, victim.uid, roll, chance, attacker_won)
            svc.empire_service.recalculate_effects(victim)
            svc.empire_service.recalculate_effects(thief)
            break  # one artefact per battle
        else:
            log.info("[LOOT] Artefact steal failed: %s  thief uid=%d  victim uid=%d  roll=%.3f >= chance=%.2f (attacker_won=%s)",
                     artefact, thief.uid, victim.uid, roll, chance, attacker_won)
    return stolen


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
    from gameserver.engine.ai_service import AI_UID as _AI_UID
    _attacker_is_ai = attacker.uid == _AI_UID
    if _attacker_is_ai:
        # AI wins: pick the active research with the most progress: max(effort - remaining).
        active = [
            (iid, rem) for iid, rem in defender.knowledge.items()
            if rem > 0 and items.get(iid)
        ]
        if active:
            chosen_iid = max(active, key=lambda x: (items[x[0]].effort - x[1]))[0]
            stealable_iids = [chosen_iid]
        else:
            stealable_iids = []
    else:
        # Human attacker: random tech the attacker hasn't started yet.
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
        current_remaining = defender.knowledge.get(chosen_iid, 0.0)
        already_researched = max(0.0, effort - current_remaining)
        gain = already_researched * pct
        # Credit human attacker: reduce remaining effort for the stolen item.
        # AI attackers don't accumulate knowledge (would block future steals).
        if not _attacker_is_ai:
            attacker_remaining = attacker.knowledge.get(chosen_iid, effort)
            attacker.knowledge[chosen_iid] = max(0.0, attacker_remaining - gain)
        # Penalise defender: stolen effort is added back, capped at full effort.
        defender.knowledge[chosen_iid] = min(effort, current_remaining + gain)
        loot["knowledge"] = {
            "iid": chosen_iid,
            "name": item.name if item else chosen_iid,
            "pct": round(pct * 100, 1),
            "amount": round(gain, 1),
        }
        log.info(
            "[LOOT] Knowledge stolen from uid=%d: %s (%.1f%% of effort %.0f = %.1f) "
            "— attacker uid=%d (ai=%s) defender remaining now %.1f",
            defender.uid, chosen_iid, pct * 100, effort, gain,
            attacker.uid, _attacker_is_ai, defender.knowledge[chosen_iid],
        )
        # Pause research_queue if its requirements are no longer met.
        if defender.research_queue is not None:
            upgrades = svc.upgrade_provider
            if upgrades is not None:
                completed: set[str] = set()
                for k, v in defender.buildings.items():
                    if v <= 0:
                        completed.add(k)
                for k, v in defender.knowledge.items():
                    if v <= 0:
                        completed.add(k)
                completed.update(defender.artefacts)
                if not upgrades.check_requirements(defender.research_queue, completed):
                    log.info(
                        "[LOOT] Pausing research %s for uid=%d: requirements no longer met after knowledge steal",
                        defender.research_queue, defender.uid,
                    )
                    defender.research_queue = None

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

    # artefact steal is handled separately in _apply_artefact_steal (called for both outcomes)

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

        if event.new_phase == "in_siege" and svc.database:
            from gameserver.util.push_service import notify_siege_started, notify_under_siege
            attacker_empire = svc.empire_service.get(attacker_uid)
            defender_empire = svc.empire_service.get(defender_uid)
            attacker_name = attacker_empire.name if attacker_empire else "Someone"
            defender_name = defender_empire.name if defender_empire else "your target"
            asyncio.ensure_future(notify_siege_started(svc.database, attacker_uid, defender_name))
            asyncio.ensure_future(notify_under_siege(svc.database, defender_uid, attacker_name))

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
        asyncio.create_task(_async_phase_changed(event))

    return _on_attack_phase_changed


def _create_spy_arrived_handler() -> Callable:
    """Create a handler for SpyArrived events.

    Sends the attacker a workshop intelligence report and notifies the
    defender that the "attack" has ended.
    """
    async def _async_spy_arrived(event: "SpyArrived") -> None:
        svc = _svc()
        attacker_uid = event.attacker_uid
        defender_uid = event.defender_uid

        defender = svc.empire_service.get(defender_uid)
        attacker_empire = svc.empire_service.get(attacker_uid)
        if defender is None or attacker_empire is None:
            log.warning("[spy] Empire not found: attacker=%d defender=%d", attacker_uid, defender_uid)
            return

        # Build intel report — import from military to avoid duplication
        from gameserver.network.handlers.military import _build_spy_report
        report_text, report_data = _build_spy_report(defender, svc)

        # Notify defender that the attack ended (remove it from their UI)
        finished_msg = {
            "type": "attack_phase_changed",
            "attack_id": event.attack_id,
            "attacker_uid": attacker_uid,
            "defender_uid": defender_uid,
            "army_aid": event.army_aid,
            "new_phase": "finished",
        }
        if svc.server:
            await svc.server.send_to(defender_uid, finished_msg)
            # Send spy_report push to attacker
            await svc.server.send_to(attacker_uid, {
                "type": "spy_report",
                "attack_id": event.attack_id,
                "defender_uid": defender_uid,
                "defender_name": defender.name,
                **report_data,
            })

        # Send inbox message to attacker
        inbox_body = f"🕵 Spy report on {defender.name}\n" + report_text
        await svc.database.send_message(from_uid=0, to_uid=attacker_uid, body=inbox_body)
        log.info("[spy] Report sent: attacker=%d defender=%d era=%s",
                 attacker_uid, defender_uid, report_data.get("era", "?"))

    def _on_spy_arrived(event: "SpyArrived") -> None:
        asyncio.create_task(_async_spy_arrived(event))

    return _on_spy_arrived


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
        from gameserver.engine.battle_service import BattleService
        from gameserver.models.battle import BattleState
        import gameserver.network.handlers._core as _core_mod

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
        from gameserver.models.structure import structure_from_item
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
        bid = _core_mod._next_bid
        _core_mod._next_bid += 1
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
        _core_mod._active_battles[defender_uid] = battle

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

        # Push notification to defender
        if svc.database:
            from gameserver.util.push_service import notify_under_siege
            atk_display = attacker_empire.name if attacker_empire else "Someone"
            asyncio.ensure_future(notify_under_siege(svc.database, defender_uid, atk_display))

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
        battle_svc = BattleService(items=items, gc=svc.empire_service._gc if svc.empire_service else None)

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
    from gameserver.engine.battle_service import BattleService
    from gameserver.models.battle import BattleState
    import gameserver.network.handlers._core as _core_mod

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
    from gameserver.models.structure import structure_from_item
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
    bid = _core_mod._next_bid
    _core_mod._next_bid += 1

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
