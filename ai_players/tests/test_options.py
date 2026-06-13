"""Unit tests for the Option abstraction and category weighting."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bot.planners.base import Action, Option, category_weight  # noqa: E402


def _opt(**kw):
    kw.setdefault("category", "defense")
    kw.setdefault("description", "x")
    kw.setdefault("run", lambda api: None)
    return Option(**kw)


def test_base_score_priced():
    assert _opt(price=100, gain=50).base_score() == 0.5


def test_base_score_free_is_infinite():
    assert _opt(price=0, gain=1).base_score() == float("inf")
    # free but no gain → worthless
    assert _opt(price=0, gain=0).base_score() == 0.0


def test_tiers():
    assert _opt(mandatory=True).tier() == 3
    assert _opt(price=0, gain=1).tier() == 2
    assert _opt(price=10, gain=1).tier() == 1


def test_to_action():
    o = _opt(description="do it", run=lambda api: "ran")
    a = o.to_action()
    assert isinstance(a, Action)
    assert a.description == "do it"
    assert a.run(None) == "ran"


def test_category_weight_defaults_to_one():
    assert category_weight({}, "balanced", "economy", "defense") == 1.0


def test_category_weight_uses_personality():
    cfg = {"category_weights": {"aggressive": {"attack": 1.6, "defense": 0.7}}}
    assert category_weight(cfg, "aggressive", "economy", "attack") == 1.6
    assert category_weight(cfg, "aggressive", "economy", "defense") == 0.7


def test_active_strategy_boost():
    cfg = {"category_weights": {"balanced": {"defense": 1.0}},
           "active_strategy_boost": 1.5}
    # defense option while defense is active → boosted
    assert category_weight(cfg, "balanced", "defense", "defense") == 1.5
    # economy option while defense active → no boost
    cfg["category_weights"]["balanced"]["economy"] = 1.0
    assert category_weight(cfg, "balanced", "defense", "economy") == 1.0


def test_artifact_maps_to_attack_category_for_boost():
    cfg = {"category_weights": {"balanced": {"attack": 1.0}},
           "active_strategy_boost": 2.0}
    # active artifact strategy boosts attack-category options
    assert category_weight(cfg, "balanced", "artifact", "attack") == 2.0
