"""Frontier defense planner: incremental corridor growth with flexible replanning.

Builds a single walkable corridor away from the castle (growing-tree style,
serpentine heading), buys side tiles along the corridor edge and places towers
on them. When the preferred direction is blocked the planner turns instead
(BA*-style replanning); a flood-safety rule (a new corridor tile may touch the
existing corridor at exactly one tile) guarantees the corridor never shortcuts
itself.

**The live map is the only state.** Every position is re-derived each cycle
from `GET /api/map` (`defense_analysis.corridor_from_map`) — the way a human
player reads the board before deciding what to buy. Nothing positional is ever
remembered between cycles, so the planner cannot drift out of sync with the
server. It used to persist the corridor in bot memory, which silently diverged
from the real map on all three production bots and left them planning against
a phantom location for a week.

The invariant that makes derivation work: after every completed action the map
alone describes the maze. Corridor tiles are always `spawnpoint`/`path`/
`castle`, so an `empty` tile is always a tower spot (or the debris of an
interrupted grow — see the repair action). That is why growing is ATOMIC: one
action buys the tile AND moves the anchor onto it.

All applicable options are proposed every cycle (not just the first match) —
the dispatcher (bot/dispatch.py) picks the highest-priority AFFORDABLE one and
still tries lower-priority options when higher ones aren't affordable, so a
tick isn't stuck doing nothing just because the top option is too expensive
right now. Priority order (see PRIO_* constants), highest first:
1. Tower on any owned empty tile (a tower spot, or leftover grow debris).
2. Repair: finish an interrupted grow by moving the anchor onto its dangling
   empty neighbor (free).
3. Era-swap: replace an outdated placed tower with the best current-era one.
4. Flank: if a corridor tile has no adjacent tower yet, buy a side tile next
   to it — corridor segments are never left unguarded for long.
5. Grow the corridor: buy the next void tile at an end and move the anchor
   onto it, in one action (serpentine heading, turn when blocked).
6. Buy any remaining side tile adjacent to the corridor for extra towers.
7. Workshop-upgrade the most-placed tower type — lowest priority, so it only
   actually runs when nothing above it is affordable this cycle.

Tiles a neighboring empire owns are skipped up front using the fog-range view
(`ctx.foreign_tiles`, from `GET /api/map/neighbors` — the same information the
map screen shows a human). If that view is unavailable the bot just attempts
the purchase and reads the rejection; a failed `buy_tile` is excluded for the
rest of the tick only (bot/dispatch.py) and retried fresh next cycle, never
blacklisted permanently — land ownership nearby changes over a season.
"""

from __future__ import annotations

import logging
import random
from collections import Counter

