"""Tests: item_upgrades are correctly applied during battle.

Covers all 8 upgrade modifiers:
  Tower  (structure): damage, range, reload, effect_duration, effect_value
  Critter           : health, speed, armour
"""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from gameserver.engine.battle_service import BattleService
from gameserver.loaders.game_config_loader import (
    GameConfig, StructureUpgradeDef, CritterUpgradeDef,
)
from gameserver.models.battle import BattleState
from gameserver.models.critter import Critter
from gameserver.models.empire import Empire
from gameserver.models.hex import HexCoord
from gameserver.models.items import ItemDetails, ItemType
from gameserver.models.structure import Structure


# ── Helpers ───────────────────────────────────────────────────────────────────

IID_TOWER   = "T"
IID_CRITTER = "C"

BASE_DAMAGE    = 10.0
BASE_RANGE     = 5.0
BASE_RELOAD_MS = 2000.0
BASE_HEALTH    = 50.0
BASE_SPEED     = 1.0
BASE_ARMOUR    = 5.0


def _path(n: int = 5) -> list[HexCoord]:
    return [HexCoord(i, 0) for i in range(n)]


def _empire(**kw) -> Empire:
    return Empire(uid=1, name="Test", **kw)


def _gc(su: StructureUpgradeDef | None = None,
        cu: CritterUpgradeDef  | None = None) -> GameConfig:
    gc = MagicMock(spec=GameConfig)
    gc.structure_upgrades = su or StructureUpgradeDef()
    gc.critter_upgrades   = cu or CritterUpgradeDef()
    return gc


def _tower_structure(sid: int = 1, damage: float = BASE_DAMAGE,
                     rng: float = BASE_RANGE,
                     reload_ms: float = BASE_RELOAD_MS,
                     effects: dict | None = None) -> Structure:
    return Structure(
        sid=sid, iid=IID_TOWER,
        position=HexCoord(0, 0),
        damage=damage, range=rng,
        reload_time_ms=reload_ms,
        shot_speed=10.0,
        effects=effects or {},
        reload_remaining_ms=0.0,
    )


def _critter_item(health: float = BASE_HEALTH,
                  speed: float = BASE_SPEED,
                  armour: float = BASE_ARMOUR) -> ItemDetails:
    return ItemDetails(
        iid=IID_CRITTER, item_type=ItemType.CRITTER,
        health=health, speed=speed, armour=armour,
    )


def _svc(su: StructureUpgradeDef | None = None,
         cu: CritterUpgradeDef  | None = None,
         critter_item: ItemDetails | None = None) -> BattleService:
    items = [critter_item] if critter_item else []
    return BattleService(items=items, gc=_gc(su, cu))


def _fire_and_land(svc: BattleService, battle: BattleState,
                   dt_tower: float = 50.0, dt_shot: float = 9999.0) -> None:
    """Step towers (fire), then advance shots until they land."""
    svc._step_towers(battle, dt_tower)
    svc._step_shots(battle, dt_shot)


def _critter_in_range(health: float = 200.0, progress: float = 0.1) -> Critter:
    c = Critter(
        cid=1, iid="target",
        health=health, max_health=health,
        speed=0.01, armour=0.0,
        path=_path(), path_progress=progress,
    )
    return c


# ══════════════════════════════════════════════════════════════════════════════
# Tower upgrades (structure)
# ══════════════════════════════════════════════════════════════════════════════

