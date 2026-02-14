/**
 * Battle View — dedicated real-time tower defense battle display.
 *
 * Features:
 *  - Hex grid canvas with autonomous critter movement
 *  - Shot visualization (tower → critter)
 *  - Health bars and effect overlays (burn, slow)
 *  - Battle status panel (waves, score, timer)
 *  - Full-screen optimized layout
 *
 * Architecture:
 *  Server sends delta updates (spawn/die/fire events) every 250ms.
 *  Client autonomously interpolates critter movement along paths.
 *
 * WebSocket lifecycle:
 *  - WS connects only when battle view is entered
 *  - WS disconnects when leaving the battle view
 *  - WS disconnects on mobile screen-off (visibility hidden)
 *  - WS reconnects on mobile screen-on if still on battle view
 */

import { HexGrid, getTileType, registerTileType } from '../lib/hex_grid.js';
import { hexKey } from '../lib/hex.js';
import { eventBus } from '../events.js';
import { rest } from '../rest.js';

/** @type {import('../state.js').StateStore} */
let st;
/** @type {HTMLElement} */
let container;
let _unsub = [];

/** @type {HexGrid|null} */
let grid = null;

// ── Battle WebSocket ────────────────────────────────────────

/** @type {WebSocket|null} */
let _ws = null;
let _wsUrl = '';
let _wsConnected = false;
let _wsReconnectTimer = null;
let _wsIntentionalClose = false;

let _wsConnectTimeout = null;

/**
 * Connect the battle WebSocket (with JWT token).
 * Only called from enter() or mobile wake-up.
 */
function _wsConnect() {
  if (_ws && (_ws.readyState === WebSocket.OPEN || _ws.readyState === WebSocket.CONNECTING)) {
    return;  // already connected or connecting
  }

  _wsIntentionalClose = false;

  // Build WS URL — use same host:port as REST API, path /ws
  const restBase = rest.baseUrl || `http://${window.location.hostname}:8080`;
  const restUrl = new URL(restBase);
  const wsProto = restUrl.protocol === 'https:' ? 'wss:' : 'ws:';
  const baseUrl = `${wsProto}//${restUrl.host}/ws`;
  _wsUrl = rest.getAuthenticatedWsUrl(baseUrl);

  _addDebugLog(`🔌 WS connecting to ${baseUrl}...`);
  let ws;
  try {
    ws = new WebSocket(_wsUrl);
  } catch (err) {
    _addDebugLog(`❌ WS constructor error: ${err.message}`);
    return;
  }
  _ws = ws;

  // Connection timeout — mobile browsers may hang without firing error/close
  _wsConnectTimeout = setTimeout(() => {
    if (ws.readyState === WebSocket.CONNECTING) {
      _addDebugLog(`⏱ WS timeout after 8s (still CONNECTING) — closing`);
      ws.close();
    }
  }, 8000);

  ws.addEventListener('open', () => {
    clearTimeout(_wsConnectTimeout);
    _wsConnected = true;
    _addDebugLog('🟢 WS connected');
    _updateWsIndicator(true);

    // Register for battle updates
    _sendWs({ type: 'battle_register', target_uid: st.summary?.uid });
  });

  ws.addEventListener('message', (ev) => {
    let msg;
    try {
      msg = JSON.parse(ev.data);
    } catch (err) {
      console.warn('[Battle.WS] invalid JSON:', ev.data);
      return;
    }
    _handleWsMessage(msg);
  });

  ws.addEventListener('close', (ev) => {
    clearTimeout(_wsConnectTimeout);
    _wsConnected = false;
    _updateWsIndicator(false);
    _addDebugLog(`🔴 WS closed (code=${ev.code} reason=${ev.reason || 'none'})`);

    if (!_wsIntentionalClose) {
      // Auto-reconnect after 2s if not intentionally closed
      _wsReconnectTimer = setTimeout(() => _wsConnect(), 2000);
    }
    _ws = null;
  });

  ws.addEventListener('error', (ev) => {
    clearTimeout(_wsConnectTimeout);
    _addDebugLog(`⚠ WS error (readyState=${ws.readyState}, url=${baseUrl})`);
  });
}

