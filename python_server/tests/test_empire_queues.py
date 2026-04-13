"""Tests for Empire build_queue and research_queue processing."""

from unittest.mock import MagicMock

import pytest

from gameserver.engine.empire_service import EmpireService
from gameserver.models.empire import Empire
CITIZEN_EFFECT: float = 0.03  # per-citizen modifier (matches game.yaml citizen_effect)


@pytest.fixture
def service() -> EmpireService:
    return EmpireService(upgrade_provider=MagicMock(), event_bus=MagicMock())


@pytest.fixture
def empire() -> Empire:
    return Empire(uid=1, name="Test")


# ── Build queue ────────────────────────────────────────────────────────


class TestBuildQueue:
    def test_no_active_build_does_nothing(self, service: EmpireService, empire: Empire):
        """build_queue is None → buildings dict unchanged."""
        empire.buildings["hut"] = 5.0
        service._progress_buildings(empire, dt=1.0)
        assert empire.buildings["hut"] == 5.0

    def test_active_build_progresses(self, service: EmpireService, empire: Empire):
        """The active build item ticks down, others stay untouched."""
        empire.buildings["hut"] = 5.0
        empire.buildings["wall"] = 3.0
        empire.build_queue = "hut"

        service._progress_buildings(empire, dt=2.0)

        assert empire.buildings["hut"] == 3.0
        assert empire.buildings["wall"] == 3.0

    def test_building_completes_and_clears(self, service: EmpireService, empire: Empire):
        """When remaining reaches 0 the build_queue is set to None."""
        empire.buildings["hut"] = 1.0
        empire.build_queue = "hut"

        service._progress_buildings(empire, dt=1.0)

        assert empire.buildings["hut"] == 0.0
        assert empire.build_queue is None

    def test_building_completes_with_overshoot(self, service: EmpireService, empire: Empire):
        """dt larger than remaining → clamped to 0, build_queue cleared."""
        empire.buildings["hut"] = 0.5
        empire.build_queue = "hut"

        service._progress_buildings(empire, dt=2.0)

        assert empire.buildings["hut"] == 0.0
        assert empire.build_queue is None

    def test_already_finished_item_clears(self, service: EmpireService, empire: Empire):
        """If active item has remaining ≤ 0, just clear it."""
        empire.buildings["hut"] = 0.0
        empire.build_queue = "hut"

        service._progress_buildings(empire, dt=1.0)

        assert empire.build_queue is None


# ── Research queue ─────────────────────────────────────────────────────


