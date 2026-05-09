# 1) ERA System

only one era system should previal:
The yaml way: **YAML-item** | `STONE_AGE`, `MEDIEVAL`, `INDUSTRIAL` |



Three different era key systems exist and must not be mixed:

| System | Example | Used in |
|--------|---------|---------|
| **German** | `STEINZEIT`, `MITTELALTER` | `ERA_ORDER`, `get_current_era()`, `era_effects` dict keys |
| **Internal** | `stone`, `middle_ages`, `renaissance` | `game.yaml` keys, `ai_generator`, `ERA_BACKEND_TO_INTERNAL` |
| **YAML-item** | `STONE_AGE`, `MEDIEVAL`, `INDUSTRIAL` | `era:` field in `knowledge.yaml`, `ERA_ITEM_TO_INDEX` |

Mappings: `ERA_BACKEND_TO_INTERNAL` in `util/army_generator.py`, `ERA_YAML_TO_KEY` in `util/eras.py`.  
Travel offsets are stored as legacy flat fields: `stone_travel_offset`, `middle_ages_travel_offset`, etc. in `GameConfig`.

### Upgrade System

- **Item upgrades** (`item_upgrades: dict[iid, dict[stat, level]]`) live on `Empire`.
- **Price formula**: `base_cost × (total_levels_on_iid + 1)²` — base cost from `game.yaml item_upgrade_base_costs[era_index]`.
- Era index for structures/critters is built at startup in `main.py` (`_item_era_index`) by parsing YAML section comments.
- Structure stats: `damage`, `range`, `reload`, `effect_duration`, `effect_value` (+2–3% per level).
- Critter stats: `health`, `speed`, `armour` (+2% per level).
- Applied in `battle_service._step_armies()` at spawn time (normal waves) and `_make_critter_from_item()` (spawn-on-death).

# 2) Multi-Device Login (gleiche UID, zwei Browser-Tabs/Geräte)

### Problem

Der Server erlaubt pro UID nur **eine aktive WS-Verbindung**. Verbindet sich ein zweites Device mit der gleichen UID, schließt `register_session()` (`network/server.py:119`) die erste Verbindung mit Code 1008 ("Superseded by new connection"). Das löst auf Device 1 einen Reconnect-Timer aus (2s), der wiederum Device 2 verdrängt → Loop alle ~5s, beide Devices ruckeln dauerhaft.

### Betroffene Dateien

| Datei | Stelle | Rolle |
|-------|--------|-------|
| `network/server.py:102–125` | `register_session()` | schließt alte WS bei gleicher UID |
| `network/server.py:127–142` | `unregister_session()` | räumt Session auf |
| `network/handlers/battle.py:327–350` | `handle_battle_register` | `_evict_observer_from_all` entfernt UID aus anderen Battles |
| `web/js/views/defense/ws.js:114–124` | `close`-Handler | reconnect nach 2s wenn nicht intentional |

### Lösungsoptionen

**Option A — Multi-Connection pro UID (empfohlen)**
`_connections` von `dict[uid, ws]` auf `dict[uid, set[ws]]` umstellen. `send_to` sendet an alle WS der UID. `register_session` verdrängt nicht mehr. `observer_uids` in `BattleState` bleibt unverändert (UID-basiert). Aufwand: mittel, alle `send_to`-Aufrufe bleiben kompatibel wenn `send_to` intern iteriert.

**Option B — Reconnect bei 1008 unterdrücken**
Client erkennt Code 1008 und verzichtet auf Reconnect. Verhindert den Loop, aber das zweite Device bekommt nach dem ersten Reconnect-Zyklus dauerhaft keine Updates mehr. Kein echtes Multi-Device.

**Option C — Nur im Battle-Kontext: observer_uids als connection-basiertes Set**
Statt UID-basierter Observer ein `set[ws]` oder `set[(uid, ws_id)]`. Aufwändiger, da alle Broadcast-Pfade angepasst werden müssen.


### Webserver autharkie

Überprüfen welche configs der webserver selbst ließt und welche daten er vom gameserver bekommt