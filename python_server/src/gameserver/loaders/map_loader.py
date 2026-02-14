"""Map loader — parses hex map definitions into HexMap models.

Format: dict of {"q,r": "tile_type"} where tile_type is one of:
- "castle": Destination for critters
- "spawnpoint": Starting point for critters
- "path": Traversable tile on the critter path
- "build": Buildable tile for structures
- "void": Non-traversable tile
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from gameserver.models.hex import HexCoord
from gameserver.models.map import HexMap
from gameserver.engine.hex_pathfinding import find_path_from_spawn_to_castle


def load_map(path: str | Path) -> HexMap:
    """Load a hex map from a YAML file.

    For backwards compatibility, supports both old and new formats.

    Args:
        path: Path to the map YAML file.

    Returns:
        Populated HexMap instance.
    """
    path = Path(path)
    with path.open() as f:
        data: dict[str, Any] = yaml.safe_load(f) or {}

    # Check if this is the new format (tiles dict) or old format (paths + build_tiles)
    if "tiles" in data:
        # New format: tiles dict with q,r -> tile_type
        return load_map_from_tiles(data["tiles"])
    else:
        # Old format: separate paths and build_tiles
        hex_map = HexMap()
        
        # Parse build tiles
        raw_tiles = data.get("build_tiles", [])
        hex_map.build_tiles = {HexCoord(q=t[0], r=t[1]) for t in raw_tiles}
        
        return hex_map


def load_map_from_tiles(tiles: dict[str, str]) -> HexMap:
    """Load a HexMap from a tiles dictionary.

    Args:
        tiles: Dict of {"q,r": "tile_type"} where tile_type is:
               'castle', 'spawnpoint', 'path', 'build', 'void', etc.

    Returns:
        Populated HexMap instance with critter_path and build_tiles.
    """
    hex_map = HexMap()

    # Extract build tiles
    for key, tile_type in tiles.items():
        if tile_type == "build":
            q, r = map(int, key.split(","))
            hex_map.build_tiles.add(HexCoord(q, r))

    # Calculate critter path from spawnpoint to castle
    critter_path = find_path_from_spawn_to_castle(tiles)
    if critter_path:
        hex_map.critter_path = critter_path

    return hex_map
