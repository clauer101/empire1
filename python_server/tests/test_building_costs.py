"""Unit tests for building cost deduction in build_item."""

import pytest
from gameserver.models.empire import Empire
from gameserver.engine.empire_service import EmpireService
from gameserver.engine.upgrade_provider import UpgradeProvider
from gameserver.loaders.item_loader import load_items
from gameserver.util.events import EventBus


def _make_items():
    """Load all items from config directory."""
    return load_items("config")


def _make_service():
    """Create empire service with all items loaded."""
    items = _make_items()
    up = UpgradeProvider()
    up.load(items)
    bus = EventBus()
    return EmpireService(up, bus)


@pytest.fixture
def service():
    """Create empire service."""
    return _make_service()


@pytest.fixture
def empire_with_gold(service):
    """Create empire with plenty of gold to build."""
    empire = Empire(uid=1, name="Test Empire")
    empire.resources["gold"] = 100000.0
    # Add BASE_CAMP as prerequisite (starting building)
    empire.buildings["BASE_CAMP"] = 0.0  # Mark as completed
    service.register(empire)
    return empire


class TestBuildingCostDeduction:
    """Test that building costs are deducted correctly."""

    def test_cost_deducted_on_first_build_start(self, service, empire_with_gold):
        """Costs should be deducted when starting a new building."""
        initial_gold = empire_with_gold.resources["gold"]
        
        # Start building FIRE_PLACE (costs 20 gold)
        result = service.build_item(empire_with_gold, "FIRE_PLACE")
        
        # Should succeed
        assert result is None, f"Expected success but got error: {result}"
        
        # 20 gold should be deducted
        assert empire_with_gold.resources["gold"] == initial_gold - 20, \
            f"Expected 20 gold deducted for FIRE_PLACE, but got {initial_gold - empire_with_gold.resources['gold']} deducted"

    def test_cost_not_deducted_on_resume(self, service, empire_with_gold):
        """Costs should NOT be deducted when resuming a paused building."""
        initial_gold = empire_with_gold.resources["gold"]
        
        # Start building FIRE_PLACE (costs 20 gold)
        service.build_item(empire_with_gold, "FIRE_PLACE")
        gold_after_first = empire_with_gold.resources["gold"]
        
        # Simulate pausing by adding gold
        empire_with_gold.resources["gold"] += 100  # Add extra gold
        
        # Now resume FIRE_PLACE (it still has progress)
        empire_with_gold.resources["gold"] += 100  # Add extra gold again
        service.build_item(empire_with_gold, "FIRE_PLACE")
        gold_after_resume = empire_with_gold.resources["gold"]
        
        # Gold should NOT have changed from resuming (no costs on resume)
        # Flow: 100000 - 20 (FIRE_PLACE first start) + 100 + 100 - 0 (no cost on resume)
        # = 100180
        assert gold_after_resume == 100180, \
            f"Expected 100180 gold (no cost on resume), got {gold_after_resume}"

    def test_insufficient_gold_blocks_build(self, service, empire_with_gold):
        """Building with costs should fail if insufficient gold."""
        # FIRE_PLACE costs 20 gold — set gold below that
        empire_with_gold.resources["gold"] = 0.0
        
        result = service.build_item(empire_with_gold, "FIRE_PLACE")
        
        # Should fail because not enough gold
        assert result is not None, "Expected error when gold is insufficient"
        assert "gold" in result.lower(), f"Expected gold error, got: {result}"
        
        # With exactly enough gold it should succeed
        empire_with_gold.resources["gold"] = 20.0
        result2 = service.build_item(empire_with_gold, "FIRE_PLACE")
        assert result2 is None, f"Expected success with exact gold, got: {result2}"

    def test_multiple_costs_deducted_correctly(self, service, empire_with_gold):
        """Each building deducts its own gold cost."""
        initial_gold = empire_with_gold.resources["gold"]
        
        # Build FIRE_PLACE (costs 20 gold)
        service.build_item(empire_with_gold, "FIRE_PLACE")
        gold_after_first = empire_with_gold.resources["gold"]
        cost_one = initial_gold - gold_after_first
        assert cost_one == 20, f"FIRE_PLACE should cost 20 gold, got {cost_one}"
        
        # Mark FIRE_PLACE complete and build MAIN_HOUSE (costs 500 gold)
        empire_with_gold.buildings["FIRE_PLACE"] = 0.0  # Mark completed
        service.build_item(empire_with_gold, "MAIN_HOUSE")
        gold_after_second = empire_with_gold.resources["gold"]
        cost_two = gold_after_first - gold_after_second
        assert cost_two == 500, f"MAIN_HOUSE should cost 500 gold, got {cost_two}"

    def test_completed_building_cannot_rebuild(self, service, empire_with_gold):
        """Cannot rebuild an already completed building."""
        # Mark FIRE_PLACE as completed
        empire_with_gold.buildings["FIRE_PLACE"] = 0.0
        initial_gold = empire_with_gold.resources["gold"]
        
        result = service.build_item(empire_with_gold, "FIRE_PLACE")
        
        # Should return error
        assert result is not None, "Expected error for completed building"
        assert "already completed" in result, f"Expected completion error, got: {result}"
        
        # Gold should remain unchanged
        assert empire_with_gold.resources["gold"] == initial_gold

    def test_cost_deducted_before_effort_set(self, service, empire_with_gold):
        """Ensure building state is set correctly after cost deduction."""
        initial_gold = empire_with_gold.resources["gold"]
        
        # Start FIRE_PLACE (costs 20 gold)
        service.build_item(empire_with_gold, "FIRE_PLACE")
        
        # Check that:
        # 1. Cost WAS deducted (FIRE_PLACE costs 20)
        assert empire_with_gold.resources["gold"] == initial_gold - 20, \
            f"Expected 20 gold deducted, got {initial_gold - empire_with_gold.resources['gold']}"
        
        # 2. Building effort was set
        assert "FIRE_PLACE" in empire_with_gold.buildings
        assert empire_with_gold.buildings["FIRE_PLACE"] > 0, \
            "Building effort should be set to positive value"

    def test_cost_scaling_with_effort(self, service, empire_with_gold):
        """Verify building costs are deducted correctly."""
        # FIRE_PLACE: effort 120, cost 20 gold
        initial_gold = empire_with_gold.resources["gold"]
        service.build_item(empire_with_gold, "FIRE_PLACE")
        cost1 = initial_gold - empire_with_gold.resources["gold"]
        assert cost1 == 20, f"FIRE_PLACE should cost 20 gold, got {cost1}"
        
        # Now mark FIRE_PLACE as complete and try MAIN_HOUSE
        empire_with_gold.resources["gold"] = initial_gold
        empire_with_gold.buildings["FIRE_PLACE"] = 0.0  # Mark as completed
        
        # MAIN_HOUSE: effort 1000, cost 500 gold
        service.build_item(empire_with_gold, "MAIN_HOUSE")
        cost2 = initial_gold - empire_with_gold.resources["gold"]
        assert cost2 == 500, f"MAIN_HOUSE should cost 500 gold, got {cost2}"

    def test_gold_exactly_required_succeeds(self, service, empire_with_gold):
        """Building should succeed when gold equals exact cost."""
        # FIRE_PLACE costs exactly 20 gold
        empire_with_gold.resources["gold"] = 20.0
        
        result = service.build_item(empire_with_gold, "FIRE_PLACE")
        
        # Should succeed with exact amount
        assert result is None, f"Expected success with exact gold, got: {result}"
        
        # Gold should be 0 after deduction
        assert empire_with_gold.resources["gold"] == 0.0

    def test_gold_insufficient_by_one_fails(self, service, empire_with_gold):
        """Building should fail when gold is one short of required cost."""
        # FIRE_PLACE costs 20 gold — set to 19 (one short)
        empire_with_gold.resources["gold"] = 19.0
        
        result = service.build_item(empire_with_gold, "FIRE_PLACE")
        
        # Should fail (1 gold short)
        assert result is not None, "Expected failure when 1 gold short"
        assert "gold" in result.lower(), f"Expected gold error, got: {result}"
        
        # Gold should remain unchanged at 19
        assert abs(empire_with_gold.resources["gold"] - 19.0) < 0.01


class TestRequirementsAndCosts:
    """Test interaction between requirements and costs."""

    def test_requirements_checked_before_costs(self, service, empire_with_gold):
        """Requirements should be validated before deducting costs."""
        # Remove BASE_CAMP prerequisite to make FIRE_PLACE unavailable
        empire_with_gold.buildings.clear()
        initial_gold = empire_with_gold.resources["gold"]
        
        result = service.build_item(empire_with_gold, "FIRE_PLACE")
        
        # Should fail on requirements
        assert result is not None, "Expected error for unmet requirements"
        assert "Requirements not met" in result
        
        # Gold should not be deducted
        assert empire_with_gold.resources["gold"] == initial_gold, \
            "Gold should not be deducted when requirements are not met"
