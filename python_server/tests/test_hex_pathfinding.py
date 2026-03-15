"""Tests for hex_pathfinding: critter_hex_pos, hex_world_distance, and helpers."""

from __future__ import annotations

import math

import pytest

from gameserver.models.hex import HexCoord
from gameserver.engine.hex_pathfinding import (
    critter_hex_pos,
    hex_world_distance,
    validate_path,
    path_distance,
    sub_path_from,
    find_path_from_spawn_to_castle,
)


# ── Helpers ────────────────────────────────────────────────────────────────

def _hpath(*coords: tuple[int, int]) -> list[HexCoord]:
    return [HexCoord(q, r) for q, r in coords]

def _hline(length: int) -> list[HexCoord]:
    """Straight horizontal path: (0,0) → (length-1, 0)."""
    return [HexCoord(q, 0) for q in range(length)]


# ── critter_hex_pos ────────────────────────────────────────────────────────

class TestCritterHexPos:
    def test_at_start(self):
        path = _hline(5)
        q, r = critter_hex_pos(path, 0.0)
        assert q == pytest.approx(0.0)
        assert r == pytest.approx(0.0)

    def test_at_end(self):
        path = _hline(5)
        q, r = critter_hex_pos(path, 1.0)
        assert q == pytest.approx(4.0)
        assert r == pytest.approx(0.0)

    def test_midpoint_two_tile_path(self):
        path = _hpath((0, 0), (2, 0))
        q, r = critter_hex_pos(path, 0.5)
        assert q == pytest.approx(1.0)
        assert r == pytest.approx(0.0)

    def test_quarter_progress_five_tiles(self):
        path = _hline(5)     # q = 0..4
        q, r = critter_hex_pos(path, 0.25)
        assert q == pytest.approx(1.0)
        assert r == pytest.approx(0.0)

    def test_interpolates_between_tiles(self):
        path = _hpath((0, 0), (4, 0))   # two tiles, q-gap of 4
        q, r = critter_hex_pos(path, 0.5)
        # half-way → q=2.0
        assert q == pytest.approx(2.0)
        assert r == pytest.approx(0.0)

    def test_fractional_position_is_not_snapped(self):
        path = _hline(3)   # q in {0,1,2}
        q, r = critter_hex_pos(path, 0.3)
        # floatIdx = 0.3*2 = 0.6 → between tile 0 and tile 1, frac=0.6
        assert q == pytest.approx(0.6)
        assert r == pytest.approx(0.0)

    def test_r_coordinate_interpolated(self):
        path = _hpath((0, 0), (0, 4))
        q, r = critter_hex_pos(path, 0.75)
        assert q == pytest.approx(0.0)
        assert r == pytest.approx(3.0)

    def test_diagonal_path(self):
        path = _hpath((0, 0), (1, 0), (2, -1))
        q, r = critter_hex_pos(path, 0.5)
        # floatIdx = 0.5*2 = 1.0 → exactly tile index 1 → (1, 0)
        assert q == pytest.approx(1.0)
        assert r == pytest.approx(0.0)

    def test_empty_path_returns_origin(self):
        q, r = critter_hex_pos([], 0.5)
        assert (q, r) == (0.0, 0.0)

    def test_single_tile_path(self):
        path = [HexCoord(3, -2)]
        q, r = critter_hex_pos(path, 0.7)
        assert q == pytest.approx(3.0)
        assert r == pytest.approx(-2.0)

    def test_progress_clamped_at_one(self):
        path = _hline(5)
        q, _ = critter_hex_pos(path, 1.0)
        assert q == pytest.approx(4.0)

    def test_progress_zero_always_at_start(self):
        path = _hpath((5, 3), (6, 3), (7, 2))
        q, r = critter_hex_pos(path, 0.0)
        assert q == pytest.approx(5.0)
        assert r == pytest.approx(3.0)


# ── hex_world_distance ─────────────────────────────────────────────────────

