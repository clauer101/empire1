/**
 * Empire Composer — hex map editor with drag-and-drop tile placement.
 *
 * Features:
 *  - 8x8 hex grid rendered on Canvas
 *  - Tile palette with drag-and-drop
 *  - Click-to-inspect tile properties
 *  - Save / Load / Clear map
 *  - Export / Import JSON
 */

import { HexGrid, TILE_TYPES, getTileType, registerTileType } from '../lib/hex_grid.js';
import { hexKey } from '../lib/hex.js';
import { eventBus } from '../events.js';
import { rest } from '../rest.js';

/** @type {import('../api.js').ApiClient} */
let api;
/** @type {import('../state.js').StateStore} */
let st;
/** @type {HTMLElement} */
let container;
let _unsub = [];

/** @type {HexGrid|null} */
let grid = null;

const STORAGE_KEY = 'e3_map_editor';

// Battle state
let _battleActive = false;

// ── View lifecycle ──────────────────────────────────────────

function init(el, _api, _state) {
  container = el;
  api = _api;
  st = _state;

  container.innerHTML = `
    <div class="hex-editor">
      <div class="hex-editor__toolbar">
        <h2 class="hex-editor__title">⬡ Map Editor</h2>
        <div class="hex-editor__actions">
          <button id="map-save" class="btn-sm" title="Karte speichern">Save</button>
          <button id="map-battle" class="btn-ghost btn-sm" title="Schlacht starten">Battle</button>
        </div>
      </div>

      <div id="map-error-banner" style="display:none;padding:8px 12px;margin:0 0 8px 0;background:#8a3a3a;color:#ffcccc;border-left:4px solid #c85a5a;border-radius:2px;font-size:0.9rem;"></div>

      <div class="hex-editor__body">
        <aside class="hex-editor__palette" id="tile-palette"></aside>
        <div class="hex-editor__canvas-wrap" id="canvas-wrap">
          <canvas id="hex-canvas"></canvas>
        </div>
        <aside class="hex-editor__props" id="tile-props">
          <div class="panel">
            <div class="panel-header">Tile Properties</div>
            <div id="props-content" class="props-empty">
              Click a tile to inspect
            </div>
          </div>
          <div class="panel" style="margin-top:8px">
            <div class="panel-header">Map Info</div>
            <div id="map-info">
              <div class="panel-row"><span class="label">Tiles</span><span class="value" id="info-total">0</span></div>
              <div class="panel-row"><span class="label">Placed</span><span class="value" id="info-placed">0</span></div>
              <div class="panel-row"><span class="label">Paths</span><span class="value" id="info-paths">0</span></div>
              <div class="panel-row"><span class="label">Spawns</span><span class="value" id="info-spawns">0</span></div>
              <div class="panel-row"><span class="label">Towers</span><span class="value" id="info-towers">0</span></div>
            </div>
          </div>
        </aside>
      </div>
    </div>
  `;
}

async function enter() {
  _initCanvas();
  _bindToolbar();

  // Load items from server to get unlocked structures
  try {
    await rest.getItems();
  } catch (err) {
    console.warn('[Composer] could not load items:', err.message);
  }

  // Subscribe to item updates
  _unsub.push(eventBus.on('state:items', _buildPalette));

  // Subscribe to battle events (delta-based)
  _unsub.push(eventBus.on('server:battle_setup', _onBattleSetup));
  _unsub.push(eventBus.on('server:battle_update', _onBattleUpdate));
  _unsub.push(eventBus.on('server:battle_summary', _onBattleSummary));

  _buildPalette();

  // Load map from server, fallback to localStorage
  try {
    const response = await rest.loadMap();
    if (response && response.tiles) {
      grid.fromJSON({ tiles: response.tiles });
      console.log('[Composer] Map loaded from server');
    } else {
      _tryLoadFromStorage();
    }
  } catch (err) {
    console.warn('[Composer] could not load map from server, using localStorage:', err.message);
    _tryLoadFromStorage();
  }

  _updateMapInfo();
}