class TestTowerDamageUpgrade:
    """damage upgrade → shot deals base × (1 + pct/100 × level) damage."""

    def _setup(self, dmg_pct: float, level: int):
        su = StructureUpgradeDef(damage=dmg_pct)
        svc = _svc(su=su)
        defender = _empire(item_upgrades={IID_TOWER: {"damage": level}})
        c = _critter_in_range(health=200.0)
        struct = _tower_structure(damage=BASE_DAMAGE)
        b = BattleState(bid=1, defender=defender, 
                        critters={c.cid: c}, structures={struct.sid: struct})
        _fire_and_land(svc, b)
        return c

    def test_level1_damage_applied(self):
        """Level 1 damage upgrade at 50% per level → 10 × 1.5 = 15 damage dealt."""
        c = self._setup(dmg_pct=50.0, level=1)
        assert c.health == pytest.approx(200.0 - BASE_DAMAGE * 1.5)

    def test_level2_damage_applied(self):
        """Level 2 damage upgrade at 50% per level → 10 × 2.0 = 20 damage dealt."""
        c = self._setup(dmg_pct=50.0, level=2)
        assert c.health == pytest.approx(200.0 - BASE_DAMAGE * 2.0)

    def test_level0_no_change(self):
        """Level 0 → no bonus, base damage only."""
        c = self._setup(dmg_pct=50.0, level=0)
        assert c.health == pytest.approx(200.0 - BASE_DAMAGE)

    def test_different_iid_not_affected(self):
        """Upgrade on IID_TOWER must not affect a tower with a different IID."""
        su = StructureUpgradeDef(damage=100.0)
        svc = _svc(su=su)
        defender = _empire(item_upgrades={IID_TOWER: {"damage": 1}})
        c = _critter_in_range(health=200.0)
        other_struct = Structure(
            sid=2, iid="OTHER",
            position=HexCoord(0, 0),
            damage=BASE_DAMAGE, range=BASE_RANGE,
            reload_time_ms=BASE_RELOAD_MS,
            shot_speed=10.0, effects={}, reload_remaining_ms=0.0,
        )
        b = BattleState(bid=1, defender=defender, 
                        critters={c.cid: c}, structures={other_struct.sid: other_struct})
        _fire_and_land(svc, b)
        assert c.health == pytest.approx(200.0 - BASE_DAMAGE)


class TestTowerRangeUpgrade:
    """range upgrade → tower fires at critters that would otherwise be out of range."""

    def _build(self, rng_pct: float, level: int,
               base_range: float, critter_progress: float):
        su = StructureUpgradeDef(range=rng_pct)
        svc = _svc(su=su)
        defender = _empire(item_upgrades={IID_TOWER: {"range": level}})
        c = Critter(cid=1, iid="t", health=100.0, max_health=100.0,
                    speed=0.01, armour=0.0,
                    path=_path(), path_progress=critter_progress)
        struct = _tower_structure(rng=base_range)
        b = BattleState(bid=1, defender=defender, 
                        critters={c.cid: c}, structures={struct.sid: struct})
        svc._step_towers(b, 50.0)
        return b

    def test_upgrade_extends_range(self):
        """Base range 0.3 × (1 + 100%/100 × 1) = 0.6 → fires at critter ~0.4 away."""
        b = self._build(rng_pct=100.0, level=1,
                        base_range=0.3, critter_progress=0.1)
        assert len(b.pending_shots) == 1

    def test_no_upgrade_too_short(self):
        """Without upgrade, range stays at 0.3 and critter ~0.4 away is out of range."""
        su = StructureUpgradeDef(range=100.0)
        svc = _svc(su=su)
        defender = _empire()   # no item_upgrades
        c = Critter(cid=1, iid="t", health=100.0, max_health=100.0,
                    speed=0.01, armour=0.0,
                    path=_path(), path_progress=0.1)
        struct = _tower_structure(rng=0.3)
        b = BattleState(bid=1, defender=defender, 
                        critters={c.cid: c}, structures={struct.sid: struct})
        svc._step_towers(b, 50.0)
        assert len(b.pending_shots) == 0

    def test_level2_doubles_bonus(self):
        """Level 2 × 100% → range × 3 → even farther critter is reached."""
        b = self._build(rng_pct=100.0, level=2,
                        base_range=0.3, critter_progress=0.2)
        assert len(b.pending_shots) == 1


