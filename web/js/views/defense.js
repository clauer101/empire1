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

// ── Tower era statistics ─────────────────────────────────────
const _TOWER_ERA = {
  BASIC_TOWER: 'Steinzeit',    SLING_TOWER: 'Steinzeit',
  DOUBLE_SLING_TOWER: 'Neolith.', SPIKE_TRAP: 'Neolith.',
  ARROW_TOWER: 'Bronze',       BALLISTA_TOWER: 'Bronze',    FIRE_TOWER: 'Bronze',
  CATAPULTS: 'Eisenzeit',      ARBELESTE_TOWER: 'Eisenzeit',
  TAR_TOWER: 'Mittelalter',    HEAVY_TOWER: 'Mittelalter',  BOILING_OIL: 'Mittelalter',
  CANNON_TOWER: 'Renaissance', RIFLE_TOWER: 'Renaissance',  COLD_TOWER: 'Renaissance', ICE_TOWER: 'Renaissance',
  FLAME_THROWER: 'Industrie',  SHOCK_TOWER: 'Industrie',    PARALYZNG_TOWER: 'Industrie', GATLING_TOWER: 'Industrie',
  NAPALM_THROWER: 'Moderne',   MG_TOWER: 'Moderne',         RAPID_FIRE_MG_BUNKER: 'Moderne',
  RADAR_TOWER: 'Moderne',      ANTI_AIR_TOWER: 'Moderne',   LASER_TOWER: 'Moderne',
  SNIPER_TOWER: 'Zukunft',     ROCKET_TOWER: 'Zukunft',
};
const _ERA_COLORS = {
  'Steinzeit':   '#8B7355', 'Neolith.':    '#A0887A', 'Bronze':      '#CD7F32',
  'Eisenzeit':   '#888888', 'Mittelalter': '#6B8A8A', 'Renaissance': '#8B6914',
  'Industrie':   '#FF6B35', 'Moderne':     '#4B9CD3', 'Zukunft':     '#9B59B6',
};
const _ERA_ORDER_STAT = ['Steinzeit','Neolith.','Bronze','Eisenzeit','Mittelalter','Renaissance','Industrie','Moderne','Zukunft'];
const _NON_TOWER = new Set(['castle','spawnpoint','path','empty','void','']);

function _buildEraStatsHTML(tiles) {
  if (!tiles) return '';
  const towers = tiles.filter(t => !_NON_TOWER.has(t.type));
  if (!towers.length) return '<div style="color:var(--text-dim);font-size:11px;padding:4px 0;">No towers placed</div>';
  const byEra = {};
  for (const t of towers) {
    const era = _TOWER_ERA[t.type] || '?';
    byEra[era] = (byEra[era] || 0) + 1;
  }
  const total = Object.values(byEra).reduce((a, b) => a + b, 0);
  const maxCount = Math.max(1, ...Object.values(byEra));
  const rows = _ERA_ORDER_STAT
    .filter(era => byEra[era])
    .map(era => {
      const cnt = byEra[era];
      const barPct = Math.round(cnt / maxCount * 100);
      const pct = Math.round(cnt / total * 100);
      const col = _ERA_COLORS[era] || '#888';
      return `<div class="age-row">
        <span class="age-name">${era}</span>
        <div class="age-bar-outer"><div class="age-bar-inner" style="width:${barPct}%;background:${col}"></div></div>
        <span class="age-pct">${pct}%</span>
        <span style="color:var(--text-dim);font-size:10px;font-family:monospace">${cnt}×</span>
      </div>`;
    }).join('');
  return `<div style="font-size:11px;color:var(--text-dim);margin-bottom:4px;">${towers.length} towers total</div><div class="age-bars">${rows}</div>`;
}


/** @type {import('../state.js').StateStore} */
let st;
/** @type {HTMLElement} */
let container;
let _unsub = [];

/** @type {HexGrid|null} */
let grid = null;

/** @type {number|null} attack_id of the pending incoming attack (set from dashboard) */
let _pendingAttackId = null;
/** @type {number|null} defender_uid when spectating an outgoing attack */
let _spectateDefenderUid = null;

// ── Map Editor State ────────────────────────────────────────
let _isDirtyPath = false;
let _autoSaveTimer = null;

// ── Battle WebSocket ────────────────────────────────────────

/** @type {WebSocket|null} */
let _ws = null;
let _wsUrl = '';
let _wsConnected = false;
let _wsReconnectTimer = null;
let _wsIntentionalClose = false;

let _wsConnectTimeout = null;

function _fmtTitleResource(value, digits = 0) {
  const normalized = value ?? 0;
  if (normalized >= 1000) return (Math.floor(normalized / 100) / 10) + 'k';
  return Math.floor(normalized * Math.pow(10, digits)) / Math.pow(10, digits);
}

function _setBattleTitle(label) {
  const titleEl = container?.querySelector('.battle-title');
  if (!titleEl) return;

  const resources = st?.summary?.resources || {};
  titleEl.textContent = '';
  const labelSpan = document.createElement('span');
  labelSpan.textContent = label + ' ';
  const efxBtn = document.createElement('button');
  efxBtn.id = 'defense-effects-btn';
  efxBtn.className = 'prod-info-btn';
  efxBtn.title = 'Show defense effects';
  efxBtn.textContent = '🔍';
  labelSpan.appendChild(efxBtn);
  titleEl.appendChild(labelSpan);

  const resourceWrap = document.createElement('span');
  resourceWrap.className = 'title-resources';

  const goldEl = document.createElement('span');
  goldEl.className = 'title-gold';
  goldEl.textContent = '💰 ' + _fmtTitleResource(resources.gold);

  const cultureEl = document.createElement('span');
  cultureEl.className = 'title-culture';
  cultureEl.textContent = '🎭 ' + _fmtTitleResource(resources.culture);

  const lifeEl = document.createElement('span');
  lifeEl.className = 'title-life';
  const lifeIcon = document.createElement('span');
  lifeIcon.style.color = '#e05c5c';
  lifeIcon.textContent = '❤';
  lifeEl.append(lifeIcon, document.createTextNode(' ' + _fmtTitleResource(resources.life, 1)));

  resourceWrap.append(goldEl, cultureEl, lifeEl);
  titleEl.append(resourceWrap);
}

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
    _sendWs({ type: 'battle_register', target_uid: _spectateDefenderUid ?? st.summary?.uid, ...(_pendingAttackId != null ? { attack_id: _pendingAttackId } : {}) });
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
      // Auto-reconnect after 2s only if an attack is still active
      _wsReconnectTimer = setTimeout(() => _connectWsIfNeeded(), 2000);
    }
    _ws = null;
  });

  ws.addEventListener('error', (ev) => {
    clearTimeout(_wsConnectTimeout);
    _addDebugLog(`⚠ WS error (readyState=${ws.readyState}, url=${baseUrl})`);
  });
}

/**
 * Show/hide the battle status info rows depending on whether an attack is active.
 */
function _updateBattleStatusVisibility(visible) {
  const info = container?.querySelector('#battle-status-info');
  if (info) info.style.display = visible ? 'contents' : 'none';
  requestAnimationFrame(_fitCanvas);
}

/**
 * Connect the WS only when there is an active (siege/battle) attack.
 * Called on enter() and again whenever the phase changes.
 */
