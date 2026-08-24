"""Strategy model: one opening rule and two running rules, nothing else.

0. A bot with no active strategy — brand new, or just wiped by a season reset —
   opens on `defense` via `season_start_defense_strategy()`. Bots always enter a
   season building their maze first, never raiding.
1. A fully lost defense immediately switches to `defense` — this always wins,
   unconditionally, overriding whatever was active before.
2. Winning DEFENSE_WIN_STREAK_TARGET (see run_bot.py) defenses in a row rolls
   a NEW strategy via `roll_strategy()` (attack or growth, weighted by
   `config.yaml` and personality) — this is the only way out of `defense`.

There is no revenge-attack-on-defeat mechanism and no wall-clock strategy
rotation: attack/growth both hold with NO_EXPIRY until the next lost defense.
Research, buildings, citizens and ruler skill-ups run unconditionally via
baseline regardless of strategy. Attack's free actions (spy/attack calls,
wave-fill with an already-unlocked critter) also run regardless of the active
strategy — see bot/dispatch.py::gather_options — since they cost no gold;
growth is the one exception (it means "invest in nothing, not even free").
"""

from __future__ import annotations

import random
from datetime import datetime, timedelta, timezone
from typing import Any

from .planners.base import weighted_top_n
from .state import BotState, now_iso, parse_iso

STRATEGY_TYPES = ["defense", "attack", "growth"]

# Sentinel valid_until for a strategy that should persist indefinitely rather
# than expire on a wall-clock timer — attack/growth both hold until the next
# lost defense forces a switch back to defense, not for a randomized duration.
NO_EXPIRY = "2099-01-01T00:00:00Z"


def is_expired(strategy: dict | None) -> bool:
    if not strategy:
        return True
    try:
        return datetime.now(timezone.utc) > parse_iso(strategy["valid_until"])
    except (KeyError, ValueError):
        return True


def _valid_until(config: dict, stype: str) -> str:
    lo, hi = config["strategy"]["duration_hours"][stype]
    until = datetime.now(timezone.utc) + timedelta(hours=random.uniform(lo, hi))
    return until.strftime("%Y-%m-%dT%H:%M:%SZ")


def _personality_weights(config: dict, state: BotState) -> dict[str, float]:
    """Base strategy weights scaled by the bot's personality multipliers."""
    weights = {t: float(w) for t, w in config["strategy"]["weights"].items()
               if t in STRATEGY_TYPES}
    personality = getattr(state, "personality", "balanced") or "balanced"
    mults = (config.get("personalities") or {}).get(personality, {})
    for t, m in mults.items():
        if t in weights:
            weights[t] = weights[t] * float(m)
    return weights


def roll_strategy(config: dict, state: BotState, context: dict[str, Any]) -> dict:
    """Weighted-random pick between attack and growth (config.yaml
    strategy.weights, scaled by personality) — the only way out of defense,
    reached after DEFENSE_WIN_STREAK_TARGET consecutive defense wins (see
    run_bot.py). Attack is excluded from the pool when no attackable target
    exists; if that leaves nothing, growth is used, and if growth also has
    zero weight, falls back to a short-lived defense placeholder (re-checked
    again soon rather than parking on defense for hours)."""
    targets = context.get("targets") or []
    weights = _personality_weights(config, state)
    if not targets:
        weights.pop("attack", None)
    weights.pop("defense", None)
    types = [t for t in weights if weights[t] > 0]
    if not types:
        return {
            "type": "defense",
            "params": {},
            "valid_until": (datetime.now(timezone.utc)
                            + timedelta(minutes=5)).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "source": "no_targets",
            "started_at": now_iso(),
        }

    chosen = random.choices(types, weights=[weights[t] for t in types], k=1)[0]
    if chosen == "attack":
        # Sample across the WHOLE viable pool (not just config.selection.top_n,
        # which was too narrow with only a handful of opponents in play) so bots
        # spread across different targets instead of every bot's weighted draw
        # converging on the single globally weakest empire.
        target = weighted_top_n(targets, key=lambda t: t.get("score", 0.0), n=len(targets))
        return {
            "type": "attack",
            "params": {"target_uid": target["uid"], "target_name": target["name"],
                       "phase": "strengthen"},
            "valid_until": NO_EXPIRY,
            "source": "defense_won",
            "started_at": now_iso(),
        }
    return {
        "type": "growth",
        "params": {},
        "valid_until": NO_EXPIRY,
        "source": "defense_won",
        "started_at": now_iso(),
    }


def season_start_defense_strategy(config: dict) -> dict:
    """Opening strategy for a bot with no active strategy.

    Covers both ways that happens: a brand-new bot on its first tick, and a bot
    whose state was just wiped by a season reset (`BotState.reset()` clears
    `strategy`). Bots always start a season on defense so they build a maze
    before doing anything else.

    Uses the same wall-clock window as a breach-forced defense
    (`config.strategy.duration_hours.defense`) rather than NO_EXPIRY: rule 2
    (defense win streak) is the intended way out, but on a quiet opening where
    nobody attacks the bot there are no defense wins to accumulate, so the
    window lets it move on to attack/growth instead of parking on defense.
    """
    return {
        "type": "defense",
        "params": {},
        "valid_until": _valid_until(config, "defense"),
        "source": "season_start",
        "started_at": now_iso(),
    }


def breach_defense_strategy(config: dict) -> dict:
    return {
        "type": "defense",
        "params": {},
        "valid_until": _valid_until(config, "defense"),
        "source": "breach",
        "started_at": now_iso(),
    }


def make_override(payload: dict, config: dict) -> dict:
    stype = payload.get("type")
    if stype not in STRATEGY_TYPES:
        raise ValueError(f"unknown strategy type: {stype!r}, must be one of {STRATEGY_TYPES}")
    duration = payload.get("duration_hours")
    if duration is not None:
        until = datetime.now(timezone.utc) + timedelta(hours=float(duration))
        valid_until = until.strftime("%Y-%m-%dT%H:%M:%SZ")
    else:
        valid_until = _valid_until(config, stype)
    params = dict(payload.get("params", {}))
    if stype == "attack":
        params.setdefault("phase", "spy")
    return {
        "type": stype,
        "params": params,
        "valid_until": valid_until,
        "source": "override",
        "started_at": now_iso(),
    }
