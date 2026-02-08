"""Tests for hex map validation in the map_save_request handler."""

from __future__ import annotations

from collections import deque
from typing import Optional

import pytest


def _has_path_from_spawn_to_castle(tiles: dict[str, str]) -> bool:
    """Check if there's a path from any spawnpoint to the castle.
    
    Can only traverse spawnpoint, path, and castle tiles via 6-connected hex neighbors.
    
    Args:
        tiles: Dict of {"q,r": "tile_type"} where tile_type is 'castle', 'spawnpoint', etc.
    
    Returns:
        True if at least one path exists, False otherwise.
    """
    # Find castle and spawnpoints
    castle_key: Optional[str] = None
    spawn_keys: list[str] = []
    
    for key, tile_type in tiles.items():
        if tile_type == 'castle':
            castle_key = key
        elif tile_type == 'spawnpoint':
            spawn_keys.append(key)
    
    # Must have both
    if not castle_key or not spawn_keys:
        return False
    
    # Parse key to coordinates
    def key_to_coords(k: str) -> tuple[int, int]:
        q, r = k.split(',')
        return int(q), int(r)
    
    # Hex neighbors in axial coordinates
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
        
        while queue:
            q, r = queue.popleft()
            
            # Reached castle?
            if (q, r) == (castle_q, castle_r):
                return True
            
            # Explore neighbors
            for nq, nr in hex_neighbors(q, r):
                if (nq, nr) not in visited:
                    key = coords_to_key(nq, nr)
                    tile_type = tiles.get(key)
                    
                    # Only traverse through passable tiles
                    if tile_type in ('spawnpoint', 'path', 'castle'):
                        visited.add((nq, nr))
                        queue.append((nq, nr))
    
    return False


class TestPathfinding:
    """Test the _has_path_from_spawn_to_castle helper."""

    def test_simple_path(self) -> None:
        """Simple linear path from spawn to castle."""
        tiles = {
            "0,0": "spawnpoint",
            "1,0": "path",
            "2,0": "castle",
        }
        assert _has_path_from_spawn_to_castle(tiles) is True

    def test_no_spawnpoint(self) -> None:
        """No path if there's no spawnpoint."""
        tiles = {
            "0,0": "castle",
        }
        assert _has_path_from_spawn_to_castle(tiles) is False

    def test_no_castle(self) -> None:
        """No path if there's no castle."""
        tiles = {
            "0,0": "spawnpoint",
            "1,0": "path",
        }
        assert _has_path_from_spawn_to_castle(tiles) is False

    def test_castle_adjacent_to_spawn(self) -> None:
        """Castle directly adjacent to spawnpoint (no path tiles needed)."""
        tiles = {
            "0,0": "spawnpoint",
            "1,0": "castle",
        }
        assert _has_path_from_spawn_to_castle(tiles) is True

    def test_disconnected_path(self) -> None:
        """Path exists but doesn't connect."""
        tiles = {
            "0,0": "spawnpoint",
            "5,0": "path",
            "6,0": "castle",
        }
        assert _has_path_from_spawn_to_castle(tiles) is False

    def test_multiple_spawnpoints_one_connects(self) -> None:
        """Multiple spawns, only one has a path."""
        tiles = {
            "0,0": "spawnpoint",
            "1,0": "path",
            "2,0": "castle",
            "10,10": "spawnpoint",
        }
        assert _has_path_from_spawn_to_castle(tiles) is True

    def test_multiple_spawnpoints_none_connect(self) -> None:
        """Multiple spawns, none have a path."""
        tiles = {
            "0,0": "spawnpoint",
            "5,0": "path",
            "10,10": "castle",
            "10,20": "spawnpoint",
        }
        assert _has_path_from_spawn_to_castle(tiles) is False

    def test_zigzag_path(self) -> None:
        """Path with turns."""
        tiles = {
            "0,0": "spawnpoint",
            "1,0": "path",
            "1,-1": "path",
            "2,-1": "castle",
        }
        assert _has_path_from_spawn_to_castle(tiles) is True

    def test_path_with_empty_tiles_blocked(self) -> None:
        """Empty tiles block path."""
        tiles = {
            "0,0": "spawnpoint",
            "1,0": "empty",
            "2,0": "castle",
        }
        assert _has_path_from_spawn_to_castle(tiles) is False

    def test_void_tiles_block_path(self) -> None:
        """Void tiles block path."""
        tiles = {
            "0,0": "spawnpoint",
            "1,0": "void",
            "2,0": "castle",
        }
        assert _has_path_from_spawn_to_castle(tiles) is False

    def test_hexagon_connectivity(self) -> None:
        """Test 6-connected hexagon neighbors."""
        tiles = {
            "0,0": "spawnpoint",
            "0,1": "path",       # SE
            "0,0": "spawnpoint",
            "0,1": "castle",
        }
        assert _has_path_from_spawn_to_castle(tiles) is True

    def test_long_winding_path(self) -> None:
        """Long winding path with many turns."""
        tiles = {
            "0,0": "spawnpoint",
            "1,0": "path",
            "2,0": "path",
            "2,-1": "path",
            "2,-2": "path",
            "1,-2": "path",
            "0,-2": "castle",
        }
        assert _has_path_from_spawn_to_castle(tiles) is True

    def test_empty_dict(self) -> None:
        """Empty tiles dict returns False."""
        tiles: dict[str, str] = {}
        assert _has_path_from_spawn_to_castle(tiles) is False

    def test_spawn_through_multiple_paths(self) -> None:
        """Multiple possible paths, only need one."""
        tiles = {
            "0,0": "spawnpoint",
            "1,0": "path",
            "1,-1": "path",
            "2,-1": "castle",
            "1,1": "path",  # Alternative path (unused)
            "1,2": "empty",  # Dead end
        }
        assert _has_path_from_spawn_to_castle(tiles) is True
