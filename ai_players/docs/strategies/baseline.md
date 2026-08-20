# Baseline Obligations (all strategies)

> **Implementation:** `ai_players/bot/planners/baseline.py` — `baseline_action()`,
> called in `run_bot.py` before the strategy planner each cycle
> (`action = baseline_action(ctx) or planner.propose(ctx)`). The breach trigger
> (`memory.pending_breach`) is set in `bot/analyzer.py::process_new_reports`.
> Savings goals: `bot/savings.py` (`set_goal`/`get_goal`/`spendable_gold`),
> enforced via `BotContext.spendable_gold` and the `respect_savings` default of
> `cheapest_affordable` in `bot/planners/base.py`.
> This file is the spec — when the baseline changes, update it (and vice versa).

Three obligations hold regardless of the active strategy, with one exception:
obligation 1 is entirely suspended while [growth](growth.md) is active (a
deliberate "invest in nothing" strategy).

## 1. Defense must never be neglected

Two triggers, active in every strategy **except** [growth](growth.md), which
suspends both as a deliberate "invest in nothing" strategy:

- **Breach response** — whenever a defensive battle report shows a breach
  (`🏰 Reached > 0`), the next cycle takes one defensive action (tower
  placement / tile purchase / upgrade — same logic as the
  [defense strategy](defense.md)) before any strategy-specific action. This
  fires even when the defender still won the battle overall.
- A **fully lost** defense (the whole battle, not just a partial breach) goes
  further and **unconditionally forces a full strategy switch to defense**
  (`run_bot.py`, `strategy.py::breach_defense_strategy`, source `breach`) for
  3–8 hours, resetting the defense-win-streak to 0 — the only way out is
  winning `DEFENSE_WIN_STREAK_TARGET` (3) defenses in a row (see
  `bot-flow.md`'s Strategy System section), not just taking the one-off
  action above.
- **Tower floor** — a minimum number of placed towers is maintained at all
  times so AI waves always meet an adequate defense:
  `min_towers = 2 + 2 × era_rank` (stone = 2, iron = 8, …). Placed towers are
  counted from the map tiles (`summary.structures` is only synced during
  battles). Defensive actions taken here include the full defense toolkit:
  spawn/castle relocation to lengthen the critter path, tile purchases,
  tower placement, and targeted upgrades. While below the
  floor, each cycle runs one defensive action — buying tiles and building
  towers even under the attack strategy. Tiles are bought whenever fewer
  than 2 owned tiles still cover the path, so territory expands along with
  the tower count. If the needed tower/tile is
  unaffordable, the defense logic declares a savings goal (obligation 3),
  which protects the gold from queue filling until the purchase is possible.
  Suspended entirely while [growth](growth.md) is active — see there.

## 2. Minimize idle time on building and research

An empty research or build queue is dead progress. Before strategy-specific
actions, the baseline fills an empty research queue and build queue itself,
preferring items with an economic effect (`_has_econ_effect`/`ECON_EFFECTS`
in `baseline.py`) over plain filler at the same price — the baseline only
guarantees the queues never sit idle while something is affordable.

Research selection, in priority order, once the queue is empty:

1. **Resume a paused item** — only if it is still unlocked (its remaining
   requirement may itself be unresearched; resuming an item whose
   requirements aren't met would fail every cycle with no fallback).
2. **Missing tower-unlock requirement** — the oldest not-yet-unlocked tower of
   the empire's own era may need more than its era-defining knowledge (e.g.
   `ARBELESTE_TOWER` needs `FORGE` + `IRON`, not just `IRON`); its first
   missing knowledge requirement is forced next so the maze doesn't get stuck
   defending with an older, weaker tower.
3. **Missing "main" branch tech** — every knowledge item has a `branch`
   (`main` | `left` | `right`; unset defaults to `main`). Main-branch techs
   are the required backbone (e.g. `TRIBAL_LEADERSHIP`, which gates the ruler
   system) and must all eventually get researched; left/right techs are
   optional side branches. Without this step, an advanced empire almost
   always has *some* unresearched current-era tech, so a left-behind
   main-branch tech from an earlier era would never get picked — the
   current-era preference in step 4 never falls back to older eras while the
   current era still has anything left to research. This step forces the
   oldest (lowest-era) not-yet-started, currently-unlockable main-branch tech.
4. **Random pool** — otherwise, prefer unlocked techs from the current era
   (falling back to any unlocked tech if none remain), then prefer
   economy-effect techs within that pool, then pick randomly. Left/right
   branch techs only ever get chosen here — they may or may not ever be
   researched, by design.

## 3. Respect savings goals

Strategies can save toward an expensive purchase (no permanent reserve — only
when a planner names a concrete item, e.g. defense saving for a high-coverage
tower, attack saving for an army). While `memory.savings_goal` is active:

- **Non-owning spenders** (baseline queue filling, other planner steps) may only
  spend gold *above* the goal amount (`spendable_gold = max(0, gold − amount)`).
  Queues may therefore stay idle while saving — saving outranks obligation 2.
- **Bootstrap exception:** if the empire has zero passive gold income
  (`base_gold <= 0`), no savings goal is declared at all this cycle
  (`bot/dispatch.py::choose_action`) — every option is evaluated at face
  value instead. Without any income a savings goal can never be reached on
  its own (e.g. attack's army goal on a fresh empire with no buildings), so a
  lower-priority unaffordable option (the goal owner) must not starve a
  higher-priority option that's affordable right now (typically a baseline
  econ building) — that building is exactly what turns income positive and
  lets the normal savings-goal cap resume next cycle. Also mirrored in
  `baseline.py`'s own build-queue candidate selection for consistency when
  `baseline_options` is inspected directly (e.g. in tests).
- The **owning planner** (same strategy type) bypasses the cap and clears the
  goal after the purchase.
- Goals auto-expire: TTL = min(strategy remainder, 2 h), and any strategy-type
  change drops the goal — bots never deadlock on saving.
