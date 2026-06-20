"""Comb defense planner: a space-filling-curve (boustrophedon) maze builder.

Builds a dense comb maze over the owned field (see
defense_analysis.next_comb_action): every other line is a full tower wall with
one rotating gap, so the critter corridor snakes back and forth and every
corridor lane is flanked by tower walls on BOTH sides. The planner grows the
field by buying land out to a fixed extent, producing a long winding path.

Same interface as DefensePlanner/SpiralDefensePlanner (Planner.propose_options →
list[Option], so the inherited Planner.propose works too), so the three are
interchangeable. The logic is intentionally minimal: ask the geometry helper for
the next step and wrap it in a single Option.
"""

from __future__ import annotations

import random

from bot.defense_analysis import (
    next_comb_action, pick_tower, tower_class,
)
from .base import Option, Planner


def _tile_type(value) -> str:
    if isinstance(value, dict):
        return value.get("type", "")
    return str(value)


class CombDefensePlanner(Planner):
    def propose_options(self, ctx, *, advance_phase: bool = True) -> list[Option]:
        tiles = ctx.api.get_map().get("tiles", {})
        structures = ctx.items.get("structures", {})
        # Per-bot seed (stable across cycles), same pattern as DefensePlanner.
        seed = ctx.memory.setdefault("maze_seed", random.getrandbits(32) or 1)

        action = next_comb_action(tiles, seed=seed)
        if action is None:
            return []

        kind = action["kind"]
        q, r = action["q"], action["r"]
        key = f"{q},{r}"

        if kind == "buy":
            price = float(ctx.summary.get("tile_price", 0.0) or 0.0)
            return [Option(
                category="defense", price=price, gain=1.0,
                description=f"buy tile {q},{r} (comb field)",
                run=lambda api, q=q, r=r: api.buy_tile(q, r),
                saves_for=price,
                goal_meta={"item": f"tile {q},{r}", "action": "tile"})]

        if kind == "spawn":
            new_tiles = dict(tiles)
            old = next((k for k, v in tiles.items()
                        if _tile_type(v) == "spawnpoint"), None)
            if old is not None:
                new_tiles[old] = "empty"
            new_tiles[key] = "spawnpoint"
            return [Option(
                category="defense", price=0.0, gain=100.0,
                description=f"move spawn to {q},{r} (extend comb)",
                run=lambda api, t=new_tiles: api.save_map(t))]

        # kind == "tower": pick a tower the same way DefensePlanner does so
        # unlock + class-mix balancing is reused, then place it on the wall tile.
        placed_counts: dict[str, int] = {}
        for v in tiles.values():
            iid = _tile_type(v)
            if iid in structures:
                cls = tower_class(structures[iid])
                placed_counts[cls] = placed_counts.get(cls, 0) + 1
        tower_iid = pick_tower(structures, placed_counts, ctx.is_unlocked,
                               top_n=ctx.top_n)
        if tower_iid is None:
            return []
        tower_cost = float((structures[tower_iid].get("costs") or {})
                           .get("gold", 0.0))
        new_tiles = dict(tiles)
        new_tiles[key] = tower_iid
        return [Option(
            category="defense", price=tower_cost, gain=2.0,
            description=f"place {tower_class(structures[tower_iid])} tower "
                        f"{tower_iid} at {q},{r} (comb wall)",
            run=lambda api, t=new_tiles: api.save_map(t),
            saves_for=tower_cost,
            goal_meta={"item": tower_iid, "action": "tower"})]
