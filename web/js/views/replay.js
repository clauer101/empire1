/**
 * Replay View — plays back recorded battle events.
 *
 * Observer-only mode: no palette, no tile clicking, no WebSocket.
 * Events are dispatched by timestamp using requestAnimationFrame.
 */

import { HexGrid, registerTileType } from '../lib/hex_grid.js';
import { hexKey } from '../lib/hex.js';
import { rest } from '../rest.js';

/** @type {import('../state.js').StateStore} */
let st;
/** @type {HTMLElement} */
let container;

/** @type {HexGrid|null} */
let grid = null;

// ── Playback state ──────────────────────────────────────────
let _events = [];
let _eventIdx = 0;
let _startTime = 0;       // performance.now() when playback started
let _pausedAt = 0;         // elapsed ms when paused
let _speed = 1;
let _playing = false;
let _finished = false;
let _totalMs = 0;
let _bid = null;
let _rafId = null;
let _resizeHandler = null;

// Structure colors (same as defense.js)
const STRUCTURE_COLORS = [
  { color: '#3a5a4a', stroke: '#4a7a5a' },
  { color: '#4a4a6a', stroke: '#5a5a8a' },
  { color: '#5a3a3a', stroke: '#7a4a4a' },
  { color: '#3a4a5a', stroke: '#4a6a7a' },
  { color: '#5a4a3a', stroke: '#7a6a4a' },
  { color: '#4a5a4a', stroke: '#6a7a6a' },
];

// ── View lifecycle ──────────────────────────────────────────

function init(el, _api, _state) {
  container = el;
  st = _state;

  container.innerHTML = `
    <div class="battle-view">
      <h2 class="battle-title" id="replay-title">📽 Replay</h2>

      <!-- Status Panel -->
      <div class="battle-status" id="replay-status">
        <div class="battle-status__item" style="grid-column:1/-1;">
          <div style="display:flex;justify-content:space-between;align-items:center;width:100%">
            <div>
              <span class="label">🛡 Defender</span>
              <span class="value" id="replay-defender" style="color:var(--accent)">-</span>
            </div>
            <div style="text-align:center">
              <span class="label">⚔ Army</span>
              <span class="value" id="replay-army">-</span>
            </div>
            <div style="text-align:right">
              <span class="label">⚔ Attacker</span>
              <span class="value" id="replay-attacker" style="color:var(--danger)">-</span>
            </div>
          </div>
        </div>
        <div class="battle-status__item" style="grid-column:1/-1;">
          <div style="display:flex;justify-content:space-between;align-items:center;width:100%">
            <div>
              <span class="label">Status</span>
              <span class="value" id="replay-status-text">Loading…</span>
            </div>
            <div style="text-align:right">
              <span class="label">Time</span>
              <span class="value" id="replay-elapsed">00:00 / 00:00</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Download Progress -->
      <div class="battle-status__item" id="replay-progress-wrap" style="grid-column:1/-1;display:none;">
        <div style="width:100%;">
          <div style="display:flex;justify-content:space-between;margin-bottom:4px;">
            <span class="label">Loading replay…</span>
            <span class="label" id="replay-progress-label"></span>
          </div>
          <div style="height:6px;background:var(--border,#333);border-radius:3px;overflow:hidden;">
            <div id="replay-progress-bar" style="height:100%;width:0%;background:var(--accent,#4fc3f7);border-radius:3px;transition:width 0.1s linear;"></div>
          </div>
        </div>
      </div>

      <!-- Playback Controls -->
      <div class="battle-status__item" style="grid-column:1/-1;">
        <div style="display:flex;gap:8px;align-items:center;justify-content:center;width:100%;">
          <button id="replay-play" style="flex:1;background:var(--accent,#4fc3f7);border:none;color:#fff;padding:8px 16px;border-radius:var(--radius,4px);font-size:1em;font-weight:bold;cursor:pointer;letter-spacing:0.5px;">▶ Play</button>
          <select id="replay-speed" style="width:56px;padding:6px 4px;border-radius:var(--radius,4px);border:1px solid var(--border,#333);background:var(--surface,#1e1e2e);color:var(--text,#eee);font-size:0.9em;">
            <option value="0.5">0.5×</option>
            <option value="1" selected>1×</option>
            <option value="2">2×</option>
            <option value="4">4×</option>
          </select>
        </div>
      </div>

      <!-- Canvas (full width, no palette) -->
      <div class="battle-view__body" style="grid-template-columns:1fr;">
        <div class="battle-canvas-wrap" id="replay-canvas-wrap">
          <canvas id="replay-canvas"></canvas>
        </div>
      </div>

      <!-- Summary Overlay -->
      <div class="battle-summary-overlay" id="replay-summary" style="display:none;">
        <div class="battle-summary-card">
          <h3 id="replay-summary-title">Battle Complete</h3>
          <div id="replay-summary-content"></div>
          <button id="replay-summary-close" class="btn-primary">Close</button>
        </div>
      </div>
    </div>
  `;

  const playBtn = container.querySelector('#replay-play');
  playBtn.disabled = true;
  playBtn.style.opacity = '0.4';
  playBtn.style.cursor = 'not-allowed';
  playBtn.addEventListener('click', _togglePlay);
  container.querySelector('#replay-speed').addEventListener('change', (e) => {
    const newSpeed = parseFloat(e.target.value) || 1;
    if (_playing) {
      // Capture current game-time position, then re-anchor _startTime so
      // elapsed stays continuous from this moment at the new speed.
      const current = _elapsedMs();
      _speed = newSpeed;
      _startTime = performance.now() - current / _speed;
    } else {
      // Paused: _pausedAt already holds the correct position; just update speed.
      _speed = newSpeed;
    }
  });
  container.querySelector('#replay-summary-close').addEventListener('click', () => {
    container.querySelector('#replay-summary').style.display = 'none';
  });
}

