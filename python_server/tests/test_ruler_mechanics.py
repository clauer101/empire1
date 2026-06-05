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
    "damage_min": 1.0,
    "damage_max": 30.0,
    "value_min": 10,
    "value_max": 1000,
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

    def test_mid_level_interpolates_quadratically(self):
        mid = (RULER_MAX_LEVEL + 1) // 2  # level 9 for max_level=18
        stats = ruler_critter_stats(MAJA_CFG, level=mid)
        t = ((mid - 1) / (RULER_MAX_LEVEL - 1)) ** 2
        expected_health = 20.0 + (2000.0 - 20.0) * t
        assert stats["health"] == pytest.approx(expected_health)

    def test_value_scales_with_level(self):
        stats_l1 = ruler_critter_stats(MAJA_CFG, level=1)
        stats_l18 = ruler_critter_stats(MAJA_CFG, level=RULER_MAX_LEVEL)
        assert stats_l1["value"] == pytest.approx(10.0)
        assert stats_l18["value"] == pytest.approx(1000.0)

    def test_scale_grows_with_level(self):
        stats_l1 = ruler_critter_stats(MAJA_CFG, level=1)
        stats_l18 = ruler_critter_stats(MAJA_CFG, level=RULER_MAX_LEVEL)
        assert stats_l18["scale"] > stats_l1["scale"]

    def test_animation_path_preserved(self):
        stats = ruler_critter_stats(MAJA_CFG, level=1)
        assert stats["animation"] == "assets/sprites/ruler/maja"


# ── 2. Combat attributes scale with ruler level ───────────────────────────────

_COMBAT_ATTRS = [
    ("health",  "health_min",  "health_max"),
    ("speed",   "speed_min",   "speed_max"),
    ("armour",  "armour_min",  "armour_max"),
    ("damage",  "damage_min",  "damage_max"),
]

ALL_RULER_CFGS = {
    "MAJA": MAJA_CFG,
    "BORIN": {
        "speed_min": 0.6, "speed_max": 1.0,
        "health_min": 18.0, "health_max": 2800.0,
        "armour_min": 1.0, "armour_max": 17.0,
        "damage_min": 1.0, "damage_max": 30.0,
        "value_min": 10, "value_max": 1200,
        "animation": "assets/sprites/ruler/borin",
        "scale_base": 1.0, "q": [], "w": [], "e": [], "r": [],
    },
    "NANDI": {
        "speed_min": 0.8, "speed_max": 1.2,
        "health_min": 18.0, "health_max": 2100.0,
        "armour_min": 0.0, "armour_max": 13.0,
        "damage_min": 1.0, "damage_max": 30.0,
        "value_min": 10, "value_max": 1000,
        "animation": "assets/sprites/ruler/nandi",
        "scale_base": 1.0, "q": [], "w": [], "e": [], "r": [],
    },
    "LUCIEN": {
        "speed_min": 0.6, "speed_max": 1.1,
        "health_min": 18.0, "health_max": 2200.0,
        "armour_min": 0.0, "armour_max": 15.0,
        "damage_min": 1.0, "damage_max": 30.0,
        "value_min": 10, "value_max": 1200,
        "animation": "assets/sprites/ruler/lucien",
        "scale_base": 1.0, "q": [], "w": [], "e": [], "r": [],
    },
    "ALRIC": {
        "speed_min": 0.5, "speed_max": 1.0,
        "health_min": 22.0, "health_max": 3000.0,
        "armour_min": 1.0, "armour_max": 19.0,
        "damage_min": 1.0, "damage_max": 30.0,
        "value_min": 10, "value_max": 1200,
        "animation": "assets/sprites/ruler/alric",
        "scale_base": 1.0, "q": [], "w": [], "e": [], "r": [],
    },
}


