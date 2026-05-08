# Effects Guide — Towers, Critters & Empire

Wie neue Effects hinzugefügt werden und wie das bestehende System funktioniert.

---

## Übersicht: Relevante Dateien

| Datei | Rolle |
|---|---|
| `config/structures.yaml` | Shot-Effect-Keys je Tower definieren |
| `config/critters.yaml` | (keine Effects — nur `armour`, `spawn_on_death`) |
| `config/knowledge.yaml` | Empire-Effects via Knowledge-Items |
| `models/items.py` → `ItemDetails` | `effects: dict` aus YAML laden |
| `models/structure.py` → `Structure` | `effects: dict` zur Laufzeit |
| `models/shot.py` → `Shot` | `effects: dict` kopiert vom Structure |
| `models/critter.py` → `Critter` | Status-Felder (`slow_*`, `burn_*`) |
| `engine/battle_service.py` | Shot-Effects & Empire-Modifikatoren anwenden |
| `engine/empire_service.py` | `recalculate_effects()`, Life-Regen |
| `web/js/views/defense.js` | Effects-Anzeige in Tower-Details |

---

## Teil 1: Shot-Effects (Tower → Critter)

Shot-Effects werden beim Schuss auf einen Critter angewendet. Sie stehen in `structures.yaml` und werden zur Laufzeit in `Shot.effects` kopiert.

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

### Splash
```yaml
effects: {splash_radius: 0.6}
```
- `splash_radius` (float, Hex-Einheiten): Trifft alle Critter im Radius um den Primärtreffer.
- Implementiert in `_apply_shot_damage` → alle Critter im Radius erhalten vollen Schaden (inkl. Burn/Slow falls auch gesetzt).
- `_VISUAL_SPLASH = 3` → Projektil-Typ für den Client.

### Armour-Verhalten
- **Direktschaden**: `max(0.5, damage - critter.armour)`
- **Burn-DoT**: ignoriert Armour vollständig
- **Slow/Stun**: kein Schaden, Armour irrelevant

---

## Teil 2: Empire-Effects (Globalmodifikatoren)

Empire-Effects werden durch abgeschlossene Knowledge-Items freigeschaltet und via `recalculate_effects()` auf das Empire-Dict angewendet. Sie sind persistent und gelten für alle Aktionen des Empires.

### Ressourcen & Wirtschaft

| Effect-Key | Typ | Beschreibung |
|---|---|---|
| `gold_offset` | float | Goldertrag pro Sekunde (additiv) |
| `culture_offset` | float | Kulturertrag pro Sekunde (additiv) |
| `life_offset` | float | Life-Regen pro Sekunde (additiv) |
| `life_modifier` | float (0.0–1.0+) | Multiplikator auf `life_offset`: `regen = life_offset × (1 + life_modifier)` |

### Baugeschwindigkeit & Forschung

| Effect-Key | Typ | Beschreibung |
|---|---|---|
| `build_speed` | float | Baubeschleunigung (additiv auf Fortschritt) |
| `research_speed` | float | Forschungsbeschleunigung (additiv auf Fortschritt) |

### Wellen-Timing

| Effect-Key | Typ | Beschreibung |
|---|---|---|
| `wave_delay_offset` | float (ms) | Verzögerung zwischen Wellen-Spawns (positiv = langsamer) |

---

## Teil 3: Critter-Buffs (Angreifer-Empire)

Diese Effects im Angreifer-Empire verstärken alle gespawnten Critter. Angewendet in `_step_armies` und `_make_critter_from_item`.

| Effect-Key | Typ | Beschreibung |
|---|---|---|
| `speed_modifier` | float (0.0–1.0+) | `critter.speed × (1 + speed_modifier)` |
| `health_modifier` | float (0.0–1.0+) | `critter.health × (1 + health_modifier)` |
| `armour_modifier` | float (0.0–1.0+) | `critter.armour × (1 + armour_modifier)` |

**Beispiel**: `health_modifier: 0.5` → Critter haben +50% HP.

---

## Teil 4: Tower-Buffs (Verteidiger-Empire)

Diese Effects im Verteidiger-Empire verstärken alle aktiven Türme. Angewendet live in `_step_towers`.

| Effect-Key | Typ | Beschreibung |
|---|---|---|
| `damage_modifier` | float (0.0–1.0+) | `shot.damage × (1 + damage_modifier)` |
| `range_modifier` | float (0.0–1.0+) | `structure.range × (1 + range_modifier)` — erhöht Angriffsreichweite |
| `reload_modifier` | float (0.0–1.0+) | `reload_decrement = dt_ms × (1 + reload_modifier)` — Tower feuert schneller |

**Beispiel**: `reload_modifier: 0.5` → Tower lädt 50% schneller nach.

---

## Neuen Shot-Effect hinzufügen — Schritt für Schritt

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


### 8. Textbeschreibung für neue effects:

Neue efeects bekommen eine textbeschreibung in web/js/i18n.js
