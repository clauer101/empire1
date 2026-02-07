"""Hexagonal coordinate system using axial coordinates (q, r).

Axial coordinates define position on a hex grid where:
- q axis runs roughly east
- r axis runs roughly south-east
- s = -q - r is the implicit third cube coordinate

Reference: https://www.redblobgames.com/grids/hexagons/
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class HexCoord:
    """Immutable axial hex coordinate.

    Attributes:
        q: Column coordinate (east axis).
        r: Row coordinate (south-east axis).
    """

    q: int
    r: int

    # -- Cube coordinate -------------------------------------------------

    @property
    def s(self) -> int:
        """Implicit cube coordinate: s = -q - r."""
        return -self.q - self.r

    # -- Arithmetic ------------------------------------------------------

    def __add__(self, other: HexCoord) -> HexCoord:
        return HexCoord(self.q + other.q, self.r + other.r)

    def __sub__(self, other: HexCoord) -> HexCoord:
        return HexCoord(self.q - other.q, self.r - other.r)

    # -- Geometry --------------------------------------------------------

    def distance_to(self, other: HexCoord) -> int:
        """Hex grid distance (number of steps along hex edges)."""
        dq = abs(self.q - other.q)
        dr = abs(self.r - other.r)
        ds = abs(self.s - other.s)
        return max(dq, dr, ds)

    def neighbors(self) -> list[HexCoord]:
        """Return the 6 adjacent hex coordinates."""
        return [HexCoord(self.q + dq, self.r + dr) for dq, dr in _DIRECTIONS]

    def ring(self, radius: int) -> list[HexCoord]:
        """Return all hexes at exactly `radius` steps away.

        Returns empty list for radius <= 0.
        """
        if radius <= 0:
            return []
        results: list[HexCoord] = []
        # Start at "top-left" of ring
        h = HexCoord(self.q - radius, self.r + radius)
        for direction in _DIRECTIONS:
            for _ in range(radius):
                results.append(h)
                h = HexCoord(h.q + direction[0], h.r + direction[1])
        return results

    def disk(self, radius: int) -> set[HexCoord]:
        """Return all hexes within `radius` steps (inclusive)."""
        results: set[HexCoord] = set()
        for dq in range(-radius, radius + 1):
            for dr in range(max(-radius, -dq - radius), min(radius, -dq + radius) + 1):
                results.add(HexCoord(self.q + dq, self.r + dr))
        return results

    def line_to(self, other: HexCoord) -> list[HexCoord]:
        """Return a list of hex coordinates forming a line from self to other.

        Uses linear interpolation in cube space with rounding.
        """
        from gameserver.util.hex_math import hex_linedraw

        return hex_linedraw(self, other)

    # -- Serialization ---------------------------------------------------

    def __repr__(self) -> str:
        return f"Hex({self.q},{self.r})"


# The 6 axial direction vectors (flat-top layout)
_DIRECTIONS: list[tuple[int, int]] = [
    (1, 0),   # E
    (1, -1),  # NE
    (0, -1),  # NW
    (-1, 0),  # W
    (-1, 1),  # SW
    (0, 1),   # SE
]
