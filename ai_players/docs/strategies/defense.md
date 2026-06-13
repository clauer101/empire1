# Defense Strategy

> **Implementation:** `ai_players/bot/planners/defense.py` — `DefensePlanner.propose()`.
> Analysis/geometry: `bot/defense_analysis.py` (`analyze_replay`, `coverage_score`,
> `score_candidate_tiles`, `pick_tower`); saving: `bot/savings.py`; replay fetch:
> `api_client.get_replay` (gzip decode); replay keys queued by
> `bot/analyzer.py::process_new_reports` into `memory.defense_replays`.
> Weights/durations: `config.yaml`; defeat-boost: `bot/strategy.py::roll_strategy`.
> This file is the spec — when the planner changes, update it (and vice versa).

**Goal:** Make the own hex map harder to break through, using battle replays to
find and close the exact path segments where critters get through.

Default weight: 3. Duration: 3–8 hours. Weight is doubled after a recent
defensive defeat. Independently of the random roll, **any AI breach forces an
immediate switch to this strategy** (`strategy.py::breach_defense_strategy`) —
breaches are always answered by building out the defense.

## Replay analysis

Each defense battle report carries a replay key. The planner downloads every
replay exactly once (`memory.analyzed_replay_keys`, capped at 10; one fetch per
cycle) and histograms critter deaths over path progress (10 bins):

- **Weak segments** = zero-kill bins, or late-path bins with less than half the
  average kills — stretches where critters pass mostly unharmed.
- No kills at all but breaches → the entire path is weak.

The result (weak segments, death histogram, ordered path) is persisted in
`memory.defense_analysis`. Without any replay yet, coverage uses uniform weights.

## Coverage scoring

Candidate tiles are owned empty tiles **and** purchasable void tiles adjacent to
owned land. Empty tiles whose occupation would sever the only spawn→castle
route are excluded (the server rejects such placements). The map API only lists existing tiles, so void candidates are
derived from hex adjacency (any missing neighbor of owned land is purchasable). Each is scored by the weighted number of interpolated path points
within the tower's range (continuous hex distance, matching the server's
targeting math). Points inside weak segments count 3×.

## Tower mix

Towers are classified by effects: `slow`, `splash`, or `damage` (burn counts as
damage). The placed mix is steered toward **damage : slow : splash ≈ 3 : 1 : 1**;
the planner picks the best unlocked tower of the most under-represented class by
`damage / reload_time × (1 + range/4)`.

## What prod data shows (4,033 AI battles, 2026-06)

Analysis of `ai_battle_log` plus the hex maps of the best/worst prod defenders
(`data/prod/state.yaml`) yields three robust, monotonic predictors of defense
success — the planner's priorities are tuned to them:

| Factor | Evidence | Planner consequence |
|---|---|---|
| **Path length** | win% rises from 55% (path <5) to 84% (path ≥30); breach rate falls 32% → 1.4% | spawn/castle relocation is action priority 0; tile buying feeds it |
| **Tower density** | sweet spot 1.1–2.0 towers per path tile (≈73% win); **>2.0 collapses to 53%** | `TOWER_DENSITY_MAX = 2.0`: above it, no more towers — upgrades/buildings instead |
| **Gold per tower** | 50k–200k gold/tower → 82% win, >200k → 88%, <1k → 57% | targeted upgrades are preferred over cramming once density is healthy |
| Tower mix | all top maps: majority damage + 10–25% slow/splash, no zero-coverage path tile, avg coverage ≥4 | 3:1:1 mix target, coverage-scored placement |

Worst defenders confirm the inverse: short paths (<10) with high density
(FosCo: 1.9 towers/tile on a 19-tile path, 27% win) lose to long, well-covered
paths with fewer but stronger towers.

## Maze carving (seeded serpentine)

While the path is shorter than `MAZE_LENGTH_TARGET` (28 tiles), the planner
carves a serpentine maze: towers are placed ON owned tiles to build walls
perpendicular to the spawn→castle axis, each wall leaving a one-tile gap at
alternating ends so the route doubles back (`defense_analysis.plan_maze_walls`
/ `next_maze_tile`). Rules:

- The owned field is every non-void tile (towers count — they already act as
  walls); a serpentine plan needs at least 9 owned tiles.
- The wall gap must be a traversable tile, and the first gap sits at the end
  far from the spawn — otherwise the wall would align with the natural
  diagonal and yield no path gain.
- **Seeded randomization:** each bot draws a persistent random
  `memory.maze_seed` once; the seed varies the wall-grid offset and lane
  widths so every bot builds a visibly different maze. The plan is a pure
  function of (tiles, seed) and therefore stable across build cycles. A
  randomized layout that would not lengthen the path falls back to the
  deterministic legacy plan; seed 0 = legacy layout.
- Carving is **exempt from the density cap**: every carved tower lengthens
  the path, so it lowers density.
- When no safe wall tile remains but the path is still short, the planner
  buys the best covering void tile ("widen maze block") when affordable, so
  carving can resume; unaffordable → sell-to-carve (see Selling towers),
  then fall through to tower placement.

