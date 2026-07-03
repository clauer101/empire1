"""Defense strategy planner: greedy path-adjacent tower placement.

Build priority per cycle:
1. Place tower on owned empty tile adjacent to path (row 1) — with extension guard
2. Buy void tile adjacent to path (creates new row 1 spots)
3. Buy void tile whose tower placement would lengthen the path
4. Build on row 2 (adjacent to row 1) — only when no tiles can be purchased
[Guard] Never build on the last tile that could still extend the path

Upgrades (era-swap, workshop, targeted) are always offered in addition to the
maze improvement options above — not as a fallback. The dispatcher picks among
all emitted options per iteration of the multi-action tick loop.
"""

from __future__ import annotations

import logging

from bot.analyzer import ERA_RANK
from bot.defense_analysis import (
    HEX_DIRS, analyze_replay, best_relocation, bfs_path, coverage_score,
    path_points, pick_tower, tower_class, tower_quality, weight_fn_from_memory,
)
from .base import (
    Action, BotContext, Option, Planner, cheapest_affordable, weighted_top_n,
)

log = logging.getLogger("bot.planner.defense")

# Mandatory-option priorities (kept below baseline breach/tower-floor)
PRIO_BUILD_ROW1    = 12
PRIO_RELOCATE      = 11  # free, wins over tile purchase on score but loses to row1 build
PRIO_BUY_PATH_ADJ  = 11
PRIO_BUY_EXTENSION = 10
PRIO_ERA_SWAP      =  9  # below all placement/buy options so tower count grows first

# Gain multipliers — ensure maze improvement outscores upgrades
ROW1_GAIN_BONUS = 8.0   # row1 build always beats upgrades
ROW2_GAIN_BONUS = 2.0   # row2 beats upgrades but loses to any buying option

MIN_PATH_GAIN     = 1
FREE_DEFENSE_GAIN = 100.0

UPGRADE_GOLD_BUFFER  = 500
SELL_REFUND_DEFAULT  = 0.3
MAX_UPGRADE_LEVEL    = 20
UPGRADE_STATS        = ("damage", "range", "reload", "effect_duration", "effect_value")
UPGRADE_QUALITY_GAIN = 0.025

DEFENSIVE_EFFECTS = ("siege_offset", "wave_delay_offset",
                     "restore_life_after_loss_offset", "max_life_modifier",
                     "life_regen_modifier")


def _tile_type(value) -> str:
    if isinstance(value, dict):
        return value.get("type", "")
    return str(value)


def _parse_key(key: str) -> tuple[int, int]:
    q, r = key.split(",")
    return int(q), int(r)


