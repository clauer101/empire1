"""Planner base: planners emit Options; the dispatcher runs them in strict
priority order each cycle (free first, then priced highest-priority-first —
see bot/dispatch.py)."""

from __future__ import annotations

import logging
import random
from dataclasses import dataclass, field
from typing import Any, Callable, Sequence, TypeVar

log = logging.getLogger("bot.planner")

T = TypeVar("T")


def weighted_top_n(candidates: Sequence[T], key: Callable[[T], float], n: int,
                   *, reverse: bool = True, rng: Any = random) -> T | None:
    """Pick one of the best `n` candidates, weighted toward the top.

    Sorts by `key` (descending by default; pass reverse=False for ascending,
    e.g. cheapest-first), keeps the best `n`, then samples one with rank-based
    weights (best rank → highest probability). Rank weights are used instead of
    raw scores so the result is robust to negative or zero scores. With n<=1 or
    a single candidate this is deterministic (always the best), preserving the
    old behavior.
    """
    if not candidates:
        return None
    ordered = sorted(candidates, key=key, reverse=reverse)
    pool = ordered[:max(1, n)]
    if len(pool) == 1:
        return pool[0]
    weights = list(range(len(pool), 0, -1))  # e.g. [3,2,1] for the top 3
    return rng.choices(pool, weights=weights, k=1)[0]


class Action:
    """One executable game action: a description plus a callable on the api client."""

    def __init__(self, description: str, run: Callable[[Any], Any]):
        self.description = description
        self.run = run

    def __repr__(self) -> str:
        return f"Action({self.description})"


@dataclass
class Option:
    """A candidate action a planner offers the dispatcher.

    Dispatch (bot/dispatch.py) is strict priority order, not ROI: free options
    (price <= 0) always run before any priced one, regardless of priority;
    among priced options, higher `priority` wins. `gain`/`base_score`/`tier`/
    `filler`/`mandatory` are legacy fields kept for `Planner.propose()` and a
    few single-planner "pick the best of my own options" call sites (e.g.
    baseline.py's tower-floor/breach-response helper) — they no longer affect
    the dispatcher's cross-planner ordering. When the chosen option is
    unaffordable and carries saves_for/goal_meta, the dispatcher saves toward
    it instead of running a lower-priority option that would spend the gold.
    """

    category: str                       # "baseline" | "defense" | "attack"
    description: str
    run: Callable[[Any], Any]
    price: float = 0.0                  # gold cost; 0.0 = free
    gain: float = 1.0                   # rough common "power/value" unit (legacy, see above)
    mandatory: bool = False             # legacy tier field, see class docstring
    priority: int = 0                   # dispatch order among priced options (higher first)
    saves_for: float = 0.0              # if unaffordable, gold to save toward (0 = don't)
    goal_meta: dict | None = field(default=None)  # {item, action, sticky} for set_goal
    filler: bool = False                # legacy tier field, see class docstring

    def base_score(self) -> float:
        if self.price <= 0:
            return float("inf") if self.gain > 0 else 0.0
        return self.gain / self.price

    def tier(self) -> int:
        """Tier ordering, higher wins first:
        3 = mandatory, 2 = free, 1 = priced productive, 0 = filler.

        Filler (queue fill / fallback build) always ranks last so a valuable but
        cheaper-per-gold productive option is never displaced by keep-busy work.
        Only used by Planner.propose() and single-planner helpers — see class
        docstring; the cross-planner dispatcher no longer uses this.
        """
        if self.mandatory:
            return 3
        if self.filler:
            return 0
        return 2 if self.price <= 0 else 1

    def to_action(self) -> Action:
        return Action(self.description, self.run)


def category_weight(config: dict, personality: str, active_type: str,
                    category: str) -> float:
    """Score multiplier for an option's category given the bot's personality.

    Missing config → 1.0. Options whose category matches the active strategy
    get an extra active_strategy_boost so the chosen focus stays primary.
    """
    weights = (config.get("category_weights") or {}).get(personality, {})
    w = float(weights.get(category, 1.0))
    # artifact strategy shares the "attack" option category.
    active_cat = "attack" if active_type == "artifact" else active_type
    if category == active_cat:
        w *= float(config.get("active_strategy_boost", 1.0) or 1.0)
    return w


