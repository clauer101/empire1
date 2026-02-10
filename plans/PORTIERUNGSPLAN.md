# Portierungsplan: Java GameServer → Python

## Übersicht

Portierung eines Multiplayer Tower-Defense / Empire-Building Spielservers von Java nach Python.

### Geänderte Prämissen

| Thema | Alt (Java) | Neu (Python) |
|-------|-----------|--------------|
| Item/Critter/Tower-Konfiguration | `items.xml` übernehmen | **Neu definieren** in YAML |
| Karten-Geometrie | Rechteckiges 96×54 Grid, Pixel-Koordinaten | **Hexagonales Grid**, Axialkoordinaten (q, r) |
| Distanzberechnung | Euklidisch in Pixelraum | **Hex-Distanz**: `(|dq| + |dq+dr| + |dr|) / 2` |
| Serialisierung | XStream XML über ObjectOutputStream | **JSON** über WebSockets |
| Threading | Thread pro Connection + Battle-Thread | **asyncio** Event-Loop + Tasks |
| Datenbank | JDBC + raw SQL | **aiosqlite** |
| Typisierung | Java-Klassen | **dataclasses** + **Pydantic** |
| Prozessmodell | 2 JVM-Prozesse über TCP | **1 Prozess**, Server + Engine im selben asyncio-Loop |

---

## Zielarchitektur

```
python_server/
├── pyproject.toml
├── config/
│   ├── items.yaml
│   ├── ai_templates.yaml
│   └── maps/
├── src/
│   └── gameserver/
│       ├── __init__.py
│       ├── main.py
│       ├── models/          # Reine Datenmodelle (dataclasses)
│       ├── engine/          # Spiellogik-Services
│       ├── network/         # WebSocket-Server + Routing
│       ├── persistence/     # Datenhaltung
│       ├── loaders/         # YAML/TMX Config-Parser
│       └── util/            # Konstanten, Events, Hex-Math
└── tests/
```

---

## Phasenplan

### Phase 1 — Hex-Fundament + Item-Definitionen (Woche 1–2)

| Schritt | Was | Abhängigkeit |
|---------|-----|-------------|
| 1.1 | `util/hex_math.py` — Axialkoordinaten, Distanz, Nachbarn, Ring, Linie | Keine |
| 1.2 | `models/hex.py` — `HexCoord(q, r)` dataclass mit Operatoren | Keine |
| 1.3 | `models/map.py` — Hex-Map mit Pfaden, Bauzonen, Belegung | 1.1, 1.2 |
| 1.4 | `models/items.py` — `ItemDetails` als Pydantic-Modell | Keine |
| 1.5 | `config/items.yaml` — Item/Critter/Tower-Definitionen | 1.4 |
| 1.6 | `loaders/item_loader.py` — YAML → ItemDetails | 1.4 |
| 1.7 | `loaders/map_loader.py` — Map-Dateien → HexMap | 1.3 |
| 1.8 | `engine/upgrade_provider.py` — Tech-Tree aus Config | 1.6 |
| 1.9 | `util/constants.py`, `util/effects.py`, `util/events.py` | Keine |

**Validierung:** Unit-Tests für Hex-Math, geladene Items/Maps.

---

### Phase 2 — Kampfsystem (Woche 3–5)

Aufgebaut in 7 Schichten, von innen nach außen:

#### Schicht 1: Hex-Geometrie
- `util/hex_math.py`, `models/hex.py`
- Axialkoordinaten, Distanz, Nachbarn, Ring, Linie
- Tests: Distanz-Symmetrie, Nachbar-Anzahl, Ring-Größe, Linien-Endpunkte

#### Schicht 2: Hex-Pfade & Map
- `models/map.py`
- 4 Pfade als `list[HexCoord]`, Bauzonen als `set[HexCoord]`, Belegung
- Tests: Pfad-Konnektivität, Bau-Blockierung, Überlappung

#### Schicht 3: Critter-Bewegung
- `models/critter.py`
- Fraktionale Position auf Pfad (`path_progress`), Speed in Hex/s
- Statuseffekte: Slow (Multiplikator + Timer), Burn (DPS + Timer)
- Schadensformel: `max(min(dmg, 1), dmg - armour)`, Burn ignoriert Rüstung
- Tests: Bewegung, Zielankunft, Schaden mit/ohne Rüstung, Slow/Burn

