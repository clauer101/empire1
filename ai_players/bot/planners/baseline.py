"""Baseline obligations that apply to EVERY strategy, before the strategy planner runs.

1. Defense must never be neglected: a defensive breach triggers an immediate
   defensive action, and a minimum tower count (scaling with the bot's era,
   so AI wave strength is always met with an adequate defense) is maintained
   regardless of the active strategy — including buying tiles and building
   towers while pursuing economy/attack/artifact goals.
2. Idle time on building and research must be minimized: empty queues are
   filled with the cheapest affordable item before strategy-specific actions.
3. Savings goals are respected: queue filling only spends gold above an
   active goal (see bot/savings.py); the goal-owning planner bypasses the cap.
"""

from __future__ import annotations

from bot.analyzer import ERA_RANK
from bot.army_building import pick_ruler

from .base import Action, BotContext, Option, cheapest_affordable
from .defense import DefensePlanner

_defense = DefensePlanner()

# Minimum placed towers: base + per-era scaling (AI waves grow with era)
FLOOR_BASE_TOWERS = 2
FLOOR_TOWERS_PER_ERA = 2

# Mandatory-option priority: breach response must beat the tower floor.
PRIO_BREACH = 30
PRIO_TOWER_FLOOR = 20
# Gain for the free ruler claim — rulers are strong, so it outranks filler.
RULER_CLAIM_GAIN = 100.0


# Map tile types that are terrain, not placed towers
TERRAIN_TILES = {"void", "empty", "path", "spawnpoint", "castle"}


def min_towers(ctx: BotContext) -> int:
    era_rank = ERA_RANK.get(ctx.summary.get("era", "stone"), 0)
    return FLOOR_BASE_TOWERS + FLOOR_TOWERS_PER_ERA * era_rank


def placed_towers(ctx: BotContext) -> int:
    """Count placed towers from the map (summary.structures is only synced
    during battles and is empty otherwise)."""
    tiles = ctx.api.get_map().get("tiles", {})
    def _type(v):
        return v.get("type", "") if isinstance(v, dict) else str(v)
    return sum(1 for v in tiles.values() if _type(v) not in TERRAIN_TILES)


def _best_defense_option(ctx: BotContext) -> Option | None:
    """Highest-ranked defense option, preserving its price/saves_for/goal_meta
    so a baseline-wrapped mandatory action stays affordability-aware.

    Prefers an affordable option (baseline needs an action it can run now); when
    none is affordable, returns the best overall so the dispatcher can save
    toward it.
    """
    options = _defense.propose_options(ctx)
    if not options:
        return None
    key = lambda o: (o.tier(), o.priority, o.base_score())  # noqa: E731
    affordable = [o for o in options if ctx.affordable_option(o)]
    return max(affordable or options, key=key)


def baseline_options(ctx: BotContext) -> list[Option]:
    """Emit baseline obligation options (breach, tower floor, ruler, queues)."""
    options: list[Option] = []

    # 1a. Breach response: one defensive action after critters reached the castle.
    #     Mandatory (top priority). Consume the flag whether or not we found an
    #     action so the bot never loops on an unaffordable breach response.
    if ctx.memory.get("pending_breach"):
        base = _best_defense_option(ctx)
        ctx.memory["pending_breach"] = False
        if base:
            options.append(Option(
                category="baseline", mandatory=True, priority=PRIO_BREACH,
                description=f"baseline defense (breach response): {base.description}",
                run=base.run, price=base.price, gain=base.gain,
                saves_for=base.saves_for, goal_meta=base.goal_meta))

    # 1b. Tower floor: keep a minimum defense against AI waves in every strategy.
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

    # 1c. Claim a ruler as soon as one is unlocked (free, strategy-independent).
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

    # 2. Minimize idle time: keep both queues busy (respects savings goals).
    if not ctx.summary.get("research_queue"):
        iid = cheapest_affordable(ctx.items.get("knowledge", {}), ctx)
        if iid:
            item = ctx.items.get("knowledge", {}).get(iid, {})
            price = float((item.get("costs") or {}).get("gold", 0.0))
            options.append(Option(
                category="baseline", price=price, gain=1.0, filler=True,
                description=f"baseline research {iid}",
                run=lambda api, iid=iid: api.build(iid)))

    if not ctx.summary.get("build_queue"):
        iid = cheapest_affordable(ctx.items.get("buildings", {}), ctx)
        if iid:
            item = ctx.items.get("buildings", {}).get(iid, {})
            price = float((item.get("costs") or {}).get("gold", 0.0))
            options.append(Option(
                category="baseline", price=price, gain=1.0, filler=True,
                description=f"baseline build {iid}",
                run=lambda api, iid=iid: api.build(iid)))

    return options


def baseline_action(ctx: BotContext) -> Action | None:
    """Compatibility wrapper: best baseline option as a single Action (or None)."""
    options = baseline_options(ctx)
    if not options:
        return None
    best = max(options, key=lambda o: (o.tier(), o.priority, o.base_score()))
    return best.to_action()
