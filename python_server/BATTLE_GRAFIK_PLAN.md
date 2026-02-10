# Battle Grafik Implementierungsplan

**Version:** 1.0  
**Datum:** 2026-02-10  
**Status:** Draft – Bereit zur Implementierung

---

## 1. Executive Summary

Dieser Plan beschreibt die Implementierung der grafischen Battle-Darstellung für das E3 Tower-Defense-Spiel. Die Battle läuft serverseitig in einer State Machine (TRAVELLING → IN_SIEGE → IN_BATTLE), während der Client die Grafik autonom rendert basierend auf delta-basierten Updates vom Server.

### Architektur (Client-Side Autonomous Rendering)

```
Server (Python)                          Client (JavaScript)
━━━━━━━━━━━━━━━━                        ━━━━━━━━━━━━━━━━━━━━
BattleService                            HexGrid + Canvas
├─ step_shots()       ─────────┐        ├─ _stepBattleCritters()
├─ step_critters()             │        ├─ _renderCritters()
├─ step_towers()               │        ├─ _renderShots()
├─ step_armies()               ├───────→├─ _renderEffects()
└─ broadcast (250ms)  ─────────┘        └─ _renderHealthBars()
     │                                       │
     └─ battle_update                       │
        ├─ new_critters: [...]              │
        ├─ dead_critter_ids: [...]          │
        ├─ new_shots: [...]                 │
        └─ finished_critter_ids: [...]      │
                                            │
        WebSocket ──────────────────────────┘
```

**Prinzip:** Server sendet nur Ereignisse (spawn, die, fire), Client interpoliert Bewegung autonom.

---

## 2. Unterschiede zur Java-Referenzimplementierung

### 2.1 Critter-Spawning

| Aspekt | Java (alt) | Python (neu) |
|--------|------------|--------------|
| **Spawnpoints** | 4 Richtungen (N/E/S/W) | **1 Richtung** (spawnpoint tile) |
| **Paths** | 4 verschiedene Pfade | **1 Pfad** pro Map |
| **Strategie** | Verteidiger muss 4 Seiten abdecken | Fokus auf einzelnen Chokepoint |
| **Map-Layout** | Fest vorgegebene Karte | **Individuell im Composer** erstellt |

**Code-Auswirkung:**
```python
# Python (vereinfacht):
armies: dict[str, Army]  # Keys: "north", aber praktisch nur eine Army pro Battle
path = empire.hex_map.paths.get("main", None)  # Ein einziger Pfad

# Java (komplex):
mNorthArmy, mEastArmy, mSouthArmy, mWestArmy  # 4 separate Armeen
ArrayList<HexField> northPath, eastPath, ...   # 4 separate Pfade
```

### 2.2 Hex-Grid vs. Kartesisch

| Aspekt | Java | Python |
|--------|------|--------|
| **Grid-System** | Kartesisch (X/Y) | **Hex (Q/R)** – Axial Coordinates |
| **Distanz** | `Math.sqrt((x2-x1)² + (y2-y1)²)` | Hex-Distanz: `(abs(q1-q2) + abs(r1-r2) + abs(q1+r1-q2-r2)) / 2` |
| **Nachbarn** | 8 Richtungen (u.a. diagonal) | **6 Richtungen** (keine Diagonalen) |
| **Pathfinding** | A* auf Grid | **BFS auf Hex-Graph** |

### 2.3 Map Creation

| Aspekt | Java | Python |
|--------|------|--------|
| **Map-Quelle** | Fest im Code | **Composer (Editor)** – Drag & Drop |
| **Speicherung** | Hardcoded | `map_save_request` → YAML |
| **Build-Tiles** | Vordefiniert | **Dynamisch** – vom Player platziert |
| **Validierung** | Keine | `test_map_validation.py` – prüft castle + spawnpoint |

---

## 3. Implementierungsplan

### Phase 1: Server-Side Data Preparation ✅

**Status:** Bereits implementiert!

