"""Tests for slow and burn combat effects.

Covers the full chain:
  structures.yaml effects → Shot.effects → Critter.slow_*/burn_* fields → movement tick
"""

import pytest
from gameserver.engine.battle_service import BattleService, _shot_visual_type, _VISUAL_SLOW, _VISUAL_BURN, _VISUAL_NORMAL
from gameserver.loaders.item_loader import load_items
from gameserver.models.battle import BattleState
from gameserver.models.critter import Critter
from gameserver.models.hex import HexCoord
from gameserver.models.shot import Shot
from gameserver.models.structure import Structure


# ── Helpers ──────────────────────────────────────────────────


def _long_path(n: int = 20) -> list[HexCoord]:
    return [HexCoord(i, 0) for i in range(n)]


def _critter(health: float = 100.0, speed: float = 2.0) -> Critter:
    return Critter(
        cid=1, iid="test", health=health, max_health=health,
        speed=speed, path=_long_path(), path_progress=0.0,
    )


def _battle(*critters: Critter, **kwargs) -> BattleState:
    return BattleState(
        bid=1, defender=None, attacker=None,
        critters={c.cid: c for c in critters},
        **kwargs,
    )


# ── _shot_visual_type helper ──────────────────────────────────


class TestShotVisualType:
    def test_burn_effects_return_burn(self):
        assert _shot_visual_type({"burn_dps": 2.0, "burn_duration": 3000.0}) == _VISUAL_BURN

    def test_burn_duration_alone_returns_burn(self):
        assert _shot_visual_type({"burn_duration": 3000.0}) == _VISUAL_BURN

    def test_slow_effects_return_slow(self):
        assert _shot_visual_type({"slow_duration": 2000.0, "slow_ratio": 0.5}) == _VISUAL_SLOW

    def test_slow_ratio_alone_returns_slow(self):
        assert _shot_visual_type({"slow_ratio": 0.5}) == _VISUAL_SLOW

    def test_empty_effects_return_normal(self):
        assert _shot_visual_type({}) == _VISUAL_NORMAL

    def test_unknown_effects_return_normal(self):
        assert _shot_visual_type({"some_other_effect": 1.0}) == _VISUAL_NORMAL


# ── Slow effect via Shot ──────────────────────────────────────


