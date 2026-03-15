"""Hex pathfinding on the game map.

Provides pathfinding utilities for critter movement on hexagonal grids.
Used to generate and validate paths from map entry points to the base.

Paths are pre-defined in map config as ordered hex coordinate lists.
This module provides:
- Path validation (connectivity, no gaps)
- Pathfinding (BFS from spawn to castle)
- Path distance calculation
- Sub-path extraction (for spawn-on-death placement)
"""

from __future__ import annotations

import math
from collections import deque
from typing import Optional

from gameserver.models.hex import HexCoord

# sqrt(3) — distance between two adjacent flat-top hex centers in "size=1" space
_SQRT3 = math.sqrt(3)


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


def find_path_from_spawn_to_castle(tiles: dict[str, str]) -> Optional[list[HexCoord]]:
    """Find a path from any spawnpoint to the castle using BFS.
    
    Traverses only spawnpoint, path, and castle tiles via 6-connected hex neighbors.
    
    Args:
        tiles: Dict of {"q,r": "tile_type"} where tile_type is 'castle', 'spawnpoint', etc.
    
    Returns:
        List of HexCoord from spawn to castle, or None if no path exists.
    """
    # Find castle and spawnpoints
    castle_key: Optional[str] = None
    spawn_keys: list[str] = []
    
    for key, tile_type in tiles.items():
        if tile_type == 'castle':
            castle_key = key
        elif tile_type == 'spawnpoint':
            spawn_keys.append(key)
    
    if not castle_key or not spawn_keys:
        return None
    
    def key_to_coords(k: str) -> tuple[int, int]:
        q, r = k.split(',')
        return int(q), int(r)
    
    def hex_neighbors(q: int, r: int) -> list[tuple[int, int]]:
        return [
            (q + 1, r),
            (q + 1, r - 1),
            (q, r - 1),
            (q - 1, r),
            (q - 1, r + 1),
            (q, r + 1),
        ]
    
    def coords_to_key(q: int, r: int) -> str:
        return f"{q},{r}"
    
    castle_q, castle_r = key_to_coords(castle_key)
    
    # BFS from each spawnpoint
    for spawn_key in spawn_keys:
        spawn_q, spawn_r = key_to_coords(spawn_key)
        
        queue: deque[tuple[int, int]] = deque([(spawn_q, spawn_r)])
        visited: set[tuple[int, int]] = {(spawn_q, spawn_r)}
        parent: dict[tuple[int, int], Optional[tuple[int, int]]] = {(spawn_q, spawn_r): None}
        
        while queue:
            q, r = queue.popleft()
            
            # Reached castle?
            if (q, r) == (castle_q, castle_r):
                # Reconstruct path
                path: list[tuple[int, int]] = []
                current: Optional[tuple[int, int]] = (q, r)
                while current is not None:
                    path.append(current)
                    current = parent.get(current)
                path.reverse()
                return [HexCoord(pq, pr) for pq, pr in path]
            
            # Explore neighbors
            for nq, nr in hex_neighbors(q, r):
                if (nq, nr) not in visited:
                    key = coords_to_key(nq, nr)
                    tile_type = tiles.get(key)
                    
                    # Only traverse through passable tiles
                    if tile_type in ('spawnpoint', 'path', 'castle'):
                        visited.add((nq, nr))
                        parent[(nq, nr)] = (q, r)
                        queue.append((nq, nr))
    
    return None


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


def critter_hex_pos(path: list[HexCoord], path_progress: float) -> tuple[float, float]:
    """Return the interpolated (q, r) position of a critter on its path.

    path_progress is normalized in [0.0, 1.0] over the whole path.
    Returns sub-tile-precise floating-point hex coordinates — the critter
    is between two hex centers, not snapped to a grid tile.

    Args:
        path: Ordered list of HexCoord tile centers the critter follows.
        path_progress: Normalized progress [0, 1] along the path.

    Returns:
        (q, r) as floats representing the interpolated hex position.
    """
    if not path:
        return (0.0, 0.0)
    if len(path) == 1:
        return (float(path[0].q), float(path[0].r))
    max_idx = len(path) - 1
    float_idx = path_progress * max_idx
    idx = min(int(float_idx), max_idx - 1)
    frac = float_idx - idx
    a, b = path[idx], path[idx + 1]
    return (a.q + (b.q - a.q) * frac, a.r + (b.r - a.r) * frac)


def hex_world_distance(q1: float, r1: float, q2: float, r2: float) -> float:
    """Euclidean distance between two positions in hex-world space.

    Works for any combination of integer tile coords and fractional critter
    positions.  1 unit = distance between two adjacent tile centers
    (flat-top hex layout, independent of canvas hexSize).

    Formula derivation:
      hexToPixel maps (q, r) → (1.5·q, √3/2·q + √3·r) at size=1.
      All six neighbors are exactly √3 pixels away at size=1.
      → hex_units = euclidean_pixel_distance / √3

    Args:
        q1, r1: First position (hex-space, may be fractional).
        q2, r2: Second position (hex-space, may be fractional).

    Returns:
        Distance in hex units (float).
    """
    dq = q2 - q1
    dr = r2 - r1
    dx = 1.5 * dq
    dy = 0.5 * _SQRT3 * dq + _SQRT3 * dr
    return math.sqrt(dx * dx + dy * dy) / _SQRT3
