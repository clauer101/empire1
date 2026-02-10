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
 */

import { HexGrid, getTileType, registerTileType } from '../lib/hex_grid.js';
import { hexKey } from '../lib/hex.js';
import { eventBus } from '../events.js';

/** @type {import('../api.js').ApiClient} */
let api;
/** @type {import('../state.js').StateStore} */
let st;
/** @type {HTMLElement} */
let container;
let _unsub = [];

/** @type {HexGrid|null} */
let grid = null;

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
  api = _api;
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
  _initCanvas();

  // Subscribe to battle events
  _unsub.push(eventBus.on('server:battle_setup', _onBattleSetup));
  _unsub.push(eventBus.on('server:battle_update', _onBattleUpdate));
  _unsub.push(eventBus.on('server:battle_summary', _onBattleSummary));
  _unsub.push(eventBus.on('server:battle_status', _onBattleStatus));

  // Subscribe to items for structure tile types
  _unsub.push(eventBus.on('state:items', _registerStructureTileTypes));

  // Load items to get structure tiles
  try {
    await api.getItems();
  } catch (err) {
    console.warn('[Battle] could not load items:', err.message);
  }

  _registerStructureTileTypes();

  // Subscribe to battle updates for defending empire
  // (check if there's an active attack we should monitor)
  _subscribeToActiveAttacks();

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
  
  // Unsubscribe from battle updates
  _unsubscribeFromBattle();
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

async function _subscribeToActiveAttacks() {
  // Check if user is involved in any attack (as defender)
  const summary = st.summary;
  if (!summary || !summary.uid) return;
  
  // Subscribe to our own uid (will receive updates when we're defended)
  await api._request({
    type: 'battle_register',
    target_uid: summary.uid,
  }, null);
  console.log('[Battle] Subscribed to battle updates for uid=' + summary.uid);
}

async function _unsubscribeFromBattle() {
  const summary = st.summary;
  if (!summary || !summary.uid) return;
  
  await api._request({
    type: 'battle_unregister',
    target_uid: summary.uid,
  }, null);
  console.log('[Battle] Unsubscribed from battle updates');
}

function _onBattleStatus(msg) {
  if (!msg) return;
  
  // Check if wave changed (reset spawned counter)
  if (_battleState.current_wave && msg.current_wave) {
    if (_battleState.current_wave_id !== msg.current_wave.wave_id) {
      _battleState.current_wave_spawned = 0;
      _battleState.current_wave_id = msg.current_wave.wave_id;
    }
  } else if (msg.current_wave) {
    _battleState.current_wave_id = msg.current_wave.wave_id;
  }
  
  // Update battle state
  _battleState.phase = msg.phase || 'waiting';
  _battleState.defender_uid = msg.defender_uid;
  _battleState.defender_name = msg.defender_name || 'Unknown';
  _battleState.attacker_uid = msg.attacker_uid;
  _battleState.attacker_name = msg.attacker_name || 'Unknown';
  _battleState.time_since_start_s = msg.time_since_start_s || 0;
  _battleState.current_wave = msg.current_wave;
  _battleState.next_wave = msg.next_wave;
  _battleState.total_waves = msg.total_waves || 0;
  _battleState.next_wave_countdown_ms = msg.next_wave_countdown_ms || 0;
  
  // Update current wave spawned counter from server
  if (msg.current_wave_critter_pointer !== undefined) {
    _battleState.current_wave_spawned = msg.current_wave_critter_pointer;
  }
  
  // Update status display
  _updateStatusFromBattleMsg ();
}

function _onBattleSetup(msg) {
  console.log('[Battle] Battle setup:', msg);

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
    current_wave: null,
    current_wave_id: -1,
    next_wave: null,
    total_waves: 0,
    time_since_start_s: 0,
    current_wave_spawned: 0,
    next_wave_countdown_ms: 0,
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
    for (const cid of msg.dead_critter_ids) {
      console.log('[Battle] Critter killed: cid=%d', cid);
      grid.removeBattleCritter(cid);
    }
  }

  // Remove finished critters (reached castle)
  if (msg.finished_critter_ids && msg.finished_critter_ids.length > 0) {
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
