# YAML-Attribute hinzufügen — Checkliste

Wenn ein neues Attribut in eine Konfigurationsdatei (`config/*.yaml`) eingeführt werden soll, müssen die folgenden Dateien in dieser Reihenfolge angepasst werden.

---

## 1. `config/*.yaml` — Attribut in den Daten eintragen

Das Attribut in jede betroffene Entität eintragen, z. B. für alle Tower in `structures.yaml`:

```yaml
BASIC_TOWER:
  name: "Basic Tower"
  select: first    # ← neues Attribut
  ...
```

**Betroffene Dateien je nach Entitätstyp:**

| Entität      | Datei                          |
|--------------|-------------------------------|
| Gebäude      | `config/buildings.yaml`        |
| Forschung    | `config/knowledge.yaml`        |
| Türme        | `config/structures.yaml`       |
| Critter      | `config/critters.yaml`         |
| Artefakte    | `config/artefacts.yaml`        |
| Spielregeln  | `config/game.yaml`             |

---

## 2. `models/items.py` — Feld in `ItemDetails` ergänzen

`ItemDetails` ist das gemeinsame Datentransfer-Objekt für alle YAML-Kategorien (frozen dataclass). Hier gehört das Feld in den richtigen Themenblock:

```python
# Structure
damage: float = 0.0
range: int = 0
reload_time_ms: float = 0.0
shot_speed: float = 0.0
shot_type: str = "normal"
shot_sprite: str = ""
select: str = "first"   # ← hier eingetragen
```

Wichtig: `ItemDetails` ist `frozen=True`. Nur Felder mit Defaultwert ergänzen.

---

## 3. `models/structure.py` — Feld in `Structure` ergänzen (nur für tower-spezifische Attribute)

`Structure` ist das Laufzeit-Objekt für einen platzierten Turm. Attribute, die während der Battle gebraucht werden, müssen hier stehen:

```python
shot_sprite: str = ""
select: str = "first"   # ← hier eingetragen
effects: dict[str, float] = field(default_factory=dict)
```

Analog gibt es für andere Entitäten eigene Modelle:
- Critter → `models/critter.py`
- Building → kein eigenes Laufzeit-Objekt (nur ItemDetails)

---

## 4. `loaders/item_loader.py` — Attribut in `_parse_section` auslesen

`_parse_section` baut aus dem rohen YAML-Dict den `ItemDetails`-Konstruktoraufruf:

```python
items.append(ItemDetails(
    ...
    shot_sprite=attrs.get("shot_sprite", ""),
    select=attrs.get("select", "first"),   # ← hier ergänzen
    sprite=attrs.get("sprite", None),
    ...
))
```

Defaultwert hier muss mit dem Defaultwert in `ItemDetails` übereinstimmen.

---

## 5. `network/handlers.py` — Attribut in alle `Structure(...)`-Aufrufe übernehmen

In `handlers.py` gibt es **4 Stellen**, an denen ein `Structure`-Objekt gebaut wird. Alle müssen das neue Feld erhalten:

```python
structure = Structure(
    ...
    shot_sprite=getattr(item, "shot_sprite", ""),
    select=getattr(item, "select", "first"),   # ← an allen 4 Stellen
    effects=getattr(item, "effects", {}),
)
```

Die vier Stellen sind in diesen Funktionen:
- `_send_battle_setup` (Zeile ~1003)
- `sync_structures` (Zeile ~1947)
- `battle:start_requested` Handler, erster Pfad (Zeile ~2299)
- `battle:start_requested` Handler, zweiter Pfad (Zeile ~2465)

**Wichtig:** In `handlers.py` muss `getattr(item, "reload_time_ms", ...)` statt `getattr(item, "reload_time", ...)` verwendet werden — der Feldname in `ItemDetails` lautet `reload_time_ms`.

---

## 6. Engine-Code — Attribut verwenden

Das neue Feld steht jetzt auf dem `Structure`-Objekt und kann in der Battle-Engine genutzt werden, z. B. in `engine/battle_service.py`:

```python
strategy = structure.select
if strategy == "last":
    return min(in_range, key=lambda c: c.path_progress)
if strategy == "random":
    return random.choice(in_range)
return max(in_range, key=lambda c: c.path_progress)  # default: "first"
```

---

## 7. Tests

Mindestens zwei Testebenen ergänzen:

### Loader-Tests (`tests/test_item_loader.py`)
- Default-Wert korrekt (kein Attribut in YAML → Default greift)
- Alle Werte korrekt geparsed (`first`, `last`, `random`, …)
- Alle Einträge in der realen Config haben einen validen Wert

### Engine-Tests (`tests/test_tower_shooting.py` o. ä.)
- Verhalten für jeden Strategiewert testen
- Randbedingungen: leere Reichweite, nur ein Critter, mehrere Critter

---

## Kurzcheckliste

```
[ ] config/*.yaml         → Attribut zu allen betroffenen Einträgen hinzufügen
[ ] models/items.py       → Feld in ItemDetails (frozen dataclass)
[ ] models/structure.py   → Feld in Structure (wenn zur Laufzeit gebraucht)
[ ] loaders/item_loader.py → attrs.get("attribut", default) in _parse_section
[ ] network/handlers.py   → getattr(item, "attribut", default) an 4 Stellen
[ ] engine/               → Attribut verwenden (battle_service.py o. ä.)
[ ] tests/                → Loader-Tests + Engine-Tests
```

---

## Hinweise

- `ItemDetails` ist `frozen=True` und damit unveränderlich nach der Erstellung — alle Felder beim Konstruktor übergeben.
- Der Feldname in `ItemDetails` kann vom YAML-Key abweichen (z. B. `reload_time` im YAML → `reload_time_ms` im Modell). In `_parse_section` und `getattr`-Aufrufen in `handlers.py` immer den Modell-Feldnamen verwenden.
- Neue Pflichtattribute vermeiden (immer Defaultwert angeben), damit alte Saves und laufende Battles rückwärtskompatibel bleiben.
- Nach Änderungen an `structures.yaml`: `grep -c "neues_attribut" config/structures.yaml` prüfen, ob alle 29 Tower das Attribut haben.
