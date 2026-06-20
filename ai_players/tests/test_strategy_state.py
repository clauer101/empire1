import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import bot.state as state_mod  # noqa: E402
from bot.state import BotState  # noqa: E402
from bot.strategy import is_expired, make_override, roll_strategy  # noqa: E402

CONFIG = {
    "strategy": {
        "weights": {"economy": 4, "defense": 3, "attack": 2, "artifact": 1},
        "duration_hours": {"economy": [4, 10], "defense": [3, 8],
                           "attack": [1, 3], "artifact": [1, 3]},
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


def test_roll_without_army_and_poor_never_attacks():
    # gold far below 30% of the next army price → attack/artifact stay 0
    state = BotState(name="t")
    targets = [{"uid": 42, "name": "Weak", "artifact_count": 1, "score": 1.0}]
    for _ in range(50):
        s = roll_strategy(CONFIG, state, {"has_army": False, "gold": 10,
                                          "army_price": 1000, "targets": targets})
        assert s["type"] in ("economy", "defense")
        assert not is_expired(s)


def test_roll_without_army_but_rich_can_attack():
    # gold ≥ 30% of the army price → attack rollable (half weight)
    state = BotState(name="t")
    targets = [{"uid": 42, "name": "Weak", "artifact_count": 1, "score": 1.0}]
    found = False
    for _ in range(200):
        s = roll_strategy(CONFIG, state, {"has_army": False, "gold": 1000,
                                          "army_price": 500, "targets": targets})
        if s["type"] in ("attack", "artifact"):
            assert s["params"]["target_uid"] == 42
            assert s["params"]["phase"] == "strengthen"
            found = True
    assert found


def test_roll_without_army_no_targets_never_attacks():
    state = BotState(name="t")
    for _ in range(50):
        s = roll_strategy(CONFIG, state, {"has_army": False, "gold": 1000, "targets": []})
        assert s["type"] in ("economy", "defense")


def test_roll_attack_picks_target():
    state = BotState(name="t")
    targets = [{"uid": 42, "name": "Weak", "artifact_count": 1, "score": 1.0}]
    found = False
    for _ in range(100):
        s = roll_strategy(CONFIG, state, {"has_army": True, "gold": 1000,
                                          "targets": targets})
        if s["type"] in ("attack", "artifact"):
            assert s["params"]["target_uid"] == 42
            assert s["params"]["phase"] == "strengthen"
            found = True
    assert found


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


def test_attack_defeat_strategy():
    from bot.strategy import attack_defeat_strategy
    s = attack_defeat_strategy(CONFIG, 42, "Weak")
    assert s["type"] == "attack" and s["source"] == "revenge"
    assert s["params"] == {"target_uid": 42, "target_name": "Weak", "phase": "strengthen"}
    assert not is_expired(s)


def test_should_respond_to_attack_defeat_chances():
    from bot.strategy import should_respond_to_attack_defeat
    cfg = {"attack_defeat_response_chance": {"aggressive": 1.0, "defensive": 0.0}}
    assert all(should_respond_to_attack_defeat(cfg, "aggressive") for _ in range(20))
    assert not any(should_respond_to_attack_defeat(cfg, "defensive") for _ in range(20))
    # missing config / unknown personality → always respond (safe default)
    assert should_respond_to_attack_defeat({}, "balanced")


def test_roll_attack_defeat_boosts_attack_weight():
    # With the boost, attack should be rolled noticeably more often.
    state = BotState(name="t")
    targets = [{"uid": 42, "name": "Weak", "artifact_count": 0, "score": 1.0}]

    def attack_rate(boost: bool) -> float:
        ctx = {"has_army": True, "gold": 1000, "targets": targets,
               "recent_attack_defeat": boost}
        rolls = [roll_strategy(CONFIG, state, ctx)["type"] for _ in range(400)]
        return rolls.count("attack") / len(rolls)

    assert attack_rate(True) > attack_rate(False)
