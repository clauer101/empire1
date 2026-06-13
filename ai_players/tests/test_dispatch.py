"""Tests for the per-cycle option dispatcher."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import bot.dispatch as dispatch  # noqa: E402
from bot.planners.base import BotContext, Option  # noqa: E402

CONFIG = {"category_weights": {
              "balanced": {"economy": 1.0, "defense": 1.0, "attack": 1.0,
                           "baseline": 1.0},
              "aggressive": {"economy": 1.0, "defense": 1.0, "attack": 5.0,
                             "baseline": 1.0}},
          "active_strategy_boost": 1.0,
          "selection": {"top_n": 1}}


def _ctx(gold, personality="balanced", memory=None):
    summary = {"resources": {"gold": gold, "culture": 0}}
    return BotContext(summary, {}, memory if memory is not None else {},
                      {"type": "defense", "valid_until": "2099-01-01T00:00:00Z"}, None,
                      selection={"top_n": 1},
                      personality=personality)


def _ran(action):
    """Execute the chosen action's run() and return its sentinel."""
    return action.run(None) if action else None


def _patch(monkeypatch, options):
    monkeypatch.setattr(dispatch, "gather_options", lambda *a, **k: list(options))


def test_returns_one_action(monkeypatch):
    opts = [Option("defense", "place", lambda api: "A", price=10, gain=5),
            Option("defense", "other", lambda api: "B", price=10, gain=1)]
    _patch(monkeypatch, opts)
    action = dispatch.choose_action(_ctx(100), CONFIG, "defense", None)
    assert _ran(action) == "A"  # best gain/gold wins


def test_mandatory_beats_free_filler(monkeypatch):
    opts = [Option("baseline", "filler", lambda api: "F", price=0, gain=1,
                   filler=True),
            Option("attack", "spy", lambda api: "S", price=0, gain=1,
                   mandatory=True, priority=10)]
    _patch(monkeypatch, opts)
    action = dispatch.choose_action(_ctx(100), CONFIG, "attack", None)
    assert _ran(action) == "S"


def test_cheap_high_roi_beats_expensive_low_roi(monkeypatch):
    # "buy slot on a near-empty wave" (cheap, high ROI) should win over an
    # expensive low-ROI option.
    opts = [Option("attack", "buy slot", lambda api: "SLOT", price=10, gain=20),
            Option("attack", "big buy", lambda api: "BIG", price=1000, gain=50)]
    _patch(monkeypatch, opts)
    action = dispatch.choose_action(_ctx(5000), CONFIG, "attack", None)
    assert _ran(action) == "SLOT"  # 2.0 > 0.05 gain/gold


def test_personality_weight_changes_winner(monkeypatch):
    # Equal ROI economy vs attack option; aggressive personality favours attack.
    opts = [Option("economy", "eco", lambda api: "ECO", price=10, gain=10),
            Option("attack", "atk", lambda api: "ATK", price=10, gain=10)]
    _patch(monkeypatch, opts)
    action = dispatch.choose_action(_ctx(100, personality="aggressive"),
                                    CONFIG, "economy", None)
    assert _ran(action) == "ATK"


def test_saves_for_unaffordable_top_when_only_filler(monkeypatch):
    # Top option (tower) unaffordable, only a filler is affordable → declare a
    # savings goal toward the tower, run nothing or the filler.
    memory = {}
    opts = [Option("defense", "place tower", lambda api: "T", price=500, gain=50,
                   saves_for=500, goal_meta={"item": "TOWER", "action": "tower"}),
            Option("baseline", "filler", lambda api: "F", price=5, gain=1,
                   filler=True)]
    _patch(monkeypatch, opts)
    ctx = _ctx(10, memory=memory)
    action = dispatch.choose_action(ctx, CONFIG, "defense", None)
    goal = memory.get("savings_goal")
    assert goal and goal["item"] == "TOWER" and goal["amount"] == 500
    # filler must respect the savings cap: gold 10 - goal 500 < 5 → blocked
    assert action is None


def test_does_not_save_when_productive_action_affordable(monkeypatch):
    # Top option unaffordable, but a productive (non-filler) cheaper option is
    # affordable → take it, don't idle gold on a goal.
    memory = {}
    opts = [Option("defense", "expensive", lambda api: "X", price=500, gain=50,
                   saves_for=500, goal_meta={"item": "BIG", "action": "tower"}),
            Option("defense", "place now", lambda api: "NOW", price=10, gain=5)]
    _patch(monkeypatch, opts)
    ctx = _ctx(50, memory=memory)
    action = dispatch.choose_action(ctx, CONFIG, "defense", None)
    assert _ran(action) == "NOW"
    assert "savings_goal" not in memory


def test_goal_cleared_when_owner_affordable(monkeypatch):
    # An active goal whose owning option is now affordable → execute and clear.
    memory = {}
    opts = [Option("defense", "the tower", lambda api: "T", price=100, gain=50,
                   saves_for=100, goal_meta={"item": "TOWER", "action": "tower"})]
    _patch(monkeypatch, opts)
    from bot.savings import set_goal
    set_goal(memory, item="TOWER", action="tower", amount=100,
             strategy={"type": "defense", "valid_until": "2099-01-01T00:00:00Z"})
    ctx = _ctx(150, memory=memory)
    action = dispatch.choose_action(ctx, CONFIG, "defense", None)
    assert _ran(action) == "T"
    assert "savings_goal" not in memory


def test_no_options_returns_none(monkeypatch):
    _patch(monkeypatch, [])
    assert dispatch.choose_action(_ctx(100), CONFIG, "defense", None) is None


def test_secondary_attack_does_not_advance_phase():
    """As a secondary strategy the attack planner must not advance its phase
    machine (no spy/attack/transition), only emit idempotent options."""
    from bot.planners.attack import AttackPlanner

    class FakeApi:
        def military(self):
            return {"armies": [{"aid": 1, "next_wave_price": 0.0,
                                "waves": [{"iid": "C", "slots": 1}]}],
                    "available_critters": []}

    summary = {"resources": {"gold": 1000, "culture": 0},
               "attacks_outgoing": [], "effects": {}, "ruler": {"type": ""}}
    strategy = {"type": "attack", "valid_until": "2099-01-01T00:00:00Z",
                "params": {"target_uid": 9, "target_name": "v", "phase": "spy"}}
    ctx = BotContext(summary, {"critters": {}, "rulers": {}}, {}, strategy,
                     FakeApi())
    AttackPlanner().propose_options(ctx, advance_phase=False)
    # phase must stay "spy" — secondary invocation never advances it
    assert strategy["params"]["phase"] == "spy"
