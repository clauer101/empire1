"""Defense strategy planner: replay-driven coverage optimization.

Flow per cycle (one action):
1. Analyze the newest unprocessed defense replay (each key fetched exactly once)
   → weak path segments stored in memory["defense_analysis"].
2. Score candidate tiles (owned empty + purchasable void) by weighted path
   coverage; pick the desired tower via class-mix balancing.
3. Place tower / buy tile / declare a savings goal when the best move is
   unaffordable / targeted upgrade / defensive-building fallback.
"""

from __future__ import annotations

import logging
import random

from bot.analyzer import ERA_RANK
from bot.defense_analysis import (
    analyze_replay, best_relocation, bfs_path, coverage_score, next_maze_tile,
    path_points, pick_tower, score_candidate_tiles, sell_to_carve_candidate,
    tower_class, tower_quality, weight_fn_from_memory,
)
from .base import (
    Action, BotContext, Option, Planner, cheapest_affordable, weighted_top_n,
)

log = logging.getLogger("bot.planner.defense")

# Buy a tile only if its coverage clearly beats the best owned spot
TILE_PURCHASE_MARGIN = 1.3
# Minimum path-length gain (tiles) to justify relocating spawn/castle
MIN_PATH_GAIN = 2
# Prod battle data: win rate peaks at 1.1–2.0 towers per path tile and
# collapses above 2.0 — beyond that, invest in upgrades, not more towers.
TOWER_DENSITY_MAX = 2.0
# Carve a serpentine maze until the path reaches this length (prod good mazes
# run 28-41 tiles); below this, lengthening the path beats coverage placement.
MAZE_LENGTH_TARGET = 28
# Keep at least this many owned covering spots in reserve — when towers use
# them up, the planner buys tiles so defense can keep expanding.
MIN_OWNED_COVER_SPOTS = 2
# Gold buffer required before spending on upgrades
UPGRADE_GOLD_BUFFER = 500
# Fallback sell refund rate when the summary lacks tower_sell_refund
SELL_REFUND_DEFAULT = 0.3
# Server-side cap per stat (economy handler MAX_UPGRADE_LEVEL)
MAX_UPGRADE_LEVEL = 20
# Upgradeable structure stats, in preference order after the range/damage pick
UPGRADE_STATS = ("damage", "range", "reload", "effect_duration", "effect_value")
# One workshop upgrade level lifts a stat by ~2.5% (see CLAUDE.md: +2-3%/level),
# so the strength gained ≈ tower_quality × this factor.
UPGRADE_QUALITY_GAIN = 0.025
# Maze carving lengthens the path so every tower covers it repeatedly — the
# pattern of strong human mazes. Boost its gain so carving outranks plain
# coverage placement while the maze is still short.
MAZE_CARVE_BONUS = 3.0
# Free defensive actions (relocate) get a high finite gain so they sort to the
# top of the free tier without needing mandatory status.
FREE_DEFENSE_GAIN = 100.0

