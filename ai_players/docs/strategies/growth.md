# Growth Strategy

> **Implementation:** `ai_players/bot/planners/growth.py` — `GrowthPlanner`.
> Reached via `bot/strategy.py::roll_strategy()`, only ever called from
> `run_bot.py`'s defense-win-streak handling (see below).
> This file is the spec — when growth changes, update it (and vice versa).

## What it does

Nothing. `GrowthPlanner.propose_options()` always returns an empty list —
no army spend, no maze upkeep. Growth means "invest in neither attack nor
defense, not even for free": gold is left for [baseline](baseline.md)'s
unconditional research/building/citizen spend only.

Three things are switched off while growth is active:

- **Attack's free background actions** — spy/attack calls and wave-fill with
  an already-unlocked critter normally run regardless of which strategy is
  active, since they cost no gold (`bot/dispatch.py::gather_options`).
  Growth is the one exception: `gather_options` skips the attack planner
  entirely while growth is active.
- **Breach response** — normally one defensive action fires the cycle after
  a partial breach; suppressed during growth (the flag is still cleared so
  it doesn't fire retroactively once growth ends).
- **Tower floor** — normally a minimum tower count
  (`2 + 2 × era_rank`) is maintained at all times; suppressed during growth.

A **fully lost** defense still force-switches the strategy to `defense`
unconditionally (`run_bot.py`, same as during attack) — growth does not
protect against that, it only stops proactive spend.

## Reaching growth

Growth never expires on a wall-clock timer (`valid_until: NO_EXPIRY`). It is
reached only via the **defense-win-streak** mechanism in `run_bot.py` — the
only two rules that govern strategy at all (see `bot-flow.md`):

- A fully lost defense immediately (and unconditionally) switches to
  `defense` and resets `memory.defense_win_streak` to 0.
- Winning a defensive battle increments the streak. Once it reaches
  `DEFENSE_WIN_STREAK_TARGET` (3), `roll_strategy()` picks a new strategy —
  weighted-random between [attack](attack.md) and growth (`config.yaml`
  `strategy.weights`, scaled by personality). Attack is excluded from that
  roll when no attackable target exists, in which case growth is the only
  candidate left (or, if growth also has zero weight, a short-lived
  `defense` placeholder).
- The choice holds until the next fully lost defense, which resets the
  streak and forces `defense` again.

## Why growth suppresses attack's free actions

Attack's spy/attack/wave-fill actions normally run in the background no
matter which strategy is active, because they're free — see
`bot/dispatch.py::gather_options`. Growth is the sole exception: it means
"invest in nothing," and letting a free attack continue in the background
would defeat that.
