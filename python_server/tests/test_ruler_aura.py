"""Unit tests for the ruler aura system."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from gameserver.engine.empire_service import ruler_critter_stats, RULER_MAX_LEVEL
from gameserver.engine.battle_service import BattleService
from gameserver.models.critter import Critter
from gameserver.models.structure import Structure
from gameserver.models.hex import HexCoord
from gameserver.models.battle import BattleState
from gameserver.models.empire import Empire


# ── Config fixtures ──────────────────────────────────────────────────────────

RULER_CFG = {
    "speed_min": 0.5,
    "speed_max": 1.0,
    "health_min": 100.0,
    "health_max": 1000.0,
    "armour_min": 1.0,
    "armour_max": 10.0,
    "damage_min": 1.0,
    "damage_max": 20.0,
    "value_min": 10.0,
    "value_max": 500.0,
    "animation": "assets/sprites/ruler/maja",
    "scale_base": 1.0,
    "aura_min": 2.0,
    "aura_max": 6.0,
    "aura_effects": {
        "increase_armour_modifier": 0.25,
        "increase_critter_speed": 0.10,
        "slow_tower_modifier": 0.20,
        "reduce_tower_damage": 0.15,
    },
}

# Simple 3-hex path for testing
PATH = [HexCoord(0, 0), HexCoord(1, 0), HexCoord(2, 0)]


def _ruler_critter(aura_radius: float = 3.0, path_progress: float = 0.0) -> Critter:
    c = Critter(
        cid=1, iid="ruler_maja",
        path=PATH, path_progress=path_progress,
        health=500.0, max_health=500.0, speed=0.7, armour=5.0,
        is_ruler=True, aura_radius=aura_radius,
        aura_effects=dict(RULER_CFG["aura_effects"]),
    )
    return c


def _plain_critter(cid: int, path_progress: float = 0.0) -> Critter:
    return Critter(
        cid=cid, iid="SLAVE",
        path=PATH, path_progress=path_progress,
        health=50.0, max_health=50.0, speed=0.5, armour=2.0,
    )


def _structure(sid: int, q: int, r: int) -> Structure:
    return Structure(
        sid=sid, iid="TOWER", position=HexCoord(q, r),
        damage=10.0, range=3.0, reload_time_ms=2000.0, shot_speed=2.0,
    )


def _make_battle(ruler: Critter, extra_critters: list[Critter] = (), structures: list[Structure] = ()) -> BattleState:
    defender = Empire(uid=1, name="Defender")
    battle = BattleState(
        bid=1,
        defender=defender,
        attacker_uids=[2],
        attacker_gains={2: {}},
    )
    battle.critters[ruler.cid] = ruler
    for c in extra_critters:
        battle.critters[c.cid] = c
    for s in structures:
        battle.structures[s.sid] = s
    return battle


def _make_svc() -> BattleService:
    gc = MagicMock()
    gc.structure_upgrades = None
    return BattleService(gc=gc)


# ── ruler_critter_stats: aura_radius scales with level ───────────────────────

class TestRulerCritterStatsAura:
    def test_level1_uses_aura_min(self):
        stats = ruler_critter_stats(RULER_CFG, level=1)
        assert stats["aura_radius"] == pytest.approx(RULER_CFG["aura_min"])

    def test_max_level_uses_aura_max(self):
        stats = ruler_critter_stats(RULER_CFG, level=RULER_MAX_LEVEL)
        assert stats["aura_radius"] == pytest.approx(RULER_CFG["aura_max"])

    def test_mid_level_between_min_and_max(self):
        stats = ruler_critter_stats(RULER_CFG, level=9)
        assert RULER_CFG["aura_min"] <= stats["aura_radius"] <= RULER_CFG["aura_max"]

    def test_aura_effects_propagated(self):
        given = {"increase_armour_modifier": 0.25}
        stats = ruler_critter_stats(RULER_CFG, level=1, aura_effects=given)
        assert stats["aura_effects"] == given

    def test_no_aura_config_returns_zero(self):
        cfg = {k: v for k, v in RULER_CFG.items() if not k.startswith("aura")}
        stats = ruler_critter_stats(cfg, level=1)
        assert stats["aura_radius"] == 0.0
        assert stats["aura_effects"] == {}


# ── _apply_ruler_auras: critter buffs ────────────────────────────────────────

class TestApplyRulerAurasCritters:
    def test_critter_in_range_gets_in_aura(self):
        ruler = _ruler_critter(aura_radius=3.0, path_progress=0.5)
        ally = _plain_critter(cid=2, path_progress=0.5)  # same position
        battle = _make_battle(ruler, extra_critters=[ally])
        svc = _make_svc()

        svc._apply_ruler_auras(battle)

        assert ally.in_aura is True

    def test_critter_outside_range_untouched(self):
        ruler = _ruler_critter(aura_radius=0.5, path_progress=0.0)
        ally = _plain_critter(cid=2, path_progress=1.0)  # far end of path
        battle = _make_battle(ruler, extra_critters=[ally])
        svc = _make_svc()

        svc._apply_ruler_auras(battle)

        assert ally.in_aura is False
        assert ally.aura_armour_modifier == 0.0

    def test_armour_modifier_applied(self):
        ruler = _ruler_critter(aura_radius=3.0, path_progress=0.5)
        ally = _plain_critter(cid=2, path_progress=0.5)
        battle = _make_battle(ruler, extra_critters=[ally])
        svc = _make_svc()

        svc._apply_ruler_auras(battle)

        assert ally.aura_armour_modifier == pytest.approx(0.25)

    def test_speed_modifier_applied(self):
        ruler = _ruler_critter(aura_radius=3.0, path_progress=0.5)
        ally = _plain_critter(cid=2, path_progress=0.5)
        battle = _make_battle(ruler, extra_critters=[ally])
        svc = _make_svc()

        svc._apply_ruler_auras(battle)

        assert ally.aura_speed_modifier == pytest.approx(0.10)

    def test_ruler_does_not_buff_itself(self):
        ruler = _ruler_critter(aura_radius=3.0, path_progress=0.5)
        battle = _make_battle(ruler)
        svc = _make_svc()

        svc._apply_ruler_auras(battle)

        assert ruler.in_aura is False
        assert ruler.aura_speed_modifier == 0.0

    def test_reset_clears_previous_tick_state(self):
        # Use a very small radius so moving apart puts ally out of range
        ruler = _ruler_critter(aura_radius=0.3, path_progress=0.5)
        ally = _plain_critter(cid=2, path_progress=0.5)
        battle = _make_battle(ruler, extra_critters=[ally])
        svc = _make_svc()

        svc._apply_ruler_auras(battle)
        assert ally.in_aura is True

        # Move ruler to start, ally to far end — distance > 0.3 radius
        ruler.path_progress = 0.0
        ally.path_progress = 1.0
        svc._apply_ruler_auras(battle)

        assert ally.in_aura is False
        assert ally.aura_speed_modifier == 0.0

    def test_dead_ruler_has_no_aura(self):
        ruler = _ruler_critter(aura_radius=3.0, path_progress=0.5)
        ruler.health = 0.0
        ally = _plain_critter(cid=2, path_progress=0.5)
        battle = _make_battle(ruler, extra_critters=[ally])
        svc = _make_svc()

        svc._apply_ruler_auras(battle)

        assert ally.in_aura is False


# ── _apply_ruler_auras: tower debuffs ────────────────────────────────────────

class TestApplyRulerAurasTowers:
    def test_tower_in_range_debuffed(self):
        ruler = _ruler_critter(aura_radius=3.0, path_progress=0.0)  # at hex (0,0)
        tower = _structure(sid=1, q=1, r=0)  # nearby
        battle = _make_battle(ruler, structures=[tower])
        svc = _make_svc()

        svc._apply_ruler_auras(battle)

        assert tower.aura_damage_modifier == pytest.approx(0.15)
        assert tower.aura_reload_modifier == pytest.approx(0.20)

    def test_tower_outside_range_untouched(self):
        ruler = _ruler_critter(aura_radius=0.5, path_progress=0.0)
        tower = _structure(sid=1, q=5, r=0)  # far away
        battle = _make_battle(ruler, structures=[tower])
        svc = _make_svc()

        svc._apply_ruler_auras(battle)

        assert tower.aura_damage_modifier == 0.0
        assert tower.aura_reload_modifier == 0.0


# ── Aura modifier applied in damage calculation ───────────────────────────────

class TestAuraDamageReduction:
    def _shoot(self, armour: float, aura_armour_mod: float, shot_damage: float = 10.0) -> float:
        """Apply a shot to a critter with the given armour + aura modifier and return damage dealt."""
        from gameserver.models.battle import Shot
        gc = MagicMock()
        gc.structure_upgrades = None
        svc = BattleService(gc=gc)

        critter = Critter(
            cid=1, iid="SLAVE", path=PATH, path_progress=0.5,
            health=100.0, max_health=100.0, speed=0.5, armour=armour,
            aura_armour_modifier=aura_armour_mod,
        )
        defender = Empire(uid=1, name="D")
        battle = BattleState(bid=1, defender=defender, attacker_uids=[2], attacker_gains={2: {}})
        battle.critters[critter.cid] = critter

        shot = Shot(
            damage=shot_damage, target_cid=1, source_sid=1,
            effects={}, flight_remaining_ms=0.0,
            origin=HexCoord(0, 0), path_progress=1.0,
        )
        svc._apply_shot_damage(battle, shot)
        return 100.0 - critter.health

    def test_aura_armour_reduces_damage(self):
        base_damage = self._shoot(armour=2.0, aura_armour_mod=0.0)
        aura_damage = self._shoot(armour=2.0, aura_armour_mod=0.25)
        assert aura_damage < base_damage

    def test_zero_aura_modifier_unchanged(self):
        assert self._shoot(armour=2.0, aura_armour_mod=0.0) == pytest.approx(8.0)
