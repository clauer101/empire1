"""Frontier defense planner: incremental corridor growth with flexible replanning.

Builds a single walkable corridor away from the castle (growing-tree style,
serpentine heading), buys side tiles along the corridor edge and places towers
on them. When the preferred direction is blocked the planner turns instead
(BA*-style replanning); a flood-safety rule (a new corridor tile may touch the
existing corridor at exactly one tile) guarantees the corridor never shortcuts
itself.

All applicable options are proposed every cycle (not just the first match) —
the dispatcher (bot/dispatch.py) picks the highest-priority AFFORDABLE one and
still tries lower-priority options when higher ones aren't affordable, so a
tick isn't stuck doing nothing just because the top option is too expensive
right now. Priority order (see PRIO_* constants), highest first:
1. Tower on any stray owned empty tile that is not part of the corridor
   (closes shortcut risks immediately).
2. Relocate the spawnpoint/castle onto the corridor tip (free, extends the
   live path).
3. Era-swap: replace an outdated placed tower with the best current-era one.
4. Flank: if a corridor tile has no adjacent tower yet, buy a side tile next
   to it — corridor segments are never left unguarded for long.
5. Grow the corridor: buy the next void tile at the tip (serpentine heading,
   turn when blocked).
6. Buy any remaining side tile adjacent to the corridor for extra towers.
7. Workshop-upgrade the most-placed tower type — lowest priority, so it only
   actually runs when nothing above it is affordable this cycle.
"""

from __future__ import annotations

import logging
import random
from collections import Counter

from bot.analyzer import ERA_RANK
from bot.defense_analysis import (
    HEX_DIRS, bfs_path, coverage_score, path_points, pick_tower, tower_class,
    tower_quality,
)
from .base import BotContext, Option, Planner, weighted_top_n

log = logging.getLogger("bot.planner.frontier")

SEG_LEN = 5          # straight steps before the serpentine prefers a U-turn
MAX_CORRIDOR = 60    # stop growing after this many corridor tiles

PRIO_TOWER_STRAY = 12
PRIO_RELOCATE    = 11
PRIO_ERA_SWAP    = 10  # replace an outdated tower before growing the maze further
PRIO_FLANK       =  9
PRIO_GROW        =  8
PRIO_BUY_SIDE    =  6
PRIO_UPGRADE     =  5  # absolute last resort: only when no side tile is buyable

SELL_REFUND_DEFAULT = 0.3
UPGRADE_STATS     = ("damage", "range", "reload", "effect_duration", "effect_value")


def _applicable_upgrade_stats(effects: dict) -> tuple[str, ...]:
    """UPGRADE_STATS filtered to what this tower's effects can actually use.

    damage/range/reload always apply. effect_duration/effect_value only
    modify shot effects the tower actually has (see
    network/handlers/economy.py::handle_buy_item_upgrade, which rejects a
    mismatched stat server-side, and battle_service._step_structures, which
    only scales slow_duration/burn_duration/slow_ratio/burn_dps). Without
    this filter a plain damage tower like HEAVY_TOWER (effects={}) could get
    gold spent on an effect_duration/effect_value level that never applies in
    combat — the server now rejects the purchase, but there's no reason to
    even try it.
    """
    stats = ["damage", "range", "reload"]
    if "slow_duration" in effects or "burn_duration" in effects:
        stats.append("effect_duration")
    if "slow_ratio" in effects or "burn_dps" in effects:
        stats.append("effect_value")
    return tuple(stats)


def _max_upgrade_level(era_rank: int) -> int:
    """Level cap for an item's era: 3 x (era_rank + 1) — every item is
    upgradable at least a little, later-era items allow more levels."""
    return 3 * (era_rank + 1)


