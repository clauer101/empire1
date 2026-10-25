import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bot.planners.base import BotContext  # noqa: E402
from bot.planners.defense_frontier import (  # noqa: E402
    PRIO_BUY_SIDE,
    PRIO_UPGRADE,
    FrontierDefensePlanner,
    _applicable_upgrade_stats,
    _most_common_placed_tower,
)

STRUCTURES = {
    "ARROW_TOWER": {"range": 1.5, "damage": 5, "era": "stone"},
    "CANNON_TOWER": {"range": 2.0, "damage": 10, "era": "stone"},
}


def _ctx(summary):
    return BotContext(summary, {}, {}, {}, api=None)


def test_most_common_placed_tower_picks_majority():
    tiles = {"0,0": "ARROW_TOWER", "1,0": "ARROW_TOWER", "2,0": "CANNON_TOWER",
            "3,0": "path", "4,0": "void"}
    assert _most_common_placed_tower(tiles, STRUCTURES) == "ARROW_TOWER"


def test_most_common_placed_tower_tie_break_deterministic():
    tiles = {"0,0": "ARROW_TOWER", "1,0": "CANNON_TOWER"}
    # Tie → alphabetically-first iid, deterministic across calls.
    assert _most_common_placed_tower(tiles, STRUCTURES) == "ARROW_TOWER"


def test_most_common_placed_tower_none_when_nothing_placed():
    assert _most_common_placed_tower({"0,0": "path", "1,0": "void"}, STRUCTURES) is None


def test_upgrade_option_targets_most_placed_tower():
    tiles = {"0,0": "ARROW_TOWER", "1,0": "ARROW_TOWER", "2,0": "CANNON_TOWER"}
    summary = {"item_upgrade_prices": {"ARROW_TOWER": 100.0, "CANNON_TOWER": 50.0},
              "item_upgrades": {}}
    opt = FrontierDefensePlanner()._upgrade_option(_ctx(summary), tiles, STRUCTURES)
    assert opt is not None
    assert "ARROW_TOWER" in opt.description  # most-placed, even though pricier
    assert opt.price == 100.0


def test_upgrade_option_none_when_no_price():
    tiles = {"0,0": "ARROW_TOWER"}
    summary = {"item_upgrade_prices": {}, "item_upgrades": {}}
    assert FrontierDefensePlanner()._upgrade_option(_ctx(summary), tiles, STRUCTURES) is None


def test_upgrade_option_skips_maxed_stats():
    tiles = {"0,0": "ARROW_TOWER"}
    maxed = {stat: 20 for stat in ("range", "damage", "reload", "effect_duration",
                                   "effect_value")}
    summary = {"item_upgrade_prices": {"ARROW_TOWER": 100.0},
              "item_upgrades": {"ARROW_TOWER": maxed}}
    assert FrontierDefensePlanner()._upgrade_option(_ctx(summary), tiles, STRUCTURES) is None


def test_upgrade_is_absolute_last_priority():
    assert PRIO_UPGRADE < PRIO_BUY_SIDE


def test_applicable_upgrade_stats_excludes_effect_stats_with_no_matching_effect():
    # A plain damage tower (effects={}, e.g. HEAVY_TOWER) has no slow/burn
    # effect for effect_duration/effect_value to modify — the server rejects
    # such purchases (network/handlers/economy.py::handle_buy_item_upgrade)
    # and battle_service never applies them, so the bot must not even try.
    assert _applicable_upgrade_stats({}) == ("damage", "range", "reload")


def test_applicable_upgrade_stats_includes_effect_duration_for_slow():
    stats = _applicable_upgrade_stats({"slow_duration": 3000, "slow_ratio": 0.4})
    assert "effect_duration" in stats
    assert "effect_value" in stats


def test_applicable_upgrade_stats_includes_effect_duration_for_burn():
    stats = _applicable_upgrade_stats({"burn_duration": 2500, "burn_dps": 15})
    assert "effect_duration" in stats
    assert "effect_value" in stats


def test_upgrade_option_skips_effect_stats_for_plain_damage_tower():
    # HEAVY_TOWER-like structure: effects={}. Even with room in the upgrade
    # focus rotation, effect_duration/effect_value must never be chosen.
    structures = {"HEAVY_TOWER": {"range": 1.5, "damage": 30, "era": "medieval",
                                 "effects": {}}}
    tiles = {"0,0": "HEAVY_TOWER"}
    summary = {"item_upgrade_prices": {"HEAVY_TOWER": 100.0}, "item_upgrades": {}}
    for _ in range(10):
        opt = FrontierDefensePlanner()._upgrade_option(_ctx(summary), tiles, structures)
        assert opt is not None
        assert "effect_duration" not in opt.description
        assert "effect_value" not in opt.description


