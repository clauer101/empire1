"""Attack strategy planner: strengthen → spy → attack state machine.

Phase order: strengthen → spy → wait_spy → attack → wait_result → strengthen → …
"strengthen" only gates on having *some* army (>= 1 wave with a critter) — it
does not wait for the full wave-count/era target, since attacking is free and
that target is gold-gated and keeps moving as the empire advances era (it
could otherwise block attacking indefinitely).

Free vs. gold-spending options — this planner always runs (also as secondary
strategy, `advance_phase=False`) so the phase machine and army composition
keep making progress in the background no matter which strategy is nominally
active, but only the *free* parts of that do so unconditionally:
- Free, always-on regardless of active strategy: filling/refreshing waves
  with already-unlocked critters, ruler placement, phase sequencing (spy/
  attack/wait).
- Gold-spending (create army, add wave, buy slot, critter/era upgrades):
  gated on `is_active` (attack is the nominally active strategy). A bot
  currently in e.g. defense must not fund its army from that strategy's
  gold budget just because this planner is running as a free-riding
  secondary — see the `is_active` checks below.

Army composition rules:
- Target wave count: max(2, ceil(era_rank * 1.5)) — one army only.
- Every wave (empty or already filled) is kept on the best unlocked critter its
  own era cap (wave.max_era) allows; ties at the top era are broken uniformly
  at random so bots diverge instead of all fielding an identical army.
- The ruler is placed once, in a uniformly random existing wave.
- Wave era caps are raised toward (never above) the empire's own era_rank.
- Slot purchases are the lowest priority and always target the wave with the
  fewest slots, so slot counts grow evenly across waves.
"""

from __future__ import annotations

import logging
import math
import random
from collections import Counter

from bot.analyzer import ERA_RANK, score_targets
from bot.army_building import ruler_wave_target
from bot.savings import clear_goal

from .base import BotContext, Option, Planner, weighted_top_n

log = logging.getLogger("bot.planner.attack")

PRIO_RULER       = 17   # place the ruler — free, always first once unlocked
PRIO_FILL_WAVE   = 16   # fill an empty wave with the best current-era critter
PRIO_SWAP_WAVE   = 15   # refresh a filled wave whose critter era is outdated
PRIO_ADD_WAVE    = 14   # grow toward the target wave count
PRIO_ERA_UPGRADE = 12   # raise a wave's era cap toward era_rank
PRIO_ATTACK      = 10   # phase sequencing (spy, attack)
PRIO_BUY_SLOT    =  3   # even out slot counts (also as secondary)
PRIO_CRITTER_UPG =  2   # absolute last resort: only when no slot is buyable

CRITTER_UPGRADE_STATS = ["health", "speed", "armour"]


def _max_upgrade_level(era_rank: int) -> int:
    """Level cap for an item's era: 3 x (era_rank + 1) — every item is
    upgradable at least a little, later-era items allow more levels."""
    return 3 * (era_rank + 1)


def _focus_upgrade_stat(memory: dict, key: str, levels: dict,
                        stats: list[str], cap: int) -> str | None:
    """Commit to upgrading ONE stat for this item (remembered in `memory`)
    until it hits `cap`, then randomly try a different one.

    Without this, always trying stats in the same fixed order means every
    bot/item ends up maxing the same first stat (e.g. health) — sticking to
    one randomly-chosen focus per item, and rotating only once it's capped,
    spreads upgrades across different stats over time and across the bot
    population instead.
    """
    focus = memory.setdefault("upgrade_focus", {})
    stat = focus.get(key)
    if stat is not None and int(levels.get(stat, 0)) >= cap:
        stat = None
    if stat is None:
        candidates = [s for s in stats if int(levels.get(s, 0)) < cap]
        if not candidates:
            focus.pop(key, None)
            return None
        stat = random.choice(candidates)
        focus[key] = stat
    return stat


