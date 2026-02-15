"""Hexagonal map model.

Holds the hex grid, paths for critter movement, build zones, and occupancy tracking.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from gameserver.models.hex import HexCoord


@dataclass
class HexMap:
    """The game map as a hexagonal grid.

    Attributes:
        critter_path: Ordered list of hex coordinates that critters follow.
        build_tiles: Set of hex coordinates where structures may be placed.
        occupied: Set of hex coordinates currently occupied by structures.
    """

    critter_path: list[HexCoord] = field(default_factory=list)
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

    def get_path(self) -> list[HexCoord]:
        """Return a copy of the critter path."""
        return list(self.critter_path)

    # -- Internal --------------------------------------------------------

    @staticmethod
    def _footprint(center: HexCoord, radius: int) -> set[HexCoord]:
        """Compute the set of hexes occupied by a structure."""
        if radius <= 0:
            return {center}
        return center.disk(radius)
