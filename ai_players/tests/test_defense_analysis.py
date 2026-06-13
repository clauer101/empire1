import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bot.defense_analysis import (  # noqa: E402
    analyze_replay, coverage_score, hex_world_distance, path_points,
    pick_tower, score_candidate_tiles, tower_class, weight_fn_from_memory,
)


def test_hex_world_distance_adjacent_is_one():
    for dq, dr in [(1, 0), (0, 1), (1, -1), (-1, 0), (0, -1), (-1, 1)]:
        assert abs(hex_world_distance(0, 0, dq, dr) - 1.0) < 1e-9
    assert hex_world_distance(0, 0, 0, 0) == 0.0
    assert hex_world_distance(0, 0, 2, 0) > 1.9


def test_path_points_progress_monotonic():
    pts = path_points([(0, 0), (1, 0), (2, 0)])
    progresses = [p for _, _, p in pts]
    assert progresses == sorted(progresses)
    assert progresses[0] == 0.0 and progresses[-1] == 1.0


def test_coverage_prefers_tile_near_more_path():
    # Straight path along q axis; tile adjacent to middle beats tile at the end
    path = [(0, 0), (1, 0), (2, 0), (3, 0), (4, 0)]
    pts = path_points(path)
    uniform = lambda _p: 1.0  # noqa: E731
    mid = coverage_score((2, 1), 1.5, pts, uniform)
    end = coverage_score((4, 1), 1.5, pts, uniform)
    far = coverage_score((10, 10), 1.5, pts, uniform)
    assert mid > end > far == 0


def test_weak_segment_weighting_flips_winner():
    path = [(0, 0), (1, 0), (2, 0), (3, 0), (4, 0)]
    pts = path_points(path)
    near_start, near_end = (0, 1), (4, -1)
    uniform = lambda _p: 1.0  # noqa: E731
    assert coverage_score(near_start, 1.5, pts, uniform) == \
        coverage_score(near_end, 1.5, pts, uniform)
    # weak segment at the end of the path → near_end tile wins
    weighted = weight_fn_from_memory({"weak_segments": [[0.7, 1.0]]})
    assert coverage_score(near_end, 1.5, pts, weighted) > \
        coverage_score(near_start, 1.5, pts, weighted)


def test_analyze_replay_weak_segments():
    replay = {"events": [
        {"type": "battle_setup", "path": [{"q": 0, "r": 0}, {"q": 1, "r": 0}]},
        {"type": "battle_update", "removed_critters": [
            {"reason": "died", "path_progress": 0.1},
            {"reason": "died", "path_progress": 0.15},
            {"reason": "died", "path_progress": 0.2},
            {"reason": "reached", "path_progress": 1.0},
        ]},
        {"type": "battle_summary", "defender_won": False},
    ]}
    a = analyze_replay(replay)
    assert a.path == [(0, 0), (1, 0)]
    assert a.reach_count == 1
    assert not a.defender_won
    # kills only early → late bins are weak
    assert any(start >= 0.5 for start, _ in a.weak_segments)
    # memory round-trip shape
    mem = a.to_memory()
    assert weight_fn_from_memory(mem)(0.95) > 1.0


def test_analyze_replay_no_kills_all_weak():
    replay = {"events": [
        {"type": "battle_update", "removed_critters": [
            {"reason": "reached", "path_progress": 1.0}]},
    ]}
    assert analyze_replay(replay).weak_segments == [(0.0, 1.0)]


def test_score_candidate_tiles_includes_purchasable_void():
    tiles = {
        "0,0": "spawnpoint", "1,0": "empty", "2,0": "castle",
        "1,1": "void",   # adjacent to owned → purchasable
        "9,9": "void",   # isolated → not purchasable
    }
    out = score_candidate_tiles(tiles, [(0, 0), (1, 0), (2, 0)], 1.5,
                                lambda _p: 1.0, tile_price=50.0)
    coords = {(c["q"], c["r"]): c for c in out}
    assert (1, 0) in coords and not coords[(1, 0)]["needs_purchase"]
    assert (1, 1) in coords and coords[(1, 1)]["needs_purchase"]
    assert coords[(1, 1)]["price"] == 50.0
    assert (9, 9) not in coords


