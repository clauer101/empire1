"""Unit tests — one test class per effect category from util/effects.py.

Checks that each effect constant is actually applied by the backend.
Tests marked @pytest.mark.xfail document categories that are defined as
constants but NOT yet wired up in the engine.

Effect categories (from util/effects.py):
  1. Resource modifiers       — gold, culture, life, max_life
  2. Building & Research      — build_speed, research_speed
  3. Structure / Tower        — slow, burn (→ test_combat_effects.py), splash
  4. Critter / Army           — speed_modifier, health_modifier, armour_modifier  [NOT IMPLEMENTED]
  5. Travel & Siege           — travel_offset, siege_offset (→ test_attack_time_modifiers.py)
  6. Battle / Defense         — wave_delay_offset (→ test_wave_delay_offset.py)
  7. Loot                     — capture_gold, capture_culture (handlers.py)
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from gameserver.engine.battle_service import BattleService
from gameserver.engine.empire_service import EmpireService
from gameserver.models.battle import BattleState
from gameserver.models.critter import Critter
from gameserver.models.empire import Empire
from gameserver.models.hex import HexCoord
from gameserver.models.shot import Shot
from gameserver.models.structure import Structure
from gameserver.util import effects as fx


# ── Fixtures ───────────────────────────────────────────────────────────────────

def _svc() -> EmpireService:
    """Minimal EmpireService with mocked dependencies (base speeds = 1.0)."""
    return EmpireService(upgrade_provider=MagicMock(), event_bus=MagicMock())


def _empire(**kwargs) -> Empire:
    return Empire(uid=1, name="Test", **kwargs)


def _path(n: int = 5) -> list[HexCoord]:
    """Straight horizontal path of n tiles."""
    return [HexCoord(i, 0) for i in range(n)]


def _critter(cid: int = 1, health: float = 100.0, speed: float = 2.0,
             armour: float = 0.0, progress: float = 0.0) -> Critter:
    return Critter(
        cid=cid, iid="test",
        health=health, max_health=health,
        speed=speed, armour=armour,
        path=_path(), path_progress=progress,
    )


def _battle(*critters: Critter, structures: dict | None = None,
            pending_shots: list | None = None) -> BattleState:
    return BattleState(
        bid=1, defender=None, 
        critters={c.cid: c for c in critters},
        structures=structures or {},
        pending_shots=pending_shots or [],
    )


# ══════════════════════════════════════════════════════════════════════════════
# 1. RESOURCE MODIFIERS
# ══════════════════════════════════════════════════════════════════════════════

class TestGoldModifier:
    """GOLD_MODIFIER multiplies the effective gold income rate."""

    def test_gold_modifier_increases_income(self):
        svc = _svc()
        e = _empire()
        e.effects[fx.GOLD_MODIFIER] = 0.5  # +50%

        svc._generate_resources(e, dt=1.0)

        # base=1.0, offset=0 → (1.0 + 0) * (1 + 0.5) * 1s = 1.5
        assert e.resources["gold"] == pytest.approx(1.5)

    def test_gold_modifier_zero_gives_base_income(self):
        svc = _svc()
        e = _empire()
        e.effects[fx.GOLD_MODIFIER] = 0.0

        svc._generate_resources(e, dt=1.0)

        assert e.resources["gold"] == pytest.approx(1.0)


class TestGoldOffset:
    """GOLD_OFFSET shifts the base gold amount before the modifier is applied."""

    def test_gold_offset_adds_to_base(self):
        svc = _svc()
        e = _empire()
        e.effects[fx.GOLD_OFFSET] = 0.5  # base becomes 1.5

        svc._generate_resources(e, dt=1.0)

        # (1.0 + 0.5) * (1 + 0) * 1s = 1.5
        assert e.resources["gold"] == pytest.approx(1.5)

    def test_gold_offset_and_modifier_interact_multiplicatively(self):
        svc = _svc()
        e = _empire()
        e.effects[fx.GOLD_OFFSET] = 1.0     # base → 2.0
        e.effects[fx.GOLD_MODIFIER] = 0.5   # × 1.5

        svc._generate_resources(e, dt=1.0)

        assert e.resources["gold"] == pytest.approx(3.0)  # (1+1)*(1+0.5)


class TestCultureModifier:
    """CULTURE_MODIFIER multiplies the effective culture income rate."""

    def test_culture_modifier_increases_income(self):
        svc = _svc()
        e = _empire()
        e.effects[fx.CULTURE_MODIFIER] = 1.0  # +100%

        svc._generate_resources(e, dt=1.0)

        # base_culture=0.5 → 0.5 * (1+1) = 1.0
        assert e.resources["culture"] == pytest.approx(1.0)


class TestCultureOffset:
    """CULTURE_OFFSET shifts the base culture amount before the modifier."""

    def test_culture_offset_adds_to_base(self):
        svc = _svc()
        e = _empire()
        e.effects[fx.CULTURE_OFFSET] = 0.5   # base → 1.0

        svc._generate_resources(e, dt=1.0)

        # (0.5 + 0.5) * 1.0 * 1s = 1.0
        assert e.resources["culture"] == pytest.approx(1.0)


class TestLifeOffset:
    """LIFE_OFFSET regenerates life each tick, capped at max_life."""

    def test_life_offset_regenerates_life(self):
        svc = _svc()
        e = _empire()
        e.resources["life"] = 5.0
        e.max_life = 10.0
        e.effects[fx.LIFE_OFFSET] = 2.0   # +2 HP/s

        svc._generate_resources(e, dt=1.0)

        assert e.resources["life"] == pytest.approx(7.0)

    def test_life_offset_capped_at_max_life(self):
        svc = _svc()
        e = _empire()
        e.resources["life"] = 9.5
        e.max_life = 10.0
        e.effects[fx.LIFE_OFFSET] = 5.0   # would exceed max

        svc._generate_resources(e, dt=1.0)

        assert e.resources["life"] == pytest.approx(10.0)

    def test_negative_life_offset_does_not_regen(self):
        """life_offset ≤ 0 must not change life (no drain via this path)."""
        svc = _svc()
        e = _empire()
        e.resources["life"] = 5.0
        e.max_life = 10.0
        e.effects[fx.LIFE_OFFSET] = -1.0

        svc._generate_resources(e, dt=1.0)

        assert e.resources["life"] == pytest.approx(5.0)


class TestMaxLifeModifier:
    """MAX_LIFE_MODIFIER raises the empire's maximum life pool."""

    def test_max_life_modifier_increases_max_life(self):
        svc = _svc()
        e = _empire()
        e.effects[fx.MAX_LIFE_MODIFIER] = 5.0

        svc._recalculate_max_life(e)

        # starting_max_life default = 10
        assert e.max_life == pytest.approx(15.0)

    def test_no_max_life_modifier_keeps_default(self):
        svc = _svc()
        e = _empire()

        svc._recalculate_max_life(e)

        assert e.max_life == pytest.approx(10.0)


