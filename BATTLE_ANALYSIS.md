# Battle-Prozess Analyse: Java vs. Python

## 1. Architektur-Überblick

### Python (GameServer)
```
BattleService.run_battle()
├── asyncio event loop (15ms ticks)
├── deterministic tick() method
├── send_fn callback (WebSocket abstraction)
└── Broadcasts every 250ms only if state changed

BattleState (Datencontainer)
├── armies: dict[direction, Army]
├── critters: dict[cid, Critter]
├── structures: dict[sid, Structure]
├── pending_shots: list[Shot]
└── delta tracking (new_critters, dead_critter_ids, etc.)
```

### Java (GameEngine)
```
Battle implements Runnable
├── Thread-based (sleep 15ms)
├── step methods called in sequence
├── direct network I/O to ConnectionHandler
└── Broadcasts every 250ms

Battle (Datencontainer)
├── mNorthArmy, mEastArmy, mSouthArmy, mWestArmy
├── mCritters: ConcurrentHashMap[Integer, Critter]
├── mBattlefield: Map
├── delta tracking (mNewCritters, mDeadCritters, etc.)
```

---

## 2. Battle Tick Ordre (MUSS erhalten bleiben)

**BEIDE Implementationen verwenden denselben Tick-Order:**

1. **step_shots()** / stepShots()
   - Flugzeit für Schüsse reduzieren
   - Schaden & Effekte anwenden wenn Schuss ankommt
   - Ablauf: flight_remaining_ms → 0 → apply_damage → remove_shot

2. **step_critters()** / stepCitters()
   - Bewegung entlang Hex-Pfad voranbringen
   - Burn-Effekt applizieren (DoT)
   - Slow-Effekt updaten
   - Finished/Dead clenaup

3. **step_towers()** / stepTowers()
   - Neuaufladung (reload_remaining_ms)
   - Focus-Ziel validieren
   - Neues Ziel akquirieren (best_progress in range)
   - Schüsse feuern

4. **step_armies()** / stepArmies()
   - Wave-Timer herunterrechnen
   - Critter spawnen wenn Wave-Timer 0 ist
   - defending empire nach instanz des critter anfragen
   - defending empire leifert critter nach aktuellen effects
   - Spawn-Pointer weiterbewegen

5. **check_finished()** / endBattleIfFinished()
   - Alle Kritter weg + keine Waves mehr = Battle vorbei
   - Sieges-Bedingung prüfen

---

## 3. Critter-Bewegung

### Python Model (HexCoord-basiert)
```python
@dataclass
class Critter:
    cid: int                    # Unique critter instance ID
    iid: str                    # Item type (references ItemDetails)
    health: float
    path: list[HexCoord]        # Kompletter Pfad als Liste
    current_hex: HexCoord      # aktuelle tile des critters
    path_progress: float        # von aktueller tile bis zur nächsten tile gerechnet (wir genutzt um smoothe bewegung zu ermöglichen)
    speed: float                # hex fields/second
    
    # Movement calculation:
    distance = speed * dt_ms / 1000.0
    path_progress += distance  # wenn über 100% -> next tile
```

### Java Model (gleich)
```java
public class Critter {
    int cID;
    String mItemID;
    float mHP;
    ArrayList<HexField> mPath;
    float mWayPointIndex;       // Fractional progress
    float mSpeed;               // hex fields/second
    
    // Movement: mWayPointIndex += mSpeed * (dt / 1000.0f)
}
```

**Wichtig**: Beide nutzen **kontinuierliche Positions-Progression** nicht diskrete Schritte!

---

## 4. Schuss-Mechanik

### Beide Systeme
```
Shot {
    damage: float
    flight_time_ms: float (wird in step_shots reduziert)
    shot_type: DamageType (NORMAL, BURN, COLD, SPLASH)
    target_cid: int
    effects: dict (slow_target, burn_target, etc.)
}

When flight_time → 0:
  Critter found?
  ├─ YES: Apply damage (reduced by armour)
  │       Apply effects (slow, burn)
  │       Kill if health ≤ 0
  └─ NO: Ignore (target already dead)
```