- [x] `BattleState` mit delta tracking (`new_critters`, `new_shots`, ...)
- [x] `BattleService.tick()` mit deterministischem Ablauf
- [x] Shot-Struktur mit `source_sid` (Tower-Position)
- [x] Broadcast-Logik (250ms throttled)

**Ausstehend:**
- [ ] `Shot` in `battle_update` Message serialisieren
- [ ] `ShotVisual` Datenstruktur für Client-Rendering

### Phase 2: Client-Side Foundation ✅

**Status:** Grundlagen vorhanden!

- [x] `HexGrid.battleCritters` Registry
- [x] `addBattleCritter()` – Critter-Spawning
- [x] `_stepBattleCritters()` – Autonome Bewegung
- [x] `_getCritterPixelPos()` – Path-Interpolation
- [x] Critter-Rendering (gelber Kreis, Placeholder)

**Ausstehend:**
- [ ] Shot-Rendering (Pfeil/Projectile von Tower → Critter)
- [ ] Effekt-Rendering (Burn-DoT, Slow-Debuff)
- [ ] Health-Bar Rendering (über jedem Critter)
- [ ] Critter-Sprites (statt gelber Kreis)

### Phase 3: Shot & Effect Visualization (Neu)

**Ziel:** Schuss-Animationen und visuelle Effekte implementieren.

#### 3.1 Shot Data Structure

**Server-Seite** (`models/shot.py`):
```python
@dataclass
class Shot:
    damage: float
    target_cid: int
    source_sid: int          # ← Tower SID (für Position-Lookup)
    shot_type: int           # 0=normal, 1=slow, 2=burn
    effects: dict            # {"slow": 0.5, "burn_dps": 2.0}
    flight_remaining_ms: float
```

**Client-Seite** (neu: `shot_visual.js`):
```javascript
class ShotVisual {
  constructor(shot, startPos, targetCid) {
    this.shot = shot;
    this.startX = startPos.x;
    this.startY = startPos.y;
    this.targetCid = targetCid;
    this.progress = 0.0;  // 0 → 1
    this.alive = true;
  }

  step(dt) {
    this.progress += dt / (this.shot.flight_remaining_ms / 1000.0);
    if (this.progress >= 1.0) {
      this.alive = false;
      return true;  // hit target
    }
    return false;
  }

  getPixelPos(critterPos) {
    // Interpolate from tower position → critter position
    return {
      x: this.startX + (critterPos.x - this.startX) * this.progress,
      y: this.startY + (critterPos.y - this.startY) * this.progress,
    };
  }
}
```

#### 3.2 Shot Rendering Logic

**In `HexGrid.js`:**
```javascript
class HexGrid {
  constructor(opts) {
    // ...
    this.battleShots = new Map();  // shot_id → ShotVisual
  }

  addBattleShot(shot, source_sid) {
    const structure = this.tiles.get(hexKey(shot.source_q, shot.source_r));
    const startPos = hexToPixel(shot.source_q, shot.source_r, this.hexSize);
    const shotVisual = new ShotVisual(shot, startPos, shot.target_cid);
    this.battleShots.set(shot.shot_id, shotVisual);
  }

  _stepBattleShots(dt) {
    for (const [sid, shot] of this.battleShots) {
      if (shot.step(dt)) {
        // Hit target → trigger impact effect
        this._spawnImpactEffect(shot.targetCid, shot.shot.shot_type);
        this.battleShots.delete(sid);
      }
    }
  }

  _renderShots(ctx, sz) {
    for (const [sid, shotVis] of this.battleShots) {
      const critter = this.battleCritters.get(shotVis.targetCid);
      if (!critter) continue;  // target died mid-flight

      const critterPos = this._getCritterPixelPos(critter, sz);
      const pos = shotVis.getPixelPos(critterPos);

      // Arrow rendering (by shot type)
      switch (shotVis.shot.shot_type) {
        case 0: this._drawArrow(ctx, pos.x, pos.y, '#ffcc00'); break;  // normal
        case 1: this._drawArrow(ctx, pos.x, pos.y, '#6666ff'); break;  // slow
        case 2: this._drawArrow(ctx, pos.x, pos.y, '#ff6633'); break;  // burn
      }
    }
  }

  _drawArrow(ctx, x, y, color) {
    ctx.fillStyle = color;
    ctx.beginPath();
    ctx.arc(x, y, 4, 0, Math.PI * 2);
    ctx.fill();
    // TODO: Proper arrow shape (triangle pointing at target)
  }
}
```