/**
 * Close the battle WebSocket intentionally (no auto-reconnect).
 */
function _wsDisconnect() {
  _wsIntentionalClose = true;
  if (_wsConnectTimeout) {
    clearTimeout(_wsConnectTimeout);
    _wsConnectTimeout = null;
  }
  if (_wsReconnectTimer) {
    clearTimeout(_wsReconnectTimer);
    _wsReconnectTimer = null;
  }
  if (_ws) {
    // Unregister from battle before closing
    _sendWs({ type: 'battle_unregister', target_uid: st.summary?.uid });
    _ws.close(1000, 'leaving-battle');
    _ws = null;
    _wsConnected = false;
    _addDebugLog('🔌 WS disconnected (intentional)');
    _updateWsIndicator(false);
  }
}

/**
 * Send a JSON message over the battle WS.
 * @param {object} msg
 */
function _sendWs(msg) {
  if (_ws && _ws.readyState === WebSocket.OPEN) {
    if (st.auth?.uid) msg.sender = st.auth.uid;
    _ws.send(JSON.stringify(msg));
  }
}

/**
 * Handle incoming WS message — dispatch battle events.
 */
function _handleWsMessage(msg) {
  switch (msg.type) {
    case 'welcome':
      _addDebugLog(`WS welcome: guest_uid=${msg.temp_uid}`);
      break;
    case 'battle_setup':
      _onBattleSetup(msg);
      break;
    case 'battle_update':
      _onBattleUpdate(msg);
      break;
    case 'battle_summary':
      _onBattleSummary(msg);
      break;
    case 'battle_status':
      _onBattleStatus(msg);
      break;
    case 'attack_phase_changed':
      _addDebugLog(`Phase changed: attack_id=${msg.attack_id} → ${msg.new_phase}`);
      break;
    default:
      // Ignore non-battle messages
      break;
  }
}

/**
 * Update the WS status indicator in the status bar.
 */
function _updateWsIndicator(online) {
  const el = document.getElementById('ws-status-indicator');
  if (el) {
    el.classList.toggle('connected', online);
    el.classList.toggle('disconnected', !online);
    el.title = online ? 'Battle WS: connected' : 'Battle WS: disconnected';
  }
}

// ── Mobile visibility lifecycle ─────────────────────────────

/**
 * On mobile screen-off: close WS immediately.
 * On mobile screen-on: reconnect if still on battle view.
 */
function _onVisibilityChange() {
  if (document.visibilityState === 'hidden') {
    if (_wsConnected) {
      _addDebugLog('📱 Screen off → closing WS');
      _wsDisconnect();
    }
  } else if (document.visibilityState === 'visible') {
    if (!_wsConnected && !_wsIntentionalClose) {
      _addDebugLog('📱 Screen on → reconnecting WS');
      _wsConnect();
    }
  }
}

// Battle state
let _battleState = {
  active: false,
  bid: null,
  defender_uid: null,
  defender_name: '',
  attacker_uids: [],
  attacker_name: '',
  wave_count: 0,
  elapsed_ms: 0,
  is_finished: false,
  defender_won: null,
  phase: 'waiting',
  current_wave: null,
  current_wave_id: -1,  // Track wave_id to detect wave changes
  next_wave: null,
  total_waves: 0,
  time_since_start_s: 0,
  current_wave_spawned: 0,  // Track critters spawned in current wave
  next_wave_countdown_ms: 0,  // Time until next wave
};

// Debug log buffer
let _debugLogs = [];
const MAX_DEBUG_LOGS = 20;