function leave() {
  _unsub.forEach(fn => fn());
  _unsub = [];
  if (grid) { grid.destroy(); grid = null; }
}

// ── Palette ─────────────────────────────────────────────────

// Color palette for dynamically generated structure colors
const STRUCTURE_COLORS = [
  { color: '#3a5a4a', stroke: '#4a7a5a' },
  { color: '#4a4a6a', stroke: '#5a5a8a' },
  { color: '#5a3a3a', stroke: '#7a4a4a' },
  { color: '#3a4a5a', stroke: '#4a6a7a' },
  { color: '#5a4a3a', stroke: '#7a6a4a' },
  { color: '#4a5a4a', stroke: '#6a7a6a' },
];

function _buildPalette() {
  const palette = container.querySelector('#tile-palette');
  palette.innerHTML = '<div class="panel-header">Tile Palette</div>';

  // Register structures from server as tile types
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

  // Static categories
  const staticCategories = {
    'Basic': ['castle', 'spawnpoint', 'path', 'empty'],
  };

  // Render static categories
  for (const [catName, types] of Object.entries(staticCategories)) {
    const catEl = _createCategoryEl(catName, types);
    palette.appendChild(catEl);
  }

  // Render dynamic structures category (from server)
  const structureIds = Object.keys(structures);
  if (structureIds.length > 0) {
    const structCat = _createCategoryEl('Türme', structureIds);
    palette.appendChild(structCat);
  } else {
    const hint = document.createElement('div');
    hint.className = 'palette-hint';
    hint.innerHTML = '<em>Keine Türme freigeschaltet.<br>Forschung benötigt!</em>';
    palette.appendChild(hint);
  }
}

function _createCategoryEl(catName, typeIds) {
  const catEl = document.createElement('div');
  catEl.className = 'palette-category';
  catEl.innerHTML = '<div class="palette-category__label">' + catName + '</div>';

  for (const typeId of typeIds) {
    const t = getTileType(typeId);
    const item = document.createElement('div');
    item.className = 'palette-item';
    item.draggable = true;
    item.dataset.tileType = typeId;
    item.innerHTML = 
      '<span class="palette-swatch" style="background:' + t.color + ';border-color:' + t.stroke + '"></span>' +
      '<span class="palette-label">' + t.label + '</span>';

    item.addEventListener('dragstart', (e) => {
      e.dataTransfer.setData('text/tile-type', typeId);
      e.dataTransfer.effectAllowed = 'copy';
      item.classList.add('dragging');
    });
    item.addEventListener('dragend', () => {
      item.classList.remove('dragging');
    });

    // Click-to-paint brush
    item.addEventListener('click', () => {
      _setActiveBrush(typeId);
    });

    catEl.appendChild(item);
  }

  return catEl;
}

let _activeBrush = null;

function _setActiveBrush(typeId) {
  if (_activeBrush === typeId) {
    _activeBrush = null;
    container.querySelectorAll('.palette-item').forEach(el => el.classList.remove('active'));
    return;
  }
  _activeBrush = typeId;
  container.querySelectorAll('.palette-item').forEach(el => {
    el.classList.toggle('active', el.dataset.tileType === typeId);
  });
}

// ── Canvas ──────────────────────────────────────────────────

function _initCanvas() {
  const canvas = container.querySelector('#hex-canvas');

  grid = new HexGrid({
    canvas,
    cols: 6,
    rows: 6,
    hexSize: 28,
    onTileClick: _onTileClick,
    onTileHover: _onTileHover,
    onTileDrop: _onTileDrop,
  });
  // Initialize map: void at edges, empty in interior, then apply initial tiles
  _initializeMap();
}

function _initializeMap() {
  // Clear the prefilled 6x6 grid — start with only the defined tiles
  grid.tiles.clear();

  // Default initial tiles (used when no server data is loaded)
  const initialTiles = {
    '0,0': 'empty',
    '0,1': 'empty',
    '1,0': 'empty'
  };

  for (const [key, type] of Object.entries(initialTiles)) {
    grid.tiles.set(key, { type });
  }
  grid.addVoidNeighbors();
  grid._centerGrid();
  grid._dirty = true;
}

