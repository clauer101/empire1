import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bot.planners.base import BotContext, cheapest_affordable  # noqa: E402
from bot.savings import clear_goal, get_goal, set_goal, spendable_gold  # noqa: E402

ISO = "%Y-%m-%dT%H:%M:%SZ"
STRATEGY = {"type": "defense",
            "valid_until": (datetime.now(timezone.utc)
                            + timedelta(hours=8)).strftime(ISO)}

ITEMS = {"knowledge": {"FIRE": {"costs": {"gold": 100}, "requirements": []}}}


def _ctx(gold, memory):
    summary = {"resources": {"gold": gold, "culture": 0},
               "buildings": {}, "knowledge": {}}
    return BotContext(summary, ITEMS, memory, dict(STRATEGY), None)


def test_goal_blocks_non_owner_spending():
    memory = {}
    set_goal(memory, item="BIG_TOWER", action="tower", amount=500,
             strategy=STRATEGY)
    assert spendable_gold(400, memory, STRATEGY) == 0.0
    assert spendable_gold(600, memory, STRATEGY) == 100.0
    ctx = _ctx(400, memory)
    # baseline path (respect_savings default) blocked, owner bypass works
    assert cheapest_affordable(ITEMS["knowledge"], ctx) is None
    assert cheapest_affordable(ITEMS["knowledge"], ctx,
                               respect_savings=False) == "FIRE"


def test_goal_expiry_restores_spending():
    memory = {}
    set_goal(memory, item="x", action="tower", amount=500,
             strategy=STRATEGY, ttl_h=-1)  # already expired
    assert get_goal(memory, STRATEGY) is None
    assert "savings_goal" not in memory
    assert spendable_gold(400, memory, STRATEGY) == 400


def test_strategy_change_clears_goal():
    memory = {}
    set_goal(memory, item="x", action="army", amount=500, strategy=STRATEGY)
    assert get_goal(memory, {"type": "economy"}) is None
    assert "savings_goal" not in memory


def test_ttl_capped_by_strategy_end():
    memory = {}
    short = {"type": "defense",
             "valid_until": (datetime.now(timezone.utc)
                             + timedelta(minutes=30)).strftime(ISO)}
    goal = set_goal(memory, item="x", action="tower", amount=1,
                    strategy=short, ttl_h=5)
    assert goal["expires_at"] <= short["valid_until"]


def test_clear_goal():
    memory = {}
    set_goal(memory, item="x", action="tower", amount=1, strategy=STRATEGY)
    clear_goal(memory)
    assert get_goal(memory, STRATEGY) is None


def _attack_strategy(hours=2):
    return {"type": "attack",
            "valid_until": (datetime.now(timezone.utc)
                            + timedelta(hours=hours)).strftime(ISO)}


def test_sticky_goal_survives_strategy_type_change():
    memory = {}
    set_goal(memory, item="army", action="army", amount=500,
             strategy=_attack_strategy(), sticky=True)
    goal = get_goal(memory, {"type": "economy"})
    assert goal is not None and goal["sticky"] is True
    # reserved gold stays protected from a non-owning spender after the re-roll
    assert spendable_gold(700, memory, {"type": "economy"}) == 200.0


def test_sticky_goal_still_expires_on_ttl():
    memory = {}
    set_goal(memory, item="army", action="army", amount=500,
             strategy=_attack_strategy(), sticky=True, ttl_h=-1)
    assert get_goal(memory, {"type": "economy"}) is None


def test_sticky_goal_not_clamped_to_strategy_end():
    memory = {}
    set_goal(memory, item="army", action="army", amount=500,
             strategy=_attack_strategy(hours=0.001), sticky=True, ttl_h=2)
    # outlives the tiny attack window it was created in
    assert get_goal(memory, {"type": "economy"}) is not None
