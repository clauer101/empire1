"""Automatic tower-defense maze generation — the admin/dev balance-tuning tool.

This is the gameserver-native home of what used to be a duplicated dev tool:
`web/tools/maze-sim.html` used to call into `ai_players/bot/sim.py`, which ran
the AI bot's own defense planner against a hand-rolled `SimApi` that
reimplemented server pricing formulas (tile price curve, tower-sell refund,
item-upgrade cost) instead of using the real ones. That duplication had
already drifted (a hardcoded 0.3 tower-sell refund vs. game.yaml's 0.8).

This module reuses the *real* pricing via `EmpireService` methods, called
against a throwaway, unregistered `Empire` (never persisted, never added to
`EmpireService.all_empires`) so no real player state is touched.

The AI bot's own live maze-building (`ai_players/bot/planners/defense_frontier.py`
+ `ai_players/bot/defense_analysis.py`) is intentionally NOT this module and is
untouched by it — that package plays exclusively through the public REST API
and must stay independent of the gameserver process, so it keeps its own
(smaller, deliberately duplicated) copy of this geometry. See that package's
CLAUDE.md.

Algorithm (identical in spirit to the ai_players copy this replaces): grow a
single walkable corridor from spawn and castle simultaneously in a serpentine
pattern, wall it with towers on both sides, replace outdated towers, and
upgrade the most-common tower type as a last resort. One action is produced
per `MazeGenerator.step()` call, highest-priority first; a same-tier tie goes
to the better gain/price ratio (see `PRIO_*` below).
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Any, Callable, TypeVar

from gameserver.engine.hex_pathfinding import HEX_DIRS, find_path_from_spawn_to_castle, hex_world_distance
from gameserver.models.empire import Empire
from gameserver.models.items import ItemDetails, ItemType

T = TypeVar("T")

# A hex_map as the client/tests pass it around: {"q,r": tile_type}.
Tiles = dict[str, str]

DIR_INDEX = {d: i for i, d in enumerate(HEX_DIRS)}

# Tile types that make up the committed maze — see defense_frontier.py's
# original docstring: a bought "empty" tile is a tower spot, never corridor.
CORRIDOR_TILES = {"spawnpoint", "path", "castle"}

SAMPLES_PER_EDGE = 4  # path interpolation density for coverage scoring

SEG_LEN = 5        # straight steps before the serpentine prefers a U-turn

# Fallback (min, max) corridor length if the era is missing from game.yaml's
# `maze_length` section — matches the old flat MAX_CORRIDOR=60 ceiling this
# replaced, floored at a modest minimum so an unconfigured era still stops.
DEFAULT_MAZE_LENGTH = (10, 60)

# Fallback (min, max) tower count, same role as DEFAULT_MAZE_LENGTH above but
# for `target_maze_towers()` — used if the era is missing min_towers/max_towers.
DEFAULT_MAZE_TOWERS = (4, 30)

PRIO_TOWER_STRAY = 12
PRIO_RELOCATE = 11
PRIO_ERA_SWAP = 10
PRIO_FLANK = 9
PRIO_GROW = 8
PRIO_BUY_SIDE = 6
PRIO_UPGRADE = 5

MIX_TARGET = {"damage": 3, "slow": 1, "splash": 1}
UPGRADE_STATS = ("damage", "range", "reload", "effect_duration", "effect_value")


def target_maze_length(maze_length_cfg: dict[str, dict[str, int]], era: str,
                        rng: random.Random) -> int:
    """Draw a random target corridor length for `era` from game.yaml's
    `maze_length` section (falls back to DEFAULT_MAZE_LENGTH if the era is
    missing or misconfigured)."""
    era_cfg = maze_length_cfg.get(era) or {}
    lo, hi = DEFAULT_MAZE_LENGTH
    lo = int(era_cfg.get("min_length", lo))
    hi = int(era_cfg.get("max_length", hi))
    if hi < lo:
        hi = lo
    return rng.randint(lo, hi)


def target_maze_towers(maze_length_cfg: dict[str, dict[str, int]], era: str,
                        rng: random.Random) -> int:
    """Draw a random target tower count for `era` from game.yaml's
    `maze_length` section (falls back to DEFAULT_MAZE_TOWERS if the era is
    missing or misconfigured). Sibling of `target_maze_length` — same section,
    same fallback shape, but bounds `MazeGenerator`'s tower count instead of
    its corridor length."""
    era_cfg = maze_length_cfg.get(era) or {}
    lo, hi = DEFAULT_MAZE_TOWERS
    lo = int(era_cfg.get("min_towers", lo))
    hi = int(era_cfg.get("max_towers", hi))
    if hi < lo:
        hi = lo
    return rng.randint(lo, hi)


def _tile_type(value: Any) -> str:
    if isinstance(value, dict):
        return str(value.get("type", ""))
    return str(value)


def _parse_key(key: str) -> tuple[int, int]:
    q, r = key.split(",")
    return int(q), int(r)


def _key(pos: tuple[int, int]) -> str:
    return f"{pos[0]},{pos[1]}"


def weighted_top_n(candidates: list[T], key: Callable[[T], Any], n: int,
                    *, rng: random.Random) -> T | None:
    """Pick one of the best `n` candidates, weighted toward the top.

    Ported from ai_players/bot/planners/base.py (identical behavior) — a
    small, pure helper worth keeping alongside its only two callers instead of
    a cross-package import.
    """
    if not candidates:
        return None
    ordered = sorted(candidates, key=key, reverse=True)
    pool = ordered[:max(1, n)]
    if len(pool) == 1:
        return pool[0]
    weights = list(range(len(pool), 0, -1))
    return rng.choices(pool, weights=weights, k=1)[0]


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


def corridor_from_map(tiles: Tiles) -> tuple[list[tuple[int, int]], set[tuple[int, int]]]:
    """Derive `(route, corridor_set)` from a hex_map, spawn first, castle last.

    Mirrors ai_players' `defense_analysis.corridor_from_map`, minus the
    "trust the server's own `path` field" branch — there is no separate path
    field here, this function *is* the server's pathfinding
    (`hex_pathfinding.find_path_from_spawn_to_castle`).
    """
    corridor_set = {_parse_key(k) for k, v in tiles.items() if _tile_type(v) in CORRIDOR_TILES}
    hex_path = find_path_from_spawn_to_castle(tiles)
    route = [(c.q, c.r) for c in hex_path] if hex_path else []
    return [p for p in route if p in corridor_set], corridor_set


def end_state(walk: list[tuple[int, int]]) -> tuple[int, int, int]:
    """Serpentine state at `walk[0]` — see defense_analysis.end_state for the
    full derivation (identical logic, ported verbatim)."""
    dirs: list[int] = []
    for a, b in zip(walk, walk[1:]):
        d = DIR_INDEX.get((a[0] - b[0], a[1] - b[1]))
        if d is None:
            break
        dirs.append(d)
    if not dirs:
        return 0, 0, 1

    heading = dirs[0]
    seg_steps = 0
    for d in dirs:
        if d != heading:
            break
        seg_steps += 1

    turns_in_row = 0
    for prev, nxt in zip(dirs, dirs[1:]):
        if prev == nxt:
            break
        turns_in_row += 1

    turn_dir = 1
    if len(dirs) > 1 and dirs[0] != dirs[1]:
        turn_dir = 1 if (dirs[0] - dirs[1]) % 6 in (1, 2) else -1
    if turns_in_row >= 2:
        turn_dir = -turn_dir
    return heading, seg_steps, turn_dir


# ── Tower selection ──────────────────────────────────────────────────────────


def tower_class(item: ItemDetails) -> str:
    effects = item.effects
    if "slow_ratio" in effects or "slow_duration" in effects:
        return "slow"
    if "splash_radius" in effects:
        return "splash"
    return "damage"


def tower_quality(item: ItemDetails) -> float:
    """Single-number tower strength: DPS per reload, boosted by range."""
    reload_ms = item.reload_time_ms or 1000.0
    rng = item.range or 1.0
    return item.damage / max(reload_ms, 1.0) * (1.0 + rng / 4.0)


def pick_tower(structures: dict[str, ItemDetails], placed_counts: dict[str, int],
               era_rank: dict[str, int], top_n: int, rng: random.Random) -> str | None:
    """Pick the IID of a tower in the most under-represented class.

    Always picks from the highest-era tower present in `structures` (callers
    pre-filter `structures` to unlocked/affordable candidates).
    """
    if not structures:
        return None
    best_era_rank = max(era_rank.get(iid, 0) for iid in structures)
    candidates = {iid: it for iid, it in structures.items()
                  if era_rank.get(iid, 0) == best_era_rank}
    total_target = sum(MIX_TARGET.values())
    total_placed = sum(placed_counts.values()) or 1

    def deficit(cls: str) -> float:
        return MIX_TARGET[cls] / total_target - placed_counts.get(cls, 0) / total_placed

    by_class: dict[str, list[tuple[str, ItemDetails]]] = {}
    for iid, it in candidates.items():
        by_class.setdefault(tower_class(it), []).append((iid, it))
    for cls in sorted(by_class, key=lambda c: -deficit(c)):
        chosen: tuple[str, ItemDetails] | None = weighted_top_n(
            by_class[cls], key=lambda c: tower_quality(c[1]), n=top_n, rng=rng)
        return chosen[0] if chosen else None
    return None


@dataclass
class MazeAction:
    description: str
    price: float
    apply: Callable[[], None]
    priority: int
    gain: float = 1.0

    def base_score(self) -> float:
        if self.price <= 0:
            return math.inf if self.gain > 0 else 0.0
        return self.gain / self.price


@dataclass
class MazeGenerator:
    """Builds one maze at a time, driven by a sandbox `Empire` + `hex_map`.

    `structures`/`buildings` are the unlocked/era-filtered catalog (a subset
    of `services.upgrade_provider.items`); `era_rank` maps iid -> era index
    (reuse `services.empire_service._item_era_index`); `tile_price_for` /
    `item_upgrade_price_for` / `tower_sell_refund` are injected so this module
    never re-derives pricing formulas itself. `target_length` is the corridor
    length (tile count) to stop growing at, `target_towers` the tower count
    to stop placing new towers at — draw each once per maze via
    `target_maze_length()` / `target_maze_towers()` from game.yaml's
    `maze_length` section.
    """

    structures: dict[str, ItemDetails]
    era_rank: dict[str, int]
    tile_price_for: Callable[[Empire, int], float]
    item_upgrade_price_for: Callable[[Empire, str, str], float]
    tower_sell_refund: float
    target_length: int = DEFAULT_MAZE_LENGTH[1]
    target_towers: int = DEFAULT_MAZE_TOWERS[1]
    top_n: int = 1
    rng: random.Random = field(default_factory=random.Random)
    memory: dict[str, Any] = field(default_factory=dict)

    def step(self, tiles: Tiles, empire: Empire) -> str | None:
        """Compute and apply the single highest-priority action this cycle.

        Returns a human-readable description of what happened (prefixed with
        "FAILED: " if gold ran short), or None if nothing is applicable.
        """
        options = self._options(tiles, empire)
        if not options:
            return None
        best = max(options, key=lambda o: (o.priority, o.base_score()))
        if best.price > empire.resources.get("gold", 0.0):
            return f"FAILED: {best.description}"
        empire.resources["gold"] = empire.resources.get("gold", 0.0) - best.price
        best.apply()
        return best.description

    # ── Option assembly ──────────────────────────────────────────────────

    def _options(self, tiles: Tiles, empire: Empire) -> list[MazeAction]:
        spawns = [_parse_key(k) for k, v in tiles.items() if _tile_type(v) == "spawnpoint"]
        castles = [_parse_key(k) for k, v in tiles.items() if _tile_type(v) == "castle"]
        if not spawns or not castles:
            return []

        options: list[MazeAction] = []

        stray = [_parse_key(k) for k, v in tiles.items() if _tile_type(v) == "empty"]
        corridor, corridor_set = corridor_from_map(tiles)
        tower_count = sum(1 for v in tiles.values() if _tile_type(v) in self.structures)
        want_more_towers = tower_count < self.target_towers

        if stray and want_more_towers:
            opt = self._tower_option(tiles, stray, corridor)
            if opt:
                options.append(opt)

        swap = self._era_swap_option(tiles, empire)
        if swap:
            options.append(swap)

        upgrade = self._upgrade_option(tiles, empire)
        if upgrade:
            options.append(upgrade)

        if not corridor:
            return options  # spawn/castle exist but nothing connects them yet

        owned = {_parse_key(k) for k, v in tiles.items() if _tile_type(v) != "void"}

        for anchor, kind in ((corridor[0], "spawnpoint"), (corridor[-1], "castle")):
            repair = self._repair_option(tiles, anchor, kind, corridor_set)
            if repair:
                options.append(repair)

        if want_more_towers:
            flank = self._flank_option(tiles, corridor, corridor_set, owned, empire)
            if flank:
                options.append(flank)

        if len(corridor_set) < self.target_length:
            tower_tiles = {_parse_key(k) for k, v in tiles.items() if _tile_type(v) in self.structures}
            ends = ("spawn", "castle") if len(owned) % 2 == 0 else ("castle", "spawn")
            for end in ends:
                grow = self._grow_option(tiles, corridor, corridor_set, owned, tower_tiles, empire, end=end)
                if grow:
                    options.append(grow)

        if want_more_towers:
            side = self._side_tile_option(tiles, corridor_set, owned, corridor, empire)
            if side:
                options.append(side)

        return options

    # ── Towers ─────────────────────────────────────────────────────────

    def _tower_option(self, tiles: Tiles, stray: list[tuple[int, int]],
                       corridor: list[tuple[int, int]]) -> MazeAction | None:
        placed_counts: dict[str, int] = {}
        for v in tiles.values():
            t = _tile_type(v)
            if t in self.structures:
                cls = tower_class(self.structures[t])
                placed_counts[cls] = placed_counts.get(cls, 0) + 1
        iid = pick_tower(self.structures, placed_counts, self.era_rank, self.top_n, self.rng)
        if iid is None:
            return None

        pts = path_points(corridor) if corridor else []
        trange = self.structures[iid].range or 1.0

        def score(pos: tuple[int, int]) -> float:
            return coverage_score(pos, trange, pts, lambda p: 1.0) if pts else 0.0

        best = weighted_top_n(stray, key=score, n=self.top_n, rng=self.rng)
        assert best is not None  # `stray` is non-empty (checked by the caller)
        price = self.structures[iid].costs.get("gold", 0.0)

        def apply() -> None:
            tiles[_key(best)] = iid

        return MazeAction(
            description=f"maze: tower {iid} at ({best[0]},{best[1]})",
            price=price, apply=apply, priority=PRIO_TOWER_STRAY, gain=8.0,
        )

    def _highest_tower_rank(self) -> int:
        return max((self.era_rank.get(iid, 0) for iid in self.structures), default=0)

    def _era_swap_option(self, tiles: Tiles, empire: Empire) -> MazeAction | None:
        cur_rank = self._highest_tower_rank()
        best_new: str | None
        best_new, best_new_q = None, 0.0
        for iid, item in self.structures.items():
            if self.era_rank.get(iid, 0) != cur_rank:
                continue
            q = tower_quality(item)
            if q > best_new_q:
                best_new, best_new_q = iid, q
        if best_new is None:
            return None
        new_cost = self.structures[best_new].costs.get("gold", 0.0)

        placed = [(k, _tile_type(v)) for k, v in tiles.items() if _tile_type(v) in self.structures]
        for key, old_iid in sorted(
                placed,
                key=lambda e: (self.era_rank.get(e[1], 0), tower_quality(self.structures[e[1]]))):
            old = self.structures[old_iid]
            if self.era_rank.get(old_iid, 0) >= cur_rank:
                break
            old_cost = old.costs.get("gold", 0.0)
            net_cost = new_cost - self.tower_sell_refund * old_cost
            gain = best_new_q - tower_quality(old)
            if net_cost <= 0 or gain <= 0:
                continue

            def apply() -> None:
                tiles[key] = best_new

            return MazeAction(
                description=f"maze: era-swap {old_iid} -> {best_new} at {key}",
                price=net_cost, apply=apply, priority=PRIO_ERA_SWAP, gain=gain,
            )
        return None

    def _applicable_upgrade_stats(self, effects: dict[str, float]) -> tuple[str, ...]:
        stats = ["damage", "range", "reload"]
        if "slow_duration" in effects or "burn_duration" in effects:
            stats.append("effect_duration")
        if "slow_ratio" in effects or "burn_dps" in effects:
            stats.append("effect_value")
        return tuple(stats)

    def _max_upgrade_level(self, era_rank: int) -> int:
        return 3 * (era_rank + 1)

    def _focus_upgrade_stat(self, key: str, levels: dict[str, int],
                             stats: tuple[str, ...], cap: int) -> str | None:
        focus: dict[str, str] = self.memory.setdefault("upgrade_focus", {})
        stat = focus.get(key)
        if stat is not None and int(levels.get(stat, 0)) >= cap:
            stat = None
        if stat is None:
            candidates = [s for s in stats if int(levels.get(s, 0)) < cap]
            if not candidates:
                focus.pop(key, None)
                return None
            stat = self.rng.choice(candidates)
            focus[key] = stat
        return stat

    def _most_common_placed_tower(self, tiles: Tiles) -> str | None:
        counts: dict[str, int] = {}
        for v in tiles.values():
            t = _tile_type(v)
            if t in self.structures:
                counts[t] = counts.get(t, 0) + 1
        if not counts:
            return None
        best = max(counts.values())
        return min(iid for iid, n in counts.items() if n == best)

    def _upgrade_option(self, tiles: Tiles, empire: Empire) -> MazeAction | None:
        iid = self._most_common_placed_tower(tiles)
        if iid is None:
            return None
        levels = empire.item_upgrades.get(iid, {})
        cap = self._max_upgrade_level(self.era_rank.get(iid, 0))
        applicable = self._applicable_upgrade_stats(self.structures[iid].effects)
        stat = self._focus_upgrade_stat(iid, levels, applicable, cap)
        if stat is None:
            return None
        price = self.item_upgrade_price_for(empire, iid, stat)
        if price <= 0:
            return None

        def apply() -> None:
            item_levels = empire.item_upgrades.setdefault(iid, {})
            item_levels[stat] = item_levels.get(stat, 0) + 1

        return MazeAction(
            description=f"maze: upgrade {iid} {stat} (most-placed tower)",
            price=price, apply=apply, priority=PRIO_UPGRADE, gain=6.0,
        )

    # ── Relocation / repair ──────────────────────────────────────────────

    def _touches_once(self, pos: tuple[int, int], corridor_set: set[tuple[int, int]]) -> bool:
        return sum(1 for dq, dr in HEX_DIRS if (pos[0] + dq, pos[1] + dr) in corridor_set) == 1

    def _repair_option(self, tiles: Tiles, anchor: tuple[int, int], kind: str,
                        corridor_set: set[tuple[int, int]]) -> MazeAction | None:
        cands = sorted(
            n for n in ((anchor[0] + dq, anchor[1] + dr) for dq, dr in HEX_DIRS)
            if _tile_type(tiles.get(_key(n), "")) == "empty" and self._touches_once(n, corridor_set)
        )
        if not cands:
            return None
        new_pos = cands[0]

        def apply(old: tuple[int, int] = anchor, new: tuple[int, int] = new_pos, k: str = kind) -> None:
            tiles[_key(old)] = "path"
            tiles[_key(new)] = k

        label = "castle" if kind == "castle" else "spawn"
        return MazeAction(
            description=f"maze: move {label} to ({new_pos[0]},{new_pos[1]})",
            price=0.0, apply=apply, priority=PRIO_RELOCATE, gain=50.0,
        )

    # ── Flanking ─────────────────────────────────────────────────────────

    def _flank_option(self, tiles: Tiles, corridor: list[tuple[int, int]],
                       corridor_set: set[tuple[int, int]], owned: set[tuple[int, int]],
                       empire: Empire) -> MazeAction | None:
        for pos in corridor[1:-1]:
            missing = [(pos[0] + dq, pos[1] + dr) for dq, dr in HEX_DIRS
                       if (pos[0] + dq, pos[1] + dr) not in owned]
            if not missing:
                continue

            def adjacency(p: tuple[int, int]) -> int:
                return sum(1 for dq, dr in HEX_DIRS if (p[0] + dq, p[1] + dr) in corridor_set)

            best = weighted_top_n(missing, key=adjacency, n=self.top_n, rng=self.rng)
            assert best is not None  # `missing` is non-empty (checked above)
            price = self._tile_price(tiles, empire)

            def apply() -> None:
                tiles[_key(best)] = "empty"

            return MazeAction(
                description=f"maze: flank tile ({best[0]},{best[1]}) for corridor ({pos[0]},{pos[1]})",
                price=price, apply=apply, priority=PRIO_FLANK, gain=9.0,
            )
        return None

    # ── Growth ───────────────────────────────────────────────────────────

    def _candidate_ok(self, pos: tuple[int, int], corridor_set: set[tuple[int, int]],
                       owned: set[tuple[int, int]]) -> bool:
        return pos not in owned and self._touches_once(pos, corridor_set)

    def _grow_option(self, tiles: Tiles, corridor: list[tuple[int, int]],
                      corridor_set: set[tuple[int, int]], owned: set[tuple[int, int]],
                      tower_tiles: set[tuple[int, int]], empire: Empire, *, end: str) -> MazeAction | None:
        walk = corridor if end == "spawn" else corridor[::-1]
        anchor = walk[0]
        heading, seg_steps, turn_dir = end_state(walk)
        want_turn = seg_steps >= SEG_LEN

        straight = [heading]
        turns = [(heading + turn_dir) % 6, (heading - turn_dir) % 6,
                 (heading + 2 * turn_dir) % 6, (heading - 2 * turn_dir) % 6]
        order = (turns[:2] + straight + turns[2:]) if want_turn else (straight + turns)

        valid: list[tuple[int, int, tuple[int, int]]] = []
        for idx, d in enumerate(order):
            hq, hr = HEX_DIRS[d]
            nxt = (anchor[0] + hq, anchor[1] + hr)
            if self._candidate_ok(nxt, corridor_set, owned):
                valid.append((idx, d, nxt))
        if not valid:
            return None

        def tower_adj(pos: tuple[int, int]) -> int:
            return sum(1 for dq, dr in HEX_DIRS if (pos[0] + dq, pos[1] + dr) in tower_tiles)

        chosen = weighted_top_n(valid, key=lambda v: (tower_adj(v[2]), -v[0]), n=self.top_n, rng=self.rng)
        assert chosen is not None  # `valid` is non-empty (checked above)
        _, d, nxt = chosen
        kind = "spawnpoint" if end == "spawn" else "castle"
        price = self._tile_price(tiles, empire)

        def apply(tgt: tuple[int, int] = nxt, old: tuple[int, int] = anchor,
                  anchor_kind: str = kind) -> None:
            tiles[_key(old)] = "path"
            tiles[_key(tgt)] = anchor_kind

        return MazeAction(
            description=f"maze: grow {end} end to ({nxt[0]},{nxt[1]})" + (" [turn]" if d != heading else ""),
            price=price, apply=apply, priority=PRIO_GROW, gain=10.0,
        )

    # ── Side tiles ───────────────────────────────────────────────────────

    def _side_tile_option(self, tiles: Tiles, corridor_set: set[tuple[int, int]],
                           owned: set[tuple[int, int]], corridor: list[tuple[int, int]],
                           empire: Empire) -> MazeAction | None:
        candidates: set[tuple[int, int]] = set()
        for q, r in corridor_set:
            for dq, dr in HEX_DIRS:
                n = (q + dq, r + dr)
                if n not in owned:
                    candidates.add(n)
        if not candidates:
            return None

        pts = path_points(corridor) if corridor else []
        srange = 2.0

        def score(pos: tuple[int, int]) -> float:
            adj = sum(1 for dq, dr in HEX_DIRS if (pos[0] + dq, pos[1] + dr) in corridor_set)
            cov = coverage_score(pos, srange, pts, lambda p: 1.0) if pts else 0.0
            return adj * 10.0 + cov

        best = weighted_top_n(sorted(candidates), key=score, n=self.top_n, rng=self.rng)
        if best is None or score(best) <= 0:
            return None
        price = self._tile_price(tiles, empire)

        def apply() -> None:
            tiles[_key(best)] = "empty"

        return MazeAction(
            description=f"maze: buy side tile ({best[0]},{best[1]})",
            price=price, apply=apply, priority=PRIO_BUY_SIDE, gain=5.0,
        )

    # ── Pricing helper ───────────────────────────────────────────────────

    def _tile_price(self, tiles: Tiles, empire: Empire) -> float:
        owned_count = sum(1 for v in tiles.values() if _tile_type(v) != "void")
        return self.tile_price_for(empire, owned_count + 1)


def era_filtered_structures(items: dict[str, ItemDetails], era_rank: dict[str, int],
                             era_index: int) -> dict[str, ItemDetails]:
    """Structures at or below `era_index`, keyed by iid — the sandbox's catalog."""
    return {iid: it for iid, it in items.items()
            if it.item_type == ItemType.STRUCTURE and era_rank.get(iid, 0) <= era_index}
