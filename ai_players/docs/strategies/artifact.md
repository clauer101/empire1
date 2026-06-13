# Artifact Strategy

> **Implementation:** `ai_players/bot/planners/artifact.py` — `ArtifactPlanner`,
> a subclass of `AttackPlanner` overriding only `_goal_reached()` (checks
> `history_entry["artifacts"]`). Target scoring incl. artifact weighting:
> `bot/analyzer.py::score_targets`. Weights/durations: `config.yaml`.
> This file is the spec — when the planner changes, update it (and vice versa).

**Goal:** Steal at least one artifact from another empire.

Default weight: 1 (rarest roll). Duration: 1–3 hours. Like attack, weight is 0 without an army. Target scoring weights the opponents' `artifact_count` heavily — there is no point raiding an empire without artifacts.

## How it works

Identical phase machine to the [attack strategy](attack.md) (`spy → wait_spy → attack → wait_result`), implemented as a subclass of `AttackPlanner`. Only the success criterion differs.

Artifact theft chance in the game: ~30 % on victory, ~4 % on defeat (power-scaled), so multiple attempts against the same target may be needed.

## Success / termination criteria

- **Artifact looted** (`⚜ … acquired` in the battle report) → goal reached, strategy completed.
- **Victory without artifact** → attack the same target again (phase resets to `attack`).
- **Defeat** → give up, strategy completed, re-roll.
- **Expiry** → re-roll.

## Baseline obligations

Like every strategy, this one is subject to the [baseline obligations](baseline.md):
defense is never neglected (breach response plus an era-scaled minimum tower
count — tiles are bought and towers built in every strategy), idle time on
building and research is minimized (empty queues are filled with the cheapest
affordable item each cycle), and active savings goals are respected.