class TestLifeModifier:
    """LIFE_MODIFIER scales the life regeneration rate (multiplicative on life_offset)."""

    def test_life_modifier_should_scale_life_regen(self):
        svc = _svc()
        e = _empire()
        e.resources["life"] = 5.0
        e.max_life = 20.0
        e.effects[fx.LIFE_OFFSET] = 1.0   # base regen 1 HP/s
        e.effects[fx.LIFE_MODIFIER] = 1.0  # ×2 → 2 HP/s

        svc._generate_resources(e, dt=1.0)

        assert e.resources["life"] == pytest.approx(7.0)  # 5 + 2


# ══════════════════════════════════════════════════════════════════════════════
# 2. BUILDING & RESEARCH SPEED
# ══════════════════════════════════════════════════════════════════════════════

class TestBuildSpeedModifier:
    """BUILD_SPEED_MODIFIER multiplies construction speed."""

    def test_modifier_doubles_build_speed(self):
        svc = _svc()
        e = _empire()
        e.buildings["FORT"] = 10.0
        e.build_queue = "FORT"
        e.effects[fx.BUILD_SPEED_MODIFIER] = 1.0  # +100% → speed = base * 2

        # base_build_speed = 1.0, modifier +1.0 → effective speed = 2.0/s
        svc._progress_buildings(e, dt=1.0)

        assert e.buildings["FORT"] == pytest.approx(8.0)

    def test_no_modifier_uses_base_speed(self):
        svc = _svc()
        e = _empire()
        e.buildings["FORT"] = 10.0
        e.build_queue = "FORT"

        svc._progress_buildings(e, dt=1.0)

        assert e.buildings["FORT"] == pytest.approx(9.0)


