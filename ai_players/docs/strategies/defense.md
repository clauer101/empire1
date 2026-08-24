# Defense Strategy

> **Implementation:** `ai_players/bot/planners/defense_frontier.py` —
> `FrontierDefensePlanner.propose_options()`.
> Analysis/geometry: `bot/defense_analysis.py` (`bfs_path`, `coverage_score`,
> `pick_tower`); saving: `bot/savings.py`; maze-sim: `bot/sim.py::SimApi`.
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

## Corridor growth

The map state is `memory.frontier.corridor`: an ordered list of tile keys from
the spawn end (`corridor[0]`) to the castle end (`corridor[-1]`). Each end
keeps its own serpentine state (`heading`, `turn_dir`, `seg_steps`,
`turns_in_row`) under `memory.frontier.ends`. Growth alternates between the two
ends every cycle (`memory.frontier.next_end`).

A candidate tile for growth must be void and must touch the existing corridor
at **exactly one** tile (`_candidate_ok`) — this flood-safety rule guarantees
the corridor never shortcuts itself into a loop. The heading prefers to go
straight for `SEG_LEN = 5` steps, then prefers a U-turn (serpentine), turning
alternately left/right (`turn_dir` flips after two turns in a row). Growth
stops once the corridor reaches `MAX_CORRIDOR = 60` tiles.

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

1. **Tower a stray tile** — any owned empty tile outside the corridor is
   towered immediately (closes shortcut risk). Uses `pick_tower` +
   `coverage_score` to choose tower type and spot.
2. **Relocate spawn** — if the spawnpoint is not on `corridor[0]`, move it
   there for free (extends the live path immediately).
3. **Relocate castle** — mirror of the above for `corridor[-1]`, once the
   corridor has two distinct ends.
4. **Era-swap** — replace the oldest-era placed tower with the best current-era
   tower (sell + rebuild in one `save_map`), oldest/weakest first, only when
   the new tower's quality gain is positive and `net_cost = new_cost −
   refund × old_cost` is affordable. Done before upgrades/growth so gold is
   never spent bringing an outdated tower up to date.
5. **Flank** — every corridor tile except the two live ends must have all its
   non-corridor neighbors owned, so it ends up flanked by towers on both
   sides; missing neighbors are bought one at a time (`_flank_option`).
6. **Grow the corridor** — buy the next void tile at whichever end is due
   next (serpentine heading, turning when blocked); alternates spawn/castle
   end every cycle.
7. **Buy a side tile** — buy the best-scoring purchasable void tile adjacent
   to the corridor for a future tower, when nothing else applies.
8. **Workshop upgrade** — absolute last priority (`PRIO_UPGRADE`), only
   proposed once nothing above is available/affordable this cycle. Targets
   the most-placed tower type on the map (`_most_common_placed_tower()`).
   Commits to **one** randomly-picked stat per tower type at a time
   (`_focus_upgrade_stat()`, remembered in `memory["upgrade_focus"]`) instead
   of always maxing the same stat first — once that stat hits its cap it
   rotates to a different one. Cap is `3 × (era_rank + 1)` of the tower's own
   era (`_max_upgrade_level()`), so later-era towers allow deeper investment.

Blocked tiles (a `buy_tile` call that failed because another empire already
owns the tile) are remembered in `memory.frontier.blocked_tiles` so they are
never retried.

Weighted-random selection (`weighted_top_n`, seeded from
`memory.maze_seed` + a per-cycle step) is used across ties (tower spot,
flank tile, grow direction, side tile) so different bots build visibly
different mazes while staying reproducible and testable in the maze-sim tool
(`bot/sim.py`).

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
