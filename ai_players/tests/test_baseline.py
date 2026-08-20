import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bot.planners.base import BotContext  # noqa: E402
from bot.planners.baseline import baseline_action, min_towers  # noqa: E402

ITEMS = {
    "knowledge": {
        "FIRE": {"costs": {"gold": 10}, "requirements": []},
        "WHEEL": {"costs": {"gold": 999}, "requirements": []},
    },
    "buildings": {
        "HUT": {"costs": {"gold": 20}, "requirements": []},
    },
    "structures": {},
}


class MapApi:
    """Fake API returning a fixed map; default has 2 placed towers (floor met)."""

    def __init__(self, tiles=None):
        self.tiles = tiles if tiles is not None else {
            "0,0": "spawnpoint", "1,0": "path", "2,0": "castle",
            "0,1": "BASIC_TOWER", "1,1": "BASIC_TOWER"}

    def get_map(self):
        return {"tiles": dict(self.tiles)}


def _ctx(summary_extra=None, memory=None, api=None):
    summary = {"resources": {"gold": 100, "culture": 0},
               "research_queue": "", "build_queue": "",
               "buildings": {}, "knowledge": {}, "era": "stone"}
    summary.update(summary_extra or {})
    return BotContext(summary, ITEMS, memory or {}, {"type": "attack"},
                      api or MapApi())


def test_fills_empty_research_queue_first():
    # Both FIRE and WHEEL default to branch="main" (unset), so the
    # oldest-missing-main-branch-tech rule (both era="stone", tie broken by
    # dict order) deterministically forces FIRE first.
    action = baseline_action(_ctx())
    assert action and "research (main branch) FIRE" in action.description


def test_fills_build_queue_when_research_busy():
    action = baseline_action(_ctx({"research_queue": "FIRE"}))
    assert action and "build HUT" in action.description


def test_no_action_when_queues_busy():
    ctx = _ctx({"research_queue": "FIRE", "build_queue": "HUT"})
    assert baseline_action(ctx) is None


def test_breach_response_places_tower_with_new_planner():
    memory = {"pending_breach": True}
    items = dict(ITEMS)
    items["structures"] = {
        "BASIC_TOWER": {"costs": {"gold": 50}, "requirements": [],
                        "damage": 1, "range": 1.5, "reload_time": 2000,
                        "effects": {}},
    }

    class FakeApi:
        def get_map(self):
            return {"tiles": {"0,0": "spawnpoint", "1,0": "path",
                              "2,0": "castle", "1,1": "empty"}}

    summary = {"resources": {"gold": 100, "culture": 0},
               "research_queue": "X", "build_queue": "Y",
               "buildings": {}, "knowledge": {"HUNTING": 0},
               "tile_price": 999}
    ctx = BotContext(summary, items, memory, {"type": "attack"}, FakeApi())
    action = baseline_action(ctx)
    assert action and "baseline defense" in action.description
    assert "BASIC_TOWER" in action.description
    assert memory["pending_breach"] is False


def test_min_towers_scales_with_era():
    assert min_towers(_ctx()) == 2  # stone
    assert min_towers(_ctx({"era": "iron"})) == 2 + 2 * 3


def test_tower_floor_triggers_defense_regardless_of_strategy():
    items = dict(ITEMS)
    items["structures"] = {
        "BASIC_TOWER": {"costs": {"gold": 50}, "requirements": [],
                        "damage": 1, "range": 1.5, "reload_time": 2000,
                        "effects": {}},
    }

    class FakeApi:
        def get_map(self):
            return {"tiles": {"0,0": "spawnpoint", "1,0": "path",
                              "2,0": "castle", "1,1": "empty"}}

    summary = {"research_queue": "X", "build_queue": "Y", "tile_price": 999,
               "knowledge": {"HUNTING": 0}}
    ctx = _ctx(summary, api=FakeApi())
    ctx.items = items
    action = baseline_action(ctx)
    assert action and "towers 0/2" in action.description
    assert "BASIC_TOWER" in action.description


def test_tower_floor_satisfied_no_defense_action():
    # floor met (2 placed in stone) and queues busy → nothing to do
    ctx = _ctx({"research_queue": "X", "build_queue": "Y"})
    assert baseline_action(ctx) is None


def test_claims_ruler_when_unlocked():
    items = dict(ITEMS)
    items["rulers"] = {"MAJA": {}, "BORIN": {}}
    # floor met (2 towers), queues busy → baseline reaches the ruler step
    ctx = _ctx({"research_queue": "X", "build_queue": "Y",
                "effects": {"ruler_unlock": 1}, "ruler": {"type": ""}})
    ctx.items = items
    action = baseline_action(ctx)
    # pick_ruler is random — any catalog ruler is valid
    assert action and ("claim ruler MAJA" in action.description
                       or "claim ruler BORIN" in action.description)


def test_no_ruler_claim_without_unlock():
    items = dict(ITEMS)
    items["rulers"] = {"MAJA": {}}
    ctx = _ctx({"research_queue": "X", "build_queue": "Y",
                "ruler": {"type": ""}})  # no ruler_unlock effect
    ctx.items = items
    assert baseline_action(ctx) is None


def test_no_ruler_claim_when_already_chosen():
    items = dict(ITEMS)
    items["rulers"] = {"MAJA": {}}
    ctx = _ctx({"research_queue": "X", "build_queue": "Y",
                "effects": {"ruler_unlock": 1}, "ruler": {"type": "MAJA"}})
    ctx.items = items
    assert baseline_action(ctx) is None


def test_build_queue_bypasses_savings_cap_when_no_income():
    # Army savings goal (amount 1000) far exceeds gold (100) → spendable_gold
    # would normally be 0, blocking HUT (price 20). With base_gold <= 0 the
    # empire can never out-earn the goal, so the build queue bypasses the cap.
    memory = {"savings_goal": {
        "item": "army", "action": "army", "amount": 1000.0,
        "strategy_type": "attack", "sticky": True,
        "created_at": "2026-01-01T00:00:00Z", "expires_at": "2099-01-01T00:00:00Z"}}
    ctx = _ctx({"research_queue": "FIRE", "base_gold": 0.0}, memory=memory)
    action = baseline_action(ctx)
    assert action and "build HUT" in action.description


def test_build_queue_respects_savings_cap_when_income_positive():
    # Same goal, but base_gold > 0 → the empire will eventually reach the
    # goal on its own, so the normal savings cap applies and build stays idle.
    memory = {"savings_goal": {
        "item": "army", "action": "army", "amount": 1000.0,
        "strategy_type": "attack", "sticky": True,
        "created_at": "2026-01-01T00:00:00Z", "expires_at": "2099-01-01T00:00:00Z"}}
    ctx = _ctx({"research_queue": "FIRE", "base_gold": 5.0}, memory=memory)
    assert baseline_action(ctx) is None


def test_pending_breach_cleared_even_without_affordable_defense():
    memory = {"pending_breach": True}

    class FakeApi:
        def get_map(self):
            return {"tiles": {}}  # nothing the defense planner can act on

    ctx = _ctx({"research_queue": "FIRE", "build_queue": "HUT"},
               memory=memory, api=FakeApi())
    assert baseline_action(ctx) is None
    assert memory["pending_breach"] is False