function _onTileClick(q, r, tile) {
  if (_activeBrush && _activeBrush !== 'void') {
    grid.setTile(q, r, _activeBrush);
    grid.addVoidNeighbors();
    _updateMapInfo();
    _autoSave();
  }
  _showProperties(q, r, grid.getTile(q, r));
}

function _onTileHover(_q, _r) {
  // Future: coordinate display
}

function _onTileDrop(q, r, tileTypeId) {
  if (tileTypeId !== 'void') {
    grid.addVoidNeighbors();
    _updateMapInfo();
    _autoSave();
  }
}

// ── Property Panel ──────────────────────────────────────────

function _showProperties(q, r, tile) {
  const content = container.querySelector('#props-content');
  if (!tile) {
    content.innerHTML = '<span class="props-empty">No tile selected</span>';
    return;
  }

  const t = getTileType(tile.type);

  // Build extra info for structures from server data
  let extraInfo = '';
  if (t.serverData) {
    const s = t.serverData;
    extraInfo = 
      '<div class="props-divider"></div>' +
      '<div class="props-section-label">Turm-Stats</div>' +
      '<div class="props-row"><span class="label">Damage</span><span class="value">' + (s.damage || 0) + '</span></div>' +
      '<div class="props-row"><span class="label">Range</span><span class="value">' + (s.range || 0) + ' hex</span></div>' +
      '<div class="props-row"><span class="label">Reload</span><span class="value">' + (s.reload_time_ms || 0) + ' ms</span></div>' +
      '<div class="props-row"><span class="label">Shot</span><span class="value">' + (s.shot_type || 'normal') + '</span></div>';
    if (s.requirements && s.requirements.length > 0) {
      extraInfo += '<div class="props-row"><span class="label">Requires</span><span class="value mono">' + s.requirements.join(', ') + '</span></div>';
    }
  }

  content.innerHTML = 
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
      extraInfo +
      '<div class="props-divider"></div>' +
      '<label>Change Type' + (tile.type === 'void' ? ' (Locked)' : '') + '</label>' +
      '<select id="props-type-select" style="margin-top:4px"' + (tile.type === 'void' ? ' disabled' : '') + '>' +
        Object.values(TILE_TYPES).filter(function(tt) { return tt.id !== 'void'; }).map(function(tt) {
          return '<option value="' + tt.id + '"' + (tt.id === tile.type ? ' selected' : '') + '>' + tt.label + '</option>';
        }).join('') +
      '</select>' +
    '</div>';

  const select = content.querySelector('#props-type-select');
  if (!select.disabled) {
    select.addEventListener('change', function(e) {
      grid.setTile(q, r, e.target.value);
      _showProperties(q, r, grid.getTile(q, r));
      _updateMapInfo();
      _autoSave();
    });
  }
}

// ── Map Info ────────────────────────────────────────────────

function _updateMapInfo() {
  if (!grid) return;
  let placed = 0, paths = 0, spawns = 0, towers = 0;
  const items = st.items || {};
  const serverStructures = items.structures || {};

  for (const [, tile] of grid.tiles) {
    const t = tile.type || 'empty';
    if (t !== 'empty' && t !== 'void') placed++;
    if (t === 'path') paths++;
    if (t.startsWith('spawn')) spawns++;
    if (serverStructures[t] || t === 'tower_slot') towers++;
  }

  const el = function(id) { return container.querySelector('#' + id); };
  if (el('info-total'))  el('info-total').textContent  = grid.tiles.size;
  if (el('info-placed')) el('info-placed').textContent = placed;
  if (el('info-paths'))  el('info-paths').textContent  = paths;
  if (el('info-spawns')) el('info-spawns').textContent = spawns;
  if (el('info-towers')) el('info-towers').textContent = towers;
}

// ── Toolbar ─────────────────────────────────────────────────

