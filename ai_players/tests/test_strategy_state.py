import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import bot.state as state_mod  # noqa: E402
from bot.state import BotState  # noqa: E402
from bot.strategy import is_expired, make_override, roll_strategy  # noqa: E402

CONFIG = {
    "strategy": {
        "weights": {"defense": 3, "attack": 2, "growth": 1},
        "duration_hours": {"defense": [3, 8]},
    }
}


def _iso(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def test_is_expired():
    assert is_expired(None)
    assert is_expired({})
    future = _iso(datetime.now(timezone.utc) + timedelta(hours=1))
    past = _iso(datetime.now(timezone.utc) - timedelta(hours=1))
    assert not is_expired({"valid_until": future})
    assert is_expired({"valid_until": past})


def test_roll_strategy_picks_attack_or_growth_when_target_exists():
    # roll_strategy is a weighted-random pick between attack/growth (never
    # defense — defense is only ever entered via a lost battle, not rolled).
    state = BotState(name="t")
    targets = [{"uid": 42, "name": "Weak", "artifact_count": 1, "score": 1.0}]
    for _ in range(50):
        s = roll_strategy(CONFIG, state, {"targets": targets})
        assert s["type"] in ("attack", "growth")
        assert not is_expired(s)
        if s["type"] == "attack":
            assert s["params"]["target_uid"] == 42
            assert s["params"]["phase"] == "strengthen"


def test_roll_strategy_no_targets_never_picks_attack():
    state = BotState(name="t")
    for _ in range(50):
        s = roll_strategy(CONFIG, state, {"targets": []})
        assert s["type"] != "attack"
        assert not is_expired(s)


def test_make_override():
    s = make_override({"type": "defense", "duration_hours": 6}, CONFIG)
    assert s["type"] == "defense" and s["source"] == "override"
    assert not is_expired(s)
    try:
        make_override({"type": "nonsense"}, CONFIG)
        assert False
    except ValueError:
        pass


def test_state_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setattr(state_mod, "STATES_DIR", tmp_path)
    state = BotState.load_or_create("testbot")
    assert state.account["username"].startswith("testbot_")
    state.account["uid"] = 7
    state.memory["opponents"]["Foo"] = {"est_strength": 0.5}
    state.save()

    loaded = BotState.load_or_create("testbot")
    assert loaded.account == state.account
    assert loaded.memory["opponents"]["Foo"]["est_strength"] == 0.5


def test_breach_defense_strategy():
    from bot.strategy import breach_defense_strategy
    s = breach_defense_strategy(CONFIG)
    assert s["type"] == "defense" and s["source"] == "breach"
    assert not is_expired(s)


def test_season_start_defense_strategy():
    # Rule 0: a bot with no strategy opens on defense, on the same wall-clock
    # window as a breach-forced defense (not NO_EXPIRY).
    from bot.strategy import NO_EXPIRY, season_start_defense_strategy
    s = season_start_defense_strategy(CONFIG)
    assert s["type"] == "defense" and s["source"] == "season_start"
    assert not is_expired(s)
    assert s["valid_until"] != NO_EXPIRY


def test_season_reset_leaves_no_strategy_so_rule_0_applies():
    # BotState.reset() (called by _check_season_reset on a new season) clears
    # the strategy, which is exactly the condition run_bot.py's rule 0 keys on.
    state = BotState(name="t")
    state.strategy = {"type": "attack", "params": {}, "valid_until": "2099-01-01T00:00:00Z"}
    state.reset()
    assert state.strategy is None




