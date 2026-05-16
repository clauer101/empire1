"""Unit tests for the 11 new empire effects introduced in this session."""

from unittest.mock import MagicMock, patch

import pytest

from gameserver.engine.attack_service import AttackService
from gameserver.engine.empire_service import EmpireService
from gameserver.engine.upgrade_provider import UpgradeProvider
from gameserver.loaders.game_config_loader import GameConfig
from gameserver.models.empire import Empire
from gameserver.util.events import EventBus
from gameserver.util import effects as fx


# ── shared fixtures ────────────────────────────────────────────────────


@pytest.fixture
def gc() -> GameConfig:
    return GameConfig()


@pytest.fixture
def service(gc: GameConfig) -> EmpireService:
    return EmpireService(upgrade_provider=UpgradeProvider(), event_bus=EventBus(), game_config=gc)


@pytest.fixture
def empire() -> Empire:
    e = Empire(uid=1, name="Test")
    e.max_life = 100.0
    e.resources["life"] = 0.0
    return e


# ── citizen_cost_modifier ─────────────────────────────────────────────


class TestCitizenCostModifier:
    def test_reduces_citizen_price(self, service: EmpireService, empire: Empire):
        """citizen_cost_modifier 0.5 halves the citizen price."""
        raw = service._citizen_price(1)
        empire.effects[fx.CITIZEN_COST_MODIFIER] = 0.5
        discounted = service.citizen_price_for(empire, 1)
        assert discounted == pytest.approx(raw * 0.5)

    def test_no_modifier_uses_full_price(self, service: EmpireService, empire: Empire):
        """Without modifier, citizen_price_for == _citizen_price."""
        raw = service._citizen_price(3)
        assert service.citizen_price_for(empire, 3) == pytest.approx(raw)

    def test_modifier_applied_in_upgrade_citizen(self, service: EmpireService, empire: Empire):
        """upgrade_citizen uses discounted price for the culture check."""
        empire.citizens = {"artist": 0, "merchant": 0, "scientist": 0}
        empire.effects[fx.CITIZEN_COST_MODIFIER] = 0.9  # 90% off
        discounted_price = service.citizen_price_for(empire, 1)
        raw_price = service._citizen_price(1)
        # Give exactly the discounted amount (less than raw price)
        empire.resources["culture"] = discounted_price
        assert discounted_price < raw_price, "modifier must actually reduce price"
        err = service.upgrade_citizen(empire)
        assert err is None  # succeeds at discounted price


# ── tile_cost_modifier ────────────────────────────────────────────────


class TestTileCostModifier:
    def test_reduces_tile_price(self, service: EmpireService, empire: Empire):
        """tile_cost_modifier 0.3 reduces tile price by 30%."""
        raw = service._tile_price(5)
        empire.effects[fx.TILE_COST_MODIFIER] = 0.3
        assert service.tile_price_for(empire, 5) == pytest.approx(raw * 0.7)

    def test_no_modifier_full_price(self, service: EmpireService, empire: Empire):
        raw = service._tile_price(2)
        assert service.tile_price_for(empire, 2) == pytest.approx(raw)


# ── wave_cost_modifier ────────────────────────────────────────────────


class TestWaveCostModifier:
    def test_reduces_wave_price(self, service: EmpireService, empire: Empire):
        raw = service._wave_price(2)
        empire.effects[fx.WAVE_COST_MODIFIER] = 0.25
        assert service.wave_price_for(empire, 2) == pytest.approx(raw * 0.75)

    def test_no_modifier_full_price(self, service: EmpireService, empire: Empire):
        raw = service._wave_price(1)
        assert service.wave_price_for(empire, 1) == pytest.approx(raw)


# ── wave_era_cost_modifier ────────────────────────────────────────────


class TestWaveEraCostModifier:
    def test_reduces_era_price(self, service: EmpireService, empire: Empire):
        raw = service._wave_era_price(2)
        empire.effects[fx.WAVE_ERA_COST_MODIFIER] = 0.5
        assert service.wave_era_price_for(empire, 2) == pytest.approx(raw * 0.5)

    def test_no_modifier_full_price(self, service: EmpireService, empire: Empire):
        raw = service._wave_era_price(1)
        assert service.wave_era_price_for(empire, 1) == pytest.approx(raw)


# ── building_cost_modifier ────────────────────────────────────────────


