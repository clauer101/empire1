"""Spiral defense planner: a deliberately simple alternative to DefensePlanner.

Builds a snail-shell spiral maze around the castle (see
defense_analysis.next_spiral_action): a single coiled corridor winds from the
outer spawn down to the central castle, walled by one continuous spiral arm —
no concentric rings. A tower is placed whenever one fits; only when none can be
placed is a tile bought. Maximising the spawn→castle path is the design goal.

Same interface as DefensePlanner (Planner.propose_options → list[Option], so the
inherited Planner.propose works too), so the two are interchangeable. The logic
is intentionally minimal: ask the geometry helper for the next step and wrap it
in a single Option.
"""

from __future__ import annotations

import random

from bot.defense_analysis import (
    next_spiral_action, pick_tower, tower_class,
)
from .base import Option, Planner


def _tile_type(value) -> str:
    if isinstance(value, dict):
        return value.get("type", "")
    return str(value)


class SpiralDefensePlanner(Planner):
    def propose_options(self, ctx, *, advance_phase: bool = True) -> list[Option]:
        tiles = ctx.api.get_map().get("tiles", {})
        structures = ctx.items.get("structures", {})
        # Per-bot seed (stable across cycles), same pattern as DefensePlanner.
        seed = ctx.memory.setdefault("maze_seed", random.getrandbits(32) or 1)

        action = next_spiral_action(tiles, seed=seed)
        if action is None:
            return []

        kind = action["kind"]
        q, r = action["q"], action["r"]
        key = f"{q},{r}"

        if kind == "buy":
            price = float(ctx.summary.get("tile_price", 0.0) or 0.0)
            return [Option(
                category="defense", price=price, gain=1.0,
                description=f"buy tile {q},{r} (spiral field)",
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
                description=f"move spawn to {q},{r} (extend spiral)",
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
                        f"{tower_iid} at {q},{r} (spiral wall)",
            run=lambda api, t=new_tiles: api.save_map(t),
            saves_for=tower_cost,
            goal_meta={"item": tower_iid, "action": "tower"})]
