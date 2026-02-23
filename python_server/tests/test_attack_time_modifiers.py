"""Tests for travel- and siege-time offsets.

Effects tested:
  TRAVEL_TIME_OFFSET  – attacker effect; added to base travel time.
                        Negative value = faster travel.
                        Formula: eta = max(1, base + offset)

  SIEGE_TIME_OFFSET   – defender effect; added to base siege time.
                        Positive value = longer siege.
                        Formula: siege = max(1, base + offset)
"""

import pytest
from gameserver.engine.attack_service import AttackService
from gameserver.engine.empire_service import EmpireService
from gameserver.engine.upgrade_provider import UpgradeProvider
from gameserver.loaders.game_config_loader import GameConfig
from gameserver.models.army import Army, CritterWave
from gameserver.models.empire import Empire
from gameserver.util import effects as fx
from gameserver.util.events import EventBus

ATTACKER_UID = 1
DEFENDER_UID = 2
BASE_TRAVEL = 100.0   # seconds
BASE_SIEGE  = 30.0    # seconds


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def svc():
    """Minimal services with two registered empires and configurable effects."""
    event_bus = EventBus()
    upgrade_provider = UpgradeProvider()
    gc = GameConfig()
    gc.base_travel_offset = BASE_TRAVEL
    gc.base_siege_offset = BASE_SIEGE
    empire_service = EmpireService(upgrade_provider, event_bus, gc)
    attack_service = AttackService(event_bus, gc, empire_service)

    attacker = Empire(uid=ATTACKER_UID, name="Attacker")
    defender = Empire(uid=DEFENDER_UID, name="Defender")
    empire_service.register(attacker)
    empire_service.register(defender)

    return attack_service, empire_service


def _make_army(uid: int, aid: int = 1) -> Army:
    """Return a minimal army with one wave, ready to start an attack."""
    wave = CritterWave(
        wave_id=1,
        iid="soldier",
        slots=1,
        num_critters_spawned=0,
        next_critter_ms=0,
    )
    return Army(aid=aid, uid=uid, name="Test Army", waves=[wave])


def _start(svc_tuple, attacker_uid=ATTACKER_UID, defender_uid=DEFENDER_UID, aid=1):
    """Helper: register army on attacker and call start_attack."""
    attack_service, empire_service = svc_tuple
    attacker = empire_service.get(attacker_uid)
    attacker.armies = [_make_army(attacker_uid, aid)]
    result = attack_service.start_attack(attacker_uid, defender_uid, aid, empire_service)
    return result


# ===========================================================================
# Travel-time modifier tests
# ===========================================================================

class TestTravelTimeModifiers:
    def test_base_travel_time_no_effects(self, svc):
        """No effects → ETA equals base travel time."""
        attack = _start(svc)
        assert attack.eta_seconds == pytest.approx(BASE_TRAVEL)

    def test_attacker_offset_reduces_eta(self, svc):
        """Negative TRAVEL_TIME_OFFSET on attacker shortens travel time."""
        attack_service, empire_service = svc
        empire_service.get(ATTACKER_UID).effects[fx.TRAVEL_TIME_OFFSET] = -20.0

        attack = _start(svc)
        # 100 + (-20) = 80
        assert attack.eta_seconds == pytest.approx(80.0)

    def test_attacker_offset_increases_eta(self, svc):
        """Positive TRAVEL_TIME_OFFSET on attacker lengthens travel time."""
        attack_service, empire_service = svc
        empire_service.get(ATTACKER_UID).effects[fx.TRAVEL_TIME_OFFSET] = 15.0

        attack = _start(svc)
        # 100 + 15 = 115
        assert attack.eta_seconds == pytest.approx(115.0)

    def test_attacker_offset_clamped_to_one(self, svc):
        """ETA is clamped to minimum 1.0 s even with large negative offset."""
        attack_service, empire_service = svc
        empire_service.get(ATTACKER_UID).effects[fx.TRAVEL_TIME_OFFSET] = -500.0

        attack = _start(svc)
        assert attack.eta_seconds == pytest.approx(1.0)

    def test_defender_offset_does_not_affect_travel(self, svc):
        """TRAVEL_TIME_OFFSET on the *defender* has no effect on ETA."""
        attack_service, empire_service = svc
        empire_service.get(DEFENDER_UID).effects[fx.TRAVEL_TIME_OFFSET] = -50.0

        attack = _start(svc)
        assert attack.eta_seconds == pytest.approx(BASE_TRAVEL)


# ===========================================================================
# Siege-time modifier tests
# ===========================================================================

class TestSiegeTimeModifiers:
    def test_base_siege_time_no_effects(self, svc):
        """No effects → siege equals base siege time."""
        attack_service, _ = svc
        duration = attack_service._calculate_siege_duration(ATTACKER_UID, DEFENDER_UID)
        assert duration == pytest.approx(BASE_SIEGE)

    def test_defender_offset_increases_duration(self, svc):
        """Positive SIEGE_TIME_OFFSET on defender lengthens siege."""
        attack_service, empire_service = svc
        empire_service.get(DEFENDER_UID).effects[fx.SIEGE_TIME_OFFSET] = 15.0

        duration = attack_service._calculate_siege_duration(ATTACKER_UID, DEFENDER_UID)
        # 30 + 15 = 45
        assert duration == pytest.approx(45.0)

    def test_defender_offset_reduces_duration(self, svc):
        """Negative SIEGE_TIME_OFFSET on defender shortens siege."""
        attack_service, empire_service = svc
        empire_service.get(DEFENDER_UID).effects[fx.SIEGE_TIME_OFFSET] = -15.0

        duration = attack_service._calculate_siege_duration(ATTACKER_UID, DEFENDER_UID)
        # 30 - 15 = 15
        assert duration == pytest.approx(15.0)

    def test_siege_clamped_to_one(self, svc):
        """Siege duration is clamped to minimum 1.0 s."""
        attack_service, empire_service = svc
        empire_service.get(DEFENDER_UID).effects[fx.SIEGE_TIME_OFFSET] = -500.0

        duration = attack_service._calculate_siege_duration(ATTACKER_UID, DEFENDER_UID)
        assert duration == pytest.approx(1.0)

    def test_attacker_offset_does_not_affect_siege(self, svc):
        """SIEGE_TIME_OFFSET on the *attacker* has no effect on siege duration."""
        attack_service, empire_service = svc
        empire_service.get(ATTACKER_UID).effects[fx.SIEGE_TIME_OFFSET] = 300.0

        duration = attack_service._calculate_siege_duration(ATTACKER_UID, DEFENDER_UID)
        assert duration == pytest.approx(BASE_SIEGE)

    def test_unknown_attacker_siege_uses_base(self, svc):
        """If attacker UID is unknown, base siege time is used."""
        attack_service, _ = svc
        duration = attack_service._calculate_siege_duration(9999, DEFENDER_UID)
        assert duration == pytest.approx(BASE_SIEGE)

    def test_unknown_defender_siege_uses_base(self, svc):
        """If defender UID is unknown, base siege time is used."""
        attack_service, _ = svc
        duration = attack_service._calculate_siege_duration(ATTACKER_UID, 9999)
        assert duration == pytest.approx(BASE_SIEGE)
