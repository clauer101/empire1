"""Test shot damage application and effects."""

import pytest
from gameserver.engine.battle_service import BattleService
from gameserver.models.battle import BattleState
from gameserver.models.critter import Critter, DamageType
from gameserver.models.shot import Shot
from gameserver.models.hex import HexCoord


class TestShotDamageApplication:
    """Test that shots apply damage correctly when they arrive."""
    
    def test_shot_applies_damage_on_arrival(self):
        """Shot should apply damage when flight_remaining_ms reaches 0."""
        service = BattleService()
        
        critter = Critter(
            cid=100,
            iid="orc",
            health=50.0,
            max_health=50.0,
            speed=2.0,
            path=[HexCoord(2, 0), HexCoord(1, 0), HexCoord(0, 0)],
            path_progress=0.5,
        )
        
        shot = Shot(
            damage=10.0,
            target_cid=100,
            source_sid=1,
            flight_remaining_ms=50.0,  # Will arrive after 50ms
            origin=HexCoord(0, 0),
            path_progress=0.0,
        )
        
        battle = BattleState(
            bid=1,
            defender=None,
            attacker=None,
            critters={100: critter},
            pending_shots=[shot],
        )
        
        # Step once - shot still in flight
        service._step_shots(battle, 30.0)
        assert len(battle.pending_shots) == 1
        assert shot.flight_remaining_ms == pytest.approx(20.0)
        assert critter.health == pytest.approx(50.0)  # Not hit yet
        
        # Step again - shot arrives
        service._step_shots(battle, 30.0)
        assert len(battle.pending_shots) == 0  # Shot removed
        assert critter.health == pytest.approx(40.0)  # Damaged
    
    def test_shot_path_progress_updates(self):
        """Shot path_progress should increase from 0.0 to 1.0 during flight."""
        service = BattleService()
        
        critter = Critter(
            cid=100,
            iid="orc",
            health=50.0,
            max_health=50.0,
            speed=2.0,
            path=[HexCoord(2, 0), HexCoord(1, 0), HexCoord(0, 0)],
            path_progress=0.5,
        )
        
        shot = Shot(
            damage=10.0,
            target_cid=100,
            source_sid=1,
            flight_remaining_ms=100.0,
            origin=HexCoord(0, 0),
            path_progress=0.0,
        )
        
        battle = BattleState(
            bid=1,
            defender=None,
            attacker=None,
            critters={100: critter},
            pending_shots=[shot],
        )
        
        # Step 1: 25% through flight
        service._step_shots(battle, 25.0)
        assert shot.path_progress == pytest.approx(0.25, abs=0.01)
        
        # Step 2: 50% through flight
        service._step_shots(battle, 25.0)
        assert shot.path_progress == pytest.approx(0.50, abs=0.01)
        
        # Step 3: 75% through flight
        service._step_shots(battle, 25.0)
        assert shot.path_progress == pytest.approx(0.75, abs=0.01)
    
    def test_shot_respects_armour(self):
        """Normal damage should be reduced by critter armour."""
        service = BattleService()
        
        critter = Critter(
            cid=100,
            iid="armored_orc",
            health=50.0,
            max_health=50.0,
            speed=2.0,
            armour=3.0,  # 3 damage reduction
            path=[HexCoord(2, 0)],
            path_progress=0.0,
        )
        
        shot = Shot(
            damage=10.0,
            target_cid=100,
            source_sid=1,
            shot_type=DamageType.NORMAL,
            flight_remaining_ms=10.0,
            origin=HexCoord(0, 0),
        )
        
        battle = BattleState(
            bid=1,
            defender=None,
            attacker=None,
            critters={100: critter},
            pending_shots=[shot],
        )
        
        # Shot arrives and applies damage (10 - 3 armour = 7 damage)
        service._step_shots(battle, 20.0)
        assert critter.health == pytest.approx(43.0)
    
    def test_shot_cold_applies_slow_effect(self):
        """COLD shot should apply slow effect to critter."""
        service = BattleService()
        
        critter = Critter(
            cid=100,
            iid="orc",
            health=50.0,
            max_health=50.0,
            speed=2.0,
            path=[HexCoord(2, 0)],
            path_progress=0.0,
        )
        
        shot = Shot(
            damage=5.0,
            target_cid=100,
            source_sid=1,
            shot_type=DamageType.COLD,
            effects={"slow_target": 0.5, "slow_target_duration": 2.0},  # 50% speed for 2s
            flight_remaining_ms=10.0,
            origin=HexCoord(0, 0),
        )
        
        battle = BattleState(
            bid=1,
            defender=None,
            attacker=None,
            critters={100: critter},
            pending_shots=[shot],
        )
        
        # Shot arrives
        service._step_shots(battle, 20.0)
        
        # Verify slow effect applied
        assert critter.slow_remaining_ms == pytest.approx(2000.0)
        assert critter.slow_speed == pytest.approx(1.0)  # 2.0 * 0.5
        assert critter.health == pytest.approx(45.0)  # Also took damage
    
    def test_shot_burn_applies_dot_effect(self):
        """BURN shot should apply burn DoT effect to critter."""
        service = BattleService()
        
        critter = Critter(
            cid=100,
            iid="orc",
            health=50.0,
            max_health=50.0,
            speed=2.0,
            path=[HexCoord(2, 0)],
            path_progress=0.0,
        )
        
        shot = Shot(
            damage=5.0,
            target_cid=100,
            source_sid=1,
            shot_type=DamageType.BURN,
            effects={"burn_target_dps": 2.0, "burn_target_duration": 3.0},  # 2 dps for 3s
            flight_remaining_ms=10.0,
            origin=HexCoord(0, 0),
        )
        
        battle = BattleState(
            bid=1,
            defender=None,
            attacker=None,
            critters={100: critter},
            pending_shots=[shot],
        )
        
        # Shot arrives
        service._step_shots(battle, 20.0)
        
        # Verify burn effect applied
        assert critter.burn_remaining_ms == pytest.approx(3000.0)
        assert critter.burn_dps == pytest.approx(2.0)
        assert critter.health == pytest.approx(45.0)  # Initial damage
    
    def test_shot_misses_if_critter_died(self):
        """Shot should miss if target critter no longer exists."""
        service = BattleService()
        
        shot = Shot(
            damage=10.0,
            target_cid=999,  # Non-existent critter
            source_sid=1,
            flight_remaining_ms=10.0,
            origin=HexCoord(0, 0),
        )
        
        battle = BattleState(
            bid=1,
            defender=None,
            attacker=None,
            critters={},  # No critters
            pending_shots=[shot],
        )
        
        # Shot arrives but has no target
        service._step_shots(battle, 20.0)
        
        # Shot should be removed even though it missed
        assert len(battle.pending_shots) == 0