---

## 5. Broadcast-Strategie

### Python
```python
should_broadcast() → broadcast_timer_ms <= 0

Bei jedem Broadcast:
  delta_list = {
    critters: [critters],
    shots: [shots],
    finished_critter_ids: [reached end],
    structures: [towers]
  }
  
  reset_broadcast() → clear deltas + reset timer
  -> braodcasts beinhalten zu jedem zeitpunkt die komplettten informationen was auf der karte zu rendern ist. in theorie könnte man also von jedem einzelnen broadcast den korrekten zu stadn zeichnen. das soll verhindern, dass sich inkosistente zustände nicht selbst heilen.
  broadcast intervall soll 20hz sein.
  die map wird bei battle setup einmalig übermittelt. sie wird sich nicht ändern währnd gekämpft wird.
```

### Java
```java
if (!mNewStructures.isEmpty() ||
    !mNewCritters.isEmpty() ||
    !mDeadCritters.isEmpty() ||
    ...) {
    broadcastUpdate();
}
```

**Beide**: Delta-basiert, nicht vollständiger State!

---

## 6. Server ↔ Client Kommunikation

### Python
```python
send_fn(uid: int, data: dict) → Async callback
  Abstrahiert WebSocket-Layer
  
Messages gesendet:
  battle_setup → {"bid", "participants", "structures", "map"}
  battle_update (50ms) → {"critters", "shots", ...}
  battle_summary (on finish) → {"winner", "gains", "losses"}
```

### Java
```java
MessageBuilder.BattleSetup(battle)
MessageBuilder.BattleUpdate(battle, empire)
MessageBuilder.BattleSummary(battle)

Sendet direkt über ConnectionHandler.Send(Request)
```

---

## 7. Army Spawning (Wave-System)

### Python
```python
class Army {
    waves: list[CritterWave]  # {iid: str, slots: int}
}

# In step_armies():
critter_spawn_time -= dt_ms
if critter_spawn_time <= 0:  
    spawn_critter(wave.iid, path)
    spawn_pointer+=1
    critter_spawn_time = critter.respawn_timer  # Next spawn delay: hängt von den crittern des angreifers ab. muss in der critter factory des angreifers mitgesendet werden
```

### Java
```java
public class Army {
    ArrayList<CritterWave> mWaves;
    int mSpawnPointer;           // Current wave index
    float mNextWaveIn;           // ms until next spawn
}

// In stepArmies():
mNextWaveIn -= timeElapsed;
if (mNextWaveIn <= 0) {
    spawnWave(mWaves[mSpawnPointer]);
    mNextWaveIn = interval;
    mSpawnPointer++;
}
```

---

## 8. Siege vs. Battle


### Python: Attack Model (WIP)
```python
class Attack:
    attack_id: int
    attacker_uid: int
    defender_uid: int
    army_aid: int
    phase: enum [TRAVELLING, IN_SIEGE, IN_BATTLE, FINISHED]
    eta_seconds: float
    total_eta_seconds: float
    total_sieg_time: float  # fehlte hier
    siege_remaining_seconds: float
```

**Status**: Phase-Maschine implementiert, aber Siege-Phase ist nicht aktiv
- TRAVELLING → IN_SIEGE (TODO: Validate arrival)
- IN_SIEGE → IN_BATTLE (TODO: Start when defender ready)
- IN_BATTLE → FINISHED (TODO: Battle result)

### Java: Battle Komponente
```java
// Battle startet wenn beide Seiten ready sind
// Keine Attack-Klasse in Java = Angriff = direkter Battle
```

---

## 9. Implementierungs-Unterschiede (Key Points)

| Aspekt | Python | Java |
|--------|--------|------|
| Concurrency | asyncio (event-driven) | Threads (preemptive) |
| Daten-Struktur | dataclass + dict | POJO + HashMap |
| Network Layer | abstrahiert (send_fn) | direkt (ConnectionHandler) |
| Dauer-Simulation | long integer ms | float ms |
| Effekte | dict mit keys | Effects ArrayList |
| Hex-Pathfinding | BFS utility function | vorberechnet in Army |
| Battle-ID | auto-increment | AtomicInteger |
| Critter-Spawning | wave-based timer | mSpawnPointer |

