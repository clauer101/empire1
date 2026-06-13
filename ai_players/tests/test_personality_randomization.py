"""Tests for per-bot personality bias and weighted top-N selection."""

import random
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import bot.state as state_mod  # noqa: E402
from bot.defense_analysis import pick_tower  # noqa: E402
from bot.planners.base import weighted_top_n  # noqa: E402
from bot.state import PERSONALITIES, BotState  # noqa: E402
from bot.strategy import roll_strategy, should_respond_to_breach  # noqa: E402

CONFIG = {
    "strategy": {
        "weights": {"economy": 4, "defense": 3, "attack": 2, "artifact": 1},
        "duration_hours": {"economy": [4, 10], "defense": [3, 8],
                           "attack": [1, 3], "artifact": [1, 3]},
    },
    "personalities": {
        "economy":    {"economy": 3.0, "defense": 1.0, "attack": 0.5, "artifact": 0.7},
        "aggressive": {"economy": 0.7, "defense": 0.5, "attack": 3.0, "artifact": 1.5},
        "defensive":  {"economy": 1.0, "defense": 3.0, "attack": 0.5, "artifact": 0.5},
        "balanced":   {"economy": 1.0, "defense": 1.0, "attack": 1.0, "artifact": 1.0},
    },
    "selection": {"top_n": 3},
    "breach_response_chance": {
        "economy": 0.3, "aggressive": 0.2, "defensive": 1.0, "balanced": 0.6,
    },
}


# --- weighted_top_n ---------------------------------------------------------

def test_weighted_top_n_deterministic_for_n1():
    items = [("a", 1), ("b", 5), ("c", 3)]
    for _ in range(20):
        assert weighted_top_n(items, key=lambda x: x[1], n=1) == ("b", 5)


def test_weighted_top_n_ascending():
    items = [("a", 1), ("b", 5), ("c", 3)]
    assert weighted_top_n(items, key=lambda x: x[1], n=1, reverse=False) == ("a", 1)


def test_weighted_top_n_empty():
    assert weighted_top_n([], key=lambda x: x, n=3) is None


def test_weighted_top_n_distributes_but_favors_best():
    items = [("a", 10), ("b", 9), ("c", 8), ("d", 1)]
    rng = random.Random(1234)
    counts = Counter(weighted_top_n(items, key=lambda x: x[1], n=3, rng=rng)[0]
                     for _ in range(3000))
    # Only the top 3 ever chosen; the worst (d) never.
    assert "d" not in counts
    assert set(counts) == {"a", "b", "c"}
    # Best is most frequent.
    assert counts["a"] > counts["b"] > counts["c"]


# --- personality bias -------------------------------------------------------

def _attack_share(personality: str, draws: int = 2000) -> float:
    state = BotState(name="t", personality=personality)
    targets = [{"uid": 1, "name": "X", "score": 1.0}]
    ctx = {"has_army": True, "gold": 1000, "targets": targets}
    types = Counter(roll_strategy(CONFIG, state, ctx)["type"] for _ in range(draws))
    return (types["attack"] + types["artifact"]) / draws


def test_aggressive_attacks_more_than_economy():
    assert _attack_share("aggressive") > _attack_share("economy") + 0.2


def test_defensive_picks_defense_most():
    state = BotState(name="t", personality="defensive")
    ctx = {"has_army": True, "gold": 1000, "targets": [{"uid": 1, "name": "X", "score": 1.0}]}
    types = Counter(roll_strategy(CONFIG, state, ctx)["type"] for _ in range(2000))
    assert types.most_common(1)[0][0] == "defense"


def test_missing_personality_config_falls_back_balanced():
    # CONFIG without personalities → no multiplier applied, still valid roll.
    cfg = {"strategy": CONFIG["strategy"], "selection": {"top_n": 1}}
    state = BotState(name="t", personality="aggressive")
    s = roll_strategy(cfg, state, {"has_army": False, "gold": 1000, "targets": []})
    assert s["type"] in ("economy", "defense")


# --- personality persistence ------------------------------------------------

def test_new_account_gets_personality(tmp_path, monkeypatch):
    monkeypatch.setattr(state_mod, "STATES_DIR", tmp_path)
    state = BotState.load_or_create("pbot")
    assert state.personality in PERSONALITIES


def test_personality_persists_across_reload(tmp_path, monkeypatch):
    monkeypatch.setattr(state_mod, "STATES_DIR", tmp_path)
    state = BotState.load_or_create("pbot")
    state.personality = "aggressive"
    state.save()
    loaded = BotState.load_or_create("pbot")
    assert loaded.personality == "aggressive"


def test_legacy_state_without_personality_defaults_balanced(tmp_path, monkeypatch):
    monkeypatch.setattr(state_mod, "STATES_DIR", tmp_path)
    (tmp_path / "old.yaml").write_text(
        "account: {username: bot_old_x, uid: 3}\nstrategy: null\n")
    loaded = BotState.load_or_create("old")
    assert loaded.personality == "balanced"


# --- breach response by personality ----------------------------------------

def test_defensive_always_responds_to_breach():
    for _ in range(200):
        assert should_respond_to_breach(CONFIG, "defensive") is True


def test_aggressive_often_ignores_breach():
    responses = sum(should_respond_to_breach(CONFIG, "aggressive") for _ in range(2000))
    # chance 0.2 → roughly 400; assert it clearly ignores most breaches.
    assert 200 < responses < 700


def test_missing_breach_config_defaults_to_always_respond():
    cfg = {"strategy": CONFIG["strategy"]}
    for _ in range(50):
        assert should_respond_to_breach(cfg, "aggressive") is True


# --- pick_tower randomization ----------------------------------------------

def test_pick_tower_top_n_deterministic_default():
    structures = {
        "T1": {"class": "arrow", "damage": 10, "reload_time": 1000, "range": 2},
        "T2": {"class": "arrow", "damage": 5, "reload_time": 1000, "range": 1},
    }
    for _ in range(10):
        assert pick_tower(structures, {}, lambda it: True) == "T1"


def test_pick_tower_top_n_samples():
    structures = {
        "T1": {"class": "arrow", "damage": 10, "reload_time": 1000, "range": 2},
        "T2": {"class": "arrow", "damage": 9, "reload_time": 1000, "range": 2},
    }
    rng = random.Random(7)
    picks = Counter(pick_tower(structures, {}, lambda it: True, top_n=3, rng=rng)
                    for _ in range(500))
    assert set(picks) == {"T1", "T2"}