class TestBurnDamageOverTime:
    """Test that burn damage is applied over time."""
    
    def test_burn_damage_ticks_during_movement(self):
        """Burn damage should be applied during critter movement."""
        service = BattleService()
        
        # Create a critter with a longer path so it doesn't finish immediately
        long_path = [HexCoord(i, 0) for i in range(10)]  # 10 tile path = 9 hex travel distance
        
        critter = Critter(
            cid=100,
            iid="orc",
            health=50.0,
            max_health=50.0,
            speed=1.0,  # 1 hex/s
            burn_remaining_ms=2000.0,  # 2 seconds of burn
            burn_dps=5.0,  # 5 damage per second
            path=long_path,
            path_progress=0.0,
        )
        
        battle = BattleState(
            bid=1,
            defender=None,
            attacker=None,
            critters={100: critter},
        )
        
        # Move for 1 second (1000ms)
        service._step_critters(battle, 1000.0)
        
        # Should have taken 5 damage (1s * 5 dps)
        assert critter.health == pytest.approx(45.0)
        assert critter.burn_remaining_ms == pytest.approx(1000.0)
        assert critter.cid in battle.critters  # Still alive
        
        # Move for another 1 second
        service._step_critters(battle, 1000.0)
        
        # Should have taken another 5 damage
        assert critter.health == pytest.approx(40.0)
        assert critter.burn_remaining_ms == pytest.approx(0.0)
        assert critter.cid in battle.critters  # Still alive
