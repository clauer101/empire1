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


# ── Spiral maze (alternating path / tower rings) ─────────────────────────────
#
# Dead simple and fully deterministic: rings around the castle alternate between
# a row of PATH (odd radius) and a row of TOWERS (even radius). Each tower ring
# has exactly one gap; the gap rotates a little ring-to-ring so the critter route
# threads gap-to-gap and spirals down to the castle. Every tile is either path or
# tower — no dead-ends, no empty pockets — and there is no randomness.
#
# Build order (per cycle, one action): place a tower wherever the plan calls for
# one and the path survives (towers first), else buy the next field tile, else
# park the spawn at the outer mouth. The plan depends only on the tile's ring, so
# the same spiral just extends outward as the field grows.

# Outermost ring the spiral grows to (each ring adds ~6·r tiles).
SPIRAL_MAX_RADIUS = 11
# Fraction of a ring the single gap rotates per successive tower ring, so the
# gaps line up into a spiral rather than a straight radial seam.
SPIRAL_GAP_STEP = 0.125


def _hex_distance(q: int, r: int) -> int:
    """Axial hex distance from the origin to (q, r)."""
    return (abs(q) + abs(r) + abs(q + r)) // 2


def _hex_angle(q: int, r: int) -> float:
    """Angle (radians, [0, 2π)) of tile (q, r) around the origin in hex world."""
    x = 1.5 * q
    y = math.sqrt(3) * (r + 0.5 * q)
    a = math.atan2(y, x)
    return a + 2 * math.pi if a < 0 else a


def hex_ring(radius: int) -> list[tuple[int, int]]:
    """Ordered offsets of the 6·radius hexes at hex-distance `radius` from origin.

    Walks the ring using HEX_DIRS (red-blob ordering): start at direction[4]
    scaled by `radius`, then step `radius` tiles along each of the 6 directions.
    `radius <= 0` returns the single origin tile.
    """
    if radius <= 0:
        return [(0, 0)]
    results: list[tuple[int, int]] = []
    sq, sr = HEX_DIRS[4]
    q, r = sq * radius, sr * radius
    for dq, dr in HEX_DIRS:
        for _ in range(radius):
            results.append((q, r))
            q, r = q + dq, r + dr
    return results