class TestRulerCombatScaling:
    """Validate all four combat attributes scale correctly with ruler level."""

    @pytest.mark.parametrize("attr,key_min,key_max", _COMBAT_ATTRS)
    def test_level1_equals_min(self, attr, key_min, key_max):
        stats = ruler_critter_stats(MAJA_CFG, level=1)
        assert stats[attr] == pytest.approx(MAJA_CFG[key_min])

    @pytest.mark.parametrize("attr,key_min,key_max", _COMBAT_ATTRS)
    def test_max_level_equals_max(self, attr, key_min, key_max):
        stats = ruler_critter_stats(MAJA_CFG, level=RULER_MAX_LEVEL)
        assert stats[attr] == pytest.approx(MAJA_CFG[key_max])

    @pytest.mark.parametrize("attr,key_min,key_max", _COMBAT_ATTRS)
    def test_monotonically_increasing(self, attr, key_min, key_max):
        """Each successive level must have a higher or equal attribute value."""
        prev = ruler_critter_stats(MAJA_CFG, level=1)[attr]
        for lvl in range(2, RULER_MAX_LEVEL + 1):
            cur = ruler_critter_stats(MAJA_CFG, level=lvl)[attr]
            assert cur >= prev, f"{attr} decreased from level {lvl-1} to {lvl}"
            prev = cur

    @pytest.mark.parametrize("attr,key_min,key_max", _COMBAT_ATTRS)
    def test_quadratic_interpolation_at_midpoint(self, attr, key_min, key_max):
        mid = (RULER_MAX_LEVEL + 1) // 2
        t = ((mid - 1) / (RULER_MAX_LEVEL - 1)) ** 2
        expected = MAJA_CFG[key_min] + (MAJA_CFG[key_max] - MAJA_CFG[key_min]) * t
        stats = ruler_critter_stats(MAJA_CFG, level=mid)
        assert stats[attr] == pytest.approx(expected)

    @pytest.mark.parametrize("attr,key_min,key_max", _COMBAT_ATTRS)
    def test_max_strictly_greater_than_min(self, attr, key_min, key_max):
        """Max-level stats must exceed level-1 stats (assuming _max > _min in config)."""
        s1 = ruler_critter_stats(MAJA_CFG, level=1)
        s_max = ruler_critter_stats(MAJA_CFG, level=RULER_MAX_LEVEL)
        if MAJA_CFG[key_max] > MAJA_CFG[key_min]:
            assert s_max[attr] > s1[attr]

    @pytest.mark.parametrize("ruler_id,cfg", list(ALL_RULER_CFGS.items()))
    @pytest.mark.parametrize("attr,key_min,key_max", _COMBAT_ATTRS)
    def test_all_rulers_level1_eq_min(self, ruler_id, cfg, attr, key_min, key_max):
        stats = ruler_critter_stats(cfg, level=1)
        assert stats[attr] == pytest.approx(cfg[key_min]), \
            f"{ruler_id}: {attr} at level 1 should equal {key_min}"

    @pytest.mark.parametrize("ruler_id,cfg", list(ALL_RULER_CFGS.items()))
    @pytest.mark.parametrize("attr,key_min,key_max", _COMBAT_ATTRS)
    def test_all_rulers_max_level_eq_max(self, ruler_id, cfg, attr, key_min, key_max):
        stats = ruler_critter_stats(cfg, level=RULER_MAX_LEVEL)
        assert stats[attr] == pytest.approx(cfg[key_max]), \
            f"{ruler_id}: {attr} at max level should equal {key_max}"

    def test_level_zero_clamped_to_level1(self):
        """Levels below 1 must be treated as level 1 (t clamped to 0)."""
        stats_0 = ruler_critter_stats(MAJA_CFG, level=0)
        stats_1 = ruler_critter_stats(MAJA_CFG, level=1)
        for attr, _, _ in _COMBAT_ATTRS:
            assert stats_0[attr] == pytest.approx(stats_1[attr])

    def test_level_above_max_clamped(self):
        """Levels above RULER_MAX_LEVEL must not exceed max values."""
        stats_over = ruler_critter_stats(MAJA_CFG, level=RULER_MAX_LEVEL + 5)
        stats_max = ruler_critter_stats(MAJA_CFG, level=RULER_MAX_LEVEL)
        for attr, _, _ in _COMBAT_ATTRS:
            assert stats_over[attr] == pytest.approx(stats_max[attr])


# ── 4. Ruler XP awarded for kills and victory ─────────────────────────────────


class TestRulerXpAward:
    def _make_battle(self, critters_killed=3, critters_reached=1, kills_era_xp_sum=None):
        from gameserver.models.army import CritterWave
        battle = MagicMock()
        ruler_wave = CritterWave(wave_id=0, iid="MAJA", slots=1.0)
        army = MagicMock(uid=1, waves=[ruler_wave])
        battle.armies = {1: army}
        battle.defender = 99
        battle.critters_killed = critters_killed
        battle.critters_reached = critters_reached
        # kills_era_xp_sum defaults to critters_killed (era_idx=1 per critter)
        battle.kills_era_xp_sum = kills_era_xp_sum if kills_era_xp_sum is not None else float(critters_killed)
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
        emp_svc._ERA_ORDER = ["stone", "middle_ages", "renaissance"]
        emp_svc.get_current_era.return_value = "stone"
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


# ── 5. Ruler gets no XP when not in combat (zero critters, no victory) ────────


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
        emp_svc._ERA_ORDER = ["stone"]
        emp_svc.get_current_era.return_value = "stone"
        svc.empire_service = emp_svc

        _award_ruler_xp(battle, svc, attacker_won=False)
        assert empire.ruler.xp == pytest.approx(0.0)


# ── 6. AI attacker gets no XP (ruler XP skipped for AI_UID) ──────────────────


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


# ── 7. Skill level thresholds ─────────────────────────────────────────────────


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


# ── 8. Ruler effects recalculated/restored correctly ─────────────────────────


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


# ── 9. Ruler level derived from XP correctly ─────────────────────────────────


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
