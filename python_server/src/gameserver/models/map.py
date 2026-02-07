"""Hexagonal map model.

Holds the hex grid, paths for critter movement, build zones, and occupancy tracking.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from gameserver.models.hex import HexCoord


class Direction(Enum):
    """Cardinal entry directions for critter paths."""

    NORTH = "north"
    SOUTH = "south"
    EAST = "east"
    WEST = "west"


@dataclass
class HexMap:
    """The game map as a hexagonal grid.

    Attributes:
        paths: Ordered list of hex coordinates per direction that critters follow.
        build_tiles: Set of hex coordinates where structures may be placed.
        occupied: Set of hex coordinates currently occupied by structures.
    """

    paths: dict[Direction, list[HexCoord]] = field(default_factory=dict)
    build_tiles: set[HexCoord] = field(default_factory=set)
    occupied: set[HexCoord] = field(default_factory=set)

    # -- Queries ---------------------------------------------------------

    def can_build(self, center: HexCoord, radius: int = 0) -> bool:
        """Check whether a structure with given footprint radius can be placed.

        Args:
            center: Center hex of the structure.
            radius: Footprint radius (0 = single hex, 1 = center + neighbors).

        Returns:
            True if all required tiles are buildable and unoccupied.
        """
        footprint = self._footprint(center, radius)
        return footprint <= self.build_tiles and not (footprint & self.occupied)

    def place_structure(self, center: HexCoord, radius: int = 0) -> None:
        """Mark tiles as occupied by a structure."""
        self.occupied |= self._footprint(center, radius)

    def remove_structure(self, center: HexCoord, radius: int = 0) -> None:
        """Free tiles previously occupied by a structure."""
        self.occupied -= self._footprint(center, radius)

    def path_length(self, direction: Direction) -> int:
        """Number of hex steps in a path (fields - 1)."""
        path = self.paths.get(direction, [])
        return max(0, len(path) - 1)

    def get_path(self, direction: Direction) -> list[HexCoord]:
        """Return a copy of the path for the given direction."""
        return list(self.paths.get(direction, []))

    # -- Internal --------------------------------------------------------

    @staticmethod
    def _footprint(center: HexCoord, radius: int) -> set[HexCoord]:
        """Compute the set of hexes occupied by a structure."""
        if radius <= 0:
            return {center}
        return center.disk(radius)