class TestBuildSpeedOffset:
    """BUILD_SPEED_OFFSET is added to the base speed before the modifier."""

    def test_offset_adds_to_base_speed(self):
        svc = _svc()
        e = _empire()
        e.buildings["FORT"] = 10.0
        e.build_queue = "FORT"
        e.effects[fx.BUILD_SPEED_OFFSET] = 1.0  # base 1+1=2, modifier=0 → 2/s

        svc._progress_buildings(e, dt=1.0)

        assert e.buildings["FORT"] == pytest.approx(8.0)


class TestResearchSpeedModifier:
    """RESEARCH_SPEED_MODIFIER multiplies research speed."""

    def test_modifier_doubles_research_speed(self):
        svc = _svc()
        e = _empire()
        e.knowledge["FIRE"] = 10.0
        e.research_queue = "FIRE"
        e.effects[fx.RESEARCH_SPEED_MODIFIER] = 1.0  # +100%

        svc._progress_knowledge(e, dt=1.0)

        assert e.knowledge["FIRE"] == pytest.approx(8.0)

    def test_no_modifier_uses_base_speed(self):
        svc = _svc()
        e = _empire()
        e.knowledge["FIRE"] = 10.0
        e.research_queue = "FIRE"

        svc._progress_knowledge(e, dt=1.0)

        assert e.knowledge["FIRE"] == pytest.approx(9.0)


class TestResearchSpeedOffset:
    """RESEARCH_SPEED_OFFSET is added to the base research speed."""

    def test_offset_adds_to_base_research_speed(self):
        svc = _svc()
        e = _empire()
        e.knowledge["FIRE"] = 10.0
        e.research_queue = "FIRE"
        e.effects[fx.RESEARCH_SPEED_OFFSET] = 1.0  # base 1+1=2/s

        svc._progress_knowledge(e, dt=1.0)

        assert e.knowledge["FIRE"] == pytest.approx(8.0)


# ══════════════════════════════════════════════════════════════════════════════
# 3. STRUCTURE / TOWER — Splash damage
#    (slow / burn are covered in test_combat_effects.py)
# ══════════════════════════════════════════════════════════════════════════════