class TestTowerReloadUpgrade:
    """reload upgrade → reload timer decrements faster per tick."""

    def _setup(self, reload_pct: float, level: int,
               remaining_ms: float, tick_ms: float):
        su = StructureUpgradeDef(reload=reload_pct)
        svc = _svc(su=su)
        defender = _empire(item_upgrades={IID_TOWER: {"reload": level}})
        c = _critter_in_range()
        struct = _tower_structure()
        struct.reload_remaining_ms = remaining_ms
        b = BattleState(bid=1, defender=defender, 
                        critters={c.cid: c}, structures={struct.sid: struct})
        svc._step_towers(b, tick_ms)
        return b

    def test_upgrade_fires_where_base_would_not(self):
        """reload +100% per level, level 1: 500ms remaining - 300ms × 2 = fires."""
        b = self._setup(reload_pct=100.0, level=1,
                        remaining_ms=500.0, tick_ms=300.0)
        assert len(b.pending_shots) == 1

    def test_no_upgrade_does_not_fire(self):
        """Without upgrade, 500ms - 300ms = 200ms left → no shot."""
        su = StructureUpgradeDef(reload=100.0)
        svc = _svc(su=su)
        defender = _empire()
        c = _critter_in_range()
        struct = _tower_structure()
        struct.reload_remaining_ms = 500.0
        b = BattleState(bid=1, defender=defender, 
                        critters={c.cid: c}, structures={struct.sid: struct})
        svc._step_towers(b, 300.0)
        assert len(b.pending_shots) == 0

    def test_level2_reloads_even_faster(self):
        """reload +100% level 2: mult = 3 → 200ms remaining, tick 70ms × 3 = 210 → fires."""
        b = self._setup(reload_pct=100.0, level=2,
                        remaining_ms=200.0, tick_ms=70.0)
        assert len(b.pending_shots) == 1


class TestTowerEffectDurationUpgrade:
    """effect_duration upgrade → slow_duration / burn_duration on shot scaled by %."""

    def _shoot(self, efdur_pct: float, level: int, base_effects: dict) -> dict:
        su = StructureUpgradeDef(effect_duration=efdur_pct)
        svc = _svc(su=su)
        defender = _empire(item_upgrades={IID_TOWER: {"effect_duration": level}})
        c = _critter_in_range()
        struct = _tower_structure(effects=base_effects)
        b = BattleState(bid=1, defender=defender, 
                        critters={c.cid: c}, structures={struct.sid: struct})
        svc._step_towers(b, 50.0)
        assert b.pending_shots, "Tower must have fired"
        return b.pending_shots[0].effects

    def test_slow_duration_pct(self):
        """Level 1, +100% per level → slow_duration × 2."""
        efx = self._shoot(100.0, 1, {"slow_duration": 1000.0, "slow_ratio": 0.3})
        assert efx["slow_duration"] == pytest.approx(2000.0)

    def test_burn_duration_pct(self):
        """Level 2, +50% per level → burn_duration × 2."""
        efx = self._shoot(50.0, 2, {"burn_duration": 2000.0, "burn_dps": 5.0})
        assert efx["burn_duration"] == pytest.approx(4000.0)

    def test_level0_no_change(self):
        """Level 0 → duration unchanged."""
        efx = self._shoot(100.0, 0, {"slow_duration": 1000.0, "slow_ratio": 0.3})
        assert efx["slow_duration"] == pytest.approx(1000.0)

    def test_no_effect_key_unaffected(self):
        """slow_ratio is not changed by effect_duration upgrade."""
        efx = self._shoot(100.0, 2, {"slow_duration": 1000.0, "slow_ratio": 0.3})
        assert efx["slow_ratio"] == pytest.approx(0.3)


class TestTowerEffectValueUpgrade:
    """effect_value upgrade → slow_ratio / burn_dps on shot are scaled up."""

    def _shoot(self, efval_pct: float, level: int, base_effects: dict) -> dict:
        su = StructureUpgradeDef(effect_value=efval_pct)
        svc = _svc(su=su)
        defender = _empire(item_upgrades={IID_TOWER: {"effect_value": level}})
        c = _critter_in_range()
        struct = _tower_structure(effects=base_effects)
        b = BattleState(bid=1, defender=defender, 
                        critters={c.cid: c}, structures={struct.sid: struct})
        svc._step_towers(b, 50.0)
        assert b.pending_shots, "Tower must have fired"
        return b.pending_shots[0].effects

    def test_slow_ratio_scaled(self):
        """Level 1 at +100% → slow_ratio × 2."""
        efx = self._shoot(100.0, 1, {"slow_duration": 1000.0, "slow_ratio": 0.3})
        assert efx["slow_ratio"] == pytest.approx(0.6)

    def test_burn_dps_scaled(self):
        """Level 2 at +50% → burn_dps × 2."""
        efx = self._shoot(50.0, 2, {"burn_duration": 2000.0, "burn_dps": 10.0})
        assert efx["burn_dps"] == pytest.approx(20.0)

    def test_level0_no_change(self):
        """Level 0 → value unchanged."""
        efx = self._shoot(100.0, 0, {"slow_duration": 1000.0, "slow_ratio": 0.3})
        assert efx["slow_ratio"] == pytest.approx(0.3)

    def test_duration_key_unaffected(self):
        """slow_duration is not changed by effect_value upgrade."""
        efx = self._shoot(100.0, 2, {"slow_duration": 1000.0, "slow_ratio": 0.3})
        assert efx["slow_duration"] == pytest.approx(1000.0)


