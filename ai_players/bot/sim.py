"""Time-accelerated maze/defense simulation using the REAL DefensePlanner.

Runs the identical bot implementation (bot.planners.defense.DefensePlanner +
bot.defense_analysis) against an in-memory map, as if the defense strategy
were permanently active. No game server involved: SimApi applies the
planner's actions (save_map / buy_tile / upgrades / buildings) locally and
charges gold using the server price formulas passed in by the caller.
"""

from __future__ import annotations

from typing import Any

from bot.planners.base import BotContext
from bot.planners.defense import DefensePlanner

START_TILES = {"0,0": "castle", "0,1": "spawnpoint", "1,0": "empty"}

TOWER_SELL_REFUND = 0.3  # mirrors game.yaml tower_sell_refund


def tile_price(i: int, p: dict) -> float:
    """Server formula empire_service._tile_price: u + (i*y)*(i+z)**v."""
    return float(p["u"] + (i * p["y"]) * (i + p["z"]) ** p["v"])


class SimApi:
    """Applies planner actions to an in-memory map, mirroring server rules."""

    def __init__(self, tiles: dict, structures: dict, buildings: dict,
                 state: dict, tile_params: dict):
        self.tiles = tiles
        self.structures = structures
        self.buildings = buildings
        self.state = state          # gold, tiles_bought, item_upgrades, completed
        self.tile_params = tile_params

    def get_map(self) -> dict:
        return {"tiles": dict(self.tiles)}

    def save_map(self, new_tiles: dict) -> dict:
        cost = 0.0
        for key, value in new_tiles.items():
            old = self.tiles.get(key)
            if value in self.structures and old != value:
                cost += float((self.structures[value].get("costs") or {})
                              .get("gold", 0.0))
            if old in self.structures and old != value:
                # Selling refunds part of the gold cost (server rule).
                cost -= TOWER_SELL_REFUND * float(
                    (self.structures[old].get("costs") or {}).get("gold", 0.0))
        if cost > self.state["gold"]:
            return {"success": False, "error": "not enough gold"}
        self.state["gold"] -= cost
        self.tiles.clear()
        self.tiles.update(new_tiles)
        return {"success": True}

    def buy_tile(self, q: int, r: int) -> dict:
        price = self.state["tile_price"]
        if price > self.state["gold"]:
            return {"success": False, "error": "not enough gold"}
        self.state["gold"] -= price
        self.tiles[f"{q},{r}"] = "empty"
        self.state["tiles_bought"] += 1
        self.state["tile_price"] = tile_price(
            len(self.tiles) + 1, self.tile_params)
        return {"success": True}

    def buy_item_upgrade(self, iid: str, stat: str) -> dict:
        """Price formula: base_cost × (total_levels_on_iid + 1)²."""
        levels = self.state["item_upgrades"].setdefault(iid, {})
        total = sum(levels.values())
        base = float(self.state["upgrade_base_by_iid"].get(iid, 100.0))
        price = base * (total + 1) ** 2
        if price > self.state["gold"]:
            return {"success": False, "error": "not enough gold"}
        self.state["gold"] -= price
        levels[stat] = levels.get(stat, 0) + 1
        return {"success": True}

    def build(self, iid: str) -> dict:
        cost = float((self.buildings.get(iid, {}).get("costs") or {})
                     .get("gold", 0.0))
        if cost > self.state["gold"]:
            return {"success": False, "error": "not enough gold"}
        self.state["gold"] -= cost
        self.state["completed"][iid] = 0.0  # finishes instantly in the sim
        return {"success": True}

    def get_replay(self, key: str) -> dict:  # no replays in the sim
        raise RuntimeError("no replays in simulation")


def simulate_defense(
    structures: dict,
    buildings: dict,
    *,
    cycles: int = 200,
    start_gold: float = 200.0,
    gold_per_cycle: float = 100.0,
    start_tiles: dict | None = None,
    completed: set[str] | None = None,
    tile_params: dict | None = None,
    upgrade_base_by_iid: dict | None = None,
    top_n: int = 1,
    seed: int | None = None,
) -> dict[str, Any]:
    """Run `cycles` defense-planner cycles; return the step log + final map.

    Each cycle adds `gold_per_cycle` gold (the time acceleration) and asks the
    real DefensePlanner for exactly one action, like the live bot loop.

    `seed` fixes the maze randomization (memory["maze_seed"]) for reproducible
    runs; None lets the planner draw one, like a live bot. The seed actually
    used is returned in the result.
    """
    import random

    from bot.defense_analysis import bfs_path

    tiles = dict(start_tiles or START_TILES)
    tile_params = tile_params or {"u": 0, "y": 0.7, "z": 1, "v": 2.1}
    state = {
        "gold": float(start_gold),
        "tiles_bought": 0,
        "tile_price": tile_price(len(tiles) + 1, tile_params),
        "item_upgrades": {},
        "completed": {iid: 0.0 for iid in (completed or set())},
        "upgrade_base_by_iid": upgrade_base_by_iid or {},
    }
    api = SimApi(tiles, structures, buildings, state, tile_params)
    items = {"structures": structures, "buildings": buildings, "knowledge": {}}
    # SystemRandom: unaffected by the random.seed() below from a previous run
    maze_seed = int(seed) if seed else (random.SystemRandom().getrandbits(32) or 1)
    # Seed the global RNG too: weighted top-N sampling in the planners uses
    # it, so the whole run is reproducible from `seed`.
    random.seed(maze_seed)
    memory: dict[str, Any] = {"maze_seed": maze_seed}
    strategy = {"type": "defense", "params": {},
                "valid_until": "2099-01-01T00:00:00Z"}
    planner = DefensePlanner()

    steps: list[dict] = []
    last_snapshot: dict | None = None
    for cycle in range(cycles):
        state["gold"] += gold_per_cycle
        summary = {
            "resources": {"gold": state["gold"], "culture": 0.0},
            "tile_price": state["tile_price"],
            "tower_sell_refund": TOWER_SELL_REFUND,
            "item_upgrades": {k: dict(v) for k, v in state["item_upgrades"].items()},
            "buildings": dict(state["completed"]),
            "knowledge": {},
            "artifacts": [],
            "build_queue": [],
            "research_queue": [],
        }
        ctx = BotContext(summary, items, memory, strategy, api,
                         selection={"top_n": top_n})
        action = planner.propose(ctx)
        desc = None
        if action is not None:
            result = action.run(api)
            ok = not (isinstance(result, dict) and result.get("success") is False)
            desc = action.description if ok else f"FAILED: {action.description}"
        elif memory.get("savings_goal"):
            goal = memory["savings_goal"]
            desc = f"saving for {goal['action']} {goal['item']} ({goal['amount']:.0f}g)"

        path = bfs_path(tiles) or []
        towers = sum(1 for v in tiles.values() if v in structures)
        snapshot = dict(tiles)
        step = {
            "cycle": cycle,
            "gold": round(state["gold"], 1),
            "action": desc,
            "path_len": len(path),
            "towers": towers,
            "tile_price": round(state["tile_price"], 1),
        }
        if snapshot != last_snapshot:
            step["tiles"] = snapshot
            last_snapshot = snapshot
        steps.append(step)

    return {
        "steps": steps,
        "final_tiles": dict(tiles),
        "final_path_len": steps[-1]["path_len"] if steps else 0,
        "final_towers": steps[-1]["towers"] if steps else 0,
        "item_upgrades": state["item_upgrades"],
        "gold_left": round(state["gold"], 1),
        "seed": maze_seed,
    }