class TestResearchQueue:
    def test_no_active_research_does_nothing(self, service: EmpireService, empire: Empire):
        empire.knowledge["fire"] = 5.0
        service._progress_knowledge(empire, dt=1.0)
        assert empire.knowledge["fire"] == 5.0

    def test_active_research_progresses(self, service: EmpireService, empire: Empire):
        empire.knowledge["fire"] = 5.0
        empire.knowledge["wheel"] = 3.0
        empire.research_queue = "fire"

        service._progress_knowledge(empire, dt=2.0)

        assert empire.knowledge["fire"] == 3.0
        assert empire.knowledge["wheel"] == 3.0

    def test_research_completes_and_clears(self, service: EmpireService, empire: Empire):
        empire.knowledge["fire"] = 1.0
        empire.research_queue = "fire"

        service._progress_knowledge(empire, dt=1.0)

        assert empire.knowledge["fire"] == 0.0
        assert empire.research_queue is None

    def test_scientist_bonus_speeds_research(self, service: EmpireService, empire: Empire):
        empire.knowledge["fire"] = 10.0
        empire.research_queue = "fire"
        empire.citizens["scientist"] = 10

        speed = 1.0 + 10 * CITIZEN_EFFECT  # 1.3
        service._progress_knowledge(empire, dt=1.0)

        assert empire.knowledge["fire"] == pytest.approx(10.0 - speed)

    def test_research_effect_bonus(self, service: EmpireService, empire: Empire):
        empire.knowledge["fire"] = 10.0
        empire.research_queue = "fire"
        empire.effects["research_speed_modifier"] = 0.5

        # (base + offset) * (1 + modifier) = (1.0 + 0) * (1 + 0.5) = 1.5
        speed = 1.0 * (1 + 0.5)
        service._progress_knowledge(empire, dt=1.0)

        assert empire.knowledge["fire"] == pytest.approx(10.0 - speed)

    def test_research_speed_offset_bonus(self, service: EmpireService, empire: Empire):
        """research_speed_offset adds to base before multiplier is applied."""
        empire.knowledge["fire"] = 10.0
        empire.research_queue = "fire"
        empire.effects["research_speed_offset"] = 0.2

        # (base + offset) * (1 + modifier) = (1.0 + 0.2) * 1.0 = 1.2
        speed = (1.0 + 0.2) * 1.0
        service._progress_knowledge(empire, dt=1.0)

        assert empire.knowledge["fire"] == pytest.approx(10.0 - speed)

    def test_research_speed_offset_and_modifier_combined(self, service: EmpireService, empire: Empire):
        """offset and modifier stack multiplicatively: (base+offset)*(1+modifier)."""
        empire.knowledge["fire"] = 10.0
        empire.research_queue = "fire"
        empire.effects["research_speed_offset"] = 0.2
        empire.effects["research_speed_modifier"] = 0.5

        # (1.0 + 0.2) * (1 + 0.5) = 1.2 * 1.5 = 1.8
        speed = (1.0 + 0.2) * (1.0 + 0.5)
        service._progress_knowledge(empire, dt=1.0)

        assert empire.knowledge["fire"] == pytest.approx(10.0 - speed)

    def test_research_speed_offset_with_scientists(self, service: EmpireService, empire: Empire):
        """offset, modifier and scientist bonus all combine correctly."""
        empire.knowledge["fire"] = 10.0
        empire.research_queue = "fire"
        empire.effects["research_speed_offset"] = 0.2
        empire.citizens["scientist"] = 10

        # (base + offset) * (1 + modifier + scientists * citizen_effect)
        # = (1.0 + 0.2) * (1 + 0 + 10 * CITIZEN_EFFECT)
        speed = (1.0 + 0.2) * (1.0 + 10 * CITIZEN_EFFECT)
        service._progress_knowledge(empire, dt=1.0)

        assert empire.knowledge["fire"] == pytest.approx(10.0 - speed)

    def test_already_finished_research_clears(self, service: EmpireService, empire: Empire):
        empire.knowledge["fire"] = 0.0
        empire.research_queue = "fire"

        service._progress_knowledge(empire, dt=1.0)

        assert empire.research_queue is None


# ── Research speed formula contract ───────────────────────────────────
#
# The formula MUST be:  speed = (base + offset) * (1 + modifier + n_sci * citizen_effect)
#
# Both empire_service._progress_knowledge() AND the frontend research.js
# calculate the remaining wall-clock time from this formula. Any deviation
# between the two causes the UI to show wrong durations (the bug that was
# previously present in research.js where `offset` was not applied).
#
# These tests pin the exact formula end-to-end so a regression will fail
# loudly rather than silently showing wrong numbers in the UI.


class TestResearchSpeedFormulaContract:
    """Pin the research speed formula so backend/frontend regressions are caught."""

    def test_offset_applied_before_multiplier(self, service: EmpireService, empire: Empire):
        """Core invariant: offset adds to base FIRST, then the whole sum is multiplied.

        (base + offset) * (1 + modifier)  ≠  base * (1 + modifier) + offset
        """
        empire.knowledge["fire"] = 10.0
        empire.research_queue = "fire"
        empire.effects["research_speed_offset"] = 0.5
        empire.effects["research_speed_modifier"] = 1.0  # 2× multiplier

        # Correct:  (1.0 + 0.5) * (1 + 1.0) = 1.5 * 2 = 3.0
        # Wrong:     1.0 * (1 + 1.0) + 0.5   = 2.0 + 0.5 = 2.5
        expected_speed = (1.0 + 0.5) * (1.0 + 1.0)
        wrong_speed    =  1.0 * (1.0 + 1.0) + 0.5

        service._progress_knowledge(empire, dt=1.0)

        assert empire.knowledge["fire"] == pytest.approx(10.0 - expected_speed)
        assert empire.knowledge["fire"] != pytest.approx(10.0 - wrong_speed)

    def test_recalculate_effects_feeds_offset_into_progress(
        self, service: EmpireService, empire: Empire
    ):
        """End-to-end: a completed building with research_speed_offset is picked up
        by recalculate_effects and then used correctly in _progress_knowledge.

        This mirrors how the server populates summary.effects for the frontend.
        """
        # Simulate a completed building that grants research_speed_offset=0.2
        empire.buildings["scriptorium"] = 0.0  # 0 remaining = completed
        service._upgrades.get_effects.return_value = {"research_speed_offset": 0.2}
        service.recalculate_effects(empire)

        assert empire.effects.get("research_speed_offset") == pytest.approx(0.2)

        # Now research should use that offset
        empire.knowledge["fire"] = 10.0
        empire.research_queue = "fire"
        service._upgrades.get_effects.return_value = {}  # knowledge item has no extra effects

        expected_speed = (1.0 + 0.2) * 1.0  # no modifier, no scientists
        service._progress_knowledge(empire, dt=1.0)

        assert empire.knowledge["fire"] == pytest.approx(10.0 - expected_speed)

    def test_duration_formula(self, service: EmpireService, empire: Empire):
        """Documents the exact wall-clock duration formula used by both server and UI.

        Given effort E and speed factors, the expected duration is:
            duration = E / ((base + offset) * (1 + modifier + scientists * citizen_effect))
        """
        effort = 360.0
        empire.knowledge["fire"] = effort
        empire.research_queue = "fire"
        empire.effects["research_speed_offset"] = 0.2
        empire.effects["research_speed_modifier"] = 0.5
        empire.citizens["scientist"] = 4

        base     = service._base_research_speed  # 1.0
        offset   = 0.2
        modifier = 0.5
        speed    = (base + offset) * (1.0 + modifier + 4 * CITIZEN_EFFECT)
        expected_duration = effort / speed

        # Advance by the expected duration — should be exactly done
        service._progress_knowledge(empire, dt=expected_duration)
        assert empire.knowledge["fire"] == pytest.approx(0.0, abs=1e-9)
        assert empire.research_queue is None