# ══════════════════════════════════════════════════════════════════════════════
# Critter upgrades
# ══════════════════════════════════════════════════════════════════════════════

class TestCritterHealthUpgrade:
    """health upgrade → critter spawned with base × (1 + pct/100 × level) HP."""

    def _spawn(self, health_pct: float, level: int,
               base_health: float = BASE_HEALTH) -> Critter:
        cu = CritterUpgradeDef(health=health_pct)
        svc = _svc(cu=cu, critter_item=_critter_item(health=base_health))
        upgrades = {IID_CRITTER: {"health": level}} if level > 0 else {}
        return svc._make_critter_from_item(IID_CRITTER, path=_path(),
                                           attacker_item_upgrades=upgrades)

    def test_level1(self):
        """Level 1 at +100% per level → health × 2."""
        c = self._spawn(health_pct=100.0, level=1)
        assert c.health     == pytest.approx(BASE_HEALTH * 2.0)
        assert c.max_health == pytest.approx(BASE_HEALTH * 2.0)

    def test_level2(self):
        """Level 2 at +50% per level → health × 2."""
        c = self._spawn(health_pct=50.0, level=2)
        assert c.health == pytest.approx(BASE_HEALTH * 2.0)

    def test_level0_unchanged(self):
        """Level 0 → base health."""
        c = self._spawn(health_pct=100.0, level=0)
        assert c.health == pytest.approx(BASE_HEALTH)

    def test_max_health_matches_health(self):
        """max_health must always equal health after upgrade."""
        c = self._spawn(health_pct=20.0, level=3)
        assert c.max_health == pytest.approx(c.health)

    def test_other_iid_not_upgraded(self):
        """Upgrade on IID_CRITTER must not affect a different IID."""
        cu = CritterUpgradeDef(health=100.0)
        svc = _svc(cu=cu, critter_item=_critter_item())
        c = svc._make_critter_from_item(IID_CRITTER, path=_path(),
                                        attacker_item_upgrades={"OTHER": {"health": 5}})
        assert c.health == pytest.approx(BASE_HEALTH)


class TestCritterSpeedUpgrade:
    """speed upgrade → critter spawned with base × (1 + pct/100 × level) speed."""

    def _spawn(self, speed_pct: float, level: int,
               base_speed: float = BASE_SPEED) -> Critter:
        cu = CritterUpgradeDef(speed=speed_pct)
        svc = _svc(cu=cu, critter_item=_critter_item(speed=base_speed))
        upgrades = {IID_CRITTER: {"speed": level}} if level > 0 else {}
        return svc._make_critter_from_item(IID_CRITTER, path=_path(),
                                           attacker_item_upgrades=upgrades)

    def test_level1(self):
        """Level 1 at +100% per level → speed × 2."""
        c = self._spawn(speed_pct=100.0, level=1)
        assert c.speed == pytest.approx(BASE_SPEED * 2.0)

    def test_level3(self):
        """Level 3 at +50% per level → speed × 2.5."""
        c = self._spawn(speed_pct=50.0, level=3)
        assert c.speed == pytest.approx(BASE_SPEED * 2.5)

    def test_level0_unchanged(self):
        c = self._spawn(speed_pct=100.0, level=0)
        assert c.speed == pytest.approx(BASE_SPEED)