class TestSplashRadius:
    """SPLASH_RADIUS causes a shot to damage nearby critters on impact."""

    def _make_shot(self, target_cid: int, splash_radius: float,
                   damage: float = 10.0) -> Shot:
        return Shot(
            damage=damage, target_cid=target_cid, source_sid=1,
            effects={"splash_radius": splash_radius},
            flight_remaining_ms=1.0, origin=HexCoord(0, 0),
        )

    def test_splash_hits_nearby_critter(self):
        """Critter within splash_radius is damaged on impact.

        Path has 5 tiles (max_idx=4):
          progress=0.0   → float_idx=0.0  → pos (0, 0)   (primary target)
          progress=0.125 → float_idx=0.5  → pos (0.5, 0) → distance ≈ 0.5  ≤ 0.6 → HIT
        """
        svc = BattleService()
        c_target = _critter(cid=1, progress=0.0)
        c_nearby = _critter(cid=2, progress=0.125)   # pos (0.5, 0), dist=0.5
        shot = self._make_shot(target_cid=1, splash_radius=0.6)

        b = _battle(c_target, c_nearby, pending_shots=[shot])
        svc._step_shots(b, 10.0)

        assert c_target.health < 100.0, "Primary target should be damaged"
        assert c_nearby.health < 100.0, "Nearby critter within splash_radius must also be damaged"

    def test_splash_does_not_hit_far_critter(self):
        """Critter beyond splash_radius is NOT damaged.

          progress=0.0  → pos (0, 0)   (primary target)
          progress=0.25 → float_idx=1.0 → pos (1, 0) → distance = 1.0 > 0.6 → NO HIT
        """
        svc = BattleService()
        c_target = _critter(cid=1, progress=0.0)
        c_far = _critter(cid=2, progress=0.25)       # pos (1, 0), dist=1.0
        shot = self._make_shot(target_cid=1, splash_radius=0.6)

        b = _battle(c_target, c_far, pending_shots=[shot])
        svc._step_shots(b, 10.0)

        assert c_far.health == pytest.approx(100.0), "Critter outside splash_radius must NOT be damaged"

    def test_no_splash_radius_means_no_aoe(self):
        """Shot without splash_radius only damages the direct target."""
        svc = BattleService()
        c_target = _critter(cid=1, progress=0.0)
        c_other = _critter(cid=2, progress=0.25)
        shot = Shot(
            damage=20.0, target_cid=1, source_sid=1,
            effects={},   # no splash_radius
            flight_remaining_ms=1.0, origin=HexCoord(0, 0),
        )

        b = _battle(c_target, c_other, pending_shots=[shot])
        svc._step_shots(b, 10.0)

        assert c_other.health == pytest.approx(100.0)


# ══════════════════════════════════════════════════════════════════════════════
# 3b. ARMOUR — direct shot damage reduction (critter stat, not empire effect)
# ══════════════════════════════════════════════════════════════════════════════

class TestArmourDamageReduction:
    """Critter armour reduces incoming shot damage; minimum damage is 0.5."""

    def test_armour_reduces_damage(self):
        svc = BattleService()
        c = _critter(armour=5.0)
        shot = Shot(
            damage=10.0, target_cid=c.cid, source_sid=1,
            effects={}, flight_remaining_ms=1.0, origin=HexCoord(0, 0),
        )
        b = _battle(c, pending_shots=[shot])
        svc._step_shots(b, 10.0)

        # 10 - 5 = 5 actual damage
        assert c.health == pytest.approx(95.0)

    def test_armour_clamps_minimum_damage_to_half(self):
        """Even with high armour, a shot with damage > 0 deals at least 0.5."""
        svc = BattleService()
        c = _critter(armour=100.0)
        shot = Shot(
            damage=10.0, target_cid=c.cid, source_sid=1,
            effects={}, flight_remaining_ms=1.0, origin=HexCoord(0, 0),
        )
        b = _battle(c, pending_shots=[shot])
        svc._step_shots(b, 10.0)

        assert c.health == pytest.approx(99.5)  # 100 - 0.5

    def test_zero_base_damage_shot_deals_no_damage(self):
        """A shot with damage=0 (e.g. pure-effect tower) deals 0, not 0.5."""
        svc = BattleService()
        c = _critter()
        shot = Shot(
            damage=0.0, target_cid=c.cid, source_sid=1,
            effects={}, flight_remaining_ms=1.0, origin=HexCoord(0, 0),
        )
        b = _battle(c, pending_shots=[shot])
        svc._step_shots(b, 10.0)

        assert c.health == pytest.approx(100.0)


# ══════════════════════════════════════════════════════════════════════════════
# 4. CRITTER / ARMY MODIFIERS  ← NOT IMPLEMENTED
# ══════════════════════════════════════════════════════════════════════════════