def _spiral_gap_offset(radius: int) -> tuple[int, int]:
    """The single gap tile (offset from castle) of the tower ring at `radius`."""
    ring = hex_ring(radius)
    gap_idx = int(round((radius // 2) * SPIRAL_GAP_STEP * len(ring))) % len(ring)
    return ring[gap_idx]


def spiral_is_wall(dq: int, dr: int, seed: int = 0) -> bool:
    """True if the tile at offset (dq, dr) from the castle is a planned tower.

    Even-radius rings are tower rows (minus their one gap); odd-radius rings and
    the castle are path. Fully deterministic — `seed` is accepted only for a
    uniform interface with the other planners and is ignored.
    """
    k = _hex_distance(dq, dr)
    if k == 0 or k % 2 == 1:
        return False
    return (dq, dr) != _spiral_gap_offset(k)


def _spiral_path_len(tiles: dict, spawn_key: str) -> int:
    """Spawn→castle BFS length with the spawnpoint moved to `spawn_key` (0 = no path)."""
    sim = dict(tiles)
    for k, v in sim.items():
        if _tile_type(v) == "spawnpoint":
            sim[k] = "empty"
    sim[spawn_key] = "spawnpoint"
    path = bfs_path(sim)
    return len(path) if path else 0


def _best_spawn(tiles: dict, castle: tuple[int, int],
                seed: int) -> tuple[int, int] | None:
    """Owned corridor tile that maximises the spawn→castle path (the design goal).

    Restricted to the outermost owned ring so the mouth stays at the field edge;
    ties broken deterministically. Only tiles that keep a valid path qualify.
    """
    cq, cr = castle
    corridor = [(q, r) for (q, r) in
                (_parse_key(k) for k, v in tiles.items() if _tile_type(v) != "void")
                if (q, r) != castle and not spiral_is_wall(q - cq, r - cr, seed)]
    if not corridor:
        return None
    outer = max(_hex_distance(q - cq, r - cr) for q, r in corridor)
    ring = [(q, r) for q, r in corridor
            if _hex_distance(q - cq, r - cr) == outer]
    best: tuple[int, int] | None = None
    best_key = (-1, 0.0)
    for q, r in ring:
        plen = _spiral_path_len(tiles, f"{q},{r}")
        if plen == 0:
            continue
        key = (plen, -_hex_angle(q - cq, r - cr))
        if key > best_key:
            best_key, best = key, (q, r)
    return best


def next_spiral_action(tiles: dict, *, seed: int = 0,
                       max_radius: int = SPIRAL_MAX_RADIUS) -> dict | None:
    """Next single build step toward the snail-shell spiral, or None.

    Priority (per the strategy): place a wall tower whenever one fits, else buy
    the next field tile, else park the spawn at the outer mouth. Returns one of
    {"kind":"tower"|"buy"|"spawn", "q", "r"} or None when the snail is complete
    out to `max_radius` (or the path has reached MAZE_MAX_PATH_LEN).
    """
    castle = next((_parse_key(k) for k, v in tiles.items()
                   if _tile_type(v) == "castle"), None)
    if castle is None:
        return None
    cq, cr = castle
    spawn = next((_parse_key(k) for k, v in tiles.items()
                  if _tile_type(v) == "spawnpoint"), None)

    owned = [(q, r) for (q, r) in
             (_parse_key(k) for k, v in tiles.items() if _tile_type(v) != "void")]
    max_r = max((_hex_distance(q - cq, r - cr) for q, r in owned), default=0)

    # 0. Park the spawn at the mouth that maximises the spawn→castle path (the
    #    optimisation target), so the BFS guard below protects the real coil
    #    rather than a trivial spawn-adjacent-to-castle path. Only relocate when
    #    it strictly improves, and only to a tile that keeps a valid path.
    mouth = _best_spawn(tiles, castle, seed)
    if mouth is not None and spawn != mouth:
        cur_len = (_spiral_path_len(tiles, f"{spawn[0]},{spawn[1]}")
                   if spawn is not None else 0)
        if _spiral_path_len(tiles, f"{mouth[0]},{mouth[1]}") > cur_len:
            return {"kind": "spawn", "q": mouth[0], "r": mouth[1]}

    # 1. TOWER-FIRST: wherever three empty tiles touch (a spot wider than one
    #    tile), wall one of them — provided it keeps a valid spawn→castle path.
    #    This tightens the maze to a width-1 coil and lengthens the path. Prefer
    #    the snail's wall tile, then nearest the castle, for a stable spiral.
    triangle = _empty_triangle_tiles(tiles)
    candidates = sorted(
        triangle,
        key=lambda t: (0 if spiral_is_wall(t[0] - cq, t[1] - cr, seed) else 1,
                       _hex_distance(t[0] - cq, t[1] - cr)))
    for q, r in candidates:
        sim = dict(tiles)
        sim[f"{q},{r}"] = "blocked"
        if bfs_path(sim) is not None:
            return {"kind": "tower", "q": q, "r": r}

    # 2. BUY (no tower placeable): grow the field inside-out out to the radius
    #    cap (maximising the path is the goal, so we fill the whole snail), but
    #    always finish owning the current frontier ring first.
    target = max_r if max_r >= max_radius else max_r + 1
    for rad in range(1, target + 1):
        for dq, dr in hex_ring(rad):
            q, r = cq + dq, cr + dr
            key = f"{q},{r}"
            if key not in tiles or _tile_type(tiles[key]) == "void":
                return {"kind": "buy", "q": q, "r": r}

    return None


# ── Boustrophedon comb (space-filling-curve maze) ────────────────────────────
#
# A space-filling curve is a single continuous path that visits every cell of a
# region; the simplest one is the boustrophedon ("ox-plough") serpentine, where
# lanes snake back and forth and connect at alternating ends. This builds that
# maze explicitly: every OTHER line (columns of constant q, or rows of constant
# r when the seed flips orientation) is a full tower wall with one traversable
# gap, so the corridor must double back and every corridor lane is flanked by
# tower walls on BOTH sides. Full wall lines are used (rather than scattered
# blockers) because they also block the two diagonal hex neighbours that would
# otherwise let critters leak sideways between parallel lanes.
#
# Build order per cycle (one action): park the spawn at the field corner that
# maximises the path, then place a wall tower wherever one fits (towers first),
# otherwise buy the next field tile to grow the region out to COMB_MAX_EXTENT.

# Hex-distance the comb grows the owned field to (each ring adds ~6·r tiles).
COMB_MAX_EXTENT = 5


def plan_comb_walls(tiles: dict, seed: int = 0) -> list[tuple[int, int]]:
    """Ordered wall tiles for a dense boustrophedon comb over the owned field.

    Every other line is walled full-height with a single traversable gap; gaps
    alternate ends line-to-line so the route zig-zags (U-turns) and each corridor
    lane ends up flanked by tower walls on both sides. Spawn and castle lines are
    never walled. Tiles are ordered gap-outward so a partially built wall already
    constrains the route, which suits one-tower-per-cycle play. `seed` picks the
    orientation (columns vs rows) and start offset for per-bot variety; the plan
    is a pure function of (tiles, seed), and seed=0 is the deterministic layout.
    """
    rng = random.Random(seed) if seed else None
    owned = {_parse_key(k) for k, v in tiles.items() if _tile_type(v) != "void"}
    spawn = next((_parse_key(k) for k, v in tiles.items()
                  if _tile_type(v) == "spawnpoint"), None)
    castle = next((_parse_key(k) for k, v in tiles.items()
                   if _tile_type(v) == "castle"), None)
    if spawn is None or castle is None or len(owned) < 9:
        return []

    # Wall lines run along constant `axis` (0 = columns of constant q, 1 = rows
    # of constant r); `cross` is the coordinate that varies along a wall line.
    axis = rng.randint(0, 1) if rng else 0
    cross = 1 - axis
    lines = sorted({t[axis] for t in owned})
    lo, hi = lines[0], lines[-1]
    start = lo + 1 + (rng.choice((0, 1)) if rng else 0)
    wall_lines = [n for n in range(start, hi, 2)
                  if n not in (spawn[axis], castle[axis])]

    walls: list[tuple[int, int]] = []
    for i, n in enumerate(wall_lines):
        line = sorted(t for t in owned if t[axis] == n)
        open_tiles = [t for t in line
                      if _tile_type(tiles.get(f"{t[0]},{t[1]}")) in
                      ("empty", "path", "spawnpoint", "castle")]
        if len(line) < 2 or not open_tiles:
            continue
        open_vals = [t[cross] for t in open_tiles]
        # First gap sits at the end far from the spawn (a near-side gap aligns
        # with the natural diagonal and yields no path gain); then alternate.
        far_is_max = (abs(max(open_vals) - spawn[cross])
                      >= abs(min(open_vals) - spawn[cross]))
        at_max = far_is_max if i % 2 == 0 else not far_is_max
        gap = max(open_vals) if at_max else min(open_vals)
        line_tiles = [t for t in line if t[cross] != gap]
        line_tiles.sort(key=lambda t: -abs(t[cross] - gap))
        walls.extend(line_tiles)

    if rng:
        # A randomized orientation must actually lengthen the path; if it does
        # not, fall back to the deterministic layout (mirrors plan_maze_walls).
        sim = dict(tiles)
        for q, r in walls:
            if _tile_type(sim.get(f"{q},{r}")) == "empty":
                sim[f"{q},{r}"] = "blocked"
        base_path, new_path = bfs_path(tiles), bfs_path(sim)
        if (base_path is not None and
                (new_path is None or len(new_path) <= len(base_path))):
            return plan_comb_walls(tiles, 0)
    return walls


def _best_comb_spawn(tiles: dict,
                     castle: tuple[int, int]) -> tuple[int, int] | None:
    """Owned outer-ring tile that maximises the spawn→castle path.

    Mirrors _best_spawn but without a wall classification: restrict to the
    outermost owned ring (so the mouth stays at the field edge), keep only tiles
    that leave a valid path, and break ties deterministically by angle.
    """
    cq, cr = castle
    owned = [(q, r) for (q, r) in
             (_parse_key(k) for k, v in tiles.items() if _tile_type(v) != "void")
             if (q, r) != castle]
    if not owned:
        return None
    outer = max(_hex_distance(q - cq, r - cr) for q, r in owned)
    ring = [(q, r) for q, r in owned if _hex_distance(q - cq, r - cr) == outer]
    best: tuple[int, int] | None = None
    best_key = (-1, 0.0)
    for q, r in ring:
        plen = _spiral_path_len(tiles, f"{q},{r}")
        if plen == 0:
            continue
        key = (plen, -_hex_angle(q - cq, r - cr))
        if key > best_key:
            best_key, best = key, (q, r)
    return best


def next_comb_action(tiles: dict, *, seed: int = 0,
                     max_extent: int = COMB_MAX_EXTENT) -> dict | None:
    """Next single build step toward the boustrophedon comb, or None.

    Priority (one action per call): park the spawn at the mouth that maximises
    the path, else place a wall tower wherever one fits (towers first), else buy
    the next field tile out to `max_extent`. Returns one of
    {"kind":"spawn"|"tower"|"buy", "q", "r"} or None when the comb is complete
    (or the path has reached MAZE_MAX_PATH_LEN).
    """
    castle = next((_parse_key(k) for k, v in tiles.items()
                   if _tile_type(v) == "castle"), None)
    if castle is None:
        return None
    cq, cr = castle
    spawn = next((_parse_key(k) for k, v in tiles.items()
                  if _tile_type(v) == "spawnpoint"), None)

    base = bfs_path(tiles)
    if base is not None and len(base) >= MAZE_MAX_PATH_LEN:
        return None

    owned = [(q, r) for (q, r) in
             (_parse_key(k) for k, v in tiles.items() if _tile_type(v) != "void")]

    # 0. Park the spawn at the mouth that maximises the path, so the BFS guard
    #    below protects the real corridor rather than a spawn-adjacent shortcut.
    mouth = _best_comb_spawn(tiles, castle)
    if mouth is not None and spawn != mouth:
        cur_len = (_spiral_path_len(tiles, f"{spawn[0]},{spawn[1]}")
                   if spawn is not None else 0)
        if _spiral_path_len(tiles, f"{mouth[0]},{mouth[1]}") > cur_len:
            return {"kind": "spawn", "q": mouth[0], "r": mouth[1]}

    # 1. TOWER-FIRST: convert the first planned wall tile that is still empty and
    #    whose placement keeps a valid spawn→castle path.
    for q, r in plan_comb_walls(tiles, seed):
        key = f"{q},{r}"
        if _tile_type(tiles.get(key)) != "empty":
            continue
        sim = dict(tiles)
        sim[key] = "blocked"
        if bfs_path(sim) is not None:
            return {"kind": "tower", "q": q, "r": r}

    # 2. BUY (no tower placeable): grow the field ring-by-ring out to the extent
    #    cap, always finishing the current frontier ring first (hex_ring keeps
    #    every new tile adjacent to owned land, the server purchase rule).
    max_r = max((_hex_distance(q - cq, r - cr) for q, r in owned), default=0)
    target = max_r if max_r >= max_extent else max_r + 1
    for rad in range(1, target + 1):
        for dq, dr in hex_ring(rad):
            q, r = cq + dq, cr + dr
            key = f"{q},{r}"
            if key not in tiles or _tile_type(tiles[key]) == "void":
                return {"kind": "buy", "q": q, "r": r}

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
