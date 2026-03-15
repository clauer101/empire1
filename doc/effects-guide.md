# Effects Guide — Towers & Critters

Wie neue Effects hinzugefügt werden und wie das bestehende System funktioniert.

---

## Übersicht: Relevante Dateien

| Datei | Rolle |
|---|---|
| `config/structures.yaml` | Effect-Keys je Tower definieren |
| `config/critters.yaml` | (keine Effects — nur `armour`, `spawn_on_death`) |
| `models/items.py` → `ItemDetails` | `effects: dict` aus YAML laden |
| `models/structure.py` → `Structure` | `effects: dict` zur Laufzeit |
| `models/shot.py` → `Shot` | `effects: dict` kopiert vom Structure |
| `models/critter.py` → `Critter` | Status-Felder (`slow_*`, `burn_*`) |
| `engine/battle_service.py` | Effekte anwenden (Schuss trifft, Tick) |
| `web/js/views/defense.js` | Effects-Anzeige in Tower-Details |

---

## Aktuelle Effects

### Slow / Stun
```yaml
effects: {slow_duration: 2000, slow_ratio: 0.3}
```
- `slow_duration` (ms): Wie lange der Slow dauert.
- `slow_ratio` (0.0–1.0): Geschwindigkeitsmultiplikator. `0` = vollständiger Stun.
- Stackt **nicht** — neue Treffer überschreiben den laufenden Timer.

### Burn / DoT
```yaml
effects: {burn_duration: 3000, burn_dps: 2.0}
```
- `burn_duration` (ms): Wie lange der Burn dauert.
- `burn_dps` (float): Schaden pro Sekunde — ignoriert Armour.
- Stackt **nicht** — neue Treffer überschreiben Timer und dps.
- Tower mit `damage: 0` + Burn: nur DoT-Schaden (kein Direktschaden).

---

## Neuen Effect hinzufügen — Schritt für Schritt

### 1. YAML: Keys im Tower definieren

`config/structures.yaml` — neuen Effect-Key(s) eintragen:

```yaml
MY_TOWER:
  effects: {my_effect_duration: 3000, my_effect_value: 2.5}
```

Keys können beliebig benannt werden — sie werden als `dict[str, float]` durchgereicht.

---

### 2. Critter-Statusfelder anlegen

`models/critter.py` — Felder für den laufenden Zustand des Critters hinzufügen:

```python
@dataclass
class Critter:
    # ... bestehende Felder ...
    my_effect_remaining_ms: float = 0.0
    my_effect_value: float = 0.0
```

---

### 3. Effect beim Treffer anwenden

`engine/battle_service.py` → `_apply_shot_damage(battle, shot)`:

```python
# MY_EFFECT
if "my_effect_duration" in shot.effects or "my_effect_value" in shot.effects:
    critter.my_effect_remaining_ms = float(shot.effects.get("my_effect_duration", 3000.0))
    critter.my_effect_value        = float(shot.effects.get("my_effect_value", 1.0))
```

---

### 4. Effect im Tick-Loop verarbeiten

`engine/battle_service.py` → `_move_critter(battle, critter, dt_ms)`:

```python
# MY_EFFECT tick
if critter.my_effect_remaining_ms > 0:
    tick_ms = min(dt_ms, critter.my_effect_remaining_ms)
    # ... Logik anwenden, z.B. Schaden oder Modifikator ...
    critter.my_effect_remaining_ms = max(0.0, critter.my_effect_remaining_ms - dt_ms)
```

---

### 5. Effect-Zustand an Client senden

`engine/battle_service.py` — im Broadcast-Dict des Critters ergänzen:

```python
"my_effect_remaining_ms": max(0, critter.my_effect_remaining_ms),
```

---

### 6. Visual Shot-Type (optional)

`engine/battle_service.py` → `_shot_visual_type(effects)`:

```python
# Neue Konstante oben:
_VISUAL_MY_EFFECT = 4

# In der Funktion:
if "my_effect_duration" in effects or "my_effect_value" in effects:
    return _VISUAL_MY_EFFECT
```

Der Shot-Type wird an den Client gesendet; `hex_grid.js` kann ihn für Farbe/Sprite des Projektils nutzen.

---

### 7. Effect in Tower-Details anzeigen (optional)

`web/js/views/defense.js` — im Effects-Block der `_showTileDetails`-Funktion.

Die bestehende Anzeige gibt alle Effect-Keys automatisch aus:
```js
Object.entries(s.effects).map(([k, v]) => k + ': ' + v).join(', ')
```
Falls eine schönere Darstellung gewünscht ist, dort eigene Labels eintragen.

---

## Splash (nicht implementiert)

`_VISUAL_SPLASH = 3` und `DamageType.SPLASH = 3` sind definiert. YAML-Header erwähnt `splash_radius`.  
Es gibt **keine** Flächenschaden-Logik in `battle_service.py`.

Für Splash müsste in `_apply_shot_damage` nach Treffern in Reichweite `splash_radius` gesucht und jeweils Schaden angewendet werden.

---

## Armour-Verhalten

- **Direktschaden**: `max(0.5, damage - critter.armour)`
- **Burn-DoT**: ignoriert Armour vollständig
- **Slow/Stun**: kein Schaden, Armour irrelevant
