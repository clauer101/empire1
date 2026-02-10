"""Test siege duration calculation based on defender effects."""

import pytest
from gameserver.engine.attack_service import AttackService
from gameserver.engine.empire_service import EmpireService
from gameserver.engine.upgrade_provider import UpgradeProvider
from gameserver.loaders.game_config_loader import GameConfig
from gameserver.models.empire import Empire
from gameserver.util.events import EventBus
from gameserver.util import effects


@pytest.fixture
def services():
    """Create minimal services for testing."""
    event_bus = EventBus()
    upgrade_provider = UpgradeProvider()
    gc = GameConfig()
    gc.base_siege_offset = 30.0
    empire_service = EmpireService(upgrade_provider, event_bus, gc)
    attack_service = AttackService(event_bus, gc, empire_service)
    return attack_service, empire_service


def test_siege_duration_default_no_effects(services):
    """Siege duration with no defender effects should use base value."""
    attack_service, empire_service = services
    
    # Create defender with no effects
    defender = Empire(uid=100, name="Defender")
    empire_service.register(defender)
    
    # Calculate siege duration
    duration = attack_service._calculate_siege_duration(100)
    
    # Should be base value (30.0 + 30.0 * 0.0 = 30.0)
    assert duration == 30.0


def test_siege_duration_with_offset_only(services):
    """Siege duration with only SIEGE_TIME_OFFSET effect."""
    attack_service, empire_service = services
    
    # Create defender with SIEGE_TIME_OFFSET effect
    defender = Empire(uid=100, name="Defender")
    defender.effects[effects.SIEGE_TIME_OFFSET] = 45.0
    empire_service.register(defender)
    
    # Calculate siege duration: 45.0 + 45.0 * 0.0 = 45.0
    duration = attack_service._calculate_siege_duration(100)
    assert duration == 45.0


def test_siege_duration_with_offset_and_modifier(services):
    """Siege duration with both SIEGE_TIME_OFFSET and SIEGE_TIME_MODIFIER effects."""
    attack_service, empire_service = services
    
    # Create defender with both effects
    defender = Empire(uid=100, name="Defender")
    defender.effects[effects.SIEGE_TIME_OFFSET] = 40.0
    defender.effects[effects.SIEGE_TIME_MODIFIER] = 0.5  # +50%
    empire_service.register(defender)
    
    # Calculate: 40.0 + (40.0 * 0.5) = 40.0 + 20.0 = 60.0
    duration = attack_service._calculate_siege_duration(100)
    assert duration == 60.0


def test_siege_duration_with_negative_modifier(services):
    """Siege duration with negative SIEGE_TIME_MODIFIER (faster siege)."""
    attack_service, empire_service = services
    
    # Create defender with negative modifier
    defender = Empire(uid=100, name="Defender")
    defender.effects[effects.SIEGE_TIME_OFFSET] = 30.0
    defender.effects[effects.SIEGE_TIME_MODIFIER] = -0.3  # -30%
    empire_service.register(defender)
    
    # Calculate: 30.0 + (30.0 * -0.3) = 30.0 - 9.0 = 21.0
    duration = attack_service._calculate_siege_duration(100)
    assert duration == 21.0


def test_siege_duration_nonexistent_defender(services):
    """Siege duration for nonexistent defender should use base value."""
    attack_service, empire_service = services
    
    # Calculate for nonexistent defender
    duration = attack_service._calculate_siege_duration(999)
    
    # Should fall back to base value
    assert duration == 30.0
