# Defense Strategy

> **Implementation:** `ai_players/bot/planners/defense_frontier.py` —
> `FrontierDefensePlanner.propose_options()`.
> Analysis/geometry: `bot/defense_analysis.py` (`corridor_from_map`,
> `end_state`, `bfs_path`, `coverage_score`, `pick_tower`); saving:
> `bot/savings.py`. The admin/dev maze-sim tool (`web/tools/maze-sim.html`) no
> longer runs this code — it is backed by a separate, gameserver-native port at
> `python_server/src/gameserver/engine/maze_generator.py`, which is not the spec
> for this file and does not need to stay in sync with it.
> Duration: `config.yaml`; forced switch: `bot/strategy.py::breach_defense_strategy`;
> season opening: `bot/strategy.py::season_start_defense_strategy`.
> This file is the spec — when the planner changes, update it (and vice versa).

**Goal:** Make the own hex map harder to break through by growing a single
walkable corridor (spawn → castle) that is walled with towers on both sides,
instead of filling the whole owned field.

Defense is never chosen by `roll_strategy()`'s weighted roll (that only ever
picks between [attack](attack.md) and [growth](growth.md)). It is reached two
other ways, per the rules in `bot-flow.md`'s Strategy System section.

**As the season opening (rule 0):** a bot with no active strategy — brand new,
or just wiped by a season reset — always starts here for 3–8 hours
(`strategy.py::season_start_defense_strategy`), so every bot enters a season
building its maze before it considers raiding. The win streak starts at 0, so
the normal way out is rule 2; if nobody attacks the bot during that window it
expires into the usual attack/growth roll instead.

**Reactively (rule 1):** a **fully lost** defense (the whole battle, not just
a partial breach) immediately force-switches to this strategy for 3–8 hours
(`strategy.py::breach_defense_strategy`) and resets the win streak to 0;
winning `DEFENSE_WIN_STREAK_TARGET` (3) defenses in a row is the only way
back out. A brief 5-minute defense placeholder is also used by
`roll_strategy()` when no attackable target exists and growth has zero
weight. The always-on baseline minimum-tower-floor and one-off
breach-response action (below) run regardless of the active strategy —
except while [growth](growth.md) is active, which suspends both.

## State: the live map, nothing else

**The planner persists no coordinates.** Every position is re-derived each
cycle from `GET /api/map` (`defense_analysis.corridor_from_map`) — the way a
human player reads the board before deciding what to buy. The only things kept
in memory are position-independent: `maze_seed` (per-bot RNG identity),
`maze_step` (counter) and `upgrade_focus`.

This is deliberate. The corridor used to live in `memory.frontier`, which
silently diverged from the server on all three production bots: they spent a
week planning purchases around a phantom location 15-20 hexes from their real
castle, every action failing, while gold piled up. Deriving from the map makes
that failure mode impossible rather than merely unlikely.

Two derived values replace the old stored geometry:

- **`corridor_set`** — every committed corridor tile, from tile TYPE
  (`spawnpoint`/`path`/`castle`). Type-derived rather than route-derived so the
  flood-safety rule stays complete even while the route transiently cuts
  through a bought-but-untowered side tile.
- **`corridor`** — the ordered route, taken from the server's own `path` field
  (the route `battle_service` actually walks) and falling back to
  `defense_analysis.bfs_path` when a caller's map response has none (e.g. a
  test fixture). `corridor[0]` is the spawn and `corridor[-1]` the castle by
  construction.

The invariant that makes this work: **after every completed action the map
alone describes the maze.** Corridor tiles are always `spawnpoint`/`path`/
`castle`, so an `empty` tile always means "tower spot" (or the debris of an
interrupted grow, see action 2). That is why growing is atomic — see action 6.

If spawn and castle exist but nothing connects them, the corridor actions are
skipped entirely and a deduplicated warning is logged; towers and upgrades
continue so gold still gets spent usefully.

## Corridor growth

A candidate tile for growth must be void and must touch the existing corridor
at **exactly one** tile (`_touches_once`/`_candidate_ok`) — this flood-safety
rule guarantees the corridor never shortcuts itself into a loop. Tiles a
neighboring empire owns are filtered out up front via `ctx.foreign_tiles`
(from `GET /api/map/neighbors`, the fog-range view the map screen shows).

The serpentine state is re-derived from the corridor's own shape each cycle
(`defense_analysis.end_state`): the heading prefers to go straight for
`SEG_LEN = 5` steps, then prefers a U-turn, turning alternately left/right
(`turn_dir` flips after two turns in a row). Note `seg_steps` is a run length
(1 right after a turn), so a U-turn comes one tile earlier than with the old
persisted counter. Growth stops once `corridor_set` reaches
`MAX_CORRIDOR = 60` tiles.