async function enter() {
  // Get battle ID from router param
  const hash = window.location.hash.replace('#', '');
  const slashIdx = hash.indexOf('/');
  _bid = slashIdx > 0 ? hash.substring(slashIdx + 1) : null;

  if (!_bid) {
    _setStatus('No replay ID specified');
    return;
  }

  _reset();
  _initCanvas();
  _setTitle(`📽 Replay — Battle #${_bid}`);
  _setStatus('Loading…');

  // Load structure tile types from items
  try {
    await rest.getItems();
  } catch (err) {
    // non-fatal
  }
  _registerStructureTileTypes();

  // Fetch replay data with progress tracking
  try {
    const data = await _fetchWithProgress(`/api/replays/${_bid}`, container);
    if (!data || !data.events || data.events.length === 0) {
      _setStatus('Replay not found or empty');
      return;
    }
    _events = data.events;
    _totalMs = _events[_events.length - 1].t || 0;

    // Immediately dispatch all t=0 events (battle_setup) so the map renders right away
    while (_eventIdx < _events.length && _events[_eventIdx].t <= 0) {
      _dispatchEvent(_events[_eventIdx]);
      _eventIdx++;
    }
    _pausedAt = 0;

    _setStatus('Ready — press Play');
    _updateTimeDisplay(0);
  } catch (err) {
    _setStatus(`Error: ${err.message}`);
  }
}

function leave() {
  _stopPlayback();
  if (_resizeHandler) {
    window.removeEventListener('resize', _resizeHandler);
    _resizeHandler = null;
  }
  if (grid) {
    grid.destroy();
    grid = null;
  }
}

// ── Canvas setup ────────────────────────────────────────────

function _initCanvas() {
  // Destroy previous grid to stop its render loop (prevents zombie rAF on same canvas)
  if (grid) { grid.destroy(); grid = null; }

  const wrap = container.querySelector('#replay-canvas-wrap');
  const canvas = container.querySelector('#replay-canvas');

  grid = new HexGrid({
    canvas,
    cols: 6,
    rows: 6,
    hexSize: 28,
    onTileClick: () => {},   // no interaction in replay
    onTileHover: null,
    onTileDrop: () => {},
  });

  // Clear the default 6×6 grid created by the constructor.
  // The actual map is loaded later from the replay data.
  grid.tiles.clear();
  grid._dirty = true;

  const updateSize = () => {
    const rect = wrap.getBoundingClientRect();
    canvas.style.width = rect.width + 'px';
    canvas.style.height = rect.height + 'px';
    grid._resize();
  };

  updateSize();
  _resizeHandler = updateSize;
  window.addEventListener('resize', _resizeHandler);
}

function _registerStructureTileTypes() {
  const items = st.items || {};
  const structures = items.structures || {};
  let colorIdx = 0;
  for (const [iid, info] of Object.entries(structures)) {
    const c = STRUCTURE_COLORS[colorIdx % STRUCTURE_COLORS.length];
    colorIdx++;
    registerTileType(iid, {
      label: info.name || iid,
      color: c.color,
      stroke: c.stroke,
      icon: null,
      spriteUrl: info.sprite ? '/' + info.sprite : null,
      serverData: info,
    });
  }
  if (grid) {
    grid._invalidateBase();
    grid._dirty = true;
  }
}

