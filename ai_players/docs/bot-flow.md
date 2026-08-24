# Bot Flow

This document is the **source of truth** for the bot's runtime behavior.
When the flow changes, update this file first — the implementation follows.

---

## Overview

Each bot runs as a long-lived process (spawned by `fleet.py`). Once per minute it
executes a complete **tick**: login, act, discard token, sleep. The bot never stays
logged in between ticks — the login at the start of each tick recreates a wiped
empire automatically (server-side behavior in `auth.py`).

Multiple bots run in parallel; each has its own state file (`states/<name>.yaml`)
and a unique control port for runtime overrides.

---

## Tick Structure

```
┌─────────────────────────────────────────────────────┐
│  Every cycle_interval_s seconds (default: 60)        │
│                                                     │
│  1. LOGIN          POST /api/auth/login             │
│  2. CYCLE          fetch data + execute actions     │
│  3. SAVE STATE     write states/<name>.yaml         │
│  4. LOGOUT         set api.token = None             │
│  5. SLEEP          wait until next tick             │
└─────────────────────────────────────────────────────┘
```

### Step 1 — Login

`api.login()` fetches a fresh JWT token. If the empire was wiped (season reset),
the server's login handler automatically creates a new empire for the account.
No special handling needed in the bot.

If login fails (server down, network error), the tick is skipped and the bot
sleeps until the next tick.

### Step 2 — Cycle (`cycle()` in `run_bot.py`)

The cycle runs in two phases:

**Phase A — One-time setup (runs once per tick):**

1. `GET /api/empire/summary` — current empire state, resources, era
2. `GET /api/empire/items` — available items catalog (always fresh; no cache)
3. Drain control port commands (strategy overrides, rerolls)
4. `GET /api/messages` → process battle reports into memory
   - Defense fully lost → force-switch to `defense`, unconditionally, resets
     the win streak
   - Defense won → increment the win streak; at `DEFENSE_WIN_STREAK_TARGET`
     (3) consecutive wins, roll a new strategy (attack/growth)
5. Strategy expiry check → in practice only ever fires for the short-lived
   `no_targets` placeholder; attack/growth hold indefinitely (`NO_EXPIRY`)

**Phase B — Action loop (up to `MAX_ACTIONS_PER_TICK = 20` iterations):**

```
loop:
    GET /api/empire/summary    ← refresh gold after each action
    ctx = BotContext(summary, items, memory, strategy)
    action = choose_action(ctx)
    if action is None → break  ← nothing affordable
    action.run(api)
    if action failed → break   ← avoid tight retry loop
```

The loop exits when no affordable action exists or the iteration limit is reached.

### Step 3 — Save State

`BotState` is written to `states/<name>.yaml` (atomic via temp file + rename).
Saved fields: account credentials, personality, active strategy, memory, runtime counters.

### Step 4 — Logout

`api.token = None` — the token is simply discarded. No server call needed (JWT
is stateless). The next tick starts unauthenticated and calls `login()` again.

### Step 5 — Sleep

`sleep(max(0, tick_start + interval - now))` — if the cycle took longer than
`cycle_interval_s`, sleep is skipped and the next tick starts immediately.

---

## Action Selection

Each tick, `choose_action()` (in `bot/dispatch.py`) is called repeatedly (up
to `MAX_ACTIONS_PER_TICK`) so a single tick can run several actions, not just
one. Dispatch is **strict priority order** — no ROI/personality scoring:

1. **Free options (price ≤ 0) always run first**, in priority order — they
   never compete with or get excluded by priced options.
2. **Priced options** are then checked highest-priority first. An unaffordable
   one is skipped (not blocking); every remaining priority is still checked
   and run if affordable this tick.
3. **Nothing affordable at all** → the tick ends and waits for the next one.

Options are gathered from, in no particular precedence (priority numbers
decide, not source):

- **Baseline obligations** (`bot/planners/baseline.py`): breach response,
  tower floor maintenance, ruler claim, research/build queue filling
- **Active strategy planner** (`bot/planners/<strategy>.py`)
- **Attack's free actions** — spy/attack calls and wave-fill with an
  already-unlocked critter cost no gold, so they always run regardless of the
  active strategy (`bot/dispatch.py::gather_options`), not just while attack
  is active. The one exception is `growth` (see `growth.md`): while it's
  active, nothing runs except baseline — not even attack's free actions.
  There is no more "secondary strategy" concept; this replaced it.

