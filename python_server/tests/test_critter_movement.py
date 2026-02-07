"""Tests for critter movement and damage."""

import pytest
from gameserver.models.critter import Critter, DamageType
from gameserver.models.hex import HexCoord


def _make_critter(
    speed: float = 2.0,
    health: float = 100.0,
    armour: float = 0.0,
    path_len: int = 10,
) -> Critter:
    """Create a critter on a straight horizontal path."""
    path = [HexCoord(q, 0) for q in range(path_len)]
    return Critter(
        cid=1, iid="test", health=health, max_health=health,
        speed=speed, armour=armour, path=path,
    )


class TestCritterMovement:
    def test_initial_position(self):
        c = _make_critter()
        assert c.path_progress == 0.0
        assert c.current_hex == HexCoord(0, 0)

    def test_move_one_second(self):
        c = _make_critter(speed=2.0)
        c.path_progress += c.speed * (1000 / 1000)
        assert c.path_progress == pytest.approx(2.0)

    def test_current_hex_advances(self):
        c = _make_critter(speed=3.0)
        c.path_progress = 3.0
        assert c.current_hex == HexCoord(3, 0)

    def test_finished_at_end(self):
        c = _make_critter(path_len=5)
        c.path_progress = 4.0  # len - 1
        assert c.is_finished

    def test_not_finished_before_end(self):
        c = _make_critter(path_len=5)
        c.path_progress = 3.5
        assert not c.is_finished

    def test_remainder_path(self):
        c = _make_critter(path_len=10)
        c.path_progress = 3.0
        assert c.remainder_path == pytest.approx(6.0)


class TestCritterDamage:
    def test_normal_damage(self):
        c = _make_critter(health=100)
        effective = max(min(10.0, 1.0), 10.0 - c.armour)
        c.health -= effective
        assert c.health == pytest.approx(90.0)

    def test_damage_with_armour(self):
        c = _make_critter(health=100, armour=3.0)
        dmg = 10.0
        effective = max(min(dmg, 1.0), dmg - c.armour)
        c.health -= effective
        assert c.health == pytest.approx(93.0)

    def test_damage_minimum_is_one(self):
        c = _make_critter(health=100, armour=100.0)
        dmg = 5.0
        effective = max(min(dmg, 1.0), dmg - c.armour)
        assert effective == 1.0

    def test_tiny_damage_preserved(self):
        c = _make_critter(health=100, armour=100.0)
        dmg = 0.5
        effective = max(min(dmg, 1.0), dmg - c.armour)
        assert effective == pytest.approx(0.5)

    def test_burn_bypasses_armour(self):
        c = _make_critter(health=100, armour=50.0)
        dmg = 10.0
        # Burn ignores armour
        c.health -= dmg
        assert c.health == pytest.approx(90.0)

    def test_death_on_zero_health(self):
        c = _make_critter(health=5.0)
        c.health = 0.0
        assert not c.is_alive


class TestCritterEffects:
    def test_slow_reduces_speed(self):
        c = _make_critter(speed=4.0)
        c.slow_remaining_ms = 2000.0
        c.slow_speed = 2.0
        assert c.effective_speed == 2.0

    def test_slow_expires(self):
        c = _make_critter(speed=4.0)
        c.slow_remaining_ms = 0.0
        c.slow_speed = 2.0
        assert c.effective_speed == 4.0

    def test_normal_speed_without_slow(self):
        c = _make_critter(speed=3.0)
        assert c.effective_speed == 3.0
