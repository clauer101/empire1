"""Pure defense-analysis functions: replay weakness analysis and coverage scoring.

No API calls here — everything operates on plain dicts so it is fully unit-testable.
Geometry matches the server's targeting math (battle_service / hex_pathfinding):
tower range is a continuous hex-world distance from the tower tile center to the
interpolated critter position.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Any, Callable

HEX_DIRS = [(1, 0), (1, -1), (0, -1), (-1, 0), (-1, 1), (0, 1)]
PATH_TILES = {"path", "spawnpoint"}

N_BINS = 10              # path_progress histogram resolution
WEAK_WEIGHT = 3.0        # coverage weight inside weak segments
SAMPLES_PER_EDGE = 4     # path interpolation density


def hex_world_distance(q1: float, r1: float, q2: float, r2: float) -> float:
    """Continuous hex-world distance; adjacent tile centers are exactly 1.0."""
    dq, dr = q2 - q1, r2 - r1
    dx = 1.5 * dq
    dy = 0.5 * math.sqrt(3) * dq + math.sqrt(3) * dr
    return math.sqrt(dx * dx + dy * dy) / math.sqrt(3)


# ── Replay analysis ──────────────────────────────────────────────────────────


@dataclass
class ReplayAnalysis:
    defender_won: bool = False
    path: list[tuple[int, int]] = field(default_factory=list)
    death_bins: list[int] = field(default_factory=lambda: [0] * N_BINS)
    reach_count: int = 0
    weak_segments: list[tuple[float, float]] = field(default_factory=list)

    def to_memory(self) -> dict:
        """Compact YAML-serializable form for bot memory."""
        return {
            "defender_won": self.defender_won,
            "death_bins": list(self.death_bins),
            "reach_count": self.reach_count,
            "weak_segments": [list(s) for s in self.weak_segments],
        }


def analyze_replay(replay: dict) -> ReplayAnalysis:
    """Histogram critter deaths over path progress; mark weak segments.

    Weak segment = a late-half progress bin with below-average kill count,
    i.e. a stretch of path where critters pass mostly unharmed.
    """
    result = ReplayAnalysis()
    for event in replay.get("events", []):
        etype = event.get("type")
        if etype == "battle_setup":
            result.path = [(p["q"], p["r"]) for p in event.get("path", [])]
        elif etype == "battle_update":
            for rc in event.get("removed_critters", []):
                progress = float(rc.get("path_progress", 0.0))
                if rc.get("reason") == "died":
                    idx = min(N_BINS - 1, int(progress * N_BINS))
                    result.death_bins[idx] += 1
                elif rc.get("reason") == "reached":
                    result.reach_count += 1
        elif etype == "battle_summary":
            result.defender_won = bool(event.get("defender_won"))

    total_deaths = sum(result.death_bins)
    if total_deaths > 0:
        mean = total_deaths / N_BINS
        for i, kills in enumerate(result.death_bins):
            # Critters reaching the castle make the LATE path weak by definition
            late = i >= N_BINS // 2
            if kills == 0 or (late and kills < 0.5 * mean):
                result.weak_segments.append((i / N_BINS, (i + 1) / N_BINS))
    elif result.reach_count > 0:
        # No kills at all but breaches: whole path is weak
        result.weak_segments = [(0.0, 1.0)]
    return result


def weight_fn_from_memory(analysis: dict | None) -> Callable[[float], float]:
    """Build a progress→weight function from a stored analysis dict (or uniform)."""
    segments = [(float(a), float(b))
                for a, b in (analysis or {}).get("weak_segments", [])]
    if not segments:
        return lambda _progress: 1.0
    return lambda p: WEAK_WEIGHT if any(a <= p < b for a, b in segments) else 1.0


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


def score_candidate_tiles(tiles: dict, path: list[tuple[int, int]],
                          tower_range: float,
                          weight_fn: Callable[[float], float],
                          tile_price: float) -> list[dict]:
    """Score owned empty tiles and purchasable void tiles by path coverage.

    Returns sorted (best first) list of {q, r, score, needs_purchase, price}.
    Purchasable = void tile adjacent to an owned non-void tile (server rule).
    The map dict only lists existing tiles — void neighbors of owned land are
    usually absent from it, so they are derived from hex adjacency here.
    """
    pts = path_points(path)
    owned = {_parse_key(k) for k, v in tiles.items() if _tile_type(v) != "void"}
    explicit_void = {_parse_key(k) for k, v in tiles.items()
                     if _tile_type(v) == "void"}
    empty = {_parse_key(k) for k, v in tiles.items() if _tile_type(v) == "empty"}
    # Implicit voids: hexes adjacent to owned land with no map entry at all
    void = explicit_void | (
        {(q + dq, r + dr) for q, r in owned for dq, dr in HEX_DIRS}
        - owned - explicit_void)
    purchasable = {(q, r) for q, r in void
                   if any((q + dq, r + dr) in owned for dq, dr in HEX_DIRS)}

    candidates: list[dict] = []
    for (q, r), needs_purchase in (
            [(t, False) for t in empty] + [(t, True) for t in purchasable]):
        score = coverage_score((q, r), tower_range, pts, weight_fn)
        if score > 0:
            candidates.append({"q": q, "r": r, "score": score,
                               "needs_purchase": needs_purchase,
                               "price": tile_price if needs_purchase else 0.0})
    candidates.sort(key=lambda c: -c["score"])
    return candidates


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


def best_relocation(tiles: dict) -> dict | None:
    """Spawn/castle placement on owned land that maximizes the critter path.

    Tries all (spawn, castle) pairs over empty tiles plus the current spots and
    returns {"tiles": new_map, "old_len": n, "new_len": m} for the longest
    shortest-path, or None when nothing beats the current layout (or the map
    has multiple spawnpoints — those layouts are left untouched).
    """
    spawns = [k for k, v in tiles.items() if _tile_type(v) == "spawnpoint"]
    castles = [k for k, v in tiles.items() if _tile_type(v) == "castle"]
    if len(spawns) != 1 or len(castles) != 1:
        return None
    current = bfs_path(tiles)
    old_len = len(current) if current else 0

    spots = [k for k, v in tiles.items() if _tile_type(v) == "empty"]
    spots += [spawns[0], castles[0]]
    best: dict | None = None
    for s_key in spots:
        for c_key in spots:
            if s_key == c_key:
                continue
            cand = dict(tiles)
            cand[spawns[0]] = "empty"
            cand[castles[0]] = "empty"
            cand[s_key] = "spawnpoint"
            cand[c_key] = "castle"
            path = bfs_path(cand)
            if path and (best is None or len(path) > best["new_len"]):
                best = {"tiles": cand, "old_len": old_len, "new_len": len(path)}
    if best is None or best["new_len"] <= old_len:
        return None
    return best


# ── Maze carving ─────────────────────────────────────────────────────────────

# Stop carving once the BFS path is this long (prod good mazes run 28-41 tiles).
MAZE_MAX_PATH_LEN = 60


def _is_tower(value) -> bool:
    """True for a placed tower/structure tile (not terrain, not void)."""
    return _tile_type(value) not in TRAVERSABLE and _tile_type(value) != "void"


def plan_maze_walls(tiles: dict, seed: int = 0) -> list[tuple[int, int]]:
    """Target wall tiles for a serpentine maze over the owned field.

    A single blocker cannot lengthen the path in an open hex block (many equal
    geodesics exist), so a real maze needs WALLS: full barriers perpendicular to
    the spawn→castle axis, each leaving a one-tile gap that alternates ends to
    force the route to double back (U-turns). This is the pattern of strong human
    mazes in prod.

    Walls run along constant q (columns); gaps alternate between the low-r and
    high-r edge of the owned block. Spawn and castle tiles are never walled.
    Returns the ordered list of (q, r) tiles to convert to towers (wall by wall,
    each wall ordered from its gap outward), best for one-tower-per-cycle play.

    `seed` randomizes the layout (gap phase, wall-column offset, gap depth) so
    different bots/runs build visibly different mazes. The plan is a pure
    function of (tiles, seed), so the same seed keeps the plan stable across
    build cycles. seed=0 keeps the legacy deterministic layout.
    """
    rng = random.Random(seed) if seed else None
    # Owned field = every non-void tile. Tower tiles count: they are owned land
    # and already act as walls — excluding them would shrink the field below
    # the 9-tile minimum as soon as coverage placement fills bought tiles.
    owned = {_parse_key(k) for k, v in tiles.items()
             if _tile_type(v) != "void"}
    spawn = next((_parse_key(k) for k, v in tiles.items()
                  if _tile_type(v) == "spawnpoint"), None)
    castle = next((_parse_key(k) for k, v in tiles.items()
                   if _tile_type(v) == "castle"), None)
    if spawn is None or castle is None or len(owned) < 9:
        return []

    qs = [q for q, _ in owned]
    q_lo, q_hi = min(qs), max(qs)
    # Wall every OTHER interior column, leaving the column between two walls as
    # an open serpentine lane (a solid block of walls would just squeeze the
    # route along one edge instead of zig-zagging it). Never wall the outermost
    # columns or the columns holding spawn/castle.
    if rng:
        # Random wall grid: shifted start column and occasional double-width
        # lanes, so each seed yields a visibly different serpentine.
        wall_qs = []
        q = q_lo + rng.choice((1, 2))
        while q < q_hi:
            if q not in (spawn[0], castle[0]):
                wall_qs.append(q)
            q += 2 if rng.random() < 0.8 else 3
    else:
        wall_qs = [q for q in range(q_lo + 1, q_hi, 2)
                   if q not in (spawn[0], castle[0])]

    walls: list[tuple[int, int]] = []
    for i, q in enumerate(wall_qs):
        col = sorted(r for (cq, r) in owned if cq == q)
        # The gap must be traversable — a gap on a tower tile would make the
        # wall a full barrier and sever the path.
        open_rs = [r for r in col
                   if _tile_type(tiles.get(f"{q},{r}")) in
                   ("empty", "path", "spawnpoint", "castle")]
        if len(col) < 2 or not open_rs:
            continue  # too short to form a wall, or no traversable gap
        # Gap alternates ends so the route must zig-zag the full column height.
        # The FIRST gap sits at the end far from the spawn (a gap on the spawn
        # side would align with the natural diagonal and yield no path gain);
        # gaps must sit at the extremes for the same reason.
        far_is_max = abs(max(open_rs) - spawn[1]) >= abs(min(open_rs) - spawn[1])
        at_max = far_is_max if i % 2 == 0 else not far_is_max
        gap_r = max(open_rs) if at_max else min(open_rs)
        # Order wall tiles from the gap outward (so a partially built wall already
        # constrains the route near the gap).
        col_tiles = [(q, r) for r in col if r != gap_r]
        col_tiles.sort(key=lambda t: -abs(t[1] - gap_r))
        walls.extend(col_tiles)

    if rng:
        # Guard: a randomized layout must actually lengthen the path (a sparse
        # or unlucky wall set may leave the natural diagonal intact). If it
        # doesn't, fall back to the deterministic legacy plan.
        sim = dict(tiles)
        for q, r in walls:
            if _tile_type(sim.get(f"{q},{r}")) == "empty":
                sim[f"{q},{r}"] = "blocked"
        base_path, new_path = bfs_path(tiles), bfs_path(sim)
        if (base_path is not None and
                (new_path is None or len(new_path) <= len(base_path))):
            return plan_maze_walls(tiles, 0)
    return walls


def sell_to_carve_candidate(tiles: dict, seed: int,
                            order: list[str]) -> str | None:
    """Key of the placed tower whose removal re-enables maze carving.

    Called when next_maze_tile(tiles, seed) is None but the path is still
    short. Tries each tower key in the given order (the caller sorts by
    defensive value, worst first): simulate the tile becoming empty and return
    the first key where carving can resume and the route stays valid.
    Returns None when no single removal helps.

    Guard against sell/rebuild churn (which only burns the 70% non-refunded
    cost): the removal counts only when carving out the WHOLE resumed plan
    leaves a path at least 2 tiles longer than the current one — simulated
    here by playing the plan to completion on a copy.
    """
    base = bfs_path(tiles)
    if base is None:
        return None
    for key in order:
        sim = dict(tiles)
        sim[key] = "empty"
        if bfs_path(sim) is None:
            continue
        for _ in range(64):  # play the resumed serpentine plan to its end
            spot = next_maze_tile(sim, seed)
            if spot is None:
                break
            sim[f"{spot[0]},{spot[1]}"] = "WALL"  # any non-traversable type
        new = bfs_path(sim)
        if new is not None and len(new) >= len(base) + 2:
            return key
    return None


def next_maze_tile(tiles: dict, seed: int = 0) -> tuple[int, int] | None:
    """Next owned empty tile to convert to a tower toward the serpentine plan.

    Returns the first planned wall tile that is still empty and whose placement
    keeps a valid spawn→castle path (mirrors the server "Weg verbaut" rule), or
    None when the maze is complete / no safe wall tile remains / the path is
    already at least MAZE_MAX_PATH_LEN long. `seed` is forwarded to
    plan_maze_walls to randomize the layout per bot.
    """
    base = bfs_path(tiles)
    if base is None or len(base) >= MAZE_MAX_PATH_LEN:
        return None
    for q, r in plan_maze_walls(tiles, seed):
        key = f"{q},{r}"
        if _tile_type(tiles.get(key)) != "empty":
            continue
        sim = dict(tiles)
        sim[key] = "blocked"
        if bfs_path(sim) is not None:
            return (q, r)
    return None


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

    placed_counts: tower class → number currently placed.
    usable: predicate (unlocked + affordable), supplied by the planner.
    top_n: among the usable towers in the chosen class, sample one of the best
    `top_n` by quality (weighted toward the best). top_n=1 → deterministic best.
    """
    candidates = [(iid, it) for iid, it in structures.items() if usable(it)]
    if not candidates:
        return None
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
