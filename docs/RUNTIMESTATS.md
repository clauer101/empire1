# Runtime Stats — Empire Interaction Logging

Per-empire lifetime statistics, stored in SQLite and updated at event time (no polling).

---

## Storage

Two tables in `gameserver.db` (created automatically on startup via `CREATE TABLE IF NOT EXISTS`):

### `empire_stats`

One row per empire (uid). All counters default to 0.

| Column | Type | Meaning |
|---|---|---|
| `uid` | INTEGER PK | Empire/user ID |
| `attacks_won_human` | INTEGER | Attacks won against human defenders |
| `attacks_lost_human` | INTEGER | Attacks lost against human defenders |
| `attacks_won_ai` | INTEGER | *(reserved — AI is always defender)* |
| `attacks_lost_ai` | INTEGER | *(reserved)* |
| `defense_won_human` | INTEGER | Defenses won against human attackers |
| `defense_lost_human` | INTEGER | Defenses lost against human attackers |
| `defense_won_ai` | INTEGER | Defenses won against AI attackers |
| `defense_lost_ai` | INTEGER | Defenses lost against AI attackers |
| `spies_sent` | INTEGER | Total spy attacks dispatched |
| `towers_sold` | INTEGER | Total towers sold via map save |
| `towers_placed` | INTEGER | Total towers placed via map save |
| `artifacts_stolen` | INTEGER | Total artifacts stolen by this empire |
| `longest_battle_ms` | INTEGER | Duration of longest battle in ms |
| `critters_killed` | INTEGER | Total critters killed across all defenses |
| `culture_stolen` | REAL | Total culture stolen from this empire |
| `research_stolen` | REAL | Total research effort stolen from this empire |
| `culture_won` | REAL | Total culture gained by looting others |
| `research_won` | REAL | Total research effort gained by looting others |
| `defense_gold_earned` | REAL | Total gold earned by killing critters in defense |
| `first_era_reached` | INTEGER | Count of eras this empire was first globally to reach |
| `critter_upgrade_levels` | INTEGER | Peak total critter upgrade levels across all critter IIDs |
| `tower_upgrade_levels` | INTEGER | Peak total tower upgrade levels across all tower IIDs |

### `artifact_holds`

One row per (uid, artifact_iid) pair. Tracks cumulative hold duration per artifact per empire.

| Column | Type | Meaning |
|---|---|---|
| `uid` | INTEGER | Empire ID |
| `artifact_iid` | TEXT | Artifact item ID |
| `acquired_at` | REAL | Unix timestamp when last acquired (NULL if not held) |
| `total_held_secs` | REAL | Accumulated hold time from completed hold periods |

To compute current hold time (including ongoing holds):
```sql
SELECT uid, artifact_iid,
  total_held_secs + CASE WHEN acquired_at IS NOT NULL
    THEN (unixepoch() - acquired_at) ELSE 0 END AS held_secs
FROM artifact_holds;
```

---

## Event Hooks

All writes use `asyncio.ensure_future(...)` (fire-and-forget) and are wrapped in `try/except` so failures never affect gameplay.

| Stat | Hook location | File |
|---|---|---|
| Battle outcomes (win/loss × human/AI) | `_run_battle_task()` after battle ends | `handlers/battle_task.py` |
| Longest battle | Same, `record_empire_stat_max()` | `handlers/battle_task.py` |
| Critters killed | Same, `battle.critters_killed` | `handlers/battle_task.py` |
| Defense gold earned | Same, `battle.defender_gold_earned` | `handlers/battle_task.py` |
| Culture stolen/won | Same, from `loot` dict | `handlers/battle_task.py` |
| Research stolen/won | Same, from `loot["knowledge"]` | `handlers/battle_task.py` |
| Artifact stolen + hold tracking | Same, from `_apply_artifact_steal()` return | `handlers/battle_task.py` |
| Spies sent | `handle_spy_attack()` after `start_attack()` succeeds | `handlers/military.py` |
| Towers sold | `handle_map_save_request()` sell-refund loop | `handlers/economy.py` |
| Towers placed | `handle_map_save_request()` cost-deduction block | `handlers/economy.py` |
| First era reached | `_apply_effects()` before/after era comparison | `engine/empire_service.py` |
| Critter/Tower upgrade levels | `handle_buy_item_upgrade()` after successful purchase | `handlers/economy.py` |

"First era reached" uses `global_state._eras_first_reached` (a module-level set) to track which eras have already been claimed globally. The first empire to reach a given era gets `first_era_reached += 1`.

---

## DB Methods (`persistence/database.py`)

| Method | Purpose |
|---|---|
| `record_empire_stat(uid, **increments)` | Upsert row, add integer increments to one or more columns |
| `record_empire_stat_float(uid, field, value)` | Upsert row, add float value to one column |
| `record_empire_stat_max(uid, field, value)` | Upsert row, update column only if new value is larger |
| `record_artifact_acquired(uid, iid, ts)` | Set `acquired_at` timestamp for a hold start |
| `record_artifact_lost(uid, iid, ts)` | Accumulate hold delta into `total_held_secs`, clear `acquired_at` |
| `get_empire_stats(uid)` | Return stats dict for one empire |
| `get_all_empire_stats()` | Return all rows |
| `get_artifact_hold_totals()` | Return (uid, iid, held_secs) including ongoing holds |

---

## Adding a New Stat

1. **Add the column** to the `empire_stats` CREATE TABLE in `_SCHEMA` (`database.py`).  
   `CREATE TABLE IF NOT EXISTS` is idempotent, but existing databases need a migration:
   ```python
   # In Database.connect(), after the existing migration try/except blocks:
   try:
       await self._conn.execute("SELECT new_column FROM empire_stats LIMIT 1")
   except aiosqlite.OperationalError:
       await self._conn.execute("ALTER TABLE empire_stats ADD COLUMN new_column INTEGER DEFAULT 0")
   ```

2. **Find the event hook** — the place in the code where the action happens (see table above for existing patterns).

3. **Call the appropriate method** fire-and-forget:
   ```python
   asyncio.ensure_future(svc.database.record_empire_stat(uid, new_column=1))
   ```
   Use `record_empire_stat_float` for REAL columns, `record_empire_stat_max` for "highest ever" columns.

4. **Expose via API** (optional) — `get_all_empire_stats()` returns all columns; add the new field to the season-results endpoint or a dedicated admin endpoint.
