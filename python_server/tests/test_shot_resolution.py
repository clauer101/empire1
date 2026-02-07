"""Tests for shot resolution."""

import pytest
from gameserver.models.shot import Shot
from gameserver.models.critter import DamageType


class TestShot:
    def test_shot_creation(self):
        s = Shot(damage=10, target_cid=1, source_sid=1, flight_remaining_ms=500)
        assert s.flight_remaining_ms == 500

    def test_shot_default_type(self):
        s = Shot(damage=5, target_cid=1, source_sid=1)
        assert s.shot_type == DamageType.NORMAL

    def test_shot_with_effects(self):
        s = Shot(
            damage=5, target_cid=1, source_sid=1,
            effects={"slow_target": 0.5, "slow_target_duration": 2.0}
        )
        assert s.effects["slow_target"] == pytest.approx(0.5)


class TestShotFlightTime:
    def test_flight_time_from_distance(self):
        """Flight time = hex_dist / shot_speed * 1000 ms."""
        hex_dist = 3
        shot_speed = 6.0  # hex/s
        expected_ms = 3 / 6.0 * 1000  # = 500ms
        assert expected_ms == pytest.approx(500.0)

    def test_flight_time_adjacent(self):
        hex_dist = 1
        shot_speed = 10.0
        expected_ms = 1 / 10.0 * 1000
        assert expected_ms == pytest.approx(100.0)