def _focus_upgrade_stat(memory: dict, key: str, levels: dict,
                        stats: tuple[str, ...], cap: int) -> str | None:
    """Commit to upgrading ONE stat for this item (remembered in `memory`)
    until it hits `cap`, then randomly try a different one.

    Without this, always trying stats in the same fixed order means every
    bot/tower ends up maxing the same first stat — sticking to one
    randomly-chosen focus per item, and rotating only once it's capped,
    spreads upgrades across different stats over time and across the bot
    population instead.
    """
    focus = memory.setdefault("upgrade_focus", {})
    stat = focus.get(key)
    if stat is not None and int(levels.get(stat, 0)) >= cap:
        stat = None
    if stat is None:
        candidates = [s for s in stats if int(levels.get(s, 0)) < cap]
        if not candidates:
            focus.pop(key, None)
            return None
        stat = random.choice(candidates)
        focus[key] = stat
    return stat


def _tile_type(value) -> str:
    if isinstance(value, dict):
        return value.get("type", "")
    return str(value)


def _parse_key(key: str) -> tuple[int, int]:
    q, r = key.split(",")
    return int(q), int(r)


def _key(pos: tuple[int, int]) -> str:
    return f"{pos[0]},{pos[1]}"


def _most_common_placed_tower(tiles: dict, structures: dict) -> str | None:
    """The tower iid with the most placed instances on the map.

    Ties broken by iid for determinism."""
    counts = Counter(
        t for v in tiles.values()
        if (t := _tile_type(v)) in structures
    )
    if not counts:
        return None
    best = max(counts.values())
    return min(iid for iid, n in counts.items() if n == best)


