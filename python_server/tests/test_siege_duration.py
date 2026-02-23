"""Test siege duration calculation based on defender effects."""

import pytest
from gameserver.engine.attack_service import AttackService
from gameserver.engine.empire_service import EmpireService
from gameserver.engine.upgrade_provider import UpgradeProvider
from gameserver.loaders.game_config_loader import GameConfig
from gameserver.models.empire import Empire
from gameserver.util.events import EventBus
from gameserver.util import effects


ATTACKER_UID = 1
DEFENDER_UID = 100


@pytest.fixture
def services():
    """Create minimal services for testing."""
    event_bus = EventBus()
    upgrade_provider = UpgradeProvider()
    gc = GameConfig()
    gc.base_siege_offset = 30.0
    empire_service = EmpireService(upgrade_provider, event_bus, gc)
    attack_service = AttackService(event_bus, gc, empire_service)
    # Register a plain attacker empire (no effects) used by all tests
    attacker = Empire(uid=ATTACKER_UID, name="Attacker")
    empire_service.register(attacker)
    return attack_service, empire_service


def test_siege_duration_default_no_effects(services):
    """Siege duration with no defender effects should use base value."""
    attack_service, empire_service = services

    defender = Empire(uid=DEFENDER_UID, name="Defender")
    empire_service.register(defender)

    duration = attack_service._calculate_siege_duration(ATTACKER_UID, DEFENDER_UID)

    # Should be base value (30.0 + 30.0 * 0.0 = 30.0)
    assert duration == 30.0


def test_siege_duration_with_modifier_only(services):
    """Siege duration with positive SIEGE_TIME_OFFSET (additive)."""
    attack_service, empire_service = services

    defender = Empire(uid=DEFENDER_UID, name="Defender")
    defender.effects[effects.SIEGE_TIME_OFFSET] = 15.0
    empire_service.register(defender)

    # 30 + 15 = 45
    duration = attack_service._calculate_siege_duration(ATTACKER_UID, DEFENDER_UID)
    assert duration == 45.0


def test_siege_duration_with_doubled_modifier(services):
    """Siege duration when SIEGE_TIME_OFFSET equals the base (doubles it)."""
    attack_service, empire_service = services

    defender = Empire(uid=DEFENDER_UID, name="Defender")
    defender.effects[effects.SIEGE_TIME_OFFSET] = 30.0  # same as base
    empire_service.register(defender)

    # 30 + 30 = 60
    duration = attack_service._calculate_siege_duration(ATTACKER_UID, DEFENDER_UID)
    assert duration == 60.0


def test_siege_duration_with_negative_modifier(services):
    """Siege duration with negative SIEGE_TIME_OFFSET (faster siege)."""
    attack_service, empire_service = services

    defender = Empire(uid=DEFENDER_UID, name="Defender")
    defender.effects[effects.SIEGE_TIME_OFFSET] = -9.0
    empire_service.register(defender)

    # 30 - 9 = 21
    duration = attack_service._calculate_siege_duration(ATTACKER_UID, DEFENDER_UID)
    assert duration == 21.0


def test_siege_duration_nonexistent_defender(services):
    """Siege duration for nonexistent defender should fall back to base value."""
    attack_service, empire_service = services

    duration = attack_service._calculate_siege_duration(ATTACKER_UID, 999)

    assert duration == 30.0
