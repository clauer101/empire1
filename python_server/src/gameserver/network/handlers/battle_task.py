"""Battle task helpers — battle loop, loot, event handler factories.

Split from battle.py to keep files under 1000 lines (T3.1).
All public names are re-exported from battle.py so external callers are unchanged.
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any, Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from gameserver.engine.battle_service import BattleService
    from gameserver.models.battle import BattleState
    from gameserver.util.events import (
        AttackPhaseChanged,
        BattleObserverBroadcast,
        BattleStartRequested,
        ItemCompleted,
        SpyArrived,
    )

from gameserver.util import effects as fx

log = logging.getLogger(__name__)


def _svc() -> Any:
    from gameserver.network.handlers._core import _svc as _core_svc
    return _core_svc()


def _tile_type(v: Any) -> str:
    from gameserver.network.handlers._core import _tile_type as _core_tile_type
    return _core_tile_type(v)


def _tile_select(v: Any, item_default: str = "first") -> str:
    from gameserver.network.handlers._core import _tile_select as _core_tile_select
    return _core_tile_select(v, item_default)


def _get_active_battles() -> Any:
    from gameserver.network.handlers._core import _active_battles
    return _active_battles


def _sync_battle_structures(battle: "BattleState", tiles: dict[str, Any], items_dict: dict[str, Any]) -> list[int]:
    """Sync battle.structures from the current tile map.

    Adds towers placed after battle started, removes demolished towers, and leaves
    untouched towers intact so their reload timers and targeting state survive.
    Returns list of newly added SIDs.
    """
    from gameserver.models.structure import structure_from_item
    from gameserver.models.hex import HexCoord

    NON_STRUCTURE = {"empty", "path", "spawnpoint", "castle", "blocked", "void"}

    new_pos_types: dict[tuple[int, int], tuple[str, str]] = {}
    for tile_key, tile_val in tiles.items():
        tile_type = _tile_type(tile_val)
        if tile_type not in NON_STRUCTURE:
            q, r = map(int, tile_key.split(","))
            new_pos_types[(q, r)] = (tile_type, _tile_select(tile_val))

    sids_to_remove = [
        s.sid for s in battle.structures.values()
        if (s.position.q, s.position.r) not in new_pos_types
           or new_pos_types[(s.position.q, s.position.r)][0] != s.iid
    ]
    for sid in sids_to_remove:
        s = battle.structures.pop(sid)
        log.info("[sync_structures] Removed structure sid=%d iid=%s at (%d,%d)",
                 s.sid, s.iid, s.position.q, s.position.r)

    existing_pos: set[tuple[int, int]] = {
        (s.position.q, s.position.r) for s in battle.structures.values()
    }
    next_sid = max(battle.structures.keys(), default=0) + 1
    new_sids: list[int] = []

    for (q, r), (tile_type, tile_select) in new_pos_types.items():
        if (q, r) in existing_pos:
            continue
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


async def _run_battle_task(
    bid: int,
    battle: "BattleState",
    battle_svc: "BattleService",
    send_fn: Any,
    broadcast_interval_ms: float = 250.0,
) -> None:
    """Wrapper for the async battle loop with cleanup and resource transfer."""
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
            # Best-effort: client may have disconnected — swallow to avoid masking the outer crash
            log.debug("send_summary failed after timeout recovery", exc_info=True)
    except Exception:
        import traceback
        log.error("Battle loop crashed: %s", traceback.format_exc())

        battle.defender_won = True
        battle.is_finished = True

        from gameserver.engine.ai_service import AI_UID as _AI_UID
        if battle.army is not None and (battle.attacker is None or battle.attacker.uid != _AI_UID):
            for wave in battle.army.waves:
                wave.num_critters_spawned = 0
                wave.next_critter_ms = 0
            log.info("[battle] bid=%d army '%s' reset after crash", bid, battle.army.name)

        try:
            await battle_svc.send_summary(battle, send_fn, loot={})
            _summary_sent = True
        except Exception:
            # Client may have disconnected during crash recovery — swallow silently
            log.debug("send_summary failed during crash recovery", exc_info=True)

    try:
        log.info("[battle] bid=%d complete: attacker_wins=%s", bid, not battle.defender_won)

        loot: dict[str, Any] = {}
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

                gains_lines = ""
                if battle.attacker and battle.attacker.uid != 0:
                    gains = battle.attacker_gains.get(battle.attacker.uid, {})
                    if gains:
                        parts = ", ".join(f"+{int(v)} {k}" for k, v in gains.items() if v > 0)
                        if parts:
                            gains_lines = f"💰 Captured: {parts}\n"

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
        if battle.defender:
            _get_active_battles().pop(battle.defender.uid, None)


def _apply_artefact_steal(battle: "BattleState", svc: Any, attacker_won: bool) -> "str | None":
    """Roll per-artefact steal after a battle. AI attackers never steal artefacts."""
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
        chance = getattr(cfg, "base_artifact_steal_victory", 0.5) if cfg else 0.5
    else:
        chance = getattr(cfg, "base_artifact_steal_defeat", 0.05) if cfg else 0.05

    stolen = None
    for artefact in list(victim.artefacts):
        roll = _random.random()
        if roll < chance:
            victim.artefacts.remove(artefact)
            thief.artefacts.append(artefact)
            stolen = artefact
            log.info(
                "[LOOT] Artefact stolen: %s  thief uid=%d  victim uid=%d  roll=%.3f < chance=%.2f (attacker_won=%s)",
                artefact, thief.uid, victim.uid, roll, chance, attacker_won,
            )
            svc.empire_service.recalculate_effects(victim)
            svc.empire_service.recalculate_effects(thief)
            break
        else:
            log.info(
                "[LOOT] Artefact steal failed: %s  thief uid=%d  victim uid=%d  roll=%.3f >= chance=%.2f (attacker_won=%s)",
                artefact, thief.uid, victim.uid, roll, chance, attacker_won,
            )
    return stolen


def _compute_and_apply_loot(battle: "BattleState", svc: Any) -> dict[str, Any]:
    """Compute and apply loot on defender loss. Returns loot dict."""
    import random as _random

    defender = battle.defender
    attacker = battle.attacker
    if not defender or not attacker:
        return {}

    cfg = svc.game_config
    items = svc.upgrade_provider.items if svc.upgrade_provider else {}
    loot: dict[str, Any] = {"knowledge": None, "culture": 0.0, "artefact": None, "life_restored": 0.0}

    from gameserver.engine.ai_service import AI_UID as _AI_UID
    _attacker_is_ai = attacker.uid == _AI_UID
    if _attacker_is_ai:
        active = [
            (iid, rem) for iid, rem in defender.knowledge.items()
            if rem > 0 and items.get(iid)
        ]
        stealable_iids = [max(active, key=lambda x: (items[x[0]].effort - x[1]))[0]] if active else []
    else:
        stealable_iids = [iid for iid in defender.knowledge if iid not in attacker.knowledge]

    if stealable_iids:
        chosen_iid = _random.choice(stealable_iids)
        item = items.get(chosen_iid)
        effort = item.effort if item else 0.0
        min_pct = getattr(cfg, "min_lose_knowledge", 0.03) if cfg else 0.03
        max_pct = getattr(cfg, "max_lose_knowledge", 0.15) if cfg else 0.15
        pct = _random.uniform(min_pct, max_pct)
        current_remaining = defender.knowledge.get(chosen_iid, 0.0)
        already_researched = max(0.0, effort - current_remaining)
        gain = already_researched * pct
        if not _attacker_is_ai:
            attacker_remaining = attacker.knowledge.get(chosen_iid, effort)
            attacker.knowledge[chosen_iid] = max(0.0, attacker_remaining - gain)
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

    min_c = getattr(cfg, "min_lose_culture", 0.01) if cfg else 0.01
    max_c = getattr(cfg, "max_lose_culture", 0.05) if cfg else 0.05
    pct_culture = _random.uniform(min_c, max_c)
    culture_pool = defender.resources.get("culture", 0.0)
    culture_stolen = round(culture_pool * pct_culture, 2)
    if culture_stolen > 0:
        defender.resources["culture"] = max(0.0, culture_pool - culture_stolen)
        attacker.resources["culture"] = attacker.resources.get("culture", 0.0) + culture_stolen
        battle.defender_losses["culture"] = battle.defender_losses.get("culture", 0.0) + culture_stolen
        loot["culture"] = culture_stolen
        log.info("[LOOT] Culture stolen from uid=%d: %.1f (%.1f%%)",
                 defender.uid, culture_stolen, pct_culture * 100)

    from gameserver.util.effects import RESTORE_LIFE_AFTER_LOSS_OFFSET
    base_restore = getattr(cfg, "restore_life_after_loss_offset", 1.0) if cfg else 1.0
    effect_restore = defender.effects.get(RESTORE_LIFE_AFTER_LOSS_OFFSET, 0.0)
    total_restore = base_restore + effect_restore
    current_life = defender.resources.get("life", 0.0)
    max_life = getattr(defender, "max_life", 10.0)
    life_restored = min(total_restore, max(0.0, max_life - current_life))
    if life_restored > 0:
        defender.resources["life"] = current_life + life_restored
        loot["life_restored"] = round(life_restored, 2)
        log.info("[LOOT] Life restored to uid=%d: %.2f (base=%.1f + effect=%.1f)",
                 defender.uid, life_restored, base_restore, effect_restore)

    return loot


def _create_item_completed_handler() -> Callable[..., Any]:
    """Push an item_completed message to the owning player when a build/research finishes."""
    async def _async_item_completed(event: "ItemCompleted") -> None:
        svc = _svc()
        if svc.server:
            await svc.server.send_to(event.empire_uid, {"type": "item_completed", "iid": event.iid})
            log.debug("[push] item_completed iid=%s uid=%d", event.iid, event.empire_uid)

    def _on_item_completed(event: "ItemCompleted") -> None:
        asyncio.create_task(_async_item_completed(event))

    return _on_item_completed


def _create_attack_phase_handler() -> Callable[..., Any]:
    """Create a handler for AttackPhaseChanged events."""
    async def _async_phase_changed(event: "AttackPhaseChanged") -> None:
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

        attack = None
        for a in svc.attack_service.get_all_attacks():
            if a.attack_id == event.attack_id:
                attack = a
                break
        if attack and hasattr(attack, "_observers") and attack._observers:
            from gameserver.network.handlers.battle import _send_battle_state_to_observer
            for observer_uid in list(attack._observers):
                try:
                    await _send_battle_state_to_observer(attack, observer_uid)
                except Exception as exc:
                    log.exception("Failed to push battle_status on phase change to uid=%d: %s",
                                  observer_uid, exc)

    def _on_attack_phase_changed(event: "AttackPhaseChanged") -> None:
        asyncio.create_task(_async_phase_changed(event))

    return _on_attack_phase_changed


def _create_spy_arrived_handler() -> Callable[..., Any]:
    """Create a handler for SpyArrived events."""
    async def _async_spy_arrived(event: "SpyArrived") -> None:
        svc = _svc()
        attacker_uid = event.attacker_uid
        defender_uid = event.defender_uid

        defender = svc.empire_service.get(defender_uid)
        attacker_empire = svc.empire_service.get(attacker_uid)
        if defender is None or attacker_empire is None:
            log.warning("[spy] Empire not found: attacker=%d defender=%d", attacker_uid, defender_uid)
            return

        from gameserver.network.handlers.military import _build_spy_report
        report_text, report_data = _build_spy_report(defender, svc)

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
            await svc.server.send_to(attacker_uid, {
                "type": "spy_report",
                "attack_id": event.attack_id,
                "defender_uid": defender_uid,
                "defender_name": defender.name,
                **report_data,
            })

        inbox_body = f"🕵 Spy report on {defender.name}\n" + report_text
        await svc.database.send_message(from_uid=0, to_uid=attacker_uid, body=inbox_body)
        log.info("[spy] Report sent: attacker=%d defender=%d era=%s",
                 attacker_uid, defender_uid, report_data.get("era", "?"))

    def _on_spy_arrived(event: "SpyArrived") -> None:
        asyncio.create_task(_async_spy_arrived(event))

    return _on_spy_arrived


def _create_battle_observer_broadcast_handler() -> Callable[..., Any]:
    """Create a handler for BattleObserverBroadcast events."""
    async def _async_broadcast_to_observers(event: "BattleObserverBroadcast") -> None:
        svc = _svc()
        attack = None
        for a in svc.attack_service.get_all_attacks():
            if a.attack_id == event.attack_id:
                attack = a
                break
        if not attack or not getattr(attack, "_observers", None):
            return
        from gameserver.network.handlers.battle import _send_battle_state_to_observer
        for observer_uid in list(attack._observers):
            try:
                await _send_battle_state_to_observer(attack, observer_uid)
            except Exception as e:
                log.exception("Failed to send battle status to observer %d: %s", observer_uid, e)

    def _on_battle_observer_broadcast(event: "BattleObserverBroadcast") -> None:
        asyncio.create_task(_async_broadcast_to_observers(event))

    return _on_battle_observer_broadcast


def _abort_battle_setup(attack_id: int, army: Any = None) -> None:
    """Mark an attack FINISHED when battle creation fails."""
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


def _create_battle_start_handler() -> Callable[..., Any]:
    """Create a handler for BattleStartRequested events."""
    async def _async_create_battle(event: "BattleStartRequested") -> None:
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

        defender_empire = svc.empire_service.get(defender_uid)
        if defender_empire is None:
            log.error("[battle:start_requested] FAIL: defender %d not found", defender_uid)
            _abort_battle_setup(attack_id, attacking_army)
            return

        if not defender_empire.hex_map:
            log.error("[battle:start_requested] FAIL: defender %d has no map", defender_uid)
            _abort_battle_setup(attack_id, attacking_army)
            return

        from gameserver.engine.hex_pathfinding import find_path_from_spawn_to_castle
        tiles = defender_empire.hex_map
        critter_path = find_path_from_spawn_to_castle(tiles)

        if not critter_path:
            log.error("[battle:start_requested] FAIL: defender %d map has no valid path", defender_uid)
            _abort_battle_setup(attack_id, attacking_army)
            return

        structures_dict = {}
        if defender_empire.structures:
            structures_dict = dict(defender_empire.structures)

        from gameserver.models.structure import structure_from_item
        from gameserver.models.hex import HexCoord
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
                    log.debug("[battle:start_requested] Loaded structure sid=%d iid=%s at (%d,%d)",
                              structure.sid, structure.iid, q, r)

        bid = _core_mod._next_bid
        _core_mod._next_bid += 1

        existing_observers: set[int] = set()
        attack_obj = svc.attack_service.get(attack_id)
        if attack_obj and hasattr(attack_obj, "_observers"):
            existing_observers = set(attack_obj._observers)

        from gameserver.persistence.replay import ReplayRecorder
        replay_rec = ReplayRecorder(bid=bid, defender_uid=defender_uid, attacker_uid=attacker_uid)

        battle = BattleState(
            bid=bid,
            attack_id=attack_id,
            defender=defender_empire,
            attacker=attacker_empire,
            army=attacking_army,
            structures=structures_dict,
            observer_uids={attacker_uid, defender_uid} | existing_observers,
            critter_path=critter_path,
            recorder=replay_rec,
        )
        _get_active_battles()[defender_uid] = battle

        assert battle.recorder is not None
        log.info("[battle:start_requested] SUCCESS: battle %d created (attacker=%d, defender=%d)",
                 bid, attacker_uid, defender_uid)

        setup_msg = {
            "type": "battle_setup",
            "bid": bid,
            "replay_key": battle.recorder.replay_key,
            "defender_uid": defender_uid,
            "attacker_uid": attacker_uid,
            "defender_name": defender_empire.name if defender_empire else "",
            "attacker_name": attacker_empire.name if attacker_empire else "",
            "attacker_army_name": attacking_army.name if attacking_army else "",
            "tiles": tiles,
            "structures": [
                {"sid": s.sid, "iid": s.iid, "q": s.position.q, "r": s.position.r,
                 "damage": s.damage, "range": s.range, "select": s.select}
                for s in structures_dict.values()
            ],
            "path": [{"q": h.q, "r": h.r} for h in critter_path],
        }

        if svc.server:
            await svc.server.send_to(attacker_uid, setup_msg)
            await svc.server.send_to(defender_uid, setup_msg)

        if svc.database:
            from gameserver.util.push_service import notify_under_siege
            atk_display = attacker_empire.name if attacker_empire else "Someone"
            asyncio.ensure_future(notify_under_siege(svc.database, defender_uid, atk_display))

        battle.recorder.record(0, setup_msg)  # recorder asserted non-None above

        _initial_delay_ms = svc.game_config.initial_wave_delay_ms
        _wave_delay_offset_ms = (
            defender_empire.get_effect(fx.WAVE_DELAY_OFFSET, 0.0) if defender_empire else 0.0
        )
        log.info("[battle:wave_timers] defender=%d wave_delay_offset=%.0fms initial_delay=%.0fms",
                 defender_uid, _wave_delay_offset_ms, _initial_delay_ms)
        for _i, _wave in enumerate(attacking_army.waves):
            _wave.next_critter_ms = int(_i * _initial_delay_ms) + (_i + 1) * _wave_delay_offset_ms
            _wave.num_critters_spawned = 0
            log.info("[battle:wave_timers] wave[%d] next_critter_ms=%.0f", _i, _wave.next_critter_ms)

        items = svc.upgrade_provider.items if svc.upgrade_provider else {}
        battle_svc = BattleService(items=items, gc=svc.empire_service._gc if svc.empire_service else None)

        broadcast_interval_ms = 250.0
        if svc.game_config and hasattr(svc.game_config, "broadcast_interval_ms"):
            broadcast_interval_ms = svc.game_config.broadcast_interval_ms

        async def send_fn(uid: int, data: dict[str, Any]) -> bool:
            if svc.server:
                return bool(await svc.server.send_to(uid, data))
            return False

        asyncio.create_task(_run_battle_task(bid, battle, battle_svc, send_fn, broadcast_interval_ms))

    def sync_handler(event: "BattleStartRequested") -> None:
        asyncio.create_task(_async_create_battle(event))

    return sync_handler


async def _on_battle_start_requested(event: "BattleStartRequested") -> None:
    """Legacy entry point kept for compatibility — delegates to _create_battle_start_handler."""
    # Delegate directly — _create_battle_start_handler() is the factory; call the inner logic here
    from gameserver.engine.battle_service import BattleService
    from gameserver.models.battle import BattleState
    import gameserver.network.handlers._core as _core_mod

    svc = _svc()
    attacker_uid = event.attacker_uid
    defender_uid = event.defender_uid
    army_aid = event.army_aid
    attack_id = event.attack_id

    attacker_empire = svc.empire_service.get(attacker_uid)
    if attacker_empire is None:
        _abort_battle_setup(attack_id)
        return

    attacking_army = next((a for a in attacker_empire.armies if a.aid == army_aid), None)
    if attacking_army is None:
        _abort_battle_setup(attack_id)
        return

    defender_empire = svc.empire_service.get(defender_uid)
    if defender_empire is None or not defender_empire.hex_map:
        _abort_battle_setup(attack_id, attacking_army)
        return

    from gameserver.engine.hex_pathfinding import find_path_from_spawn_to_castle
    tiles = defender_empire.hex_map
    critter_path = find_path_from_spawn_to_castle(tiles)
    if not critter_path:
        _abort_battle_setup(attack_id, attacking_army)
        return

    structures_dict = dict(defender_empire.structures) if defender_empire.structures else {}

    from gameserver.models.structure import structure_from_item
    from gameserver.models.hex import HexCoord
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

    bid = _core_mod._next_bid
    _core_mod._next_bid += 1

    from gameserver.persistence.replay import ReplayRecorder
    replay_rec = ReplayRecorder(bid=bid, defender_uid=defender_uid, attacker_uid=attacker_uid)

    battle = BattleState(
        bid=bid,
        attack_id=attack_id,
        defender=defender_empire,
        attacker=attacker_empire,
        army=attacking_army,
        structures=structures_dict,
        observer_uids={attacker_uid, defender_uid},
        critter_path=critter_path,
        recorder=replay_rec,
    )
    _get_active_battles()[defender_uid] = battle

    setup_msg = {
        "type": "battle_setup",
        "bid": bid,
        "defender_uid": defender_uid,
        "attacker_uid": attacker_uid,
        "tiles": tiles,
        "structures": [
            {"sid": s.sid, "iid": s.iid, "q": s.position.q, "r": s.position.r,
             "damage": s.damage, "range": s.range, "select": s.select}
            for s in structures_dict.values()
        ],
        "path": [{"q": h.q, "r": h.r} for h in critter_path],
    }

    if svc.server:
        await svc.server.send_to(attacker_uid, setup_msg)
        await svc.server.send_to(defender_uid, setup_msg)

    _initial_delay_ms = svc.game_config.initial_wave_delay_ms
    _wave_delay_offset_ms = (
        defender_empire.get_effect(fx.WAVE_DELAY_OFFSET, 0.0) if defender_empire else 0.0
    )
    for _i, _wave in enumerate(attacking_army.waves):
        _wave.next_critter_ms = int((_i + 1) * _initial_delay_ms) + _wave_delay_offset_ms
        _wave.num_critters_spawned = 0

    items = svc.upgrade_provider.items if svc.upgrade_provider else {}
    battle_svc = BattleService(items=items)

    broadcast_interval_ms = 250.0
    if svc.game_config and hasattr(svc.game_config, "broadcast_interval_ms"):
        broadcast_interval_ms = svc.game_config.broadcast_interval_ms

    async def send_fn(uid: int, data: dict[str, Any]) -> bool:
        if svc.server:
            return bool(await svc.server.send_to(uid, data))
        return False

    asyncio.create_task(_run_battle_task(bid, battle, battle_svc, send_fn, broadcast_interval_ms))
