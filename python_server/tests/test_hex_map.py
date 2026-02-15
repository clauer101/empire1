"""Tests for HexMap — paths, build zones, occupancy."""

from gameserver.models.hex import HexCoord
from gameserver.models.map import HexMap


def _make_straight_path(length: int) -> HexMap:
    """Create a map with a straight path of given length along q axis."""
    path = [HexCoord(q, 0) for q in range(length)]
    build = {HexCoord(q, 1) for q in range(length)}  # row below path
    return HexMap(critter_path=path, build_tiles=build)


class TestHexMapPaths:
    def test_path_length(self):
        m = _make_straight_path(10)
        assert len(m.critter_path) == 10

    def test_empty_path_length_zero(self):
        m = HexMap()
        assert len(m.critter_path) == 0

    def test_get_path_returns_list(self):
        m = _make_straight_path(5)
        assert len(m.critter_path) == 5
        assert m.critter_path[0] == HexCoord(0, 0)
        assert m.critter_path[-1] == HexCoord(4, 0)


class TestHexMapBuilding:
    def test_can_build_on_build_tile(self):
        m = _make_straight_path(5)
        assert m.can_build(HexCoord(2, 1))

    def test_cannot_build_outside_zone(self):
        m = _make_straight_path(5)
        assert not m.can_build(HexCoord(2, 5))

    def test_cannot_build_on_path(self):
        m = _make_straight_path(5)
        assert not m.can_build(HexCoord(2, 0))

    def test_place_then_occupied(self):
        m = _make_straight_path(5)
        pos = HexCoord(2, 1)
        m.place_structure(pos)
        assert not m.can_build(pos)

    def test_remove_frees_tile(self):
        m = _make_straight_path(5)
        pos = HexCoord(2, 1)
        m.place_structure(pos)
        m.remove_structure(pos)
        assert m.can_build(pos)

    def test_overlap_blocked(self):
        m = _make_straight_path(10)
        m.place_structure(HexCoord(3, 1))
        # Same tile occupied → blocked
        assert not m.can_build(HexCoord(3, 1))

    def test_footprint_radius(self):
        build = HexCoord(5, 1).disk(2)
        m = HexMap(build_tiles=build)
        assert m.can_build(HexCoord(5, 1), radius=1)
        m.place_structure(HexCoord(5, 1), radius=1)
        assert not m.can_build(HexCoord(5, 1), radius=1)