def test_propose_options_includes_upgrade_alongside_unaffordable_options():
    """propose_options must collect ALL applicable options in one call, not
    just the first match — otherwise the dispatcher's strict-priority model
    (bot/dispatch.py) never even sees a lower-priority option like a workshop
    upgrade when a higher-priority one (era-swap, flank, grow, buy-side) is
    unaffordable, and the bot ends up doing nothing despite having gold for
    the upgrade."""
    tiles = {"0,0": "spawnpoint", "1,0": "path", "2,0": "castle",
            "0,1": "BASIC_TOWER", "1,1": "BASIC_TOWER", "2,1": "BASIC_TOWER"}
    structures = {
        "BASIC_TOWER": {"era": "stone", "requirements": [], "costs": {"gold": 100},
                       "damage": 2, "range": 1.5, "reload_time": 2400, "effects": {}},
    }

    class MapApi:
        def get_map(self):
            return {"tiles": dict(tiles)}

    summary = {
        "current_era": "stone", "era": "stone", "tower_sell_refund": 0.3,
        "resources": {"gold": 5, "culture": 0},
        "tile_price": 100000,  # far more than available gold: growth/side-buy unaffordable
        "item_upgrade_prices": {"BASIC_TOWER": 3.0},  # affordable
        "item_upgrades": {},
        "buildings": {}, "knowledge": {"HUNTING": 0.0},
    }
    items = {"structures": structures, "knowledge": {}, "buildings": {}, "rulers": {}}
    ctx = BotContext(summary, items, {}, {"type": "defense", "params": {}}, MapApi(),
                     map_data={"tiles": dict(tiles)})
    opts = FrontierDefensePlanner().propose_options(ctx)
    descriptions = [o.description for o in opts]
    assert any("upgrade BASIC_TOWER" in d for d in descriptions)
    # The unaffordable higher-priority options must ALSO be present — the
    # dispatcher (not this planner) decides what's affordable.
    assert any(d.startswith("frontier: grow") or d.startswith("frontier: buy side tile")
              for d in descriptions)


def test_upgrade_cap_scales_with_tower_era():
    tiles = {"0,0": "IRON_TOWER"}
    structures = {"IRON_TOWER": {"range": 1.5, "damage": 5, "era": "iron"}}  # rank 3
    maxed = {stat: 12 for stat in ("range", "damage", "reload", "effect_duration",
                                   "effect_value")}  # 3*(3+1) = 12
    summary = {"item_upgrade_prices": {"IRON_TOWER": 100.0},
              "item_upgrades": {"IRON_TOWER": maxed}}
    assert FrontierDefensePlanner()._upgrade_option(_ctx(summary), tiles, structures) is None
    maxed["damage"] = 11  # one below cap → upgradable again
    assert FrontierDefensePlanner()._upgrade_option(_ctx(summary), tiles, structures) is not None


def test_upgrade_focus_sticks_to_one_stat_per_tower():
    from bot.planners.defense_frontier import UPGRADE_STATS
    tiles = {"0,0": "ARROW_TOWER"}
    summary = {"item_upgrade_prices": {"ARROW_TOWER": 100.0}, "item_upgrades": {}}
    ctx = _ctx(summary)
    first = FrontierDefensePlanner()._upgrade_option(ctx, tiles, STRUCTURES)
    assert first is not None
    stat = next(s for s in UPGRADE_STATS if f" {s} " in first.description)
    for _ in range(5):
        again = FrontierDefensePlanner()._upgrade_option(ctx, tiles, STRUCTURES)
        assert f" {stat} " in again.description


# ── Map-derived geometry (the production drift incident) ─────────────────────

_STRUCT = {
    "BASIC_TOWER": {"era": "stone", "requirements": [], "costs": {"gold": 10},
                    "damage": 2, "range": 1.5, "reload_time": 2400, "effects": {}},
}