from bot.analyzer import ERA_RANK
from bot.defense_analysis import (
    HEX_DIRS, corridor_from_map, coverage_score, end_state, path_points,
    pick_tower, tower_class, tower_quality,
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

        # Drop the geometry this planner used to persist. It could drift away
        # from the live map with nothing to notice, which is exactly what broke
        # the production bots; positions are derived below instead.
        ctx.memory.pop("frontier", None)

        # Per-bot seeded RNG so choices vary between bots but stay reproducible
        # for a given bot (and testable). Advance the step each call so
        # successive decisions within a tick differ — otherwise a rejected
        # tile would be re-picked identically for the whole tick.
        seed = ctx.memory.setdefault("maze_seed", random.getrandbits(32) or 1)
        step = int(ctx.memory.get("maze_step", 0))
        ctx.memory["maze_step"] = step + 1
        rng = random.Random(seed + step)

        corridor, corridor_set = corridor_from_map(map_data)
        owned = {_parse_key(k) for k, v in tiles.items()
                 if _tile_type(v) != "void"}
        foreign = ctx.foreign_tiles

        # Collect every option this cycle instead of returning the first
        # match: options carry a `priority` (see PRIO_* above) precisely so
        # the dispatcher (bot/dispatch.py, strict priority order) can pick
        # the highest-priority AFFORDABLE one and still try lower-priority
        # options (e.g. a workshop upgrade) when higher ones — like a tile
        # purchase this empire can't yet afford — aren't affordable. A
        # planner that returns only its first non-None option defeats that:
        # the dispatcher never even sees the lower-priority alternatives.
        options: list[Option] = []

        # 1. Every owned empty tile is a tower spot — tower it. Under the
        #    map-only invariant an "empty" is never part of the corridor, so
        #    this also cleans up a grow whose relocation half failed.
        stray = [_parse_key(k) for k, v in tiles.items()
                 if _tile_type(v) == "empty"]
        if stray:
            opt = self._tower_option(ctx, tiles, structures, stray, corridor, rng)
            if opt:
                options.append(opt)

        # 2. Era-swap: replace an outdated placed tower with the best
        #    current-era tower (sell + rebuild in one save_map). Higher
        #    priority than upgrade — spending gold to level up a tower that's
        #    about to be replaced would be wasted. Also higher than growing
        #    the maze so tower quality is brought up to date before the
        #    corridor expands.
        swap = self._era_swap_option(ctx, tiles, structures)
        if swap:
            options.append(swap)

        # 3. Upgrade a current-era tower when that is cheaper than the next tile
        #    purchase. Expanding the maze costs `tile_price`; if improving a placed
        #    tower costs less, spend on the upgrade instead. Lowest priority here —
        #    the dispatcher falls back to it when era-swap/flank/grow/buy-side are
        #    all unaffordable or unavailable this cycle.
        upgrade = self._upgrade_option(ctx, tiles, structures)
        if upgrade:
            options.append(upgrade)

        # Everything below needs to know where the corridor runs. Without a
        # route (spawn and castle exist but nothing connects them — a data
        # event or a hand-edited map) the corridor actions would all be
        # guesses, so skip them and say so once: the missing signal here is
        # what let the production bots fail silently for a week. Towers and
        # upgrades above still run, so gold keeps being spent usefully.
        if not corridor:
            self._warn_no_route(spawns[0], castles[0])
            return options
        self._no_route_key = None

        # 4. Repair: an anchor with a dangling empty neighbor is a grow whose
        #    relocation half did not land — finish it for free.
        for anchor, kind in ((corridor[0], "spawnpoint"), (corridor[-1], "castle")):
            repair = self._repair_option(tiles, anchor, kind, corridor_set)
            if repair:
                options.append(repair)

        # 5. Flank: every corridor tile (except the two live ends) needs an
        #    adjacent tower spot before we keep growing.
        flank = self._flank_option(ctx, corridor, corridor_set, owned, foreign, rng)
        if flank:
            options.append(flank)

        # 6. Grow at BOTH ends — the dispatcher runs whichever is affordable.
        #    Which end is offered first alternates with the owned-tile count:
        #    every successful grow buys exactly one tile, so the parity flips
        #    each time. That keeps the two ends taking turns for callers that
        #    execute only the single best option (Planner.propose) without
        #    needing a stored cursor.
        if len(corridor_set) < MAX_CORRIDOR:
            tower_tiles = {_parse_key(k) for k, v in tiles.items()
                           if _tile_type(v) in structures}
            ends = ("spawn", "castle") if len(owned) % 2 == 0 else ("castle", "spawn")
            for end in ends:
                grow = self._grow_option(ctx, corridor, corridor_set, owned,
                                         tower_tiles, foreign, rng, end=end)
                if grow:
                    options.append(grow)

        # 7. Buy the best side tile along the corridor for a future tower
        side = self._side_tile_option(ctx, tiles, structures, corridor_set,
                                      owned, foreign, corridor, rng)
        if side:
            options.append(side)

        return options

    def _warn_no_route(self, spawn: tuple[int, int],
                       castle: tuple[int, int]) -> None:
        """Log once per spawn/castle pair that the maze has no walkable route.

        propose_options runs up to ~40x per tick, so this is deduped on the
        planner (PLANNERS holds one instance) to keep the signal readable.
        """
        key = (spawn, castle)
        if getattr(self, "_no_route_key", None) == key:
            return
        self._no_route_key = key
        log.warning("no spawn→castle route on the live map (spawn %s, castle %s)"
                    " — skipping corridor actions, towers/upgrades continue",
                    spawn, castle)

    # ── Flanking ────────────────────────────────────────────────────────────

    def _flank_option(self, ctx: BotContext, corridor: list[tuple[int, int]],
                      corridor_set: set[tuple[int, int]],
                      owned: set[tuple[int, int]],
                      foreign: set[tuple[int, int]],
                      rng: random.Random) -> Option | None:
        """Wall in the corridor: buy EVERY missing neighbor tile of the oldest
        unwalled corridor tile.

        No gaps are tolerated — each corridor tile (except the two still-growing
        ends) must have all its non-corridor neighbors owned, so rule 1 turns
        them into a contiguous tower wall on both sides. Tiles a neighboring
        empire owns are skipped up front via the fog-range view; when that view
        is unavailable the purchase is simply attempted and the rejection is
        excluded for the rest of the tick (bot/dispatch.py), never blacklisted.
        """
        # Skip both ends — they are still growing and get walled on later passes.
        for pos in corridor[1:-1]:
            missing = [
                (pos[0] + dq, pos[1] + dr) for dq, dr in HEX_DIRS
                if (pos[0] + dq, pos[1] + dr) not in owned
                and (pos[0] + dq, pos[1] + dr) not in foreign
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
                return api.buy_tile(p[0], p[1])

            return Option(
                category="defense",
                description=f"frontier: flank tile ({best[0]},{best[1]}) "
                            f"for corridor ({pos[0]},{pos[1]})",
                run=run, price=price, gain=9.0,
                mandatory=True, priority=PRIO_FLANK, mutates_map=True,
            )
        return None

    # ── Growth ──────────────────────────────────────────────────────────────

    def _touches_once(self, pos: tuple[int, int],
                      corridor_set: set[tuple[int, int]]) -> bool:
        """Flood safety: `pos` may join the corridor at exactly one tile.

        Both anchors live in the corridor (spawn at corridor[0], castle at
        corridor[-1]), so a single touch forbids shortcuts at either end
        without a separate castle term.
        """
        return sum(1 for dq, dr in HEX_DIRS
                   if (pos[0] + dq, pos[1] + dr) in corridor_set) == 1

    def _candidate_ok(self, pos: tuple[int, int],
                      corridor_set: set[tuple[int, int]],
                      owned: set[tuple[int, int]],
                      foreign: set[tuple[int, int]] = frozenset()) -> bool:
        """A new corridor tile must be buyable void and satisfy flood safety."""
        return (pos not in owned and pos not in foreign
                and self._touches_once(pos, corridor_set))

    def _grow_option(self, ctx: BotContext, corridor: list[tuple[int, int]],
                     corridor_set: set[tuple[int, int]],
                     owned: set[tuple[int, int]],
                     tower_tiles: set[tuple[int, int]],
                     foreign: set[tuple[int, int]], rng: random.Random, *,
                     end: str) -> Option | None:
        """Extend one end by one tile: buy it AND move the anchor onto it.

        Both halves live in a single action on purpose. A bought-but-not-yet-
        connected tile would be a piece of maze state the live map cannot
        express (it looks exactly like a tower spot), and remembering it is
        what used to drift out of sync. Doing both here keeps the invariant
        that the map alone describes the maze.
        """
        walk = corridor if end == "spawn" else corridor[::-1]
        anchor = walk[0]
        heading, seg_steps, turn_dir = end_state(walk)
        want_turn = seg_steps >= SEG_LEN

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
            nxt = (anchor[0] + hq, anchor[1] + hr)
            if self._candidate_ok(nxt, corridor_set, owned, foreign):
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
        kind = "spawnpoint" if end == "spawn" else "castle"

        def run(api, tgt=nxt, old=anchor, anchor_kind=kind):
            res = api.buy_tile(tgt[0], tgt[1])
            if isinstance(res, dict) and res.get("success") is False:
                return res  # nothing bought, nothing to connect
            # save_map replaces the whole map, so build the payload from a
            # FRESH read — a snapshot from the start of the cycle would delete
            # tiles bought earlier in this tick.
            new_tiles = dict(api.get_map()["tiles"])
            new_tiles[_key(old)] = "path"
            new_tiles[_key(tgt)] = anchor_kind
            return api.save_map(new_tiles)

        price = float(ctx.summary.get("tile_price", 0.0))
        return Option(
            category="defense",
            description=f"frontier: grow {end} end to ({nxt[0]},{nxt[1]})"
                        + (" [turn]" if d != heading else ""),
            run=run, price=price, gain=10.0,
            mandatory=True, priority=PRIO_GROW, mutates_map=True,
        )

    # ── Relocation ───────────────────────────────────────────────────────────

    def _repair_option(self, tiles: dict, anchor: tuple[int, int], kind: str,
                       corridor_set: set[tuple[int, int]]) -> Option | None:
        """Finish a grow whose relocation half did not land.

        An owned `empty` tile hanging off an anchor and touching the corridor
        exactly once can only be a bought corridor step that never got walked
        onto — an ordinary tower spot either isn't next to an anchor or touches
        the corridor more than once. Adopting it is free and strictly better
        than towering it, so it runs before the priced stray-tower option.
        """
        cands = sorted(
            n for n in ((anchor[0] + dq, anchor[1] + dr) for dq, dr in HEX_DIRS)
            if _tile_type(tiles.get(_key(n), "")) == "empty"
            and self._touches_once(n, corridor_set)
        )
        return self._relocate_option(anchor, cands[0], kind) if cands else None

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
            mandatory=True, priority=PRIO_RELOCATE, mutates_map=True,
        )

    # ── Towers ──────────────────────────────────────────────────────────────

    def _tower_option(self, ctx: BotContext, tiles: dict, structures: dict,
                      stray: list[tuple[int, int]],
                      corridor: list[tuple[int, int]],
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

        pts = path_points(corridor) if corridor else []
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
            mandatory=True, priority=PRIO_TOWER_STRAY, mutates_map=True,
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
            # Build the payload from a FRESH read: save_map replaces the whole
            # map, so posting this cycle's snapshot would delete any tile
            # bought earlier in the same tick.
            def run(api, k=key, iid=best_new):
                new_tiles = dict(api.get_map()["tiles"])
                new_tiles[k] = iid
                return api.save_map(new_tiles)

            return Option(
                category="defense",
                description=f"frontier: era-swap {old_iid} → {best_new} at {key}",
                run=run, price=net_cost, gain=gain,
                mandatory=True, priority=PRIO_ERA_SWAP, mutates_map=True,
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
                          foreign: set[tuple[int, int]],
                          corridor: list[tuple[int, int]],
                          rng: random.Random) -> Option | None:
        # Purchasable voids adjacent to the corridor (they become tower spots).
        candidates = set()
        for q, r in corridor_set:
            for dq, dr in HEX_DIRS:
                n = (q + dq, r + dr)
                if n not in owned and n not in foreign:
                    candidates.add(n)
        if not candidates:
            return None

        pts = path_points(corridor) if corridor else []
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
            return api.buy_tile(pos[0], pos[1])

        return Option(
            category="defense",
            description=f"frontier: buy side tile ({best[0]},{best[1]})",
            run=run, price=price, gain=5.0,
            mandatory=True, priority=PRIO_BUY_SIDE, mutates_map=True,
        )
