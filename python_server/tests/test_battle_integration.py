"""Integration tests for the battle system.

These tests use the deterministic tick() method to simulate
complete battle scenarios without timing dependencies.
"""

import pytest
from gameserver.engine.battle_service import BattleService
from gameserver.models.battle import BattleState
from gameserver.models.critter import Critter, DamageType
from gameserver.models.structure import Structure
from gameserver.models.shot import Shot
from gameserver.models.hex import HexCoord
from gameserver.models.empire import Empire
from gameserver.models.army import Army, CritterWave


class ItemMock:
    """Mock item for testing."""
    def __init__(self, iid, **kwargs):
        self.iid = iid
        for key, value in kwargs.items():
            setattr(self, key, value)


class TestBattleIntegration:
    """Integration tests for complete battle scenarios."""
    
    def test_full_battle_critters_die_and_reach_goal(self):
        """Complete battle: critters spawn, get shot, some die, some reach goal.
        
        Uses 10x speeds for faster test execution.
        """
        # Create mock items with 10x speeds
        items = {
            "fast_soldier": ItemMock(
                "fast_soldier",
                health=5.0,  # More HP so some survive
                speed=1.5,  # 10x normal (0.15 -> 1.5 hex/s)
                armour=0.0,
                time_between=200,  # 10x faster spawn (2000ms -> 200ms)
            ),
            "fast_tower": ItemMock(
                "fast_tower",
                damage=1.0,
                range=2,  # Shorter range so not all critters are hit
                reload_time_ms=100,  # 10x faster reload (1000ms -> 100ms)
                shot_speed=80.0,  # 10x faster shot (8.0 -> 80.0 hex/s)
                shot_type=0,  # NORMAL
                effects={},
            ),
        }
        
        service = BattleService(items=items)
        
        # Create defender with initial life
        defender = Empire(uid=1, name="Defender")
        defender.resources["life"] = 10.0
        
        # Create attacker
        attacker = Empire(uid=2, name="Attacker")
        
        # Create path: spawn at (0,5), move through (1,4), (2,3), end at (3,2)
        # Path length = 4 hexes
        critter_path = [
            HexCoord(0, 5),
            HexCoord(1, 4),
            HexCoord(2, 3),
            HexCoord(3, 2),
        ]
        
        # Create tower at (2,2) - slightly off the path, shorter range
        tower = Structure(
            sid=1,
            iid="fast_tower",
            position=HexCoord(2, 2),
            damage=1.0,
            range=2,
            reload_time_ms=100.0,
            shot_speed=80.0,
            shot_type=0,
            effects={},
            reload_remaining_ms=0.0,  # Ready to fire
        )
        
        # Create army with 3 fast soldiers (2 HP each)
        wave = CritterWave(
            wave_id=1,
            iid="fast_soldier",
            slots=3,
            num_critters_spawned=0,
            next_critter_ms=0,  # Spawn immediately
        )
        army = Army(
            aid=1,
            uid=2,
            name="Test Army",
            waves=[wave],
        )
        
        # Create battle
        battle = BattleState(
            bid=1,
            defender=defender,
            attacker=attacker,
            army=army,
            structures={1: tower},
            critter_path=critter_path,
        )
        
        # Track events
        total_spawned = 0
        total_killed = 0
        total_finished = 0
        initial_life = defender.resources["life"]
        last_life = initial_life
        
        # Run battle for ~10 seconds of game time (10000ms)
        # With 10x speeds, this simulates ~100 seconds of normal gameplay
        dt_ms = 15.0  # 15ms per tick (realistic tick rate)
        max_ticks = int(10000 / dt_ms)
        
        for tick in range(max_ticks):
            # Count critters before tick
            critters_before = len(battle.critters)
            
            # Execute tick
            service.tick(battle, dt_ms)
            
            # Count critters after tick
            critters_after = len(battle.critters)
            
            # Check for spawns (critters increased)
            if critters_after > critters_before:
                total_spawned += (critters_after - critters_before)
            
            # Check for deaths/finishes (critters decreased)
            if critters_after < critters_before:
                decrease = critters_before - critters_after
                
                # Check if defender life changed this tick
                current_life = defender.resources["life"]
                if current_life < last_life:
                    # Life was lost, so critter(s) finished
                    life_lost_this_tick = last_life - current_life
                    finished_this_tick = int(life_lost_this_tick)
                    total_finished += finished_this_tick
                    total_killed += (decrease - finished_this_tick)
                    last_life = current_life
                else:
                    # No life lost, so all were killed
                    total_killed += decrease
            
            # Stop if battle finished
            if battle.is_finished:
                break
        
        # Verify outcomes
        assert total_spawned == 3, f"Expected 3 critters spawned, got {total_spawned}"
        
        # Verify all critters were accounted for (killed or finished)
        total_accounted = total_killed + total_finished
        assert total_accounted == 3, f"Expected all 3 critters accounted for, got {total_killed} killed + {total_finished} finished = {total_accounted}"
        
        # Verify no critters left on field
        assert len(battle.critters) == 0, "Expected no critters remaining"
        assert len(battle.pending_shots) == 0, "Expected no shots remaining"
        
        # If critters finished, verify defender lost life
        if total_finished > 0:
            final_life = defender.resources["life"]
            life_lost = initial_life - final_life
            assert life_lost == total_finished, f"Life lost ({life_lost}) should match critters finished ({total_finished})"
    
    def test_battle_defender_wins_all_critters_killed(self):
        """Battle where all critters are killed before reaching goal."""
        # Create items with 10x speeds and strong tower
        items = {
            "weak_critter": ItemMock(
                "weak_critter",
                health=1.0,  # Low health
                speed=0.5,  # Slow
                armour=0.0,
                time_between=500,
            ),
            "strong_tower": ItemMock(
                "strong_tower",
                damage=10.0,  # High damage
                range=10,  # Long range
                reload_time_ms=100,
                shot_speed=100.0,
                shot_type=0,
                effects={},
            ),
        }
        
        service = BattleService(items=items)
        
        defender = Empire(uid=1, name="Defender")
        defender.resources["life"] = 10.0
        attacker = Empire(uid=2, name="Attacker")
        
        # Short path
        critter_path = [HexCoord(0, 0), HexCoord(1, 0), HexCoord(2, 0)]
        
        # Strong tower at start of path
        tower = Structure(
            sid=1,
            iid="strong_tower",
            position=HexCoord(1, 0),
            damage=10.0,
            range=10,
            reload_time_ms=100.0,
            shot_speed=100.0,
            shot_type=0,
            effects={},
            reload_remaining_ms=0.0,
        )
        
        # Army with 2 weak critters
        wave = CritterWave(
            wave_id=1,
            iid="weak_critter",
            slots=2,
            num_critters_spawned=0,
            next_critter_ms=0,
        )
        army = Army(
            aid=1,
            uid=2,
            name="Test Army",
            waves=[wave],
        )
        
        battle = BattleState(
            bid=1,
            defender=defender,
            attacker=attacker,
            army=army,
            structures={1: tower},
            critter_path=critter_path,
        )
        
        initial_life = defender.resources["life"]
        
        # Run battle
        for tick in range(1000):
            service.tick(battle, 15.0)
            if battle.is_finished:
                break
        
        # Verify defender won (no life lost)
        assert defender.resources["life"] == initial_life, "Defender should not lose life"
        assert len(battle.critters) == 0, "All critters should be killed"
        
    def test_critter_reaches_goal_damages_defender(self):
        """Verify that critter reaching goal reduces defender life by 1."""
        service = BattleService()
        
        defender = Empire(uid=1, name="Defender")
        defender.resources["life"] = 10.0
        
        # Create critter at end of path
        critter = Critter(
            cid=1,
            iid="soldier",
            health=5.0,
            max_health=5.0,
            speed=1.5,
            path=[HexCoord(0, 0), HexCoord(1, 0)],
            path_progress=0.99,  # Almost at goal
        )
        
        battle = BattleState(
            bid=1,
            defender=defender,
            attacker=None,
            critters={1: critter},
        )
        
        initial_life = defender.resources["life"]
        
        # Step critters (will move to path_progress >= 1.0)
        service._step_critters(battle, 100.0)
        
        # Verify critter removed and life reduced
        assert 1 not in battle.critters, "Critter should be removed"
        assert defender.resources["life"] == initial_life - 1.0, "Life should decrease by 1"
        assert battle.defender_losses.get("life", 0.0) == 1.0, "Defender losses should track life"


