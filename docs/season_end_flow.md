# Season End Flow

## Overview

A season ends when a player completes the configured `end_criterion` item (default: `THE_WORLD_WONDER`). From that moment the game goes through four distinct phases before the next season starts.

```
Player builds end_criterion item
        │
        ▼
Phase 1: End Rally          (end_ralley_duration seconds, default 1 week)
        │
        ▼
Phase 2: Leadtime / Wipe    (next_season_leadtime reached → empires wiped)
        │
        ▼
Phase 3: Frozen Countdown   (game frozen until next_season_start)
        │
        ▼
Phase 4: New Season Starts  (season_number +1, game unfreezes)
```

---

## Phase 1 — End Rally

**Trigger:** `empire_service._apply_effects()` calls `try_set_end_criterion_activated()` when a player finishes building the item whose IID matches `game.yaml: end_criterion`.

**What happens:**
- `global_state._end_criterion_activated` is set to the current UTC timestamp (only the first caller wins — idempotent).
- `global_state._end_criterion_empire_uid/name` records who triggered it.
- `is_end_rally_active()` returns `True` while `now - activated < end_ralley_duration` (from `game.yaml`).
- During the rally, `end_ralley_effects` (gold bonus, siege speed modifier, etc.) are broadcast to all clients via the summary endpoint.
- The frontend shows an "End Rally Active" banner in the era overlay.

**Configured in `game.yaml`:**
```yaml
end_criterion: THE_WORLD_WONDER
end_ralley_duration: 604800        # seconds (1 week)
end_ralley_effects:
  gold_offset: 2
  siege_time_modifier: 0.5
```

---

## Phase 2 — Leadtime Wipe

**Trigger:** `next_season_leadtime` is reached (ISO-8601 UTC timestamp, set via `state.yaml` or the admin API). This is typically configured a short time before `next_season_start` so a maintenance window exists between the wipe and the new season opening.

**What happens (in `game_loop._step()`):**
1. `set_season_reset_triggered(True)` — marks the game as "between seasons".
2. `empires.wipe_all_empires()` — all `Empire` objects removed from memory.
3. `attacks.wipe_all_attacks()` — all in-flight attacks cancelled.
4. `clear_end_criterion()` — resets the end-criterion state.
5. `database.wipe_season_stats()` (async) — deletes `empire_stats`, `era_firsts`, `artifact_holds`.
6. `next_season_leadtime` is cleared from global state so this block does not re-trigger.
7. `_season_snapshot_done = False` — allows the snapshot to run.

**Season snapshot (`_take_season_snapshot()`)** runs concurrently:
- Copies `state.yaml` and `gameserver.db` (via `VACUUM INTO`) to `data/{env}/results/season1/`.
- Writes `empire_stats.csv` and `artifact_holds.csv`.
- Saves `last_season_artifacts` table: records which artifact IIDs each empire held, used to grant a bonus on next login (see Phase 4 / Login Bonus below).

After the wipe the game loop **returns early every tick** (game is frozen). Clients see a countdown banner toward `next_season_start`.

---

## Phase 3 — Frozen Countdown

**Condition:** `is_season_reset_triggered() == True` and `next_season_start` has not yet been reached.

- All game ticks are skipped (`_step()` returns early).
- REST and WebSocket endpoints still respond; `summary` includes `season_reset_triggered: true`, `next_season_start`, and `next_season_leadtime`.
- Frontend shows a full-screen countdown banner (`SeasonResetActive`).

**Relevant keys in `state.yaml` / `global_state`:**

| Key | Description |
|-----|-------------|
| `season_reset_triggered` | True while frozen between seasons |
| `next_season_start` | ISO-8601 UTC — when the new season opens |
| `next_season_leadtime` | ISO-8601 UTC — when the wipe fires (cleared after use) |
| `next_season_title` | Title string for the new season |
| `season_number` | Current season number (incremented at Phase 4) |
| `season_title` | Current season title |

---

## Phase 4 — New Season Starts

**Trigger:** `next_season_start` is reached while `season_reset_triggered == True`.

**What happens:**
1. `set_season(season_number + 1, new_title)` — increments the counter, updates the title.
2. `set_season_reset_triggered(False)` — unfreezes the game loop.
3. Normal ticking resumes.

**Login / Signup after the wipe:** When a user logs in and their empire no longer exists (wiped), `auth.login` calls `_create_empire_for_new_user()`, which:
1. Creates a fresh `Empire` at a grid-based spawn position (`empire_spawn_spacing` hex distance apart, configured in `game.yaml`).
2. Calls `_maybe_grant_last_season_artifact()` — if the user held artifacts at the end of the previous season (stored in `last_season_artifacts`), one is chosen at random and added to the new empire.
3. Calls `_maybe_grant_artifact_lottery()` — standard artifact distribution check.

---

## Configuration Reference (`game.yaml`)

| Key | Type | Description |
|-----|------|-------------|
| `end_criterion` | string | Item IID that triggers the end rally |
| `end_ralley_duration` | int (seconds) | How long the rally lasts |
| `end_ralley_effects` | dict | Bonus effects active during the rally |
| `next_season_start` | ISO-8601 string | When the new season opens |
| `next_season_leadtime` | ISO-8601 string | When the wipe fires (set via admin/state.yaml) |
| `empire_spawn_spacing` | int | Hex distance between spawn points for new empires |

---

## State Persistence

All season state is persisted in `state.yaml` (saved periodically and on shutdown) under the `global:` section. On server restart, `main.py` restores the full season state including `end_criterion_activated`, `season_reset_triggered`, `next_season_start`, and `next_season_leadtime` so a server restart during any phase is safe and resumes exactly where it left off.

---

## Key Files

| File | Role |
|------|------|
| `engine/global_state.py` | In-memory season state and end-criterion flags |
| `engine/game_loop.py` | Phase transitions in `_step()`, snapshot in `_take_season_snapshot()` |
| `engine/empire_service.py` | Detects end_criterion completion, calls `try_set_end_criterion_activated()` |
| `network/handlers/auth.py` | Empire re-creation on login, last-season artifact bonus |
| `persistence/database.py` | `wipe_season_stats()`, `save_last_season_artifacts()`, `get_last_season_artifacts()` |
| `persistence/state_save.py` / `state_load.py` | Persists and restores global season state across restarts |
| `config/game.yaml` | All season-related configuration values |