class TestSlowEffect:
    def test_slow_shot_sets_slow_timer(self):
        """Shot with slow effects applies slow_remaining_ms from slow_duration."""
        svc = BattleService()
        c = _critter(speed=4.0)
        shot = Shot(
            damage=0.0, target_cid=c.cid, source_sid=1,
            effects={"slow_ratio": 0.5, "slow_duration": 3000.0},
            flight_remaining_ms=10.0, origin=HexCoord(0, 0),
        )
        b = _battle(c, pending_shots=[shot])
        svc._step_shots(b, 20.0)

        assert c.slow_remaining_ms == pytest.approx(3000.0)
        assert c.slow_speed == pytest.approx(2.0)  # 4.0 * 0.5

    def test_slow_timer_counts_down_each_step(self):
        """slow_remaining_ms decrements by dt_ms on each critter step."""
        svc = BattleService()
        c = _critter(speed=2.0)
        c.slow_remaining_ms = 1500.0
        c.slow_speed = 1.0
        b = _battle(c)

        svc._step_critters(b, 500.0)
        assert c.slow_remaining_ms == pytest.approx(1000.0)

        svc._step_critters(b, 500.0)
        assert c.slow_remaining_ms == pytest.approx(500.0)

        svc._step_critters(b, 500.0)
        assert c.slow_remaining_ms == pytest.approx(0.0)

    def test_slow_reduces_movement(self):
        """Slowed critter covers less ground than un-slowed critter."""
        svc = BattleService()

        c_normal = _critter(speed=2.0)
        c_slowed = _critter(speed=2.0)
        c_slowed.cid = 2
        c_slowed.slow_remaining_ms = 5000.0
        c_slowed.slow_speed = 1.0  # half speed

        b = _battle(c_normal, c_slowed)
        svc._step_critters(b, 1000.0)  # 1 second

        # Normal critter: 2 hex/s × 1s / (path_len-1) = 2/19 ≈ 0.105 progress
        # Slowed critter: 1 hex/s × 1s / (path_len-1) = 1/19 ≈ 0.053 progress
        assert c_normal.path_progress > c_slowed.path_progress

    def test_slow_expires_and_speed_restores(self):
        """Once slow_remaining_ms reaches 0, critter uses full speed again."""
        svc = BattleService()
        c = _critter(speed=4.0)
        c.slow_remaining_ms = 100.0
        c.slow_speed = 1.0
        b = _battle(c)

        # Tick past the slow duration
        svc._step_critters(b, 200.0)

        assert c.slow_remaining_ms == pytest.approx(0.0)
        # On the next tick the critter uses full speed
        progress_before = c.path_progress
        svc._step_critters(b, 1000.0)
        distance_at_full = c.path_progress - progress_before
        path_len = len(c.path) - 1
        assert distance_at_full == pytest.approx(4.0 / path_len, rel=0.01)

    def test_no_slow_when_effects_empty(self):
        """Shot with empty effects does not apply slow."""
        svc = BattleService()
        c = _critter(speed=2.0)
        shot = Shot(
            damage=0.0, target_cid=c.cid, source_sid=1,
            effects={},
            flight_remaining_ms=10.0, origin=HexCoord(0, 0),
        )
        b = _battle(c, pending_shots=[shot])
        svc._step_shots(b, 20.0)

        assert c.slow_remaining_ms == pytest.approx(0.0)


# ── Burn effect via Shot ──────────────────────────────────────


class TestBurnEffect:
    def test_burn_shot_sets_burn_timer(self):
        """Shot with burn effects applies burn_remaining_ms from burn_duration."""
        svc = BattleService()
        c = _critter()
        shot = Shot(
            damage=0.0, target_cid=c.cid, source_sid=1,
            effects={"burn_dps": 3.0, "burn_duration": 4000.0},
            flight_remaining_ms=10.0, origin=HexCoord(0, 0),
        )
        b = _battle(c, pending_shots=[shot])
        svc._step_shots(b, 20.0)

        assert c.burn_remaining_ms == pytest.approx(4000.0)
        assert c.burn_dps == pytest.approx(3.0)

    def test_burn_deals_damage_over_time(self):
        """burn_dps × elapsed_s is subtracted from health each tick."""
        svc = BattleService()
        c = _critter(health=100.0, speed=0.1)
        c.burn_remaining_ms = 3000.0
        c.burn_dps = 5.0
        b = _battle(c)

        svc._step_critters(b, 1000.0)  # 1 second
        assert c.health == pytest.approx(95.0)  # 5 dps × 1s
        assert c.burn_remaining_ms == pytest.approx(2000.0)

        svc._step_critters(b, 1000.0)
        assert c.health == pytest.approx(90.0)
        assert c.burn_remaining_ms == pytest.approx(1000.0)

        svc._step_critters(b, 1000.0)
        assert c.health == pytest.approx(85.0)
        assert c.burn_remaining_ms == pytest.approx(0.0)

    def test_burn_timer_counts_down_each_step(self):
        """burn_remaining_ms decrements by dt_ms on each step."""
        svc = BattleService()
        c = _critter(speed=0.1)
        c.burn_remaining_ms = 2000.0
        c.burn_dps = 1.0
        b = _battle(c)

        svc._step_critters(b, 500.0)
        assert c.burn_remaining_ms == pytest.approx(1500.0)

        svc._step_critters(b, 1000.0)
        assert c.burn_remaining_ms == pytest.approx(500.0)

    def test_burn_expires_cleanly(self):
        """burn_remaining_ms does not go below 0."""
        svc = BattleService()
        c = _critter(health=100.0, speed=0.1)
        c.burn_remaining_ms = 200.0
        c.burn_dps = 1.0
        b = _battle(c)

        svc._step_critters(b, 500.0)  # Tick past expiry
        assert c.burn_remaining_ms == pytest.approx(0.0)

    def test_burn_bypasses_armour(self):
        """Burn damage does not get reduced by armour."""
        svc = BattleService()
        c = _critter(health=100.0, speed=0.1)
        c.armour = 50.0
        shot = Shot(
            damage=0.0, target_cid=c.cid, source_sid=1,
            effects={"burn_dps": 5.0, "burn_duration": 1000.0},
            flight_remaining_ms=1.0, origin=HexCoord(0, 0),
        )
        b = _battle(c, pending_shots=[shot])
        svc._step_shots(b, 10.0)   # Apply burn
        svc._step_critters(b, 1000.0)  # Tick 1s

        assert c.health == pytest.approx(95.0)  # 5 dps × 1s, armour NOT applied

    def test_burn_kills_critter(self):
        """Critter with too little health dies from burn DoT."""
        svc = BattleService()
        c = _critter(health=3.0, speed=0.1)
        c.burn_remaining_ms = 5000.0
        c.burn_dps = 2.0
        b = _battle(c)

        svc._step_critters(b, 2000.0)  # 4 total damage
        assert c.cid not in b.critters  # Died and was removed

    def test_no_burn_when_effects_empty(self):
        """Shot with empty effects does not apply burn."""
        svc = BattleService()
        c = _critter()
        shot = Shot(
            damage=0.0, target_cid=c.cid, source_sid=1,
            effects={},
            flight_remaining_ms=10.0, origin=HexCoord(0, 0),
        )
        b = _battle(c, pending_shots=[shot])
        svc._step_shots(b, 20.0)

        assert c.burn_remaining_ms == pytest.approx(0.0)


