"""Baseline obligations that apply to EVERY strategy, before the strategy planner runs.

1. Defense must never be neglected: a defensive breach triggers an immediate
   defensive action, and a minimum tower count (scaling with the bot's era) is
   maintained regardless of the active strategy.
2. Research and buildings are always pursued when queues are empty.
   Buildings prefer items with economic effects. Research prefers economic items.
3. Citizens are upgraded whenever comfortably affordable.
4. Ruler skill-ups are spent as they become available.
5. Savings goals are respected: queue filling only spends gold above an active
   goal (see bot/savings.py); the goal-owning planner bypasses the cap.
"""

from __future__ import annotations

import time

from bot.analyzer import ERA_RANK
from bot.api_client import ApiError
from bot.army_building import next_skill, pick_ruler

from .base import Action, BotContext, Option, cheapest_affordable
from .defense import DefensePlanner

_defense = DefensePlanner()

FLOOR_BASE_TOWERS = 2
FLOOR_TOWERS_PER_ERA = 2

PRIO_BREACH      = 30
PRIO_TOWER_FLOOR = 20
PRIO_BUILD_QUEUE = 15  # above all defense options (10-12), below tower floor
PRIO_RESEARCH    = 15  # same level as build
PRIO_CITIZEN     = 14
PRIO_RULER_SKILL = 13

RULER_CLAIM_GAIN  = 100.0
GAIN_ECON_ITEM    = 2.0
GAIN_PLAIN_ITEM   = 1.0
GAIN_CITIZEN      = 3.0
GAIN_RULER_SKILL  = 50.0
SKILL_RETRY_S     = 120.0   # per-skill retry after level-requirement failure

ECON_EFFECTS = (
    "gold_modifier", "gold_offset", "culture_modifier", "culture_offset",
    "research_speed_modifier", "research_speed_offset",
    "build_speed_modifier", "citizen_effect_modifier",
)

TERRAIN_TILES = {"void", "empty", "path", "spawnpoint", "castle"}


def _has_econ_effect(item: dict) -> bool:
    effects = item.get("effects") or {}
    return any(k in effects for k in ECON_EFFECTS)


def min_towers(ctx: BotContext) -> int:
    era_rank = ERA_RANK.get(ctx.summary.get("era", "stone"), 0)
    return FLOOR_BASE_TOWERS + FLOOR_TOWERS_PER_ERA * era_rank


def placed_towers(ctx: BotContext) -> int:
    tiles = ctx.get_map().get("tiles", {})
    def _type(v):
        return v.get("type", "") if isinstance(v, dict) else str(v)
    return sum(1 for v in tiles.values() if _type(v) not in TERRAIN_TILES)


def _best_defense_option(ctx: BotContext) -> Option | None:
    options = _defense.propose_options(ctx)
    if not options:
        return None
    key = lambda o: (o.tier(), o.priority, o.base_score())  # noqa: E731
    affordable = [o for o in options if ctx.affordable_option(o)]
    return max(affordable or options, key=key)


