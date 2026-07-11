"""Pure defense-analysis functions: coverage scoring and maze/corridor geometry.

No API calls here — everything operates on plain dicts so it is fully unit-testable.
Geometry matches the server's targeting math (battle_service / hex_pathfinding):
tower range is a continuous hex-world distance from the tower tile center to the
interpolated critter position.
"""

from __future__ import annotations

import math
import random
from typing import Any, Callable

HEX_DIRS = [(1, 0), (1, -1), (0, -1), (-1, 0), (-1, 1), (0, 1)]
PATH_TILES = {"path", "spawnpoint"}

SAMPLES_PER_EDGE = 4     # path interpolation density


def hex_world_distance(q1: float, r1: float, q2: float, r2: float) -> float:
    """Continuous hex-world distance; adjacent tile centers are exactly 1.0."""
    dq, dr = q2 - q1, r2 - r1
    dx = 1.5 * dq
    dy = 0.5 * math.sqrt(3) * dq + math.sqrt(3) * dr
    return math.sqrt(dx * dx + dy * dy) / math.sqrt(3)


# ── Coverage scoring ─────────────────────────────────────────────────────────


def path_points(path: list[tuple[int, int]],
                samples_per_edge: int = SAMPLES_PER_EDGE) -> list[tuple[float, float, float]]:
    """Interpolated (q, r, progress) points along the path."""
    if len(path) < 2:
        return [(float(q), float(r), 0.0) for q, r in path]
    points: list[tuple[float, float, float]] = []
    total = (len(path) - 1) * samples_per_edge
    for i in range(len(path) - 1):
        (q1, r1), (q2, r2) = path[i], path[i + 1]
        for s in range(samples_per_edge):
            t = s / samples_per_edge
            idx = i * samples_per_edge + s
            points.append((q1 + (q2 - q1) * t, r1 + (r2 - r1) * t, idx / total))
    points.append((float(path[-1][0]), float(path[-1][1]), 1.0))
    return points


def coverage_score(tile: tuple[int, int], tower_range: float,
                   path_pts: list[tuple[float, float, float]],
                   weight_fn: Callable[[float], float]) -> float:
    """Weighted count of path points within tower range of the tile center."""
    tq, tr = tile
    return sum(weight_fn(progress)
               for q, r, progress in path_pts
               if hex_world_distance(tq, tr, q, r) <= tower_range)


def _tile_type(value) -> str:
    if isinstance(value, dict):
        return value.get("type", "")
    return str(value)


def _parse_key(key: str) -> tuple[int, int]:
    q, r = key.split(",")
    return int(q), int(r)



# ── Path length / spawn+castle relocation ───────────────────────────────────

# Tile types critters can traverse (mirrors server hex_pathfinding BFS)
TRAVERSABLE = {"spawnpoint", "path", "empty", "castle"}


def bfs_path(tiles: dict) -> list[tuple[int, int]] | None:
    """Shortest critter path spawn→castle (server BFS semantics), or None."""
    spawns = [_parse_key(k) for k, v in tiles.items()
              if _tile_type(v) == "spawnpoint"]
    castles = [_parse_key(k) for k, v in tiles.items()
               if _tile_type(v) == "castle"]
    if not spawns or not castles:
        return None
    castle = castles[0]
    walkable = {_parse_key(k) for k, v in tiles.items()
                if _tile_type(v) in TRAVERSABLE}
    best: list[tuple[int, int]] | None = None
    for spawn in spawns:
        frontier = [spawn]
        came: dict[tuple[int, int], tuple[int, int] | None] = {spawn: None}
        while frontier:
            nxt: list[tuple[int, int]] = []
            for q, r in frontier:
                if (q, r) == castle:
                    path = [(q, r)]
                    while came[path[-1]] is not None:
                        path.append(came[path[-1]])  # type: ignore[arg-type]
                    path.reverse()
                    if best is None or len(path) < len(best):
                        best = path
                    nxt = []
                    break
                for dq, dr in HEX_DIRS:
                    n = (q + dq, r + dr)
                    if n in walkable and n not in came:
                        came[n] = (q, r)
                        nxt.append(n)
            frontier = nxt
    return best


# ── Tower selection ──────────────────────────────────────────────────────────

# Desired ratio among placed towers: damage-focused vs. slow vs. splash
MIX_TARGET = {"damage": 3, "slow": 1, "splash": 1}


def tower_class(item: dict) -> str:
    effects = item.get("effects") or {}
    if "slow_ratio" in effects or "slow_duration" in effects:
        return "slow"
    if "splash_radius" in effects:
        return "splash"
    return "damage"  # burn-only towers count as damage dealers


def tower_quality(item: dict) -> float:
    """Single-number tower strength: DPS per reload, boosted by range."""
    damage = float(item.get("damage", 0.0) or 0.0)
    reload_ms = float(item.get("reload_time", 1000) or 1000)
    rng = float(item.get("range", 1.0) or 1.0)
    return damage / max(reload_ms, 1.0) * (1.0 + rng / 4.0)


def pick_tower(structures: dict, placed_counts: dict[str, int],
               usable: Callable[[dict], bool],
               top_n: int = 1, rng: Any = random) -> str | None:
    """Pick the IID of a usable tower in the most under-represented class.

    Always picks from the highest available era. Within that era, class-mix
    balancing (damage/slow/splash) determines which tower class to place.

    placed_counts: tower class → number currently placed.
    usable: predicate (unlocked + affordable), supplied by the planner.
    top_n: among the usable towers in the chosen class, sample one of the best
    `top_n` by quality (weighted toward the best). top_n=1 → deterministic best.
    """
    from bot.analyzer import ERA_RANK  # local import to avoid circular dependency
    candidates = [(iid, it) for iid, it in structures.items() if usable(it)]
    if not candidates:
        return None
    # Restrict to highest era available so new towers are always best-era.
    best_era_rank = max(ERA_RANK.get(it.get("era", "stone"), 0) for _, it in candidates)
    candidates = [(iid, it) for iid, it in candidates
                  if ERA_RANK.get(it.get("era", "stone"), 0) == best_era_rank]
    total_target = sum(MIX_TARGET.values())
    total_placed = sum(placed_counts.values()) or 1

    def deficit(cls: str) -> float:
        return MIX_TARGET[cls] / total_target - placed_counts.get(cls, 0) / total_placed

    by_class: dict[str, list[tuple[str, dict]]] = {}
    for iid, it in candidates:
        by_class.setdefault(tower_class(it), []).append((iid, it))
    for cls in sorted(by_class, key=lambda c: -deficit(c)):
        ordered = sorted(by_class[cls], key=lambda c: tower_quality(c[1]), reverse=True)
        pool = ordered[:max(1, top_n)]
        if len(pool) == 1:
            return pool[0][0]
        weights = list(range(len(pool), 0, -1))
        return rng.choices(pool, weights=weights, k=1)[0][0]
    return None
