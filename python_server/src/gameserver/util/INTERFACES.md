# util/ — Schnittstellen

## Rolle
Querschnittsfunktionen: Konstanten, Event-Bus, Hex-Mathematik, Effect-Keys, Formatierung.
Keine Abhängigkeiten zu `engine/`, `network/`, `persistence/`.

## Abhängigkeiten

```
util/
├── constants.py   → (keine)
├── effects.py     → (keine)
├── events.py      → (keine, nur stdlib)
├── hex_math.py    → models/hex.py (HexCoord)
└── types.py       → (keine)
```

## Wird verwendet von

| Konsument | Welche Util-Module |
|-----------|-------------------|
| `models/hex.py` | `hex_math.hex_linedraw` (für `line_to()`) |
| `models/battle.py` | `constants` (MIN_KEEP_ALIVE, BROADCAST_INTERVAL) |
| `models/army.py` | `constants` (INITIAL_WAVE_DELAY) |
| `engine/battle_service.py` | `events` (EventBus), `effects` (Schlüssel), `constants` (Timing) |
| `engine/empire_service.py` | `events` (EventBus), `effects`, `constants` |
| `engine/attack_service.py` | `events`, `constants` |
| `engine/army_service.py` | `constants` (WAVES_PER_LEVEL) |
| `engine/statistics.py` | `effects` |
| `network/router.py` | — |
| Alle Services | `events.EventBus` als zentrale Kommunikation |

## Schnittstellen

### EventBus
```python
bus = EventBus()
bus.on(EventType, handler)       # Handler registrieren
bus.off(EventType, handler)      # Handler entfernen
bus.emit(event)                  # Event an alle Handler senden
bus.clear()                      # Alle Handler entfernen
```

Event-Typen (definiert in `events.py`):
- `CritterStarted(critter_id, direction)`
- `CritterFinished(critter_id, with_transfer)`
- `CritterDied(critter_id)`
- `StructureShot(structure_id, shot_index)`
- `BattleFinished(battle_id, defender_won)`
- `AttackArrived(attack_id, defender_uid, army_aid)`
- `SiegeExpired(defender_uid)`
- `ItemCompleted(empire_uid, iid)`

### hex_math
```python
hex_distance(a, b) -> int
hex_linedraw(a, b) -> list[HexCoord]
hex_ring(center, radius) -> list[HexCoord]
hex_disk(center, radius) -> set[HexCoord]
hex_neighbors(coord) -> list[HexCoord]
```

### constants
Numerische Konstanten als Modul-Level-Variablen. Kein State.

### effects
String-Konstanten für Effect-Keys. Kein State.

### types
```python
format_time(seconds) -> str
format_number(value) -> str
format_percent(value) -> str
```

## Design-Entscheidung: EventBus statt Interfaces

Der Java-Code verwendet `ICritterListener` und `IStructureListener` als Interfaces.
In Python ersetzen wir das durch einen typisierten EventBus:

**Vorteile:**
- Lose Kopplung: Emitter kennt die Listener nicht
- Einfach testbar: Event emitten → Ergebnis prüfen
- Kein Interface-Boilerplate
- Neue Events ohne bestehende Klassen zu ändern

**Regel:** Events sind `frozen=True` dataclasses — immutable nach Erzeugung.
