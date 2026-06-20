"""Strategy model: weighted random selection with wall-clock lifetime.

A strategy's lifetime is a wall-clock window (``valid_until``). The bot runs as
an external process independent of the server game tick.
"""

from __future__ import annotations

import random
from datetime import datetime, timedelta, timezone
from typing import Any

from .planners.base import weighted_top_n
from .state import BotState, now_iso, parse_iso

STRATEGY_TYPES = ["economy", "defense", "attack", "artifact"]


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
    weights = {t: float(w) for t, w in config["strategy"]["weights"].items()}
    personality = getattr(state, "personality", "balanced") or "balanced"
    mults = (config.get("personalities") or {}).get(personality, {})
    for t, m in mults.items():
        if t in weights:
            weights[t] = weights[t] * float(m)
    return weights


_VARIETY_WINDOW = 3   # look back this many strategies for the variety boost
_VARIETY_BOOST  = 3.0 # multiply weight of types not seen in the window


def _variety_weights(weights: dict[str, float], memory: dict) -> dict[str, float]:
    """Boost strategy types not played in the last _VARIETY_WINDOW rounds.

    Keeps the population rotating through all strategy types without forcing a
    strict round-robin: the roll is still random, just steered toward variety.
    """
    history = memory.get("strategy_history", [])
    recent = set(history[-_VARIETY_WINDOW:])
    return {t: (w if t in recent else w * _VARIETY_BOOST)
            for t, w in weights.items()}


def roll_strategy(config: dict, state: BotState, context: dict[str, Any]) -> dict:
    """Pick a new random strategy, modulated by current context.

    context keys: has_army (bool), recent_defeat (bool), gold (float),
                  targets (list of scored targets, best first).
    """
    # Per-bot personality bias: applied before context modulation so hard
    # constraints below (e.g. attack=0 without an army) still win.
    weights = _personality_weights(config, state)

    if not context.get("has_army"):
        # No army yet: the attack planner can create one (incl. saving toward
        # it), so only gate when an army is financially out of reach.
        army_price = float(context.get("army_price", 0.0) or 0.0)
        if army_price > 0 and context.get("gold", 0.0) < 0.3 * army_price:
            weights["attack"] = 0
            weights["artifact"] = 0
        else:
            # Army build-up costs time within the strategy window → half weight
            weights["attack"] = weights.get("attack", 0) / 2
            weights["artifact"] = weights.get("artifact", 0) / 2
    if context.get("recent_defeat"):
        weights["defense"] = weights.get("defense", 0) * 2
    if context.get("recent_attack_defeat"):
        # A lost attack re-prioritizes the offensive (mirror of the
        # defensive defeat boost above).
        weights["attack"] = weights.get("attack", 0) * 2
    if context.get("gold", 0.0) < 200:
        weights["economy"] = weights.get("economy", 0) * 2
    if not context.get("targets"):
        weights["attack"] = 0
        weights["artifact"] = 0

    types = [t for t in STRATEGY_TYPES if weights.get(t, 0) > 0]
    if not types:
        types, weights = ["economy"], {"economy": 1}
    # Boost types not seen recently so all strategies get played over time.
    weights = _variety_weights(weights, state.memory)
    chosen = random.choices(types, weights=[weights[t] for t in types], k=1)[0]

    # Record for variety tracking (keep last 10)
    history = state.memory.setdefault("strategy_history", [])
    history.append(chosen)
    state.memory["strategy_history"] = history[-10:]

    params: dict[str, Any] = {}
    if chosen in ("attack", "artifact"):
        targets = context.get("targets", [])
        if chosen == "artifact":
            with_artifacts = [t for t in targets if t.get("artifact_count", 0) > 0]
            targets = with_artifacts or targets
        # targets are pre-sorted best-first; sample from the top-N (weighted
        # toward the best) so different bots pick different opponents.
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
    """Pick a secondary strategy type for the dispatcher to also draw from.

    Personality-weighted like roll_strategy, but only the type matters (no
    duration/target machinery). The active type is excluded; attack/artifact
    are only eligible when a target already exists (no spy/attack sequencing as
    a secondary), since they need params the dispatcher won't construct.
    """
    weights = _personality_weights(config, state)
    weights.pop(active_type, None)
    if not has_target:
        weights.pop("attack", None)
        weights.pop("artifact", None)
    types = [t for t in STRATEGY_TYPES if weights.get(t, 0) > 0]
    if not types:
        return None
    return random.choices(types, weights=[weights[t] for t in types], k=1)[0]


def should_respond_to_breach(config: dict, personality: str) -> bool:
    """Whether a bot reacts to an AI breach by switching to defense.

    Defensive bots always respond; aggressive/economy bots often ignore the
    breach and keep their current plan, so their personality stays visible
    instead of being permanently pinned to defense by repeated break-throughs.
    Unknown personality / missing config → always respond (safe default).
    """
    chance = (config.get("breach_response_chance") or {}).get(personality, 1.0)
    return random.random() < float(chance)


def breach_defense_strategy(config: dict) -> dict:
    """Forced switch to defense after an AI wave broke through.

    A breach means the current defense is insufficient — whatever the bot was
    doing, the next hours are spent strengthening the perimeter.
    """
    return {
        "type": "defense",
        "params": {},
        "valid_until": _valid_until(config, "defense"),
        "source": "breach",
        "started_at": now_iso(),
    }


def should_respond_to_attack_defeat(config: dict, personality: str) -> bool:
    """Whether a bot reacts to a LOST attack by switching back to attack.

    Offensive analog of should_respond_to_breach: aggressive bots almost
    always retaliate, defensive bots rather go back to building. Unknown
    personality / missing config → respond (mirrors the breach default).
    """
    chance = (config.get("attack_defeat_response_chance") or {}).get(personality, 1.0)
    return random.random() < float(chance)


def attack_defeat_strategy(config: dict, target_uid: int, target_name: str) -> dict:
    """Forced switch back to attack after losing an attack (revenge).

    Mirror of breach_defense_strategy: a lost attack means the army was not
    strong enough — the next window is spent spying, strengthening and
    retaliating against the same opponent.
    """
    return {
        "type": "attack",
        "params": {"target_uid": target_uid, "target_name": target_name,
                   "phase": "strengthen"},
        "valid_until": _valid_until(config, "attack"),
        "source": "revenge",
        "started_at": now_iso(),
    }


def make_override(payload: dict, config: dict) -> dict:
    """Build a strategy dict from a control-API override payload.

    Accepts ``duration_hours`` (preferred); falls back to the strategy's
    configured range when omitted.
    """
    stype = payload.get("type")
    if stype not in STRATEGY_TYPES:
        raise ValueError(f"unknown strategy type: {stype}")
    duration = payload.get("duration_hours")
    if duration is not None:
        until = datetime.now(timezone.utc) + timedelta(hours=float(duration))
        valid_until = until.strftime("%Y-%m-%dT%H:%M:%SZ")
    else:
        valid_until = _valid_until(config, stype)
    params = dict(payload.get("params", {}))
    if stype in ("attack", "artifact"):
        params.setdefault("phase", "spy")
    return {
        "type": stype,
        "params": params,
        "valid_until": valid_until,
        "source": "override",
        "started_at": now_iso(),
    }