# ── Tower fires with effects from structure ───────────────────


class TestTowerEffectsFromStructure:
    """Verify that the shot created by a tower carries the structure's effects."""

    def _slow_structure(self) -> Structure:
        return Structure(
            sid=1, iid="COLD_TOWER",
            position=HexCoord(0, 0),
            damage=5.0, range=5, reload_time_ms=2000.0,
            shot_speed=10.0,
            effects={"slow_ratio": 0.5, "slow_duration": 3000.0},
            reload_remaining_ms=0.0,
        )

    def _burn_structure(self) -> Structure:
        return Structure(
            sid=2, iid="FIRE_TOWER",
            position=HexCoord(0, 0),
            damage=2.0, range=5, reload_time_ms=2500.0,
            shot_speed=10.0,
            effects={"burn_dps": 1.0, "burn_duration": 3000.0},
            reload_remaining_ms=0.0,
        )

    def test_slow_tower_shot_carries_effects(self):
        """Slow tower fires a shot whose effects contain slow params."""
        svc = BattleService()
        c = _critter(speed=4.0)
        c.path_progress = 0.1  # hex ~1-2 away from tower at (0,0) — within range 5
        struct = self._slow_structure()
        b = BattleState(
            bid=1, defender=None, attacker=None,
            critters={c.cid: c},
            structures={struct.sid: struct},
        )

        svc._step_towers(b, 100.0)

        assert len(b.pending_shots) == 1
        shot = b.pending_shots[0]
        assert shot.effects["slow_ratio"] == pytest.approx(0.5)
        assert shot.effects["slow_duration"] == pytest.approx(3000.0)

    def test_slow_tower_slows_critter_on_hit(self):
        """Slow tower shot actually slows the critter when it arrives."""
        svc = BattleService()
        c = _critter(speed=4.0)
        c.path_progress = 0.1
        struct = self._slow_structure()
        struct.reload_remaining_ms = 0.0
        b = BattleState(
            bid=1, defender=None, attacker=None,
            critters={c.cid: c},
            structures={struct.sid: struct},
        )

        svc._step_towers(b, 50.0)   # Tower fires
        svc._step_shots(b, 1000.0)  # Long enough for shot to arrive

        assert c.slow_remaining_ms == pytest.approx(3000.0)
        assert c.slow_speed == pytest.approx(2.0)  # 4.0 * 0.5

    def test_burn_tower_burns_critter_on_hit(self):
        """Burn tower shot actually burns the critter when it arrives."""
        svc = BattleService()
        c = _critter(speed=0.1)
        c.path_progress = 0.1
        struct = self._burn_structure()
        b = BattleState(
            bid=1, defender=None, attacker=None,
            critters={c.cid: c},
            structures={struct.sid: struct},
        )

        svc._step_towers(b, 50.0)
        svc._step_shots(b, 1000.0)

        assert c.burn_remaining_ms == pytest.approx(3000.0)
        assert c.burn_dps == pytest.approx(1.0)


