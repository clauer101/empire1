"""Strategy model: weighted random selection with wall-clock lifetime.

A strategy's lifetime is a wall-clock window (``valid_until``). The bot runs as
an external process independent of the server game tick.

Only two strategies exist: defense and attack. Research, buildings, citizens
and ruler skill-ups run unconditionally via baseline regardless of strategy.
"""

from __future__ import annotations

import random
from datetime import datetime, timedelta, timezone
from typing import Any

from .planners.base import weighted_top_n
from .state import BotState, now_iso, parse_iso

STRATEGY_TYPES = ["defense", "attack"]


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


_VARIETY_WINDOW = 3
_VARIETY_BOOST  = 3.0


def _variety_weights(weights: dict[str, float], memory: dict) -> dict[str, float]:
    history = memory.get("strategy_history", [])
    recent = set(history[-_VARIETY_WINDOW:])
    return {t: (w if t in recent else w * _VARIETY_BOOST)
            for t, w in weights.items()}


def roll_strategy(config: dict, state: BotState, context: dict[str, Any]) -> dict:
    """Pick defense or attack, modulated by context."""
    weights = _personality_weights(config, state)

    if not context.get("has_army"):
        army_price = float(context.get("army_price", 0.0) or 0.0)
        if army_price > 0 and context.get("gold", 0.0) < 0.3 * army_price:
            weights["attack"] = 0
        else:
            weights["attack"] = weights.get("attack", 0) / 2

    if context.get("recent_defeat"):
        weights["defense"] = weights.get("defense", 0) * 2
    if context.get("recent_attack_defeat"):
        weights["attack"] = weights.get("attack", 0) * 2
    if not context.get("targets"):
        weights["attack"] = 0

    types = [t for t in STRATEGY_TYPES if weights.get(t, 0) > 0]
    if not types:
        types, weights = ["defense"], {"defense": 1}

    weights = _variety_weights(weights, state.memory)
    chosen = random.choices(types, weights=[weights[t] for t in types], k=1)[0]

    history = state.memory.setdefault("strategy_history", [])
    history.append(chosen)
    state.memory["strategy_history"] = history[-10:]

    params: dict[str, Any] = {}
    if chosen == "attack":
        targets = context.get("targets", [])
        top_n = int((config.get("selection") or {}).get("top_n", 1) or 1)
        target = weighted_top_n(targets, key=lambda t: t.get("score", 0.0), n=top_n)
        params = {"target_uid": target["uid"], "target_name": target["name"],
                  "phase": "strengthen"}

    return {
        "type": chosen,
        "params": params,
        "valid_until": _valid_until(config, chosen),
        "source": "random",
        "started_at": now_iso(),
    }


def roll_secondary(config: dict, state: BotState,
                   active_type: str, has_target: bool) -> str | None:
    """Pick a secondary strategy type (the one not currently active)."""
    weights = _personality_weights(config, state)
    weights.pop(active_type, None)
    if not has_target:
        weights.pop("attack", None)
    types = [t for t in STRATEGY_TYPES if weights.get(t, 0) > 0]
    if not types:
        return None
    return random.choices(types, weights=[weights[t] for t in types], k=1)[0]


def should_respond_to_breach(config: dict, personality: str) -> bool:
    chance = (config.get("breach_response_chance") or {}).get(personality, 1.0)
    return random.random() < float(chance)


def breach_defense_strategy(config: dict) -> dict:
    return {
        "type": "defense",
        "params": {},
        "valid_until": _valid_until(config, "defense"),
        "source": "breach",
        "started_at": now_iso(),
    }


def should_respond_to_attack_defeat(config: dict, personality: str) -> bool:
    chance = (config.get("attack_defeat_response_chance") or {}).get(personality, 1.0)
    return random.random() < float(chance)


def attack_defeat_strategy(config: dict, target_uid: int, target_name: str) -> dict:
    return {
        "type": "attack",
        "params": {"target_uid": target_uid, "target_name": target_name,
                   "phase": "strengthen"},
        "valid_until": _valid_until(config, "attack"),
        "source": "revenge",
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
