"""Test multi-wave battle scheduling with short intervals.

This test verifies that:
1. Multiple waves spawn in sequence
2. wave_pointer advances correctly
3. Wave spawn tracking works properly
4. Wave transitions happen at the right time
"""

import pytest
from gameserver.models.army import Army, CritterWave
from gameserver.models.battle import BattleState
from gameserver.models.hex import HexCoord
from gameserver.models.items import ItemDetails, ItemType
from gameserver.engine.battle_service import BattleService


@pytest.fixture
def battle_service():
    """Create BattleService with test critter config."""
    # Use ItemDetails objects for proper config
    items = {
        "FAST_GOBLIN": ItemDetails(
            iid="FAST_GOBLIN",
            name="Fast Goblin",
            item_type=ItemType.CRITTER,
            health=10.0,
            speed=2.0,
            time_between_ms=100.0,  # 100ms between spawns (very fast for testing)
        ),
        "FAST_ORC": ItemDetails(
            iid="FAST_ORC",
            name="Fast Orc",
            item_type=ItemType.CRITTER,
            health=15.0,
            speed=1.5,
            time_between_ms=150.0,  # 150ms between spawns
        )
    }
    return BattleService(items=items)


@pytest.fixture
def test_path():
    """Create a simple 3-tile path for testing."""
    # Spawnpoint (0,2) -> Path (0,1) -> Castle (0,0)
    return [HexCoord(0, 2), HexCoord(0, 1), HexCoord(0, 0)]


@pytest.fixture
def two_wave_army():
    """Create army with 2 waves and short intervals."""
    return Army(
        aid=1,
        uid=100,
        name="Test Army",
        waves=[
            CritterWave(wave_id=1, iid="FAST_GOBLIN", slots=3),  # 3 goblins
            CritterWave(wave_id=2, iid="FAST_ORC", slots=2),     # 2 orcs
        ]
    )


def test_two_waves_spawn_in_sequence(battle_service, test_path, two_wave_army):
    """Test that waves spawn in correct order with proper wave_pointer progression."""
    
    # Create battle with 2-wave army
    battle = BattleState(
        bid=1,
        defender_uid=200,
        attacker_uids=[100],
        attack_id=1,
        armies={"attacker_100": two_wave_army},
        structures={},
        observer_uids=set(),
    )
    
    # Initialize wave progression
    direction = "attacker_100"
    battle.army_wave_pointers[direction] = 0
    battle.army_next_wave_ms[direction] = 100.0  # First wave starts after 100ms
    
    # Simulate battle for 10 seconds (5s inter-wave delay + spawning time)
    tick_interval_ms = 15.0
    total_time_ms = 0.0
    max_time_ms = 10000.0
    
    while total_time_ms < max_time_ms:
        battle_service.tick(battle, tick_interval_ms)
        
        # Assign path to newly spawned critters (game would do this in actual battle)
        for critter in battle.new_critters:
            if not critter.path:
                critter.path = test_path
        battle.new_critters.clear()
        
        total_time_ms += tick_interval_ms
    
    # Count critters by type
    goblin_count = sum(1 for c in battle.critters.values() if c.iid == "FAST_GOBLIN")
    orc_count = sum(1 for c in battle.critters.values() if c.iid == "FAST_ORC")
    
    print(f"\n[TEST] Total critters: {len(battle.critters)}")
    print(f"[TEST] Final wave_pointer: {battle.army_wave_pointers.get(direction, -1)}")
    print(f"[TEST] FAST_GOBLIN: {goblin_count}, FAST_ORC: {orc_count}")
    
    # Assertions
    assert len(battle.critters) == 5, f"Should spawn 5 total critters, got {len(battle.critters)}"
    assert goblin_count == 3, f"Should spawn 3 goblins from wave 1, got {goblin_count}"
    assert orc_count == 2, f"Should spawn 2 orcs from wave 2, got {orc_count}"
    
    # Wave pointer should have advanced to 2 (past both waves)
    final_wave_pointer = battle.army_wave_pointers.get(direction, -1)
    assert final_wave_pointer == 2, f"Wave pointer should be 2 after both waves, got {final_wave_pointer}"


