import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bot.dispatch import choose_action  # noqa: E402
from bot.planners.base import BotContext  # noqa: E402
from bot.planners.defense import DefensePlanner  # noqa: E402

# Minimal dispatcher config: no category weighting, deterministic.
DISPATCH_CONFIG = {"category_weights": {}, "active_strategy_boost": 1.0,
                   "selection": {"top_n": 1}}

# Straight path along r=0; (1,1) covers it (adjacent), (2,1) is purchasable void
# adjacent both to owned land and to the path.
TILES = {"0,0": "spawnpoint", "1,0": "path", "2,0": "path",
         "3,0": "castle", "1,1": "empty", "2,1": "void"}

ITEMS = {
    "buildings": {},
    "knowledge": {},
    "structures": {
        "BASIC_TOWER": {"costs": {"gold": 50}, "requirements": [],
                        "damage": 1, "range": 1.5, "reload_time": 2000,
                        "effects": {}},
    },
}


class FakeApi:
    def __init__(self, tiles):
        self.tiles = tiles
        self.saved = None

    def get_map(self):
        return {"tiles": dict(self.tiles)}

    def save_map(self, new_tiles):
        self.saved = dict(new_tiles)
        return {"success": True}


def _ctx(tiles, gold=100, tile_price=30, memory=None, current_era="stone"):
    summary = {"resources": {"gold": gold, "culture": 0},
               "research_queue": "X", "build_queue": "Y",
               "buildings": {}, "knowledge": {}, "era": "stone",
               "current_era": current_era,
               "item_upgrade_prices": {}, "tile_price": tile_price}
    # memory persists across cycles in the live bot (holds e.g. maze_seed)
    return BotContext(summary, ITEMS, memory if memory is not None else {},
                      {"type": "defense", "valid_until": "2099-01-01T00:00:00Z"},
                      FakeApi(tiles), personality="balanced")


def test_buys_tile_when_owned_cover_spots_run_low():
    # Only one owned covering spot left (< MIN_OWNED_COVER_SPOTS=2) → expand.
    action = DefensePlanner().propose(_ctx(TILES))
    assert action and "buy tile" in action.description  # implicit voids count too


def test_saves_for_tile_when_expansion_unaffordable():
    tiles = dict(TILES)
    del tiles["1,1"]  # no owned covering spot at all
    ctx = _ctx(tiles, gold=10, tile_price=30)
    # The dispatcher declares the savings goal for the unaffordable top option
    # (a tile) and returns no action this cycle.
    action = choose_action(ctx, DISPATCH_CONFIG, "defense", None)
    assert action is None
    goal = ctx.memory.get("savings_goal")
    assert goal and goal["action"] == "tile" and goal["amount"] == 30


def test_places_tower_when_reserve_is_sufficient():
    tiles = dict(TILES)
    tiles["0,1"] = "empty"  # second owned covering spot → reserve OK
    # tile_price above gold: maze widening unaffordable → the dispatcher skips it
    # and falls through to the affordable coverage placement.
    action = choose_action(_ctx(tiles, tile_price=200), DISPATCH_CONFIG,
                           "defense", None)
    assert action and "place" in action.description
    assert "BASIC_TOWER" in action.description


def test_density_cap_stops_tower_placement():
    # 2-tile path with 4 towers → density 2.0 ≥ cap: no coverage towers.
    # Maze growth (carve / buy tile to widen) stays allowed — carving
    # lengthens the path and thus LOWERS density.
    tiles = {"0,0": "spawnpoint", "1,0": "castle",
             "0,1": "BASIC_TOWER", "1,1": "BASIC_TOWER",
             "2,0": "BASIC_TOWER", "2,1": "BASIC_TOWER",
             "0,2": "empty", "1,2": "empty"}
    ctx = _ctx(tiles, gold=10_000)
    ctx.summary["item_upgrades"] = {
        "BASIC_TOWER": {s: 20 for s in
                        ("damage", "range", "reload",
                         "effect_duration", "effect_value")}}
    action = DefensePlanner().propose(ctx)
    assert action is None or "place" not in action.description


def test_carves_maze_on_open_field():
    from bot.defense_analysis import bfs_path
    # Open 6x6 owned block: spawn top-left, castle bottom-right. Base path is the
    # straight diagonal (short, under target); density 0; plenty of gold → the
    # planner should carve a serpentine wall (lengthen the critter path).
    tiles = {f"{q},{r}": "empty" for q in range(6) for r in range(6)}
    tiles["0,0"] = "spawnpoint"
    tiles["5,5"] = "castle"
    old_len = len(bfs_path(tiles))

    import re
    # Drive the planner cycle-by-cycle (one tower per cycle, like the bot) and
    # confirm it carves a serpentine that lengthens the path and never severs it.
    memory = {}  # persistent like the live bot, so the maze seed is stable
    for _ in range(40):
        action = DefensePlanner().propose(_ctx(tiles, gold=10_000, memory=memory))
        if not (action and "carve maze" in action.description):
            break
        q, r = map(int, re.search(r"at (-?\d+),(-?\d+)",
                                  action.description).groups())
        tiles[f"{q},{r}"] = "BASIC_TOWER"
        assert bfs_path(tiles) is not None  # always a valid path
    assert len(bfs_path(tiles)) > old_len


def _stalled_maze_tiles():
    """7x7 block where a tower on a wall-gap tile froze carving short."""
    from bot.defense_analysis import next_maze_tile, plan_maze_walls
    tiles = {f"{q},{r}": "empty" for q in range(7) for r in range(7)}
    tiles["0,0"] = "spawnpoint"
    tiles["6,6"] = "castle"
    walls = set(plan_maze_walls(tiles, 0))
    gap = next((1, r) for r in range(7) if (1, r) not in walls)
    tiles[f"{gap[0]},{gap[1]}"] = "BASIC_TOWER"
    while (spot := next_maze_tile(tiles, 0)) is not None:
        tiles[f"{spot[0]},{spot[1]}"] = "BASIC_TOWER"
    return tiles