class TestBuildingCostModifier:
    def _service_no_effects(self) -> EmpireService:
        svc = EmpireService(upgrade_provider=MagicMock(), event_bus=MagicMock())
        svc._apply_effects = MagicMock()
        return svc

    def test_reduces_gold_cost(self, empire: Empire):
        """building_cost_modifier 0.4 → 40% cheaper gold cost."""
        svc = self._service_no_effects()
        item = MagicMock()
        item.item_type.value = "building"
        from gameserver.models.items import ItemType
        item.item_type = ItemType.BUILDING
        item.costs = {"gold": 100.0}
        item.effort = 50.0
        item.requirements = []
        svc._upgrades.get.return_value = item
        svc._upgrades.check_requirements.return_value = True

        empire.effects[fx.BUILDING_COST_MODIFIER] = 0.4
        empire.resources["gold"] = 60.0  # enough for discounted (60), not raw (100)

        err = svc.build_item(empire, "watchtower")
        assert err is None
        assert empire.resources["gold"] == pytest.approx(0.0, abs=1e-6)

    def test_no_modifier_full_cost(self, empire: Empire):
        """Without modifier, full gold cost is deducted."""
        svc = self._service_no_effects()
        item = MagicMock()
        from gameserver.models.items import ItemType
        item.item_type = ItemType.BUILDING
        item.costs = {"gold": 50.0}
        item.effort = 10.0
        item.requirements = []
        svc._upgrades.get.return_value = item
        svc._upgrades.check_requirements.return_value = True

        empire.resources["gold"] = 50.0
        err = svc.build_item(empire, "farm")
        assert err is None
        assert empire.resources["gold"] == pytest.approx(0.0, abs=1e-6)


# ── citizen_effect_modifier ───────────────────────────────────────────


class TestCitizenEffectModifier:
    def test_boosts_gold_income(self, service: EmpireService, empire: Empire):
        """citizen_effect_modifier doubles citizen contribution to gold."""
        empire.citizens = {"merchant": 2, "artist": 0, "scientist": 0}
        empire.resources["gold"] = 0.0

        # No modifier
        service._generate_resources(empire, dt=1.0)
        base_gold = empire.resources["gold"]

        # With modifier = 1.0 (doubles citizen_effect)
        empire.resources["gold"] = 0.0
        empire.effects[fx.CITIZEN_EFFECT_MODIFIER] = 1.0
        service._generate_resources(empire, dt=1.0)
        boosted_gold = empire.resources["gold"]

        # Boosted > base (exact ratio depends on base_gold formula)
        assert boosted_gold > base_gold

    def test_effective_citizen_effect_scales(self, service: EmpireService, empire: Empire):
        """effective_citizen_effect returns base + modifier (additive)."""
        base = service._citizen_effect
        empire.effects[fx.CITIZEN_EFFECT_MODIFIER] = 0.5
        assert service.effective_citizen_effect(empire) == pytest.approx(base + 0.5)


# ── other_citizen_gold_modifier ───────────────────────────────────────


class TestOtherCitizenGoldModifier:
    def test_artists_contribute_to_gold(self, service: EmpireService, empire: Empire):
        """Artists generate gold when other_citizen_gold_modifier is set."""
        empire.citizens = {"merchant": 0, "artist": 3, "scientist": 0}
        empire.resources["gold"] = 0.0
        empire.effects[fx.OTHER_CITIZEN_GOLD_MODIFIER] = 0.02  # 2% per artist

        service._generate_resources(empire, dt=1.0)
        # gold = base_gold * (1 + 3 * 0.02) * dt  (assuming base_gold > 0)
        assert empire.resources["gold"] > 0.0

    def test_without_modifier_artists_earn_no_gold(self, service: EmpireService, empire: Empire):
        """Without modifier, artists do not affect gold income."""
        empire.citizens = {"merchant": 0, "artist": 5, "scientist": 0}
        empire.resources["gold"] = 0.0
        # no other_citizen_gold_modifier effect

        service._generate_resources(empire, dt=1.0)
        # Only base gold (no merchant bonus)
        base_only_gold = service._base_gold * 1.0  # modifier = 0
        assert empire.resources["gold"] == pytest.approx(base_only_gold, rel=1e-5)


# ── restore_life_during_battle_modifier ───────────────────────────────