#### 3.3 Effects Rendering

**Burn-Effekt** (DoT):
```javascript
_renderCritterEffects(ctx, critter, pos, sz) {
  // Burn effect = orange glow + particles
  if (critter.burn_remaining_ms > 0) {
    ctx.save();
    ctx.globalAlpha = 0.6;
    const grad = ctx.createRadialGradient(pos.x, pos.y, 0, pos.x, pos.y, sz * 0.5);
    grad.addColorStop(0, '#ff6633');
    grad.addColorStop(1, 'rgba(255, 102, 51, 0)');
    ctx.fillStyle = grad;
    ctx.beginPath();
    ctx.arc(pos.x, pos.y, sz * 0.5, 0, Math.PI * 2);
    ctx.fill();
    ctx.restore();
  }

  // Slow effect = blue overlay
  if (critter.slow_remaining_ms > 0) {
    ctx.save();
    ctx.globalAlpha = 0.4;
    ctx.strokeStyle = '#6666ff';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.arc(pos.x, pos.y, sz * 0.35, 0, Math.PI * 2);
    ctx.stroke();
    ctx.restore();
  }
}
```

#### 3.4 Health Bar

```javascript
_renderHealthBar(ctx, critter, pos, sz) {
  const barWidth = sz * 0.8;
  const barHeight = 4;
  const barY = pos.y - sz * 0.45;

  const ratio = Math.max(0, critter.health / critter.max_health);

  // Background (dark)
  ctx.fillStyle = 'rgba(0, 0, 0, 0.5)';
  ctx.fillRect(pos.x - barWidth / 2, barY, barWidth, barHeight);

  // Health bar (gradient red → yellow → green)
  let color;
  if (ratio > 0.6) color = '#4caf50';
  else if (ratio > 0.3) color = '#ffcc00';
  else color = '#d32f2f';

  ctx.fillStyle = color;
  ctx.fillRect(pos.x - barWidth / 2, barY, barWidth * ratio, barHeight);

  // Border
  ctx.strokeStyle = 'rgba(255, 255, 255, 0.3)';
  ctx.lineWidth = 1;
  ctx.strokeRect(pos.x - barWidth / 2, barY, barWidth, barHeight);
}
```

### Phase 4: Critter Sprites (Optional Enhancement)

**Ziel:** Ersetzt gelben Kreis durch Critter-Icons/Sprites basierend auf `iid`.

#### 4.1 Sprite Sheet

**Assets:**
```
web/assets/critters/
├── spider.png      (32x32)
├── goblin.png      (32x32)
├── orc.png         (32x32)
└── dragon.png      (48x48)
```

**Preload in `hex_grid.js`:**
```javascript
constructor(opts) {
  // ...
  this.critterSprites = new Map();
  this._loadCritterSprites();
}

_loadCritterSprites() {
  const sprites = {
    'spider': '/assets/critters/spider.png',
    'goblin': '/assets/critters/goblin.png',
    'orc':    '/assets/critters/orc.png',
    'dragon': '/assets/critters/dragon.png',
  };
  for (const [iid, url] of Object.entries(sprites)) {
    const img = new Image();
    img.src = url;
    img.onload = () => this._dirty = true;
    this.critterSprites.set(iid, img);
  }
}
```