class TestCritterArmyModifiers:
    """item_upgrades (per-IID, per-stat) scale spawned critters via _make_critter_from_item."""

    def _svc(self, health=5.0, speed=0.5, armour=0.5, extra_items=None):
        from unittest.mock import MagicMock
        from gameserver.loaders.game_config_loader import GameConfig, CritterUpgradeDef
        gc = MagicMock(spec=GameConfig)
        gc.critter_upgrades = CritterUpgradeDef(health=health, speed=speed, armour=armour)
        gc.structure_upgrades = None
        return BattleService(items=extra_items or [], gc=gc)

    def test_speed_modifier_increases_critter_speed(self):
        """item_upgrades speed upgrade increases critter speed."""
        svc = self._svc(speed=0.5)
        base    = svc._make_critter_from_item("soldier", path=_path())
        boosted = svc._make_critter_from_item("soldier", path=_path(),
                                               attacker_item_upgrades={"soldier": {"speed": 1}})
        assert boosted.speed > base.speed

    def test_health_modifier_increases_critter_health(self):
        """item_upgrades health=100 upgrade doubles critter health."""
        svc = self._svc(health=100.0)
        base    = svc._make_critter_from_item("soldier", path=_path())
        boosted = svc._make_critter_from_item("soldier", path=_path(),
                                               attacker_item_upgrades={"soldier": {"health": 1}})
        assert boosted.health == pytest.approx(base.health * 2.0)
        assert boosted.max_health == pytest.approx(base.max_health * 2.0)

    def test_armour_modifier_increases_critter_armour(self):
        """item_upgrades armour upgrade scales critter armour by %."""
        from gameserver.models.items import ItemDetails, ItemType
        item = ItemDetails(iid="heavy", item_type=ItemType.CRITTER,
                           armour=10.0, health=50.0, speed=1.0)
        svc = self._svc(armour=100.0, extra_items=[item])  # +100% per level
        base    = svc._make_critter_from_item("heavy", path=_path())
        boosted = svc._make_critter_from_item("heavy", path=_path(),
                                               attacker_item_upgrades={"heavy": {"armour": 1}})
        assert base.armour == pytest.approx(10.0)
        assert boosted.armour == pytest.approx(20.0)  # 10 × 2

    def test_no_effects_leaves_stats_unchanged(self):
        """Empty item_upgrades dict must not change critter stats."""
        svc = self._svc()
        base = svc._make_critter_from_item("soldier", path=_path())
        same = svc._make_critter_from_item("soldier", path=_path(),
                                            attacker_item_upgrades={})
        assert same.speed  == pytest.approx(base.speed)
        assert same.health == pytest.approx(base.health)
        assert same.armour == pytest.approx(base.armour)


# ══════════════════════════════════════════════════════════════════════════════
# 3c. TOWER EMPIRE MODIFIERS
# ══════════════════════════════════════════════════════════════════════════════