CATALOG = {
    "DMG": {"damage": 5, "range": 2, "reload_time": 1000, "effects": {}},
    "BIG_DMG": {"damage": 10, "range": 2, "reload_time": 1000, "effects": {}},
    "ICE": {"damage": 1, "range": 2, "reload_time": 1000,
            "effects": {"slow_ratio": 0.5, "slow_duration": 2000}},
    "BOOM": {"damage": 3, "range": 2, "reload_time": 1000,
             "effects": {"splash_radius": 0.5}},
}


def test_tower_class():
    assert tower_class(CATALOG["DMG"]) == "damage"
    assert tower_class(CATALOG["ICE"]) == "slow"
    assert tower_class(CATALOG["BOOM"]) == "splash"


def test_pick_tower_balances_mix():
    usable = lambda _it: True  # noqa: E731
    # nothing placed → damage class has the biggest deficit, best damage tower wins
    assert pick_tower(CATALOG, {}, usable) == "BIG_DMG"
    # plenty of damage towers placed → slow or splash is picked
    picked = pick_tower(CATALOG, {"damage": 6}, usable)
    assert picked in ("ICE", "BOOM")
    # only one usable tower → it is picked regardless of mix
    assert pick_tower(CATALOG, {"damage": 6},
                      lambda it: it is CATALOG["DMG"]) == "DMG"


def test_bfs_path_orders_tiles():
    from bot.defense_analysis import bfs_path
    tiles = {"0,0": "spawnpoint", "1,0": "empty", "2,0": "empty", "3,0": "castle"}
    assert bfs_path(tiles) == [(0, 0), (1, 0), (2, 0), (3, 0)]
    # tower blocks the straight line entirely → no path
    tiles["1,0"] = "BASIC_TOWER"
    assert bfs_path(tiles) is None


def test_best_relocation_lengthens_path():
    from bot.defense_analysis import best_relocation, bfs_path
    # spawn and castle adjacent, empties stretching out to the right
    tiles = {"0,0": "spawnpoint", "1,0": "castle",
             "2,0": "empty", "3,0": "empty", "4,0": "empty"}
    reloc = best_relocation(tiles)
    assert reloc and reloc["new_len"] > reloc["old_len"]
    assert reloc["old_len"] == 2 and reloc["new_len"] == 5
    assert len(bfs_path(reloc["tiles"])) == 5


def test_best_relocation_none_when_already_optimal():
    from bot.defense_analysis import best_relocation
    tiles = {"0,0": "spawnpoint", "1,0": "empty", "2,0": "castle"}
    reloc = best_relocation(tiles)
    # endpoints already maximal on this map
    assert reloc is None


# ── Maze carving (serpentine wall planner) ─────────────────────────────────────

def _block(n):
    """Square owned block: spawn top-left (0,0), castle bottom-right (n-1,n-1)."""
    tiles = {f"{q},{r}": "empty" for q in range(n) for r in range(n)}
    tiles["0,0"] = "spawnpoint"
    tiles[f"{n - 1},{n - 1}"] = "castle"
    return tiles


def _carve_all(tiles):
    """Apply next_maze_tile repeatedly until the maze is complete."""
    from bot.defense_analysis import next_maze_tile
    placed = 0
    while (spot := next_maze_tile(tiles)) is not None:
        tiles[f"{spot[0]},{spot[1]}"] = "BASIC_TOWER"
        placed += 1
    return placed


def test_maze_walls_alternate_gap_ends():
    from bot.defense_analysis import plan_maze_walls
    walls = plan_maze_walls(_block(7))
    cols = {}
    for q, r in walls:
        cols.setdefault(q, []).append(r)
    # Walls live on alternating interior columns (every other q).
    wall_qs = sorted(cols)
    assert wall_qs == [1, 3, 5]
    # Each wall covers all-but-one row of the block (one gap tile per column).
    for q in wall_qs:
        assert len(cols[q]) == 6  # 7 rows minus the gap


def test_maze_carving_lengthens_path_serpentine():
    from bot.defense_analysis import bfs_path
    tiles = _block(7)
    start = len(bfs_path(tiles))
    placed = _carve_all(tiles)
    final = len(bfs_path(tiles))
    # The serpentine more than doubles a 7x7 block's straight diagonal path.
    assert final > start
    assert final >= 20 and placed > 0