function _bindToolbar() {
  const $ = function(id) { return container.querySelector('#' + id); };

  $('map-save').addEventListener('click', async function() {
    try {
      const data = grid.toJSON();
      const tiles = data.tiles || {};
      const resp = await rest.saveMap(tiles);
      
      if (resp && resp.success === false) {
        _showMapError(resp.error || 'Save failed');
        _flashButton($('map-save'), 'Failed!');
        return;
      }
      
      _flashButton($('map-save'), 'Saved!');
    } catch (err) {
      _showMapError(err.message);
      _flashButton($('map-save'), 'Error!');
      console.error('[Composer] save error:', err.message);
    }
  });

  $('map-battle').addEventListener('click', function() {
    // Navigate to battle view — WS connection is managed there
    window.location.hash = '#battle';
  });
}

function _flashButton(btn, text) {
  const orig = btn.textContent;
  btn.textContent = text;
  btn.style.color = 'var(--success)';
  setTimeout(function() {
    btn.textContent = orig;
    btn.style.color = '';
  }, 1200);
}

function _showMapError(message) {
  const banner = container.querySelector('#map-error-banner');
  banner.textContent = '❌ ' + message;
  banner.style.display = 'block';
  setTimeout(function() {
    banner.style.display = 'none';
  }, 5000);
}

// ── Persistence (localStorage + Server) ────────────────────

function _tryLoadFromStorage() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) {
      grid.fromJSON(JSON.parse(raw));
    }
  } catch (e) {
    console.warn('[Composer] load failed', e);
  }
}

let _autoSaveTimeout = null;

function _autoSave() {
  // Debounce server save (max every 1 second)
  if (_autoSaveTimeout) clearTimeout(_autoSaveTimeout);
  _autoSaveTimeout = setTimeout(async function() {
    try {
      const data = grid.toJSON();
      const tiles = data.tiles || {};
      const resp = await rest.saveMap(tiles);
      if (resp && resp.success === false) {
        console.warn('[Composer] ⚠ Auto-save rejected:', resp.error);
      } else {
        console.log('[Composer] ✓ Auto-saved to server');
      }
    } catch (err) {
      console.error('[Composer] ✗ Server save failed:', err.message);
    }
  }, 1000);  // Reduced from 2000ms to 1000ms for faster persistence
}

// ── Battle events (delta-based, Java-style) ─────────────────

function _onBattleSetup(msg) {
  console.log('[Composer] Battle setup:', msg);
  grid.clearBattle();
  _battleActive = true;
  grid._dirty = true;
}

function _onBattleUpdate(msg) {
  if (!msg) return;

  // Spawn new critters (client will autonomously move them along path)
  if (msg.new_critters && msg.new_critters.length > 0) {
    for (const c of msg.new_critters) {
      console.log(
        '[SPAWN] Critter spawned: cid=%d type=%s speed=%.1f path_len=%d',
        c.cid, c.iid, c.speed || 0, c.path ? c.path.length : 0
      );
      grid.addBattleCritter(c.cid, c.path, c.speed);
    }
  }

  // Remove dead critters
  if (msg.dead_critter_ids && msg.dead_critter_ids.length > 0) {
    for (const cid of msg.dead_critter_ids) {
      console.log('[SPAWN] Critter killed: cid=%d', cid);
      grid.removeBattleCritter(cid);
    }
  }

  // Remove finished critters (reached castle)
  if (msg.finished_critter_ids && msg.finished_critter_ids.length > 0) {
    for (const cid of msg.finished_critter_ids) {
      console.log('[SPAWN] Critter finished: cid=%d', cid);
      grid.removeBattleCritter(cid);
    }
  }

  // Shots (visual only — future)
  if (msg.new_shots && msg.new_shots.length > 0) {
    console.log('[SPAWN] Shots fired: count=%d', msg.new_shots.length);
  }

  grid._dirty = true;
}

function _onBattleSummary(msg) {
  console.log('[Composer] Battle summary:', msg);
  _battleActive = false;
  // Keep critters visible briefly, then clean up
  setTimeout(() => {
    grid.clearBattle();
  }, 1500);
}

// ── Export ───────────────────────────────────────────────────

export default {
  id: 'composer',
  title: 'Map Editor',
  init,
  enter,
  leave,
};
