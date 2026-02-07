"""Hex pathfinding on the game map.

Provides pathfinding utilities for critter movement on hexagonal grids.
Used to generate and validate paths from map entry points to the base.

Paths are pre-defined in map config as ordered hex coordinate lists.
This module provides:
- Path validation (connectivity, no gaps)
- Path distance calculation
- Sub-path extraction (for spawn-on-death placement)
"""

from __future__ import annotations

from gameserver.models.hex import HexCoord


def validate_path(path: list[HexCoord]) -> bool:
    """Check that each consecutive pair in the path are hex neighbors.

    Args:
        path: Ordered list of hex coordinates.

    Returns:
        True if the path is valid (all steps are between neighbors).
    """
    if len(path) < 2:
        return True
    return all(path[i].distance_to(path[i + 1]) == 1 for i in range(len(path) - 1))


def path_distance(path: list[HexCoord]) -> int:
    """Return the number of steps in a path (len - 1)."""
    return max(0, len(path) - 1)


def sub_path_from(path: list[HexCoord], start_index: int) -> list[HexCoord]:
    """Extract a sub-path starting from a given index.

    Useful for spawn-on-death: children start partway along the parent's path.

    Args:
        path: The full path.
        start_index: Index to start from (clamped to valid range).

    Returns:
        Sub-path from start_index to the end.
    """
    start_index = max(0, min(start_index, len(path) - 1))
    return path[start_index:]

from __future__ import annotations

from gameserver.models.hex import HexCoord
from gameserver.models.map import HexMap


def validate_path(path: list[HexCoord]) -> bool:
    """Check that each consecutive pair in the path are hex neighbors."""
    for i in range(len(path) - 1):
        if path[i].distance_to(path[i + 1]) != 1:
            return False
    return True


def path_length(path: list[HexCoord]) -> int:
    """Number of steps in a path (fields - 1)."""
    return max(0, len(path) - 1)


def remaining_distance(path: list[HexCoord], progress: float) -> float:
    """Remaining hex steps from a fractional path position."""
    return max(0.0, len(path) - 1 - progress)
