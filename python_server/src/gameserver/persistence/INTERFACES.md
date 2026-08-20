# persistence/ — Schnittstellen

## Rolle
Datenhaltung: SQLite-Datenbank, Zustandsspeicherung/-wiederherstellung, Replay-Aufzeichnung.
Einzige Schicht mit Datei-/Datenbank-I/O.

## Abhängigkeiten

```
persistence/
├── database.py     → (keine, nur aiosqlite)
├── state_save.py   → models/ (alle, für Serialisierung)
├── state_load.py   → models/ (alle, für Deserialisierung)
└── replay.py       → (keine)
```

## Wird verwendet von

| Konsument | Was |
|-----------|-----|
| `main.py` | `database.connect()`, `state_load.load_state()` beim Start |
| `engine/game_loop.py` | `state_save.save_state()` periodisch (alle 30s) |
| `engine/battle_service.py` | `replay.ReplayRecorder` für Battle-Aufzeichnung |
| `network/auth.py` | `database.get_user()`, `database.create_user()` |

## Schnittstellen

### Database
```python
async connect() -> None
async close() -> None

# Users
async get_user(username) -> dict | None
async create_user(username, password_hash, email) -> int

# Messages
async get_messages(uid, limit=50) -> list[dict]
async send_message(from_uid, to_uid, text) -> None

# Rankings
async update_ranking(uid, tai) -> None
async get_rankings(limit=20) -> list[dict]

# Alliances (directional declarations; mutual = active alliance, pools culture for leaderboard ranking)
async toggle_alliance_declaration(from_uid, to_uid) -> bool  # insert if absent, delete if present
async get_alliance_declarations_for(uid) -> tuple[set[int], set[int]]  # (declared_to, declared_by)
async get_all_mutual_alliances() -> dict[int, set[int]]  # {uid: {allied_uid, ...}} two-way declarations only
```

### State Save/Load
```python
async save_state(state_dict, path="state.json") -> None
async load_state(path="state.json") -> dict | None
```

Das `state_dict` enthält:
- `empires`: dict[uid, Empire-Daten]
- `attacks`: list[Attack-Daten]
- `battles`: list[BattleState-Daten]
- `engine_state`: Spielphase, Tick-Counter, etc.

### ReplayRecorder
```python
record(timestamp_ms, event_dict) -> None
async save(path=None) -> None
```

## Datenfluss

```
Engine-State (Models)
       │
       ▼
  state_save.save_state()  ──────▶  state.json
                                         │
  state_load.load_state()  ◀─────────────┘
       │
       ▼
  Engine-State (Models)


  Battle-Events
       │
       ▼
  replay.record(ts, event)
       │
       ▼
  replay.save()  ──────▶  replays/{bid}.json
```