# ── structures.yaml integration ──────────────────────────────


class TestStructuresYamlEffects:
    """Verify that effects are correctly loaded from structures.yaml."""

    @pytest.fixture(scope="class")
    def items_by_iid(self):
        import pathlib
        config = pathlib.Path(__file__).parent.parent / "config"
        return {i.iid: i for i in load_items(config)}

    def test_spike_trap_has_slow_effects(self, items_by_iid):
        item = items_by_iid["SPIKE_TRAP"]
        assert item.effects.get("slow_duration", 0) > 0
        assert 0 <= item.effects.get("slow_ratio", -1) <= 1

    def test_tar_tower_has_slow_effects(self, items_by_iid):
        item = items_by_iid["TAR_TOWER"]
        assert item.effects.get("slow_duration", 0) > 0
        assert 0 <= item.effects.get("slow_ratio", -1) <= 1

    def test_cold_tower_has_slow_effects(self, items_by_iid):
        item = items_by_iid["COLD_TOWER"]
        assert item.effects.get("slow_duration", 0) > 0
        assert 0 <= item.effects.get("slow_ratio", -1) <= 1

    def test_ice_tower_has_slow_effects(self, items_by_iid):
        item = items_by_iid["ICE_TOWER"]
        assert item.effects.get("slow_duration", 0) > 0
        assert 0 <= item.effects.get("slow_ratio", -1) <= 1

    def test_fire_tower_has_burn_effects(self, items_by_iid):
        item = items_by_iid["FIRE_TOWER"]
        assert item.effects.get("burn_duration", 0) > 0
        assert item.effects.get("burn_dps", 0) > 0

    def test_flame_thrower_has_burn_effects(self, items_by_iid):
        item = items_by_iid["FLAME_THROWER"]
        assert item.effects.get("burn_duration", 0) > 0
        assert item.effects.get("burn_dps", 0) > 0

    def test_paralyzing_tower_stuns(self, items_by_iid):
        """Paralyzing tower should have slow_duration > 0 and slow_ratio = 0 (full stop)."""
        item = items_by_iid["PARALYZNG_TOWER"]
        assert item.effects.get("slow_ratio") == pytest.approx(0.0)
        assert item.effects.get("slow_duration", 0) > 0

    def test_visual_type_slow_towers(self, items_by_iid):
        """Slow towers should produce VISUAL_SLOW shots."""
        for iid in ("SPIKE_TRAP", "TAR_TOWER", "COLD_TOWER", "ICE_TOWER"):
            item = items_by_iid[iid]
            assert _shot_visual_type(item.effects) == _VISUAL_SLOW, f"{iid} should map to VISUAL_SLOW"

    def test_visual_type_burn_towers(self, items_by_iid):
        """Burn towers should produce VISUAL_BURN shots."""
        for iid in ("FIRE_TOWER", "FLAME_THROWER"):
            item = items_by_iid[iid]
            assert _shot_visual_type(item.effects) == _VISUAL_BURN, f"{iid} should map to VISUAL_BURN"
