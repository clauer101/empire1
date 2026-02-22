"""Tests for directional travel- and siege-time modifiers.

Effects tested:
  outgoing_travel_time_offset  – attacker effect, subtracted from travel time
  incoming_travel_time_offset  – defender effect, added to travel time
  outgoing_siege_time_offset   – attacker effect, subtracted from siege time
  incoming_siege_time_offset   – defender effect, added to siege time

All values are in seconds.
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
BASE_SIEGE = 30.0     # seconds


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
        assert attack.eta_seconds == BASE_TRAVEL

    def test_outgoing_travel_reduces_eta(self, svc):
        """outgoing_travel_time_offset on attacker shortens travel time."""
        attack_service, empire_service = svc
        empire_service.get(ATTACKER_UID).effects[fx.OUTGOING_TRAVEL_TIME_OFFSET] = 20.0

        attack = _start(svc)
        # 100 - 20 = 80
        assert attack.eta_seconds == pytest.approx(80.0)

    def test_incoming_travel_increases_eta(self, svc):
        """incoming_travel_time_offset on defender lengthens travel time."""
        attack_service, empire_service = svc
        empire_service.get(DEFENDER_UID).effects[fx.INCOMING_TRAVEL_TIME_OFFSET] = 15.0

        attack = _start(svc)
        # 100 + 15 = 115
        assert attack.eta_seconds == pytest.approx(115.0)

    def test_both_travel_offsets_combined(self, svc):
        """outgoing and incoming offsets applied together."""
        attack_service, empire_service = svc
        empire_service.get(ATTACKER_UID).effects[fx.OUTGOING_TRAVEL_TIME_OFFSET] = 30.0
        empire_service.get(DEFENDER_UID).effects[fx.INCOMING_TRAVEL_TIME_OFFSET] = 10.0

        attack = _start(svc)
        # 100 - 30 + 10 = 80
        assert attack.eta_seconds == pytest.approx(80.0)

    def test_outgoing_larger_than_base_clamped_to_one(self, svc):
        """ETA is clamped to minimum 1.0 s even when offset exceeds base."""
        attack_service, empire_service = svc
        empire_service.get(ATTACKER_UID).effects[fx.OUTGOING_TRAVEL_TIME_OFFSET] = 500.0

        attack = _start(svc)
        assert attack.eta_seconds == pytest.approx(1.0)

    def test_outgoing_travel_does_not_affect_defender_empire(self, svc):
        """outgoing_travel_time_offset on the *defender* has no effect."""
        attack_service, empire_service = svc
        # Wrong empire — should be ignored
        empire_service.get(DEFENDER_UID).effects[fx.OUTGOING_TRAVEL_TIME_OFFSET] = 50.0

        attack = _start(svc)
        assert attack.eta_seconds == pytest.approx(BASE_TRAVEL)

    def test_incoming_travel_does_not_affect_attacker_empire(self, svc):
        """incoming_travel_time_offset on the *attacker* has no effect."""
        attack_service, empire_service = svc
        empire_service.get(ATTACKER_UID).effects[fx.INCOMING_TRAVEL_TIME_OFFSET] = 50.0

        attack = _start(svc)
        assert attack.eta_seconds == pytest.approx(BASE_TRAVEL)


# ===========================================================================
# Siege-time modifier tests
# ===========================================================================

class TestSiegeTimeModifiers:
    def test_base_siege_time_no_directional_effects(self, svc):
        """No directional effects → siege equals base siege time."""
        attack_service, _ = svc
        duration = attack_service._calculate_siege_duration(ATTACKER_UID, DEFENDER_UID)
        assert duration == pytest.approx(BASE_SIEGE)

    def test_outgoing_siege_reduces_duration(self, svc):
        """outgoing_siege_time_offset on attacker shortens siege."""
        attack_service, empire_service = svc
        empire_service.get(ATTACKER_UID).effects[fx.OUTGOING_SIEGE_TIME_OFFSET] = 10.0

        duration = attack_service._calculate_siege_duration(ATTACKER_UID, DEFENDER_UID)
        # 30 - 10 = 20
        assert duration == pytest.approx(20.0)

    def test_incoming_siege_increases_duration(self, svc):
        """incoming_siege_time_offset on defender lengthens siege."""
        attack_service, empire_service = svc
        empire_service.get(DEFENDER_UID).effects[fx.INCOMING_SIEGE_TIME_OFFSET] = 12.0

        duration = attack_service._calculate_siege_duration(ATTACKER_UID, DEFENDER_UID)
        # 30 + 12 = 42
        assert duration == pytest.approx(42.0)

    def test_both_siege_offsets_combined(self, svc):
        """outgoing and incoming siege offsets applied together."""
        attack_service, empire_service = svc
        empire_service.get(ATTACKER_UID).effects[fx.OUTGOING_SIEGE_TIME_OFFSET] = 8.0
        empire_service.get(DEFENDER_UID).effects[fx.INCOMING_SIEGE_TIME_OFFSET] = 5.0

        duration = attack_service._calculate_siege_duration(ATTACKER_UID, DEFENDER_UID)
        # 30 - 8 + 5 = 27
        assert duration == pytest.approx(27.0)

    def test_directional_offsets_combine_with_existing_modifier(self, svc):
        """Directional offsets stack correctly with SIEGE_TIME_OFFSET + MODIFIER."""
        attack_service, empire_service = svc
        # Existing effects on defender
        empire_service.get(DEFENDER_UID).effects[fx.SIEGE_TIME_OFFSET] = 40.0
        empire_service.get(DEFENDER_UID).effects[fx.SIEGE_TIME_MODIFIER] = 0.5  # +50%
        # Directional effects
        empire_service.get(ATTACKER_UID).effects[fx.OUTGOING_SIEGE_TIME_OFFSET] = 5.0
        empire_service.get(DEFENDER_UID).effects[fx.INCOMING_SIEGE_TIME_OFFSET] = 3.0

        duration = attack_service._calculate_siege_duration(ATTACKER_UID, DEFENDER_UID)
        # base = 40 + 40*0.5 = 60; directional: 60 - 5 + 3 = 58
        assert duration == pytest.approx(58.0)

    def test_outgoing_siege_clamped_to_one(self, svc):
        """Siege duration is clamped to minimum 1.0 s."""
        attack_service, empire_service = svc
        empire_service.get(ATTACKER_UID).effects[fx.OUTGOING_SIEGE_TIME_OFFSET] = 1000.0

        duration = attack_service._calculate_siege_duration(ATTACKER_UID, DEFENDER_UID)
        assert duration == pytest.approx(1.0)

    def test_outgoing_siege_on_defender_has_no_effect(self, svc):
        """outgoing_siege_time_offset on the *defender* is ignored."""
        attack_service, empire_service = svc
        empire_service.get(DEFENDER_UID).effects[fx.OUTGOING_SIEGE_TIME_OFFSET] = 50.0

        duration = attack_service._calculate_siege_duration(ATTACKER_UID, DEFENDER_UID)
        assert duration == pytest.approx(BASE_SIEGE)

    def test_incoming_siege_on_attacker_has_no_effect(self, svc):
        """incoming_siege_time_offset on the *attacker* is ignored."""
        attack_service, empire_service = svc
        empire_service.get(ATTACKER_UID).effects[fx.INCOMING_SIEGE_TIME_OFFSET] = 50.0

        duration = attack_service._calculate_siege_duration(ATTACKER_UID, DEFENDER_UID)
        assert duration == pytest.approx(BASE_SIEGE)

    def test_unknown_attacker_siege_uses_base(self, svc):
        """If attacker UID is unknown, outgoing adjustment is skipped gracefully."""
        attack_service, empire_service = svc
        duration = attack_service._calculate_siege_duration(9999, DEFENDER_UID)
        assert duration == pytest.approx(BASE_SIEGE)
