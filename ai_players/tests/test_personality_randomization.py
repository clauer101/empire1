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
from bot.strategy import roll_strategy  # noqa: E402

CONFIG = {
    "strategy": {
        "weights": {"defense": 3, "attack": 2, "growth": 1},
        "duration_hours": {"defense": [3, 8]},
    },
    "personalities": {
        "aggressive": {"defense": 0.5, "attack": 3.0, "growth": 0.3},
        "defensive":  {"defense": 3.0, "attack": 0.5, "growth": 2.0},
        "balanced":   {"defense": 1.0, "attack": 1.0, "growth": 1.0},
    },
    "selection": {"top_n": 3},
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


# --- roll_strategy: weighted-random between attack/growth (never defense —
# defense is only ever entered via a lost battle, not rolled). Reached after
# DEFENSE_WIN_STREAK_TARGET consecutive defense wins (run_bot.py). Attack is
# excluded from the pool when no attackable target exists. ------------------

def test_rolls_both_attack_and_growth_when_target_exists():
    targets = [{"uid": 1, "name": "X", "score": 1.0}]
    state = BotState(name="t", personality="balanced")
    seen = {roll_strategy(CONFIG, state, {"targets": targets})["type"] for _ in range(200)}
    assert seen == {"attack", "growth"}


def test_never_rolls_defense():
    targets = [{"uid": 1, "name": "X", "score": 1.0}]
    state = BotState(name="t", personality="balanced")
    for _ in range(200):
        assert roll_strategy(CONFIG, state, {"targets": targets})["type"] != "defense"


def test_attack_params_set_when_attack_rolled():
    targets = [{"uid": 1, "name": "X", "score": 1.0}]
    state = BotState(name="t", personality="balanced")
    for _ in range(200):
        s = roll_strategy(CONFIG, state, {"targets": targets})
        if s["type"] == "attack":
            assert s["params"]["target_uid"] == 1
            assert s["params"]["phase"] == "strengthen"
            return
    raise AssertionError("attack was never rolled in 200 tries")


def test_aggressive_favors_attack_over_growth():
    targets = [{"uid": 1, "name": "X", "score": 1.0}]
    state = BotState(name="t", personality="aggressive")
    counts = Counter(roll_strategy(CONFIG, state, {"targets": targets})["type"]
                     for _ in range(1000))
    assert counts["attack"] > counts["growth"]


def test_defensive_favors_growth_over_attack():
    targets = [{"uid": 1, "name": "X", "score": 1.0}]
    state = BotState(name="t", personality="defensive")
    counts = Counter(roll_strategy(CONFIG, state, {"targets": targets})["type"]
                     for _ in range(1000))
    assert counts["growth"] > counts["attack"]


def test_falls_back_to_defense_when_no_targets_and_growth_has_no_weight():
    cfg = {"strategy": {"weights": {"defense": 3, "attack": 2, "growth": 0},
                        "duration_hours": CONFIG["strategy"]["duration_hours"]}}
    state = BotState(name="t", personality="balanced")
    s = roll_strategy(cfg, state, {"targets": []})
    assert s["type"] == "defense"
    assert s["source"] == "no_targets"


def test_no_targets_still_allows_growth():
    state = BotState(name="t", personality="balanced")
    for _ in range(200):
        assert roll_strategy(CONFIG, state, {"targets": []})["type"] in ("growth", "defense")


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
