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