class _RecordingApi:
    """Fake api that records calls and serves a map the ctx snapshot lacks."""

    def __init__(self, tiles, buy_ok=True, save_ok=True, extra=None):
        self.tiles = dict(tiles)
        if extra:
            self.tiles.update(extra)
        self.buy_ok, self.save_ok = buy_ok, save_ok
        self.calls: list[tuple] = []
        self.saved: dict | None = None

    def get_map(self):
        self.calls.append(("get_map",))
        return {"tiles": dict(self.tiles)}

    def buy_tile(self, q, r):
        self.calls.append(("buy_tile", q, r))
        if not self.buy_ok:
            return {"success": False, "error": "This tile belongs to another empire"}
        self.tiles[f"{q},{r}"] = "empty"
        return {"success": True}

    def save_map(self, tiles):
        self.calls.append(("save_map",))
        self.saved = dict(tiles)
        return {"success": bool(self.save_ok)}


def _frontier_ctx(tiles, memory=None, gold=10_000, neighbors=None, api=None,
                  tile_price=1.0):
    summary = {
        "current_era": "stone", "era": "stone", "tower_sell_refund": 0.3,
        "resources": {"gold": gold, "culture": 0},
        "tile_price": tile_price,
        "item_upgrade_prices": {"BASIC_TOWER": 3.0}, "item_upgrades": {},
        "buildings": {}, "knowledge": {"HUNTING": 0.0},
    }
    items = {"structures": _STRUCT, "knowledge": {}, "buildings": {}, "rulers": {}}
    return BotContext(summary, items, memory if memory is not None else {},
                      {"type": "defense", "params": {}},
                      api or _RecordingApi(tiles),
                      map_data={"tiles": dict(tiles)}, neighbors=neighbors)


def _coords(descriptions):
    """Every (q,r) pair mentioned in the option descriptions."""
    import re
    return {(int(q), int(r))
            for d in descriptions for q, r in re.findall(r"\((-?\d+),(-?\d+)\)", d)}


def test_stale_memory_corridor_is_ignored():
    """Regression test for the production incident: a persisted corridor that
    no longer matches the live map must not influence planning at all.

    Three prod bots planned against such a phantom corridor for a week — every
    action failed with "belongs to another empire" or "must be adjacent to one
    of your existing tiles" while gold piled up."""
    tiles = {"0,0": "spawnpoint", "1,0": "path", "2,0": "castle"}
    memory = {"frontier": {"corridor": ["-15,18", "-16,19", "-18,16"],
                           "ends": {"spawn": {"heading": 3}}, "next_end": "castle",
                           "rng_step": 31115, "blocked_tiles": [[-17, 20]]}}
    opts = FrontierDefensePlanner().propose_options(_frontier_ctx(tiles, memory))

    mentioned = _coords([o.description for o in opts])
    assert mentioned, "planner produced no positional options at all"
    # Nothing may be planned anywhere near the phantom corridor.
    assert all(abs(q) <= 3 and abs(r) <= 3 for q, r in mentioned), mentioned
    # ... and the stale geometry is dropped from memory rather than kept.
    assert "frontier" not in memory


def test_options_follow_the_live_spawn_and_castle():
    """Same memory, two different live maps → options track the live map."""
    memory = {"frontier": {"corridor": ["-15,18", "-16,19"]}}
    planner = FrontierDefensePlanner()

    near = {"0,0": "spawnpoint", "1,0": "path", "2,0": "castle"}
    far = {"20,20": "spawnpoint", "21,20": "path", "22,20": "castle"}
    near_coords = _coords([o.description for o in
                           planner.propose_options(_frontier_ctx(near, dict(memory)))])
    far_coords = _coords([o.description for o in
                          planner.propose_options(_frontier_ctx(far, dict(memory)))])

    assert all(abs(q) <= 3 for q, _ in near_coords)
    assert all(q >= 18 for q, _ in far_coords)


def test_grow_option_is_atomic_buy_then_move():
    """Growing buys the tile AND moves the anchor onto it in one action, so the
    live map alone always describes the maze (no 'pending tip' to remember)."""
    tiles = {"0,0": "spawnpoint", "1,0": "path", "2,0": "castle"}
    # A tile the cycle snapshot does not know about: the save payload must be
    # rebuilt from a fresh read, or it would silently delete this tile.
    api = _RecordingApi(tiles, extra={"1,1": "BASIC_TOWER"})
    ctx = _frontier_ctx(tiles, api=api)

    grow = next(o for o in FrontierDefensePlanner().propose_options(ctx)
                if o.description.startswith("frontier: grow"))
    assert grow.mutates_map
    res = grow.run(api)

    assert res == {"success": True}
    kinds = [c[0] for c in api.calls]
    assert kinds.index("buy_tile") < kinds.index("save_map"), api.calls
    assert api.saved["1,1"] == "BASIC_TOWER", "payload was not rebuilt from a fresh map"
    # The old anchor became path, the bought tile became the anchor.
    anchors = [k for k, v in api.saved.items() if v in ("spawnpoint", "castle")]
    assert api.saved["0,0"] == "path" or api.saved["2,0"] == "path"
    assert len(anchors) == 2


