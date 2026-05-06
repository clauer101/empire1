"""Tests for tower targeting via BattleService._find_target.

All range checks use hex_world_distance (continuous Euclidean) with
interpolated critter positions — not the old discrete distance_to.

Coordinate system: flat-top axial (q, r).
  1 unit = distance between two adjacent tile centers.
  All six neighbors of any tile are exactly 1.0 units away.
"""

from __future__ import annotations

import pytest

from gameserver.engine.battle_service import BattleService
from gameserver.models.battle import BattleState
from gameserver.models.critter import Critter
from gameserver.models.hex import HexCoord
from gameserver.models.structure import Structure


# ── Factories ────────────────────────────────────────────────────────────────


def _bs() -> BattleService:
    return BattleService()


def _battle(critters: dict[int, Critter]) -> BattleState:
    return BattleState(bid=0, defender=None, critters=critters)


def _tower(q: int = 0, r: int = 0, range_: float = 1.0, select: str = "first") -> Structure:
    return Structure(
        sid=1, iid="t",
        position=HexCoord(q, r),
        damage=1, range=range_, reload_time_ms=1000, shot_speed=5,
        select=select,
    )


def _critter(cid: int, path: list[HexCoord], progress: float = 0.0) -> Critter:
    return Critter(
        cid=cid, iid="c", health=10, max_health=10,
        speed=1, armour=0, path=path, path_progress=progress,
    )


def _path(*coords: tuple[int, int]) -> list[HexCoord]:
    return [HexCoord(q, r) for q, r in coords]


# ── range=1 covers exactly the six adjacent tiles ────────────────────────────


class TestRangeOne:
    def test_critter_at_adjacent_tile_is_in_range(self):
        """Critter sitting exactly at a neighbor tile center (dist=1.0) is targeted."""
        tower = _tower(0, 0, range_=1)
        critter = _critter(1, _path((1, 0)))
        assert _bs()._find_target(_battle({1: critter}), tower) is critter

    def test_all_six_neighbors_are_in_range(self):
        """Every one of the six hex neighbors is exactly 1.0 unit away → in range=1."""
        dirs = [(1, 0), (1, -1), (0, -1), (-1, 0), (-1, 1), (0, 1)]
        for dq, dr in dirs:
            tower = _tower(0, 0, range_=1)
            critter = _critter(1, _path((dq, dr)))
            result = _bs()._find_target(_battle({1: critter}), tower)
            assert result is critter, f"neighbor ({dq},{dr}) should be in range=1"

    def test_critter_on_same_tile_is_in_range(self):
        """Distance=0 is trivially within range=1."""
        tower = _tower(3, -1, range_=1)
        critter = _critter(1, _path((3, -1)))
        assert _bs()._find_target(_battle({1: critter}), tower) is critter

    def test_critter_two_tiles_away_is_not_in_range(self):
        tower = _tower(0, 0, range_=1)
        critter = _critter(1, _path((2, 0)))
        assert _bs()._find_target(_battle({1: critter}), tower) is None


# ── Float range (e.g. 1.5) must not be truncated ────────────────────────────


class TestFloatRange:
    def test_range_stored_as_float(self):
        """range=1.5 must not be truncated to 1 by any int() cast."""
        tower = _tower(0, 0, range_=1.5)
        assert tower.range == pytest.approx(1.5)

    def test_critter_at_1_4_units_is_in_range_1_5(self):
        """Critter at dist≈1.4 is well inside range=1.5."""
        # path (1,0)→(2,0), progress=0.4 → q=1.4, dist=1.4
        tower = _tower(0, 0, range_=1.5)
        critter = _critter(1, _path((1, 0), (2, 0)), progress=0.4)
        assert _bs()._find_target(_battle({1: critter}), tower) is critter

    def test_critter_at_1_6_units_is_not_in_range_1_5(self):
        """Critter at dist≈1.6 is outside range=1.5."""
        # progress=0.6 → q=1.6, dist=1.6
        tower = _tower(0, 0, range_=1.5)
        critter = _critter(1, _path((1, 0), (2, 0)), progress=0.6)
        assert _bs()._find_target(_battle({1: critter}), tower) is None

    def test_range_1_5_reaches_further_than_range_1(self):
        """A critter at dist≈1.3 is in range=1.5 but NOT in range=1.0."""
        # progress=0.3 on path (1,0)→(2,0) → q=1.3, dist=1.3
        critter = _critter(1, _path((1, 0), (2, 0)), progress=0.3)
        battle = _battle({1: critter})

        assert _bs()._find_target(battle, _tower(0, 0, range_=1.5)) is critter
        assert _bs()._find_target(battle, _tower(0, 0, range_=1.0)) is None


