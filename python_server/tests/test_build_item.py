"""Tests for EmpireService.build_item() — requirement & cost validation."""

from __future__ import annotations

import pytest

from gameserver.models.empire import Empire
from gameserver.models.items import ItemDetails, ItemType
from gameserver.engine.empire_service import EmpireService
from gameserver.engine.upgrade_provider import UpgradeProvider
from gameserver.util.events import EventBus


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_items() -> list[ItemDetails]:
    """Create a minimal tech tree:

    INIT (building, effort=0, reqs=[])
      └─ FIRE_PLACE (building, effort=20, reqs=[INIT])
           ├─ MAIN_HOUSE (building, effort=100, reqs=[FIRE_PLACE])
           └─ HUNTING (knowledge, effort=20, reqs=[FIRE_PLACE])
                └─ CRAFTSMANSHIP (knowledge, effort=50, reqs=[FIRE_PLACE])
    """
    return [
        ItemDetails(iid="INIT", name="Initialization", item_type=ItemType.BUILDING,
                    effort=0, costs={}, requirements=[], effects={}),
        ItemDetails(iid="FIRE_PLACE", name="Fire Place", item_type=ItemType.BUILDING,
                    effort=20, costs={}, requirements=["INIT"], effects={}),
        ItemDetails(iid="MAIN_HOUSE", name="Main House", item_type=ItemType.BUILDING,
                    effort=100, costs={"gold": 50.0}, requirements=["FIRE_PLACE"], effects={}),
        ItemDetails(iid="HUNTING", name="Hunting", item_type=ItemType.KNOWLEDGE,
                    effort=20, costs={}, requirements=["FIRE_PLACE"], effects={}),
        ItemDetails(iid="CRAFTSMANSHIP", name="Craftsmanship", item_type=ItemType.KNOWLEDGE,
                    effort=50, costs={"culture": 10.0}, requirements=["FIRE_PLACE"], effects={}),
    ]


def _make_service() -> EmpireService:
    up = UpgradeProvider()
    up.load(_make_items())
    bus = EventBus()
    return EmpireService(up, bus)


def _make_empire(**overrides) -> Empire:
    defaults = dict(
        uid=1,
        name="Test",
        resources={"gold": 500.0, "culture": 200.0, "life": 10.0},
        buildings={"INIT": 0.0},  # INIT auto-completed
    )
    defaults.update(overrides)
    return Empire(**defaults)


# ---------------------------------------------------------------------------
# Tests — requirement checks
# ---------------------------------------------------------------------------

class TestBuildItemRequirements:
    """Verify that build_item enforces tech tree requirements."""

    def setup_method(self):
        self.svc = _make_service()

    def test_build_with_requirements_met(self):
        """FIRE_PLACE requires INIT — INIT is completed → should succeed."""
        empire = _make_empire()
        err = self.svc.build_item(empire, "FIRE_PLACE")
        assert err is None
        assert "FIRE_PLACE" in empire.buildings
        assert empire.build_queue == "FIRE_PLACE"

    def test_build_with_requirements_not_met(self):
        """MAIN_HOUSE requires FIRE_PLACE — not completed → should fail."""
        empire = _make_empire()  # only INIT completed
        err = self.svc.build_item(empire, "MAIN_HOUSE")
        assert err is not None
        assert "Requirements not met" in err
        assert "MAIN_HOUSE" not in empire.buildings

    def test_research_with_building_requirement_met(self):
        """HUNTING requires FIRE_PLACE (a building) — completed → success."""
        empire = _make_empire(buildings={"INIT": 0.0, "FIRE_PLACE": 0.0})
        err = self.svc.build_item(empire, "HUNTING")
        assert err is None
        assert "HUNTING" in empire.knowledge
        assert empire.research_queue == "HUNTING"

    def test_research_with_building_requirement_not_met(self):
        """HUNTING requires FIRE_PLACE — only INIT completed → should fail."""
        empire = _make_empire()  # only INIT
        err = self.svc.build_item(empire, "HUNTING")
        assert err is not None
        assert "Requirements not met" in err
        assert "HUNTING" not in empire.knowledge

    def test_research_with_building_in_progress_not_completed(self):
        """FIRE_PLACE in progress (remaining > 0) should NOT count as completed."""
        empire = _make_empire(buildings={"INIT": 0.0, "FIRE_PLACE": 10.0})
        err = self.svc.build_item(empire, "HUNTING")
        assert err is not None
        assert "Requirements not met" in err

    def test_chain_build_after_completion(self):
        """After FIRE_PLACE is completed (remaining=0), MAIN_HOUSE should work."""
        empire = _make_empire(buildings={"INIT": 0.0, "FIRE_PLACE": 0.0})
        err = self.svc.build_item(empire, "MAIN_HOUSE")
        assert err is None
        assert "MAIN_HOUSE" in empire.buildings