A server-rejected option (e.g. unmet requirements) is excluded for the rest
of that tick only, so it can't loop forever, but every other priority —
including lower ones — still gets tried (`run_bot.py`'s `failed_this_tick`).

Savings goals are simplified accordingly: the highest-priority option that is
NOT yet affordable (and asks to save via `saves_for`/`goal_meta`) reserves its
gold for every lower-priority option this cycle (`bot/savings.py`) — there is
no more "only save when everything else is filler" special case.

---

## Strategy System

A strategy is a dict `{type, valid_until, params, completed}`.

**Types:** `defense`, `attack`, `growth`

**One opening rule and two running rules govern strategy, nothing else** (see
`bot/strategy.py` and `run_bot.py`):

0. **A bot with no active strategy opens on `defense`**
   (`strategy.py::season_start_defense_strategy`). That covers a brand-new bot
   on its first tick and a bot whose state was just wiped by a season reset —
   bots always enter a season building their maze, never raiding. It uses the
   same 3–8 h window as a breach-forced defense rather than `NO_EXPIRY`, so a
   bot nobody attacks in the opening (no defense wins to accumulate, so rule 2
   can never fire) moves on to attack/growth instead of parking on defense.
1. **A fully lost defense immediately (and unconditionally) switches to
   `defense`** — this always wins, overriding whatever was active before
   (attack, growth, or an in-progress win streak). Resets the win streak to 0.
   A battle where some critters reached the castle but the defender still WON
   is not a loss here — only a complete defeat triggers this; partial
   breaches get the lighter one-off "breach response" action instead.
2. **Winning `DEFENSE_WIN_STREAK_TARGET` (3) defenses in a row is the ONLY
   way out of `defense`**: it rolls a new strategy via `roll_strategy()` —
   weighted-random between `attack` and `growth` (`config.yaml`
   `strategy.weights`, scaled by personality). `defense` itself is never
   rolled this way. Attack is excluded from the roll when no attackable
   target exists. The result holds indefinitely (`NO_EXPIRY`) until the next
   lost defense resets the streak.

There is no revenge-attack-on-defeat mechanism and no wall-clock strategy
rotation. Manual override via control port: `{"cmd": "strategy", "payload": {...}}`.

Strategy is persisted in `states/<name>.yaml` so it survives restarts.

---

## State Persistence

File: `states/<name>.yaml`

| Field | Contents |
|---|---|
| `account` | username, password, empire_name, uid |
| `personality` | one of: aggressive, defensive, balanced (rolled once) |
| `strategy` | active strategy dict (type, valid_until, params, completed) |
| `memory` | battle history, opponent scores, breach flags, savings goals |
| `runtime` | cycle counter, last_cycle timestamp |

State **is** reset between seasons: `run_bot.py::_check_season_reset` compares
`summary.season_number` against `memory.last_season` and calls `BotState.reset()`
on a change, clearing `strategy`, `memory` and `runtime` (account and personality
are kept) and wiping the log files. The bot then opens the new season on defense
via rule 0. The empire itself is recreated on the next login.

---

## Configuration (`config.yaml`)

| Key | Default | Description |
|---|---|---|
| `server_url` | `http://localhost:8180` | Gameserver API endpoint |
| `cycle_interval_s` | `60` | Seconds between tick starts |
| `control_port_base` | `9300` | Base port; each bot gets base + offset |
| `strategy.weights` | — | Weights for the post-win-streak attack/growth roll (`defense`'s weight in this table is unused — `defense` is never rolled, only forced on a lost battle) |
| `strategy.duration_hours` | — | Only `defense`'s range is used (`breach_defense_strategy` and `season_start_defense_strategy`); attack/growth hold indefinitely instead |
| `personalities` | — | Per-personality strategy weight multipliers |
| `selection.top_n` | `3` | Weighted sampling among *equally viable* candidates within a single planner step (e.g. which tile/target) — not used for cross-planner option ranking |
| `category_weights` | — | **Unused** — dispatch is strict priority order (see "Action Selection"), no personality-weighted option scoring |
| `active_strategy_boost` | `1.5` | **Unused**, same reason |

**`--fast` flag:** sets `cycle_interval_s = 5` for local testing.

---

## Edge Cases

| Situation | Behavior |
|---|---|
| Empire wiped (season reset) | Login recreates empire; bot continues normally next tick |
| Server down at login | Exception caught, tick skipped, bot sleeps until next tick |
| Cycle takes > `cycle_interval_s` | `max(0, ...)` → sleep = 0, next tick starts immediately |
| No affordable action | Loop exits at first iteration, bot sleeps rest of interval |
| Action fails (API error) | Logged as warning, description excluded for the rest of this tick (`failed_this_tick`); every other priority — including lower ones — is still tried |
| Loop hits MAX_ACTIONS (20) | Tick ends normally — indicates unusually many cheap actions |
| Bot receives SIGTERM | `stop["flag"] = True`, current tick finishes, state saved, exit |
