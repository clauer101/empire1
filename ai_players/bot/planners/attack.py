"""Attack strategy planner: spy → attack state machine against a chosen target.

Extras: ruler deployment (choose → skill-up → place in a wave) and
strengthen-on-defeat (slots / wave eras / waves / armies) — see
bot/army_building.py and docs/strategies/attack.md.

Emits at most one Option per cycle. Sequencing actions (army/wave setup, spy,
attack, strengthen) are mandatory so they win their tier when attack is the
active strategy. As a SECONDARY strategy (advance_phase=False) only idempotent,
non-phase options (fill empty waves) are emitted so the phase machine is never
advanced out of turn.
"""

from __future__ import annotations

import logging
import time

from bot.api_client import ApiError
from bot.army_building import (
    MAX_STRENGTHEN_ROUNDS,
    next_skill,
    ruler_wave_target,
    strengthen_plan,
)
from bot.savings import clear_goal

from .base import BotContext, Option, Planner, weighted_top_n

log = logging.getLogger("bot.planner.attack")

SKILL_RETRY_S = 3600.0  # retry skill-up an hour after a "no points" rejection
PRIO_ATTACK = 10        # mandatory priority for attack sequencing options


def _mandatory(description: str, run, *, price: float = 0.0, gain: float = 1.0,
               saves_for: float = 0.0, goal_meta: dict | None = None) -> Option:
    return Option(category="attack", description=description, run=run,
                  price=price, gain=gain, mandatory=True, priority=PRIO_ATTACK,
                  saves_for=saves_for, goal_meta=goal_meta)