function _addDebugLog(msg) {
  const timestamp = new Date().toLocaleTimeString();
  const logEntry = `[${timestamp}] ${msg}`;
  _debugLogs.unshift(logEntry);
  if (_debugLogs.length > MAX_DEBUG_LOGS) {
    _debugLogs.pop();
  }
  console.log('[Battle.DEBUG]', msg);
  _updateDebugPanel();
}

function _updateDebugPanel() {
  const panel = container?.querySelector('#battle-debug-panel');
  if (!panel) return;
  const logList = panel.querySelector('#battle-debug-logs');
  if (!logList) return;
  logList.innerHTML = _debugLogs.map(log => `<div style="font-size:11px;padding:2px 0;font-family:monospace;color:#4a4">${log}</div>`).join('');
}

// Structure colors for dynamic tile types
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
  // api parameter is no longer used — battle manages its own WS
  st = _state;

  container.innerHTML = `
    <div class="battle-view">
      <div class="battle-header">
        <h2 class="battle-title">⚔ Battle</h2>
        <div class="battle-actions">
          <button id="battle-exit" class="btn-ghost btn-sm" title="Exit to dashboard">Exit</button>
        </div>
      </div>

      <!-- Battle Status Panel -->
      <div class="battle-status" id="battle-status">
        <div class="battle-status__item" style="grid-column: 1 / -1;">
          <div style="display:flex; justify-content:space-between; align-items:center; width:100%">
            <div>
              <span class="label">Defender</span>
              <span class="value" id="battle-defender" style="color:var(--accent)">-</span>
            </div>
            <div style="text-align:right">
              <span class="label">Attacker</span>
              <span class="value" id="battle-attacker" style="color:var(--danger)">-</span>
            </div>
          </div>
        </div>
        <div class="battle-status__item">
          <span class="label">Status</span>
          <span class="value" id="battle-status-text">Waiting...</span>
        </div>
        <div class="battle-status__item">
          <span class="label">Time</span>
          <span class="value" id="battle-elapsed">00:00</span>
        </div>
        <div class="battle-status__item" style="grid-column: 1 / -1;">
          <div style="display:flex; justify-content:space-between; align-items:center; width:100%">
            <span class="label">Current Wave</span>
            <span class="value" id="battle-current-wave">-</span>
          </div>
        </div>
        <div class="battle-status__item" style="grid-column: 1 / -1;">
          <div style="display:flex; justify-content:space-between; align-items:center; width:100%">
            <span class="label">Next Wave</span>
            <span class="value" id="battle-next-wave">-</span>
          </div>
        </div>
      </div>

      <!-- Canvas Container -->
      <div class="battle-canvas-wrap" id="canvas-wrap">
        <canvas id="battle-canvas"></canvas>
      </div>

      <!-- Battle Summary Overlay (hidden initially) -->
      <div class="battle-summary-overlay" id="battle-summary" style="display:none;">
        <div class="battle-summary-card">
          <h3 id="summary-title">Battle Complete</h3>
          <div id="summary-content"></div>
          <button id="summary-close" class="btn-primary">Close</button>
        </div>
      </div>

      <!-- Debug Panel -->
      <div id="battle-debug-panel" style="position:absolute;bottom:12px;right:12px;width:300px;background:rgba(0,0,0,0.85);border:1px solid #4a4;border-radius:4px;padding:8px;max-height:200px;overflow-y:auto;z-index:999;">
        <div style="font-size:12px;font-weight:bold;color:#4a4;margin-bottom:4px;">⚙ Battle Debug</div>
        <div id="battle-debug-logs" style="font-family:monospace;color:#4a4;font-size:10px;"></div>
      </div>
    </div>
  `;

  // Bind exit button
  container.querySelector('#battle-exit').addEventListener('click', () => {
    if (_battleState.active && !_battleState.is_finished) {
      if (!confirm('Battle is still ongoing. Are you sure you want to leave?')) {
        return;
      }
    }
    window.location.hash = '#dashboard';
  });

  // Bind summary close button
  container.querySelector('#summary-close').addEventListener('click', () => {
    container.querySelector('#battle-summary').style.display = 'none';
    window.location.hash = '#dashboard';
  });
}

