# Baseline Obligations (all strategies)

> **Implementation:** `ai_players/bot/planners/baseline.py` — `baseline_action()`,
> called in `run_bot.py` before the strategy planner each cycle
> (`action = baseline_action(ctx) or planner.propose(ctx)`). The breach trigger
> (`memory.pending_breach`) is set in `bot/analyzer.py::process_new_reports`.
> Savings goals: `bot/savings.py` (`set_goal`/`get_goal`/`spendable_gold`),
> enforced via `BotContext.spendable_gold` and the `respect_savings` default of
> `cheapest_affordable` in `bot/planners/base.py`.
> This file is the spec — when the baseline changes, update it (and vice versa).

Three obligations hold **regardless of the active strategy**:

## 1. Defense must never be neglected

Two triggers, both active in **every** strategy (economy, attack, artifact too):

- **Breach response** — whenever a defensive battle report shows a breach
  (`🏰 Reached > 0`), the next cycle takes one defensive action (tower
  placement / tile purchase / upgrade — same logic as the
  [defense strategy](defense.md)) before any strategy-specific action.
  In addition, the breach **forces a strategy switch to defense**
  (`run_bot.py` step 2b, `strategy.py::breach_defense_strategy`, source
  `breach`) — the bot then spends a full defense-strategy period
  strengthening the perimeter, regardless of what it was doing before.
- **Tower floor** — a minimum number of placed towers is maintained at all
  times so AI waves always meet an adequate defense:
  `min_towers = 2 + 2 × era_rank` (stone = 2, iron = 8, …). Placed towers are
  counted from the map tiles (`summary.structures` is only synced during
  battles). Defensive actions taken here include the full defense toolkit:
  spawn/castle relocation to lengthen the critter path, tile purchases,
  tower placement, and targeted upgrades. While below the
  floor, each cycle runs one defensive action — buying tiles and building
  towers even under the economy strategy. Tiles are bought whenever fewer
  than 2 owned tiles still cover the path, so territory expands along with
  the tower count. If the needed tower/tile is
  unaffordable, the defense logic declares a savings goal (obligation 3),
  which protects the gold from queue filling until the purchase is possible.

## 2. Minimize idle time on building and research

An empty research or build queue is dead progress. Before strategy-specific
actions, the baseline fills an empty research queue with the cheapest affordable
knowledge and an empty build queue with the cheapest affordable building.
Strategy planners may still pick *better* items (e.g. economy prefers
economy-effect items) — the baseline only guarantees the queues never sit idle
while something is affordable.

## 3. Respect savings goals

Strategies can save toward an expensive purchase (no permanent reserve — only
when a planner names a concrete item, e.g. defense saving for a high-coverage
tower, attack saving for an army). While `memory.savings_goal` is active:

- **Non-owning spenders** (baseline queue filling, other planner steps) may only
  spend gold *above* the goal amount (`spendable_gold = max(0, gold − amount)`).
  Queues may therefore stay idle while saving — saving outranks obligation 2.
- The **owning planner** (same strategy type) bypasses the cap and clears the
  goal after the purchase.
- Goals auto-expire: TTL = min(strategy remainder, 2 h), and any strategy-type
  change drops the goal — bots never deadlock on saving.
