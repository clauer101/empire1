"""Tests for the per-cycle option dispatcher."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import bot.dispatch as dispatch  # noqa: E402
from bot.planners.base import BotContext, Option  # noqa: E402

CONFIG: dict = {}  # strict priority dispatch takes no config (kept for call-site shape)


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


def test_free_option_always_runs_before_priced(monkeypatch):
    # Free option has lower priority number but must still win — free options
    # always outrank priced ones regardless of priority.
    opts = [Option("defense", "priced", lambda api: "PRICED", price=10, priority=99),
            Option("baseline", "free", lambda api: "FREE", price=0, priority=0)]
    _patch(monkeypatch, opts)
    action = dispatch.choose_action(_ctx(100), CONFIG, "defense")
    assert _ran(action) == "FREE"


def test_higher_priority_priced_option_wins(monkeypatch):
    opts = [Option("defense", "low", lambda api: "LOW", price=10, priority=1),
            Option("defense", "high", lambda api: "HIGH", price=10, priority=5)]
    _patch(monkeypatch, opts)
    action = dispatch.choose_action(_ctx(100), CONFIG, "defense")
    assert _ran(action) == "HIGH"


def test_unaffordable_higher_priority_is_skipped_for_affordable_lower(monkeypatch):
    # The highest-priority option is unaffordable and doesn't ask to save
    # (no saves_for/goal_meta) — it must not block a lower-priority option
    # that IS affordable.
    opts = [Option("defense", "big", lambda api: "BIG", price=1000, priority=5),
            Option("defense", "small", lambda api: "SMALL", price=10, priority=1)]
    _patch(monkeypatch, opts)
    action = dispatch.choose_action(_ctx(100), CONFIG, "defense")
    assert _ran(action) == "SMALL"


def test_exclude_skips_already_failed_option_this_tick(monkeypatch):
    # Simulates run_bot.py's action loop: a server-rejected option is passed
    # back in `exclude` so the next-highest-priority option still runs.
    opts = [Option("defense", "rejected", lambda api: "REJ", price=10, priority=5),
            Option("defense", "fallback", lambda api: "FALLBACK", price=10, priority=1)]
    _patch(monkeypatch, opts)
    action = dispatch.choose_action(_ctx(100), CONFIG, "defense",
                                    exclude={"rejected"})
    assert _ran(action) == "FALLBACK"


def test_unaffordable_top_priority_declares_goal_and_blocks_lower(monkeypatch):
    # Highest-priority option (tower) unaffordable and asks to save → a goal is
    # declared, and the goal's reserved gold blocks even a lower-priority
    # option that would otherwise be affordable (strict priority order: the
    # top priority's savings need always wins over running something lower).
    memory = {}
    opts = [Option("defense", "place tower", lambda api: "T", price=500,
                   priority=5, saves_for=500,
                   goal_meta={"item": "TOWER", "action": "tower"}),
            Option("baseline", "filler", lambda api: "F", price=5, priority=1)]
    _patch(monkeypatch, opts)
    ctx = _ctx(10, memory=memory)
    action = dispatch.choose_action(ctx, CONFIG, "defense")
    goal = memory.get("savings_goal")
    assert goal and goal["item"] == "TOWER" and goal["amount"] == 500
    # lower-priority option must respect the savings cap: gold 10 - goal 500 < 5 → blocked
    assert action is None


def test_unaffordable_option_without_goal_meta_does_not_block_lower(monkeypatch):
    # Highest-priority option is unaffordable but doesn't ask to save (no
    # saves_for/goal_meta) — no goal is declared, so a lower-priority
    # affordable option still runs.
    memory = {}
    opts = [Option("defense", "expensive", lambda api: "X", price=500, priority=5),
            Option("defense", "place now", lambda api: "NOW", price=10, priority=1)]
    _patch(monkeypatch, opts)
    ctx = _ctx(50, memory=memory)
    action = dispatch.choose_action(ctx, CONFIG, "defense")
    assert _ran(action) == "NOW"
    assert "savings_goal" not in memory


def test_goal_cleared_when_owner_affordable(monkeypatch):
    # An active goal whose owning option is now affordable → execute and clear.
    memory = {}
    opts = [Option("defense", "the tower", lambda api: "T", price=100,
                   priority=5, saves_for=100,
                   goal_meta={"item": "TOWER", "action": "tower"})]
    _patch(monkeypatch, opts)
    from bot.savings import set_goal
    set_goal(memory, item="TOWER", action="tower", amount=100,
             strategy={"type": "defense", "valid_until": "2099-01-01T00:00:00Z"})
    ctx = _ctx(150, memory=memory)
    action = dispatch.choose_action(ctx, CONFIG, "defense")
    assert _ran(action) == "T"
    assert "savings_goal" not in memory


def test_no_options_returns_none(monkeypatch):
    _patch(monkeypatch, [])
    assert dispatch.choose_action(_ctx(100), CONFIG, "defense") is None


def test_secondary_attack_still_advances_phase():
    """Attacking is free, so the attack planner keeps progressing its own
    phase machine even while a DIFFERENT strategy (e.g. defense) is active —
    its target/phase then live in memory["attack_state"], not strategy.params."""
    from bot.planners.attack import AttackPlanner

    class FakeApi:
        def military(self):
            return {"armies": [{"aid": 1, "next_wave_price": 0.0,
                                "waves": [{"iid": "C", "slots": 1}]}],
                    "available_critters": []}

    summary = {"resources": {"gold": 1000, "culture": 0},
               "attacks_outgoing": [], "effects": {}, "ruler": {"type": ""}}
    # Defense is the active strategy here — attack.py must still advance its
    # own (memory-backed) phase, since it self-detects it isn't active.
    strategy = {"type": "defense", "valid_until": "2099-01-01T00:00:00Z", "params": {}}
    memory = {"attack_state": {"target_uid": 9, "target_name": "v", "phase": "spy"}}
    ctx = BotContext(summary, {"critters": {}, "rulers": {}}, memory, strategy,
                     FakeApi())
    AttackPlanner().propose_options(ctx, advance_phase=False)
    assert memory["attack_state"]["phase"] == "wait_spy"
