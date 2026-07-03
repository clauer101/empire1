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
   - Breach detected → force-switch to defense strategy (personality-gated)
   - Lost attack detected → mark for revenge; may force-switch to attack strategy
5. Strategy expiry check → if expired or completed, roll a new strategy

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

Each tick, `choose_action()` (in `bot/dispatch.py`) selects the best action from:

- **Baseline obligations** (`bot/planners/baseline.py`): always evaluated first
  - Breach response (mandatory if `memory["pending_breach"]` is set)
  - Tower floor maintenance (minimum towers per era: `2 + 2 × era_rank`)
  - Ruler claim (free, when unlocked and no ruler equipped)
  - Queue filling (cheapest research + build, filler priority)
- **Active strategy planner** (`bot/planners/<strategy>.py`)
- **Secondary strategy planner** (weighted random, for diversity)

Options are scored as `gain / price × personality_weight × category_weight`.
The top-N are sampled probabilistically so different bots make different choices.

---

## Strategy System

A strategy is a dict `{type, valid_until, params, completed}`.

**Types:** `economy`, `defense`, `attack`, `artifact`

**Lifecycle:**
- Rolled at startup and whenever the current strategy expires or is marked completed
- Duration from `config.yaml strategy.duration_hours.<type>` (random range)
- Force-switches: breach → defense; lost attack → attack (both personality-gated)
- Manual override via control port: `{"cmd": "strategy", "payload": {...}}`

Strategy is persisted in `states/<name>.yaml` so it survives restarts.

---

## State Persistence

File: `states/<name>.yaml`

| Field | Contents |
|---|---|
| `account` | username, password, empire_name, uid |
| `personality` | one of: economy, aggressive, defensive, balanced (rolled once) |
| `strategy` | active strategy dict (type, valid_until, params, completed) |
| `memory` | battle history, opponent scores, breach flags, savings goals |
| `runtime` | cycle counter, last_cycle timestamp |

State is **not** reset between seasons. The bot resumes with the same strategy
and memory after a wipe; only the empire itself is recreated on next login.

---

## Configuration (`config.yaml`)

| Key | Default | Description |
|---|---|---|
| `server_url` | `http://localhost:8180` | Gameserver API endpoint |
| `cycle_interval_s` | `60` | Seconds between tick starts |
| `control_port_base` | `9300` | Base port; each bot gets base + offset |
| `strategy.weights` | — | Relative weights for initial strategy roll |
| `strategy.duration_hours` | — | Strategy lifetime ranges per type |
| `personalities` | — | Per-personality strategy weight multipliers |
| `breach_response_chance` | — | Probability to force-switch to defense on breach |
| `attack_defeat_response_chance` | — | Probability to force-switch to attack on loss |
| `selection.top_n` | `3` | Weighted sampling from top N options |
| `category_weights` | — | Per-personality option scoring multipliers |
| `active_strategy_boost` | `1.5` | Extra multiplier for options matching active strategy |

**`--fast` flag:** sets `cycle_interval_s = 5` for local testing.

---

## Edge Cases

| Situation | Behavior |
|---|---|
| Empire wiped (season reset) | Login recreates empire; bot continues normally next tick |
| Server down at login | Exception caught, tick skipped, bot sleeps until next tick |
| Cycle takes > `cycle_interval_s` | `max(0, ...)` → sleep = 0, next tick starts immediately |
| No affordable action | Loop exits at first iteration, bot sleeps rest of interval |
| Action fails (API error) | Logged as warning, loop breaks to avoid tight retry |
| Loop hits MAX_ACTIONS (20) | Tick ends normally — indicates unusually many cheap actions |
| Bot receives SIGTERM | `stop["flag"] = True`, current tick finishes, state saved, exit |
