"""Tests for hex math utilities."""

from gameserver.models.hex import HexCoord
from gameserver.util.hex_math import hex_distance, hex_linedraw


class TestHexDistance:
    def test_distance_to_self_is_zero(self):
        h = HexCoord(3, -2)
        assert h.distance_to(h) == 0

    def test_distance_to_neighbor_is_one(self):
        a = HexCoord(0, 0)
        for n in a.neighbors():
            assert a.distance_to(n) == 1

    def test_distance_is_symmetric(self):
        a, b = HexCoord(1, 2), HexCoord(-3, 5)
        assert a.distance_to(b) == b.distance_to(a)

    def test_distance_known_value(self):
        a, b = HexCoord(0, 0), HexCoord(3, -1)
        assert a.distance_to(b) == 3


class TestHexNeighbors:
    def test_neighbor_count(self):
        assert len(HexCoord(0, 0).neighbors()) == 6

    def test_neighbors_are_distance_one(self):
        center = HexCoord(5, -3)
        for n in center.neighbors():
            assert center.distance_to(n) == 1


class TestHexRing:
    def test_ring_zero_is_empty(self):
        assert HexCoord(0, 0).ring(0) == []

    def test_ring_one_has_six(self):
        assert len(HexCoord(0, 0).ring(1)) == 6

    def test_ring_n_has_6n(self):
        for r in range(1, 5):
            assert len(HexCoord(0, 0).ring(r)) == 6 * r

    def test_ring_elements_at_correct_distance(self):
        center = HexCoord(2, -1)
        for h in center.ring(3):
            assert center.distance_to(h) == 3


class TestHexDisk:
    def test_disk_zero_is_center(self):
        c = HexCoord(0, 0)
        assert c.disk(0) == {c}

    def test_disk_one_has_seven(self):
        assert len(HexCoord(0, 0).disk(1)) == 7

    def test_disk_two_has_nineteen(self):
        assert len(HexCoord(0, 0).disk(2)) == 19


class TestHexLinedraw:
    def test_line_to_self(self):
        h = HexCoord(1, 1)
        assert hex_linedraw(h, h) == [h]

    def test_line_includes_endpoints(self):
        a, b = HexCoord(0, 0), HexCoord(3, 0)
        line = hex_linedraw(a, b)
        assert line[0] == a
        assert line[-1] == b

    def test_line_length_is_distance_plus_one(self):
        a, b = HexCoord(0, 0), HexCoord(2, -2)
        line = hex_linedraw(a, b)
        assert len(line) == hex_distance(a, b) + 1

    def test_line_consecutive_neighbors(self):
        a, b = HexCoord(0, 0), HexCoord(4, -2)
        line = hex_linedraw(a, b)
        for i in range(len(line) - 1):
            assert line[i].distance_to(line[i + 1]) == 1