Requires `HUNTING` (the first tower unlock) to be researched — without any
buildable tower, growing the corridor would just buy undefended land.

## Coverage scoring

`defense_analysis.coverage_score`/`path_points` score candidate tiles by the
weighted number of interpolated path points within a tower's range (continuous
hex distance, matching the server's targeting math). Used both to pick the
best stray tile for an immediate tower and to rank flank/side tile candidates.

## Tower mix

Towers are classified by effects: `slow`, `splash`, or `damage` (burn counts as
damage). The placed mix is steered toward **damage : slow : splash ≈ 3 : 1 : 1**
(`defense_analysis.pick_tower`); the planner picks the best unlocked tower of
the most under-represented class by `damage / reload_time × (1 + range/4)`
(`tower_quality`).

## Actions (in priority order, one per cycle)

1. **Tower an empty tile** — every owned empty tile is a tower spot and is
   towered immediately (closes shortcut risk). Uses `pick_tower` +
   `coverage_score` to choose tower type and spot.
2. **Repair an interrupted grow** — an owned `empty` tile hanging off an
   anchor and touching the corridor exactly once can only be a bought corridor
   step whose relocation half did not land; the anchor moves onto it for free
   (`_repair_option`). An ordinary tower spot is never adopted: it either
   isn't adjacent to an anchor or touches the corridor more than once.
3. **Era-swap** — replace the oldest-era placed tower with the best current-era
   tower (sell + rebuild in one `save_map`), oldest/weakest first, only when
   the new tower's quality gain is positive and `net_cost = new_cost −
   refund × old_cost` is affordable. Done before upgrades/growth so gold is
   never spent bringing an outdated tower up to date.
4. **Flank** — every corridor tile except the two live ends must have all its
   non-corridor neighbors owned, so it ends up flanked by towers on both
   sides; missing neighbors are bought one at a time (`_flank_option`).
5. **Grow the corridor** — buy the next void tile at an end **and move the
   anchor onto it in the same action** (`buy_tile` then `save_map`). Both
   halves belong together: a bought-but-unconnected tile is maze state the map
   cannot express (it looks exactly like a tower spot), and remembering it is
   what used to drift. Both ends are proposed every cycle; which one is
   offered first alternates with the owned-tile parity, so callers that run
   only the single best option (`Planner.propose`, the maze-sim) still grow
   both ends. If the buy succeeds but the `save_map` fails, the tile is left
   as `empty` and is finished by action 2 or towered by action 1 — never a
   phantom.
6. **Buy a side tile** — buy the best-scoring purchasable void tile adjacent
   to the corridor for a future tower, when nothing else applies.
7. **Workshop upgrade** — absolute last priority (`PRIO_UPGRADE`), only
   proposed once nothing above is available/affordable this cycle. Targets
   the most-placed tower type on the map (`_most_common_placed_tower()`).
   Commits to **one** randomly-picked stat per tower type at a time
   (`_focus_upgrade_stat()`, remembered in `memory["upgrade_focus"]`) instead
   of always maxing the same stat first — once that stat hits its cap it
   rotates to a different one. Cap is `3 × (era_rank + 1)` of the tower's own
   era (`_max_upgrade_level()`), so later-era towers allow deeper investment.

Foreign land is normally skipped before it is ever proposed (`foreign_tiles`,
above). Should a `buy_tile` still be rejected — the fog view is unavailable, or
a neighbor claimed the tile in between — it is excluded only for the rest of
the current tick (`bot/dispatch.py`'s per-tick exclude set, keyed by option
description) and retried fresh next cycle. Nothing is blacklisted permanently:
nearby ownership changes over a season, and a permanent list would eventually
wall the bot in on data that no longer holds.

Every `save_map` payload is rebuilt from a fresh `GET /api/map` inside the
action, because the endpoint replaces the whole map — posting a snapshot taken
at the start of the cycle would delete tiles bought earlier in the same tick.

Weighted-random selection (`weighted_top_n`, seeded from
`memory.maze_seed` + `memory.maze_step`) is used across ties (tower spot,
flank tile, grow direction, side tile) so different bots build visibly
different mazes while staying reproducible and testable.

## Success criteria

No terminal goal — runs until expiry. Effectiveness shows up as fewer
`🏰 Reached` breaches in subsequent battle reports.

## Baseline obligations

Like attack and growth, this strategy is subject to the
[baseline obligations](baseline.md): defense is never neglected (breach
response plus an era-scaled minimum tower count — except while
[growth](growth.md) is active, which suspends both), idle time on building
and research is minimized (empty queues are filled with the cheapest
affordable item each cycle), and active savings goals are respected.