def test_next_maze_tile_never_severs_path():
    from bot.defense_analysis import bfs_path, next_maze_tile
    # 1-wide strip: the only empty carries the only route → no safe wall tile.
    tiles = {"0,0": "spawnpoint", "1,0": "empty", "2,0": "castle"}
    assert next_maze_tile(tiles) is None
    # And carving a block must always leave a valid path at every step.
    tiles = _block(7)
    while (spot := next_maze_tile(tiles)) is not None:
        tiles[f"{spot[0]},{spot[1]}"] = "BASIC_TOWER"
        assert bfs_path(tiles) is not None


def test_next_maze_tile_respects_max_path_len():
    from bot.defense_analysis import (
        MAZE_MAX_PATH_LEN, bfs_path, next_maze_tile,
    )
    # A long pre-built straight strip already exceeds the cap → stop carving.
    n = MAZE_MAX_PATH_LEN + 2
    tiles = {f"{q},0": "empty" for q in range(n)}
    tiles["0,0"] = "spawnpoint"
    tiles[f"{n - 1},0"] = "castle"
    assert len(bfs_path(tiles)) >= MAZE_MAX_PATH_LEN
    assert next_maze_tile(tiles) is None


def test_plan_maze_walls_empty_when_field_too_small():
    from bot.defense_analysis import plan_maze_walls
    tiles = {"0,0": "spawnpoint", "1,0": "empty", "2,0": "castle"}
    assert plan_maze_walls(tiles) == []


def test_plan_maze_walls_seed_varies_and_is_stable():
    from bot.defense_analysis import plan_maze_walls
    tiles = _block(7)
    plans = {tuple(plan_maze_walls(tiles, seed)) for seed in range(1, 30)}
    assert len(plans) > 1                                   # seeds differ
    for seed in (1, 7, 23):                                 # same seed = stable
        assert plan_maze_walls(tiles, seed) == plan_maze_walls(tiles, seed)
    assert plan_maze_walls(tiles, 0) == plan_maze_walls(tiles)  # legacy default


def test_sell_to_carve_candidate_finds_blocking_tower():
    from bot.defense_analysis import (
        bfs_path, next_maze_tile, plan_maze_walls, sell_to_carve_candidate,
    )
    # Block a wall-gap tile with a tower, then carve until stalled: the maze
    # freezes short of its serpentine plan.
    tiles = _block(7)
    walls = set(plan_maze_walls(tiles, 0))
    gap = next((q, r) for q in (1,) for r in range(7) if (q, r) not in walls)
    tiles[f"{gap[0]},{gap[1]}"] = "BASIC_TOWER"
    while (spot := next_maze_tile(tiles, 0)) is not None:
        tiles[f"{spot[0]},{spot[1]}"] = "BASIC_TOWER"
    assert next_maze_tile(tiles, 0) is None
    towers = [k for k, v in tiles.items() if v == "BASIC_TOWER"]
    key = sell_to_carve_candidate(tiles, 0, towers)
    assert key is not None
    sim = dict(tiles)
    sim[key] = "empty"
    assert bfs_path(sim) is not None
    assert next_maze_tile(sim, 0) is not None  # carving resumes


def test_sell_to_carve_candidate_none_when_no_removal_helps():
    from bot.defense_analysis import next_maze_tile, sell_to_carve_candidate
    # 1-wide strip: too small for any maze regardless of which tower goes.
    tiles = {"0,0": "spawnpoint", "1,0": "empty", "2,0": "castle",
             "1,1": "BASIC_TOWER"}
    assert next_maze_tile(tiles, 0) is None
    assert sell_to_carve_candidate(tiles, 0, ["1,1"]) is None


def test_seeded_carving_still_lengthens_path_and_keeps_route():
    from bot.defense_analysis import bfs_path, next_maze_tile
    for seed in (1, 7, 23, 42):
        tiles = _block(7)
        start = len(bfs_path(tiles))
        while (spot := next_maze_tile(tiles, seed)) is not None:
            tiles[f"{spot[0]},{spot[1]}"] = "BASIC_TOWER"
            assert bfs_path(tiles) is not None
        assert len(bfs_path(tiles)) > start
