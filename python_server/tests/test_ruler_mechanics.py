"""Unit tests for ruler mechanics: critter stats, XP, constraints, effects, skill thresholds."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from gameserver.engine.empire_service import EmpireService, ruler_critter_stats, RULER_MAX_LEVEL
from gameserver.models.empire import Empire, Ruler


# ── Fixtures ──────────────────────────────────────────────────────────────────

MAJA_CFG = {
    "speed_min": 0.2,
    "speed_max": 1.1,
    "health_min": 20.0,
    "health_max": 2000.0,
    "armour_min": 1.0,
    "armour_max": 19.0,
    "value_base": 1000,
    "base_damage": 1,
    "animation": "assets/sprites/ruler/maja",
    "scale_base": 1.0,
    "q": [{"research_speed_offset": 0.1}, {"research_speed_offset": 0.2},
          {"research_speed_offset": 0.4}, {"research_speed_offset": 0.8},
          {"research_speed_offset": 1.6}],
    "w": [],
    "e": [],
    "r": [],
}


@pytest.fixture
def service() -> EmpireService:
    rulers = {"MAJA": MAJA_CFG}
    return EmpireService(upgrade_provider=MagicMock(), event_bus=MagicMock(), rulers=rulers)


@pytest.fixture
def empire() -> Empire:
    emp = Empire(uid=1, name="Test")
    emp.ruler = Ruler(type="MAJA", name="Maja", xp=0.0)
    return emp


# ── 1. Ruler critter stats scale correctly with level ─────────────────────────


class TestRulerCritterStats:
    def test_level_1_uses_min_values(self):
        stats = ruler_critter_stats(MAJA_CFG, level=1)
        assert stats["health"] == pytest.approx(20.0)
        assert stats["speed"] == pytest.approx(0.2)
        assert stats["armour"] == pytest.approx(1.0)

    def test_max_level_uses_max_values(self):
        stats = ruler_critter_stats(MAJA_CFG, level=RULER_MAX_LEVEL)
        assert stats["health"] == pytest.approx(2000.0)
        assert stats["speed"] == pytest.approx(1.1)
        assert stats["armour"] == pytest.approx(19.0)

    def test_mid_level_interpolates_linearly(self):
        mid = (RULER_MAX_LEVEL + 1) // 2  # level 9 for max_level=18
        stats = ruler_critter_stats(MAJA_CFG, level=mid)
        # t = (9-1)/(18-1) ≈ 0.471
        t = (mid - 1) / (RULER_MAX_LEVEL - 1)
        expected_health = 20.0 + (2000.0 - 20.0) * t
        assert stats["health"] == pytest.approx(expected_health)

    def test_value_scales_with_level(self):
        stats = ruler_critter_stats(MAJA_CFG, level=5)
        assert stats["value"] == pytest.approx(1000 * 5)

    def test_scale_grows_with_level(self):
        stats_l1 = ruler_critter_stats(MAJA_CFG, level=1)
        stats_l18 = ruler_critter_stats(MAJA_CFG, level=RULER_MAX_LEVEL)
        assert stats_l18["scale"] > stats_l1["scale"]

    def test_animation_path_preserved(self):
        stats = ruler_critter_stats(MAJA_CFG, level=1)
        assert stats["animation"] == "assets/sprites/ruler/maja"


# ── 2. Ruler XP awarded for kills and victory ─────────────────────────────────


class TestRulerXpAward:
    def _make_battle(self, critters_killed=3, critters_reached=1):
        battle = MagicMock()
        battle.armies = {1: MagicMock(uid=1)}
        battle.defender = 99
        battle.critters_killed = critters_killed
        battle.critters_reached = critters_reached
        return battle

    def _make_svc(self, empire):
        svc = MagicMock()
        svc.game_config = MagicMock(
            ruler_xp_per_kill=1.0,
            ruler_xp_per_reached_per_era=10.0,
            ruler_xp_victory_per_era=50.0,
        )
        emp_svc = MagicMock()
        emp_svc.get.return_value = empire
        emp_svc._ERA_ORDER = ["STEINZEIT", "MITTELALTER", "RENAISSANCE"]
        emp_svc.get_current_era.return_value = "STEINZEIT"
        svc.empire_service = emp_svc
        return svc

    def test_xp_awarded_on_kills(self, empire):
        from gameserver.network.handlers.battle_task import _award_ruler_xp
        battle = self._make_battle(critters_killed=5, critters_reached=0)
        svc = self._make_svc(empire)
        _award_ruler_xp(battle, svc, attacker_won=False)
        # 5 kills × 1.0 xp_per_kill = 5 XP
        assert empire.ruler.xp == pytest.approx(5.0)

    def test_xp_awarded_on_victory(self, empire):
        from gameserver.network.handlers.battle_task import _award_ruler_xp
        battle = self._make_battle(critters_killed=0, critters_reached=0)
        svc = self._make_svc(empire)
        _award_ruler_xp(battle, svc, attacker_won=True)
        # era_idx = 1, victory = 50 × 1 = 50
        assert empire.ruler.xp == pytest.approx(50.0)

    def test_xp_accumulates_across_battles(self, empire):
        from gameserver.network.handlers.battle_task import _award_ruler_xp
        battle = self._make_battle(critters_killed=2, critters_reached=0)
        svc = self._make_svc(empire)
        _award_ruler_xp(battle, svc, attacker_won=False)
        _award_ruler_xp(battle, svc, attacker_won=False)
        assert empire.ruler.xp == pytest.approx(4.0)


# ── 3. Ruler gets no XP when not in combat (zero critters, no victory) ────────


class TestRulerNoXpWhenIdle:
    def test_no_xp_for_zero_outcome(self, empire):
        from gameserver.network.handlers.battle_task import _award_ruler_xp
        battle = MagicMock()
        battle.armies = {1: MagicMock(uid=1)}
        battle.defender = 99
        battle.critters_killed = 0
        battle.critters_reached = 0
        svc = MagicMock()
        svc.game_config = MagicMock(
            ruler_xp_per_kill=1.0,
            ruler_xp_per_reached_per_era=10.0,
            ruler_xp_victory_per_era=50.0,
        )
        emp_svc = MagicMock()
        emp_svc.get.return_value = empire
        emp_svc._ERA_ORDER = ["STEINZEIT"]
        emp_svc.get_current_era.return_value = "STEINZEIT"
        svc.empire_service = emp_svc

        _award_ruler_xp(battle, svc, attacker_won=False)
        assert empire.ruler.xp == pytest.approx(0.0)


# ── 4. AI attacker gets no XP (ruler XP skipped for AI_UID) ──────────────────


class TestRulerNoXpForAI:
    def test_ai_uid_is_skipped(self):
        from gameserver.network.handlers.battle_task import _award_ruler_xp
        from gameserver.engine.ai_service import AI_UID

        battle = MagicMock()
        battle.armies = {AI_UID: MagicMock(uid=AI_UID)}
        battle.critters_killed = 10
        battle.critters_reached = 5
        battle.defender = 99

        svc = MagicMock()
        svc.empire_service.get.return_value = None  # should never be called for AI

        _award_ruler_xp(battle, svc, attacker_won=True)
        # empire_service.get should never be called with AI_UID
        svc.empire_service.get.assert_not_called()


# ── 5. Skill level thresholds ─────────────────────────────────────────────────


class TestSkillLevelThresholds:
    """Tests for skill-up validation logic in /api/empire/ruler/skill-up."""

    def _skill_up_result(self, empire, skill, level_override=None):
        """Simulate the skill-up validation logic from routers/empire.py."""
        from gameserver.engine.empire_service import EmpireService
        svc = EmpireService(upgrade_provider=MagicMock(), event_bus=MagicMock(), rulers={"MAJA": MAJA_CFG})
        ruler_level = level_override if level_override is not None else svc.ruler_level_from_xp(empire.ruler.xp)
        ruler = empire.ruler
        total_points = ruler.q + ruler.w + ruler.e + ruler.r
        if total_points >= ruler_level:
            return {"success": False, "error": "No skill points available"}
        current = getattr(ruler, skill)
        if skill in ("q", "w", "e"):
            if current >= 5:
                return {"success": False, "error": "max"}
            if current + 1 == 5 and ruler_level < 9:
                return {"success": False, "error": "level 9 required"}
        else:
            unlock_levels = [6, 11, 16]
            if current >= len(unlock_levels):
                return {"success": False, "error": "max"}
            if ruler_level < unlock_levels[current]:
                return {"success": False, "error": f"level {unlock_levels[current]} required"}
        setattr(ruler, skill, current + 1)
        svc.recalculate_effects(empire)
        return {"success": True}

    def test_q_level_5_requires_ruler_level_9(self):
        emp = Empire(uid=1, name="T")
        emp.ruler = Ruler(type="MAJA", name="Maja", q=4, w=0, e=0, r=0)
        # ruler_level=8, total_points=4 < 8, but q+1=5 needs ruler_level>=9
        result = self._skill_up_result(emp, "q", level_override=8)
        assert result["success"] is False
        assert "9" in result["error"]

    def test_q_level_5_allowed_at_ruler_level_9(self):
        emp = Empire(uid=1, name="T")
        emp.ruler = Ruler(type="MAJA", name="Maja", q=4, w=0, e=0, r=0)
        result = self._skill_up_result(emp, "q", level_override=9)
        assert result["success"] is True
        assert emp.ruler.q == 5

    def test_r_skill_first_unlock_at_level_6(self):
        emp = Empire(uid=1, name="T")
        emp.ruler = Ruler(type="MAJA", name="Maja", q=4, w=0, e=0, r=0)
        result = self._skill_up_result(emp, "r", level_override=5)
        assert result["success"] is False
        assert "6" in result["error"]

    def test_r_skill_first_unlock_succeeds_at_level_6(self):
        emp = Empire(uid=1, name="T")
        emp.ruler = Ruler(type="MAJA", name="Maja", q=4, w=1, e=0, r=0)
        result = self._skill_up_result(emp, "r", level_override=6)
        assert result["success"] is True
        assert emp.ruler.r == 1

    def test_r_skill_second_unlock_at_level_11(self):
        emp = Empire(uid=1, name="T")
        # total_points=6 < ruler_level=10, r=1 → trying r level 2 needs ruler_level 11
        emp.ruler = Ruler(type="MAJA", name="Maja", q=3, w=2, e=0, r=1)
        result = self._skill_up_result(emp, "r", level_override=10)
        assert result["success"] is False
        assert "11" in result["error"]

    def test_r_skill_third_unlock_at_level_16(self):
        emp = Empire(uid=1, name="T")
        emp.ruler = Ruler(type="MAJA", name="Maja", q=5, w=5, e=2, r=2)
        result = self._skill_up_result(emp, "r", level_override=15)
        assert result["success"] is False
        assert "16" in result["error"]

    def test_no_points_when_all_spent(self):
        emp = Empire(uid=1, name="T")
        emp.ruler = Ruler(type="MAJA", name="Maja", q=3, w=0, e=0, r=0)
        # ruler_level=3 == total_points=3 → no points left
        result = self._skill_up_result(emp, "w", level_override=3)
        assert result["success"] is False
        assert "points" in result["error"]


# ── 6. Ruler effects recalculated/restored correctly ─────────────────────────


class TestRulerEffectsRestored:
    def test_ruler_effects_applied_in_recalculate(self, service, empire):
        empire.ruler.q = 1  # research_speed_offset: 0.1
        service.recalculate_effects(empire)
        assert empire.effects.get("research_speed_offset", 0.0) == pytest.approx(0.1)

    def test_ruler_effects_cleared_when_type_removed(self, service, empire):
        empire.ruler.q = 1
        service.recalculate_effects(empire)
        # Remove ruler
        empire.ruler.type = ""
        service.recalculate_effects(empire)
        assert empire.effects.get("research_speed_offset", 0.0) == pytest.approx(0.0)

    def test_higher_skill_level_gives_higher_effect(self, service, empire):
        empire.ruler.q = 2
        service.recalculate_effects(empire)
        effect_l2 = empire.effects.get("research_speed_offset", 0.0)

        empire.ruler.q = 4
        service.recalculate_effects(empire)
        effect_l4 = empire.effects.get("research_speed_offset", 0.0)

        assert effect_l4 > effect_l2

    def test_recalculate_is_idempotent(self, service, empire):
        empire.ruler.q = 3
        service.recalculate_effects(empire)
        val1 = empire.effects.get("research_speed_offset", 0.0)
        service.recalculate_effects(empire)
        val2 = empire.effects.get("research_speed_offset", 0.0)
        assert val1 == pytest.approx(val2)

    def test_get_ruler_effects_returns_dict(self, service, empire):
        empire.ruler.q = 2
        effects = service.get_ruler_effects(empire)
        assert "research_speed_offset" in effects
        assert effects["research_speed_offset"] == pytest.approx(0.2)

    def test_get_ruler_effects_empty_for_no_ruler(self, service):
        emp = Empire(uid=2, name="No ruler")
        assert service.get_ruler_effects(emp) == {}


# ── 7. Ruler level derived from XP correctly ─────────────────────────────────


class TestRulerLevelFromXp:
    def test_zero_xp_is_level_1(self, service):
        assert service.ruler_level_from_xp(0.0) == 1

    def test_sufficient_xp_reaches_level_2(self, service):
        xp_for_2 = service.ruler_xp_for_level(2)
        assert service.ruler_level_from_xp(xp_for_2) == 2

    def test_max_level_capped(self, service):
        assert service.ruler_level_from_xp(1e12) == RULER_MAX_LEVEL

    def test_xp_just_below_next_level_stays(self, service):
        xp_for_3 = service.ruler_xp_for_level(2) + service.ruler_xp_for_level(3)
        level = service.ruler_level_from_xp(xp_for_3 - 0.01)
        assert level == 2
