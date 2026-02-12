"""Test that IN_BATTLE attacks loaded from persisted state trigger correctly."""

import pytest
from unittest.mock import MagicMock, patch
import asyncio

from gameserver.engine.attack_service import AttackService
from gameserver.models.attack import Attack, AttackPhase
from gameserver.models.army import Army, CritterWave
from gameserver.models.empire import Empire
from gameserver.util.events import EventBus, BattleStartRequested


@pytest.mark.asyncio
async def test_restored_in_battle_attack_triggers_battle_start() -> None:
    """When an attack is loaded from persistent state with phase=IN_BATTLE,
    it should return the attack object on first step() to signal battle should start."""
    
    # Create event bus
    event_bus = EventBus()
    
    # Create attack service
    attack_svc = AttackService(event_bus=event_bus)
    
    # Create a persisted attack that was already IN_BATTLE
    # (simulating state loaded from YAML)
    persisted_attack = Attack(
        attack_id=42,
        attacker_uid=100,
        defender_uid=2,
        army_aid=1,
        phase=AttackPhase.IN_BATTLE,  # <-- Already in battle!
        eta_seconds=0.0,
        total_eta_seconds=0.0,
        siege_remaining_seconds=0.0,
        total_siege_seconds=0.0,
        wave_pointer=0,
        critter_pointer=0,
        next_wave_ms=5000.0,
    )
    
    # Add to attack service (simulating load from state file)
    attack_svc._attacks.append(persisted_attack)
    
    # Step should recognize this is in battle and return the attack
    result = attack_svc.step(persisted_attack, dt=0.016)
    
    # Should return the attack (indicating battle should start)
    assert result is not None
    assert result.attack_id == 42
    assert result.phase == AttackPhase.IN_BATTLE
    assert 42 in attack_svc._battles_started  # Flag is set


@pytest.mark.asyncio
async def test_restored_in_battle_attack_does_not_trigger_twice() -> None:
    """Returned attack (battle start signal) should only happen once, even if step() is called multiple times."""
    
    # Create event bus
    event_bus = EventBus()
    
    # Create attack service
    attack_svc = AttackService(event_bus=event_bus)
    
    # Create a persisted attack in IN_BATTLE
    persisted_attack = Attack(
        attack_id=42,
        attacker_uid=100,
        defender_uid=2,
        army_aid=1,
        phase=AttackPhase.IN_BATTLE,
        eta_seconds=0.0,
        total_eta_seconds=0.0,
        siege_remaining_seconds=0.0,
        total_siege_seconds=0.0,
        wave_pointer=0,
        critter_pointer=0,
        next_wave_ms=5000.0,
    )
    
    attack_svc._attacks.append(persisted_attack)
    
    # First step should return attack (battle start signal)
    result1 = attack_svc.step(persisted_attack, dt=0.016)
    assert result1 is not None
    assert 42 in attack_svc._battles_started
    
    # Second step should NOT return attack (already started)
    result2 = attack_svc.step(persisted_attack, dt=0.016)
    assert result2 is None  # Already started, no second signal
    
    # Third step should also not return
    result3 = attack_svc.step(persisted_attack, dt=0.016)
    assert result3 is None


@pytest.mark.asyncio
async def test_normal_transition_to_in_battle_still_works() -> None:
    """Ensure normal SIEGE->IN_BATTLE transition still works correctly."""
    
    # Create event bus
    event_bus = EventBus()
    
    # Track emitted events
    phase_changed_events = []
    
    def capture_phase_event(event):
        phase_changed_events.append(event)
    
    from gameserver.util.events import AttackPhaseChanged
    event_bus.on(AttackPhaseChanged, capture_phase_event)
    
    # Create attack service
    attack_svc = AttackService(event_bus=event_bus)
    
    # Create an attack in IN_SIEGE phase
    attack = Attack(
        attack_id=43,
        attacker_uid=100,
        defender_uid=2,
        army_aid=1,
        phase=AttackPhase.IN_SIEGE,
        eta_seconds=0.0,
        total_eta_seconds=0.0,
        siege_remaining_seconds=1.0,  # 1 second remaining
        total_siege_seconds=30.0,
        wave_pointer=0,
        critter_pointer=0,
        next_wave_ms=25000.0,
    )
    
    attack_svc._attacks.append(attack)
    
    # Step with less remaining time
    result = attack_svc.step(attack, dt=0.5)
    
    # Should still be in siege (only 0.5s of 1.0s has passed)
    assert attack.phase == AttackPhase.IN_SIEGE
    assert attack.siege_remaining_seconds == 0.5
    assert result is None
    assert len(phase_changed_events) == 0
    
    # Step again with more than remaining time
    result = attack_svc.step(attack, dt=1.0)
    
    # Should have transitioned to IN_BATTLE
    assert attack.phase == AttackPhase.IN_BATTLE
    assert attack.siege_remaining_seconds == 0.0
    assert result is attack  # Should return the attack for battle start
    assert len(phase_changed_events) == 1  # Phase change event emitted
    assert phase_changed_events[0].new_phase == "in_battle"
    assert 43 in attack_svc._battles_started  # Battle marked as started
