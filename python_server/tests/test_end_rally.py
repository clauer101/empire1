"""Tests for the end-rally system.

Validates the full flow:
  1. end_criterion item is built/researched
  2. end_criterion_activated timestamp is set in global_state
  3. end_rally_effects are applied to ALL empires via recalculate_effects
  4. Rally expires after end_rally_duration
"""
from __future__ import annotations

import pytest
from gameserver.engine.empire_service import EmpireService
from gameserver.engine import global_state
from gameserver.engine.upgrade_provider import UpgradeProvider
from gameserver.loaders.game_config_loader import GameConfig
from gameserver.models.empire import Empire
from gameserver.models.items import ItemDetails, ItemType
from gameserver.util.events import EventBus

EMPIRE_A = 1
EMPIRE_B = 2
END_CRITERION_IID = "THE_WORLD_WONDER"
RALLY_GOLD_OFFSET = 2.0
RALLY_TRAVEL_MODIFIER = 0.5


@pytest.fixture(autouse=True)
def reset_global_state():
    """Ensure global_state is clean before and after each test."""
    global_state.restore_end_criterion_activated(None)
    yield
    global_state.restore_end_criterion_activated(None)


@pytest.fixture
def svc():
    event_bus = EventBus()

    # Register the end-criterion item with no costs/requirements
    wonder = ItemDetails(
        iid=END_CRITERION_IID,
        item_type=ItemType.BUILDING,
        effort=1.0,
        effects={},
    )
    upgrade_provider = UpgradeProvider()
    upgrade_provider.load([wonder])

    gc = GameConfig()
    gc.end_criterion = END_CRITERION_IID
    gc.end_rally_duration = 604800.0  # 1 week
    gc.end_rally_effects = {
        "gold_offset": RALLY_GOLD_OFFSET,
        "travel_time_modifier": RALLY_TRAVEL_MODIFIER,
    }

    empire_service = EmpireService(upgrade_provider, event_bus, gc)

    empire_a = Empire(uid=EMPIRE_A, name="Alpha")
    empire_b = Empire(uid=EMPIRE_B, name="Beta")
    empire_a.buildings[END_CRITERION_IID] = 0.0  # pre-complete the build
    empire_service.register(empire_a)
    empire_service.register(empire_b)

    return empire_service, gc


class TestEndRallyTrigger:
    def test_no_rally_before_criterion(self, svc):
        """Rally is not active before end_criterion is completed."""
        empire_service, gc = svc
        assert global_state.get_end_criterion_activated() is None
        assert not global_state.is_end_rally_active(gc)

    def test_rally_activates_when_criterion_built(self, svc):
        """Completing the end_criterion building triggers the rally."""
        empire_service, gc = svc
        empire_a = empire_service.get(EMPIRE_A)

        # Simulate completion: mark building done and call _apply_effects
        empire_a.buildings[END_CRITERION_IID] = 0.0
        empire_service._apply_effects(empire_a, END_CRITERION_IID)

        assert global_state.get_end_criterion_activated() is not None
        assert global_state.is_end_rally_active(gc)

    def test_rally_effects_applied_to_triggering_empire(self, svc):
        """After rally triggers, end_rally_effects appear on the triggering empire."""
        empire_service, gc = svc
        empire_a = empire_service.get(EMPIRE_A)

        empire_service._apply_effects(empire_a, END_CRITERION_IID)

        assert empire_a.effects.get("gold_offset", 0.0) == pytest.approx(RALLY_GOLD_OFFSET)
        assert empire_a.effects.get("travel_time_modifier", 0.0) == pytest.approx(RALLY_TRAVEL_MODIFIER)

    def test_rally_effects_applied_to_all_empires(self, svc):
        """After rally triggers, end_rally_effects are applied to ALL registered empires."""
        empire_service, gc = svc
        empire_a = empire_service.get(EMPIRE_A)
        empire_b = empire_service.get(EMPIRE_B)

        empire_service._apply_effects(empire_a, END_CRITERION_IID)

        # Both empires should have rally effects
        assert empire_b.effects.get("gold_offset", 0.0) == pytest.approx(RALLY_GOLD_OFFSET)
        assert empire_b.effects.get("travel_time_modifier", 0.0) == pytest.approx(RALLY_TRAVEL_MODIFIER)

    def test_rally_only_triggers_once(self, svc):
        """Calling _apply_effects with the end_criterion a second time does not re-trigger."""
        empire_service, gc = svc
        empire_a = empire_service.get(EMPIRE_A)

        empire_service._apply_effects(empire_a, END_CRITERION_IID)
        first_activation = global_state.get_end_criterion_activated()

        # Second call (e.g. another empire somehow completes the same item)
        empire_service._apply_effects(empire_a, END_CRITERION_IID)
        second_activation = global_state.get_end_criterion_activated()

        assert first_activation == second_activation

    def test_new_empire_recalculate_gets_rally_effects(self, svc):
        """An empire that calls recalculate_effects while rally is active gets the effects."""
        empire_service, gc = svc
        empire_a = empire_service.get(EMPIRE_A)

        # Trigger rally
        empire_service._apply_effects(empire_a, END_CRITERION_IID)

        # Register a new empire and recalculate
        empire_c = Empire(uid=99, name="Gamma")
        empire_service.register(empire_c)
        empire_service.recalculate_effects(empire_c)

        assert empire_c.effects.get("gold_offset", 0.0) == pytest.approx(RALLY_GOLD_OFFSET)

    def test_rally_inactive_after_duration_expires(self, svc):
        """Rally is considered inactive after end_rally_duration seconds have passed."""
        from datetime import datetime, timezone, timedelta

        empire_service, gc = svc
        gc.end_rally_duration = 10.0  # short duration for test

        # Set activation to 11 seconds ago (expired)
        expired_time = datetime.now(timezone.utc) - timedelta(seconds=11)
        global_state.restore_end_criterion_activated(expired_time)

        assert not global_state.is_end_rally_active(gc)

    def test_seconds_remaining_decreases_over_time(self, svc):
        """end_rally_seconds_remaining returns a value less than the full duration."""
        from datetime import datetime, timezone, timedelta

        empire_service, gc = svc
        gc.end_rally_duration = 3600.0

        # Set activation to 60 seconds ago
        past_time = datetime.now(timezone.utc) - timedelta(seconds=60)
        global_state.restore_end_criterion_activated(past_time)

        remaining = global_state.end_rally_seconds_remaining(gc)
        assert remaining == pytest.approx(3540.0, abs=2.0)  # 3600 - 60 ± 2s

    def test_non_criterion_item_does_not_trigger_rally(self, svc):
        """Completing a different item does not trigger the rally."""
        empire_service, gc = svc
        empire_a = empire_service.get(EMPIRE_A)

        empire_service._apply_effects(empire_a, "SOME_OTHER_ITEM")

        assert global_state.get_end_criterion_activated() is None
        assert not global_state.is_end_rally_active(gc)