class TestTowerEmpireModifiers:
    """item_upgrades (per-IID, per-stat) scale tower behaviour in BattleService._step_towers."""

    def _gc_with_structure_upgrades(self, damage=5.0, range_=0.1, reload=5.0):
        from unittest.mock import MagicMock
        from gameserver.loaders.game_config_loader import GameConfig, StructureUpgradeDef
        gc = MagicMock(spec=GameConfig)
        gc.structure_upgrades = StructureUpgradeDef(damage=damage, range=range_, reload=reload)
        gc.critter_upgrades = None
        return gc

    def _basic_structure(self, damage: float = 10.0, rng: float = 5.0,
                         reload_ms: float = 2000.0) -> Structure:
        return Structure(
            sid=1, iid="BASIC_TOWER",
            position=HexCoord(0, 0),
            damage=damage, range=rng, reload_time_ms=reload_ms,
            shot_speed=10.0, effects={}, reload_remaining_ms=0.0,
        )

    def test_damage_modifier_increases_tower_damage(self):
        """item_upgrades damage upgrade → tower deals more damage."""
        gc = self._gc_with_structure_upgrades(damage=50.0)  # +50% per level
        svc = BattleService(gc=gc)
        c = _critter(health=100.0, speed=0.01)
        c.path_progress = 0.1
        struct = self._basic_structure(damage=10.0)
        defender = _empire(item_upgrades={"BASIC_TOWER": {"damage": 1}})
        b = BattleState(bid=1, defender=defender, 
                        critters={c.cid: c}, structures={struct.sid: struct})

        svc._step_towers(b, 50.0)
        svc._step_shots(b, 5000.0)

        assert c.health == pytest.approx(85.0)  # 100 - 15 (+50% of 10)

    def test_range_modifier_extends_tower_range(self):
        """item_upgrades range upgrade so tower reaches critter otherwise out of range.

        Path: 5 tiles; progress=0.1 → float_idx=0.4 → pos ≈ (0.4, 0)
        hex_world_distance((0,0), (0.4,0)) ≈ 0.4.
        base range = 0.3 → too short. with +100% upgrade → 0.6 → reaches critter.
        """
        gc = self._gc_with_structure_upgrades(range_=100.0)  # +100% per level → doubles range
        svc = BattleService(gc=gc)
        c = _critter(speed=0.01)
        c.path_progress = 0.1
        struct = self._basic_structure(rng=0.3)

        # Without upgrade: no shot
        b_no = BattleState(bid=1, defender=_empire(), 
                           critters={c.cid: c}, structures={struct.sid: struct})
        svc._step_towers(b_no, 50.0)
        assert len(b_no.pending_shots) == 0, "Tower must not fire without upgrade"

        # With range upgrade level 1 → effective range = 0.6 → fires
        c2 = _critter(cid=2, speed=0.01)
        c2.path_progress = 0.1
        struct2 = self._basic_structure(rng=0.3)
        defender = _empire(item_upgrades={"BASIC_TOWER": {"range": 1}})
        b_mod = BattleState(bid=2, defender=defender, 
                            critters={c2.cid: c2}, structures={struct2.sid: struct2})
        svc._step_towers(b_mod, 50.0)
        assert len(b_mod.pending_shots) == 1, "Tower should fire with range upgrade"

    def test_reload_modifier_speeds_up_cooldown(self):
        """item_upgrades reload upgrade → tower fires faster.

        Without upgrade: 500ms remaining - 300ms tick = 200 > 0 → no shot.
        With reload upgrade +100%: effective decrement = 600 → 500 - 600 ≤ 0 → fires.
        """
        gc = self._gc_with_structure_upgrades(reload=100.0)  # +100% per level
        svc = BattleService(gc=gc)
        c = _critter(speed=0.01)
        c.path_progress = 0.1

        # No upgrade → no shot
        struct1 = self._basic_structure(reload_ms=2000.0)
        struct1.reload_remaining_ms = 500.0
        b_no = BattleState(bid=1, defender=_empire(), 
                           critters={c.cid: c}, structures={struct1.sid: struct1})
        svc._step_towers(b_no, 300.0)
        assert len(b_no.pending_shots) == 0, "Tower must not fire without upgrade"

        # With reload upgrade level 1 → fires
        c2 = _critter(cid=2, speed=0.01)
        c2.path_progress = 0.1
        struct2 = self._basic_structure(reload_ms=2000.0)
        struct2.reload_remaining_ms = 500.0
        defender = _empire(item_upgrades={"BASIC_TOWER": {"reload": 1}})
        b_mod = BattleState(bid=2, defender=defender, 
                            critters={c2.cid: c2}, structures={struct2.sid: struct2})
        svc._step_towers(b_mod, 300.0)
        assert len(b_mod.pending_shots) == 1, "Tower should fire with reload upgrade"
