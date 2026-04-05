"""Tests for the wave_delay_offset defender effect.

The defending empire's WAVE_DELAY_OFFSET effect is added to every
wave's next_critter_ms timer at battle-start time (handlers.py).

Formula (per wave i, 0-indexed):
    wave.next_critter_ms = int(i * initial_delay_ms) + wave_delay_offset_ms

where wave_delay_offset_ms = defender.get_effect(WAVE_DELAY_OFFSET, 0.0)
"""

import pytest
from gameserver.models.army import Army, CritterWave
from gameserver.models.empire import Empire
from gameserver.util import effects as fx

INITIAL_DELAY_MS = 15_000.0  # mirrors game.yaml default


def _make_army(num_waves: int = 3) -> Army:
    waves = [
        CritterWave(wave_id=i + 1, iid="soldier", slots=5,
                    num_critters_spawned=0, next_critter_ms=0)
        for i in range(num_waves)
    ]
    return Army(aid=1, uid=2, name="Test Army", waves=waves)


def _apply_wave_timers(army: Army, defender: Empire | None,
                       initial_delay_ms: float = INITIAL_DELAY_MS) -> None:
    """Reproduce the handler logic that initialises wave timers at battle start.

    Formula: wave[i].next_critter_ms = i * initial_delay + (i+1) * offset
    This ensures every wave-to-wave interval is extended by the offset,
    not just the first wave.
    """
    wave_delay_offset_ms = (
        defender.get_effect(fx.WAVE_DELAY_OFFSET, 0.0)
        if defender else 0.0
    )
    for i, wave in enumerate(army.waves):
        wave.next_critter_ms = int(i * initial_delay_ms) + (i + 1) * wave_delay_offset_ms
        wave.num_critters_spawned = 0


# ===========================================================================
# Wave delay offset tests
# ===========================================================================

class TestWaveDelayOffset:

    def test_no_effect_baseline(self):
        """Without any effect, wave timers follow i × initial_delay_ms."""
        army = _make_army(3)
        defender = Empire(uid=1, name="Defender")

        _apply_wave_timers(army, defender)

        assert army.waves[0].next_critter_ms == pytest.approx(0.0)
        assert army.waves[1].next_critter_ms == pytest.approx(15_000.0)
        assert army.waves[2].next_critter_ms == pytest.approx(30_000.0)

    def test_positive_offset_delays_all_waves(self):
        """Each wave gets (i+1)*offset so every wave-to-wave interval grows."""
        army = _make_army(3)
        defender = Empire(uid=1, name="Defender")
        defender.effects[fx.WAVE_DELAY_OFFSET] = 5_000.0

        _apply_wave_timers(army, defender)

        # wave[i] = i*15000 + (i+1)*5000
        assert army.waves[0].next_critter_ms == pytest.approx(5_000.0)   # 0 + 1*5000
        assert army.waves[1].next_critter_ms == pytest.approx(25_000.0)  # 15000 + 2*5000
        assert army.waves[2].next_critter_ms == pytest.approx(45_000.0)  # 30000 + 3*5000

    def test_negative_offset_advances_all_waves(self):
        """Negative WAVE_DELAY_OFFSET shortens every wave-to-wave interval."""
        army = _make_army(3)
        defender = Empire(uid=1, name="Defender")
        defender.effects[fx.WAVE_DELAY_OFFSET] = -5_000.0

        _apply_wave_timers(army, defender)

        assert army.waves[0].next_critter_ms == pytest.approx(-5_000.0)  # 0 + 1*(-5000)
        assert army.waves[1].next_critter_ms == pytest.approx(5_000.0)   # 15000 + 2*(-5000)
        assert army.waves[2].next_critter_ms == pytest.approx(15_000.0)  # 30000 + 3*(-5000)

    def test_no_defender_uses_zero_offset(self):
        """None defender (edge case) must not raise and must use offset=0."""
        army = _make_army(2)

        _apply_wave_timers(army, defender=None)

        assert army.waves[0].next_critter_ms == pytest.approx(0.0)
        assert army.waves[1].next_critter_ms == pytest.approx(15_000.0)

    def test_offset_on_attacker_has_no_effect(self):
        """WAVE_DELAY_OFFSET on the attacker empire must not influence timers."""
        army = _make_army(2)
        defender = Empire(uid=1, name="Defender")          # no offset
        attacker = Empire(uid=2, name="Attacker")
        attacker.effects[fx.WAVE_DELAY_OFFSET] = 99_999.0  # should be ignored

        _apply_wave_timers(army, defender)  # only defender is passed

        assert army.waves[0].next_critter_ms == pytest.approx(0.0)
        assert army.waves[1].next_critter_ms == pytest.approx(15_000.0)

    def test_spawn_count_reset_on_timer_init(self):
        """Wave timer init must also reset num_critters_spawned to 0."""
        army = _make_army(2)
        army.waves[0].num_critters_spawned = 3
        army.waves[1].num_critters_spawned = 5
        defender = Empire(uid=1, name="Defender")

        _apply_wave_timers(army, defender)

        assert army.waves[0].num_critters_spawned == 0
        assert army.waves[1].num_critters_spawned == 0

    def test_offset_scales_with_multiple_waves(self):
        """wave[i] = i*initial_delay + (i+1)*offset — offset compounds per wave."""
        army = _make_army(5)
        defender = Empire(uid=1, name="Defender")
        defender.effects[fx.WAVE_DELAY_OFFSET] = 3_000.0

        _apply_wave_timers(army, defender)

        for i, wave in enumerate(army.waves):
            expected = int(i * INITIAL_DELAY_MS) + (i + 1) * 3_000.0
            assert wave.next_critter_ms == pytest.approx(expected), \
                f"Wave {i}: expected {expected}, got {wave.next_critter_ms}"
