"""Per-cycle option dispatcher.

Each cycle the bot gathers scored Options from baseline obligations, the active
strategy, and one personality-weighted secondary strategy. Options are scored on
a common utility-per-gold basis multiplied by a personality/active-strategy
category weight, then one affordable option is chosen (weighted-top-N for
diversity). When the best option is unaffordable but worth saving for, a savings
goal is declared and the bot may still spend leftover gold on an affordable
filler — preserving "one action per cycle".
"""

from __future__ import annotations

import logging

from .planners import PLANNERS
from .planners.base import (
    Action, BotContext, Option, category_weight, weighted_top_n,
)
from .planners.baseline import baseline_options
from .savings import clear_goal, get_goal, set_goal

log = logging.getLogger("bot.dispatch")


def gather_options(ctx: BotContext, active_type: str,
                   secondary_type: str | None) -> list[Option]:
    """Collect options from baseline + active strategy + secondary strategy."""
    options = list(baseline_options(ctx))
    options += PLANNERS[active_type].propose_options(ctx, advance_phase=True)
    if secondary_type and secondary_type != active_type:
        options += PLANNERS[secondary_type].propose_options(ctx, advance_phase=False)
    return options


def _scored(ctx: BotContext, config: dict, active_type: str,
            o: Option) -> tuple[int, int, float]:
    """Sort key: (tier, priority, weighted score). Higher is better."""
    weight = category_weight(config, ctx.personality, active_type, o.category)
    return (o.tier(), o.priority, o.base_score() * weight)


def choose_action(ctx: BotContext, config: dict, active_type: str,
                  secondary_type: str | None) -> Action | None:
    """Pick exactly one action for this cycle (or None to wait).

    Mandatory options win their tier; otherwise the highest weighted gain/gold
    wins, sampled via weighted_top_n for inter-bot diversity. If the best option
    overall is unaffordable but carries a savings target, declare/keep a goal and
    still execute an affordable filler that respects the goal.
    """
    options = gather_options(ctx, active_type, secondary_type)
    if not options:
        clear_goal(ctx.memory)
        return None

    ranked = sorted(options, key=lambda o: _scored(ctx, config, active_type, o),
                    reverse=True)
    top = ranked[0]

    # Options we could execute right now (ignoring any savings cap). We only
    # start saving toward an expensive top option when everything else affordable
    # this cycle is mere filler (queue fill / fallback build) — otherwise doing
    # the affordable productive action now beats idling gold.
    affordable_now = [o for o in ranked if ctx.affordable_option(o)]
    only_filler = all(o.filler for o in affordable_now)

    # Goal handling: if the top option is unaffordable but worth saving for, and
    # nothing productive is affordable right now, declare a goal and (optionally)
    # run a goal-respecting filler this cycle.
    saving = False
    if (not ctx.affordable_option(top) and top.saves_for > 0 and top.goal_meta
            and only_filler):
        if get_goal(ctx.memory, ctx.strategy) is None:
            set_goal(ctx.memory, item=top.goal_meta["item"],
                     action=top.goal_meta.get("action", "buy"),
                     amount=top.saves_for, strategy=ctx.strategy,
                     sticky=bool(top.goal_meta.get("sticky", False)))
        saving = True

    # Eligible options to execute now: affordable, and (when saving) respecting
    # the savings cap so we don't spend the gold we're saving.
    respect = saving
    eligible = [o for o in ranked if ctx.affordable_option(o, respect_savings=respect)]
    if not eligible:
        return None  # nothing affordable this cycle — wait / keep saving

    # If we are NOT saving and the top eligible option is the one that owns the
    # active goal, clear it (the purchase is happening).
    chosen = _pick(ctx, config, active_type, eligible)
    if chosen is None:
        return None
    if not saving:
        goal = get_goal(ctx.memory, ctx.strategy)
        if goal is not None and chosen.goal_meta \
                and chosen.goal_meta.get("item") == goal.get("item"):
            clear_goal(ctx.memory)
    log.debug("dispatch chose: %s (price=%.0f gain=%.2f, saving=%s)",
              chosen.description, chosen.price, chosen.gain, saving)
    return chosen.to_action()


def _pick(ctx: BotContext, config: dict, active_type: str,
          eligible: list[Option]) -> Option | None:
    """Within the best tier, sample one option weighted toward the best score."""
    best_tier = max(o.tier() for o in eligible)
    tier_opts = [o for o in eligible if o.tier() == best_tier]
    # Mandatory tier: deterministic by priority then score (sequencing must be
    # stable); other tiers sample for diversity.
    if best_tier == 3:
        return max(tier_opts, key=lambda o: (o.priority,
                   o.base_score() * category_weight(config, ctx.personality,
                                                     active_type, o.category)))
    return weighted_top_n(
        tier_opts,
        key=lambda o: o.base_score() * category_weight(
            config, ctx.personality, active_type, o.category),
        n=ctx.top_n)
