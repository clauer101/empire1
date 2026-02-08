"""Tests for Empire build_queue and research_queue processing."""

from unittest.mock import MagicMock

import pytest

from gameserver.engine.empire_service import EmpireService
from gameserver.models.empire import Empire
from gameserver.util.constants import CITIZEN_EFFECT


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

        speed = 1.0 + 0.5  # base + effect
        service._progress_knowledge(empire, dt=1.0)

        assert empire.knowledge["fire"] == pytest.approx(10.0 - speed)

    def test_already_finished_research_clears(self, service: EmpireService, empire: Empire):
        empire.knowledge["fire"] = 0.0
        empire.research_queue = "fire"

        service._progress_knowledge(empire, dt=1.0)

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

