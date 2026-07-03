"""Attack strategy planner: strengthen → spy → attack state machine.

Phase order: strengthen → spy → wait_spy → attack → wait_result → strengthen → …

Strengthen phase buys era upgrades for all waves first, then adds waves up to
max(2, era_rank × 2), then transitions to spy. Slot buying and critter workshop
upgrades are always emitted (also as secondary strategy) so gold is never idle.
"""

from __future__ import annotations

import logging

from bot.analyzer import ERA_RANK
from bot.army_building import critter_power, next_skill, ruler_wave_target
from bot.savings import clear_goal

from .base import BotContext, Option, Planner

log = logging.getLogger("bot.planner.attack")

PRIO_ERA_UPGRADE = 14   # get all waves to current era — highest strengthen prio
PRIO_ADD_WAVE    = 13   # add waves up to max(2, era_rank * 2)
PRIO_ATTACK      = 10   # phase sequencing (spy, attack)
PRIO_BUY_SLOT    =  8   # always buy slots (also as secondary)
PRIO_CRITTER_UPG =  7   # workshop critter upgrade (also as secondary)

CRITTER_UPGRADE_STATS = ["health", "speed", "armour"]
MAX_UPGRADE_LEVEL = 20


def _mandatory(description: str, run, *, price: float = 0.0, gain: float = 1.0,
               priority: int = PRIO_ATTACK,
               saves_for: float = 0.0, goal_meta: dict | None = None) -> Option:
    return Option(category="attack", description=description, run=run,
                  price=price, gain=gain, mandatory=True, priority=priority,
                  saves_for=saves_for, goal_meta=goal_meta)


def _current_era_critters(critters: dict, era_rank: int,
                           ruler_iids: set, ctx: BotContext) -> list[str]:
    """IIDs of unlocked critters at the highest available era <= era_rank, by power."""
    candidates = [
        (iid, c) for iid, c in critters.items()
        if iid not in ruler_iids
        and int(c.get("era_index", 0)) <= era_rank
        and ctx.is_unlocked(c)
    ]
    if not candidates:
        return []
    best_era = max(int(c.get("era_index", 0)) for _, c in candidates)
    at_best = [(iid, c) for iid, c in candidates
               if int(c.get("era_index", 0)) == best_era]
    return [iid for iid, _ in sorted(at_best,
            key=lambda x: critter_power(x[1]), reverse=True)]


def _critter_upgrade_option(ctx: BotContext, iid: str) -> Option | None:
    """Next workshop upgrade (health → speed → armour) for a critter iid, or None."""
    upgrades = (ctx.summary.get("item_upgrades") or {}).get(iid, {})
    prices = ctx.summary.get("item_upgrade_prices") or {}
    for stat in CRITTER_UPGRADE_STATS:
        level = int(upgrades.get(stat, 0) or 0)
        if level >= MAX_UPGRADE_LEVEL:
            continue
        price = float(((prices.get(iid) or {})).get(stat, 0.0) or 0.0)
        if price <= 0:
            continue
        return Option(
            category="attack",
            description=f"upgrade critter {iid} {stat} (lv{level + 1})",
            price=price, gain=0.5, mandatory=True, priority=PRIO_CRITTER_UPG,
            run=lambda api, iid=iid, stat=stat: api.buy_item_upgrade(iid, stat))
    return None


