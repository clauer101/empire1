"""Map loader — parses hex map definitions into HexMap models.

Replaces the Java MapInterpreter SAX parser for TMX files.
New format: YAML-based hex map definitions.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from gameserver.models.hex import HexCoord
from gameserver.models.map import Direction, HexMap


def load_map(path: str | Path) -> HexMap:
    """Load a hex map from a YAML file.

    Expected format:
        paths:
          north: [[q,r], [q,r], ...]
          south: [[q,r], [q,r], ...]
          east:  [[q,r], [q,r], ...]
          west:  [[q,r], [q,r], ...]
        build_tiles: [[q,r], [q,r], ...]

    Args:
        path: Path to the map YAML file.

    Returns:
        Populated HexMap instance.
    """
    path = Path(path)
    with path.open() as f:
        data: dict[str, Any] = yaml.safe_load(f) or {}

    hex_map = HexMap()

    # Parse paths
    for dir_name, direction in [
        ("north", Direction.NORTH),
        ("south", Direction.SOUTH),
        ("east", Direction.EAST),
        ("west", Direction.WEST),
    ]:
        raw_path = data.get("paths", {}).get(dir_name, [])
        hex_map.paths[direction] = [HexCoord(q=p[0], r=p[1]) for p in raw_path]

    # Parse build tiles
    raw_tiles = data.get("build_tiles", [])
    hex_map.build_tiles = {HexCoord(q=t[0], r=t[1]) for t in raw_tiles}

    return hex_map