def test_sells_tower_to_unblock_maze():
    from bot.defense_analysis import bfs_path
    tiles = _stalled_maze_tiles()
    # Widening tile unaffordable (tile_price >> gold), rebuild affordable
    # (gold >= tower cost) → the sell-to-carve option is the affordable way to
    # resume carving. Drive cycles via the dispatcher until the sell appears.
    memory = {"maze_seed": 0}
    action = None
    for _ in range(5):
        ctx = _ctx(tiles, gold=100, tile_price=10_000, memory=memory)
        action = choose_action(ctx, DISPATCH_CONFIG, "defense", None)
        assert action is not None
        if "sell tower" in action.description:
            break
        action.run(ctx.api)
        tiles = ctx.api.saved
    assert action and "sell tower" in action.description
    action.run(ctx.api)
    saved = ctx.api.saved
    sold = [k for k, v in saved.items()
            if v == "empty" and tiles[k] == "BASIC_TOWER"]
    assert len(sold) == 1
    assert bfs_path(saved) is not None


def test_no_sell_when_rebuild_unaffordable():
    tiles = _stalled_maze_tiles()
    # gold below tower cost → outer carving guard blocks the sell entirely.
    ctx = _ctx(tiles, gold=10, tile_price=10_000, memory={"maze_seed": 0})
    action = DefensePlanner().propose(ctx)
    assert action is None or "sell tower" not in action.description


TIER_ITEMS = {
    "buildings": {},
    "knowledge": {},
    "structures": {
        "WEAK_TOWER": {"costs": {"gold": 100}, "requirements": [],
                       "era": "stone",
                       "damage": 1, "range": 1.5, "reload_time": 1000,
                       "effects": {}},
        "STRONG_TOWER": {"costs": {"gold": 200}, "requirements": [],
                         "era": "bronze",
                         "damage": 10, "range": 1.5, "reload_time": 1000,
                         "effects": {}},
    },
}


def _tier_up_tiles():
    """Path lined with weak towers on both sides: density 2.0, no covering
    spots left (ring-2 voids are out of tower range → score 0)."""
    tiles = {f"{q},0": "path" for q in range(10)}
    tiles["0,0"] = "spawnpoint"
    tiles["9,0"] = "castle"
    for q in range(10):
        tiles[f"{q},-1"] = "WEAK_TOWER"
        tiles[f"{q},1"] = "WEAK_TOWER"
    # Cap the strip ends too, so no purchasable void is in tower range
    for key in ("-1,0", "-1,1", "10,0", "10,-1"):
        tiles[key] = "WEAK_TOWER"
    return tiles


def _tier_ctx(gold):
    # current_era=bronze → WEAK_TOWER (stone) is outdated, STRONG_TOWER (bronze)
    # is the current-era replacement. tile_price huge so expansion never wins.
    ctx = _ctx(_tier_up_tiles(), gold=gold, tile_price=10_000,
               memory={"maze_seed": 1}, current_era="bronze")
    ctx.items = TIER_ITEMS
    return ctx


def test_era_swap_replaces_outdated_tower():
    # gold 180 < STRONG cost 200, but 180 + 30% refund of WEAK (30) covers it.
    ctx = _tier_ctx(gold=180)
    action = DefensePlanner().propose(ctx)
    assert action and "era-swap" in action.description
    assert "STRONG_TOWER" in action.description
    action.run(ctx.api)
    saved = ctx.api.saved
    assert sum(1 for v in saved.values() if v == "STRONG_TOWER") == 1
    assert sum(1 for v in saved.values() if v == "WEAK_TOWER") == 23


def test_no_era_swap_when_replacement_is_same_era():
    # No current-era tower available (both towers are stone) → nothing to swap.
    ctx = _tier_ctx(gold=180)
    ctx.summary["current_era"] = "stone"
    action = DefensePlanner().propose(ctx)
    assert action is None or "era-swap" not in action.description


def test_no_era_swap_when_budget_with_refund_insufficient():
    # 150 + 30 refund = 180 < 200 → era-swap unaffordable. Via the dispatcher
    # the swap is not executed (it may save toward it instead).
    ctx = _tier_ctx(gold=150)
    action = choose_action(ctx, DISPATCH_CONFIG, "defense", None)
    assert action is None or "era-swap" not in action.description


def test_sim_api_refunds_on_tower_sell():
    from bot.sim import SimApi
    structures = TIER_ITEMS["structures"]
    tiles = {"0,0": "spawnpoint", "1,0": "empty", "2,0": "castle",
             "1,1": "WEAK_TOWER"}
    state = {"gold": 0.0, "tiles_bought": 0, "tile_price": 10.0,
             "item_upgrades": {}, "completed": {}, "upgrade_base_by_iid": {}}
    api = SimApi(tiles, structures, {}, state, {"u": 0, "y": 1, "z": 1, "v": 1})
    new_tiles = dict(tiles)
    new_tiles["1,1"] = "empty"
    assert api.save_map(new_tiles)["success"]
    assert state["gold"] == 30.0  # 30% of the 100g WEAK_TOWER


def test_never_places_tower_that_blocks_the_only_path():
    # (1,0) carries the only route spawn→castle — must not be a tower spot;
    # with no other owned spot the planner expands by buying a tile instead.
    tiles = {"0,0": "spawnpoint", "1,0": "empty", "2,0": "castle"}
    action = DefensePlanner().propose(_ctx(tiles, gold=1000))
    assert action is not None
    assert "place" not in action.description
    assert "buy tile" in action.description