def test_wave_pointer_tracking(battle_service, test_path, two_wave_army):
    """Test that wave_pointer is correctly tracked during wave transitions."""
    
    battle = BattleState(
        bid=1,
        defender_uid=200,
        attacker_uids=[100],
        attack_id=1,
        armies={"attacker_100": two_wave_army},
        structures={},
        observer_uids=set(),
    )
    
    direction = "attacker_100"
    battle.army_wave_pointers[direction] = 0
    battle.army_next_wave_ms[direction] = 100.0
    
    wave_pointer_history = []
    
    # Simulate and track wave_pointer changes (10s to allow 5s inter-wave delay)
    tick_interval_ms = 15.0
    total_time_ms = 0.0
    
    while total_time_ms < 10000.0:
        current_pointer = battle.army_wave_pointers.get(direction, -1)
        
        # Record if wave_pointer changed
        if not wave_pointer_history or wave_pointer_history[-1] != current_pointer:
            wave_pointer_history.append(current_pointer)
            print(f"[TEST] t={total_time_ms:.0f}ms: wave_pointer={current_pointer}")
        
        battle_service.tick(battle, tick_interval_ms)
        
        # Assign path to newly spawned critters
        for critter in battle.new_critters:
            if not critter.path:
                critter.path = test_path
        battle.new_critters.clear()
        
        total_time_ms += tick_interval_ms
    
    print(f"\n[TEST] Wave pointer progression: {wave_pointer_history}")
    
    # Should see progression: 0 -> 1 -> 2
    assert 0 in wave_pointer_history, "Should start at wave 0"
    assert 1 in wave_pointer_history, "Should advance to wave 1"
    assert 2 in wave_pointer_history, "Should advance to wave 2 after completion"
    
    # Check order
    idx_0 = wave_pointer_history.index(0)
    idx_1 = wave_pointer_history.index(1)
    idx_2 = wave_pointer_history.index(2)
    
    assert idx_0 < idx_1 < idx_2, "Wave pointer should advance in order: 0 -> 1 -> 2"


def test_wave_spawn_intervals(battle_service, test_path):
    """Test that critters within a wave spawn at correct intervals."""
    
    # Single wave with 3 critters
    army = Army(
        aid=1,
        uid=100,
        name="Test",
        waves=[CritterWave(wave_id=1, iid="FAST_GOBLIN", slots=3)]
    )
    
    battle = BattleState(
        bid=1,
        defender_uid=200,
        attacker_uids=[100],
        attack_id=1,
        armies={"attacker_100": army},
        structures={},
        observer_uids=set(),
    )
    
    direction = "attacker_100"
    battle.army_wave_pointers[direction] = 0
    battle.army_next_wave_ms[direction] = 0.0  # Wave starts immediately
    
    spawn_times = []
    tick_interval_ms = 15.0
    total_time_ms = 0.0
    
    while total_time_ms < 2000.0:
        prev_count = len(battle.critters)
        battle_service.tick(battle, tick_interval_ms)
        
        # Assign path to newly spawned critters
        for critter in battle.new_critters:
            if not critter.path:
                critter.path = test_path
        battle.new_critters.clear()
        
        # Check if new critter spawned
        if len(battle.critters) > prev_count:
            spawn_times.append(total_time_ms)
            print(f"[TEST] Critter {len(battle.critters)} spawned at t={total_time_ms:.0f}ms")
        
        total_time_ms += tick_interval_ms
    
    print(f"\n[TEST] Spawn times: {spawn_times}")
    
    assert len(spawn_times) == 3, f"Should spawn 3 critters, got {len(spawn_times)}"
    
    # Check intervals between spawns (should be ~100ms as configured)
    if len(spawn_times) >= 2:
        interval_1 = spawn_times[1] - spawn_times[0]
        interval_2 = spawn_times[2] - spawn_times[1]
        
        print(f"[TEST] Intervals: {interval_1:.0f}ms, {interval_2:.0f}ms")
        
        # Allow some tolerance due to tick granularity (15ms)
        assert 85 <= interval_1 <= 115, f"First interval should be ~100ms, got {interval_1:.0f}ms"
        assert 85 <= interval_2 <= 115, f"Second interval should be ~100ms, got {interval_2:.0f}ms"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

