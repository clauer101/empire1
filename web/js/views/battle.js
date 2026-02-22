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
import { debug } from '../debug.js';

/** @type {import('../state.js').StateStore} */
let st;
/** @type {HTMLElement} */
let container;
let _unsub = [];

/** @type {HexGrid|null} */
let grid = null;

/** @type {number|null} attack_id of the pending incoming attack (set from dashboard) */
let _pendingAttackId = null;

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
  
  // Show/hide based on debug mode
  panel.style.display = debug.enabled ? 'block' : 'none';
  if (!debug.enabled) return;
  
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
        <div class="battle-status__item" style="grid-column: 1 / -1;">
          <div style="display:flex; justify-content:space-between; align-items:center; width:100%">
            <div>
              <span class="label">Status</span>
              <span class="value" id="battle-status-text">Waiting...</span>
            </div>
            <div style="text-align:right">
              <span class="label">Time</span>
              <span class="value" id="battle-elapsed">00:00</span>
            </div>
          </div>
        </div>
        <div class="battle-status__item" style="grid-column: 1 / -1;">
          <div style="display:flex; justify-content:space-between; align-items:center; width:100%">
            <span class="label">Next Wave</span>
            <span class="value" id="battle-next-wave">-</span>
          </div>
        </div>
        <div class="battle-status__item" id="fight-now-item" style="display:none;grid-column: 1 / -1;">
          <button id="fight-now-btn" style="width:100%;background:var(--danger,#e53935);border:none;color:#fff;padding:8px 16px;border-radius:var(--radius,4px);font-size:1em;font-weight:bold;cursor:pointer;letter-spacing:0.5px;">⚔ Fight now!</button>
        </div>
      </div>

      <!-- Battle Body (Canvas + Props Panel) -->
      <div class="battle-view__body">
        <!-- Canvas Container -->
        <div class="battle-canvas-wrap" id="canvas-wrap">
          <canvas id="battle-canvas"></canvas>
        </div>

        <!-- Tower Properties Panel (Desktop only) -->
        <aside class="battle-view__props" id="tower-props">
          <div class="panel">
            <div class="panel-header">Tower Details</div>
            <div id="tower-props-content" class="props-empty">
              Click a tower to inspect
            </div>
          </div>
        </aside>
      </div>

      <!-- Battle Summary Overlay (hidden initially) -->
      <div class="battle-summary-overlay" id="battle-summary" style="display:none;">
        <div class="battle-summary-card">
          <h3 id="summary-title">Battle Complete</h3>
          <div id="summary-content"></div>
          <button id="summary-close" class="btn-primary">Close</button>
        </div>
      </div>

      <!-- Tower Details Overlay -->
      <div class="tile-overlay" id="tower-overlay" style="display:none;">
        <div class="tile-overlay__content">
          <div class="tile-overlay__header">
            <h3>Tower Details</h3>
            <button class="tile-overlay__close" id="tower-overlay-close">✕</button>
          </div>
          <div class="tile-overlay__body" id="tower-overlay-body">
          </div>
        </div>
      </div>

      <!-- Debug Panel -->
      <div id="battle-debug-panel" style="position:absolute;bottom:12px;right:12px;width:300px;background:rgba(0,0,0,0.85);border:1px solid #4a4;border-radius:4px;padding:8px;max-height:200px;overflow-y:auto;z-index:999;">
        <div style="font-size:12px;font-weight:bold;color:#4a4;margin-bottom:4px;">⚙ Battle Debug</div>
        <div id="battle-debug-logs" style="font-family:monospace;color:#4a4;font-size:10px;"></div>
      </div>
    </div>
  `;

  // Bind summary close button
  container.querySelector('#summary-close').addEventListener('click', () => {
    container.querySelector('#battle-summary').style.display = 'none';
    window.location.hash = '#dashboard';
  });

  // Bind Fight now! button (visible only during in_siege when navigated from dashboard)
  container.querySelector('#fight-now-btn').addEventListener('click', async () => {
    const btn = container.querySelector('#fight-now-btn');
    if (!_pendingAttackId) return;
    btn.disabled = true;
    btn.textContent = 'Sending...';
    try {
      const resp = await rest.skipSiege(_pendingAttackId);
      if (resp.success) {
        btn.textContent = '✓ Siege ended!';
        setTimeout(() => {
          btn.textContent = '⚔ Fight now!';
          btn.disabled = false;
        }, 3000);
      } else {
        btn.textContent = `✗ ${resp.error || 'Error'}`;
        setTimeout(() => {
          btn.textContent = '⚔ Fight now!';
          btn.disabled = false;
        }, 2500);
      }
    } catch (err) {
      btn.textContent = '✗ Request failed';
      setTimeout(() => {
        btn.textContent = '⚔ Fight now!';
        btn.disabled = false;
      }, 2500);
    }
  });

  // Bind tower overlay
  _bindTowerOverlay();
}

function _bindTowerOverlay() {
  const closeBtn = container.querySelector('#tower-overlay-close');
  const overlay = container.querySelector('#tower-overlay');
  
  if (closeBtn) {
    closeBtn.addEventListener('click', () => {
      overlay.style.display = 'none';
    });
  }
  
  // Close on backdrop click
  if (overlay) {
    overlay.addEventListener('click', (e) => {
      if (e.target === overlay) {
        overlay.style.display = 'none';
      }
    });
  }
}

function _showTowerDetails(q, r, tile) {
  const overlayBody = container.querySelector('#tower-overlay-body');
  const overlay = container.querySelector('#tower-overlay');
  const propsContent = container.querySelector('#tower-props-content');
  
  if (!tile) {
    return;
  }

  const t = getTileType(tile.type);

  // Build tower info from server data
  let towerInfo = '';
  if (t.serverData) {
    const s = t.serverData;
    towerInfo = 
      '<div class="props-divider"></div>' +
      '<div class="props-section-label">Tower Stats</div>' +
      '<div class="props-row"><span class="label">Damage</span><span class="value">' + (s.damage || 0) + '</span></div>' +
      '<div class="props-row"><span class="label">Range</span><span class="value">' + (s.range || 0) + ' hex</span></div>' +
      '<div class="props-row"><span class="label">Reload</span><span class="value">' + (s.reload_time_ms || 0) + ' ms</span></div>' +
      '<div class="props-row"><span class="label">Shot Speed</span><span class="value">' + (s.shot_speed || 0) + ' hex/s</span></div>' +
      '<div class="props-row"><span class="label">Shot Type</span><span class="value">' + (s.shot_type || 'normal') + '</span></div>';
    if (s.effects && Object.keys(s.effects).length > 0) {
      const effectsStr = Object.entries(s.effects).map(([k, v]) => k + ': ' + v).join(', ');
      towerInfo += '<div class="props-row"><span class="label">Effects</span><span class="value">' + effectsStr + '</span></div>';
    }
    if (s.requirements && s.requirements.length > 0) {
      towerInfo += '<div class="props-row"><span class="label">Requires</span><span class="value" style="font-size:10px;">' + s.requirements.join(', ') + '</span></div>';
    }
  } else {
    // Not a tower tile, don't show anything
    return;
  }

  const detailsHTML = 
    '<div class="props-tile">' +
      '<div class="props-row">' +
        '<span class="label">Position</span>' +
        '<span class="value mono">' + q + ', ' + r + '</span>' +
      '</div>' +
      '<div class="props-row">' +
        '<span class="label">Type</span>' +
        '<span class="value">' +
          '<span class="palette-swatch--sm" style="background:' + t.color + ';border-color:' + t.stroke + '"></span>' +
          t.label +
        '</span>' +
      '</div>' +
      '<div class="props-row">' +
        '<span class="label">Key</span>' +
        '<span class="value mono">' + hexKey(q, r) + '</span>' +
      '</div>' +
      towerInfo +
    '</div>';
  
  // Update desktop props panel
  if (propsContent) {
    propsContent.innerHTML = detailsHTML;
  }
  
  // Update mobile overlay
  if (overlayBody) {
    overlayBody.innerHTML = detailsHTML;
    // Show overlay only on mobile
    if (window.innerWidth <= 1100) {
      overlay.style.display = 'flex';
    }
  }
}

async function enter() {
  _debugLogs = [];  // Clear previous debug logs
  _updateDebugPanel();  // Initialize debug panel visibility
  _initCanvas();

  // Check if navigated from dashboard for a specific incoming attack
  if (st.pendingIncomingAttack) {
    _pendingAttackId = st.pendingIncomingAttack.attack_id;
    st.pendingIncomingAttack = null;
  }

  // Subscribe to items for structure tile types
  _unsub.push(eventBus.on('state:items', _registerStructureTileTypes));

  // Load items to get structure tiles (via REST)
  try {
    await rest.getItems();
  } catch (err) {
    console.warn('[Battle] could not load items:', err.message);
  }

  _registerStructureTileTypes();

  // Load map from server (like composer)
  try {
    const response = await rest.loadMap();
    if (response && response.tiles) {
      grid.fromJSON({ tiles: response.tiles });
      grid.addVoidNeighbors();
      grid._centerGrid();
      console.log('[Battle] Map loaded from server');
    }
  } catch (err) {
    console.warn('[Battle] could not load map from server:', err.message);
  }

  // Connect battle WebSocket
  _wsConnect();

  // Listen for mobile screen on/off
  document.addEventListener('visibilitychange', _onVisibilityChange);
  _unsub.push(() => document.removeEventListener('visibilitychange', _onVisibilityChange));

  // Start status update loop
  _startStatusLoop();

  // Load map background image
  _loadMapBackground();
}

function leave() {
  _unsub.forEach(fn => fn());
  _unsub = [];
  _pendingAttackId = null;
  if (grid) {
    grid.destroy();
    grid = null;
  }
  _stopStatusLoop();

  // Disconnect battle WebSocket
  _wsDisconnect();
}

/** Fetch the first available map PNG and apply it as the grid background. */
async function _loadMapBackground() {
  try {
    const res = await fetch('/api/maps');
    if (!res.ok) return;
    const { maps } = await res.json();
    if (maps && maps.length > 0 && grid) {
      await grid.setMapBackground(maps[0].url);
    }
  } catch (e) {
    console.warn('[Battle] map background not loaded:', e.message);
  }
}

function _initCanvas() {
  const wrap = container.querySelector('#canvas-wrap');
  const canvas = container.querySelector('#battle-canvas');

  grid = new HexGrid({
    canvas,
    cols: 6,
    rows: 6,
    hexSize: 28,
    onTileClick: (q, r, tile) => _showTowerDetails(q, r, tile),
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
      icon: null,
      spriteUrl: info.sprite ? '/' + info.sprite : null,
      serverData: info,
    });
  }

  // Invalidate the base cache so tiles re-render with the correct tile types.
  // This is needed when items arrive after the map has already been rendered.
  if (grid) {
    grid._invalidateBase();
    grid._dirty = true;
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
  const wasActive = grid.battleActive;
  grid.clearBattle();

  // Load battle map
  if (msg.tiles) {
    grid.fromJSON({ tiles: msg.tiles });
    grid.addVoidNeighbors();
    // Only center on first setup, not on reconnect/refresh
    if (!wasActive) {
      grid._centerGrid();
    }
  }

  // Store critter path for rendering
  if (msg.path) {
    grid.setBattlePath(msg.path);
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

  // Update critter positions (new format: all critters with path_progress)
  if (msg.critters && Array.isArray(msg.critters)) {
    // Build set of active critter IDs from server
    const activeCids = new Set();
    for (const c of msg.critters) {
      grid.updateBattleCritter(c);
      activeCids.add(c.cid);
    }
    
    // Remove critters that are no longer in server's list (died or finished)
    for (const cid of grid.battleCritters.keys()) {
      if (!activeCids.has(cid)) {
        grid.removeBattleCritter(cid);
      }
    }
    
    grid._dirty = true;
  }

  // Update shot positions (all shots with path_progress)
  if (msg.shots && Array.isArray(msg.shots)) {
    if (msg.shots.length > 0) {
      console.log('[Battle] Received', msg.shots.length, 'shots');
    }
    
    // Build set of active shot IDs from server
    const activeShotIds = new Set();
    for (const shot of msg.shots) {
      grid.updateBattleShot(shot);
      // Shot ID is constructed as `${source_sid}_${target_cid}`
      const shot_id = `${shot.source_sid}_${shot.target_cid}`;
      activeShotIds.add(shot_id);
    }
    
    // Remove shots that are no longer in server's list (arrived or target died)
    for (const shot_id of grid.battleShots.keys()) {
      if (!activeShotIds.has(shot_id)) {
        grid.battleShots.delete(shot_id);
      }
    }
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

  // Show/hide Fight now! button (only during siege, only when navigated from dashboard)
  const fightNowItem = container.querySelector('#fight-now-item');
  if (fightNowItem) {
    const showFightNow = _pendingAttackId !== null && _battleState.phase === 'in_siege';
    fightNowItem.style.display = showFightNow ? '' : 'none';
  }

  // Update next wave with countdown
  const nextWaveEl = container.querySelector('#battle-next-wave');
  if (nextWaveEl) {
    if (_battleState.current_wave) {
      // Show current wave being spawned
      const w = _battleState.current_wave;
      const spawned = _battleState.current_wave_spawned;
      const total = w.slots;
      nextWaveEl.textContent = `${w.critter_iid} (${spawned}/${total})`;
    } else if (_battleState.next_wave) {
      // Show next wave with countdown
      const w = _battleState.next_wave;
      const countdown = _battleState.next_wave_countdown_ms;
      const timeStr = countdown > 0 ? ` in ${_formatTime(countdown)}` : '';
      nextWaveEl.textContent = `${w.critter_iid} x${w.slots}${timeStr}`;
    } else {
      nextWaveEl.textContent = 'done';
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