class Planner:
    def propose_options(self, ctx: "BotContext", *,
                        advance_phase: bool = True) -> list[Option]:
        raise NotImplementedError

    def propose(self, ctx: "BotContext") -> Action | None:
        """Compatibility helper: best single option by base_score (or None).

        Used by the dispatcher's baseline tower-floor/breach hooks and by tests
        that assert on a single action. Mandatory options win, then free, then
        highest gain/price.
        """
        options = self.propose_options(ctx)
        if not options:
            return None
        best = max(options, key=lambda o: (o.tier(), o.priority, o.base_score()))
        return best.to_action()


class BotContext:
    """Everything a planner may inspect during one cycle."""

    def __init__(self, summary: dict, items: dict, memory: dict,
                 strategy: dict, api: Any, selection: dict | None = None,
                 personality: str = "balanced",
                 map_data: dict | None = None):
        self.summary = summary
        self.items = items
        self.memory = memory
        self.strategy = strategy
        self.api = api
        self.personality = personality
        self.selection = selection or {"top_n": 1}
        self._map_cache: dict | None = map_data

    def get_map(self) -> dict:
        """Return cached map or fetch once (caller should pre-populate via map_data)."""
        if self._map_cache is None:
            self._map_cache = self.api.get_map()
        return self._map_cache

    @property
    def top_n(self) -> int:
        return int(self.selection.get("top_n", 1) or 1)

    @property
    def gold(self) -> float:
        return float(self.summary.get("resources", {}).get("gold", 0.0))

    @property
    def culture(self) -> float:
        return float(self.summary.get("resources", {}).get("culture", 0.0))

    @property
    def spendable_gold(self) -> float:
        """Gold available to NON-owning spenders while a savings goal is active."""
        from bot.savings import spendable_gold
        return spendable_gold(self.gold, self.memory, self.strategy)

    def affordable(self, costs: dict, respect_savings: bool = False) -> bool:
        gold = self.spendable_gold if respect_savings else self.gold
        return (gold >= float(costs.get("gold", 0.0))
                and self.culture >= float(costs.get("culture", 0.0)))

    def affordable_option(self, o: "Option", respect_savings: bool = False) -> bool:
        gold = self.spendable_gold if respect_savings else self.gold
        return gold >= float(o.price)

    @property
    def completed(self) -> set[str]:
        """All completed item iids (buildings/knowledge with 0 remaining effort + artifacts)."""
        done = {iid for iid, rem in (self.summary.get("buildings") or {}).items()
                if (rem or 0) <= 0}
        done |= {iid for iid, rem in (self.summary.get("knowledge") or {}).items()
                 if (rem or 0) <= 0}
        done |= set(self.summary.get("artifacts") or [])
        return done

    @property
    def started(self) -> set[str]:
        """Items already started (any progress entry) or queued."""
        started = set(self.summary.get("buildings") or {})
        started |= set(self.summary.get("knowledge") or {})
        started |= set(self.summary.get("build_queue") or [])
        started |= set(self.summary.get("research_queue") or [])
        return started

    def is_unlocked(self, item: dict) -> bool:
        return set(item.get("requirements") or []).issubset(self.completed)


def cheapest_affordable(section: dict, ctx: BotContext,
                        predicate: Callable[[dict], bool] | None = None,
                        respect_savings: bool = True) -> str | None:
    """IID of the cheapest unlocked, not-yet-started item the bot can afford.

    The items catalog has no unlocked/built flags — availability is derived from
    summary.buildings/knowledge (iid → remaining effort) and item requirements.
    Respects active savings goals by default; the goal-owning planner may pass
    respect_savings=False to bypass the cap.
    """
    candidates = [
        (iid, it) for iid, it in section.items()
        if iid not in ctx.started
        and ctx.is_unlocked(it)
        and ctx.affordable(it.get("costs") or {}, respect_savings=respect_savings)
        and (predicate is None or predicate(it))
    ]
    if not candidates:
        return None
    chosen = weighted_top_n(
        candidates,
        key=lambda c: float((c[1].get("costs") or {}).get("gold", 0.0)),
        n=ctx.top_n, reverse=False)
    return chosen[0] if chosen else None