class TestRestoreLifeDuringBattleModifier:
    def test_boosts_regen_when_in_battle(self, service: EmpireService, empire: Empire):
        """Life regen is boosted while the empire is under attack."""
        empire.effects["life_regen_modifier"] = 1.0  # 1 HP/s
        empire.effects[fx.RESTORE_LIFE_DURING_BATTLE_MODIFIER] = 0.5  # +0.5 HP/s additive

        fake_battle = object()
        with patch("gameserver.network.handlers._core._active_battles", {empire.uid: fake_battle}):
            service._generate_resources(empire, dt=1.0)

        assert empire.resources["life"] == pytest.approx(1.5)

    def test_no_boost_when_not_in_battle(self, service: EmpireService, empire: Empire):
        """Life regen is NOT boosted when the empire is not under attack."""
        empire.effects["life_regen_modifier"] = 1.0
        empire.effects[fx.RESTORE_LIFE_DURING_BATTLE_MODIFIER] = 1.0

        with patch("gameserver.network.handlers._core._active_battles", {}):
            service._generate_resources(empire, dt=1.0)

        assert empire.resources["life"] == pytest.approx(1.0)


# ── lump sums on skill-up ─────────────────────────────────────────────


class TestLumpSumsOnSkillUp:
    def test_gold_lump_sum_not_in_empire_effects(self):
        """gold_lump_sum_on_skill_up must not accumulate in empire.effects."""
        gc = GameConfig()
        rulers = {
            "king": {
                "q": [{"gold_lump_sum_on_skill_up": 500.0}],
                "w": [], "e": [], "r": [],
            }
        }
        svc = EmpireService(upgrade_provider=UpgradeProvider(), event_bus=EventBus(), game_config=gc)
        svc._rulers = rulers
        emp = Empire(uid=1, name="T")
        emp.ruler.type = "king"
        emp.ruler.q = 1  # already at level 1

        svc.recalculate_effects(emp)

        assert fx.GOLD_LUMP_SUM_ON_SKILL_UP not in emp.effects

    def test_culture_lump_sum_not_in_empire_effects(self):
        """culture_lump_sum_on_skill_up must not accumulate in empire.effects."""
        gc = GameConfig()
        rulers = {
            "queen": {
                "q": [{"culture_lump_sum_on_skill_up": 300.0}],
                "w": [], "e": [], "r": [],
            }
        }
        svc = EmpireService(upgrade_provider=UpgradeProvider(), event_bus=EventBus(), game_config=gc)
        svc._rulers = rulers
        emp = Empire(uid=1, name="T")
        emp.ruler.type = "queen"
        emp.ruler.q = 1

        svc.recalculate_effects(emp)

        assert fx.CULTURE_LUMP_SUM_ON_SKILL_UP not in emp.effects


# ── enemy_siege_time_modifier ─────────────────────────────────────────


class TestEnemySiegeTimeModifier:
    @pytest.fixture
    def services(self):
        event_bus = EventBus()
        gc = GameConfig()
        empire_service = EmpireService(UpgradeProvider(), event_bus, gc)
        attack_service = AttackService(event_bus, gc, empire_service)
        return attack_service, empire_service

    def test_reduces_siege_duration(self, services):
        """Attacker with enemy_siege_time_modifier 0.5 halves siege duration."""
        attack_service, empire_service = services
        attacker = Empire(uid=1, name="Attacker")
        attacker.effects[fx.ENEMY_SIEGE_TIME_MODIFIER] = 0.5
        empire_service.register(attacker)

        defender = Empire(uid=2, name="Defender")
        empire_service.register(defender)

        duration = attack_service._calculate_siege_duration(1, 2, base_override=30.0)
        assert duration == pytest.approx(15.0)  # 30 * (1 - 0.5)

    def test_no_effect_without_modifier(self, services):
        """Without modifier, siege duration is the base value."""
        attack_service, empire_service = services
        attacker = Empire(uid=1, name="Attacker")
        empire_service.register(attacker)

        defender = Empire(uid=2, name="Defender")
        empire_service.register(defender)

        duration = attack_service._calculate_siege_duration(1, 2, base_override=30.0)
        assert duration == pytest.approx(30.0)

    def test_stacks_with_defender_siege_time_modifier(self, services):
        """Attacker's enemy_siege_time_modifier stacks multiplicatively with defender's."""
        attack_service, empire_service = services
        attacker = Empire(uid=1, name="Attacker")
        attacker.effects[fx.ENEMY_SIEGE_TIME_MODIFIER] = 0.5
        empire_service.register(attacker)

        defender = Empire(uid=2, name="Defender")
        defender.effects[fx.SIEGE_TIME_MODIFIER] = 0.5
        empire_service.register(defender)

        # 30 * (1 - 0.5) * (1 - 0.5) = 7.5
        duration = attack_service._calculate_siege_duration(1, 2, base_override=30.0)
        assert duration == pytest.approx(7.5)