async function enter() {
  _debugLogs = [];  // Clear previous debug logs
  _initCanvas();

  // Subscribe to items for structure tile types
  _unsub.push(eventBus.on('state:items', _registerStructureTileTypes));

  // Load items to get structure tiles (via REST)
  try {
    await rest.getItems();
  } catch (err) {
    console.warn('[Battle] could not load items:', err.message);
  }

  _registerStructureTileTypes();

  // Connect battle WebSocket
  _wsConnect();

  // Listen for mobile screen on/off
  document.addEventListener('visibilitychange', _onVisibilityChange);
  _unsub.push(() => document.removeEventListener('visibilitychange', _onVisibilityChange));

  // Start status update loop
  _startStatusLoop();
}

function leave() {
  _unsub.forEach(fn => fn());
  _unsub = [];
  if (grid) {
    grid.destroy();
    grid = null;
  }
  _stopStatusLoop();

  // Disconnect battle WebSocket
  _wsDisconnect();
}

// ── Canvas initialization ───────────────────────────────────

function _initCanvas() {
  const wrap = container.querySelector('#canvas-wrap');
  const canvas = container.querySelector('#battle-canvas');

  grid = new HexGrid({
    canvas,
    cols: 8,
    rows: 8,
    hexSize: 32,
    onTileClick: null,  // Read-only during battle
    onTileHover: null,
    onTileDrop: null,
  });

  // Set explicit dimensions for full canvas area
  const updateSize = () => {
    const rect = wrap.getBoundingClientRect();
    canvas.style.width = rect.width + 'px';
    canvas.style.height = rect.height + 'px';
    grid._resize();
  };

  updateSize();
  window.addEventListener('resize', updateSize);
  _unsub.push(() => window.removeEventListener('resize', updateSize));
}

function _registerStructureTileTypes() {
  const items = st.items || {};
  const structures = items.structures || {};

  let colorIdx = 0;
  for (const [iid, info] of Object.entries(structures)) {
    const colorDef = STRUCTURE_COLORS[colorIdx % STRUCTURE_COLORS.length];
    colorIdx++;
    registerTileType(iid, {
      label: info.name || iid,
      color: colorDef.color,
      stroke: colorDef.stroke,
      icon: '🗼',
      serverData: info,
    });
  }
}

// ── Battle Events ───────────────────────────────────────────

function _onBattleStatus(msg) {
  if (!msg) return;
  
  // Log phase changes
  if (_battleState.phase !== (msg.phase || 'waiting')) {
    _addDebugLog(`Phase: ${_battleState.phase} → ${msg.phase || 'waiting'}`);
  }
  
  // Update battle state
  _battleState.phase = msg.phase || 'waiting';
  _battleState.defender_uid = msg.defender_uid;
  _battleState.defender_name = msg.defender_name || 'Unknown';
  _battleState.attacker_uid = msg.attacker_uid;
  _battleState.attacker_name = msg.attacker_name || 'Unknown';
  _battleState.time_since_start_s = msg.time_since_start_s || 0;
  
  // Update status display
  _updateStatusFromBattleMsg();
}

function _onBattleSetup(msg) {
  console.log('[Battle] Battle setup:', msg);
  _addDebugLog(`🎮 Battle Setup: ${msg.defender_name} vs ${msg.attacker_name}`);

  // Reset state
  _battleState = {
    active: true,
    bid: msg.bid || null,
    defender_uid: msg.defender_uid || null,
    defender_name: '',
    attacker_uids: msg.attacker_uids || [],
    attacker_name: '',
    wave_count: 0,
    elapsed_ms: 0,
    is_finished: false,
    defender_won: null,
    phase: 'waiting',
    time_since_start_s: 0,
  };

  // Clear previous battle
  grid.clearBattle();

  // Load battle map
  if (msg.tiles) {
    grid.fromJSON({ tiles: msg.tiles });
    grid.addVoidNeighbors();
    grid._centerGrid();
  }

  // Place structures (towers)
  if (msg.structures) {
    for (const s of msg.structures) {
      const key = hexKey(s.q, s.r);
      grid.setTile(s.q, s.r, s.iid);
      const tile = grid.tiles.get(key);
      if (tile) {
        tile.sid = s.sid;
        tile.structure_data = s;
      }
    }
  }

  grid.battleActive = true;
  grid._dirty = true;

  // Update status
  _updateStatus('Battle starting...');
}

