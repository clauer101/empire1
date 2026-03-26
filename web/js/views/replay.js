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
    _speed = parseFloat(e.target.value) || 1;
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

  // Fetch replay data
  try {
    const data = await rest.getReplay(_bid);
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

// ── Export ──────────────────────────────────────────────────

export default {
  id: 'replay',
  title: 'Replay',
  init,
  enter,
  leave,
};
