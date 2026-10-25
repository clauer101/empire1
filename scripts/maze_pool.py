"""maze_pool.py — Auto-generated random mazes for balancing simulations.

Builds mazes with `gameserver.engine.maze_generator.MazeGenerator` — the same
engine behind `/api/admin/maze/step` (the admin maze-generation tool) — driven
headlessly against a throwaway, unregistered `Empire` and a real (but
otherwise idle) `EmpireService`, so pricing uses the exact same formulas the
live server does. Target corridor length is drawn per era from game.yaml's
`maze_length` section (see `target_maze_length`).

Mirrors `scripts/army_pool.py`'s role for armies: both produce ready-to-battle
objects (`Maze` / `AttackingArmy`) that plug directly into
`scripts/battle_sim.py`'s `build_structures` / `make_battle` / `run_battle`.
"""

from __future__ import annotations

import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "python_server" / "src"))

from gameserver.engine.empire_service import EmpireService
from gameserver.engine.hex_pathfinding import find_path_from_spawn_to_castle
from gameserver.engine.maze_generator import (
    MazeGenerator,
    era_filtered_structures,
    target_maze_length,
    target_maze_towers,
)
from gameserver.loaders.game_config_loader import GameConfig
from gameserver.models.empire import Empire
from gameserver.models.items import ItemDetails
from gameserver.util.eras import ERA_ORDER
from gameserver.util.maze_loader import Maze

MAZE_START_TILES = {"0,0": "castle", "0,1": "spawnpoint", "1,0": "empty"}

# Building an auto-maze is bounded: corridor growth stops at target_length,
# and flank/tower/side-tile/upgrade/era-swap all draw from strictly finite
# pools once the corridor is fixed-length, so the generator eventually stops
# producing actions on its own. IDLE_STOP mirrors web/tools/maze-sim.html's
# own "stop after 5 empty cycles" heuristic; MAX_STEPS is just a safety cap.
IDLE_STOP = 5
MAX_STEPS = 4000


def generate_random_maze(
    era: str,
    empire_service: EmpireService,
    items_dict: dict[str, ItemDetails],
    game_config: GameConfig,
    seed: int,
    top_n: int = 2,
    life: float | None = None,
    tower_type: str | None = None,
    target_length: int | None = None,
    target_towers: int | None = None,
) -> Maze:
    """Build one random maze for `era`, ready for `scripts.battle_sim`.

    Args:
        tower_type: restrict the era's tower catalog to only towers of this
            `tower_type` (e.g. "fast") — e.g. for a single-tower-class
            counter-test maze. Raises ValueError listing the tower types
            actually available for `era` if the filtered catalog is empty.
        target_length: force an exact corridor length instead of drawing one
            randomly from game.yaml's per-era `maze_length` range.
        target_towers: force an exact tower count instead of drawing one
            randomly from game.yaml's per-era `maze_length` range.

    Raises ValueError if `era` isn't a known era, RuntimeError if the
    generator somehow produces a maze with no spawn-to-castle path (should
    not happen — MazeGenerator's flood-safety rule keeps the corridor
    connected by construction).
    """
    if era not in ERA_ORDER:
        raise ValueError(f"unknown era {era!r}; choose from {ERA_ORDER}")
    era_index = ERA_ORDER.index(era)
    era_rank = empire_service._item_era_index
    structures = era_filtered_structures(items_dict, era_rank, era_index)
    if tower_type is not None:
        matching = {iid: it for iid, it in structures.items() if it.tower_type == tower_type}
        if not matching:
            available = sorted({it.tower_type for it in structures.values() if it.tower_type})
            raise ValueError(f"no {tower_type!r} towers for era {era!r}; available tower_types: {available}")
        structures = matching
    maze_length_cfg = getattr(game_config, "maze_length", {}) or {}
    if target_length is None:
        target_length = target_maze_length(maze_length_cfg, era, random.Random(seed))
    if target_towers is None:
        target_towers = target_maze_towers(maze_length_cfg, era, random.Random(seed))

    tiles: dict[str, str] = dict(MAZE_START_TILES)
    sandbox = Empire(uid=-1)
    sandbox.resources["gold"] = float("inf")

    generator = MazeGenerator(
        structures=structures, era_rank=era_rank,
        tile_price_for=empire_service.tile_price_for,
        item_upgrade_price_for=empire_service._item_upgrade_price,
        tower_sell_refund=float(getattr(game_config, "tower_sell_refund", 0.3)),
        target_length=target_length, target_towers=target_towers,
        top_n=top_n, rng=random.Random(seed),
    )

    idle = 0
    for _ in range(MAX_STEPS):
        action = generator.step(tiles, sandbox)
        idle = 0 if action else idle + 1
        if idle >= IDLE_STOP:
            break

    hex_map = dict(tiles)
    path = find_path_from_spawn_to_castle(hex_map)
    if not path:
        raise RuntimeError(f"generate_random_maze({era!r}, seed={seed}) produced no spawn->castle path")

    tower_count = sum(1 for v in hex_map.values() if v in structures)
    resolved_life = life if life is not None else float(getattr(game_config, "starting_max_life", 10.0))

    return Maze(
        name=f"random-{era}-seed{seed}",
        source="generated",
        hex_map=hex_map,
        path=path,
        era=era,
        tower_count=tower_count,
        life=resolved_life,
    )