function _onBattleUpdate(msg) {
  if (!msg) return;

  // Spawn new critters (client will autonomously move them along path)
  if (msg.new_critters && msg.new_critters.length > 0) {
    _addDebugLog(`👹 ${msg.new_critters.length} critters spawned`);
    for (const c of msg.new_critters) {
      console.log(
        '[Battle] Critter spawned: cid=%d type=%s speed=%.1f path_len=%d',
        c.cid, c.iid, c.speed || 0, c.path ? c.path.length : 0
      );
      grid.addBattleCritter(c.cid, c.path, c.speed);
      _battleState.wave_count++;
      // Note: current_wave_spawned is updated from battle_status, not here
    }
  }

  // Remove dead critters
  if (msg.dead_critter_ids && msg.dead_critter_ids.length > 0) {
    _addDebugLog(`💀 ${msg.dead_critter_ids.length} critters killed`);
    for (const cid of msg.dead_critter_ids) {
      console.log('[Battle] Critter killed: cid=%d', cid);
      grid.removeBattleCritter(cid);
    }
  }

  // Remove finished critters (reached castle)
  if (msg.finished_critter_ids && msg.finished_critter_ids.length > 0) {
    _addDebugLog(`🏰 ${msg.finished_critter_ids.length} critters reached castle`);
    for (const cid of msg.finished_critter_ids) {
      console.log('[Battle] Critter finished: cid=%d', cid);
      grid.removeBattleCritter(cid);
    }
  }

  // Shots (TODO: Phase 3 - Shot visualization)
  if (msg.new_shots && msg.new_shots.length > 0) {
    console.log('[Battle] Shots fired: count=%d', msg.new_shots.length);
    // TODO: grid.addBattleShot(shot)
  }

  grid._dirty = true;
  // Status is updated by battle_status messages, not by battle_update
}

function _onBattleSummary(msg) {
  console.log('[Battle] Battle summary:', msg);
  const result = msg.defender_won ? '🎉 Victory' : '💀 Defeat';
  _addDebugLog(`⚔ Battle Finished: ${result}`);

  _battleState.is_finished = true;
  _battleState.defender_won = msg.defender_won || false;
  _battleState.active = false;

  // Keep critters visible briefly, then clean up
  setTimeout(() => {
    grid.clearBattle();
  }, 1500);

  // Show summary overlay
  _showSummary(msg);
  _updateStatus('Battle complete!');
}

// ── Status Updates ──────────────────────────────────────────

let _statusLoopId = null;

function _startStatusLoop() {
  _statusLoopId = setInterval(() => {
    if (_battleState.active) {
      _battleState.elapsed_ms += 100;
    }
    _updateStatusPanel();
  }, 100);
}

function _stopStatusLoop() {
  if (_statusLoopId) {
    clearInterval(_statusLoopId);
    _statusLoopId = null;
  }
}

function _updateStatus(text) {
  const el = container.querySelector('#battle-status-text');
  if (el) el.textContent = text;
}

function _updateStatusPanel() {
  const critterCount = grid ? grid.battleCritters.size : 0;

  const elapsedEl = container.querySelector('#battle-elapsed');
  if (elapsedEl) elapsedEl.textContent = _formatTime(_battleState.time_since_start_s * 1000);
}