// ── Playback engine ─────────────────────────────────────────

function _reset() {
  _stopPlayback();
  _events = [];
  _eventIdx = 0;
  _pausedAt = 0;
  _playing = false;
  _finished = false;
  _totalMs = 0;
  _speed = 1;
  const sel = container.querySelector('#replay-speed');
  if (sel) sel.value = '1';
  const btn = container.querySelector('#replay-play');
  if (btn) btn.textContent = '▶ Play';
}

function _togglePlay() {
  if (_finished) {
    // Restart
    _eventIdx = 0;
    _pausedAt = 0;
    _finished = false;
    if (grid) grid.clearBattle();
    // Dispatch t=0 events (battle_setup) immediately
    while (_eventIdx < _events.length && _events[_eventIdx].t <= 0) {
      _dispatchEvent(_events[_eventIdx]);
      _eventIdx++;
    }
    _playing = true;
    _startTime = performance.now();
    container.querySelector('#replay-play').textContent = '⏸ Pause';
    container.querySelector('#replay-summary').style.display = 'none';
    _setStatus('⚔ Playing…');
    _tick();
    return;
  }

  if (_playing) {
    // Pause
    _pausedAt = _elapsedMs();
    _playing = false;
    if (_rafId) { cancelAnimationFrame(_rafId); _rafId = null; }
    container.querySelector('#replay-play').textContent = '▶ Play';
    _setStatus('⏸ Paused');
  } else {
    // Play / Resume
    _playing = true;
    _startTime = performance.now() - (_pausedAt / _speed);
    container.querySelector('#replay-play').textContent = '⏸ Pause';
    _setStatus('⚔ Playing…');
    _tick();
  }
}

function _stopPlayback() {
  _playing = false;
  if (_rafId) { cancelAnimationFrame(_rafId); _rafId = null; }
}

function _elapsedMs() {
  if (!_playing) return _pausedAt;
  return (performance.now() - _startTime) * _speed;
}

function _tick() {
  if (!_playing) return;

  const elapsed = _elapsedMs();
  _updateTimeDisplay(elapsed);

  // Dispatch all events up to current elapsed time
  while (_eventIdx < _events.length && _events[_eventIdx].t <= elapsed) {
    _dispatchEvent(_events[_eventIdx]);
    _eventIdx++;
  }

  // Check if finished
  if (_eventIdx >= _events.length) {
    _playing = false;
    _finished = true;
    container.querySelector('#replay-play').textContent = '↻ Replay';
    _setStatus('✓ Replay complete');
    return;
  }

  _rafId = requestAnimationFrame(_tick);
}

// ── Event dispatch ──────────────────────────────────────────

function _dispatchEvent(evt) {
  switch (evt.type) {
    case 'battle_setup':
      _onSetup(evt);
      break;
    case 'battle_update':
      _onUpdate(evt);
      break;
    case 'battle_summary':
      _onSummary(evt);
      break;
    case 'battle_status':
      _onStatus(evt);
      break;
  }
}

function _onSetup(msg) {
  // Enable play button now that the map is ready
  const playBtn = container.querySelector('#replay-play');
  if (playBtn) {
    playBtn.disabled = false;
    playBtn.style.opacity = '';
    playBtn.style.cursor = '';
  }

  if (grid) {
    grid.clearBattle();

    if (msg.tiles) {
      grid.fromJSON({ tiles: msg.tiles });
      grid.addVoidNeighbors();
      grid._centerGrid();
    }

    if (msg.path) {
      grid.setBattlePath(msg.path);
    }

    if (msg.structures) {
      for (const s of msg.structures) {
        const _meta = (s.select && s.select !== 'first') ? { select: s.select } : {};
        grid.setTile(s.q, s.r, s.iid, _meta);
        const tile = grid.tiles.get(hexKey(s.q, s.r));
        if (tile) {
          tile.sid = s.sid;
          tile.structure_data = s;
        }
      }
    }

    grid.battleActive = true;
    grid._dirty = true;

    _loadMapBackground();
  }

  // Update header
  const defName = msg.defender_name || 'Defender';
  const atkName = msg.attacker_name || 'Attacker';
  const armyName = msg.attacker_army_name || '';
  const defEl = container.querySelector('#replay-defender');
  const atkEl = container.querySelector('#replay-attacker');
  const armyEl = container.querySelector('#replay-army');
  if (defEl) defEl.textContent = defName;
  if (atkEl) atkEl.textContent = atkName;
  if (armyEl) armyEl.textContent = armyName || '-';
}