def _mandatory(description: str, run, *, price: float = 0.0, gain: float = 1.0,
               priority: int = PRIO_ATTACK,
               saves_for: float = 0.0, goal_meta: dict | None = None) -> Option:
    return Option(category="attack", description=description, run=run,
                  price=price, gain=gain, mandatory=True, priority=priority,
                  saves_for=saves_for, goal_meta=goal_meta)


def _target_waves(era_rank: int) -> int:
    """Target wave count for the (single) attack army: max(2, ceil(era_rank*1.5))."""
    return max(2, math.ceil(era_rank * 1.5))


def _era_rank_of(critter: dict) -> int:
    """A critter catalog entry's era rank.

    The catalog (GET /api/empire/items → critters) stores the era as the
    string key `era` (e.g. "bronze"), not an integer — unlike wave.max_era
    (already an int on the same 0..8 scale). Must go through ERA_RANK.
    """
    return ERA_RANK.get(critter.get("era", "stone"), 0)


def _top_era_pick(candidates: list[dict]) -> dict | None:
    """Uniformly random critter among those at the highest era rank present.

    Multiple critters can share the highest reachable era; picking randomly
    among them (instead of always the single strongest by critter_power)
    spreads variety across the bot population per the era-tie rule.
    """
    if not candidates:
        return None
    best_era = max(_era_rank_of(c) for c in candidates)
    at_best = [c for c in candidates if _era_rank_of(c) == best_era]
    return random.choice(at_best)


def _most_common_wave_critter(waves: list[dict], ruler_iids: set) -> str | None:
    """The critter iid appearing in the most placed (non-ruler) waves.

    Upgrades apply per iid regardless of how many waves/slots use it, so
    upgrading whichever critter type is most represented in the army benefits
    the largest share of it. Ties broken by iid for determinism."""
    counts = Counter(
        iid for w in waves
        if (iid := w.get("iid")) and iid not in ruler_iids
    )
    if not counts:
        return None
    best = max(counts.values())
    return min(iid for iid, n in counts.items() if n == best)


def _critter_upgrade_option(ctx: BotContext, iid: str) -> Option | None:
    """Next workshop upgrade for a critter iid, or None — focuses on one
    randomly-picked stat until it hits the era-scaled cap (see
    `_focus_upgrade_stat`/`_max_upgrade_level`).

    Last priority: only ever proposed once nothing more impactful (fill/swap/
    ruler/growth/slot) is available or affordable this cycle."""
    upgrades = (ctx.summary.get("item_upgrades") or {}).get(iid, {})
    price = float((ctx.summary.get("item_upgrade_prices") or {}).get(iid, 0.0) or 0.0)
    if price <= 0:
        return None
    critter = ctx.items.get("critters", {}).get(iid, {})
    cap = _max_upgrade_level(_era_rank_of(critter))
    stat = _focus_upgrade_stat(ctx.memory, iid, upgrades, CRITTER_UPGRADE_STATS, cap)
    if stat is None:
        return None
    level = int(upgrades.get(stat, 0) or 0)
    return Option(
        category="attack",
        description=f"upgrade critter {iid} {stat} (lv{level + 1})",
        price=price, gain=0.5, mandatory=True, priority=PRIO_CRITTER_UPG,
        run=lambda api, iid=iid, stat=stat: api.buy_item_upgrade(iid, stat))


def _empire_list(ctx: BotContext) -> list[dict]:
    """ctx.api.empires() returns {"empires": [...]}, not a bare list."""
    empires = ctx.api.empires()
    return empires if isinstance(empires, list) else (empires or {}).get("empires", [])


