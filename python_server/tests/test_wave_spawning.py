"""Tests for wave spawning."""

import pytest
from gameserver.models.army import Army, CritterWave
from gameserver.models.critter import Critter
from gameserver.models.hex import HexCoord
from gameserver.models.map import Direction


def _make_wave(num_critters: int = 5, interval_ms: float = 500) -> CritterWave:
    critters = [
        Critter(
            cid=i, iid="goblin", health=10, max_health=10,
            speed=2, armour=0, path=[HexCoord(q, 0) for q in range(10)],
        )
        for i in range(num_critters)
    ]
    return CritterWave(
        critter_iid="goblin", slots=num_critters,
        critters=critters, spawn_interval_ms=interval_ms,
    )


class TestCritterWave:
    def test_initial_state(self):
        w = _make_wave(5)
        assert w.spawn_pointer == 0
        assert not w.is_dispatched

    def test_dispatched_after_all_spawned(self):
        w = _make_wave(3)
        w.spawn_pointer = 3
        assert w.is_dispatched

    def test_not_dispatched_partially(self):
        w = _make_wave(3)
        w.spawn_pointer = 2
        assert not w.is_dispatched


class TestArmy:
    def test_initial_wave_delay(self):
        army = Army(aid=1, uid=100, direction=Direction.NORTH)
        assert army.next_wave_ms == pytest.approx(25_000.0)

    def test_finished_with_no_waves(self):
        army = Army(aid=1, uid=100, direction=Direction.NORTH, waves=[])
        assert army.is_finished

    def test_not_finished_with_active_waves(self):
        army = Army(
            aid=1, uid=100, direction=Direction.NORTH,
            waves=[_make_wave(3)],
        )
        assert not army.is_finished

    def test_finished_when_last_dispatched(self):
        w = _make_wave(3)
        w.spawn_pointer = 3
        army = Army(aid=1, uid=100, direction=Direction.NORTH, waves=[w])
        assert army.is_finished
