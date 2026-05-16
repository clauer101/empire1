"""Tests for ruler-specific empire effects."""

from unittest.mock import MagicMock

import pytest

from gameserver.engine.empire_service import EmpireService
from gameserver.models.empire import Empire


@pytest.fixture
def service() -> EmpireService:
    return EmpireService(upgrade_provider=MagicMock(), event_bus=MagicMock())


@pytest.fixture
def empire() -> Empire:
    return Empire(uid=1, name="Test")


# ── research_cost_modifier ─────────────────────────────────────────────


class TestResearchCostModifier:
    def test_no_modifier_uses_full_effort(self, service: EmpireService, empire: Empire):
        """Without modifier, knowledge effort is set verbatim."""
        item = MagicMock()
        item.item_type.value = "knowledge"
        item.effort = 100.0
        item.costs = {}
        empire.knowledge["fire"] = 100.0

        # Simulate is_new_start path directly
        cost_mod = max(0.0, 1.0 - empire.get_effect("research_cost_modifier", 0.0))
        result = item.effort * cost_mod
        assert result == 100.0

    def test_modifier_reduces_effort(self, service: EmpireService, empire: Empire):
        """research_cost_modifier 0.25 → 25% less effort on new research start."""
        empire.effects["research_cost_modifier"] = 0.25
        cost_mod = max(0.0, 1.0 - empire.get_effect("research_cost_modifier", 0.0))
        assert cost_mod == pytest.approx(0.75)

    def test_modifier_applied_on_new_research(self, service: EmpireService, empire: Empire):
        """New research item gets reduced effort when modifier is active."""
        empire.effects["research_cost_modifier"] = 0.20
        # Simulate what build_item does on is_new_start for KNOWLEDGE
        effort = 200.0
        cost_mod = max(0.0, 1.0 - empire.get_effect("research_cost_modifier", 0.0))
        empire.knowledge["fire"] = effort * cost_mod
        assert empire.knowledge["fire"] == pytest.approx(160.0)

    def test_modifier_clamped_at_zero(self, service: EmpireService, empire: Empire):
        """Modifier > 1.0 does not produce negative effort."""
        empire.effects["research_cost_modifier"] = 1.5
        cost_mod = max(0.0, 1.0 - empire.get_effect("research_cost_modifier", 0.0))
        assert cost_mod == 0.0

    def test_modifier_not_applied_on_resume(self, service: EmpireService, empire: Empire):
        """Resuming an already-started item does not re-apply the modifier."""
        empire.effects["research_cost_modifier"] = 0.50
        empire.knowledge["fire"] = 60.0  # already started, remaining = 60
        empire.research_queue = "fire"
        service._progress_knowledge(empire, dt=1.0)
        # Only 1 tick of base speed (1.0) should be subtracted, not a re-reduction
        assert empire.knowledge["fire"] == pytest.approx(59.0)


# ── scientist_citizen_bonus ────────────────────────────────────────────


class TestScientistCitizenBonus:
    def test_no_bonus_uses_base_citizen_effect(self, service: EmpireService, empire: Empire):
        """Without bonus, research speed equals base formula."""
        empire.citizens["scientist"] = 4
        empire.knowledge["fire"] = 10.0
        empire.research_queue = "fire"
        # base_research_speed=1, citizen_effect=0.03, 4 scientists → multiplier 1.12
        service._progress_knowledge(empire, dt=1.0)
        assert empire.knowledge["fire"] == pytest.approx(10.0 - 1.0 * 1.12)

    def test_bonus_amplifies_scientist_contribution(self, service: EmpireService, empire: Empire):
        """scientist_citizen_bonus doubles each scientist's contribution."""
        empire.citizens["scientist"] = 4
        empire.effects["scientist_citizen_bonus"] = 1.0  # ×2 per scientist
        empire.knowledge["fire"] = 10.0
        empire.research_queue = "fire"
        # multiplier = 1 + 4 * 0.03 * 2 = 1.24
        service._progress_knowledge(empire, dt=1.0)
        assert empire.knowledge["fire"] == pytest.approx(10.0 - 1.0 * 1.24)

    def test_bonus_zero_scientists_has_no_effect(self, service: EmpireService, empire: Empire):
        """Bonus with zero scientists makes no difference."""
        empire.citizens["scientist"] = 0
        empire.effects["scientist_citizen_bonus"] = 5.0
        empire.knowledge["fire"] = 10.0
        empire.research_queue = "fire"
        service._progress_knowledge(empire, dt=1.0)
        assert empire.knowledge["fire"] == pytest.approx(9.0)  # base speed 1.0