class FrontierDefensePlanner(Planner):
    def propose_options(self, ctx: BotContext, *,
                        advance_phase: bool = True) -> list[Option]:
        # Maze building requires HUNTING (first tower unlock) — without it
        # bought tiles could never be towered, so don't start the maze at all.
        if "HUNTING" not in ctx.completed:
            return []
        map_data = ctx.get_map()
        tiles: dict = map_data.get("tiles", {})
        structures: dict = ctx.items.get("structures", {})

        spawns = [_parse_key(k) for k, v in tiles.items()
                  if _tile_type(v) == "spawnpoint"]
        castles = [_parse_key(k) for k, v in tiles.items()
                   if _tile_type(v) == "castle"]
        if not spawns or not castles:
            return []
        spawn, castle = spawns[0], castles[0]

        mem = ctx.memory.setdefault("frontier", {})
        corridor: list[str] = mem.setdefault("corridor", [])
        self._init_ends(mem, corridor, spawn, castle)

        # Per-bot seeded RNG so choices vary between bots but stay reproducible
        # for a given bot (and testable in the maze-sim tool). Advance the seed
        # each cycle so successive decisions differ.
        seed = ctx.memory.setdefault("maze_seed", random.getrandbits(32) or 1)
        step = int(mem.get("rng_step", 0))
        mem["rng_step"] = step + 1
        rng = random.Random(seed + step)

        corridor_set = {_parse_key(k) for k in corridor}
        owned = {_parse_key(k) for k, v in tiles.items()
                 if _tile_type(v) != "void"}
        # Tiles a previous buy_tile call found already owned by a neighboring
        # empire — never proposed again (there is no space to grow there).
        blocked = {tuple(p) for p in mem.setdefault("blocked_tiles", [])}

        # Collect every option this cycle instead of returning the first
        # match: options carry a `priority` (see PRIO_* above) precisely so
        # the dispatcher (bot/dispatch.py, strict priority order) can pick
        # the highest-priority AFFORDABLE one and still try lower-priority
        # options (e.g. a workshop upgrade) when higher ones — like a tile
        # purchase this empire can't yet afford — aren't affordable. A
        # planner that returns only its first non-None option defeats that:
        # the dispatcher never even sees the lower-priority alternatives.
        options: list[Option] = []

        # 1. Stray empties (owned, walkable, outside corridor) → tower NOW
        stray = [
            _parse_key(k) for k, v in tiles.items()
            if _tile_type(v) == "empty" and _parse_key(k) not in corridor_set
        ]
        if stray:
            opt = self._tower_option(ctx, tiles, structures, stray, rng)
            if opt:
                options.append(opt)

        # 2. Spawn not on its corridor end → relocate it there (free). The spawn
        #    end is corridor[0]; after a spawn-end grow the freshly bought tile is
        #    corridor[0] and the spawn is one tile inward, so this moves it out.
        spawn_end = _parse_key(corridor[0])
        if spawn != spawn_end and _tile_type(tiles.get(_key(spawn_end), "")) in ("empty", "path"):
            options.append(self._relocate_option(spawn, spawn_end, "spawnpoint"))

        # 3. Castle not on its corridor end → relocate it there (free). The castle
        #    end is corridor[-1]; mirror of the spawn relocation. Only once the
        #    corridor has two distinct ends (len >= 2).
        castle_end = _parse_key(corridor[-1])
        if (corridor[-1] != corridor[0] and castle != castle_end
                and _tile_type(tiles.get(_key(castle_end), "")) in ("empty", "path")):
            options.append(self._relocate_option(castle, castle_end, "castle"))

        # 4. Era-swap: replace an outdated placed tower with the best
        #    current-era tower (sell + rebuild in one save_map). Higher
        #    priority than upgrade — spending gold to level up a tower that's
        #    about to be replaced would be wasted. Also higher than growing
        #    the maze so tower quality is brought up to date before the
        #    corridor expands.
        swap = self._era_swap_option(ctx, tiles, structures)
        if swap:
            options.append(swap)

        # 5. Upgrade a current-era tower when that is cheaper than the next tile
        #    purchase. Expanding the maze costs `tile_price`; if improving a placed
        #    tower costs less, spend on the upgrade instead. Lowest priority here —
        #    the dispatcher falls back to it when era-swap/flank/grow/buy-side are
        #    all unaffordable or unavailable this cycle.
        upgrade = self._upgrade_option(ctx, tiles, structures)
        if upgrade:
            options.append(upgrade)

        # 6. Flank: every corridor tile (except the two live ends) needs an
        #    adjacent tower spot before we keep growing.
        flank = self._flank_option(ctx, corridor, corridor_set, owned, rng, blocked)
        if flank:
            options.append(flank)

        # 7. Grow the corridor at BOTH ends, alternating: the spawn end
        #    (corridor[0], spawn follows) and the castle end (corridor[-1], castle
        #    follows). Try the `next_end` first; if blocked, try the other end.
        if len(corridor) < MAX_CORRIDOR:
            tower_tiles = {_parse_key(k) for k, v in tiles.items()
                           if _tile_type(v) in structures}
            first = mem.get("next_end", "spawn")
            order = [first, "castle" if first == "spawn" else "spawn"]
            for name in order:
                end_index = 0 if name == "spawn" else -1
                grow = self._grow_option(
                    ctx, tiles, mem["ends"][name], corridor, corridor_set,
                    owned, tower_tiles, rng, end_index=end_index,
                    append=(name == "castle"), blocked=blocked)
                if grow:
                    # Advance the cursor so the other end goes next cycle.
                    mem["next_end"] = "castle" if name == "spawn" else "spawn"
                    options.append(grow)
                    break

        # 8. Buy the best side tile along the corridor for a future tower
        side = self._side_tile_option(ctx, tiles, structures, corridor_set,
                                      owned, rng, blocked)
        if side:
            options.append(side)

        return options

    # ── Flanking ────────────────────────────────────────────────────────────

    def _flank_option(self, ctx: BotContext, corridor: list[str],
                      corridor_set: set[tuple[int, int]],
                      owned: set[tuple[int, int]],
                      rng: random.Random,
                      blocked: set[tuple[int, int]] = frozenset()) -> Option | None:
        """Wall in the corridor: buy EVERY missing neighbor tile of the oldest
        unwalled corridor tile.

        No gaps are tolerated — each corridor tile (except the two still-growing
        ends) must have all its non-corridor neighbors owned, so rule 1 turns
        them into a contiguous tower wall on both sides. `blocked` holds tiles
        already known to belong to another empire, so a failed purchase there
        never gets retried.
        """
        corridor_pos = [_parse_key(k) for k in corridor]

        # Skip both ends — they are still growing and get walled on later passes.
        for pos in corridor_pos[1:-1]:
            missing = [
                (pos[0] + dq, pos[1] + dr) for dq, dr in HEX_DIRS
                if (pos[0] + dq, pos[1] + dr) not in owned
                and (pos[0] + dq, pos[1] + dr) not in blocked
            ]
            if not missing:
                continue

            def adjacency(p: tuple[int, int]) -> int:
                return sum(1 for dq, dr in HEX_DIRS
                           if (p[0] + dq, p[1] + dr) in corridor_set)

            # Weighted-random among the best missing neighbors for inter-bot variety.
            best = weighted_top_n(missing, key=adjacency, n=ctx.top_n, rng=rng)
            price = float(ctx.summary.get("tile_price", 0.0))

            def run(api, p=best):
                res = api.buy_tile(p[0], p[1])
                if isinstance(res, dict) and res.get("success") is False:
                    self._remember_blocked(ctx, p)
                return res

            return Option(
                category="defense",
                description=f"frontier: flank tile ({best[0]},{best[1]}) "
                            f"for corridor ({pos[0]},{pos[1]})",
                run=run, price=price, gain=9.0,
                mandatory=True, priority=PRIO_FLANK,
            )
        return None

    def _remember_blocked(self, ctx: BotContext, pos: tuple[int, int]) -> None:
        """Record a tile that buy_tile rejected as foreign-owned, so future
        cycles pick a different tile instead of retrying the same failure."""
        mem = ctx.memory.setdefault("frontier", {})
        blocked_list = mem.setdefault("blocked_tiles", [])
        entry = [pos[0], pos[1]]
        if entry not in blocked_list:
            blocked_list.append(entry)

    # ── Growth ──────────────────────────────────────────────────────────────

    def _initial_heading(self, front: tuple[int, int],
                         back: tuple[int, int]) -> int:
        """Heading pointing from `back` toward `front` (i.e. outward from back)."""
        dq, dr = front[0] - back[0], front[1] - back[1]
        best, best_dot = 0, -999
        for i, (hq, hr) in enumerate(HEX_DIRS):
            dot = hq * dq + hr * dr
            if dot > best_dot:
                best, best_dot = i, dot
        return best

    def _init_ends(self, mem: dict, corridor: list[str],
                   spawn: tuple[int, int], castle: tuple[int, int]) -> None:
        """Seed a fresh corridor and migrate legacy single-ended state.

        Target layout: corridor[0] = spawn end, corridor[-1] = castle end, with
        per-end serpentine state under mem["ends"]. Legacy corridors grew at the
        tip with the spawn chasing it, so on migration the growing tip end is the
        spawn end — reverse the list so corridor[0] becomes that spawn end, then
        make sure the castle key sits at corridor[-1].
        """
        if not corridor:
            corridor.append(_key(spawn))
            if _key(castle) != _key(spawn):
                corridor.append(_key(castle))

        if "ends" not in mem:
            legacy = {
                "heading": mem.get("heading", 0),
                "turn_dir": mem.get("turn_dir", 1),
                "seg_steps": mem.get("seg_steps", 0),
                "turns_in_row": mem.get("turns_in_row", 0),
            }
            # Legacy tip (corridor[-1]) was the spawn end → make it corridor[0].
            if "heading" in mem:
                corridor.reverse()
            if _key(castle) not in corridor:
                corridor.append(_key(castle))
            elif corridor and corridor[-1] != _key(castle):
                # Keep the castle at the castle end.
                corridor.remove(_key(castle))
                corridor.append(_key(castle))
            mem["ends"] = {
                "spawn": legacy,
                "castle": {"heading": self._initial_heading(castle, spawn),
                           "turn_dir": 1, "seg_steps": 0, "turns_in_row": 0},
            }
            for k in ("heading", "turn_dir", "seg_steps", "turns_in_row"):
                mem.pop(k, None)
        mem.setdefault("next_end", "spawn")

    def _candidate_ok(self, pos: tuple[int, int],
                      corridor_set: set[tuple[int, int]],
                      owned: set[tuple[int, int]],
                      blocked: set[tuple[int, int]] = frozenset()) -> bool:
        """A new corridor tile must be void and touch the corridor exactly once.

        Both anchors live in the corridor (spawn on corridor[0], castle on
        corridor[-1]), so touching corridor_set exactly once forbids shortcuts at
        either end without a separate castle term. `blocked` holds tiles a prior
        buy_tile attempt found already owned by another empire.
        """
        if pos in owned or pos in blocked:
            return False
        touches = sum(
            1 for dq, dr in HEX_DIRS
            if (pos[0] + dq, pos[1] + dr) in corridor_set
        )
        return touches == 1

    def _grow_option(self, ctx: BotContext, tiles: dict, end_state: dict,
                     corridor: list[str], corridor_set: set[tuple[int, int]],
                     owned: set[tuple[int, int]],
                     tower_tiles: set[tuple[int, int]], rng: random.Random, *,
                     end_index: int, append: bool,
                     blocked: set[tuple[int, int]] = frozenset()) -> Option | None:
        tip = _parse_key(corridor[end_index])
        heading = int(end_state.get("heading", 0))
        turn_dir = int(end_state.get("turn_dir", 1))
        want_turn = int(end_state.get("seg_steps", 0)) >= SEG_LEN

        # Serpentine preference: straight while the segment lasts, then U-turn.
        straight = [heading]
        turns = [(heading + turn_dir) % 6, (heading - turn_dir) % 6,
                 (heading + 2 * turn_dir) % 6, (heading - 2 * turn_dir) % 6]
        order = (turns[:2] + straight + turns[2:]) if want_turn \
            else (straight + turns)

        # Valid candidates in serpentine order; then prefer those that hug
        # existing towers (path runs alongside the wall, not into open space).
        valid: list[tuple[int, int, tuple[int, int]]] = []  # (order_idx, d, pos)
        for idx, d in enumerate(order):
            hq, hr = HEX_DIRS[d]
            nxt = (tip[0] + hq, tip[1] + hr)
            if self._candidate_ok(nxt, corridor_set, owned, blocked):
                valid.append((idx, d, nxt))
        if not valid:
            return None  # fully blocked → this end is finished

        def tower_adj(pos: tuple[int, int]) -> int:
            return sum(1 for dq, dr in HEX_DIRS
                       if (pos[0] + dq, pos[1] + dr) in tower_tiles)

        # Weighted-random among the best candidates (tower-hugging, then serpentine
        # order) so bots diverge instead of all carving the identical maze.
        chosen = weighted_top_n(
            valid, key=lambda v: (tower_adj(v[2]), -v[0]), n=ctx.top_n, rng=rng)
        _, d, nxt = chosen
        turned = d != heading

        def run(api, q=nxt[0], r=nxt[1], nd=d, was_turn=turned):
            res = api.buy_tile(q, r)
            if isinstance(res, dict) and res.get("success"):
                if append:
                    corridor.append(f"{q},{r}")
                else:
                    corridor.insert(0, f"{q},{r}")
                end_state["heading"] = nd
                if was_turn:
                    end_state["turns_in_row"] = int(end_state.get("turns_in_row", 0)) + 1
                    if end_state["turns_in_row"] >= 2:  # U-turn done → next row
                        end_state["turn_dir"] = -int(end_state.get("turn_dir", 1))
                        end_state["turns_in_row"] = 0
                    end_state["seg_steps"] = 0
                else:
                    end_state["seg_steps"] = int(end_state.get("seg_steps", 0)) + 1
                    end_state["turns_in_row"] = 0
            elif isinstance(res, dict) and res.get("success") is False:
                self._remember_blocked(ctx, (q, r))
            return res

        price = float(ctx.summary.get("tile_price", 0.0))
        end_label = "castle" if append else "spawn"
        return Option(
            category="defense",
            description=f"frontier: grow {end_label} end to ({nxt[0]},{nxt[1]})"
                        + (" [turn]" if turned else ""),
            run=run, price=price, gain=10.0,
            mandatory=True, priority=PRIO_GROW,
        )

    # ── Relocation ───────────────────────────────────────────────────────────

    def _relocate_option(self, old_pos: tuple[int, int],
                         new_pos: tuple[int, int], kind: str) -> Option:
        """Move the spawnpoint or castle from old_pos to new_pos (free save_map).

        `kind` is "spawnpoint" or "castle". Old tile becomes path, new tile
        becomes the anchor; the two are adjacent so the path stays connected.
        """
        def run(api):
            new_tiles = dict(api.get_map()["tiles"])
            new_tiles[_key(old_pos)] = "path"
            new_tiles[_key(new_pos)] = kind
            return api.save_map(new_tiles)

        label = "castle" if kind == "castle" else "spawn"
        return Option(
            category="defense",
            description=f"frontier: move {label} to ({new_pos[0]},{new_pos[1]})",
            run=run, price=0.0, gain=50.0,
            mandatory=True, priority=PRIO_RELOCATE,
        )

    # ── Towers ──────────────────────────────────────────────────────────────

    def _tower_option(self, ctx: BotContext, tiles: dict, structures: dict,
                      stray: list[tuple[int, int]],
                      rng: random.Random) -> Option | None:
        placed_counts: dict[str, int] = {}
        for k, v in tiles.items():
            t = _tile_type(v)
            if t in structures:
                cls = tower_class(structures[t])
                placed_counts[cls] = placed_counts.get(cls, 0) + 1
        iid = pick_tower(structures, placed_counts, lambda it: True,
                         top_n=ctx.top_n)
        if iid is None:
            return None

        path = bfs_path(tiles) or []
        pts = path_points(path) if path else []
        trange = float(structures[iid].get("range", 1.0) or 1.0)

        def score(pos: tuple[int, int]) -> float:
            return coverage_score(pos, trange, pts, lambda p: 1.0) if pts else 0.0

        # Weighted-random among the best-covering stray tiles for variety.
        best = weighted_top_n(stray, key=score, n=ctx.top_n, rng=rng)
        price = float((structures[iid].get("costs") or {}).get("gold", 0.0))

        def run(api, pos=best, tower=iid):
            new_tiles = dict(api.get_map()["tiles"])
            new_tiles[_key(pos)] = tower
            return api.save_map(new_tiles)

        return Option(
            category="defense",
            description=f"frontier: tower {iid} at ({best[0]},{best[1]})",
            run=run, price=price, gain=8.0,
            mandatory=True, priority=PRIO_TOWER_STRAY,
        )

    def _highest_unlocked_tower_rank(self, ctx: BotContext, structures: dict) -> int:
        """Highest era rank with at least one unlocked tower.

        The empire's nominal tech era (``current_era``) can outpace its actually
        unlocked towers when era-defining knowledge is researched before the
        tower-specific requirements (e.g. IRON unlocks the Iron era, but
        ARBELESTE_TOWER also needs FORGE). Matching pick_tower()'s own logic
        here keeps era-swap/upgrade from stalling in that gap.
        """
        ranks = [ERA_RANK.get(it.get("era", "stone"), 0)
                 for it in structures.values() if ctx.is_unlocked(it)]
        return max(ranks, default=0)

    def _era_swap_option(self, ctx: BotContext, tiles: dict,
                         structures: dict) -> Option | None:
        """Replace the oldest-era placed tower with the best current-era tower.

        Sells the outdated tower (partial gold refund) and rebuilds the strongest
        available current-era tower on the same tile in a single save_map. Oldest
        era first (cheapest to replace), matching the cheapest-first upgrade rule.
        """
        cur_rank = self._highest_unlocked_tower_rank(ctx, structures)

        # Best unlocked tower of the current era.
        best_new, best_new_q = None, 0.0
        for iid, item in structures.items():
            if ERA_RANK.get(item.get("era", "stone"), 0) != cur_rank:
                continue
            if not ctx.is_unlocked(item):
                continue
            q = tower_quality(item)
            if q > best_new_q:
                best_new, best_new_q = iid, q
        if best_new is None:
            return None
        new_cost = float((structures[best_new].get("costs") or {}).get("gold", 0.0))
        refund_rate = float(ctx.summary.get("tower_sell_refund", SELL_REFUND_DEFAULT)
                            or SELL_REFUND_DEFAULT)

        placed = [(k, _tile_type(v)) for k, v in tiles.items()
                  if _tile_type(v) in structures]
        # Oldest era first (then weakest) so the cheapest outdated tower goes first.
        for key, old_iid in sorted(
                placed,
                key=lambda e: (ERA_RANK.get(structures[e[1]].get("era", "stone"), 0),
                               tower_quality(structures[e[1]]))):
            old = structures[old_iid]
            if ERA_RANK.get(old.get("era", "stone"), 0) >= cur_rank:
                break  # remaining towers are all current-era or newer
            old_cost = float((old.get("costs") or {}).get("gold", 0.0))
            net_cost = new_cost - refund_rate * old_cost
            gain = best_new_q - tower_quality(old)
            if net_cost <= 0 or gain <= 0:
                continue
            new_tiles = dict(tiles)
            new_tiles[key] = best_new

            def run(api, t=new_tiles):
                return api.save_map(t)

            return Option(
                category="defense",
                description=f"frontier: era-swap {old_iid} → {best_new} at {key}",
                run=run, price=net_cost, gain=gain,
                mandatory=True, priority=PRIO_ERA_SWAP,
            )
        return None

    def _upgrade_option(self, ctx: BotContext, tiles: dict,
                        structures: dict) -> Option | None:
        """Upgrade workshop stats for the most-placed tower type on the map.

        Upgrades apply per iid regardless of how many instances are placed,
        so upgrading whichever tower type is most common benefits the
        largest share of the maze. Absolute last priority (PRIO_UPGRADE) —
        only proposed once nothing more impactful (tower/relocate/era-swap/
        flank/grow/buy-side) is available or affordable this cycle.
        """
        upgrade_prices = ctx.summary.get("item_upgrade_prices") or {}
        upgrades = ctx.summary.get("item_upgrades") or {}

        iid = _most_common_placed_tower(tiles, structures)
        if iid is None:
            return None
        price = float(upgrade_prices.get(iid, 0.0) or 0.0)
        if price <= 0:
            return None

        levels = upgrades.get(iid) or {}
        cap = _max_upgrade_level(ERA_RANK.get(structures[iid].get("era", "stone"), 0))
        applicable = _applicable_upgrade_stats(structures[iid].get("effects") or {})
        stat = _focus_upgrade_stat(ctx.memory, iid, levels, applicable, cap)
        if stat is None:
            return None

        def run(api, iid=iid, stat=stat):
            return api.buy_item_upgrade(iid, stat)

        return Option(
            category="defense",
            description=f"frontier: upgrade {iid} {stat} (most-placed tower)",
            run=run, price=price, gain=6.0,
            mandatory=True, priority=PRIO_UPGRADE,
        )

    def _side_tile_option(self, ctx: BotContext, tiles: dict, structures: dict,
                          corridor_set: set[tuple[int, int]],
                          owned: set[tuple[int, int]],
                          rng: random.Random,
                          blocked: set[tuple[int, int]] = frozenset()) -> Option | None:
        # Purchasable voids adjacent to the corridor (they become tower spots).
        candidates = set()
        for q, r in corridor_set:
            for dq, dr in HEX_DIRS:
                n = (q + dq, r + dr)
                if n not in owned and n not in blocked:
                    candidates.add(n)
        if not candidates:
            return None

        path = bfs_path(tiles) or []
        pts = path_points(path) if path else []
        # Generic mid-size range for scoring the spot itself
        srange = 2.0

        def score(pos: tuple[int, int]) -> float:
            adj = sum(1 for dq, dr in HEX_DIRS
                      if (pos[0] + dq, pos[1] + dr) in corridor_set)
            cov = coverage_score(pos, srange, pts, lambda p: 1.0) if pts else 0.0
            return adj * 10.0 + cov

        # Weighted-random among the best side spots for inter-bot variety.
        best = weighted_top_n(sorted(candidates), key=score, n=ctx.top_n, rng=rng)
        if score(best) <= 0:
            return None
        price = float(ctx.summary.get("tile_price", 0.0))

        def run(api, pos=best):
            res = api.buy_tile(pos[0], pos[1])
            if isinstance(res, dict) and res.get("success") is False:
                self._remember_blocked(ctx, pos)
            return res

        return Option(
            category="defense",
            description=f"frontier: buy side tile ({best[0]},{best[1]})",
            run=run, price=price, gain=5.0,
            mandatory=True, priority=PRIO_BUY_SIDE,
        )