---

---

## 11. Implementierungs-Updates (Aktuell)

### ✅ Broadcast Interval Konfigurierbar
- **Wo**: `config/game.yaml` → `broadcast_interval_ms`
- **Wie**: 
  - `BattleState.broadcast_interval_ms` ist nun ein Daten-Feld (nicht Konstante)
  - `BattleService.run_battle()` erhält `broadcast_interval_ms` als Parameter
  - `handlers.py._run_battle_task()` liest game_config und passed den Wert
  - Default: 250ms (Java-kompatibel)

```python
# In handlers.py:
broadcast_interval_ms = svc.game_config.broadcast_interval_ms or 250.0
await battle_svc.run_battle(battle, send_fn, broadcast_interval_ms)

# In battle_service.py:
async def run_battle(self, battle, send_fn, broadcast_interval_ms=250.0):
    battle.broadcast_interval_ms = broadcast_interval_ms
    battle.broadcast_timer_ms = broadcast_interval_ms
```

### ✅ Shot Source Identifier
- **Status**: Bereits vollständig implementiert!
- **Wo**: `models/shot.py`
  ```python
  @dataclass
  class Shot:
      damage: float
      target_cid: int
      source_sid: int          # ← Tower ID (Structure ID)
      shot_type: int
      effects: dict
      flight_remaining_ms: float
  ```
- **Gesetzt in**: `battle_service.py._step_towers()`
  ```python
  shot = Shot(
      damage=structure.damage,
      target_cid=structure.focus_cid,
      source_sid=sid,        # ← Tower Position
      ...
  )
  ```
- **Use Case**: Client kann Schuss-Animation von Tower-Position → Critter-Position zeichnen
- **Nächster Schritt**: In `battle_update` Nachricht serialisieren und an Client senden

---

## 12. Single Spawnpoint Architektur (Python vs. Java)

### Unterschied zur Java-Implementierung

**Java** (4 Directions):
```
mNorthArmy → spawns in North → all critters take North path
mEastArmy  → spawns in East  → all critters take East path
mSouthArmy → spawns in South → all critters take South path
mWestArmy  → spawns in West  → all critters take West path

→ Verteidiger muss 4 verschiedene Türme-Positionen absichern!
```

**Python** (Single Spawnpoint):
```
armies: dict[str, Army]  # Keys: "north", "east", "south", "west"
        └─ Aber praktisch nur EINE Army active pro Battle
        
All critters use SAME path:
  spawnpoint → castle
  
→ Vereinfachte Türme-Platzierung, aber weniger Strategie
```

### Technische Details

1. **Path berechnet bei Battle-Start**
   ```python
   # battle_service.py hat keine Spawnpoint-Logik für 4 Richtungen
   # Path kommt vom Map (defender_uid empire map)
   ```

2. **Wave Spawning**
   ```python
   for direction, army in battle.armies.items():
       # Itarisiert durch alle Directions
       # Aber normalerweise nur "north" (oder default "main"?)
   ```

3. **Was bedeutet "keine Direction mehr"**
   - ✓ Critter kommen nicht von 4 verschiedenen Spawnpoints
   - ✓ Es gibt einen einzigen Startpunkt pro Map
   - ✓ Vereinfachter als Java (strategisch weniger komplex)
   - ✗ Armies-Dict ist noch vestigial (aus Java-Port)

### Empfehlung für Cleanup

Langfristig könnte vereinfacht werden:
```python
# Statt: armies: dict[str, Army]
# Besser: armies: Army | list[Army]

# Und wave_spawn_pointers: dict[tuple[str, int], int]
# Besser: wave_spawn_pointers: dict[int, int]
```

Aber nicht kritisch — aktuelle Struktur funktioniert fine.
