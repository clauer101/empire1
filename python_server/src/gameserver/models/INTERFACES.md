# models/ — Schnittstellen

## Rolle
Reine Datenmodelle (dataclasses / Pydantic). Keine Geschäftslogik, kein I/O.

## Abhängigkeiten
- `models/hex.py` ← `util/hex_math.py` (für `line_to()`)
- Keine Abhängigkeit zu `engine/`, `network/`, `persistence/`

## Wird verwendet von

| Konsument | Welche Models |
|-----------|---------------|
| `engine/battle_service.py` | `BattleState`, `Critter`, `Structure`, `Shot`, `Army`, `CritterWave` |
| `engine/empire_service.py` | `Empire`, `Structure`, `HexMap` |
| `engine/attack_service.py` | `Attack` |
| `engine/army_service.py` | `Army`, `SpyArmy`, `CritterWave` |
| `engine/upgrade_provider.py` | `ItemDetails`, `ItemType` |
| `engine/game_loop.py` | `Empire`, `Attack` |
| `engine/statistics.py` | `Empire` |
| `network/router.py` | `messages.py` (alle Message-Typen) |
| `network/server.py` | `messages.py` (Serialisierung) |
| `persistence/state_save.py` | Alle Models für Zustandsdump |
| `persistence/state_load.py` | Alle Models für Zustandswiederherstellung |
| `loaders/item_loader.py` | `ItemDetails`, `ItemType` |
| `loaders/map_loader.py` | `HexCoord`, `HexMap`, `Direction` |

## Schnittstellen-Regeln

1. **Keine Imports aus `engine/`, `network/`, `persistence/`** — Models sind die unterste Schicht.
2. **Felder öffentlich** — kein Getter/Setter-Overhead, direkte Attribute.
3. **Derived Properties als `@property`** — z.B. `critter.is_alive`, `critter.effective_speed`.
4. **Immutable wo möglich** — `HexCoord` ist `frozen=True`, `ItemDetails` ist `frozen=True`.
5. **Mutable State explizit markiert** — `Critter`, `Structure`, `BattleState` sind mutable.

## Datenfluss

```
config/ (YAML)
    │
    ▼
loaders/ ──parse──▶ models/ ◀──create/modify── engine/
                       │
                       ▼
              persistence/ (save/load)
                       │
                       ▼
               network/ (serialize to JSON)
```

## Message-Protokoll

`models/messages.py` definiert alle Client↔Server Nachrichtentypen als Pydantic-Models.
Jeder Typ hat ein `type: Literal[...]` Feld als Diskriminator.

**Dispatch:** `parse_message(dict)` → konkretes Model → `Router.route()` → Handler.

**Kein generisches Payload-Dict** — jedes Feld ist explizit typisiert und validiert.