# ── Critter position is interpolated, not snapped to tile ───────────────────


class TestInterpolatedPosition:
    def test_critter_at_exact_boundary_in_range(self):
        """Critter interpolated to exactly 1.0 units from tower is in range=1."""
        # path (0,0)→(1,0)→(2,0), progress=0.5 → floatIdx=1.0 → q=1.0
        tower = _tower(0, 0, range_=1)
        critter = _critter(1, _path((0, 0), (1, 0), (2, 0)), progress=0.5)
        assert _bs()._find_target(_battle({1: critter}), tower) is critter

    def test_critter_just_past_boundary_not_in_range(self):
        """Critter at q=1.1 (10 % past the neighbor) is NOT in range=1."""
        # progress=0.55 → floatIdx=1.1 → q=1.1, dist=1.1
        tower = _tower(0, 0, range_=1)
        critter = _critter(1, _path((0, 0), (1, 0), (2, 0)), progress=0.55)
        assert _bs()._find_target(_battle({1: critter}), tower) is None

    def test_critter_approaching_transitions_in_to_out(self):
        """Same critter: in range when at q=0.8, out of range when at q=1.2."""
        tower = _tower(0, 0, range_=1)
        path = _path((0, 0), (1, 0), (2, 0))  # max_idx=2

        # progress=0.4 → floatIdx=0.8 → q=0.8, dist=0.8 → in range
        c_in = _critter(1, path, progress=0.4)
        assert _bs()._find_target(_battle({1: c_in}), tower) is c_in

        # progress=0.6 → floatIdx=1.2 → q=1.2, dist=1.2 → out of range
        c_out = _critter(1, path, progress=0.6)
        assert _bs()._find_target(_battle({1: c_out}), tower) is None


# ── Targeting strategies ─────────────────────────────────────────────────────


class TestTargetingStrategy:
    # Path: 9 tiles (0,0)→(8,0), tower at (5,0) range=2
    # A at q=4 (progress=4/8=0.5), B at q=6 (progress=6/8=0.75) — both dist=1 ≤ 2
    _PATH = [HexCoord(q, 0) for q in range(9)]

    def _two_critters(self, select: str):
        tower = _tower(5, 0, range_=2, select=select)
        ca = _critter(1, self._PATH, progress=4 / 8)  # less advanced
        cb = _critter(2, self._PATH, progress=6 / 8)  # more advanced
        return _battle({1: ca, 2: cb}), tower, ca, cb

    def test_first_selects_most_advanced(self):
        battle, tower, ca, cb = self._two_critters("first")
        assert _bs()._find_target(battle, tower) is cb

    def test_last_selects_least_advanced(self):
        battle, tower, ca, cb = self._two_critters("last")
        assert _bs()._find_target(battle, tower) is ca

    def test_no_critters_returns_none(self):
        tower = _tower(0, 0, range_=3)
        assert _bs()._find_target(_battle({}), tower) is None

    def test_critter_without_path_is_skipped(self):
        tower = _tower(0, 0, range_=5)
        critter = _critter(1, [], progress=0.0)
        assert _bs()._find_target(_battle({1: critter}), tower) is None

    def test_only_out_of_range_critters_returns_none(self):
        tower = _tower(0, 0, range_=1)
        critter = _critter(1, _path((5, 0)))  # dist=5 >> range=1
        assert _bs()._find_target(_battle({1: critter}), tower) is None