#### Schicht 4: Structure-Targeting & Schüsse
- `models/structure.py`, `models/shot.py`
- Reichweite in Hex-Feldern, Targeting: geringstes `remainder_path`
- Flugzeit: `hex_dist / shot_speed * 1000` ms
- Effekte: NORMAL, COLD (Slow), BURN (DoT), SPLASH (AoE)
- Tests: Targeting-Algorithmus, Reichweite, Reload, Flugzeit

#### Schicht 5: Wellen-Spawning
- `models/army.py`
- CritterWave: slots → critter count, spawn interval
- Army: wave pointer, wave delay, initial delay (25s)
- Tests: Timing, Slot-Skalierung, Spawn-Position

#### Schicht 6: Battle-Loop Integration
- `engine/battle_service.py`
- asyncio-Task mit ~15ms Tick
- Tick-Reihenfolge: Shots → Critters → Towers → Armies → Broadcast
- Splash: Hex-Radius, 500ms Sekundärschüsse, Primärziel ausgeschlossen
- Spawn-on-Death: Kinder am Eltern-Pfadpunkt, gestaffelt mit Slow
- Tests: Volle Kampfabläufe, 4-Richtungen, Broadcast-Throttling

#### Schicht 7: Loot & Kampfende
- Critter erreicht Ziel → Ressourcen stehlen (Capture-Map)
- Critter stirbt → Verteidiger bekommt Bonus (Bonus-Map)
- Sieg: Life > 0 AND keine Critter AND alle Armeen fertig AND > 10s
- Niederlage: Life ≤ 0 → sofort, dann Loot-Phase
- Tests: Ressourcen-Transfer, Loot-Berechnung, Siegbedingungen

**Deterministischer Test-Modus:** `dt_ms` wird explizit übergeben statt Wall-Clock.

---

### Phase 3 — Empire + Angriffssystem (Woche 6–7)

| Schritt | Was |
|---------|-----|
| 3.1 | `models/empire.py` — Spielerzustand: Ressourcen, Gebäude, Forschung, Armeen |
| 3.2 | `engine/empire_service.py` — Ressourcen-Generierung, Bau, Forschung, Bürger |
| 3.3 | `models/attack.py` — Reise-Zustandsautomat |
| 3.4 | `engine/attack_service.py` — ETA-Countdown, Belagerung |
| 3.5 | `engine/army_service.py` — Kosten, Slots, Spy-Optionen |
| 3.6 | `engine/ai_service.py` — KI-Armeen, Skalierung |
| 3.7 | `engine/statistics.py` — TAI, Rankings, Siegbedingungen |

---

### Phase 4 — Netzwerk + Persistenz + Integration (Woche 8–9)

| Schritt | Was |
|---------|-----|
| 4.1 | `models/messages.py` — Pydantic Request/Response pro Nachrichtentyp |
| 4.2 | `network/serialization.py` — JSON + optionale Kompression |
| 4.3 | `network/server.py` — asyncio WebSocket-Server |
| 4.4 | `network/auth.py` — Login/Signup gegen DB |
| 4.5 | `network/router.py` — Message-Dispatch nach Typ |
| 4.6 | `persistence/database.py` — aiosqlite für Users, Messages, Rankings |
| 4.7 | `persistence/state_save.py` + `state_load.py` — JSON-State-Dumps |
| 4.8 | `persistence/replay.py` — Battle-Replay-Speicherung |
| 4.9 | `engine/game_loop.py` — asyncio-basierter 1s-Tick-Loop |
| 4.10 | `main.py` — Einstiegspunkt, alles zusammenführen |
| 4.11 | Integrationstests mit echten WebSocket-Clients |

---

## Kampfsystem-Portierung im Detail

### Kernmechanik-Kette

```
Armee → Wellen → Critter-Spawn → Bewegung auf Hex-Pfad → Turm-Targeting →
Schuss (Flugzeit) → Schaden/Effekte → Splash → Spawn-on-Death → Loot
```

### HexCoord Datenmodell

```python
@dataclass(frozen=True)
class HexCoord:
    q: int
    r: int

    @property
    def s(self) -> int:
        return -self.q - self.r

    def distance_to(self, other: "HexCoord") -> int:
        return (abs(self.q - other.q)
              + abs(self.q + self.r - other.q - other.r)
              + abs(self.r - other.r)) // 2

    def neighbors(self) -> list["HexCoord"]:
        dirs = [(1,0),(-1,0),(0,1),(0,-1),(1,-1),(-1,1)]
        return [HexCoord(self.q+d[0], self.r+d[1]) for d in dirs]
```