function _updateStatusFromBattleMsg() {
  // Update defender/attacker names
  const defenderEl = container.querySelector('#battle-defender');
  const attackerEl = container.querySelector('#battle-attacker');
  
  if (defenderEl) defenderEl.textContent = _battleState.defender_name || '-';
  if (attackerEl) attackerEl.textContent = _battleState.attacker_name || '-';
  
  // Update phase
  let statusText = 'Waiting...';
  if (_battleState.phase === 'in_siege') {
    statusText = '🛡 Siege';
  } else if (_battleState.phase === 'in_battle') {
    statusText = '⚔ Battle';
  } else if (_battleState.phase === 'finished') {
    statusText = '✓ Complete';
  }
  _updateStatus(statusText);
  
  // Update current wave with critter counter
  const currentWaveEl = container.querySelector('#battle-current-wave');
  if (currentWaveEl) {
    if (_battleState.current_wave) {
      const w = _battleState.current_wave;
      const spawned = _battleState.current_wave_spawned;
      const total = w.slots;
      currentWaveEl.textContent = `${w.critter_iid} (${spawned}/${total})`;
    } else {
      // All waves finished
      currentWaveEl.textContent = 'done';
    }
  }
  
  // Update next wave with countdown
  const nextWaveEl = container.querySelector('#battle-next-wave');
  if (nextWaveEl) {
    if (_battleState.next_wave) {
      const w = _battleState.next_wave;
      const countdown = _battleState.next_wave_countdown_ms;
      const timeStr = countdown > 0 ? ` in ${_formatTime(countdown)}` : '';
      nextWaveEl.textContent = `${w.critter_iid} x${w.slots}${timeStr}`;
    } else {
      nextWaveEl.textContent = '-';
    }
  }
  
  // Update time
  const elapsedEl = container.querySelector('#battle-elapsed');
  if (elapsedEl) {
    elapsedEl.textContent = _formatTime(_battleState.time_since_start_s * 1000);
  }
}

function _formatTime(ms) {
  const totalSec = Math.floor(Math.abs(ms) / 1000);
  const min = Math.floor(totalSec / 60);
  const sec = totalSec % 60;
  const sign = ms < 0 ? '-' : '';
  return `${sign}${String(min).padStart(2, '0')}:${String(sec).padStart(2, '0')}`;
}

// ── Summary Overlay ─────────────────────────────────────────

function _showSummary(msg) {
  const overlay = container.querySelector('#battle-summary');
  const title = container.querySelector('#summary-title');
  const content = container.querySelector('#summary-content');

  const won = msg.defender_won || false;
  title.textContent = won ? '🎉 Victory!' : '💀 Defeat';
  title.style.color = won ? 'var(--green, #4caf50)' : 'var(--red, #d32f2f)';

  let html = '<div style="text-align:center;margin-top:16px">';

  if (won) {
    html += '<p>You successfully defended your empire!</p>';
  } else {
    html += '<p>Your defenses were overrun...</p>';
  }

  // Losses/Gains
  if (msg.defender_losses) {
    html += '<div style="margin-top:16px"><strong>Losses:</strong><ul style="list-style:none;padding:0">';
    for (const [res, val] of Object.entries(msg.defender_losses)) {
      html += `<li>${res}: ${Math.round(val)}</li>`;
    }
    html += '</ul></div>';
  }

  if (msg.attacker_gains && Object.keys(msg.attacker_gains).length > 0) {
    html += '<div style="margin-top:16px"><strong>Attacker Gains:</strong><ul style="list-style:none;padding:0">';
    for (const [uid, gains] of Object.entries(msg.attacker_gains)) {
      html += `<li>Player ${uid}: ${JSON.stringify(gains)}</li>`;
    }
    html += '</ul></div>';
  }

  html += '</div>';
  content.innerHTML = html;
  overlay.style.display = 'flex';
}

// ── Export ──────────────────────────────────────────────────

export default {
  id: 'battle',
  title: 'Battle',
  init,
  enter,
  leave,
};
