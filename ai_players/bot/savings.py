"""Situational savings goals — strategy-dependent saving for expensive purchases.

There is no permanent gold reserve. A planner that identifies a concrete desired
purchase it cannot yet afford declares a goal; while the goal is active,
non-owning spenders (baseline queue filling, other planner steps) may only
spend gold ABOVE the goal amount. The owning planner bypasses the cap.
Goals expire with the strategy (or after a wall-clock TTL) so bots never
deadlock.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

log = logging.getLogger("bot.savings")

ISO = "%Y-%m-%dT%H:%M:%SZ"
DEFAULT_TTL_H = 2.0


def _parse(ts: str) -> datetime | None:
    try:
        return datetime.strptime(ts, ISO).replace(tzinfo=timezone.utc)
    except (ValueError, TypeError):
        return None


def set_goal(memory: dict, *, item: str, action: str, amount: float,
             strategy: dict, ttl_h: float = DEFAULT_TTL_H,
             sticky: bool = False) -> dict:
    """Declare a savings goal owned by the current strategy.

    A sticky goal survives a strategy-type change (used for army build-up so the
    saved gold is not burned when a different strategy rolls between attack
    windows); it still expires on its TTL / strategy end so bots never deadlock.
    """
    now = datetime.now(timezone.utc)
    expires = now.timestamp() + ttl_h * 3600
    # A sticky goal must outlive the strategy window it was created in, so only
    # non-sticky goals are clamped to the strategy's end.
    strategy_end = _parse(strategy.get("valid_until", ""))
    if strategy_end is not None and not sticky:
        expires = min(expires, strategy_end.timestamp())
    goal = {
        "item": item,
        "action": action,
        "amount": float(amount),
        "strategy_type": strategy.get("type", ""),
        "sticky": bool(sticky),
        "created_at": now.strftime(ISO),
        "expires_at": datetime.fromtimestamp(expires, timezone.utc).strftime(ISO),
    }
    memory["savings_goal"] = goal
    log.info("savings goal set: %s %s needs %.0f gold (until %s)",
             action, item, amount, goal["expires_at"])
    return goal


def get_goal(memory: dict, strategy: dict) -> dict | None:
    """Return the active goal; auto-clears expired or orphaned goals."""
    goal = memory.get("savings_goal")
    if not goal:
        return None
    expires = _parse(goal.get("expires_at", ""))
    if expires is None or datetime.now(timezone.utc) >= expires:
        log.info("savings goal expired: %s", goal.get("item"))
        clear_goal(memory)
        return None
    if not goal.get("sticky") and goal.get("strategy_type") != strategy.get("type"):
        log.info("savings goal dropped (strategy changed): %s", goal.get("item"))
        clear_goal(memory)
        return None
    return goal


def clear_goal(memory: dict) -> None:
    memory.pop("savings_goal", None)


def spendable_gold(gold: float, memory: dict, strategy: dict) -> float:
    """Gold a NON-owning spender may use: everything above the goal amount."""
    goal = get_goal(memory, strategy)
    if goal is None:
        return gold
    return max(0.0, gold - float(goal["amount"]))