### Critter-Bewegung (Hex-basiert)

```python
@dataclass
class Critter:
    cid: int
    iid: str
    health: float
    speed: float          # Hex-Felder pro Sekunde
    armour: float
    path: list[HexCoord]
    path_progress: float = 0.0  # fraktionaler Index auf dem Pfad

    slow_remaining_ms: float = 0.0
    slow_speed: float = 0.0
    burn_remaining_ms: float = 0.0
    burn_dps: float = 0.0
```

Bewegungsalgorithmus:
```python
def step_critter(critter, dt_ms, events):
    critter.slow_remaining_ms = max(0, critter.slow_remaining_ms - dt_ms)
    if critter.burn_remaining_ms > 0:
        apply_damage(critter, critter.burn_dps * dt_ms / 1000, DamageType.BURN)
        critter.burn_remaining_ms = max(0, critter.burn_remaining_ms - dt_ms)
    move = critter.effective_speed * (dt_ms / 1000)
    critter.path_progress = min(critter.path_progress + move, len(critter.path) - 1)
    if critter.is_finished:
        events.emit(CritterFinished(critter.cid, with_transfer=True))
```

### Schadensformel

```python
def apply_damage(critter, damage, dtype):
    if dtype == DamageType.BURN:
        effective = damage
    else:
        effective = max(min(damage, 1.0), damage - critter.armour)
    critter.health = max(0, critter.health - effective)
```

### Tower-Targeting

```python
def find_best_target(structure, critters):
    """Ziel: Critter mit geringstem remainder_path im Range."""
    best_cid, best_remainder = None, float('inf')
    for cid, c in critters.items():
        if not c.is_alive or c.is_finished:
            continue
        if structure.position.distance_to(c.current_hex) > structure.range:
            continue
        if c.remainder_path < best_remainder:
            best_cid, best_remainder = cid, c.remainder_path
    return best_cid
```

### Battle-Loop

```python
async def run_battle(self, battle):
    while battle.keep_alive:
        dt_ms = measure_elapsed()
        self._step_shots(battle, dt_ms)
        self._step_critters(battle, dt_ms)
        self._step_towers(battle, dt_ms)
        self._step_armies(battle, dt_ms)
        self._check_finished(battle)
        if battle.should_broadcast():
            await self._broadcast(battle)
        await asyncio.sleep(0.015)
```

### Test-Pyramide

```
         ┌──────────────────────┐
         │  Integration-Tests   │  5 Tests: volle Kämpfe E2E
         ├──────────────────────┤
         │  Szenario-Tests      │  15 Tests: Kampfabläufe headless
         ├──────────────────────┤
         │  Komponenten-Tests   │  30 Tests: Critter, Tower, Shot, Wave
         ├──────────────────────┤
         │  Unit-Tests          │  20 Tests: Hex-Math, Damage-Formel
         └──────────────────────┘
```

### Wichtige Tests

| Test | Prüft |
|------|-------|
| `test_hex_distance` | Axiale Distanzberechnung |
| `test_critter_moves_along_path` | Fraktionale Pfad-Bewegung |
| `test_damage_with_armour` | Schadensreduktion, Minimum 1 |
| `test_burn_bypasses_armour` | Burn ignoriert Rüstung |
| `test_target_most_advanced` | Tower wählt am weitesten fortgeschrittenen Critter |
| `test_shot_flight_time` | Schaden erst nach Flugzeit |
| `test_splash_hits_neighbors` | AoE auf Hex-Nachbarn |
| `test_spawn_on_death` | Kinder spawnen am Eltern-Ort |
| `test_battle_defender_wins` | Alle Critter tot → Sieg |
| `test_battle_defender_loses` | Life ≤ 0 → sofort vorbei |
| `test_loot_on_finish` | Durchgekommener Critter stiehlt Ressourcen |
| `test_four_directions` | 4 Armeen gleichzeitig |

---

## Risiken & Gegenmaßnahmen

| Risiko | Maßnahme |
|--------|----------|
| Battle-Tick (15ms) blockiert asyncio | Reine Berechnung ohne I/O — schnell. Bei >50 Battles: `asyncio.to_thread()` |
| Float-Präzision bei Kampf-Physik | Deterministischer Test-Modus mit explizitem `dt_ms` |
| Hex-Geometrie-Bugs | Umfangreiche Property-Tests für Hex-Math |
| Neue Config-Formate | Validierung via Pydantic-Schemas |