# ── Integration via step() ─────────────────────────────────────────────


class TestStepIntegration:
    def test_step_processes_both(self, service: EmpireService, empire: Empire):
        """step() should advance both build and research."""
        empire.buildings["hut"] = 5.0
        empire.build_queue = "hut"
        empire.knowledge["fire"] = 5.0
        empire.research_queue = "fire"

        service.step(empire, dt=2.0)

        assert empire.buildings["hut"] == 3.0
        assert empire.knowledge["fire"] == 3.0

    def test_step_leaves_non_active_items_alone(self, service: EmpireService, empire: Empire):
        """Items in buildings/knowledge but NOT active must not change."""
        empire.buildings["old"] = 2.0
        empire.knowledge["old_k"] = 2.0
        # build_queue / research_queue are None

        service.step(empire, dt=1.0)

        assert empire.buildings["old"] == 2.0
        assert empire.knowledge["old_k"] == 2.0


# ── Effects recalculated on completion ────────────────────────────────


class TestEffectsRecalculatedOnCompletion:
    """empire.effects must be updated immediately when a building or research completes.

    Regression guard: if recalculate_effects() is not called on completion,
    the empire continues playing with stale (missing) effects until the next
    server restart.
    """

    def test_building_completion_updates_effects(self, service: EmpireService, empire: Empire):
        """Completing a building must populate empire.effects with its effects."""
        empire.buildings["granary"] = 1.0
        empire.build_queue = "granary"
        service._upgrades.get_effects.return_value = {"gold_offset": 5.0}

        assert empire.effects.get("gold_offset", 0.0) == 0.0  # not yet active

        service._progress_buildings(empire, dt=1.0)

        assert empire.buildings["granary"] == 0.0
        assert empire.effects.get("gold_offset") == pytest.approx(5.0)

    def test_research_completion_updates_effects(self, service: EmpireService, empire: Empire):
        """Completing a research item must populate empire.effects with its effects."""
        empire.knowledge["iron_smelting"] = 1.0
        empire.research_queue = "iron_smelting"
        service._upgrades.get_effects.return_value = {"damage_modifier": 0.2}

        assert empire.effects.get("damage_modifier", 0.0) == 0.0

        service._progress_knowledge(empire, dt=1.0)

        assert empire.knowledge["iron_smelting"] == 0.0
        assert empire.effects.get("damage_modifier") == pytest.approx(0.2)

    def test_multiple_completed_items_stack_effects(self, service: EmpireService, empire: Empire):
        """Effects from all completed items accumulate correctly after recalculate."""
        empire.buildings["granary"] = 0.0   # already complete
        empire.buildings["mill"] = 0.0      # already complete
        empire.knowledge["iron_smelting"] = 0.0  # already complete

        def get_effects(iid):
            return {
                "granary": {"gold_offset": 5.0},
                "mill": {"gold_offset": 3.0},
                "iron_smelting": {"damage_modifier": 0.2},
            }.get(iid, {})

        service._upgrades.get_effects.side_effect = get_effects
        service.recalculate_effects(empire)

        assert empire.effects.get("gold_offset") == pytest.approx(8.0)
        assert empire.effects.get("damage_modifier") == pytest.approx(0.2)

