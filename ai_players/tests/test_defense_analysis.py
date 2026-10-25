import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bot.defense_analysis import (  # noqa: E402
    HEX_DIRS, corridor_from_map, coverage_score, end_state, hex_world_distance,
    path_points, pick_tower, tower_class,
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


# ── Map-derived corridor (replaces the persisted maze geometry) ──────────────

def test_corridor_from_map_prefers_server_path():
    # Two equal-length routes exist; the server's own path field decides which
    # one the critters walk, so it must win over a locally computed guess.
    tiles = {"0,0": "spawnpoint", "1,0": "path", "0,1": "path", "1,1": "castle"}
    route, corridor_set = corridor_from_map(
        {"tiles": tiles, "path": [[0, 0], [0, 1], [1, 1]]})
    assert route == [(0, 0), (0, 1), (1, 1)]
    assert corridor_set == {(0, 0), (1, 0), (0, 1), (1, 1)}


def test_corridor_from_map_falls_back_to_bfs_without_path_key():
    # The maze-sim's SimApi returns {"tiles": ...} with no path field.
    tiles = {"0,0": "spawnpoint", "1,0": "path", "2,0": "castle"}
    route, _ = corridor_from_map({"tiles": tiles})
    assert route == [(0, 0), (1, 0), (2, 0)]


def test_corridor_from_map_excludes_empty_shortcut_tiles():
    # An untowered "empty" is traversable, so the server route may cut through
    # it — but it is a tower spot, not committed corridor.
    tiles = {"0,0": "spawnpoint", "1,0": "empty", "2,0": "castle",
             "0,1": "path", "1,1": "path"}
    route, corridor_set = corridor_from_map(
        {"tiles": tiles, "path": [[0, 0], [1, 0], [2, 0]]})
    assert (1, 0) not in corridor_set
    assert (1, 0) not in route
    assert {(0, 1), (1, 1)} <= corridor_set


def test_corridor_from_map_returns_empty_route_without_connection():
    tiles = {"0,0": "spawnpoint", "5,5": "castle"}
    route, corridor_set = corridor_from_map({"tiles": tiles, "path": None})
    assert route == []
    assert corridor_set == {(0, 0), (5, 5)}


def test_corridor_endpoints_are_spawn_and_castle():
    tiles = {"0,0": "spawnpoint", "1,0": "path", "2,0": "path", "3,0": "castle"}
    route, _ = corridor_from_map({"tiles": tiles})
    assert tiles[f"{route[0][0]},{route[0][1]}"] == "spawnpoint"
    assert tiles[f"{route[-1][0]},{route[-1][1]}"] == "castle"


def test_end_state_reads_heading_and_run_length():
    # Walk outward-first: three straight steps along +q.
    heading, seg_steps, _ = end_state([(3, 0), (2, 0), (1, 0), (0, 0)])
    assert HEX_DIRS[heading] == (1, 0)
    assert seg_steps == 3


def test_end_state_stops_at_a_gap():
    # A filtered-out shortcut leaves a non-adjacent step; history must stop
    # there rather than deriving a bogus heading from it.
    heading, seg_steps, _ = end_state([(1, 0), (0, 0), (9, 9)])
    assert HEX_DIRS[heading] == (1, 0)
    assert seg_steps == 1


def test_end_state_defaults_for_a_single_tile():
    assert end_state([(0, 0)]) == (0, 0, 1)
    assert end_state([]) == (0, 0, 1)
