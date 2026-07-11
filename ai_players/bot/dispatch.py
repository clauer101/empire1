"""Per-cycle option dispatcher.

Strict priority dispatch, no ROI/personality scoring:

1. Free options (price <= 0) always run first, in priority order — they never
   compete with or get excluded by priced options.
2. Priced options are then checked highest-priority first. An unaffordable one
   is skipped (not blocking); every remaining priority is still checked and
   run if affordable — one cycle can execute several actions in descending
   priority order, not just one.
3. If nothing at all is affordable, the cycle ends and waits for the next tick.

Savings goals are simplified accordingly: the highest-priority option that is
NOT yet affordable (and asks to save) blocks spendable gold for every lower
priority for this cycle (and future cycles until it clears or expires) —
see bot/savings.py. There is no more "only save when everything else is
filler" special case: priority order alone decides what gold protects.
"""

from __future__ import annotations

import logging

from .planners import PLANNERS
from .planners.base import Action, BotContext, Option
from .planners.baseline import baseline_options
from .savings import clear_goal, get_goal, set_goal

log = logging.getLogger("bot.dispatch")


def gather_options(ctx: BotContext, active_type: str) -> list[Option]:
    """Collect options from baseline + the active strategy + attack's free
    background actions.

    Attack (spy/attack calls, filling empty waves with an already-unlocked
    critter) costs no gold, so it always runs regardless of which strategy is
    active — see AttackPlanner's own is_active gate for what it does and
    doesn't spend gold on. The only exception is growth, which means "invest
    in nothing, not even for free" and while active is the sole active
    strategy (no background attack).
    """
    options = list(baseline_options(ctx))
    options += PLANNERS[active_type].propose_options(ctx, advance_phase=True)
    if active_type not in ("attack", "growth"):
        options += PLANNERS["attack"].propose_options(ctx, advance_phase=False)
    return options


def _rank_key(o: Option) -> tuple[int, int]:
    """Sort key: free options always outrank priced ones, then by priority."""
    return (0 if o.price <= 0 else 1, -o.priority)


def choose_action(ctx: BotContext, config: dict, active_type: str, *,
                  exclude: set[str] | None = None) -> Action | None:
    """Pick the next single action to run this cycle (or None to wait).

    Called repeatedly per cycle (see run_bot.py's action loop) — each call
    re-gathers options against the current (possibly just-changed) state and
    returns the highest-ranked affordable one, so a whole cycle works through
    the full priority list rather than picking once. `exclude` holds
    descriptions the caller already tried and had rejected by the server this
    tick (e.g. unmet requirements) — skipped so a single bad option can't loop
    forever; every other priority is still tried. `config` is accepted for
    call-site compatibility but no longer used (no personality/category
    weighting in strict priority dispatch).
    """
    options = gather_options(ctx, active_type)
    if exclude:
        options = [o for o in options if o.description not in exclude]
    if not options:
        clear_goal(ctx.memory)
        return None

    ranked = sorted(options, key=_rank_key)

    # The highest-priority priced option not yet affordable owns this cycle's
    # savings goal (if it asks for one) — every lower-priority priced option
    # must respect that reserved gold. Free options are never gated (checked
    # first, above, and never compete for gold anyway).
    goal_owner = next((o for o in ranked
                       if o.price > 0 and not ctx.affordable_option(o)
                       and o.saves_for > 0 and o.goal_meta), None)
    saving = False
    if goal_owner is not None:
        if get_goal(ctx.memory, ctx.strategy) is None:
            set_goal(ctx.memory, item=goal_owner.goal_meta["item"],
                     action=goal_owner.goal_meta.get("action", "buy"),
                     amount=goal_owner.saves_for, strategy=ctx.strategy,
                     sticky=bool(goal_owner.goal_meta.get("sticky", False)))
        saving = True

    for o in ranked:
        if not ctx.affordable_option(o, respect_savings=saving):
            continue
        # The option now running may be the one an active goal was saving
        # toward (whether or not IT is the one gating this cycle's saving) —
        # clear it so the goal doesn't linger after its purchase happens.
        goal = get_goal(ctx.memory, ctx.strategy)
        if goal is not None and o.goal_meta \
                and o.goal_meta.get("item") == goal.get("item"):
            clear_goal(ctx.memory)
        log.debug("dispatch chose: %s (price=%.0f priority=%d, saving=%s)",
                  o.description, o.price, o.priority, saving)
        return o.to_action()

    return None  # nothing affordable this cycle — wait / keep saving