class TestHexWorldDistance:
    def test_same_point_is_zero(self):
        assert hex_world_distance(0, 0, 0, 0) == pytest.approx(0.0)

    def test_east_neighbor_is_one(self):
        # E neighbor: (q+1, r)
        assert hex_world_distance(0, 0, 1, 0) == pytest.approx(1.0)

    def test_se_neighbor_is_one(self):
        # SE neighbor: (q, r+1)
        assert hex_world_distance(0, 0, 0, 1) == pytest.approx(1.0)

    def test_ne_neighbor_is_one(self):
        # NE neighbor: (q+1, r-1)
        assert hex_world_distance(0, 0, 1, -1) == pytest.approx(1.0)

    def test_all_six_neighbors_are_one(self):
        dirs = [(1, 0), (1, -1), (0, -1), (-1, 0), (-1, 1), (0, 1)]
        for dq, dr in dirs:
            d = hex_world_distance(0, 0, dq, dr)
            assert d == pytest.approx(1.0), f"neighbor ({dq},{dr}) gives distance {d}"

    def test_two_tiles_apart(self):
        assert hex_world_distance(0, 0, 2, 0) == pytest.approx(2.0)

    def test_three_tiles_apart(self):
        assert hex_world_distance(0, 0, 3, 0) == pytest.approx(3.0)

    def test_symmetric(self):
        assert hex_world_distance(1, 2, 4, -1) == pytest.approx(
            hex_world_distance(4, -1, 1, 2)
        )

    def test_float_position_between_neighbors(self):
        # Position exactly between (0,0) and (1,0) → distance 0.5 from origin
        d = hex_world_distance(0, 0, 0.5, 0)
        assert d == pytest.approx(0.5)

    def test_critter_vs_tower_sub_tile(self):
        """Tower at (3,1), critter interpolated between (4,1) and (5,1)."""
        # critter at 30% between tile 4 and 5 → q=4.3
        d = hex_world_distance(3.0, 1.0, 4.3, 1.0)
        assert d == pytest.approx(1.3)

    def test_range_check_float(self):
        """Critter between two tiles can be in range even if neither tile is."""
        # Tower at (0,0), range=1.5
        # Tile (2,0) is dist=2.0 (out), tile (1,0) is dist=1.0 (in).
        # Critter at 60% between them → q=1.6, dist=1.6 → just barely out
        assert hex_world_distance(0, 0, 1.6, 0) == pytest.approx(1.6)
        # At 40% → q=1.4, dist=1.4 → in range
        assert hex_world_distance(0, 0, 1.4, 0) == pytest.approx(1.4)

    def test_distance_matches_pixel_formula(self):
        """Cross-check against raw pixel distance at arbitrary size=7."""
        size = 7
        sqrt3 = math.sqrt(3)

        def to_pixel(q, r):
            return (size * 1.5 * q, size * (sqrt3 / 2 * q + sqrt3 * r))

        pairs = [(0, 0, 2, -1), (1, 3, 4, 0), (0, 0, 1, 1)]
        for q1, r1, q2, r2 in pairs:
            x1, y1 = to_pixel(q1, r1)
            x2, y2 = to_pixel(q2, r2)
            px_dist = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
            expected_hex = px_dist / (size * sqrt3)
            assert hex_world_distance(q1, r1, q2, r2) == pytest.approx(expected_hex, rel=1e-9)


# ── critter_hex_pos + hex_world_distance combined ─────────────────────────

class TestCritterTowerDistance:
    def test_critter_at_tile_same_as_hex_distance(self):
        """When critter sits exactly on a tile, world distance equals HexCoord.distance_to."""
        path = _hline(6)  # (0,0)..(5,0)
        tower_q, tower_r = 5.0, 0.0
        for progress, expected_dist in [(0.0, 5.0), (0.2, 4.0), (0.4, 3.0), (0.6, 2.0)]:
            cq, cr = critter_hex_pos(path, progress)
            d = hex_world_distance(tower_q, tower_r, cq, cr)
            assert d == pytest.approx(expected_dist), (
                f"progress={progress}: got {d}, expected {expected_dist}"
            )

    def test_critter_between_tiles_gives_float_distance(self):
        path = _hline(3)   # (0,0), (1,0), (2,0)
        tower_q, tower_r = 0.0, 0.0
        cq, cr = critter_hex_pos(path, 0.75)   # floatIdx=1.5 → q=1.5
        d = hex_world_distance(tower_q, tower_r, cq, cr)
        assert d == pytest.approx(1.5)

    def test_two_critters_relative_distance(self):
        path = _hline(5)
        cq1, cr1 = critter_hex_pos(path, 0.25)   # q=1.0
        cq2, cr2 = critter_hex_pos(path, 0.75)   # q=3.0
        d = hex_world_distance(cq1, cr1, cq2, cr2)
        assert d == pytest.approx(2.0)

    def test_range_boundary_inside(self):
        """Critter just inside range=2."""
        path = _hline(5)
        tower_q, tower_r = 0.0, 0.0
        # critter at progress=0.475 → floatIdx=0.475*4=1.9, q=1.9
        cq, cr = critter_hex_pos(path, 0.475)
        d = hex_world_distance(tower_q, tower_r, cq, cr)
        assert d < 2.0

    def test_range_boundary_outside(self):
        """Critter just outside range=2."""
        path = _hline(5)
        tower_q, tower_r = 0.0, 0.0
        # critter at progress=0.525 → floatIdx=2.1, q=2.1
        cq, cr = critter_hex_pos(path, 0.525)
        d = hex_world_distance(tower_q, tower_r, cq, cr)
        assert d > 2.0