def baseline_options(ctx: BotContext) -> list[Option]:
    """Emit baseline obligation options."""
    options: list[Option] = []

    # 1a. Breach response
    if ctx.memory.get("pending_breach"):
        base = _best_defense_option(ctx)
        ctx.memory["pending_breach"] = False
        if base:
            options.append(Option(
                category="baseline", mandatory=True, priority=PRIO_BREACH,
                description=f"baseline defense (breach response): {base.description}",
                run=base.run, price=base.price, gain=base.gain,
                saves_for=base.saves_for, goal_meta=base.goal_meta))

    # 1b. Tower floor
    placed = placed_towers(ctx)
    needed = min_towers(ctx)
    if placed < needed:
        base = _best_defense_option(ctx)
        if base:
            options.append(Option(
                category="baseline", mandatory=True, priority=PRIO_TOWER_FLOOR,
                description=f"baseline defense (towers {placed}/{needed}): "
                            f"{base.description}",
                run=base.run, price=base.price, gain=base.gain,
                saves_for=base.saves_for, goal_meta=base.goal_meta))

    # 1c. Claim ruler (free)
    ruler = ctx.summary.get("ruler") or {}
    if not ruler.get("type"):
        unlocked = float((ctx.summary.get("effects") or {}).get("ruler_unlock", 0) or 0)
        if unlocked > 0:
            iid = pick_ruler(ctx.items.get("rulers", {}))
            if iid:
                options.append(Option(
                    category="baseline", price=0.0, gain=RULER_CLAIM_GAIN,
                    description=f"baseline claim ruler {iid}",
                    run=lambda api, iid=iid: api.choose_ruler(iid)))

    # 2. Research queue — always keep something researching
    if not ctx.summary.get("research_queue"):
        # Resume paused items first (costs already paid, re-queueing is free)
        paused = {iid: rem for iid, rem in (ctx.summary.get("knowledge") or {}).items()
                  if rem and rem > 0}
        if paused:
            resume_iid = min(paused, key=paused.__getitem__)  # most-progressed first
            options.append(Option(
                category="baseline", price=0.0, gain=GAIN_PLAIN_ITEM,
                mandatory=True, priority=PRIO_RESEARCH,
                description=f"baseline research (resume) {resume_iid}",
                run=lambda api, iid=resume_iid: api.build(iid)))
        else:
            knowledge = ctx.items.get("knowledge", {})
            econ_iid = cheapest_affordable(knowledge, ctx, _has_econ_effect,
                                           respect_savings=False)
            iid = econ_iid or cheapest_affordable(knowledge, ctx, respect_savings=False)
            if iid:
                item = knowledge.get(iid, {})
                price = float((item.get("costs") or {}).get("gold", 0.0))
                options.append(Option(
                    category="baseline", price=price,
                    gain=GAIN_ECON_ITEM if iid == econ_iid else GAIN_PLAIN_ITEM,
                    mandatory=True, priority=PRIO_RESEARCH,
                    description=f"baseline research {iid}",
                    run=lambda api, iid=iid: api.build(iid)))

    # 3. Build queue — prefer economic-effect buildings
    if not ctx.summary.get("build_queue"):
        buildings = ctx.items.get("buildings", {})
        econ_iid = cheapest_affordable(buildings, ctx, _has_econ_effect)
        iid = econ_iid or cheapest_affordable(buildings, ctx)
        if iid:
            item = buildings.get(iid, {})
            price = float((item.get("costs") or {}).get("gold", 0.0))
            options.append(Option(
                category="baseline", price=price,
                gain=GAIN_ECON_ITEM if iid == econ_iid else GAIN_PLAIN_ITEM,
                mandatory=True, priority=PRIO_BUILD_QUEUE,
                description=f"baseline build {iid}",
                run=lambda api, iid=iid: api.build(iid)))

    # 4. Citizen upgrade (culture-funded, always beneficial)
    citizen_price = float(ctx.summary.get("citizen_price", 0.0) or 0.0)
    if citizen_price > 0 and ctx.culture >= citizen_price * 1.2:
        citizens = dict(ctx.summary.get("citizens", {}))
        total = sum(citizens.values()) + 1
        dist = {"merchant": round(total * 0.4), "scientist": round(total * 0.4)}
        dist["artist"] = max(0, total - dist["merchant"] - dist["scientist"])

        def _run_citizen(api, dist=dist):
            res = api.citizen_upgrade()
            if isinstance(res, dict) and res.get("success") is False:
                return res
            return api.set_citizens(dist)

        options.append(Option(
            category="baseline", price=0.0, gain=GAIN_CITIZEN,
            mandatory=True, priority=PRIO_CITIZEN,
            description=f"buy citizen + rebalance {dist}",
            run=_run_citizen))

    # 5. Ruler skill-up — free, always spend available points
    ruler_data = ctx.summary.get("ruler")
    if ruler_data:
        level = int(ruler_data.get("level", 0))
        spent = sum(int(ruler_data.get(s, 0)) for s in "qwer")
        now = time.time()
        if level > spent:
            # Find the first skill that isn't per-skill blocked due to level requirement
            blocked_skills: dict = ctx.memory.get("ruler_skill_blocked", {}) or {}
            skill = None
            for candidate in ("q", "w", "e", "r"):
                if int(ruler_data.get(candidate, 0) or 0) >= {"q": 5, "w": 5, "e": 5, "r": 3}[candidate]:
                    continue  # already capped
                if now < float(blocked_skills.get(candidate, 0.0)):
                    continue  # temporarily blocked (level requirement)
                skill = candidate
                break
            if skill:
                def _run_skill(api, skill=skill):
                    try:
                        result = api.ruler_skill_up(skill)
                    except ApiError as e:
                        if not 400 <= e.status < 500:
                            raise
                        result = {"success": False, "error": e.body}
                    if isinstance(result, dict) and result.get("success") is False:
                        blocked = ctx.memory.setdefault("ruler_skill_blocked", {})
                        blocked[skill] = time.time() + SKILL_RETRY_S
                    return result

                options.append(Option(
                    category="baseline", price=0.0, gain=GAIN_RULER_SKILL,
                    mandatory=True, priority=PRIO_RULER_SKILL,
                    description=f"ruler skill-up {skill}",
                    run=_run_skill))

    return options


def baseline_action(ctx: BotContext) -> Action | None:
    """Compatibility wrapper: best baseline option as a single Action (or None)."""
    options = baseline_options(ctx)
    if not options:
        return None
    best = max(options, key=lambda o: (o.tier(), o.priority, o.base_score()))
    return best.to_action()