**Render:**
```javascript
_renderCritters(ctx, sz) {
  for (const [cid, critter] of this.battleCritters) {
    if (!critter.alive || critter.path.length < 2) continue;
    const pos = this._getCritterPixelPos(critter, sz);

    const sprite = this.critterSprites.get(critter.iid);
    if (sprite && sprite.complete) {
      const spriteSize = sz * 0.8;
      ctx.drawImage(sprite, 
        pos.x - spriteSize / 2,
        pos.y - spriteSize / 2,
        spriteSize, spriteSize
      );
    } else {
      // Fallback: colored circle
      ctx.fillStyle = '#ffcc00';
      ctx.beginPath();
      ctx.arc(pos.x, pos.y, sz * 0.3, 0, Math.PI * 2);
      ctx.fill();
    }

    // Health bar above sprite
    this._renderHealthBar(ctx, critter, pos, sz);

    // Effects overlay
    this._renderCritterEffects(ctx, critter, pos, sz);
  }
}
```

### Phase 5: Server Message Enhancement

**Aktuell:** `battle_update` sendet:
```python
{
  "new_critters": [
    {"cid": 1, "iid": "spider", "path": [...], "speed": 2.0}
  ],
  "dead_critter_ids": [2, 5],
  "finished_critter_ids": [7],
}
```

**Neu:** Shots hinzufügen:
```python
{
  "new_critters": [...],
  "new_shots": [
    {
      "shot_id": 1,
      "source_sid": 10,        # Tower Structure ID
      "source_q": 3, "source_r": 2,  # Hex-Position
      "target_cid": 5,
      "shot_type": 1,          # 0=normal, 1=slow, 2=burn
      "flight_remaining_ms": 500.0,
      "damage": 10.0
    }
  ],
  "dead_critter_ids": [...]
}
```

**Code-Änderung in `battle_service.py`:**
```python
def _broadcast_update(self, battle: BattleState, send_fn):
    if not battle.should_broadcast():
        return
    
    # Serialize shots
    shot_dicts = []
    for shot in battle.new_shots:
        # Find tower hex position by SID
        tower = battle.structures.get(shot.source_sid)
        if tower:
            shot_dicts.append({
                "shot_id": id(shot),  # or generate unique ID
                "source_sid": shot.source_sid,
                "source_q": tower.q,   # ← NEU
                "source_r": tower.r,   # ← NEU
                "target_cid": shot.target_cid,
                "shot_type": shot.shot_type,
                "flight_remaining_ms": shot.flight_remaining_ms,
                "damage": shot.damage,
            })
    
    update = {
        "type": "battle_update",
        "new_critters": [_serialize_critter(c) for c in battle.new_critters],
        "new_shots": shot_dicts,  # ← NEU
        "dead_critter_ids": battle.dead_critter_ids[:],
        "finished_critter_ids": battle.finished_critter_ids[:],
    }
    
    await send_fn(uid, update)
```

### Phase 6: Performance Optimizations

#### 6.1 Culling

**Problem:** Bei 100+ Critters kann Rendering langsam werden.

**Lösung:** Nur Critters rendern, die im Viewport sichtbar sind.

```javascript
_isInViewport(pos) {
  const padding = this.hexSize * 2;
  return (
    pos.x * this.zoom + this.offsetX > -padding &&
    pos.x * this.zoom + this.offsetX < this._logicalWidth + padding &&
    pos.y * this.zoom + this.offsetY > -padding &&
    pos.y * this.zoom + this.offsetY < this._logicalHeight + padding
  );
}

_renderCritters(ctx, sz) {
  for (const [cid, critter] of this.battleCritters) {
    const pos = this._getCritterPixelPos(critter, sz);
    if (!this._isInViewport(pos)) continue;  // ← Culling
    // ... render critter
  }
}
```

#### 6.2 Batched Rendering

**Problem:** Viele `ctx.arc()` Aufrufe sind langsam.

**Lösung:** Draw calls batchen.

```javascript
_renderCritters(ctx, sz) {
  // First pass: draw all critter bodies
  ctx.fillStyle = '#ffcc00';
  ctx.beginPath();
  for (const [cid, critter] of this.battleCritters) {
    if (!critter.alive) continue;
    const pos = this._getCritterPixelPos(critter, sz);
    ctx.moveTo(pos.x + sz * 0.3, pos.y);
    ctx.arc(pos.x, pos.y, sz * 0.3, 0, Math.PI * 2);
  }
  ctx.fill();

  // Second pass: health bars + effects
  for (const [cid, critter] of this.battleCritters) {
    const pos = this._getCritterPixelPos(critter, sz);
    this._renderHealthBar(ctx, critter, pos, sz);
    this._renderCritterEffects(ctx, critter, pos, sz);
  }
}
```