function _connectWsIfNeeded() {
  const ACTIVE_PHASES = ['in_siege', 'in_battle'];
  const summary = st.summary || {};
  const allAttacks = [...(summary.attacks_incoming || []), ...(summary.attacks_outgoing || [])];
  const hasActiveAttack = _pendingAttackId != null
    || allAttacks.some(a => ACTIVE_PHASES.includes(a.phase));

  _updateBattleStatusVisibility(hasActiveAttack);

  if (hasActiveAttack) {
    _wsConnect();
  } else {
    _addDebugLog('No active attack — WS not connected');
  }
}


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
    _sendWs({ type: 'battle_unregister', target_uid: _spectateDefenderUid ?? st.summary?.uid });
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
  // Only process battle messages that belong to the currently subscribed defender.
  // The backend pushes attack_phase_changed / battle_status directly to both
  // attacker and defender UIDs for every attack they are involved in, so we
  // must ignore messages for attacks we are not currently watching.
  const relevantDefender = _spectateDefenderUid ?? st.summary?.uid;

  switch (msg.type) {
    case 'welcome':
      _addDebugLog(`WS welcome: guest_uid=${msg.temp_uid}`);
      break;
    case 'battle_setup':
      if (msg.defender_uid !== relevantDefender) break;
      _onBattleSetup(msg);
      break;
    case 'battle_update':
      if (msg.defender_uid !== undefined && msg.defender_uid !== relevantDefender) break;
      _onBattleUpdate(msg);
      break;
    case 'battle_summary':
      if (msg.defender_uid !== undefined && msg.defender_uid !== relevantDefender) break;
      _onBattleSummary(msg);
      break;
    case 'battle_status':
      if (msg.defender_uid !== relevantDefender) break;
      _onBattleStatus(msg);
      break;
    case 'structure_update':
      _onStructureUpdate(msg);
      break;
    case 'attack_phase_changed':
      if (msg.defender_uid !== relevantDefender) break;
      _addDebugLog(`Phase changed: attack_id=${msg.attack_id} → ${msg.new_phase}`);
      // If entering siege and we don't have an attack ID yet, capture it now
      if (msg.new_phase === 'in_siege' && !_pendingAttackId && msg.attack_id != null) {
        _pendingAttackId = msg.attack_id;
      }
      // Sync state and refresh the fight-now button immediately
      if (msg.new_phase) {
        _battleState.phase = msg.new_phase;
        _updateStatusFromBattleMsg();
      }
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
      _connectWsIfNeeded();
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
  elapsed_ms: 0,
  is_finished: false,
  defender_won: null,
  phase: 'waiting',
  time_since_start_s: 0,
  wave_info: null,  // { wave_index, total_waves, iid, critter_name, slots, spawned, next_critter_ms }
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

// ── Era-dependent castle sprite ─────────────────────────────
const _ERA_CASTLE_SPRITES = {
  STEINZEIT:          '/assets/sprites/bases/base_stone.webp',
  NEOLITHIKUM:        '/assets/sprites/bases/base_neolithicum.webp',
  BRONZEZEIT:         '/assets/sprites/bases/base_bronze.webp',
  EISENZEIT:          '/assets/sprites/bases/base_iron.webp',
  MITTELALTER:        '/assets/sprites/bases/base_middle_ages.webp',
  RENAISSANCE:        '/assets/sprites/bases/base_renaissance.webp',
  INDUSTRIALISIERUNG: '/assets/sprites/bases/base_industrial.webp',
  MODERNE:            '/assets/sprites/bases/base_modern.webp',
  ZUKUNFT:            '/assets/sprites/bases/base_future.webp',
};

function _updateCastleSprite(eraKey) {
  const url = _ERA_CASTLE_SPRITES[eraKey] || '/assets/sprites/bases/base.webp';
  registerTileType('castle', {
    label: 'Castle (Target)',
    color: '#4a4a1a',
    stroke: '#7a7a30',
    icon: null,
    spriteUrl: url,
  });
  if (grid) {
    grid._invalidateBase();
    grid._dirty = true;
  }
}

// ── Defense Effects Overlay ─────────────────────────────────

function _defEffectRows(effectKey, completedBuildings, completedResearch, items, fmt) {
  const rows = [];
  for (const iid of (completedBuildings || [])) {
    const item = items?.buildings?.[iid];
    const val = item?.effects?.[effectKey];
    if (val) rows.push(`<div class="panel-row"><span class="label">${fmt(val)}</span><span class="value" style="color:#ccc">${item.name || iid}</span></div>`);
  }
  for (const iid of (completedResearch || [])) {
    const item = items?.knowledge?.[iid];
    const val = item?.effects?.[effectKey];
    if (val) rows.push(`<div class="panel-row"><span class="label">${fmt(val)}</span><span class="value" style="color:#ccc">${item.name || iid}</span></div>`);
  }
  if (!rows.length) return `<div style="color:#555;font-size:0.85em;padding:2px 0">No items contribute yet</div>`;
  return rows.join('');
}

function _showDefenseEffectsOverlay() {
  document.querySelector('.def-effects-overlay')?.remove();

  const summary = st.summary || {};
  const effects = summary.effects || {};
  const completedBuildings = summary.completed_buildings || [];
  const completedResearch = summary.completed_research || [];
  const items = st.items || {};

  const siegeTotal   = effects.siege_offset || 0;
  const waveTotal    = effects.wave_delay_offset || 0;
  const restoreTotal = effects.restore_life_after_loss_offset || 0;

  function section(icon, title, color, totalStr, rowsHtml) {
    return `
      <div class="prod-overlay-section">
        <div class="prod-overlay-title"><span style="color:${color}">${icon} ${title}</span></div>
        ${rowsHtml}
        <div class="panel-row" style="border-top:1px solid #444;margin-top:6px;padding-top:6px">
          <span class="label" style="color:#ddd;font-weight:bold">Total</span>
          <span class="value" style="color:#fff;font-weight:bold">${totalStr}</span>
        </div>
      </div>`;
  }

  const siegeRows   = _defEffectRows('siege_offset',            completedBuildings, completedResearch, items, v => `+${v.toFixed(0)}s`);
  const waveRows    = _defEffectRows('wave_delay_offset',       completedBuildings, completedResearch, items, v => `+${(v/1000).toFixed(1)}s`);
  const restoreRows = _defEffectRows('restore_life_after_loss_offset', completedBuildings, completedResearch, items, v => `+${v.toFixed(1)} ❤`);

  // Era distribution
  const tiles = grid ? [...grid.tiles.values()] : [];
  const eraStatsHTML = `
    <div class="prod-overlay-section">
      <div class="prod-overlay-title"><span style="color:#9B59B6">🏰 Tower Era Distribution</span></div>
      ${_buildEraStatsHTML(tiles)}
    </div>`;

  const overlay = document.createElement('div');
  overlay.className = 'prod-overlay def-effects-overlay';
  overlay.innerHTML = `
    <div class="prod-overlay-box">
      <button class="prod-overlay-close" title="Close">✕</button>
      <div style="font-weight:bold;font-size:1.05em;margin-bottom:12px">🛡 Defense Effects</div>
      ${eraStatsHTML}
      ${section('⏳', 'Siege Delay',          '#ffa726', `+${siegeTotal.toFixed(0)}s`,            siegeRows)}
      ${section('🌊', 'Wave Delay',           '#4fc3f7', `+${(waveTotal/1000).toFixed(1)}s`,      waveRows)}
      ${section('❤',  'Restore Life on Loss', '#e05c5c', `+${restoreTotal.toFixed(1)}`,           restoreRows)}
    </div>`;

  overlay.addEventListener('click', e => {
    if (e.target === overlay || e.target.classList.contains('prod-overlay-close')) overlay.remove();
  });
  document.body.appendChild(overlay);
}

// ── View lifecycle ──────────────────────────────────────────

function init(el, _api, _state) {
  container = el;
  // api parameter is no longer used — battle manages its own WS
  st = _state;

  // Inject shared overlay styles (same block as status.js — skipped if already present)
  if (!document.getElementById('dashboard-grid-style')) {
    const s = document.createElement('style');
    s.id = 'dashboard-grid-style';
    s.textContent = `
      .prod-overlay{position:fixed;inset:0;background:rgba(0,0,0,.75);z-index:9999;display:flex;align-items:flex-start;justify-content:center;padding:24px 12px;overflow-y:auto}
      .prod-overlay-box{background:var(--panel-bg,#1e1e1e);border:1px solid var(--border-color,#444);border-radius:8px;width:100%;max-width:480px;padding:16px 18px;position:relative}
      .prod-overlay-close{position:absolute;top:10px;right:12px;background:none;border:none;color:#aaa;font-size:1.4em;cursor:pointer;line-height:1;padding:0}
      .prod-overlay-section{margin-bottom:14px}
      .prod-overlay-title{font-size:0.78em;font-weight:bold;text-transform:uppercase;letter-spacing:.05em;color:#888;margin-bottom:5px;padding-bottom:3px;border-bottom:1px solid var(--border-color,#444)}
      .prod-info-btn{background:none;border:none;color:#4fc3f7;font-size:0.95em;cursor:pointer;padding:0 0 0 5px;line-height:1;vertical-align:middle;opacity:.8}
      .prod-info-btn:hover{opacity:1}
    `;
    document.head.appendChild(s);
  }

  container.innerHTML = `
    <div class="battle-view">
      <h2 class="battle-title">⚔ Defense<span class="title-resources"><span class="title-gold"></span><span class="title-culture"></span><span class="title-life"></span></span></h2>

      <!-- Battle Status Panel -->
      <div class="battle-status" id="battle-status">
        <div id="battle-status-info" style="display:none;grid-column:1/-1;display:none;">
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
        </div>
        <div class="battle-status__item" id="fight-now-item" style="display:none;grid-column: 1 / -1;">
          <button id="fight-now-btn" style="width:100%;background:var(--danger,#e53935);border:none;color:#fff;padding:8px 16px;border-radius:var(--radius,4px);font-size:1em;font-weight:bold;cursor:pointer;letter-spacing:0.5px;">⚔ Fight now!</button>
        </div>
      </div>

      <!-- Battle Body (Canvas + Props Panel) -->
      <div id="map-error-banner" style="display:none;padding:6px 12px;margin:0;background:#8a3a3a;color:#ffcccc;border-left:4px solid #c85a5a;border-radius:2px;font-size:0.85rem;flex-shrink:0;"></div>
      <div class="battle-view__body">
        <!-- Canvas Container -->
        <div class="battle-canvas-wrap" id="canvas-wrap">
          <button id="map-save" style="display:none;position:absolute;top:8px;right:8px;z-index:10;font-size:11px;padding:3px 10px;" title="Save path layout">💾 Save</button>
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

      <!-- Tile Placement Menu -->
      <div class="tile-place-menu" id="tile-place-menu" style="display:none;">
        <div class="tile-place-menu__content">
          <div class="tile-place-menu__header">
            <span>Tile belegen</span>
            <button class="tile-overlay__close" id="tile-place-close">✕</button>
          </div>
          <div class="tpm-items" id="tpm-items"></div>
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

  // Bind defense effects info button (delegation — button is recreated by _setBattleTitle)
  container.addEventListener('click', e => {
    if (e.target.id === 'defense-effects-btn') _showDefenseEffectsOverlay();
  });

  // Bind summary close button
  container.querySelector('#summary-close').addEventListener('click', () => {
    container.querySelector('#battle-summary').style.display = 'none';
    window.location.hash = '#status';
  });

  // Bind Fight now! button (visible during in_siege when an incoming attack is tracked)
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

  // Bind Save button (path editor)
  container.querySelector('#map-save').addEventListener('click', _saveMap);

  // Bind placement menu close
  const placeMenu = container.querySelector('#tile-place-menu');
  container.querySelector('#tile-place-close').addEventListener('click', () => {
    placeMenu.style.display = 'none';
  });
  placeMenu.addEventListener('click', (e) => {
    if (e.target === placeMenu) placeMenu.style.display = 'none';
  });

  // Close placement menu & tower overlay on Escape
  const _onKeyDown = (e) => {
    if (e.key === 'Escape') {
      placeMenu.style.display = 'none';
      const overlay = container.querySelector('#tower-overlay');
      if (overlay) overlay.style.display = 'none';
    }
  };
  document.addEventListener('keydown', _onKeyDown);
  _unsub.push(() => document.removeEventListener('keydown', _onKeyDown));

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

function _showTileDetails(q, r, tile) {
  const overlayBody = container.querySelector('#tower-overlay-body');
  const overlay = container.querySelector('#tower-overlay');
  const propsContent = container.querySelector('#tower-props-content');

  if (!tile) return;

  const t = getTileType(tile.type);
  // Show editing controls when viewing own map; hide only when spectating a foreign map.
  const _isDefender = _spectateDefenderUid == null;

  // ── Buy-tile button for void tiles ──────────────────────
  if (tile.type === 'void') {
    const tilePrice = st.summary?.tile_price || 0;
    const currentGold = st.summary?.resources?.gold || 0;
    const canAfford = currentGold >= tilePrice;
    const buyHTML =
      '<div class="props-tile">' +
        '<div class="props-row"><span class="label">Type</span><span class="value">Void</span></div>' +
        (_isDefender
          ? '<div class="props-divider"></div>' +
            '<div class="props-row"><span class="label">Cost</span><span class="value" style="color:' + (canAfford ? 'var(--text)' : 'var(--danger)') + '">' +
            '\ud83d\udcb0 ' + Math.round(tilePrice) + ' Gold</span></div>' +
            '<button id="buy-tile-btn" class="btn" style="width:100%;margin-top:8px;"' +
            (canAfford ? '' : ' disabled title="Not enough gold"') + '>Buy Tile</button>' +
            '<div id="buy-tile-msg" style="margin-top:6px;font-size:12px;text-align:center;"></div>'
          : '') +
      '</div>';

    if (propsContent) propsContent.innerHTML = buyHTML;
    if (overlayBody) {
      overlayBody.innerHTML = buyHTML;
      if (window.innerWidth <= 1100) overlay.style.display = 'flex';
    }

    const buyHandler = async (btnEl, msgEl) => {
      btnEl.disabled = true;
      msgEl.textContent = '';
      try {
        const resp = await rest.buyTile(q, r);
        if (resp.success) {
          msgEl.textContent = '\u2713 Tile purchased!';
          msgEl.style.color = 'var(--success)';
          await rest.getSummary();
          // Reload map from server then auto-save (tile purchase already persists on server)
          const response = await rest.loadMap();
          if (response && response.tiles) {
            grid.fromJSON({ tiles: response.tiles });
            grid.addVoidNeighbors();
            const path = response.path ? response.path.map(([q, r]) => ({ q, r })) : null;
            grid.setDisplayPath(path);
            grid._dirty = true;
          }
          if (overlay) overlay.style.display = 'none';
        } else {
          msgEl.textContent = '\u2717 ' + (resp.error || 'Failed to buy tile');
          msgEl.style.color = 'var(--danger)';
          btnEl.disabled = false;
        }
      } catch (err) {
        msgEl.textContent = '\u2717 ' + err.message;
        msgEl.style.color = 'var(--danger)';
        btnEl.disabled = false;
      }
    };
    [propsContent, overlayBody].forEach(root => {
      if (!root) return;
      const b = root.querySelector('#buy-tile-btn');
      const m = root.querySelector('#buy-tile-msg');
      if (b && m) b.addEventListener('click', () => buyHandler(b, m));
    });
    return;
  }

  // ── Tower tile info ──────────────────────────────────────
  let towerInfo = '';
  let _goldCost;
  if (t.serverData) {
    const s = t.serverData;
    _goldCost = s.costs?.gold;
    const _currentGold = st.summary?.resources?.gold || 0;
    const _costColor = _goldCost && _currentGold < _goldCost ? 'var(--danger)' : 'var(--text)';
    const _tileSelect = (tile && tile.select) || s.select || 'first';
    const _selectLabels = { first: '▶ First', last: '◀ Last', random: '⁇ Random' };
    const _selectBtns = _isDefender
      ? ['first', 'last', 'random'].map(v =>
          `<button class="btn select-btn${_tileSelect === v ? ' select-btn--active' : ''}" data-select="${v}" style="flex:1;padding:3px 0;font-size:11px;">${_selectLabels[v]}</button>`
        ).join('')
      : `<span style="font-size:11px;color:var(--muted,#888)">${_selectLabels[_tileSelect]}</span>`;
    const _spriteThumb = t.spriteUrl
      ? '<div class="props-sprite-thumb" style="text-align:center;margin:6px 0 4px"><span style="display:inline-block;width:56px;height:56px;border-radius:6px;background:' + t.color + ';border:1px solid ' + t.stroke + ';background-image:url(' + t.spriteUrl + ');background-size:contain;background-repeat:no-repeat;background-position:center;"></span></div>'
      : '';
    let _efxHtml = '';
    if (s.effects && Object.keys(s.effects).length > 0) {
      const _efxParts = [];
      const ef = s.effects;
      if (ef.burn_duration || ef.burn_dps) {
        _efxParts.push('<span>🔥 ' + ((ef.burn_duration || 0) / 1000).toFixed(1) + 's @ ' + (ef.burn_dps || 0) + ' dps</span>');
      }
      if (ef.slow_duration || ef.slow_ratio != null) {
        _efxParts.push('<span>❄ ' + ((ef.slow_duration || 0) / 1000).toFixed(1) + 's @ ' + Math.round((ef.slow_ratio || 0) * 100) + '% speed</span>');
      }
      if (ef.splash_radius) {
        _efxParts.push('<span>💥 ' + ef.splash_radius + ' hex</span>');
      }
      Object.entries(ef).forEach(([k, v]) => {
        if (!['burn_duration','burn_dps','slow_duration','slow_ratio','splash_radius'].includes(k)) {
          _efxParts.push('<span>' + k + ': ' + v + '</span>');
        }
      });
      _efxHtml = '<div class="props-row effects-row"><span class="label">Effects</span><span class="value effects-list">' + _efxParts.join('') + '</span></div>';
    }
    towerInfo =
      _spriteThumb +
      '<div class="props-divider"></div>' +
      '<div class="props-section-label">Tower Stats</div>' +
      (_goldCost ? '<div class="props-row"><span class="label">Cost</span><span class="value" style="color:' + _costColor + '">💰 ' + Math.round(_goldCost).toLocaleString() + ' Gold</span></div>' : '') +
      '<div class="props-row"><span class="label">Damage</span><span class="value">' + (s.damage || 0) + '</span></div>' +
      '<div class="props-row"><span class="label">Range</span><span class="value">🎯 ' + (s.range || 0) + ' hex</span></div>' +
      '<div class="props-row"><span class="label">Reload</span><span class="value">' + ((s.reload_time_ms || 0) / 1000).toFixed(1) + ' s</span></div>' +
      _efxHtml +
      '<div class="props-divider"></div>' +
      '<div class="props-section-label">Target Select</div>' +
      '<div id="select-btns" style="display:flex;gap:4px;margin-top:4px;">' + _selectBtns + '</div>';
  } else if (!['path', 'castle', 'spawnpoint', 'empty'].includes(tile.type)) {
    // Unknown structure tile — don't show details
    return;
  }

  const detailsHTML =
    '<div class="props-tile">' +
      '<div class="props-row"><span class="label">Type</span><span class="value">' +
        '<span class="palette-swatch--sm" style="background:' + t.color + ';border-color:' + t.stroke + '"></span>' +
        t.label +
      '</span></div>' +
      towerInfo +
      (_isDefender && tile.type !== 'path'
        && !(_battleState.phase === 'in_battle' && (tile.type === 'castle' || tile.type === 'spawnpoint'))
        ? '<div class="props-divider"></div>' +
          '<button id="empty-tile-btn" class="btn btn-danger" style="width:100%;margin-top:4px;">🗑 Empty Tile' + (_goldCost ? ' (💰 ' + Math.round(_goldCost * 0.3).toLocaleString() + ' refund)' : '') + '</button>'
        : '') +
    '</div>';

  if (propsContent) propsContent.innerHTML = detailsHTML;
  if (overlayBody) {
    overlayBody.innerHTML = detailsHTML;
    const _hasContent = towerInfo || tile.type !== 'empty';
    if (window.innerWidth <= 1100 && _hasContent) overlay.style.display = 'flex';
  }

  const _doEmpty = () => {
    grid.setTile(q, r, 'empty');
    _checkPathAndSave();
    if (overlay) overlay.style.display = 'none';
    if (propsContent) propsContent.innerHTML = '';
  };

  const _bindSelectBtns = (root) => {
    if (!root) return;
    root.querySelectorAll('.select-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const val = btn.dataset.select;
        const tileData = grid.getTile(q, r);
        if (tileData) {
          tileData.select = val === 'first' ? undefined : val;
          grid._dirty = true;
          // Immediately notify server (updates live battle + persists to hex_map)
          _sendWs({ type: 'set_structure_select', hex_q: q, hex_r: r, select: val });
          _autoSave();
        }
        // Refresh button highlight without re-opening the full panel
        root.querySelectorAll('.select-btn').forEach(b => {
          b.classList.toggle('select-btn--active', b.dataset.select === val);
        });
      });
    });
  };

  [propsContent, overlayBody].forEach(root => {
    if (!root) return;
    const b = root.querySelector('#empty-tile-btn');
    if (b) b.addEventListener('click', _doEmpty);
    _bindSelectBtns(root);
  });
}

function _fitCanvas() {
  const wrap = container.querySelector('#canvas-wrap');
  if (!wrap) return;
  const body = container.querySelector('.battle-view__body');
  if (!body) return;
  // Measure how far the canvas body starts from the top of the viewport.
  // Use calc(100dvh - Xpx) so the height is always viewport-relative.
  const topOffset = Math.round(body.getBoundingClientRect().top);
  const appStyle = getComputedStyle(document.getElementById('app') || document.body);
  const padBottom = parseFloat(appStyle.paddingBottom) || 0;
  wrap.style.height = `calc(100dvh - ${topOffset + padBottom}px)`;
  grid?._resize();
}

async function enter() {
  _debugLogs = [];  // Clear previous debug logs
  _updateDebugPanel();  // Initialize debug panel visibility
  _initCanvas();
  requestAnimationFrame(_fitCanvas);

  // Apply era-dependent castle sprite for own defense
  _updateCastleSprite(st.summary?.current_era || 'STEINZEIT');

  // Reset battle state so stale data from a previous session is never shown
  _battleState = {
    active: false,
    bid: null,
    defender_uid: null,
    defender_name: '',
    attacker_uids: [],
    attacker_name: '',
    elapsed_ms: 0,
    is_finished: false,
    defender_won: null,
    phase: 'waiting',
    time_since_start_s: 0,
    wave_info: null,
  };
  _updateStatusFromBattleMsg();

  // Check if navigated from status view to spectate an outgoing battle
  if (st.pendingSpectateAttack) {
    _pendingAttackId = st.pendingSpectateAttack.attack_id;
    _spectateDefenderUid = st.pendingSpectateAttack.defender_uid;
    st.pendingSpectateAttack = null;
  }

  // Check if navigated from dashboard for a specific incoming attack
  if (st.pendingIncomingAttack) {
    _pendingAttackId = st.pendingIncomingAttack.attack_id;
    st.pendingIncomingAttack = null;
  }

  // If no attack id set (navigated via menu), auto-pick the nearest incoming attack.
  // Priority: 1) currently in_battle, 2) smallest siege_time (in_siege), 3) smallest eta_seconds
  if (_pendingAttackId == null) {
    const incoming = st.summary?.attacks_incoming || [];
    const battleAttack = incoming.find(a => a.phase === 'in_battle');
    if (battleAttack) {
      _pendingAttackId = battleAttack.attack_id;
    } else {
      const siegeAttacks = incoming.filter(a => a.phase === 'in_siege');
      if (siegeAttacks.length > 0) {
        const soonest = siegeAttacks.reduce((a, b) => ((a.siege_time ?? Infinity) <= (b.siege_time ?? Infinity) ? a : b));
        _pendingAttackId = soonest.attack_id;
      } else if (incoming.length > 0) {
        const nearest = incoming.reduce((a, b) => ((a.eta_seconds ?? Infinity) <= (b.eta_seconds ?? Infinity) ? a : b));
        _pendingAttackId = nearest.attack_id;
      }
    }
  }

  // Subscribe to items for structure tile types
  _unsub.push(eventBus.on('state:items', () => { _registerStructureTileTypes(); }));
  // Reconnect WS when summary changes (e.g. attack becomes active)
  _unsub.push(eventBus.on('state:summary', (data) => {
    if (!_wsConnected) _connectWsIfNeeded();
    if (_spectateDefenderUid == null && data?.current_era) _updateCastleSprite(data.current_era);
  }));

  // Load items to get structure tiles (via REST)
  try {
    await rest.getItems();
  } catch (err) {
    console.warn('[Battle] could not load items:', err.message);
  }

  _registerStructureTileTypes();

  if (_spectateDefenderUid != null) {
    // Spectating: hide props panel, give canvas full width, update title
    const props = container.querySelector('#tower-props');
    if (props) props.style.display = 'none';
    const body = container.querySelector('.battle-view__body');
    if (body) body.style.gridTemplateColumns = '1fr';
    _setBattleTitle('👁 Spectating...');
  } else {
    // Own defense: ensure props panel visible
    const props = container.querySelector('#tower-props');
    if (props) props.style.display = '';
    const body = container.querySelector('.battle-view__body');
    if (body) body.style.gridTemplateColumns = '';
    _setBattleTitle('⚔ Defense');
    // Load own map from server
    try {
      const response = await rest.loadMap();
      if (response && response.tiles) {
        grid.fromJSON({ tiles: response.tiles });
        grid.addVoidNeighbors();
        grid._centerGrid();
        console.log('[Battle] Map loaded from server');
        // Apply the server-computed path (null if no valid path exists)
        const path = response.path ? response.path.map(([q, r]) => ({ q, r })) : null;
        grid.setDisplayPath(path);
        if (!path) {
          let hasSp = false, hasCa = false;
          for (const [, d] of grid.tiles) {
            if (d.type === 'spawnpoint') hasSp = true;
            if (d.type === 'castle') hasCa = true;
          }
          if (hasSp && hasCa) {
            _showPersistentError('⚠️ Kein Pfad von Spawnpoint zu Castle — bitte Hindernisse entfernen.');
            _markPathDirty();
          }
        } else {
          _clearMapError();
        }
      }
    } catch (err) {
      console.warn('[Battle] could not load map from server:', err.message);
    }
  }

  // Connect battle WebSocket only if an attack is active
  _connectWsIfNeeded();

  // Listen for mobile screen on/off
  document.addEventListener('visibilitychange', _onVisibilityChange);
  _unsub.push(() => document.removeEventListener('visibilitychange', _onVisibilityChange));

  // Start status update loop
  _startStatusLoop();

  // Load map background image
  _loadMapBackground();
}

function leave() {
  const wrap = container.querySelector('#canvas-wrap');
  if (wrap) wrap.style.height = '';
  _unsub.forEach(fn => fn());
  _unsub = [];
  _pendingAttackId = null;
  _spectateDefenderUid = null;
  _isDirtyPath = false;
  clearTimeout(_autoSaveTimer);
  const menu = container?.querySelector('#tile-place-menu');
  if (menu) menu.style.display = 'none';
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

let _mapErrorTimeout = null;

/** Show a transient error banner that auto-hides after 2.5 s. */
function _showMapError(msg) {
  const wrap = container.querySelector('#canvas-wrap');
  if (!wrap) return;
  let el = wrap.querySelector('.map-error-msg');
  if (!el) {
    el = document.createElement('div');
    el.className = 'map-error-msg';
    wrap.insertBefore(el, wrap.firstChild);
  }
  el.textContent = msg;
  el.style.opacity = '1';
  clearTimeout(_mapErrorTimeout);
  _mapErrorTimeout = setTimeout(() => { el.style.opacity = '0'; }, 2500);
}

/** Show a persistent error banner that stays until _clearMapError() is called. */
function _showPersistentError(msg) {
  clearTimeout(_mapErrorTimeout);
  _mapErrorTimeout = null;
  const wrap = container.querySelector('#canvas-wrap');
  if (!wrap) return;
  let el = wrap.querySelector('.map-error-msg');
  if (!el) {
    el = document.createElement('div');
    el.className = 'map-error-msg';
    wrap.insertBefore(el, wrap.firstChild);
  }
  el.textContent = msg;
  el.style.opacity = '1';
}

/** Hide the persistent error banner. */
function _clearMapError() {
  clearTimeout(_mapErrorTimeout);
  _mapErrorTimeout = null;
  const wrap = container.querySelector('#canvas-wrap');
  if (!wrap) return;
  const el = wrap.querySelector('.map-error-msg');
  if (el) el.style.opacity = '0';
}

function _initCanvas() {
  const wrap = container.querySelector('#canvas-wrap');
  const canvas = container.querySelector('#battle-canvas');

  grid = new HexGrid({
    canvas,
    cols: 6,
    rows: 6,
    hexSize: 28,
    onTileClick: (q, r, tile) => {
      const tileData = tile || grid.getTile(q, r);
      const isOnPath = grid.battlePath?.some(p => p.q === q && p.r === r);
      const inBattle = _battleState.phase === 'in_battle';

      // Path tiles
      if (isOnPath) {
        if (inBattle) {
          _showTileDetails(q, r, { type: 'path' });
        } else if (tileData?.type === 'castle' || tileData?.type === 'spawnpoint') {
          _showTileDetails(q, r, tileData);
        } else if (tileData?.type === 'empty' && _spectateDefenderUid == null) {
          _openPlacementMenu(q, r);
        }
        return;
      }

      // void tile → always show details (buy-tile option)
      if (!tileData || tileData.type === 'void') {
        _showTileDetails(q, r, tileData);
        return;
      }

      // castle / spawnpoint → show details only outside battle
      if (tileData.type === 'castle' || tileData.type === 'spawnpoint') {
        if (!inBattle) _showTileDetails(q, r, tileData);
        return;
      }

      // empty tile → open placement menu (tower selection)
      if (tileData.type === 'empty') {
        if (_spectateDefenderUid == null) _openPlacementMenu(q, r);
        return;
      }

      // occupied tile (tower) → always show details
      _showTileDetails(q, r, tileData);
    },
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
  const catalog = items.catalog || {};

  // Include locked structures from catalog so placed-but-locked towers render correctly.
  const allStructureIids = new Set([
    ...Object.keys(structures),
    ...Object.entries(catalog)
      .filter(([, v]) => v.item_type === 'structure')
      .map(([iid]) => iid),
  ]);

  let colorIdx = 0;
  for (const iid of allStructureIids) {
    const info = structures[iid] || catalog[iid] || {};
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

// \u2500\u2500 Tile Placement Menu \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

function _clearExistingCastle(excludeQ, excludeR) {
  if (!grid) return;
  for (const [key, data] of grid.tiles) {
    if (data.type === 'castle') {
      const [sq, sr] = key.split(',').map(Number);
      if (sq === excludeQ && sr === excludeR) continue;
      grid.setTile(sq, sr, 'empty');
    }
  }
}

function _clearExistingSpawnpoint(excludeQ, excludeR) {
  if (!grid) return;
  for (const [key, data] of grid.tiles) {
    if (data.type === 'spawnpoint') {
      const [sq, sr] = key.split(',').map(Number);
      if (sq === excludeQ && sr === excludeR) continue;
      grid.setTile(sq, sr, 'empty');
    }
  }
}

/**
 * Open the tile-placement menu at the given (empty) grid coordinate.
 * Shows castle/spawnpoint always outside battle; always lists unlocked towers.
 */
function _openPlacementMenu(q, r) {
  if (grid.getTile(q, r)?.type !== 'empty') return;

  const menu = container.querySelector('#tile-place-menu');
  const itemsEl = container.querySelector('#tpm-items');
  if (!menu || !itemsEl) return;

  itemsEl.innerHTML = '';

  const inBattle = _battleState.phase === 'in_battle';

  // Detect already-placed unique tiles
  let hasCastle = false;
  let hasSpawnpoint = false;
  for (const [, tileData] of grid.tiles) {
    if (tileData.type === 'castle') hasCastle = true;
    if (tileData.type === 'spawnpoint') hasSpawnpoint = true;
  }

  // ── Setup tiles (not during active battle) — always show castle/spawnpoint; moving is allowed
  if (!inBattle) {
    const label = document.createElement('div');
    label.className = 'tpm-section-label';
    label.textContent = 'Wegpunkte';
    itemsEl.appendChild(label);

    const setupRow = document.createElement('div');
    setupRow.className = 'tpm-row';
    for (const typeId of ['castle', 'spawnpoint']) {
      const item = _createTpmItem(typeId, q, r, menu);
      if (typeId === 'castle' && hasCastle) {
        item.title += ' (verschieben)';
      } else if (typeId === 'spawnpoint' && hasSpawnpoint) {
        item.title += ' (verschieben)';
      }
      setupRow.appendChild(item);
    }
    itemsEl.appendChild(setupRow);
  }

  // ── Towers ─────────────────────────────────────────────
  const structureIds = Object.keys((st.items || {}).structures || {}).reverse();
  if (structureIds.length > 0) {
    const towerLabel = document.createElement('div');
    towerLabel.className = 'tpm-section-label';
    towerLabel.textContent = 'T\xfcrme';
    itemsEl.appendChild(towerLabel);

    const towerGrid = document.createElement('div');
    towerGrid.className = 'tpm-grid';
    for (const iid of structureIds) {
      towerGrid.appendChild(_createTpmItem(iid, q, r, menu));
    }
    itemsEl.appendChild(towerGrid);
  }

  menu.style.display = 'flex';
}

function _createTpmItem(typeId, q, r, menu) {
  const t = getTileType(typeId);
  const s = t.serverData;
  const currentGold = st.summary?.resources?.gold || 0;
  const goldCost = s?.costs?.gold;
  const canAfford = !goldCost || currentGold >= goldCost;

  const card = document.createElement('div');
  card.className = 'tpm-item' + (canAfford ? '' : ' tpm-item--disabled');
  card.title = t.label + (goldCost ? ' (\ud83d\udcb0 ' + Math.round(goldCost).toLocaleString() + ')' : '');

  // Sprite
  const sprite = document.createElement('div');
  sprite.className = 'tpm-sprite';
  sprite.style.backgroundColor = t.color;
  sprite.style.border = '2px solid ' + t.stroke;
  if (t.spriteUrl) {
    sprite.style.backgroundImage = 'url(' + t.spriteUrl + ')';
    if (typeId === 'path') sprite.style.backgroundSize = '50%';
  }
  card.appendChild(sprite);

  // Name
  const name = document.createElement('div');
  name.className = 'tpm-name';
  name.textContent = t.label;
  card.appendChild(name);

  // Cost
  if (goldCost) {
    const cost = document.createElement('div');
    cost.className = 'tpm-cost' + (canAfford ? '' : ' unaffordable');
    cost.textContent = '\ud83d\udcb0 ' + Math.round(goldCost).toLocaleString();
    card.appendChild(cost);
  }

  // Stats (towers only)
  if (s && (s.damage || s.range || s.reload_time_ms)) {
    const stats = document.createElement('div');
    stats.className = 'tpm-stats';
    const statItems = [];
    if (s.damage) statItems.push({ text: '\u2694\ufe0f\u202f' + s.damage, tip: 'Damage: ' + s.damage });
    if (s.range) statItems.push({ text: '\ud83c\udfaf\u202f' + s.range, tip: 'Range: ' + s.range });
    if (s.reload_time_ms) statItems.push({ text: '\u23f1\ufe0f\u202f' + (s.reload_time_ms / 1000).toFixed(1) + 's', tip: 'Reload Time: ' + (s.reload_time_ms / 1000).toFixed(1) + 's' });
    statItems.forEach((item) => {
      const span = document.createElement('span');
      span.title = item.tip;
      span.textContent = item.text;
      stats.appendChild(span);
    });
    card.appendChild(stats);
  }

  // Special effects badge
  if (s?.effects && Object.keys(s.effects).length > 0) {
    const efx = document.createElement('div');
    efx.className = 'tpm-effects';
    const ef = s.effects;
    const efxItems = [];
    if (ef.burn_duration || ef.burn_dps) {
      const txt = '🔥\u202f' + ((ef.burn_duration || 0) / 1000).toFixed(1) + 's @ ' + (ef.burn_dps || 0) + '\u202fdps';
      efxItems.push({ text: txt, tip: 'Burn Damage: ' + (ef.burn_dps || 0) + ' dps for ' + ((ef.burn_duration || 0) / 1000).toFixed(1) + 's' });
    }
    if (ef.slow_duration || ef.slow_ratio != null) {
      const txt = '❄\u202f' + ((ef.slow_duration || 0) / 1000).toFixed(1) + 's @ ' + Math.round((ef.slow_ratio || 0) * 100) + '%';
      efxItems.push({ text: txt, tip: 'Slow Effect: ' + Math.round((ef.slow_ratio || 0) * 100) + '% speed for ' + ((ef.slow_duration || 0) / 1000).toFixed(1) + 's' });
    }
    if (ef.splash_radius) {
      efxItems.push({ text: '💥\u202f' + ef.splash_radius, tip: 'Splash Radius: ' + ef.splash_radius + ' tiles' });
    }
    efxItems.forEach((item) => {
      const span = document.createElement('span');
      span.title = item.tip;
      span.textContent = item.text;
      efx.appendChild(span);
    });
    card.appendChild(efx);
  }

  if (canAfford) {
    card.addEventListener('click', () => {
      _placeTile(q, r, typeId);
      menu.style.display = 'none';
    });
  }

  return card;
}

function _placeTile(q, r, typeId) {
  const existingType = grid.getTile(q, r)?.type;
  if (!existingType || existingType === 'void') return;
  if (existingType !== 'empty') {
    _showMapError('Tile bereits belegt.');
    return;
  }
  if (typeId === 'spawnpoint') _clearExistingSpawnpoint(q, r);
  if (typeId === 'castle') _clearExistingCastle(q, r);
  grid.setTile(q, r, typeId);
  // Deduct tower gold cost immediately (no cost for castle/spawnpoint)
  const cost = getTileType(typeId)?.serverData?.costs?.gold || 0;
  if (cost && st.summary?.resources) {
    st.summary.resources.gold = Math.max(0, (st.summary.resources.gold || 0) - cost);
  }
  _checkPathAndSave();
}

function _markPathDirty() {
  _isDirtyPath = true;
  // Never show the save button when spectating
  if (_spectateDefenderUid != null) return;
  const btn = container.querySelector('#map-save');
  if (btn) btn.style.display = '';
}

function _clearPathDirty() {
  _isDirtyPath = false;
  const btn = container.querySelector('#map-save');
  if (btn) btn.style.display = 'none';
}

/**
 * After any tile change: check prerequisites and auto-save.
 * Only sends a save when both spawnpoint and castle are placed.
 */
function _checkPathAndSave() {
  if (_spectateDefenderUid != null) return;
  let hasSpawnpoint = false, hasCastle = false;
  for (const [, data] of grid.tiles) {
    if (data.type === 'spawnpoint') hasSpawnpoint = true;
    if (data.type === 'castle') hasCastle = true;
  }
  if (!hasCastle) {
    _showPersistentError('⚠️ Kein Castle platziert');
    grid.setDisplayPath(null);
    return;
  }
  if (!hasSpawnpoint) {
    _showPersistentError('⚠️ Kein Spawnpoint platziert');
    grid.setDisplayPath(null);
    return;
  }
  _autoSave();
}

async function _saveMap() {
  // Never save while spectating another player's battle
  if (_spectateDefenderUid != null) {
    console.warn('[Battle] _saveMap blocked: spectating uid', _spectateDefenderUid);
    return;
  }
  // Verify that the map currently shown belongs to the logged-in user
  const myUid = st?.auth?.uid;
  if (myUid == null || (_battleState.defender_uid != null && _battleState.defender_uid !== myUid)) {
    console.error('[Battle] _saveMap blocked: displayed map belongs to uid', _battleState.defender_uid, '(mine:', myUid, ')');
    const errBanner = container.querySelector('#map-error-banner');
    if (errBanner) { errBanner.textContent = '\u274c Cannot save: wrong map loaded'; errBanner.style.display = 'block'; }
    return;
  }
  const btn = container.querySelector('#map-save');
  const errBanner = container.querySelector('#map-error-banner');
  if (btn) { btn.disabled = true; btn.textContent = 'Saving\u2026'; }
  if (errBanner) errBanner.style.display = 'none';
  try {
    const data = grid.toJSON();
    const resp = await rest.saveMap(data.tiles || {});
    if (resp && resp.success === false) {
      const msg = resp.error || 'Save failed';
      console.error('[Battle] Map save failed:', msg);
      if (errBanner) { errBanner.textContent = '\u274c ' + msg; errBanner.style.display = 'block'; }
      if (btn) { btn.textContent = '\u2717 Error'; btn.style.color = 'var(--danger)'; setTimeout(() => { btn.textContent = '\ud83d\udcbe Save'; btn.style.color = ''; btn.disabled = false; }, 2000); }
    } else {
      _clearPathDirty();
      if (resp?.tiles && grid) {
        grid.fromJSON({ tiles: resp.tiles });
        grid.addVoidNeighbors();
      }
      const path = resp?.path ? resp.path.map(([q, r]) => ({ q, r })) : null;
      grid.setDisplayPath(path);
      if (path) _clearMapError();
      if (errBanner) errBanner.style.display = 'none';
      if (btn) { btn.textContent = '\u2713 Saved'; btn.style.color = 'var(--success)'; setTimeout(() => { btn.textContent = '\ud83d\udcbe Save'; btn.style.color = ''; btn.disabled = false; }, 1200); }
    }
  } catch (err) {
    const msg = err.message || 'Network error';
    console.error('[Battle] _saveMap error:', err);
    if (errBanner) { errBanner.textContent = '\u274c ' + msg; errBanner.style.display = 'block'; }
    if (btn) { btn.textContent = '\u2717 Error'; btn.style.color = 'var(--danger)'; setTimeout(() => { btn.textContent = '\ud83d\udcbe Save'; btn.style.color = ''; btn.disabled = false; }, 2000); }
  }
}

async function _autoSave() {
  // Never auto-save while spectating another player's battle
  if (_spectateDefenderUid != null) return;
  clearTimeout(_autoSaveTimer);
  _autoSaveTimer = setTimeout(async () => {
    if (!grid) { console.warn('[Battle] Auto-save skipped: grid destroyed (view left)'); return; }
    try {
      const data = grid.toJSON();
      const resp = await rest.saveMap(data.tiles || {});
      if (resp && resp.success === false) {
        _markPathDirty();
        _showPersistentError('⚠️ ' + (resp.error || 'No valid path'));
        grid.setDisplayPath(null);
      } else {
        _clearPathDirty();
        if (resp?.tiles && grid) {
          grid.fromJSON({ tiles: resp.tiles });
          grid.addVoidNeighbors();
        }
        const path = resp?.path ? resp.path.map(([q, r]) => ({ q, r })) : null;
        grid.setDisplayPath(path);
        if (path) _clearMapError();
      }
    } catch (err) {
      console.error('[Battle] Auto-save error:', err);
    }
  }, 800);
}


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
  _battleState.attacker_army_name = msg.attacker_army_name || '';
  _battleState.attacker_username = msg.attacker_username || '';
  _battleState.time_since_start_s = msg.time_since_start_s || 0;
  if ('wave_info' in msg) {
    _battleState.wave_info = msg.wave_info;
  }

  // Activate battle mode when phase transitions to in_battle
  if (msg.phase === 'in_battle' && grid && !grid.battleActive) {
    grid.battleActive = true;
  }

  // Update castle sprite when spectating (defender's era)
  if (_spectateDefenderUid != null && msg.defender_era) {
    _updateCastleSprite(msg.defender_era);
  }

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
    defender_name: msg.defender_name || '',
    attacker_uids: msg.attacker_uids || [],
    attacker_name: msg.attacker_name || '',
    attacker_army_name: msg.attacker_army_name || '',
    attacker_username: '',
    elapsed_ms: 0,
    is_finished: false,
    defender_won: null,
    phase: 'waiting',
    time_since_start_s: 0,
    wave_info: null,
  };

  // Clear previous battle
  const wasActive = grid.battleActive;
  grid.clearBattle();

  // Load battle map
  if (msg.tiles) {
    // When the defender has pending local edits (auto-save not yet persisted),
    // skip the full reload so client changes are never clobbered by server state.
    const hasPendingChanges = _spectateDefenderUid == null && (_isDirtyPath || _autoSaveTimer != null);
    if (!hasPendingChanges) {
      grid.fromJSON({ tiles: msg.tiles });
      grid.addVoidNeighbors();
      // Only center on first setup, not on reconnect/refresh
      if (!wasActive) {
        grid._centerGrid();
      }
    }
  }

  // Store critter path for rendering — only lock path during actual battle
  if (msg.path) {
    if (_battleState.phase === 'in_battle') {
      grid.setBattlePath(msg.path);
    } else {
      // During siege: show path but don't lock it
      const path = msg.path.map(p => Array.isArray(p) ? { q: p[0], r: p[1] } : p);
      grid.setDisplayPath(path);
    }
  }

  // Place structures (towers)
  if (msg.structures) {
    for (const s of msg.structures) {
      const key = hexKey(s.q, s.r);
      const _meta = (s.select && s.select !== 'first') ? { select: s.select } : {};
      grid.setTile(s.q, s.r, s.iid, _meta);
      const tile = grid.tiles.get(key);
      if (tile) {
        tile.sid = s.sid;
        tile.structure_data = s;
      }
    }
  }

  // Only activate battle mode during actual battle, not siege
  if (_battleState.phase === 'in_battle') {
    grid.battleActive = true;
  }
  grid._dirty = true;

  // Update title with defender name when spectating
  if (_spectateDefenderUid != null) {
    if (msg.defender_name) _setBattleTitle(`\u{1F441} ${msg.defender_name}`);
  }

  // Update status
  _updateStatus('Battle starting...');
}

// ── Flying HUD Icons ────────────────────────────────────────

/**
 * Spawn a flying icon image at CSS pixel coords (cx, cy) relative to #canvas-wrap.
 * Optional label (e.g. gold amount) is shown below the icon.
 * The element animates upward and fades out over 1 second, then removes itself.
 */
function _spawnFlyingIcon(imgSrc, cx, cy, label, labelColor) {
  const wrap = container.querySelector('#canvas-wrap');
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

function _onStructureUpdate(msg) {
  if (!msg || !Array.isArray(msg.structures) || !grid) return;
  _addDebugLog(`🏗 Structure update: ${msg.structures.length} towers`);

  const NON_STRUCTURE = new Set(['path', 'castle', 'spawnpoint', 'empty', 'void', 'blocked']);

  // Clear existing structure tiles (keep path/castle/spawn)
  for (const [key, tile] of grid.tiles) {
    if (!NON_STRUCTURE.has(tile.type)) {
      const [q, r] = key.split(',').map(Number);
      grid.setTile(q, r, 'empty');
    }
  }

  // Place all structures from the server snapshot
  for (const s of msg.structures) {
    const _meta = (s.select && s.select !== 'first') ? { select: s.select } : {};
    grid.setTile(s.q, s.r, s.iid, _meta);
    const key = hexKey(s.q, s.r);
    const tile = grid.tiles.get(key);
    if (tile) {
      tile.sid = s.sid;
      tile.structure_data = s;
    }
  }

  grid._invalidateBase();
  grid._dirty = true;
}

function _onBattleUpdate(msg) {
  if (!msg) return;

  // Battle updates mean we're in active battle — lock the path
  if (grid && !grid.battleActive) {
    grid.battleActive = true;
  }

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

    // Spawn flying icons for critters removed this tick (server-reported reason)
    if (msg.removed_critters && Array.isArray(msg.removed_critters)) {
      for (const rc of msg.removed_critters) {
        if (rc.reason === 'died') {
          // Critter killed — coin at its last position
          const raw = grid._getCritterPixelPos(rc.path_progress, grid.hexSize);
          const cx = raw.x * grid.zoom + grid.offsetX;
          const cy = raw.y * grid.zoom + grid.offsetY;
          const goldLabel = rc.value != null ? Math.round(rc.value) : null;
          _spawnFlyingIcon('/assets/sprites/hud/flying_coin.webp', cx, cy, goldLabel);
        } else if (rc.reason === 'reached') {
          // Critter reached castle — heart at end of path
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

  // Update shot positions (all shots with path_progress)
  if (msg.shots && Array.isArray(msg.shots)) {
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
    if (msg.defender_life != null) {
      grid.setDefenderLives(msg.defender_life, msg.defender_max_life);
    }

    if ('wave_info' in msg) {
      _battleState.wave_info = msg.wave_info;
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
  _battleState.phase = 'finished';

  // Keep critters visible briefly, then clean up
  setTimeout(() => {
    grid.clearBattle();
    // Apply the freshly-computed post-battle path from the server
    const path = msg.path ? msg.path.map(([q, r]) => ({ q, r })) : null;
    grid.setDisplayPath(path);
    if (!path) _showPersistentError('⚠️ No path from spawn to castle — please remove obstacles.');
    else _clearMapError();
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
  if (attackerEl) {
    const armyName = _battleState.attacker_army_name || _battleState.attacker_name || '-';
    const username = _battleState.attacker_username;
    attackerEl.textContent = username ? `${armyName} (${username})` : armyName;
  }
  
  // Update phase
  let statusText = 'Waiting...';
  if (_battleState.phase === 'travelling') {
    statusText = '🚶 Traveling';
  } else if (_battleState.phase === 'in_siege') {
    statusText = '🛡 Siege';
  } else if (_battleState.phase === 'in_battle') {
    statusText = '⚔ Battle';
  } else if (_battleState.phase === 'finished') {
    statusText = '✓ Complete';
  }
  _updateStatus(statusText);

  // Show/hide Fight now! button (only during siege, only when defending — not spectating)
  const fightNowItem = container.querySelector('#fight-now-item');
  if (fightNowItem) {
    const showFightNow = _pendingAttackId !== null && _battleState.phase === 'in_siege' && _spectateDefenderUid == null;
    fightNowItem.style.display = showFightNow ? '' : 'none';
  }

  // Update next wave with countdown
  const nextWaveEl = container.querySelector('#battle-next-wave');
  if (nextWaveEl) {
    const wi = _battleState.wave_info;
    if (_battleState.phase === 'travelling') {
      // During travel: show arrival countdown from the attack summary
      const attackSummary = (st.summary?.attacks_incoming || []).find(a => a.attack_id === _pendingAttackId)
        || (st.summary?.attacks_outgoing || []).find(a => a.attack_id === _pendingAttackId);
      const etaSec = attackSummary?.eta_seconds ?? null;
      if (wi && etaSec !== null) {
        const critterCount = Math.max(1, Math.floor(wi.slots / (wi.critter_slot_cost || 1)));
        nextWaveEl.textContent =
          `Wave (${wi.wave_index}/${wi.total_waves}): ${critterCount}× ${wi.critter_name}, eta: ${Math.ceil(etaSec)}s`;
      } else if (etaSec !== null) {
        nextWaveEl.textContent = `Arriving in ${Math.ceil(etaSec)}s`;
      } else {
        nextWaveEl.textContent = '-';
      }
    } else if (wi) {
      // During siege, time_since_start_s is negative (= -siege_remaining_s).
      // Guard with phase check: when attack_phase_changed fires before the next
      // battle_status arrives, time_since_start_s can still be stale-negative
      // even though the battle has started — avoid adding phantom siege time.
      const siegeRemainingMs = _battleState.phase === 'in_siege' && _battleState.time_since_start_s < 0
        ? -_battleState.time_since_start_s * 1000 : 0;
      const totalCountdownSec = Math.ceil((siegeRemainingMs + wi.next_critter_ms) / 1000);
      const timeStr = totalCountdownSec > 0 ? `${totalCountdownSec}s` : 'now';
      const critterCount = Math.max(1, Math.floor(wi.slots / (wi.critter_slot_cost || 1)));
      nextWaveEl.textContent =
        `Wave (${wi.wave_index}/${wi.total_waves}): ${critterCount}× ${wi.critter_name}, eta: ${timeStr}`;
    } else {
      nextWaveEl.textContent = _battleState.phase === 'in_battle' ? 'All waves done' : '-';
    }
  }

  // Update time — hide elapsed timer during travel (battle not yet started)
  const elapsedEl = container.querySelector('#battle-elapsed');
  if (elapsedEl) {
    elapsedEl.textContent = _battleState.phase === 'travelling'
      ? '--:--'
      : _formatTime(_battleState.time_since_start_s * 1000);
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
  title.textContent = won ? '🛡 Defender Victory' : '⚔ Attacker Victory';
  title.style.color = won ? 'var(--green, #4caf50)' : 'var(--red, #d32f2f)';

  const myUid = st?.auth?.uid;
  const isDefender = myUid != null && myUid == _battleState.defender_uid;

  const defenderName = _battleState.defender_name || 'Defender';
  const armyPart = msg.army_name || _battleState.attacker_army_name || 'the attacker';
  const usernamePart = _battleState.attacker_username ? ` (${_battleState.attacker_username})` : '';
  const attackLabel = `${armyPart}${usernamePart}`;

  let html = '<div style="margin-top:8px">';

  // Outcome sentence
  if (won) {
    html += `<p style="text-align:center">${defenderName} successfully defeated ${attackLabel}.</p>`;
  } else {
    html += `<p style="text-align:center">${attackLabel} broke through ${defenderName}'s defenses.</p>`;
  }

  // ── Battle Statistics ────────────────────────────────────────────
  {
    const sep = `style="margin-top:12px;border-top:1px solid rgba(255,255,255,0.12);padding-top:8px"`;
    const liSt = `style="padding:3px 0"`;
    html += `<div ${sep}>`;
    html += `<strong style="font-size:0.9em;text-transform:uppercase;letter-spacing:.04em">📊 Battle Statistics</strong>`;
    html += `<ul style="list-style:none;padding:0;margin:5px 0 0 0">`;

    // Attacker stats
    const spawned = msg.critters_spawned ?? 0;
    const reached = msg.critters_reached ?? 0;
    const killed = msg.critters_killed ?? 0;
    const waves = msg.num_waves ?? 0;
    html += `<li ${liSt}>⚔ Attacker: ${spawned} critters in ${waves} waves — ${reached} reached goal, ${killed} killed</li>`;

    // Defender stats
    const towers = msg.num_towers ?? 0;
    const goldEarned = Math.round(msg.defender_gold_earned ?? 0);
    html += `<li ${liSt}>🛡 Defender: ${towers} towers — ${goldEarned} gold earned</li>`;

    // Duration
    if (msg.duration_s > 0) {
      const dur = msg.duration_s;
      const dm = Math.floor(dur / 60);
      const ds = Math.floor(dur % 60);
      html += `<li ${liSt}>⏱ Duration: ${dm > 0 ? dm + 'm ' : ''}${ds}s</li>`;
    }

    html += '</ul></div>';
  }

  // ── Gold earned by defender ────────────────────────────────────────
  if (isDefender && msg.defender_gold_earned > 0) {
    const sep = `style="margin-top:12px;border-top:1px solid rgba(255,255,255,0.12);padding-top:8px"`;
    html += `<div ${sep}>`;
    html += `<strong style="font-size:0.9em;text-transform:uppercase;letter-spacing:.04em">💰 Gold Earned</strong>`;
    html += `<p style="margin:5px 0 0 0">+${Math.round(msg.defender_gold_earned).toLocaleString()} Gold from defeated attackers</p>`;
    html += `</div>`;
  }

  // ── Loot section (only on defender loss) ──────────────────────────
  const loot = msg.loot || {};
  const hasLoot = loot.knowledge || loot.culture > 0 || loot.artefact;

  if (!won) {
    const items = st?.items || {};
    const sep = `style="margin-top:12px;border-top:1px solid rgba(255,255,255,0.12);padding-top:8px"`;
    const liSt = `style="padding:3px 0"`;
    const mutedSt = `style="padding:3px 0;color:var(--muted,#888)"`;

    // ── Section 1: Stolen from you (culture + artefact) ──
    html += `<div ${sep}>`;
    html += `<strong style="font-size:0.9em;text-transform:uppercase;letter-spacing:.04em">🗡 Stolen from you</strong>`;
    html += `<ul style="list-style:none;padding:0;margin:5px 0 0 0">`;
    if (loot.culture > 0) {
      html += `<li ${liSt}>🎭 Culture: <strong>-${Math.round(loot.culture)}</strong></li>`;
    } else {
      html += `<li ${mutedSt}>🎭 Culture: –</li>`;
    }
    if (loot.artefact) {
      const artefactName = items?.artefacts?.[loot.artefact]?.name || loot.artefact;
      html += `<li ${liSt}>⚗️ Artefact: <strong>${artefactName}</strong></li>`;
    } else {
      html += `<li ${mutedSt}>⚗️ Artefact: –</li>`;
    }
    html += '</ul></div>';

    // ── Section 2: The attacker gets (knowledge) ──
    html += `<div ${sep}>`;
    html += `<strong style="font-size:0.9em;text-transform:uppercase;letter-spacing:.04em">🎓 The Attacker gets</strong>`;
    html += `<ul style="list-style:none;padding:0;margin:5px 0 0 0">`;
    if (loot.knowledge) {
      const kn = loot.knowledge;
      html += `<li ${liSt}>📖 ${kn.pct}% of <strong>${kn.name}</strong> → +${kn.amount} 🧪</li>`;
    } else {
      html += `<li ${mutedSt}>📖 Knowledge: –</li>`;
    }
    html += '</ul></div>';
  }

  // ── Section 3: Life restored (always shown after a loss) ──
  if (!won && loot.life_restored > 0) {
    const sep = `style="margin-top:12px;border-top:1px solid rgba(255,255,255,0.12);padding-top:8px"`;
    html += `<div ${sep}>`;
    html += `<strong style="font-size:0.9em;text-transform:uppercase;letter-spacing:.04em">❤️ Life Restored after Battle</strong>`;
    html += `<p style="margin:5px 0 0 0">+${loot.life_restored}</p>`;
    html += `</div>`;
  }

  html += '</div>';
  content.innerHTML = html;

  // ── AI-Feedback buttons (only for AI attacks) ──────────────────────
  const feedbackRow = container.querySelector('#summary-feedback-row');
  if (feedbackRow) feedbackRow.remove();

  if (msg.attacker_uid === 0 && msg.army_name) {
    const row = document.createElement('div');
    row.id = 'summary-feedback-row';
    row.style.cssText = 'display:flex;gap:8px;margin-top:12px;justify-content:center;';
    row.innerHTML = `
      <button id="feedback-easy" style="background:var(--green,#388e3c);color:#fff;border:none;padding:6px 16px;border-radius:var(--radius);cursor:pointer;font-size:13px;">✓ Too Easy</button>
      <button id="feedback-hard" style="background:var(--red,#d32f2f);color:#fff;border:none;padding:6px 16px;border-radius:var(--radius);cursor:pointer;font-size:13px;">✗ Too Hard</button>
    `;
    content.appendChild(row);

    const sendFeedback = async (rating) => {
      row.querySelectorAll('button').forEach(b => { b.disabled = true; b.style.opacity = '0.6'; });
      try {
        await rest.battleFeedback(msg.army_name, rating);
      } catch (e) {
        console.warn('[feedback] failed:', e);
      }
      row.innerHTML = '<span style="color:var(--text-muted);font-size:12px;">✓ Feedback sent</span>';
    };

    row.querySelector('#feedback-easy').addEventListener('click', () => sendFeedback('too_easy'));
    row.querySelector('#feedback-hard').addEventListener('click', () => sendFeedback('too_hard'));
  }

  overlay.style.display = 'flex';
}

// ── Export ──────────────────────────────────────────────────

export default {
  id: 'defense',
  title: 'Defense',
  init,
  enter,
  leave,
};