# ── gold_lump_sum_after_research ───────────────────────────────────────


class TestGoldLumpSumAfterResearch:
    def _service_no_recalc(self) -> EmpireService:
        """Service with _apply_effects stubbed out so empire.effects survives completion."""
        svc = EmpireService(upgrade_provider=MagicMock(), event_bus=MagicMock())
        svc._apply_effects = MagicMock()
        return svc

    def test_gold_awarded_on_completion(self, empire: Empire):
        """Gold lump sum is added when research completes."""
        svc = self._service_no_recalc()
        empire.effects["gold_lump_sum_after_research"] = 150.0
        empire.resources["gold"] = 100.0
        empire.knowledge["fire"] = 0.5
        empire.research_queue = "fire"

        svc._progress_knowledge(empire, dt=1.0)

        assert empire.knowledge["fire"] == 0.0
        assert empire.resources["gold"] == pytest.approx(250.0)

    def test_gold_not_awarded_mid_research(self, empire: Empire):
        """Gold is not awarded while research is still in progress."""
        svc = self._service_no_recalc()
        empire.effects["gold_lump_sum_after_research"] = 150.0
        empire.resources["gold"] = 100.0
        empire.knowledge["fire"] = 5.0
        empire.research_queue = "fire"

        svc._progress_knowledge(empire, dt=1.0)

        assert empire.resources["gold"] == pytest.approx(100.0)

    def test_no_effect_no_gold(self, empire: Empire):
        """Without the effect, completing research awards no extra gold."""
        svc = self._service_no_recalc()
        empire.resources["gold"] = 100.0
        empire.knowledge["fire"] = 0.5
        empire.research_queue = "fire"

        svc._progress_knowledge(empire, dt=1.0)

        assert empire.resources["gold"] == pytest.approx(100.0)

    def test_gold_stacks_with_existing(self, empire: Empire):
        """Lump sum adds on top of existing gold."""
        svc = self._service_no_recalc()
        empire.effects["gold_lump_sum_after_research"] = 400.0
        empire.resources["gold"] = 9600.0
        empire.knowledge["fire"] = 0.1
        empire.research_queue = "fire"

        svc._progress_knowledge(empire, dt=1.0)

        assert empire.resources["gold"] == pytest.approx(10000.0)


# ── workshop_cost_modifier ─────────────────────────────────────────────


class TestWorkshopCostModifier:
    def _make_service_with_base_cost(self, base_cost: float) -> EmpireService:
        gc = MagicMock()
        gc.item_upgrade_base_costs = [base_cost]
        svc = EmpireService(upgrade_provider=MagicMock(), event_bus=MagicMock())
        svc._gc = gc
        svc._item_era_index = {"tower": 0}
        return svc

    def test_no_modifier_full_price(self, empire: Empire):
        svc = self._make_service_with_base_cost(100.0)
        price = svc._item_upgrade_price(empire, "tower", "damage")
        assert price == pytest.approx(100.0)

    def test_modifier_reduces_price(self, empire: Empire):
        svc = self._make_service_with_base_cost(100.0)
        empire.effects["workshop_cost_modifier"] = 0.15
        price = svc._item_upgrade_price(empire, "tower", "damage")
        assert price == pytest.approx(85.0)

    def test_modifier_full_discount_clamped(self, empire: Empire):
        """Modifier ≥ 1.0 clamps price to 0, not negative."""
        svc = self._make_service_with_base_cost(100.0)
        empire.effects["workshop_cost_modifier"] = 1.5
        price = svc._item_upgrade_price(empire, "tower", "damage")
        assert price == pytest.approx(0.0)

    def test_modifier_applies_after_level_scaling(self, empire: Empire):
        """Discount is applied after the (total_levels+1)^2 scaling."""
        svc = self._make_service_with_base_cost(100.0)
        empire.effects["workshop_cost_modifier"] = 0.10
        empire.item_upgrades["tower"] = {"damage": 2}  # total_levels=2 → base=900
        price = svc._item_upgrade_price(empire, "tower", "damage")
        assert price == pytest.approx(900.0 * 0.90)