#### 6.3 OffscreenCanvas (Fortgeschritten)

Für extrem hohe Critter-Zahl (>500) kann `OffscreenCanvas` WebWorker-basiertes Rendering ermöglichen.

---

## 4. Integration mit bestehender Battle State Machine

### 4.1 Attack Service States

```python
# gameserver/engine/attack_service.py
class AttackPhase(Enum):
    TRAVELLING = "travelling"    # Army bewegt sich zur Burg
    IN_SIEGE = "in_siege"        # Army wartet (grace period)
    IN_BATTLE = "in_battle"      # Battle aktiv
```

**Ablauf:**
1. **TRAVELLING** (configurable via `travel_time_ms`)
   - Client zeigt Marschroute an (optional)
   - Countdown-Timer: "Angriff kommt in 30s"
   
2. **IN_SIEGE** (configurable via `siege_grace_period_ms`)
   - Client zeigt "Belagerung begonnen!"
   - Verteidiger hat Zeit, Türme zu platzieren
   - Countdown: "Schlacht beginnt in 10s"
   
3. **IN_BATTLE** → `BattleService.run_battle()` startet
   - Client wechselt zur Battle-View (Composer mit aktiver Battle)
   - HexGrid aktiviert `battleActive = true`

**UI-Indikatoren:**

In `statusbar.js`:
```javascript
function _renderAttacks(attacks) {
  for (const attack of attacks) {
    if (attack.phase === 'travelling') {
      return '<span style="color:orange">⚠ Angriff unterwegs (' + attack.eta_s + 's)</span>';
    } else if (attack.phase === 'in_siege') {
      return '<span style="color:red">🛡 Belagerung! Schlacht in ' + attack.battle_starts_in_s + 's</span>';
    } else if (attack.phase === 'in_battle') {
      return '<span style="color:red;font-weight:bold"><a href="#composer">⚔ BATTLE AKTIV</a></span>';
    }
  }
}
```

### 4.2 Battle View Activation

**In `composer.js`:**
```javascript
function _onBattleSetup(msg) {
  console.log('[Composer] Battle setup:', msg);
  
  // Clear previous battle state
  grid.clearBattle();
  
  // Load battle map (if different from current)
  if (msg.tiles) {
    grid.fromJSON({ tiles: msg.tiles });
    grid._centerGrid();
  }
  
  // Place structures (towers)
  if (msg.structures) {
    for (const s of msg.structures) {
      grid.setTile(s.q, s.r, s.iid);  // Place tower tile
      // Store structure metadata
      grid.tiles.get(hexKey(s.q, s.r)).sid = s.sid;
      grid.tiles.get(hexKey(s.q, s.r)).structure_data = s;
    }
  }
  
  // Mark battle as active
  _battleActive = true;
  grid.battleActive = true;
  
  // Lock editing (can't place towers during battle)
  _disableEditing();
  
  grid._dirty = true;
}

function _disableEditing() {
  document.querySelector('#tile-palette').style.pointerEvents = 'none';
  document.querySelector('#tile-palette').style.opacity = '0.5';
  document.querySelector('#map-battle').textContent = 'Battle läuft...';
  document.querySelector('#map-battle').disabled = true;
}
```

---

## 5. Testing Strategy

### 5.1 Unit Tests (Python)

**Bestehend:**
- ✅ `test_battle_integration.py` – BattleService.tick() Deterministik
- ✅ `test_shot_resolution.py` – Shot damage calculation
- ✅ `test_structure_targeting.py` – Tower target acquisition

**Neu:**
- [ ] `test_battle_broadcast.py` – Delta-Message Serialisierung
- [ ] `test_shot_visualization_data.py` – `source_q/r` in Messages