function _onUpdate(msg) {
  if (!grid) return;

  if (msg.critters && Array.isArray(msg.critters)) {
    const activeCids = new Set();
    for (const c of msg.critters) {
      grid.updateBattleCritter(c);
      activeCids.add(c.cid);
    }
    for (const cid of grid.battleCritters.keys()) {
      if (!activeCids.has(cid)) {
        grid.removeBattleCritter(cid);
      }
    }

    // Spawn flying icons for removed critters
    if (msg.removed_critters && Array.isArray(msg.removed_critters)) {
      for (const rc of msg.removed_critters) {
        if (rc.reason === 'died') {
          const raw = grid._getCritterPixelPos(rc.path_progress, grid.hexSize);
          const cx = raw.x * grid.zoom + grid.offsetX;
          const cy = raw.y * grid.zoom + grid.offsetY;
          const goldLabel = rc.value != null ? Math.round(rc.value) : null;
          _spawnFlyingIcon('/assets/sprites/hud/flying_coin.webp', cx, cy, goldLabel);
        } else if (rc.reason === 'reached') {
          const raw = grid._getCritterPixelPos(1.0, grid.hexSize);
          const cx = raw.x * grid.zoom + grid.offsetX;
          const cy = raw.y * grid.zoom + grid.offsetY;
          const dmgLabel = rc.damage != null ? `-${Math.round(rc.damage)}` : null;
          _spawnFlyingIcon('/assets/sprites/hud/flying_hearth.webp', cx, cy, dmgLabel, '#ef5350');
        }
      }
    }

    grid._dirty = true;
  }

  if (msg.shots && Array.isArray(msg.shots)) {
    const activeShotIds = new Set();
    for (const shot of msg.shots) {
      grid.updateBattleShot(shot);
      const shot_id = `${shot.source_sid}_${shot.target_cid}`;
      activeShotIds.add(shot_id);
    }
    for (const shot_id of grid.battleShots.keys()) {
      if (!activeShotIds.has(shot_id)) {
        grid.battleShots.delete(shot_id);
      }
    }
  }

  if (msg.defender_life != null) {
    grid.setDefenderLives(msg.defender_life, msg.defender_max_life);
  }

  grid._dirty = true;
}

function _onSummary(msg) {
  const won = msg.defender_won || false;
  const title = container.querySelector('#replay-summary-title');
  const content = container.querySelector('#replay-summary-content');

  title.textContent = won ? '🛡 Defender Victory' : '⚔ Attacker Victory';
  title.style.color = won ? 'var(--green, #4caf50)' : 'var(--red, #d32f2f)';
  content.innerHTML = '';

  // Keep critters visible briefly, then clean up
  setTimeout(() => { if (grid) grid.clearBattle(); }, 1500);

  container.querySelector('#replay-summary').style.display = 'flex';
}

function _onStatus(msg) {
  const defEl = container.querySelector('#replay-defender');
  const atkEl = container.querySelector('#replay-attacker');
  if (defEl && msg.defender_name) defEl.textContent = msg.defender_name;
  if (atkEl) {
    const army = msg.attacker_army_name || msg.attacker_name || '';
    const user = msg.attacker_username;
    atkEl.textContent = user ? `${army} (${user})` : army;
  }
}

// ── Map background ──────────────────────────────────────────

async function _loadMapBackground() {
  try {
    const res = await fetch('/api/maps');
    if (!res.ok) return;
    const { maps } = await res.json();
    if (maps && maps.length > 0 && grid) {
      await grid.setMapBackground(maps[0].url);
    }
  } catch (e) {
    console.warn('[Replay] map background not loaded:', e.message);
  }
}

// ── Flying HUD Icons ────────────────────────────────────────

function _spawnFlyingIcon(imgSrc, cx, cy, label, labelColor) {
  const wrap = container.querySelector('#replay-canvas-wrap');
  if (!wrap) return;
  const div = document.createElement('div');
  div.className = 'fly-wrap';
  div.style.left = cx + 'px';
  div.style.top  = cy + 'px';
  const img = document.createElement('img');
  img.src = imgSrc;
  img.className = 'fly-icon';
  div.appendChild(img);
  if (label != null) {
    const span = document.createElement('span');
    span.className = 'fly-label';
    if (labelColor) span.style.color = labelColor;
    span.textContent = (typeof label === 'string' && label.startsWith('-')) ? label : '+' + label;
    div.appendChild(span);
  }
  wrap.appendChild(div);
  div.addEventListener('animationend', () => div.remove());
}