# ---------------------------------------------------------------------------
# Tests — cost deduction
# ---------------------------------------------------------------------------

class TestBuildItemCosts:
    """Verify cost checks and deductions."""

    def setup_method(self):
        self.svc = _make_service()

    def test_costs_deducted_on_build(self):
        """MAIN_HOUSE costs 50 gold — should be deducted."""
        empire = _make_empire(buildings={"INIT": 0.0, "FIRE_PLACE": 0.0})
        gold_before = empire.resources["gold"]
        err = self.svc.build_item(empire, "MAIN_HOUSE")
        assert err is None
        assert empire.resources["gold"] == gold_before - 50.0

    def test_insufficient_resources_rejected(self):
        """Not enough gold → should fail, resources unchanged."""
        empire = _make_empire(
            buildings={"INIT": 0.0, "FIRE_PLACE": 0.0},
            resources={"gold": 10.0, "culture": 200.0, "life": 10.0},
        )
        err = self.svc.build_item(empire, "MAIN_HOUSE")
        assert err is not None
        assert "Not enough" in err
        assert empire.resources["gold"] == 10.0  # unchanged

    def test_research_costs_deducted(self):
        """CRAFTSMANSHIP costs 10 culture."""
        empire = _make_empire(buildings={"INIT": 0.0, "FIRE_PLACE": 0.0})
        culture_before = empire.resources["culture"]
        err = self.svc.build_item(empire, "CRAFTSMANSHIP")
        assert err is None
        assert empire.resources["culture"] == culture_before - 10.0


# ---------------------------------------------------------------------------
# Tests — queue constraints
# ---------------------------------------------------------------------------

class TestBuildItemQueue:
    """Verify queue busy / duplicate prevention."""

    def setup_method(self):
        self.svc = _make_service()

    def test_duplicate_building_rejected(self):
        """Cannot start a building that is already started or completed."""
        empire = _make_empire(buildings={"INIT": 0.0, "FIRE_PLACE": 0.0})
        err = self.svc.build_item(empire, "FIRE_PLACE")
        assert err is not None
        assert "already" in err.lower()

    def test_build_queue_busy(self):
        """Cannot start another building while one is in progress."""
        empire = _make_empire(buildings={"INIT": 0.0})
        self.svc.build_item(empire, "FIRE_PLACE")  # fills build_queue
        assert empire.build_queue == "FIRE_PLACE"
        # Try starting another — should fail (FIRE_PLACE not done yet)
        # MAIN_HOUSE requires FIRE_PLACE anyway, but let's test queue busy
        empire.buildings["FIRE_PLACE"] = 0.0  # force complete for requirement
        err = self.svc.build_item(empire, "MAIN_HOUSE")
        # build_queue is still FIRE_PLACE (we didn't clear it)
        assert err is not None
        assert "busy" in err.lower()

    def test_zero_effort_building_no_queue(self):
        """INIT has 0 effort — should complete instantly, no queue block."""
        empire = Empire(uid=2, name="Fresh")
        err = self.svc.build_item(empire, "INIT")
        assert err is None
        assert empire.buildings["INIT"] == 0.0
        assert empire.build_queue is None  # 0-effort doesn't occupy queue

    def test_research_queue_busy(self):
        """Cannot start two researches simultaneously."""
        empire = _make_empire(buildings={"INIT": 0.0, "FIRE_PLACE": 0.0})
        err1 = self.svc.build_item(empire, "HUNTING")
        assert err1 is None
        err2 = self.svc.build_item(empire, "CRAFTSMANSHIP")
        assert err2 is not None
        assert "busy" in err2.lower()
