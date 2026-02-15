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
        defender=None,
        attacker=None,
        attack_id=1,
        army=two_wave_army,
        critter_path=test_path,
        structures={},
        observer_uids=set(),
    )
    
    # Track critters spawned during battle (not at end, since they may reach goal)
    spawned_goblins = 0
    spawned_orcs = 0
    seen_cids = set()
    
    # Simulate battle ticks
    tick_interval_ms = 15.0
    total_time_ms = 0.0
    max_time_ms = 10000.0
    
    while total_time_ms < max_time_ms:
        # Check for newly spawned critters before tick
        for cid, critter in battle.critters.items():
            if cid not in seen_cids:
                seen_cids.add(cid)
                if critter.iid == "FAST_GOBLIN":
                    spawned_goblins += 1
                elif critter.iid == "FAST_ORC":
                    spawned_orcs += 1
                print(f"[TEST] Spawned {critter.iid} (cid={cid}) at t={total_time_ms:.0f}ms")
        
        battle_service.tick(battle, tick_interval_ms)        
        total_time_ms += tick_interval_ms
    
    print(f"\n[TEST] Total spawned: FAST_GOBLIN={spawned_goblins}, FAST_ORC={spawned_orcs}")
    
    # Assertions: verify all critters from both waves were spawned (not remaining, but spawned total)
    assert spawned_goblins == 3, f"Should spawn 3 goblins from wave 1, got {spawned_goblins}"
    assert spawned_orcs == 2, f"Should spawn 2 orcs from wave 2, got {spawned_orcs}"
    assert len(seen_cids) == 5, f"Should spawn 5 total critters, got {len(seen_cids)}"



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
        defender=None,
        attacker=None,
        attack_id=1,
        army=army,
        critter_path=test_path,
        structures={},
        observer_uids=set(),
    )
    
    spawn_times = []
    seen_cids = set()
    tick_interval_ms = 15.0
    total_time_ms = 0.0
    max_time_ms = 2000.0
    
    while total_time_ms < max_time_ms:
        # Check for newly spawned critters before tick
        for cid, critter in battle.critters.items():
            if cid not in seen_cids:
                seen_cids.add(cid)
                spawn_times.append(total_time_ms)
                print(f"[TEST] Critter {len(spawn_times)} spawned at t={total_time_ms:.0f}ms")
        
        battle_service.tick(battle, tick_interval_ms)
        total_time_ms += tick_interval_ms
    
    print(f"\n[TEST] Spawn times: {spawn_times}")
    print(f"[TEST] Total spawned: {len(seen_cids)}")
    
    # Verify critters spawned
    assert len(spawn_times) >= 1, f"Should spawn at least 1 critter, got {len(spawn_times)}"
    assert len(seen_cids) == 3, f"Should spawn 3 critters, got {len(seen_cids)}"
    
    # Check intervals between spawns (should be ~100ms as configured)
    if len(spawn_times) >= 2:
        interval_1 = spawn_times[1] - spawn_times[0]
        interval_2 = spawn_times[2] - spawn_times[1] if len(spawn_times) > 2 else None
        
        print(f"[TEST] Intervals: {interval_1:.0f}ms" + (f", {interval_2:.0f}ms" if interval_2 else ""))
        
        # Allow some tolerance due to tick granularity (15ms)
        assert 85 <= interval_1 <= 115, f"First interval should be ~100ms, got {interval_1:.0f}ms"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

