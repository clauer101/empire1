"""Test that building effects are only applied when buildings are fully completed."""

import pytest
from gameserver.models.empire import Empire
from gameserver.engine.empire_service import EmpireService
from gameserver.engine.upgrade_provider import UpgradeProvider
from gameserver.loaders.item_loader import load_items
from gameserver.util.events import EventBus


class TestBuildingEffectsCompletion:
    """Verify that effects are only applied when buildings are fully completed."""

    @pytest.fixture
    def upgrade_provider(self):
        """Load items from YAML."""
        items = load_items("config")
        provider = UpgradeProvider()
        provider.load(items)
        return provider

    @pytest.fixture
    def empire_service(self, upgrade_provider):
        """Create empire service with test items."""
        bus = EventBus()
        svc = EmpireService(upgrade_provider, bus)
        return svc

    def test_incomplete_building_does_not_apply_effects(self, empire_service):
        """
        An incomplete building (remaining_effort > 0) should NOT apply its effects
        to the empire's resource generation.
        """
        # Setup: Create empire
        empire = Empire(uid=1, name="Test Empire")
        
        # Add FIRE_PLACE as incomplete (remaining effort = 10, not 0)
        empire.buildings["FIRE_PLACE"] = 10.0  # Not complete!
        
        # Calculate effects
        empire_service.recalculate_effects(empire)
        
        # FIRE_PLACE has gold_offset: 0.1, but since it's incomplete, 
        # gold_offset should be 0
        assert empire.get_effect("gold_offset", 0.0) == 0.0, \
            "Incomplete building should not apply gold_offset effect"

    def test_completed_building_applies_effects(self, empire_service):
        """
        A completed building (remaining_effort = 0) should apply its effects
        to the empire's resource generation.
        """
        # Setup: Create empire
        empire = Empire(uid=1, name="Test Empire")
        
        # Add FIRE_PLACE as complete (remaining effort = 0)
        empire.buildings["FIRE_PLACE"] = 0.0  # Complete!
        
        # Calculate effects
        empire_service.recalculate_effects(empire)
        
        # FIRE_PLACE has gold_offset: 0.1, which should now be applied
        assert empire.get_effect("gold_offset", 0.0) == 0.1, \
            "Completed building should apply gold_offset effect"

    def test_transition_from_incomplete_to_complete(self, empire_service):
        """
        Test that effects are only applied after a building becomes complete.
        - Step 1: Building incomplete -> no effects
        - Step 2: Building complete -> effects applied
        """
        # Setup: Create empire
        empire = Empire(uid=1, name="Test Empire")
        
        # Step 1: Add FIRE_PLACE as incomplete
        empire.buildings["FIRE_PLACE"] = 10.0
        empire_service.recalculate_effects(empire)
        assert empire.get_effect("gold_offset", 0.0) == 0.0, \
            "Step 1: Incomplete building should not apply effects"
        
        # Step 2: Mark building as complete (remaining effort = 0)
        empire.buildings["FIRE_PLACE"] = 0.0
        empire_service.recalculate_effects(empire)
        assert empire.get_effect("gold_offset", 0.0) == 0.1, \
            "Step 2: Completed building should now apply effects"

    def test_multiple_buildings_effects_accumulate_only_when_complete(self, empire_service):
        """
        Test with multiple buildings where only complete ones contribute effects.
        - FIRE_PLACE: incomplete (10.0 remaining) -> should NOT contribute 0.1 gold
        - SHRINE: complete (0.0 remaining) -> should contribute 0.05 culture
        - EXCHANGE_POST: complete (0.0 remaining) -> should contribute 0.05 gold + 0.1 gold_modifier
        """
        # Setup: Create empire
        empire = Empire(uid=1, name="Test Empire")
        
        # Add buildings
        empire.buildings["FIRE_PLACE"] = 10.0      # INCOMPLETE - gold_offset: 0.1
        empire.buildings["SHRINE"] = 0.0            # COMPLETE - culture_offset: 0.05
        empire.buildings["EXCHANGE_POST"] = 0.0     # COMPLETE - gold_offset: 0.05, gold_modifier: 0.1
        
        # Calculate effects
        empire_service.recalculate_effects(empire)
        
        # Only completed buildings should apply effects:
        # - FIRE_PLACE (incomplete) should NOT contribute 0.1
        # - SHRINE (complete) should contribute 0.05 to culture
        # - EXCHANGE_POST (complete) should contribute 0.05 to gold and 0.1 to gold_modifier
        
        gold_offset = empire.get_effect("gold_offset", 0.0)
        culture_offset = empire.get_effect("culture_offset", 0.0)
        gold_modifier = empire.get_effect("gold_modifier", 0.0)
        
        # Gold offset: only EXCHANGE_POST's 0.05 (not FIRE_PLACE's 0.1)
        assert abs(gold_offset - 0.05) < 0.0001, \
            f"Gold offset should be 0.05 (only from completed EXCHANGE_POST), got {gold_offset}"
        
        # Culture offset: only SHRINE's 0.05
        assert abs(culture_offset - 0.05) < 0.0001, \
            f"Culture offset should be 0.05 (only from completed SHRINE), got {culture_offset}"
        
        # Gold modifier: only EXCHANGE_POST's 0.1
        assert abs(gold_modifier - 0.1) < 0.0001, \
            f"Gold modifier should be 0.1 (only from completed EXCHANGE_POST), got {gold_modifier}"

    def test_zero_remaining_effort_is_complete(self, empire_service):
        """
        Confirm that a building with remaining_effort = 0.0 is considered complete
        and should apply its effects.
        """
        empire = Empire(uid=1, name="Test Empire")
        
        # Exactly 0.0 remaining (complete)
        empire.buildings["SHRINE"] = 0.0
        empire_service.recalculate_effects(empire)
        
        assert empire.get_effect("culture_offset", 0.0) == 0.05, \
            "Building with 0.0 remaining effort should be complete and apply effects"

    def test_nearly_complete_building_does_not_apply_effects(self, empire_service):
        """
        Even a nearly-complete building (remaining_effort = 0.001) should NOT apply effects.
        Effects should only apply when remaining_effort == 0.
        """
        empire = Empire(uid=1, name="Test Empire")
        
        # Nearly complete, but not quite (0.001 remaining)
        empire.buildings["SHRINE"] = 0.001
        empire_service.recalculate_effects(empire)
        
        assert empire.get_effect("culture_offset", 0.0) == 0.0, \
            "Building with 0.001 remaining effort should NOT apply effects (not complete)"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