// ── UI helpers ──────────────────────────────────────────────

function _setTitle(text) {
  const el = container.querySelector('#replay-title');
  if (el) el.textContent = text;
}

function _setStatus(text) {
  const el = container.querySelector('#replay-status-text');
  if (el) el.textContent = text;
}

function _updateTimeDisplay(elapsedMs) {
  const el = container.querySelector('#replay-elapsed');
  if (el) el.textContent = `${_fmtTime(elapsedMs)} / ${_fmtTime(_totalMs)}`;
}

function _fmtTime(ms) {
  const totalSec = Math.floor(Math.abs(ms) / 1000);
  const min = Math.floor(totalSec / 60);
  const sec = totalSec % 60;
  return `${String(min).padStart(2, '0')}:${String(sec).padStart(2, '0')}`;
}

// ── Fetch with progress ─────────────────────────────────────

async function _fetchWithProgress(url, scope) {
  const wrap = scope.querySelector('#replay-progress-wrap');
  const bar  = scope.querySelector('#replay-progress-bar');
  const lbl  = scope.querySelector('#replay-progress-label');

  if (wrap) wrap.style.display = '';

  const headers = {};
  const token = localStorage.getItem('e3_jwt_token');
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const fullUrl = rest.baseUrl ? `${rest.baseUrl}${url}` : url;
  const response = await fetch(fullUrl, { headers });
  if (!response.ok) throw new Error(`HTTP ${response.status}`);

  const total = parseInt(response.headers.get('Content-Length') || '0', 10);
  const isGzip = (response.headers.get('Content-Type') || '').includes('gzip');

  // Track compressed bytes from the raw body stream for accurate progress
  const rawReader = response.body.getReader();
  const compressedChunks = [];
  let received = 0;

  // Indeterminate animation when Content-Length is unknown
  let indeterminateId = null;
  if (!total && bar) {
    let pos = 0;
    indeterminateId = setInterval(() => {
      pos = (pos + 2) % 100;
      bar.style.width = '20%';
      bar.style.marginLeft = pos + '%';
    }, 30);
  }

  while (true) {
    const { done, value } = await rawReader.read();
    if (done) break;
    compressedChunks.push(value);
    received += value.length;
    if (total && bar) {
      const pct = Math.min(100, Math.round(received / total * 100));
      bar.style.width = pct + '%';
      if (lbl) lbl.textContent = `${_fmtBytes(received)} / ${_fmtBytes(total)}`;
    } else if (lbl) {
      lbl.textContent = _fmtBytes(received);
    }
  }

  if (indeterminateId) {
    clearInterval(indeterminateId);
    bar.style.marginLeft = '0';
  }
  if (bar) bar.style.width = '100%';
  if (wrap) wrap.style.display = 'none';

  // Reassemble compressed bytes
  const compressed = new Uint8Array(received);
  let offset = 0;
  for (const chunk of compressedChunks) { compressed.set(chunk, offset); offset += chunk.length; }

  // Decompress if needed, then parse JSON
  let jsonBytes;
  if (isGzip && typeof DecompressionStream !== 'undefined') {
    const ds = new DecompressionStream('gzip');
    const writer = ds.writable.getWriter();
    const outChunks = [];
    const outReader = ds.readable.getReader();
    const pump = async () => {
      while (true) {
        const { done, value } = await outReader.read();
        if (done) break;
        outChunks.push(value);
      }
    };
    const pumpPromise = pump();
    await writer.write(compressed);
    await writer.close();
    await pumpPromise;
    let total2 = 0;
    for (const c of outChunks) total2 += c.length;
    jsonBytes = new Uint8Array(total2);
    let off2 = 0;
    for (const c of outChunks) { jsonBytes.set(c, off2); off2 += c.length; }
  } else {
    jsonBytes = compressed;
  }
  return JSON.parse(new TextDecoder().decode(jsonBytes));
}

function _fmtBytes(n) {
  if (n < 1024) return n + ' B';
  if (n < 1024 * 1024) return (n / 1024).toFixed(1) + ' KB';
  return (n / (1024 * 1024)).toFixed(1) + ' MB';
}

// ── Export ──────────────────────────────────────────────────

export default {
  id: 'replay',
  title: 'Replay',
  init,
  enter,
  leave,
};
