"""Test tower shooting mechanics."""

import pytest
from gameserver.engine.battle_service import BattleService
from gameserver.models.battle import BattleState
from gameserver.models.critter import Critter
from gameserver.models.structure import Structure
from gameserver.models.hex import HexCoord


class TestTowerShooting:
    """Test tower targeting and shot creation."""
    
    def test_tower_fires_at_critter_in_range(self):
        """Tower should fire at critter within range."""
        service = BattleService()
        
        # Create battle with tower at (0,0) and critter at (2,0)
        tower = Structure(
            sid=1,
            iid="arrow_tower",
            position=HexCoord(0, 0),
            damage=10.0,
            range=5,
            reload_time_ms=1000.0,
            shot_speed=8.0,
            reload_remaining_ms=0.0,  # Ready to fire
        )
        
        critter = Critter(
            cid=100,
            iid="orc",
            health=50.0,
            max_health=50.0,
            speed=2.0,
            path=[HexCoord(2, 0), HexCoord(1, 0), HexCoord(0, 0)],
            path_progress=0.0,
        )
        
        battle = BattleState(
            bid=1,
            defender=None,
            attacker=None,
            structures={1: tower},
            critters={100: critter},
        )
        
        # Step towers
        service._step_towers(battle, 100.0)
        
        # Verify shot was created
        assert len(battle.pending_shots) == 1
        shot = battle.pending_shots[0]
        assert shot.target_cid == 100
        assert shot.source_sid == 1
        assert shot.damage == 10.0
        assert shot.origin == HexCoord(0, 0)
        assert shot.flight_remaining_ms > 0
        
        # Verify tower is on cooldown
        assert tower.reload_remaining_ms == 1000.0
        assert tower.focus_cid == 100
    
    def test_tower_does_not_fire_when_on_cooldown(self):
        """Tower should not fire while reload timer is active."""
        service = BattleService()
        
        tower = Structure(
            sid=1,
            iid="arrow_tower",
            position=HexCoord(0, 0),
            damage=10.0,
            range=5,
            reload_time_ms=1000.0,
            shot_speed=8.0,
            reload_remaining_ms=500.0,  # Still cooling down
        )
        
        critter = Critter(
            cid=100,
            iid="orc",
            health=50.0,
            max_health=50.0,
            speed=2.0,
            path=[HexCoord(2, 0), HexCoord(1, 0), HexCoord(0, 0)],
            path_progress=0.0,
        )
        
        battle = BattleState(
            bid=1,
            defender=None,
            attacker=None,
            structures={1: tower},
            critters={100: critter},
        )
        
        # Step towers
        service._step_towers(battle, 100.0)
        
        # Verify no shot was created
        assert len(battle.pending_shots) == 0
        
        # Verify timer decremented
        assert tower.reload_remaining_ms == 400.0
    
    def test_tower_ignores_critters_out_of_range(self):
        """Tower should not target critters beyond its range."""
        service = BattleService()
        
        tower = Structure(
            sid=1,
            iid="arrow_tower",
            position=HexCoord(0, 0),
            damage=10.0,
            range=2,  # Short range
            reload_time_ms=1000.0,
            shot_speed=8.0,
            reload_remaining_ms=0.0,
        )
        
        # Critter far away at (10, 0)
        critter = Critter(
            cid=100,
            iid="orc",
            health=50.0,
            max_health=50.0,
            speed=2.0,
            path=[HexCoord(10, 0), HexCoord(9, 0), HexCoord(8, 0)],
            path_progress=0.0,
        )
        
        battle = BattleState(
            bid=1,
            defender=None,
            attacker=None,
            structures={1: tower},
            critters={100: critter},
        )
        
        # Step towers
        service._step_towers(battle, 100.0)
        
        # Verify no shot was created (critter out of range)
        assert len(battle.pending_shots) == 0
        assert tower.focus_cid is None
    
    def test_tower_targets_most_advanced_critter(self):
        """Tower should target the critter with highest path_progress."""
        service = BattleService()
        
        tower = Structure(
            sid=1,
            iid="arrow_tower",
            position=HexCoord(0, 0),
            damage=10.0,
            range=5,
            reload_time_ms=1000.0,
            shot_speed=8.0,
            reload_remaining_ms=0.0,
        )
        
        # Two critters at different progress points
        critter1 = Critter(
            cid=100,
            iid="orc",
            health=50.0,
            max_health=50.0,
            speed=2.0,
            path=[HexCoord(3, 0), HexCoord(2, 0), HexCoord(1, 0), HexCoord(0, 0)],
            path_progress=0.2,  # Less advanced
        )
        
        critter2 = Critter(
            cid=101,
            iid="spider",
            health=30.0,
            max_health=30.0,
            speed=3.0,
            path=[HexCoord(3, 0), HexCoord(2, 0), HexCoord(1, 0), HexCoord(0, 0)],
            path_progress=0.7,  # More advanced - should be targeted
        )
        
        battle = BattleState(
            bid=1,
            defender=None,
            attacker=None,
            structures={1: tower},
            critters={100: critter1, 101: critter2},
        )
        
        # Step towers
        service._step_towers(battle, 100.0)
        
        # Verify shot targets the more advanced critter
        assert len(battle.pending_shots) == 1
        shot = battle.pending_shots[0]
        assert shot.target_cid == 101  # critter2
        assert tower.focus_cid == 101