class DefensePlanner(Planner):
    def propose_options(self, ctx: BotContext, *,
                        advance_phase: bool = True) -> list[Option]:
        self._refresh_analysis(ctx)
        weight_fn = weight_fn_from_memory(ctx.memory.get("defense_analysis"))

        map_data = ctx.get_map()
        tiles = map_data.get("tiles", {})
        structures = ctx.items.get("structures", {})
        opts: list[Option] = []

        raw_path = map_data.get("path") or []
        path: list[tuple[int, int]] = [tuple(p) for p in raw_path]  # type: ignore[misc]
        if not path:
            path = bfs_path(tiles)  # fallback if server omits path
        if not path:
            opts.extend(self._investment_options(ctx, tiles, structures, [],
                                                 weight_fn, None))
            opts.extend(self._fallback_options(ctx))
            return opts

        pts = path_points(path)

        # Tile classification
        path_set = frozenset(
            _parse_key(k) for k, v in tiles.items()
            if _tile_type(v) in {"path", "spawnpoint", "castle"}
        )
        owned = frozenset(
            _parse_key(k) for k, v in tiles.items()
            if _tile_type(v) != "void"
        )
        owned_empty = [
            _parse_key(k) for k, v in tiles.items()
            if _tile_type(v) == "empty"
        ]

        # Purchasable void tiles (adjacent to owned land)
        explicit_void = frozenset(
            _parse_key(k) for k, v in tiles.items()
            if _tile_type(v) == "void"
        )
        implicit_void = (
            frozenset((q + dq, r + dr) for q, r in owned for dq, dr in HEX_DIRS)
            - owned - explicit_void
        )
        purchasable = frozenset(
            (q, r) for q, r in (explicit_void | implicit_void)
            if any((q + dq, r + dr) in owned for dq, dr in HEX_DIRS)
        )

        # Tower selection (class-mix balanced)
        placed_iids = [_tile_type(v) for v in tiles.values()
                       if _tile_type(v) in structures]
        placed_counts: dict[str, int] = {}
        for iid in placed_iids:
            cls = tower_class(structures[iid])
            placed_counts[cls] = placed_counts.get(cls, 0) + 1
        tower_iid = pick_tower(structures, placed_counts, ctx.is_unlocked,
                               top_n=ctx.top_n)

        tile_price = float(ctx.summary.get("tile_price", 0.0) or 0.0)
        tower_cost = 0.0
        tower_range = 1.5
        tower_q = 1.0  # default for gain calc when no tower available yet
        tower_cls = "damage"
        if tower_iid:
            tower = structures[tower_iid]
            tower_cost = float((tower.get("costs") or {}).get("gold", 0.0))
            tower_range = float(tower.get("range", 1.5) or 1.5)
            tower_q = tower_quality(tower)
            tower_cls = tower_class(tower)

        def _cov(t: tuple[int, int]) -> float:
            return coverage_score(t, tower_range, pts, weight_fn)

        # ── Row 1: owned empty tiles adjacent to path (needs tower to place) ──
        row1 = [(q, r) for q, r in owned_empty
                if any((q + dq, r + dr) in path_set for dq, dr in HEX_DIRS)]

        # Path-adjacent purchasable tiles (used in extension guard + prio 2)
        path_adj_buy = sorted(
            [(q, r) for q, r in purchasable
             if any((q + dq, r + dr) in path_set for dq, dr in HEX_DIRS)],
            key=_cov, reverse=True)

        # Safe row1: any path-adjacent empty tile where building doesn't sever the path.
        safe_row1: list[tuple[int, int]] = []
        for q, r in row1:
            sim = dict(tiles)
            sim[f"{q},{r}"] = "blocked"
            if bfs_path(sim) is not None:
                safe_row1.append((q, r))
        safe_row1 = sorted(safe_row1, key=_cov, reverse=True)

        # Relocation (free): always check, emitted whenever it gains >= MIN_PATH_GAIN.
        # PRIO=11 < row1 build PRIO=12, so row1 wins when affordable.
        # When row1 unaffordable, relocation wins over tile purchase on score
        # (gain=100, price=0 → infinite ROI).
        reloc = best_relocation(tiles)
        if reloc and reloc["new_len"] - reloc["old_len"] >= MIN_PATH_GAIN:
            new_tiles = reloc["tiles"]

            def _do_reloc(api, nt=new_tiles):
                ctx.memory.pop("defense_analysis", None)
                return api.save_map(nt)
            opts.append(Option(
                category="defense", price=0.0, gain=FREE_DEFENSE_GAIN,
                mandatory=True, priority=PRIO_RELOCATE,
                description=f"relocate spawn/castle "
                            f"({reloc['old_len']}→{reloc['new_len']} tiles)",
                run=_do_reloc))

        if tower_iid:
            # PRIORITY 1: Build on row 1 (path-adjacent)
            if safe_row1:
                q, r = weighted_top_n(safe_row1, key=_cov, n=ctx.top_n)
                new_tiles = dict(tiles)
                new_tiles[f"{q},{r}"] = tower_iid
                opts.append(Option(
                    category="defense", price=tower_cost,
                    gain=tower_q * ROW1_GAIN_BONUS * max(_cov((q, r)), 1.0),
                    mandatory=True, priority=PRIO_BUILD_ROW1,
                    description=f"build {tower_cls} tower {tower_iid} at {q},{r} "
                                f"(path-adjacent, coverage {_cov((q, r)):.0f})",
                    run=lambda api, t=new_tiles: api.save_map(t),
                    saves_for=tower_cost,
                    goal_meta={"item": tower_iid, "action": "tower"}))

        # PRIORITY 2: Buy void tile adjacent to path (always, even without tower)
        if path_adj_buy:
            q, r = weighted_top_n(path_adj_buy, key=_cov, n=ctx.top_n)
            opts.append(Option(
                category="defense", price=tile_price,
                gain=tower_q * max(_cov((q, r)), 1.0),
                mandatory=True, priority=PRIO_BUY_PATH_ADJ,
                description=f"buy tile {q},{r} adjacent to path",
                run=lambda api, q=q, r=r: api.buy_tile(q, r),
                saves_for=tile_price,
                goal_meta={"item": f"tile {q},{r}", "action": "tile"}))

        # PRIORITY 3: Buy tile enabling path extension (only when 1+2 unavailable)
        # Simulate buying + immediately placing a tower (non-traversable) to see
        # if the BFS path gets longer (critters forced to detour).
        if not safe_row1 and not path_adj_buy and purchasable:
            ext_buy: list[tuple[int, int]] = []
            for q, r in purchasable:
                sim = dict(tiles)
                sim[f"{q},{r}"] = "WALL"  # non-traversable: simulates tower after buy
                new_p = bfs_path(sim)
                if new_p and len(new_p) > len(path):
                    ext_buy.append((q, r))
            if ext_buy:
                q, r = weighted_top_n(ext_buy, key=_cov, n=ctx.top_n)
                opts.append(Option(
                    category="defense", price=tile_price,
                    gain=tower_q * max(_cov((q, r)), 0.5),
                    mandatory=True, priority=PRIO_BUY_EXTENSION,
                    description=f"buy tile {q},{r} (enables path extension)",
                    run=lambda api, q=q, r=r: api.buy_tile(q, r),
                    saves_for=tile_price,
                    goal_meta={"item": f"tile {q},{r}", "action": "tile"}))

        if tower_iid:
            # PRIORITY 4: Row 2 — only when no tiles can be purchased
            if not purchasable:
                row1_positions = frozenset(
                    (q + dq, r + dr)
                    for q, r in path_set
                    for dq, dr in HEX_DIRS
                ) | path_set
                row2 = [(q, r) for q, r in owned_empty
                        if (q, r) not in row1_positions
                        and any((q + dq, r + dr) in row1_positions
                                for dq, dr in HEX_DIRS)]
                safe_row2: list[tuple[int, int]] = []
                for q, r in row2:
                    sim = dict(tiles)
                    sim[f"{q},{r}"] = "blocked"
                    if bfs_path(sim) is not None:
                        safe_row2.append((q, r))
                if safe_row2:
                    q, r = weighted_top_n(safe_row2, key=_cov, n=ctx.top_n)
                    new_tiles = dict(tiles)
                    new_tiles[f"{q},{r}"] = tower_iid
                    opts.append(Option(
                        category="defense", price=tower_cost,
                        gain=tower_q * ROW2_GAIN_BONUS * max(_cov((q, r)), 1.0),
                        description=f"build {tower_cls} tower {tower_iid} at {q},{r} "
                                    f"(row 2, coverage {_cov((q, r)):.0f})",
                        run=lambda api, t=new_tiles: api.save_map(t),
                        saves_for=tower_cost,
                        goal_meta={"item": tower_iid, "action": "tower"}))

        # DEADLOCK BREAK: sell a path-adjacent tower when all expansion options
        # exhausted (no row1, no path-adj buy, no ext_buy, relocation blocked).
        # Converts a tower back to empty, creating a new row1 spot next cycle.
        # ext_buy is only populated when not safe_row1 and not path_adj_buy
        _ext_buy_found = any(True for q, r in purchasable
                             for sim in [dict(tiles) | {f"{q},{r}": "WALL"}]
                             for new_p in [bfs_path(sim)]
                             if new_p and len(new_p) > len(path))
        deadlocked = (not safe_row1 and not path_adj_buy and not _ext_buy_found
                      and not (reloc and reloc["new_len"] - reloc["old_len"] >= MIN_PATH_GAIN))
        if deadlocked and structures:
            refund_rate = float(ctx.summary.get("tower_sell_refund", SELL_REFUND_DEFAULT)
                                or SELL_REFUND_DEFAULT)
            # Find path-adjacent towers; only sell when doing so enables a
            # relocation gain — avoids the build→sell→build loop within one tick.
            adj_towers = [
                (k, iid)
                for k, v in tiles.items()
                for iid in [_tile_type(v)]
                if iid in structures
                and any((_parse_key(k)[0] + dq, _parse_key(k)[1] + dr) in path_set
                        for dq, dr in HEX_DIRS)
            ]
            best_sell: tuple[str, str, int] | None = None
            for sell_key, sell_iid in sorted(
                    adj_towers, key=lambda e: tower_quality(structures[e[1]])):
                sim_tiles = dict(tiles)
                sim_tiles[sell_key] = "empty"
                sim_reloc = best_relocation(sim_tiles)
                if sim_reloc and sim_reloc["new_len"] - sim_reloc["old_len"] >= MIN_PATH_GAIN:
                    best_sell = (sell_key, sell_iid,
                                 sim_reloc["new_len"] - sim_reloc["old_len"])
                    break
            if best_sell:
                sell_key, sell_iid, reloc_gain = best_sell
                sell_cost = float((structures[sell_iid].get("costs") or {}).get("gold", 0.0))
                refund = sell_cost * refund_rate
                new_tiles = dict(tiles)
                new_tiles[sell_key] = "empty"
                opts.append(Option(
                    category="defense", price=0.0,
                    gain=FREE_DEFENSE_GAIN * 0.5,
                    mandatory=True, priority=PRIO_BUY_EXTENSION,
                    description=f"sell {sell_iid} at {sell_key} to break deadlock "
                                f"(enables +{reloc_gain} path tiles, +{refund:.0f}g)",
                    run=lambda api, t=new_tiles: api.save_map(t)))

        # ── Era-swap first; workshop only when no era-swap available ─────────
        # Era-swap replaces old-era towers with current-era towers. Workshop
        # upgrades only happen once all placed towers are already current-era.
        cur_era = ctx.summary.get("current_era", "stone")
        refund_rate_inv = float(ctx.summary.get("tower_sell_refund", SELL_REFUND_DEFAULT)
                                or SELL_REFUND_DEFAULT)
        upgrade_prices = ctx.summary.get("item_upgrade_prices") or {}
        swap = self._era_swap(ctx, tiles, structures, cur_era, refund_rate_inv)
        if swap is not None:
            gain, price, act = swap
            # Non-mandatory, no savings-goal: era-swaps happen opportunistically
            # after new tower placement so tower count grows before quality improves.
            opts.append(Option(
                category="defense", price=price, gain=gain,
                mandatory=False, priority=PRIO_ERA_SWAP,
                description=act.description, run=act.run))
        # Workshop + targeted upgrades always offered (era-swap not exclusive)
        wk = self._workshop_option(ctx, tiles, structures, path, weight_fn,
                                   upgrade_prices)
        if wk is not None:
            gain, price, act = wk
            opts.append(Option(
                category="defense", price=price, gain=gain,
                description=act.description, run=act.run))
        up = self._targeted_upgrade(ctx, tiles, structures, path, weight_fn)
        if up is not None:
            opts.append(Option(
                category="defense", price=self._upgrade_price(ctx, up),
                gain=tower_q * UPGRADE_QUALITY_GAIN,
                description=up.description, run=up.run))

        opts.extend(self._fallback_options(ctx))
        return opts

    # ── helpers ───────────────────────────────────────────────────────────────

    def _refresh_analysis(self, ctx: BotContext) -> None:
        pending = ctx.memory.get("defense_replays", [])
        analyzed = ctx.memory.setdefault("analyzed_replay_keys", [])
        for key in pending:
            if key in analyzed:
                continue
            try:
                replay = ctx.api.get_replay(key)
            except Exception as exc:
                log.warning("replay fetch failed %s: %s", key, exc)
                analyzed.append(key)
                continue
            analysis = analyze_replay(replay)
            mem = analysis.to_memory()
            mem["path"] = [list(p) for p in analysis.path]
            ctx.memory["defense_analysis"] = mem
            analyzed.append(key)
            log.info("analyzed replay %s: weak segments %s, reached %d",
                     key, analysis.weak_segments, analysis.reach_count)
            break  # one replay per cycle
        ctx.memory["analyzed_replay_keys"] = analyzed[-10:]

    def _targeted_upgrade(self, ctx: BotContext, tiles: dict, structures: dict,
                          path: list[tuple[int, int]], weight_fn) -> Action | None:
        if ctx.spendable_gold <= UPGRADE_GOLD_BUFFER:
            return None
        pts = path_points(path)
        placed = [(k, _tile_type(v)) for k, v in tiles.items()
                  if _tile_type(v) in structures]
        if not placed:
            return None

        def weak_coverage(entry):
            key, iid = entry
            rng = float(structures[iid].get("range", 1.5) or 1.5)
            return coverage_score(_parse_key(key), rng, pts, weight_fn)

        upgrades = ctx.summary.get("item_upgrades") or {}
        for key, iid in sorted(placed, key=weak_coverage, reverse=True):
            levels = upgrades.get(iid) or {}
            rng = float(structures[iid].get("range", 1.5) or 1.5)
            plain_cov = coverage_score(_parse_key(key), rng, pts, lambda _p: 1.0)
            preferred = "range" if plain_cov < 4 else "damage"
            for stat in (preferred, *UPGRADE_STATS):
                if int(levels.get(stat, 0)) >= MAX_UPGRADE_LEVEL:
                    continue
                return Action(f"upgrade {iid} {stat} (covers weakest segment)",
                              lambda api, iid=iid, stat=stat:
                              api.buy_item_upgrade(iid, stat))
        return None

    def _investment_options(self, ctx: BotContext, tiles: dict, structures: dict,
                            path: list[tuple[int, int]], weight_fn,
                            tower_iid: str | None) -> list[Option]:
        """Era-swap and workshop upgrade as scored Options."""
        cur_era = ctx.summary.get("current_era", "stone")
        refund_rate = float(ctx.summary.get("tower_sell_refund", SELL_REFUND_DEFAULT)
                            or SELL_REFUND_DEFAULT)
        upgrade_prices = ctx.summary.get("item_upgrade_prices") or {}
        out: list[Option] = []

        swap = self._era_swap(ctx, tiles, structures, cur_era, refund_rate)
        if swap is not None:
            gain, price, act = swap
            out.append(Option(
                category="defense", price=price, gain=gain,
                mandatory=False, priority=PRIO_ERA_SWAP,
                description=act.description, run=act.run))

        wk = self._workshop_option(ctx, tiles, structures, path, weight_fn,
                                   upgrade_prices)
        if wk is not None:
            gain, price, act = wk
            out.append(Option(
                category="defense", price=price, gain=gain,
                description=act.description, run=act.run))
        return out

    def _era_swap(self, ctx: BotContext, tiles: dict, structures: dict,
                  cur_era: str, refund_rate: float
                  ) -> tuple[float, float, Action] | None:
        cur_rank = ERA_RANK.get(cur_era, 0)
        best_new = None
        best_new_q = 0.0
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

        placed = [(k, _tile_type(v)) for k, v in tiles.items()
                  if _tile_type(v) in structures]
        for key, old_iid in sorted(
                placed,
                key=lambda e: (ERA_RANK.get(structures[e[1]].get("era", "stone"), 0),
                               tower_quality(structures[e[1]]))):
            old = structures[old_iid]
            if ERA_RANK.get(old.get("era", "stone"), 0) >= cur_rank:
                break
            old_cost = float((old.get("costs") or {}).get("gold", 0.0))
            net_cost = new_cost - refund_rate * old_cost
            if net_cost <= 0:
                continue
            gain = best_new_q - tower_quality(old)
            if gain <= 0:
                continue
            new_tiles = dict(tiles)
            new_tiles[key] = best_new
            act = Action(
                f"era-swap {old_iid} → {best_new} at {key} "
                f"(gain/gold {gain / net_cost:.3f})",
                lambda api, t=new_tiles: api.save_map(t))
            return (gain, net_cost, act)
        return None

    def _workshop_option(self, ctx: BotContext, tiles: dict, structures: dict,
                         path: list[tuple[int, int]], weight_fn,
                         upgrade_prices: dict) -> tuple[float, float, Action] | None:
        pts = path_points(path)
        placed = [(k, _tile_type(v)) for k, v in tiles.items()
                  if _tile_type(v) in structures]
        upgrades = ctx.summary.get("item_upgrades") or {}

        def weak_coverage(entry):
            key, iid = entry
            rng = float(structures[iid].get("range", 1.5) or 1.5)
            return coverage_score(_parse_key(key), rng, pts, weight_fn)

        for key, iid in sorted(placed, key=weak_coverage, reverse=True):
            levels = upgrades.get(iid) or {}
            rng = float(structures[iid].get("range", 1.5) or 1.5)
            plain_cov = coverage_score(_parse_key(key), rng, pts, lambda _p: 1.0)
            preferred = "range" if plain_cov < 4 else "damage"
            for stat in (preferred, *UPGRADE_STATS):
                if int(levels.get(stat, 0)) >= MAX_UPGRADE_LEVEL:
                    continue
                price = float(upgrade_prices.get(iid, 0.0) or 0.0)
                if price <= 0:
                    continue
                gain = tower_quality(structures[iid]) * UPGRADE_QUALITY_GAIN
                act = Action(
                    f"upgrade {iid} {stat} (workshop, gain/gold {gain / price:.3f})",
                    lambda api, iid=iid, stat=stat: api.buy_item_upgrade(iid, stat))
                return (gain, price, act)
        return None

    def _upgrade_price(self, ctx: BotContext, action: Action) -> float:
        prices = ctx.summary.get("item_upgrade_prices") or {}
        parts = action.description.split()
        iid = parts[1] if len(parts) > 1 else ""
        return float(prices.get(iid, 0.0) or 0.0)

    def _fallback_options(self, ctx: BotContext) -> list[Option]:
        if ctx.summary.get("build_queue"):
            return []

        def _defensive(item: dict) -> bool:
            effects = item.get("effects") or {}
            return any(k in effects for k in DEFENSIVE_EFFECTS)

        buildings = ctx.items.get("buildings", {})
        iid = cheapest_affordable(buildings, ctx, _defensive)
        if not iid:
            return []
        price = float((buildings.get(iid, {}).get("costs") or {}).get("gold", 0.0))
        return [Option(category="defense", price=price, gain=1.0, filler=True,
                       description=f"build defensive {iid}",
                       run=lambda api, iid=iid: api.build(iid))]