### 5.2 Integration Tests (E2E)

**Playwright/Cypress:**
```javascript
test('Battle renders critters autonomously', async ({ page }) => {
  await page.goto('http://localhost:8000/#composer');
  
  // Trigger battle via debug dashboard
  await page.evaluate(() => {
    fetch('http://localhost:9000/debug/trigger_battle', { method: 'POST' });
  });
  
  // Wait for battle_setup
  await page.waitForSelector('.hex-canvas[data-battle-active="true"]');
  
  // Verify critters appear
  await page.waitForFunction(() => {
    const canvas = document.querySelector('#hex-canvas');
    const ctx = canvas.getContext('2d');
    const imgData = ctx. getImageData(0, 0, canvas.width, canvas.height);
    // Check for yellow pixels (critters)
    return imgData.data.some((v, i) => i % 4 === 0 && v > 200);  // R channel
  }, { timeout: 5000 });
});
```

### 5.3 Performance Tests

**Benchmark:**
```javascript
// In browser console during battle:
performance.mark('render-start');
grid._render();
performance.mark('render-end');
performance.measure('render', 'render-start', 'render-end');
console.log(performance.getEntriesByName('render')[0].duration, 'ms');

// Goal: < 16ms (60 FPS) bei 100 Critters
```

---

## 6. Rollout Plan

### Milestone 1: Basic Shot Visualization (1-2 Tage)
- [ ] Server: `new_shots` in `battle_update` Message
- [ ] Client: `ShotVisual` Klasse + Basic Arrow Rendering
- [ ] Test: 1 Tower schießt auf 1 Critter → Pfeil visible

### Milestone 2: Effects & Health Bars (1 Tag)
- [ ] Burn-Effekt (orange glow)
- [ ] Slow-Effekt (blue border)
- [ ] Health bar rendering (gradient)
- [ ] Test: Critter nimmt Schaden → Health bar sinkt

### Milestone 3: Critter Sprites (Optional, 1 Tag)
- [ ] Sprite sheet asset creation
- [ ] Preload logic in `HexGrid`
- [ ] Sprite rendering + fallback
- [ ] Test: Verschiedene Critter-Typen sichtbar unterscheidbar

### Milestone 4: Performance Optimization (1 Tag)
- [ ] Viewport culling
- [ ] Batched rendering
- [ ] Benchmark bei 200+ Critters
- [ ] Profiling mit Chrome DevTools

### Milestone 5: Polish & UX (1 Tag)
- [ ] Battle start/end transitions (fade in/out)
- [ ] Sound effects (optional)
- [ ] Victory/Defeat overlay
- [ ] Battle summary display

---

## 7. Open Questions & Decisions

### Q1: Wie werden Türme während Battle visualisiert?

**Optionen:**
- A) Türme bleiben statisch (nur Icon im Tile)
- B) Türme "drehen sich" zum Ziel (rotate transform)
- C) "Muzzle flash" Animation beim Schießen

**Empfehlung:** Start mit A (einfach), später C hinzufügen (visuelles Feedback).

### Q2: Wie zeigen wir Battle-Ende?

**Optionen:**
- A) Fade-out → Redirect zu Dashboard
- B) Victory/Defeat Overlay mit Stats → "Zurück" Button
- C) Battle bleibt pausiert sichtbar → manual dismiss

**Empfehlung:** B (beste UX, wie Java-Version).

### Q3: Unterstützen wir Battle-Replay?

**Java hatte:** `mReplayLog` (Request-Log zum späteren Abspielen)

**Python:** Nicht implementiert.

**Entscheidung:** Nicht im MVP, später als Feature.

### Q4: Multi-Direction Support?

**Aktuell:** Nur 1 Spawnpoint pro Map (vereinfacht).

**Java:** 4 Directions (N/E/S/W).

**Aufwand:** Groß (Path-Berechnung, UI für 4 Paths im Composer).

**Entscheidung:** Nicht im MVP, evtl. später als "Schwierigkeits-Steigerung".

