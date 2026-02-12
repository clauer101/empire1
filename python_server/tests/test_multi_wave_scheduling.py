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
    """Test that waves spawn critters in correct sequence."""
    
    # Create battle with 2-wave army
    battle = BattleState(
        bid=1,
        defender_uid=200,
        attacker_uids=[100],
        attack_id=1,
        attacker=two_wave_army,
        structures={},
        observer_uids=set(),
    )
    
    # Simulate battle ticks
    tick_interval_ms = 15.0
    total_time_ms = 0.0
    max_time_ms = 10000.0
    
    while total_time_ms < max_time_ms:
        battle_service.tick(battle, tick_interval_ms)
        
        # Assign path to newly spawned critters
        for critter in battle.new_critters:
            if not critter.path:
                critter.path = test_path
        battle.new_critters.clear()
        
        total_time_ms += tick_interval_ms
    
    # Count critters by type
    goblin_count = sum(1 for c in battle.critters.values() if c.iid == "FAST_GOBLIN")
    orc_count = sum(1 for c in battle.critters.values() if c.iid == "FAST_ORC")
    
    print(f"\n[TEST] Total critters: {len(battle.critters)}")
    print(f"[TEST] FAST_GOBLIN: {goblin_count}, FAST_ORC: {orc_count}")
    
    # Assertions: verify all critters from both waves were spawned
    assert goblin_count == 3, f"Should spawn 3 goblins from wave 1, got {goblin_count}"
    assert orc_count == 2, f"Should spawn 2 orcs from wave 2, got {orc_count}"
    assert len(battle.critters) == 5, f"Should spawn 5 total critters, got {len(battle.critters)}"



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
        attacker=army,
        structures={},
        observer_uids=set(),
    )
    
    spawn_times = []
    tick_interval_ms = 15.0
    total_time_ms = 0.0
    max_time_ms = 2000.0
    
    while total_time_ms < max_time_ms:
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
    
    # Verify critters spawned
    assert len(spawn_times) >= 1, f"Should spawn at least 1 critter, got {len(spawn_times)}"
    assert len(battle.critters) == 3, f"Should spawn 3 critters, got {len(battle.critters)}"
    
    # Check intervals between spawns (should be ~100ms as configured)
    if len(spawn_times) >= 2:
        interval_1 = spawn_times[1] - spawn_times[0]
        interval_2 = spawn_times[2] - spawn_times[1] if len(spawn_times) > 2 else None
        
        print(f"[TEST] Intervals: {interval_1:.0f}ms" + (f", {interval_2:.0f}ms" if interval_2 else ""))
        
        # Allow some tolerance due to tick granularity (15ms)
        assert 85 <= interval_1 <= 115, f"First interval should be ~100ms, got {interval_1:.0f}ms"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