def test_grow_option_skips_save_map_when_buy_fails():
    tiles = {"0,0": "spawnpoint", "1,0": "path", "2,0": "castle"}
    api = _RecordingApi(tiles, buy_ok=False)
    ctx = _frontier_ctx(tiles, api=api)

    grow = next(o for o in FrontierDefensePlanner().propose_options(ctx)
                if o.description.startswith("frontier: grow"))
    res = grow.run(api)

    assert res["success"] is False
    assert not any(c[0] == "save_map" for c in api.calls)


def test_repair_finishes_an_interrupted_grow():
    """A bought tile whose relocation half failed is adopted for free."""
    tiles = {"0,0": "spawnpoint", "1,0": "path", "2,0": "castle",
             "-1,0": "empty"}  # dangling off the spawn anchor, touches once
    opts = FrontierDefensePlanner().propose_options(_frontier_ctx(tiles))
    repair = [o for o in opts if o.description == "frontier: move spawn to (-1,0)"]
    assert repair and repair[0].price == 0.0


def test_repair_ignores_a_multi_touch_empty():
    """An ordinary tower spot touching the corridor twice is never adopted."""
    tiles = {"0,0": "spawnpoint", "1,0": "path", "2,0": "castle",
             "0,1": "empty"}  # neighbors both (0,0) and (1,0)
    opts = FrontierDefensePlanner().propose_options(_frontier_ctx(tiles))
    assert not any(d.startswith("frontier: move") for d in
                   (o.description for o in opts))
    assert any("tower BASIC_TOWER at (0,1)" in o.description for o in opts)


def test_foreign_tiles_are_never_proposed():
    """Land a neighbor owns is skipped up front, the way a human sees it on the
    map screen — not discovered by a failed purchase."""
    tiles = {"0,0": "spawnpoint", "1,0": "path", "2,0": "castle"}
    ring = [{"q": q, "r": r, "uid": 999}
            for q in range(-2, 5) for r in range(-2, 3)
            if f"{q},{r}" not in tiles]
    ctx = _frontier_ctx(tiles, neighbors={"neighbor_tiles": ring})

    opts = FrontierDefensePlanner().propose_options(ctx)
    buys = [o.description for o in opts
            if o.description.startswith(("frontier: grow", "frontier: flank",
                                         "frontier: buy side"))]
    assert buys == [], buys


def test_missing_neighbor_view_does_not_block_growth():
    """Without the neighbor view the bot simply attempts the purchase."""
    tiles = {"0,0": "spawnpoint", "1,0": "path", "2,0": "castle"}
    for neighbors in (None, {}, {"neighbor_tiles": []}):
        opts = FrontierDefensePlanner().propose_options(
            _frontier_ctx(tiles, neighbors=neighbors))
        assert any(o.description.startswith("frontier: grow") for o in opts)


def test_no_route_keeps_towers_but_skips_corridor_actions():
    """Spawn and castle exist but nothing connects them (the state a data event
    can leave behind): plan towers/upgrades, never blind tile purchases."""
    tiles = {"0,0": "spawnpoint", "9,9": "castle", "0,1": "empty"}
    opts = FrontierDefensePlanner().propose_options(_frontier_ctx(tiles))
    descriptions = [o.description for o in opts]

    assert any("tower BASIC_TOWER" in d for d in descriptions)
    assert not any(d.startswith(("frontier: grow", "frontier: flank",
                                 "frontier: buy side", "frontier: move"))
                   for d in descriptions)


def test_grow_alternates_ends_with_owned_parity():
    """Both ends are offered; which one leads alternates with the owned-tile
    count, so callers running only the best option still grow both ends."""
    planner = FrontierDefensePlanner()
    even = {"0,0": "spawnpoint", "1,0": "path", "2,0": "castle", "1,1": "path"}
    odd = dict(even, **{"1,-1": "path"})

    def first_grow(tiles):
        opts = planner.propose_options(_frontier_ctx(tiles))
        return next(o.description for o in opts
                    if o.description.startswith("frontier: grow"))

    assert first_grow(even).split()[2] != first_grow(odd).split()[2]
