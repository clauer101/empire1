# loaders/ — Schnittstellen

## Rolle
Konfiguration lesen: YAML/Map-Dateien parsen und in `models/`-Objekte umwandeln.
Werden einmalig beim Serverstart aufgerufen.

## Abhängigkeiten

```
loaders/
├── item_loader.py    → models/items.py (ItemDetails, ItemType)
├── map_loader.py     → models/hex.py (HexCoord), models/map.py (HexMap, Direction)
├── ai_loader.py      → (keine Model-Abhängigkeit, gibt raw dict zurück)
└── string_loader.py  → (keine Model-Abhängigkeit, gibt raw dict zurück)
```

Externe Abhängigkeit: `pyyaml`

## Wird verwendet von

| Konsument | Welcher Loader |
|-----------|----------------|
| `main.py` | Alle — beim Serverstart |
| `engine/upgrade_provider.py` | Erhält `list[ItemDetails]` von `item_loader` |
| `engine/ai_service.py` | Erhält `dict` von `ai_loader` |
| `engine/empire_service.py` | Erhält `HexMap` von `map_loader` (für neue Empires) |

## Schnittstellen

### item_loader
```python
load_items(path="config/items.yaml") -> list[ItemDetails]
```

### map_loader
```python
load_map(path) -> HexMap
```

### ai_loader
```python
load_ai_templates(path="config/ai_templates.yaml") -> dict
```

### string_loader
```python
load_strings(path) -> dict[str, str]
```

## Config-Format

### items.yaml
```yaml
buildings:
  farm:
    name: "Farm"
    effort: 50
    costs: {gold: 200}
    requirements: []
    effects: {gold_offset: 5}

structures:
  arrow_tower:
    name: "Arrow Tower"
    damage: 5.0
    range: 3
    reload_time: 1000
    shot_speed: 8.0

critters:
  goblin:
    name: "Goblin"
    speed: 2.0
    health: 20.0
    armour: 0.0
    slots: 1
    time_between: 500
    capture: {gold: 10}
    bonus: {gold: 5}
```

### Map-YAML
```yaml
paths:
  north: [[0,5], [1,4], [2,3], ...]
  south: [[0,-5], [1,-4], ...]
build_tiles: [[3,1], [3,2], [4,1], ...]
```

## Kein Schreib-Zugriff
Loader lesen nur. Konfiguration wird zur Laufzeit nicht verändert.