class AttackPlanner(Planner):
    """Phases stored in strategy.params["phase"]:
    spy → wait_spy → attack → wait_result (→ strengthen → attack)."""

    def __init__(self, prefer_artifacts: bool = False):
        self.prefer_artifacts = prefer_artifacts

    def propose_options(self, ctx: BotContext, *,
                        advance_phase: bool = True) -> list[Option]:
        opt = self._propose_one(ctx, advance_phase=advance_phase)
        return [opt] if opt is not None else []

    def _propose_one(self, ctx: BotContext, *, advance_phase: bool) -> Option | None:
        params = ctx.strategy.setdefault("params", {})
        target_uid = params.get("target_uid")
        target_name = params.get("target_name", "")
        if target_uid is None:
            if advance_phase:
                ctx.strategy["completed"] = True
            return None

        military = ctx.api.military()
        armies = military.get("armies", [])

        # 1. Ensure an army exists; save toward it when unaffordable
        if not armies:
            if not advance_phase:
                return None  # don't create armies as a secondary strategy
            army_price = float(ctx.summary.get("army_price", 0.0) or 0.0)
            if ctx.gold >= army_price:
                clear_goal(ctx.memory)
                return _mandatory("create army",
                                  lambda api: api.create_army("Raiders"),
                                  price=army_price)
            return _mandatory(
                "create army (saving)", lambda api: None, price=army_price,
                saves_for=army_price if army_price > 0 else 0.0,
                goal_meta={"item": "army", "action": "army", "sticky": True})

        army = armies[0]
        aid = army["aid"]
        ruler_iids = set(ctx.items.get("rulers") or {})

        # 1b. A fresh army has no waves yet — buy the first one
        if not army.get("waves"):
            if not advance_phase:
                return None
            wave_price = float(army.get("next_wave_price", 0.0) or 0.0)
            if ctx.gold >= wave_price:
                clear_goal(ctx.memory)
                return _mandatory(f"add first wave to army {aid}",
                                  lambda api: api.add_wave(aid), price=wave_price)
            return _mandatory(
                f"add first wave to army {aid} (saving)", lambda api: None,
                price=wave_price, saves_for=wave_price if wave_price > 0 else 0.0,
                goal_meta={"item": "wave", "action": "add wave", "sticky": True})

        # 2. Ruler: choose, level skills, place into a wave
        if advance_phase:
            ruler_opt = self._ruler_step(ctx, armies, ruler_iids)
            if ruler_opt is not None:
                return ruler_opt

        # 3. Fill empty waves with the strongest affordable critter (idempotent,
        #    so it is allowed even as a secondary strategy).
        critters = ctx.items.get("critters", {})
        unlocked = [(iid, c) for iid, c in critters.items() if ctx.is_unlocked(c)]
        if unlocked:
            picked = weighted_top_n(
                unlocked,
                key=lambda c: float((c[1].get("costs") or {}).get("gold", 0.0)),
                n=ctx.top_n)
            best_iid = picked[0]
            for wn, wave in enumerate(army.get("waves", [])):
                if not wave.get("iid"):
                    slots = int(wave.get("slots", 1) or 1)
                    return _mandatory(
                        f"set wave {wn} to {best_iid}",
                        lambda api, wn=wn, slots=slots:
                            api.set_wave(aid, wn, best_iid, slots))

        # Everything past here is phase sequencing — never as a secondary.
        if not advance_phase:
            return None

        # 4. Phase machine
        phase = params.get("phase", "spy")
        outgoing = ctx.summary.get("attacks_outgoing", [])

        if phase == "spy":
            params["phase"] = "wait_spy"
            return _mandatory(f"spy on {target_name} ({target_uid})",
                              lambda api: api.spy_attack(target_uid, target_name))

        if phase == "wait_spy":
            if not outgoing:
                params["phase"] = "attack"
            return None

        if phase == "attack":
            if outgoing:
                return None  # army busy
            params["phase"] = "wait_result"
            return _mandatory(
                f"attack {target_name} ({target_uid}) with army {aid}",
                lambda api: api.attack(target_uid, target_name, aid))

        if phase == "wait_result":
            self._resolve_result(ctx, params, target_name)
            return None

        if phase == "strengthen":
            return self._strengthen_step(ctx, military, ruler_iids, params)

        return None

    # ── result resolution ────────────────────────────────────────────────
    def _resolve_result(self, ctx: BotContext, params: dict, target_name: str) -> None:
        history = ctx.memory.get("attack_history", [])
        for entry in reversed(history):
            if entry.get("opponent") != target_name:
                continue
            if self._goal_reached(entry):
                clear_goal(ctx.memory)
                ctx.strategy["completed"] = True
            elif entry["outcome"] == "defeat":
                defeats = int(params.get("defeats", 0)) + 1
                params["defeats"] = defeats
                if defeats > MAX_STRENGTHEN_ROUNDS:
                    log.info("giving up on %s after %d defeats", target_name, defeats)
                    clear_goal(ctx.memory)
                    ctx.strategy["completed"] = True  # triggers re-roll
                else:
                    log.info("defeat #%d vs %s — strengthening army", defeats, target_name)
                    params["phase"] = "strengthen"
            else:
                params["phase"] = "attack"  # victory but goal not met: again
            return

    # ── ruler deployment ──────────────────────────────────────────────────

    def _ruler_step(self, ctx: BotContext, armies: list[dict],
                    ruler_iids: set[str]) -> Option | None:
        ruler = ctx.summary.get("ruler") or {}

        # a) ruler claiming is handled by the baseline planner.
        if not ruler.get("type"):
            return None

        # b) spend skill points (server answers success:false when none available)
        blocked_until = float(ctx.memory.get("ruler_skill_blocked_until", 0.0) or 0.0)
        skill = next_skill(ruler)
        if skill and time.time() >= blocked_until:
            def run_skill_up(api, skill=skill):
                try:
                    result = api.ruler_skill_up(skill)
                except ApiError as e:
                    if not 400 <= e.status < 500:
                        raise
                    result = {"success": False, "error": e.body}
                if isinstance(result, dict) and result.get("success") is False:
                    ctx.memory["ruler_skill_blocked_until"] = time.time() + SKILL_RETRY_S
                    log.info("skill-up %s rejected, retry in 1h", skill)
                return result
            return _mandatory(f"ruler skill-up {skill}", run_skill_up)

        # c) place the ruler into a wave
        target = ruler_wave_target(armies, ruler_iids)
        if target is not None:
            t_aid, t_wn = target
            ruler_type = ruler["type"]
            return _mandatory(
                f"place ruler {ruler_type} in wave {t_wn} of army {t_aid}",
                lambda api: api.set_ruler_wave(t_aid, t_wn, ruler_type))
        return None

    # ── strengthen on defeat ──────────────────────────────────────────────

    def _strengthen_step(self, ctx: BotContext, military: dict,
                         ruler_iids: set[str], params: dict) -> Option | None:
        options = strengthen_plan(military, ctx.summary, ruler_iids)
        if not options:
            params["phase"] = "attack"
            return None
        best = options[0]
        if best.price > ctx.gold:
            return _mandatory(
                f"{best.description} (saving)", lambda api: None, price=best.price,
                saves_for=best.price,
                goal_meta={"item": best.kind, "action": best.description, "sticky": True})
        clear_goal(ctx.memory)
        params["phase"] = "attack"
        return self._execute_strengthen(best)

    @staticmethod
    def _execute_strengthen(best) -> Option | None:
        """Map a StrengthenOption to its mandatory Option (shared by build-up
        and post-defeat strengthening). Cheap high-ROI buys (e.g. a slot on a
        near-empty wave) are ranked first by strengthen_plan."""
        if best.kind == "switch_critter":
            return _mandatory(
                best.description, price=best.price, gain=best.gain,
                run=lambda api: api.set_wave(best.aid, best.wave_number,
                                             best.critter_iid, best.slots))
        if best.kind == "buy_slot":
            return _mandatory(
                best.description, price=best.price, gain=best.gain,
                run=lambda api: api.buy_critter_slot(best.aid, best.wave_number))
        if best.kind == "buy_wave_era":
            return _mandatory(
                best.description, price=best.price, gain=best.gain,
                run=lambda api: api.buy_wave_era(best.aid, best.wave_number))
        if best.kind == "add_wave":
            return _mandatory(best.description, price=best.price, gain=best.gain,
                              run=lambda api: api.add_wave(best.aid))
        if best.kind == "create_army":
            return _mandatory(best.description, price=best.price, gain=best.gain,
                              run=lambda api: api.create_army("Raiders II"))
        return None

    def _goal_reached(self, history_entry: dict) -> bool:
        return history_entry.get("outcome") == "victory"