---

## 8. Dependencies & Prerequisites

### Server-Side
- [x] Python 3.9+
- [x] `asyncio` event loop
- [x] `websockets` library
- [x] BattleService with tick() method (bereits vorhanden)

### Client-Side
- [x] Modern browser (Chrome 90+, Firefox 88+)
- [x] Canvas API
- [x] WebSocket API
- [ ] Optional: OffscreenCanvas (für Performance, nicht kritisch)

### Assets
- [ ] Critter sprites (32x32 PNG) – optional
- [ ] Sound effects (MP3/OGG) – optional
- [ ] Tower "fire" animation frames – optional

---

## 9. Risk Assessment

| Risiko | Wahrscheinlichkeit | Impact | Mitigation |
|--------|-------------------|--------|------------|
| **Performance bei >200 Critters** | Mittel | Hoch | Culling, batched rendering |
| **Shot-Tracking über Netzwerk** | Niedrig | Mittel | Shot-ID mit monotonic counter |
| **Hex-Grid Komplexität** | Niedrig | Niedrig | Bereits gut getestet |
| **WebSocket Message-Größe** | Niedrig | Mittel | Delta-Updates (nicht full state) |
| **Browser-Kompatibilität** | Niedrig | Niedrig | Canvas API ist weit supported |

---

## 10. Success Metrics

### Technical KPIs
- ✅ 60 FPS bei 100 Critters (< 16ms rendertime)
- ✅ < 250ms Latenz zwischen Server-Event und Client-Darstellung
- ✅ < 10KB WebSocket message size pro Broadcast

### Functional KPIs
- ✅ Critter bewegen sich smooth entlang Pfad
- ✅ Shots visible von Tower → Critter
- ✅ Health bars updateten in Echtzeit
- ✅ Battle-Ende zeigt Ergebnis an

### UX KPIs
- ✅ User versteht Battle-Flow ohne Tutorial
- ✅ Keine Confusion über State Machine States
- ✅ Battle fühlt sich "responsive" an

---

## 11. Appendix

### A. Code-Struktur

```
python_server/
├── src/gameserver/
│   ├── engine/
│   │   ├── battle_service.py      # ← Shots hinzufügen zu broadcast
│   │   └── attack_service.py      # State machine (TRAVELLING/SIEGE/BATTLE)
│   └── models/
│       ├── battle.py               # BattleState
│       └── shot.py                 # Shot dataclass
web/
├── js/
│   ├── lib/
│   │   ├── hex_grid.js             # ← Shot rendering hinzufügen
│   │   └── shot_visual.js          # ← NEU
│   └── views/
│       └── composer.js             # Battle event handlers
└── assets/
    └── critters/                   # ← NEU (optional)
        ├── spider.png
        └── ...
```

### B. Referenzen

- [BATTLE_ANALYSIS.md](/home/pi/e3/BATTLE_ANALYSIS.md) – Java vs. Python Vergleich
- [hex_grid.js](/home/pi/e3/web/js/lib/hex_grid.js) – Renderer
- [battle_service.py](/home/pi/e3/python_server/src/gameserver/engine/battle_service.py) – Tick logic

### C. Timing-Beispiel

| Zeit (ms) | Server Event | Client Reaction |
|-----------|--------------|-----------------|
| 0 | Battle starts | `battle_setup` → grid.clearBattle() |
| 15 | step_armies() spawns critter #1 | - |
| 30 | step_armies() spawns critter #2 | - |
| 250 | broadcast → `new_critters: [1, 2]` | addBattleCritter(1), addBattleCritter(2) |
| 266 | - | Client renders critter #1 at progress=0.032 |
| 500 | step_towers() fires shot → critter #1 | - |
| 750 | broadcast → `new_shots: [{...}]` | addBattleShot() |
| 1250 | step_shots() shot hits, critter #1 dies | - |
| 1500 | broadcast → `dead_critter_ids: [1]` | removeBattleCritter(1) |

---

**Ende des Plans**

Bereit zur Implementierung! 🚀