class TestCritterArmourUpgrade:
    """armour upgrade → critter spawned with base × (1 + pct/100 × level) armour."""

    def _spawn(self, armour_pct: float, level: int,
               base_armour: float = BASE_ARMOUR) -> Critter:
        cu = CritterUpgradeDef(armour=armour_pct)
        svc = _svc(cu=cu, critter_item=_critter_item(armour=base_armour))
        upgrades = {IID_CRITTER: {"armour": level}} if level > 0 else {}
        return svc._make_critter_from_item(IID_CRITTER, path=_path(),
                                           attacker_item_upgrades=upgrades)

    def test_level1(self):
        """Level 1 at +100% per level → armour × 2."""
        c = self._spawn(armour_pct=100.0, level=1)
        assert c.armour == pytest.approx(BASE_ARMOUR * 2.0)

    def test_level2(self):
        """Level 2 at +50% per level → armour × 2."""
        c = self._spawn(armour_pct=50.0, level=2)
        assert c.armour == pytest.approx(BASE_ARMOUR * 2.0)

    def test_level0_unchanged(self):
        c = self._spawn(armour_pct=5.0, level=0)
        assert c.armour == pytest.approx(BASE_ARMOUR)


# ══════════════════════════════════════════════════════════════════════════════
# Cross-stat independence
# ══════════════════════════════════════════════════════════════════════════════

class TestUpgradeIsolation:
    """Upgrading one stat must not inadvertently change other stats."""

    def test_critter_damage_upgrade_only_affects_damage(self):
        """Only the damage stat changes; health/speed/armour must stay at base."""
        su = StructureUpgradeDef(damage=100.0, range=0.1, reload=100.0)
        svc = _svc(su=su)
        defender = _empire(item_upgrades={IID_TOWER: {"damage": 1}})
        c = _critter_in_range()
        s_base = _tower_structure()
        s_upg  = _tower_structure(sid=2)

        b_base = BattleState(bid=1, defender=_empire(), 
                             critters={c.cid: c}, structures={s_base.sid: s_base})
        c2 = _critter_in_range()
        b_upg  = BattleState(bid=2, defender=defender, 
                             critters={c2.cid: c2}, structures={s_upg.sid: s_upg})
        svc._step_towers(b_base, 50.0)
        svc._step_towers(b_upg,  50.0)

        # Both towers should fire exactly once
        assert len(b_base.pending_shots) == 1
        assert len(b_upg.pending_shots)  == 1
        # Range and reload are at the same level → same number of shots
        shot_base = b_base.pending_shots[0]
        shot_upg  = b_upg.pending_shots[0]
        # Damage differs; everything else (effects) stays equal
        assert shot_upg.damage > shot_base.damage
        assert shot_base.effects == shot_upg.effects  # no effect change from damage upgrade

    def test_critter_speed_upgrade_does_not_change_health_or_armour(self):
        cu = CritterUpgradeDef(health=100.0, speed=0.5, armour=10.0)
        svc = _svc(cu=cu, critter_item=_critter_item())
        c = svc._make_critter_from_item(IID_CRITTER, path=_path(),
                                        attacker_item_upgrades={IID_CRITTER: {"speed": 2}})
        assert c.health == pytest.approx(BASE_HEALTH)   # unchanged
        assert c.armour == pytest.approx(BASE_ARMOUR)   # unchanged
        assert c.speed  == pytest.approx(BASE_SPEED * (1 + 0.5 / 100 * 2))

    def test_critter_armour_upgrade_does_not_change_health_or_speed(self):
        cu = CritterUpgradeDef(health=100.0, speed=0.5, armour=10.0)
        svc = _svc(cu=cu, critter_item=_critter_item())
        c = svc._make_critter_from_item(IID_CRITTER, path=_path(),
                                        attacker_item_upgrades={IID_CRITTER: {"armour": 3}})
        assert c.health == pytest.approx(BASE_HEALTH)
        assert c.speed  == pytest.approx(BASE_SPEED)
        assert c.armour == pytest.approx(BASE_ARMOUR * (1 + 0.10 * 3))