## Selling towers

Removing a structure via map save refunds **30%** of its gold cost
(server `tower_sell_refund`, read from the summary; fallback
`SELL_REFUND_DEFAULT = 0.3`). The planner sells in exactly two situations:

1. **Sell-to-carve** — carving stalled (`next_maze_tile` = None), path still
   < 28, and no affordable widening tile: a single badly placed tower may be
   what blocks the serpentine plan. Placed towers are tried worst-coverage
   first (`sell_to_carve_candidate`); a removal counts only when playing the
   resumed serpentine plan to completion (simulated on a copy) yields a path
   **≥ 2 tiles longer** than the current one — this kills sell/rebuild churn
   where carving would just refill the freed tile. The winner is sold via
   `save_map` with the tile set to `empty`. Guard: only when gold ≥ current
   tower cost, so the bot can rebuild elsewhere — never sell the defense
   into a hole.
2. **Tier-up replacement** — quality mode (path ≥ 28, or density-capped):
   replace the lowest-quality placed tower with the best unlocked tower of
   the **same class** (preserves the 3:1:1 mix), but only when the new tower's
   quality (`damage / reload × (1 + range/4)`) is at least
   **`REPLACE_QUALITY_RATIO = 1.5×`** that of the old one, and
   `gold + 0.3 × old_cost ≥ new_cost`. One replacement per cycle, same tile,
   single `save_map` (the server refunds the old and charges the new tower in
   one save). Skipped while a savings goal is active. Note: item upgrades are
   iid-bound (`item_upgrades[iid]`), so levels bought on the old tower type
   keep benefiting other placed instances of that type.

The maze-sim (`bot/sim.py::SimApi`) mirrors the 30% refund
(`TOWER_SELL_REFUND`) and exposes `tower_sell_refund` in its summary, so both
behaviors are testable in the simulator.

## Path lengthening (spawn/castle relocation)

The critter path is the server's BFS from spawnpoint to castle over walkable
tiles. Moving spawnpoint and castle is free (`PUT /api/map`), so an integral
part of defense is maximizing the path length: the planner recomputes the
server-identical BFS (`defense_analysis.bfs_path`) and searches all
spawn/castle placements on owned empty tiles (`best_relocation`). When a
layout lengthens the shortest path by ≥2 tiles, the relocation is executed
before any other defense action; the stored replay analysis is reset because
its progress bins refer to the old path. Maps with multiple spawnpoints are
left untouched. Relocation never fires mid-carve (while `next_maze_tile`
still has a wall tile): moving spawn/castle would invalidate the serpentine
plan and waste the towers already placed.

## Actions (in priority order, one per cycle)

0. **Relocate spawn/castle** — lengthen the critter path (see above); free,
   highest priority (skipped mid-carve).
0c. **Carve maze** — while the path is < 28 tiles, place the desired tower on
   the next seeded serpentine wall tile; no safe wall tile left → buy the best
   covering void tile to widen the block (see Maze carving).
0d. **Sell-to-carve** — carving stalled and widening unaffordable → sell the
   one tower whose removal re-enables carving (see Selling towers).
0b. **Density cap** — at ≥2.0 towers per path tile no further coverage towers
   are placed (prod data: win rate collapses). Dense but **short** maze
   (path < 28): buy or save for a widening tile so carving can resume;
   otherwise: tier-up replacement (see Selling towers), then targeted
   upgrades / defensive buildings.
1. **Buy tile (expansion)** — when fewer than 2 owned tiles still cover the
   path, buy the best-covering purchasable tile so tower placement never
   stalls for lack of land. Defense growth always includes buying tiles.
2. **Place tower** — desired tower on the best-covering owned tile; a
   purchasable tile is bought first instead when its coverage beats the best
   owned spot by >1.3×.
3. **Save** — desired tower/tile unaffordable → declare a [savings goal](baseline.md)
   (`memory.savings_goal`); other spenders then leave the gold untouched until
   the goal is bought or expires.
3b. **Tier-up replacement** — quality mode (path ≥ 28): replace the weakest
   placed tower with a clearly stronger researched one (see Selling towers).
4. **Targeted upgrade** — with a gold buffer (> 500 spendable), upgrade the
   placed tower that best covers the weak segments: `range` if it barely reaches
   the path, otherwise `damage`. Stats at the server cap (level 20, read from
   `summary.item_upgrades`) are skipped; fully upgraded towers are passed over.
5. **Defensive buildings** — fallback: queue a building with defensive effects
   (`siege_offset`, `wave_delay_offset`, `max_life_modifier`,
   `life_regen_modifier`, `restore_life_after_loss_offset`).

## Success criteria

No terminal goal — runs until expiry. Effectiveness shows up as fewer
`🏰 Reached` breaches and shrinking weak segments in subsequent replays.

## Baseline obligations

Like every strategy, this one is subject to the [baseline obligations](baseline.md):
defense is never neglected (breach response plus an era-scaled minimum tower
count — tiles are bought and towers built in every strategy), idle time on
building and research is minimized (empty queues are filled with the cheapest
affordable item each cycle), and active savings goals are respected.