class TestCritterKillGoldReward:
    """Tests that the defender receives gold when a critter is killed."""

    def _make_battle(self, critter_value: float, defender_gold: float = 0.0) -> tuple:
        service = BattleService()
        defender = Empire(uid=1, name="Defender")
        defender.resources["gold"] = defender_gold

        critter = Critter(
            cid=1,
            iid="orc",
            health=1.0,
            max_health=1.0,
            speed=0.2,
            value=critter_value,
            path=[HexCoord(0, 0), HexCoord(1, 0)],
            path_progress=0.5,
        )
        battle = BattleState(
            bid=1,
            defender=defender,
            attacker=None,
            critters={1: critter},
        )
        return service, battle, defender, critter

    def test_defender_receives_gold_on_kill(self):
        """Killing a critter awards its value as gold to the defender."""
        service, battle, defender, critter = self._make_battle(critter_value=5.0, defender_gold=10.0)

        service._critter_died(battle, critter)

        assert defender.resources["gold"] == pytest.approx(15.0), \
            "Defender should receive critter.value gold on kill"

    def test_critter_removed_after_kill(self):
        """Critter is removed from battle after dying."""
        service, battle, defender, critter = self._make_battle(critter_value=3.0)

        service._critter_died(battle, critter)

        assert 1 not in battle.critters, "Dead critter must be removed from battle"

    def test_kill_reason_recorded_in_removed_critters(self):
        """removed_critters list records reason='died' after a kill."""
        service, battle, defender, critter = self._make_battle(critter_value=2.0)

        service._critter_died(battle, critter)

        assert len(battle.removed_critters) == 1
        entry = battle.removed_critters[0]
        assert entry["cid"] == 1
        assert entry["reason"] == "died"

    def test_zero_value_critter_awards_no_gold(self):
        """A critter with value=0 awards no gold."""
        service, battle, defender, critter = self._make_battle(critter_value=0.0, defender_gold=100.0)

        service._critter_died(battle, critter)

        assert defender.resources["gold"] == pytest.approx(100.0), \
            "Gold should be unchanged for value=0 critter"

    def test_multiple_kills_accumulate_gold(self):
        """Gold accumulates correctly across multiple critter kills."""
        service = BattleService()
        defender = Empire(uid=1, name="Defender")
        defender.resources["gold"] = 0.0

        path = [HexCoord(0, 0), HexCoord(1, 0)]
        critters = {
            i: Critter(cid=i, iid="orc", health=1.0, max_health=1.0,
                       speed=0.2, value=float(i) * 2, path=path, path_progress=0.5)
            for i in range(1, 4)  # values: 2, 4, 6 → total 12
        }
        battle = BattleState(bid=1, defender=defender, attacker=None, critters=critters)

        for critter in list(critters.values()):
            service._critter_died(battle, critter)

        assert defender.resources["gold"] == pytest.approx(12.0), \
            "Gold should accumulate: 2+4+6=12"

    def test_reaching_goal_does_not_award_gold(self):
        """A critter that reaches the goal (escaped) does not award gold."""
        service = BattleService()
        defender = Empire(uid=1, name="Defender")
        defender.resources["gold"] = 50.0
        defender.resources["life"] = 10.0

        critter = Critter(
            cid=1,
            iid="orc",
            health=5.0,
            max_health=5.0,
            speed=0.2,
            value=10.0,
            path=[HexCoord(0, 0), HexCoord(1, 0)],
            path_progress=0.99,
        )
        battle = BattleState(bid=1, defender=defender, attacker=None, critters={1: critter})

        service._step_critters(battle, 200.0)  # moves to >= 1.0 → triggers _critter_finished

        assert defender.resources["gold"] == pytest.approx(50.0), \
            "Escaped critter should not award gold"
        assert defender.resources["life"] < 10.0, "Life should decrease (critter reached goal)"