class AttackPlanner(Planner):
    """Sending an attack (spy/attack calls) costs no gold, so the phase
    machine runs regardless of whether "attack" is the nominally active
    strategy or defense is (e.g. temporarily forced after a lost defense).
    `advance_phase` no longer gates the phase sequencing. Gold-spending army
    upkeep (create army, add wave, buy slot, upgrades — see module docstring)
    IS gated on `is_active`, so a non-attack strategy's gold isn't spent on
    the army in the background.

    When attack IS the active strategy its target/phase live in
    `strategy.params` (so a fresh roll/override controls them). When it is
    NOT active, `ctx.strategy` belongs to another strategy (e.g. defense) —
    this planner then keeps its own persistent target/phase in
    `memory["attack_state"]` and self-selects a target via `score_targets`
    when it doesn't have one yet, so it keeps attacking (with whatever army
    it already has) in the background no matter what the active strategy is.

    Phases: strengthen → spy → wait_spy → attack → wait_result → strengthen → …
    """

    def propose_options(self, ctx: BotContext, *,
                        advance_phase: bool = True) -> list[Option]:
        options: list[Option] = []
        is_active = ctx.strategy.get("type") == "attack"
        params = (ctx.strategy.setdefault("params", {}) if is_active
                  else ctx.memory.setdefault("attack_state", {}))
        target_uid = params.get("target_uid")
        target_name = params.get("target_name", "")

        if target_uid is None:
            if is_active:
                ctx.strategy["completed"] = True
                return options
            # Not the active strategy: self-select a target so attacking
            # keeps happening in the background regardless of what is.
            targets = score_targets(
                _empire_list(ctx), ctx.summary.get("uid", 0),
                float(ctx.summary.get("resources", {}).get("culture", 0.0)),
                ctx.summary.get("era", "stone"), ctx.memory)
            if not targets:
                return options
            # Sample across the whole viable pool (see roll_strategy) instead
            # of always the single top-scored target, so bots spread across
            # different opponents instead of all converging on whichever
            # empire is globally weakest.
            top = weighted_top_n(targets, key=lambda t: t.get("score", 0.0),
                                 n=len(targets))
            params.update({"target_uid": int(top["uid"]),
                           "target_name": top.get("name", ""),
                           "phase": "strengthen"})
            target_uid = params["target_uid"]
            target_name = params["target_name"]

        military = ctx.api.military()
        armies = military.get("armies", [])
        critters = ctx.items.get("critters", {})
        ruler_iids = set(ctx.items.get("rulers") or {})
        era_rank = ERA_RANK.get(ctx.summary.get("era", "stone"), 0)
        target_waves = _target_waves(era_rank)

        # 1. Create army if none exists (only one army is ever built) — gold
        # spend, so only while attack is the actively chosen strategy: a bot
        # sitting in defense (or any other strategy) must not fund an army
        # from that budget just because AttackPlanner runs as a free-riding
        # background/secondary planner.
        if not armies:
            if not is_active:
                return options
            army_price = float(ctx.summary.get("army_price", 0.0) or 0.0)
            options.append(_mandatory(
                "create army", lambda api: api.create_army("Raiders"),
                price=army_price, saves_for=army_price,
                goal_meta={"item": "army", "action": "army", "sticky": True}))
            return options

        army = armies[0]
        aid = army["aid"]
        waves = army.get("waves", [])

        # 2. Add first wave if army is empty — gold spend, active-only (see above).
        if not waves:
            if not is_active:
                return options
            wave_price = float(army.get("next_wave_price", 0.0) or 0.0)
            options.append(_mandatory(
                f"add first wave to army {aid}",
                lambda api: api.add_wave(aid),
                price=wave_price, saves_for=wave_price,
                goal_meta={"item": "wave", "action": "add_wave", "sticky": True}))
            return options

        # 3. Place ruler — random existing wave
        ruler_opt = self._ruler_step(ctx, aid, waves, ruler_iids)
        if ruler_opt is not None:
            options.append(ruler_opt)

        unlocked = [dict(c, iid=iid) for iid, c in critters.items()
                    if iid not in ruler_iids and ctx.is_unlocked(c)]

        def _best_for_wave(wave: dict) -> dict | None:
            max_era = int(wave.get("max_era", 0) or 0)
            fitting = [c for c in unlocked if _era_rank_of(c) <= max_era]
            return _top_era_pick(fitting)

        # 4. Fill EVERY empty wave with the best (random-tie-broken) top-era
        #    critter it can hold — free, so all of them are proposed at once
        #    (not just the first) so a backlog clears within one tick's
        #    action budget instead of trickling one wave per cycle.
        for wn, wave in enumerate(waves):
            if wave.get("iid"):
                continue
            best = _best_for_wave(wave)
            if best is None:
                continue
            slots = int(wave.get("slots", 1) or 1)
            options.append(_mandatory(
                f"set wave {wn} to {best['iid']}",
                lambda api, wn=wn, slots=slots, iid=best["iid"]:
                    api.set_wave(aid, wn, iid, slots),
                priority=PRIO_FILL_WAVE))

        # 5. Refresh EVERY filled (non-ruler) wave whose critter era is now
        #    outdated — free, so all of them are proposed at once (see
        #    above). The "always the best critter" rule applies to existing
        #    waves too, not just freshly-added ones.
        for wn, wave in enumerate(waves):
            cur_iid = wave.get("iid") or ""
            if not cur_iid or cur_iid in ruler_iids:
                continue
            best = _best_for_wave(wave)
            if best is None:
                continue
            cur_era = _era_rank_of(critters.get(cur_iid, {}))
            if cur_era >= _era_rank_of(best):
                continue  # already at the top era this wave can hold
            slots = int(wave.get("slots", 1) or 1)
            options.append(_mandatory(
                f"switch wave {wn} to {best['iid']}",
                lambda api, wn=wn, slots=slots, iid=best["iid"]:
                    api.set_wave(aid, wn, iid, slots),
                priority=PRIO_SWAP_WAVE))

        # 6-9 all spend gold (slot purchase, critter upgrade, era upgrade,
        # add wave) — only while attack is the active strategy. Steps 3-5
        # above (ruler placement, wave fill/refresh with already-unlocked
        # critters) stay free-riding in the background since they cost
        # nothing; these must not drain a defense-strategy gold budget.
        if is_active:
            # 6. Buy a slot on the wave with the fewest slots — last resort,
            #    keeps slot counts even across waves; never on the ruler's wave.
            slot_candidates = [w for w in waves if w.get("iid") not in ruler_iids]
            if slot_candidates:
                fewest = min(slot_candidates, key=lambda w: int(w.get("slots", 1) or 1))
                slot_price = float(fewest.get("next_slot_price", 0.0) or 0.0)
                if slot_price > 0:
                    wn = waves.index(fewest)
                    options.append(_mandatory(
                        f"buy slot on wave {wn} (army {aid})",
                        lambda api, wn=wn: api.buy_critter_slot(aid, wn),
                        price=slot_price, gain=1.0, priority=PRIO_BUY_SLOT))

            # 7. Critter workshop upgrade — the most-placed critter type across
            #    the army's waves; absolute last priority (see PRIO_CRITTER_UPG).
            common_iid = _most_common_wave_critter(waves, ruler_iids)
            if common_iid is not None:
                upg_opt = _critter_upgrade_option(ctx, common_iid)
                if upg_opt is not None:
                    options.append(upg_opt)

            # 8. Era-upgrade waves toward era_rank and 9. grow toward the target
            # wave count. These used to run ONLY during the "strengthen" phase
            # and had to be fully satisfied (every wave at era_rank AND at the
            # wave-count target) before spy/attack could even start — since
            # both are gold-gated and the target keeps moving as the empire
            # advances era, that could block attacking indefinitely. Now they
            # run any time attack is active, so improving the army doesn't
            # gate the attack on ever "finishing" it.
            options += self._growth_options(ctx, army, aid, waves, era_rank, target_waves)

        # --- Phase sequencing: always runs, active or not (see class docstring) ---
        phase = params.get("phase", "strengthen")
        outgoing = ctx.summary.get("attacks_outgoing", [])

        if phase == "strengthen":
            # Attack with whatever the army currently has — as soon as at
            # least one wave carries a critter (any era), there is something
            # to send. No need to wait for the full wave-count/era target;
            # growth keeps happening in the background (step 8/9 above).
            if any(w.get("iid") and w.get("iid") not in ruler_iids for w in waves):
                clear_goal(ctx.memory)
                params["phase"] = "spy"

        elif phase == "spy":
            params["phase"] = "wait_spy"
            options.append(_mandatory(
                f"spy on {target_name} ({target_uid})",
                lambda api: api.spy_attack(target_uid, target_name)))

        elif phase == "wait_spy":
            if not outgoing:
                params["phase"] = "attack"

        elif phase == "attack":
            if not outgoing:
                params["phase"] = "wait_result"
                options.append(_mandatory(
                    f"attack {target_name} ({target_uid}) with army {aid}",
                    lambda api: api.attack(target_uid, target_name, aid)))

        elif phase == "wait_result":
            self._resolve_result(ctx, params, target_name, is_active)

        return options

    # ── background army growth (always on, never blocks attacking) ────────

    def _growth_options(self, ctx: BotContext, army: dict, aid: int,
                        waves: list, era_rank: int,
                        target_waves: int) -> list[Option]:
        """Era upgrades (capped at era_rank) and wave growth toward
        target_waves. Purely opportunistic — competes on Option priority with
        everything else (add-wave ranks above era-upgrade), never gates the
        spy/attack phase machine."""
        options: list[Option] = []

        for wn, wave in enumerate(waves):
            if int(wave.get("max_era", 0) or 0) < era_rank:
                price = float(wave.get("next_era_price", 0.0) or 0.0)
                options.append(_mandatory(
                    f"era-upgrade wave {wn} → era {era_rank}",
                    lambda api, wn=wn: api.buy_wave_era(aid, wn),
                    price=price, gain=2.0, priority=PRIO_ERA_UPGRADE,
                    saves_for=price,
                    goal_meta={"item": f"era-wave-{wn}", "action": "buy_wave_era"}))

        if len(waves) < target_waves:
            price = float(army.get("next_wave_price", 0.0) or 0.0)
            options.append(_mandatory(
                f"add wave ({len(waves)}/{target_waves})",
                lambda api: api.add_wave(aid),
                price=price, gain=3.0, priority=PRIO_ADD_WAVE,
                saves_for=price,
                goal_meta={"item": "wave", "action": "add_wave"}))

        return options

    # ── ruler placement ───────────────────────────────────────────────────

    def _ruler_step(self, ctx: BotContext, aid: int, waves: list[dict],
                    ruler_iids: set[str]) -> Option | None:
        ruler = ctx.summary.get("ruler") or {}
        if not ruler.get("type"):
            return None

        # Ruler skill-up is handled by baseline; only handle placement here.
        wn = ruler_wave_target(waves, ruler_iids)
        if wn is not None:
            ruler_type = ruler["type"]
            return _mandatory(
                f"place ruler {ruler_type} in wave {wn} of army {aid}",
                lambda api: api.set_ruler_wave(aid, wn, ruler_type),
                priority=PRIO_RULER)
        return None

    # ── result resolution ─────────────────────────────────────────────────

    def _resolve_result(self, ctx: BotContext, params: dict,
                        target_name: str, is_active: bool) -> None:
        history = ctx.memory.get("attack_history", [])
        for entry in reversed(history):
            if entry.get("opponent") != target_name:
                continue
            if entry.get("outcome") == "victory":
                clear_goal(ctx.memory)
                if is_active:
                    # Read by run_bot.py to roll a fresh (still attack) strategy.
                    ctx.strategy["completed"] = True
                else:
                    # Not the active strategy (e.g. defense is) — nothing reads
                    # "completed" for us; just drop the target so a fresh one
                    # is self-selected next cycle instead of re-attacking a
                    # target we already beat.
                    params.clear()
            else:
                # Defeat → strengthen again before next attack
                params["phase"] = "strengthen"
            return