class AttackPlanner(Planner):
    """Phases stored in strategy.params["phase"]:
    strengthen → spy → wait_spy → attack → wait_result → strengthen → …"""

    def propose_options(self, ctx: BotContext, *,
                        advance_phase: bool = True) -> list[Option]:
        options: list[Option] = []
        params = ctx.strategy.setdefault("params", {})
        target_uid = params.get("target_uid")
        target_name = params.get("target_name", "")

        if target_uid is None:
            if advance_phase:
                ctx.strategy["completed"] = True
            return options

        military = ctx.api.military()
        armies = military.get("armies", [])
        critters = ctx.items.get("critters", {})
        ruler_iids = set(ctx.items.get("rulers") or {})
        era_rank = ERA_RANK.get(ctx.summary.get("era", "stone"), 0)
        max_waves = max(2, era_rank * 2)

        # 1. Create army if none exists
        if not armies:
            if not advance_phase:
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

        # 2. Add first wave if army is empty
        if not waves:
            if not advance_phase:
                return options
            wave_price = float(army.get("next_wave_price", 0.0) or 0.0)
            options.append(_mandatory(
                f"add first wave to army {aid}",
                lambda api: api.add_wave(aid),
                price=wave_price, saves_for=wave_price,
                goal_meta={"item": "wave", "action": "add_wave", "sticky": True}))
            return options

        # 3. Place ruler (advance_phase only)
        if advance_phase:
            ruler_opt = self._ruler_step(ctx, armies, ruler_iids)
            if ruler_opt is not None:
                options.append(ruler_opt)

        # 4. Fill empty waves with best fitting critter (always, also as secondary)
        unlocked = [dict(c, iid=iid) for iid, c in critters.items()
                    if iid not in ruler_iids and ctx.is_unlocked(c)]
        for wn, wave in enumerate(waves):
            if wave.get("iid"):
                continue
            max_era = int(wave.get("max_era", 0) or 0)
            fitting = [c for c in unlocked if int(c.get("era_index", 0)) <= max_era]
            if not fitting:
                continue
            best = max(fitting, key=critter_power)
            best_iid = best["iid"]
            slots = int(wave.get("slots", 1) or 1)
            options.append(_mandatory(
                f"set wave {wn} to {best_iid}",
                lambda api, wn=wn, slots=slots, iid=best_iid:
                    api.set_wave(aid, wn, iid, slots),
                priority=PRIO_ATTACK))
            break  # one fill per tick

        # 5. Buy cheapest slot across all waves (always, also as secondary)
        if waves:
            cheapest_wave = min(waves,
                                key=lambda w: float(w.get("next_slot_price", 1e9)))
            slot_price = float(cheapest_wave.get("next_slot_price", 0.0) or 0.0)
            if slot_price > 0:
                wn = waves.index(cheapest_wave)
                options.append(_mandatory(
                    f"buy slot on wave {wn} (army {aid})",
                    lambda api, wn=wn: api.buy_critter_slot(aid, wn),
                    price=slot_price, gain=1.0, priority=PRIO_BUY_SLOT))

        # 6. Critter workshop upgrade — current-era critter (always, also as secondary)
        era_critters = _current_era_critters(critters, era_rank, ruler_iids, ctx)
        for iid in era_critters:
            upg_opt = _critter_upgrade_option(ctx, iid)
            if upg_opt is not None:
                options.append(upg_opt)
                break

        # --- Phase sequencing: only when advance_phase=True ---
        if not advance_phase:
            return options

        phase = params.get("phase", "strengthen")
        outgoing = ctx.summary.get("attacks_outgoing", [])

        if phase == "strengthen":
            options += self._strengthen_options(
                ctx, army, aid, waves, era_rank, max_waves, params)

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
            self._resolve_result(ctx, params, target_name)

        return options

    # ── strengthen ────────────────────────────────────────────────────────

    def _strengthen_options(self, ctx: BotContext, army: dict, aid: int,
                            waves: list, era_rank: int, max_waves: int,
                            params: dict) -> list[Option]:
        """Era upgrades first, then add waves, then transition to spy."""
        options: list[Option] = []

        # Era-upgrade every wave that is below current era (highest priority)
        for wn, wave in enumerate(waves):
            if int(wave.get("max_era", 0) or 0) < era_rank:
                price = float(wave.get("next_era_price", 0.0) or 0.0)
                options.append(_mandatory(
                    f"era-upgrade wave {wn} → era {era_rank}",
                    lambda api, wn=wn: api.buy_wave_era(aid, wn),
                    price=price, gain=2.0, priority=PRIO_ERA_UPGRADE,
                    saves_for=price,
                    goal_meta={"item": f"era-wave-{wn}", "action": "buy_wave_era"}))

        # All waves at current era?
        all_at_era = all(int(w.get("max_era", 0) or 0) >= era_rank for w in waves)
        if not all_at_era:
            return options  # keep saving / upgrading era before adding waves

        # Add waves up to max_waves
        if len(waves) < max_waves:
            price = float(army.get("next_wave_price", 0.0) or 0.0)
            options.append(_mandatory(
                f"add wave ({len(waves)}/{max_waves})",
                lambda api: api.add_wave(aid),
                price=price, gain=3.0, priority=PRIO_ADD_WAVE,
                saves_for=price,
                goal_meta={"item": "wave", "action": "add_wave"}))
        else:
            # All waves at era and at max count → proceed to attack
            clear_goal(ctx.memory)
            params["phase"] = "spy"

        return options

    # ── ruler placement ───────────────────────────────────────────────────

    def _ruler_step(self, ctx: BotContext, armies: list[dict],
                    ruler_iids: set[str]) -> Option | None:
        ruler = ctx.summary.get("ruler") or {}
        if not ruler.get("type"):
            return None

        # Ruler skill-up is handled by baseline; only handle placement here
        target = ruler_wave_target(armies, ruler_iids)
        if target is not None:
            t_aid, t_wn = target
            ruler_type = ruler["type"]
            return _mandatory(
                f"place ruler {ruler_type} in wave {t_wn} of army {t_aid}",
                lambda api: api.set_ruler_wave(t_aid, t_wn, ruler_type))
        return None

    # ── result resolution ─────────────────────────────────────────────────

    def _resolve_result(self, ctx: BotContext, params: dict,
                        target_name: str) -> None:
        history = ctx.memory.get("attack_history", [])
        for entry in reversed(history):
            if entry.get("opponent") != target_name:
                continue
            if entry.get("outcome") == "victory":
                clear_goal(ctx.memory)
                ctx.strategy["completed"] = True
            else:
                # Defeat → strengthen again before next attack
                params["phase"] = "strengthen"
            return

    def _goal_reached(self, history_entry: dict) -> bool:
        return history_entry.get("outcome") == "victory"
