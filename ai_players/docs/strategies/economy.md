# Economy Strategy

> **Implementation:** `ai_players/bot/planners/economy.py` — `EconomyPlanner.propose()`.
> The numbered objectives below map 1:1 to the numbered steps in `propose()`;
> economy-effect keys are the `ECON_EFFECTS` tuple. Weights/durations come from
> `config.yaml` (`strategy.weights.economy`, `strategy.duration_hours.economy`),
> context modulation from `bot/strategy.py::roll_strategy`.
> This file is the spec — when the planner changes, update it (and vice versa).

**Goal:** Maximize long-term resource and research output so all other strategies become affordable later.

Default weight: 4 (most likely roll). Duration: 4–10 hours. Weight is doubled when gold drops below 200.

## Objectives (in priority order)

1. **Keep the research queue busy** — queue the cheapest affordable knowledge, preferring items with economy effects (`gold_modifier`, `culture_modifier`, `research_speed_*`, `build_speed_modifier`, `citizen_effect_modifier`, …).
2. **Keep the build queue busy** — same selection logic for buildings.
3. **Grow the population** — buy a citizen whenever culture comfortably covers the price (≥ 120 % of cost), then rebalance to roughly 40 % merchants / 40 % scientists / 20 % artists.
4. **Develop the ruler** — choose a random ruler once unlocked; spend any unspent skill points on a random skill (q/w/e/r).

## Success criteria

The strategy has no terminal goal — it runs until its time validity expires, then a new strategy is rolled. A healthy economy phase shows continuously non-empty queues and growing citizen count in the bot log.

## Baseline obligations

Like every strategy, this one is subject to the [baseline obligations](baseline.md):
defense is never neglected (breach response plus an era-scaled minimum tower
count — tiles are bought and towers built in every strategy), idle time on
building and research is minimized (empty queues are filled with the cheapest
affordable item each cycle), and active savings goals are respected.