# Mandatory-option priorities for the maze-building sequence. Kept below the
# baseline breach/tower-floor priorities (see baseline.py) so a breach response
# still wins; among themselves: sell-to-carve (unblock) > carve > widen.
PRIO_SELL_TO_CARVE = 12
PRIO_CARVE = 11
PRIO_WIDEN = 10

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
        # 1. Replay analysis (fetch each replay exactly once)
        self._refresh_analysis(ctx)
        weight_fn = weight_fn_from_memory(ctx.memory.get("defense_analysis"))

        tiles = ctx.api.get_map().get("tiles", {})
        structures = ctx.items.get("structures", {})
        opts: list[Option] = []

        # Per-bot maze seed: drawn once, persisted in memory, so the
        # serpentine plan stays stable across cycles but differs per bot.
        maze_seed = ctx.memory.setdefault("maze_seed",
                                          random.getrandbits(32) or 1)

        # 2a. Lengthen the path: relocate spawn/castle (free) whenever a
        #     placement on owned land makes the critter route clearly longer.
        reloc = (None if next_maze_tile(tiles, maze_seed)
                 else best_relocation(tiles))
        if reloc and reloc["new_len"] - reloc["old_len"] >= MIN_PATH_GAIN:
            new_tiles = reloc["tiles"]

            def _do_reloc(api, new_tiles=new_tiles):
                ctx.memory.pop("defense_analysis", None)  # bins refer to old path
                return api.save_map(new_tiles)
            opts.append(Option(
                category="defense", price=0.0, gain=FREE_DEFENSE_GAIN,
                description=f"relocate spawn/castle to lengthen path "
                            f"({reloc['old_len']}→{reloc['new_len']} tiles)",
                run=_do_reloc))

        # Ordered path: server-identical BFS over the map, replay as fallback
        path = bfs_path(tiles) or [
            (int(q), int(r)) for q, r in
            (ctx.memory.get("defense_analysis") or {}).get("path", [])]

        # 2. Desired tower (mix-balanced, unlocked; affordability checked later)
        placed_iids = [_tile_type(v) for v in tiles.values()
                       if _tile_type(v) in structures]
        placed_counts: dict[str, int] = {}
        for iid in placed_iids:
            cls = tower_class(structures[iid])
            placed_counts[cls] = placed_counts.get(cls, 0) + 1
        tower_iid = pick_tower(structures, placed_counts, ctx.is_unlocked,
                               top_n=ctx.top_n)
        if tower_iid is None:
            opts.extend(self._fallback_options(ctx))
            return opts
        tower = structures[tower_iid]
        tower_cost = float((tower.get("costs") or {}).get("gold", 0.0))
        tower_range = float(tower.get("range", 1.5) or 1.5)
        tower_q = tower_quality(tower)

        tile_price = float(ctx.summary.get("tile_price", 0.0) or 0.0)
        candidates = score_candidate_tiles(tiles, path, tower_range,
                                           weight_fn, tile_price)

        # A tower on an empty tile that carries the only route would sever the
        # path — the server rejects that ("Weg verbaut"). Filter those out.
        def _keeps_path(c) -> bool:
            sim = dict(tiles)
            sim[f"{c['q']},{c['r']}"] = "blocked"
            return bfs_path(sim) is not None

        owned = [c for c in candidates
                 if not c["needs_purchase"] and _keeps_path(c)]
        purchasable = [c for c in candidates if c["needs_purchase"]]
        owned_pick = weighted_top_n(owned, key=lambda c: c["score"], n=ctx.top_n)
        buy_pick = weighted_top_n(purchasable, key=lambda c: c["score"], n=ctx.top_n)

        density = (len(placed_iids) / len(path)) if path else 0.0
        short_maze = bool(path) and len(path) < MAZE_LENGTH_TARGET

        # 2b/2c. Maze carving while the path is short and not yet saturated.
        # Carving is the maze-building sequence: it lengthens the path so every
        # tower covers it repeatedly. Mark it mandatory so it takes precedence
        # over plain coverage placement (the old early-return behavior), exempt
        # from the density cap. Gated on being able to afford a tower so we never
        # sell to carve without the gold to rebuild elsewhere.
        if path and short_maze and ctx.gold >= tower_cost:
            spot = next_maze_tile(tiles, maze_seed)
            if spot:
                q, r = spot
                new_tiles = dict(tiles)
                new_tiles[f"{q},{r}"] = tower_iid
                old_len = len(path)
                new_len = len(bfs_path(new_tiles) or path)
                opts.append(Option(
                    category="defense", price=tower_cost,
                    gain=tower_q * MAZE_CARVE_BONUS,
                    mandatory=True, priority=PRIO_CARVE,
                    description=f"carve maze: place {tower_class(tower)} tower "
                                f"{tower_iid} at {q},{r} (path {old_len}→{new_len})",
                    run=lambda api, t=new_tiles: api.save_map(t),
                    saves_for=tower_cost,
                    goal_meta={"item": tower_iid, "action": "carve tower"}))
            else:
                # No safe wall tile but path still short. Offer both ways to
                # resume carving; the dispatcher picks the affordable one:
                #   • widen the block by buying the best covering void tile, and
                #   • sell a placed tower that blocks the serpentine plan (free).
                if purchasable:
                    q, r = buy_pick["q"], buy_pick["r"]
                    opts.append(Option(
                        category="defense", price=tile_price,
                        gain=tower_q * max(buy_pick["score"], 0.0) * MAZE_CARVE_BONUS,
                        mandatory=True, priority=PRIO_WIDEN,
                        description=f"buy tile {q},{r} (widen maze block)",
                        run=lambda api, q=q, r=r: api.buy_tile(q, r),
                        saves_for=tile_price,
                        goal_meta={"item": f"tile {q},{r}", "action": "tile"}))
                sell = self._sell_to_carve(ctx, tiles, structures, path,
                                           weight_fn, maze_seed)
                if sell is not None:
                    opts.append(Option(
                        category="defense", price=0.0, gain=FREE_DEFENSE_GAIN,
                        mandatory=True, priority=PRIO_SELL_TO_CARVE,
                        description=sell.description, run=sell.run))

        # 3a-pre. Expansion: owned covering spots running low → buy the best
        # purchasable covering tile so tower placement never stalls for land.
        if purchasable and len(owned) < MIN_OWNED_COVER_SPOTS:
            q, r = buy_pick["q"], buy_pick["r"]
            opts.append(Option(
                category="defense", price=tile_price,
                gain=tower_q * max(buy_pick["score"], 0.0),
                description=f"buy tile {q},{r} (owned cover spots "
                            f"{len(owned)}/{MIN_OWNED_COVER_SPOTS})",
                run=lambda api, q=q, r=r: api.buy_tile(q, r),
                saves_for=tile_price,
                goal_meta={"item": f"tile {q},{r}", "action": "tile"}))

        # 3a/3b. Coverage placement — only while below the density cap (above it,
        # more towers hurt; invest in quality instead via 3d below).
        if owned and density < TOWER_DENSITY_MAX:
            best = owned_pick
            if (buy_pick
                    and buy_pick["score"] > best["score"] * TILE_PURCHASE_MARGIN):
                # 3b. A purchasable tile is clearly better → buy it first.
                q, r = buy_pick["q"], buy_pick["r"]
                opts.append(Option(
                    category="defense", price=tile_price,
                    gain=tower_q * max(buy_pick["score"], 0.0),
                    description=f"buy tile {q},{r} (coverage {buy_pick['score']:.0f} "
                                f"> owned best {best['score']:.0f})",
                    run=lambda api, q=q, r=r: api.buy_tile(q, r),
                    saves_for=tile_price,
                    goal_meta={"item": f"tile {q},{r}", "action": "tile"}))
            q, r = best["q"], best["r"]
            new_tiles = dict(tiles)
            new_tiles[f"{q},{r}"] = tower_iid
            opts.append(Option(
                category="defense", price=tower_cost,
                gain=tower_q * max(best["score"], 0.0),
                description=f"place {tower_class(tower)} tower {tower_iid} at "
                            f"{q},{r} (coverage {best['score']:.0f})",
                run=lambda api, t=new_tiles: api.save_map(t),
                saves_for=tower_cost,
                goal_meta={"item": tower_iid, "action": "tower"}))

        # 3d. Quality investments: era-swap / workshop / expansion on a common
        # strength-per-gold basis (always offered; they win when placement is
        # capped or unavailable, and compete on ROI otherwise).
        opts.extend(self._investment_options(ctx, tiles, structures, path,
                                             weight_fn, tower_iid,
                                             owned_pick, buy_pick))

        # 3d-fallback. Targeted upgrade of the tower covering the weakest segment.
        up = self._targeted_upgrade(ctx, tiles, structures, path, weight_fn)
        if up is not None:
            opts.append(Option(
                category="defense", price=self._upgrade_price(ctx, up),
                gain=tower_q * UPGRADE_QUALITY_GAIN,
                description=up.description, run=up.run))

        # 3e. Fallback defensive building.
        opts.extend(self._fallback_options(ctx))
        return opts

    # ── helpers ───────────────────────────────────────────────────────────

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
                analyzed.append(key)  # don't retry forever
                continue
            analysis = analyze_replay(replay)
            mem = analysis.to_memory()
            mem["path"] = [list(p) for p in analysis.path]
            ctx.memory["defense_analysis"] = mem
            analyzed.append(key)
            log.info("analyzed replay %s: weak segments %s, reached %d",
                     key, analysis.weak_segments, analysis.reach_count)
            break  # one replay per cycle keeps API budget flat
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
        # Towers whose coverage of weak segments is highest get upgrades first
        def weak_coverage(entry):
            key, iid = entry
            rng = float(structures[iid].get("range", 1.5) or 1.5)
            return coverage_score(_parse_key(key), rng, pts, weight_fn)
        upgrades = ctx.summary.get("item_upgrades") or {}
        for key, iid in sorted(placed, key=weak_coverage, reverse=True):
            levels = upgrades.get(iid) or {}
            # range when the tower barely covers any path, damage otherwise
            rng = float(structures[iid].get("range", 1.5) or 1.5)
            plain_cov = coverage_score(_parse_key(key), rng, pts, lambda _p: 1.0)
            preferred = "range" if plain_cov < 4 else "damage"
            for stat in (preferred, *UPGRADE_STATS):
                if int(levels.get(stat, 0)) >= MAX_UPGRADE_LEVEL:
                    continue  # stat capped server-side — never retry it
                return Action(f"upgrade {iid} {stat} (covers weakest segment)",
                              lambda api, iid=iid, stat=stat:
                              api.buy_item_upgrade(iid, stat))
        return None  # every placed tower is fully upgraded

    def _investment_options(self, ctx: BotContext, tiles: dict, structures: dict,
                            path: list[tuple[int, int]], weight_fn,
                            tower_iid: str, owned_pick, buy_pick) -> list[Option]:
        """Quality investments as scored Options on a strength-per-gold basis.

        1. Era-swap — sell the weakest outdated (older-era) placed tower and
           build a current-era one in its place.
        2. Workshop — upgrade a placed tower's stat (tech instead of land/maze).

        Strength is measured in tower_quality units (gain), price is the net
        gold cost, so base_score = gain/price is comparable to the placement and
        carving options the planner also emits. Expansion (buy tile + tower) is
        already covered by the placement options above.
        """
        cur_era = ctx.summary.get("current_era", "stone")
        refund_rate = float(ctx.summary.get("tower_sell_refund",
                                            SELL_REFUND_DEFAULT)
                            or SELL_REFUND_DEFAULT)
        upgrade_prices = ctx.summary.get("item_upgrade_prices") or {}
        out: list[Option] = []

        swap = self._era_swap(ctx, tiles, structures, cur_era, refund_rate)
        if swap is not None:
            gain, price, act = swap
            out.append(Option(
                category="defense", price=price, gain=gain,
                description=act.description, run=act.run,
                saves_for=price,
                goal_meta={"item": "era-swap", "action": "era-swap"}))

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
        """Sell the weakest placed tower from an older era, build current-era.

        Returns (gain, net_price, action) or None. Cross-class and explicitly
        era-driven: any tower from a past era is a swap candidate, replaced by
        the strongest affordable current-era tower.
        """
        cur_rank = ERA_RANK.get(cur_era, 0)
        # Best current-era tower by quality (cross-class — replacing junk beats
        # preserving the class mix).
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
        # Oldest/weakest first.
        for key, old_iid in sorted(
                placed,
                key=lambda e: (ERA_RANK.get(structures[e[1]].get("era", "stone"), 0),
                               tower_quality(structures[e[1]]))):
            old = structures[old_iid]
            if ERA_RANK.get(old.get("era", "stone"), 0) >= cur_rank:
                break  # nothing older left — list is era-sorted
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
        """Best workshop (tech) upgrade as a (gain, price, action) triple."""
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

    def _sell_to_carve(self, ctx: BotContext, tiles: dict, structures: dict,
                       path: list[tuple[int, int]], weight_fn,
                       maze_seed: int) -> Action | None:
        """Sell the placed tower whose removal re-enables maze carving."""
        pts = path_points(path)
        placed = [(k, _tile_type(v)) for k, v in tiles.items()
                  if _tile_type(v) in structures]
        if not placed:
            return None

        # Try worst defensive value first — same metric as targeted upgrades.
        def weak_coverage(entry):
            key, iid = entry
            rng = float(structures[iid].get("range", 1.5) or 1.5)
            return coverage_score(_parse_key(key), rng, pts, weight_fn)
        order = [k for k, _ in sorted(placed, key=weak_coverage)]
        key = sell_to_carve_candidate(tiles, maze_seed, order)
        if key is None:
            return None
        iid = _tile_type(tiles[key])
        new_tiles = dict(tiles)
        new_tiles[key] = "empty"
        return Action(f"sell tower {iid} at {key} (unblock maze)",
                      lambda api: api.save_map(new_tiles))

    def _upgrade_price(self, ctx: BotContext, action: Action) -> float:
        """Look up the next upgrade price for the iid named in a targeted-upgrade
        action description (`upgrade <iid> <stat> ...`)."""
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