# ── validate_path / path_distance / sub_path_from ─────────────────────────

class TestValidatePath:
    def test_empty_path_is_valid(self):
        assert validate_path([]) is True

    def test_single_tile_is_valid(self):
        assert validate_path([HexCoord(0, 0)]) is True

    def test_two_neighbors_are_valid(self):
        assert validate_path(_hpath((0, 0), (1, 0))) is True

    def test_gap_is_invalid(self):
        assert validate_path(_hpath((0, 0), (2, 0))) is False

    def test_longer_valid_path(self):
        assert validate_path(_hline(6)) is True


class TestPathDistance:
    def test_empty(self):
        assert path_distance([]) == 0

    def test_single(self):
        assert path_distance([HexCoord(0, 0)]) == 0

    def test_two_tiles(self):
        assert path_distance(_hline(2)) == 1

    def test_five_tiles(self):
        assert path_distance(_hline(5)) == 4


class TestSubPathFrom:
    def test_from_zero(self):
        path = _hline(5)
        assert sub_path_from(path, 0) == path

    def test_from_middle(self):
        path = _hline(5)
        sub = sub_path_from(path, 2)
        assert sub == [HexCoord(2, 0), HexCoord(3, 0), HexCoord(4, 0)]

    def test_from_last(self):
        path = _hline(5)
        sub = sub_path_from(path, 4)
        assert sub == [HexCoord(4, 0)]

    def test_clamps_negative(self):
        path = _hline(5)
        assert sub_path_from(path, -3) == path

    def test_clamps_beyond_end(self):
        path = _hline(5)
        sub = sub_path_from(path, 99)
        assert sub == [HexCoord(4, 0)]


# ── find_path_from_spawn_to_castle ─────────────────────────────────────────

class TestFindPath:
    def _tiles(self, entries: dict[tuple[int, int], str]) -> dict[str, str]:
        return {f"{q},{r}": t for (q, r), t in entries.items()}

    def test_direct_path(self):
        tiles = self._tiles({
            (0, 0): "spawnpoint",
            (1, 0): "path",
            (2, 0): "castle",
        })
        result = find_path_from_spawn_to_castle(tiles)
        assert result is not None
        assert result[0] == HexCoord(0, 0)
        assert result[-1] == HexCoord(2, 0)

    def test_no_castle_returns_none(self):
        tiles = self._tiles({(0, 0): "spawnpoint", (1, 0): "path"})
        assert find_path_from_spawn_to_castle(tiles) is None

    def test_no_spawn_returns_none(self):
        tiles = self._tiles({(0, 0): "path", (1, 0): "castle"})
        assert find_path_from_spawn_to_castle(tiles) is None

    def test_blocked_path_returns_none(self):
        tiles = self._tiles({
            (0, 0): "spawnpoint",
            (1, 0): "empty",   # wall — not walkable
            (2, 0): "castle",
        })
        assert find_path_from_spawn_to_castle(tiles) is None

    def test_path_is_connected(self):
        tiles = self._tiles({
            (0, 0): "spawnpoint",
            (1, 0): "path",
            (2, 0): "path",
            (3, 0): "castle",
        })
        result = find_path_from_spawn_to_castle(tiles)
        assert result is not None
        assert validate_path(result)
