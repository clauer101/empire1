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

// ── View lifecycle ──────────────────────────────────────────

function init(el, _api, _state) {
  container = el;
  api = _api;
  st = _state;

  container.innerHTML = `
    <div class="hex-editor">
      <div class="hex-editor__toolbar">
        <h2 class="hex-editor__title">⬡ Map Editor</h2>
      </div>

      <div id="map-error-banner" style="display:none;padding:8px 12px;margin:0 0 8px 0;background:#8a3a3a;color:#ffcccc;border-left:4px solid #c85a5a;border-radius:2px;font-size:0.9rem;"></div>

      <div class="hex-editor__body">
        <aside class="hex-editor__palette" id="tile-palette"></aside>
        <div class="hex-editor__canvas-wrap" id="canvas-wrap">
          <button id="map-save" class="btn-sm" style="position:absolute;top:12px;right:12px;z-index:10;" title="Karte speichern">Save</button>
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
      
      <!-- Mobile Overlay for Tile Properties -->
      <div class="tile-overlay" id="tile-overlay" style="display:none;">
        <div class="tile-overlay__content">
          <div class="tile-overlay__header">
            <h3>Tile Properties</h3>
            <button class="tile-overlay__close" id="tile-overlay-close">✕</button>
          </div>
          <div class="tile-overlay__body" id="tile-overlay-body">
          </div>
        </div>
      </div>
    </div>
  `;
}

async function enter() {
  _initCanvas();
  _bindToolbar();
  _bindMobileOverlay();

  // Load items from server to get unlocked structures
  try {
    await rest.getItems();
  } catch (err) {
    console.warn('[Composer] could not load items:', err.message);
  }

  // Subscribe to item updates
  _unsub.push(eventBus.on('state:items', _buildPalette));

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
  _loadMapBackground();
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
      icon: null,
      spriteUrl: info.sprite || null,
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
    const structCat = _createCategoryEl('Towers', structureIds);
    palette.appendChild(structCat);
  } else {
    const hint = document.createElement('div');
    hint.className = 'palette-hint';
    hint.innerHTML = '<em>No towers unlocked.<br>Research required!</em>';
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

// ── Map background ──────────────────────────────────────────

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
    console.warn('[Composer] map background not loaded:', e.message);
  }
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

// ── Map Reload ──────────────────────────────────────────────

async function _reloadMap() {
  try {
    const response = await rest.loadMap();
    if (response && response.tiles) {
      grid.fromJSON({ tiles: response.tiles });
      grid.addVoidNeighbors();
      grid._centerGrid();
      grid._dirty = true;
      _updateMapInfo();
      console.log('[Composer] Map reloaded from server');
    }
  } catch (err) {
    console.error('[Composer] Failed to reload map:', err);
    throw err;
  }
}

// ── Property Panel ──────────────────────────────────────────

function _bindMobileOverlay() {
  const closeBtn = container.querySelector('#tile-overlay-close');
  const overlay = container.querySelector('#tile-overlay');
  
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

function _showProperties(q, r, tile) {
  const content = container.querySelector('#props-content');
  const overlayBody = container.querySelector('#tile-overlay-body');
  const overlay = container.querySelector('#tile-overlay');
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
      '<div class="props-row"><span class="label">Shot Speed</span><span class="value">' + (s.shot_speed || 0) + ' hex/s</span></div>' +
      '<div class="props-row"><span class="label">Shot Type</span><span class="value">' + (s.shot_type || 'normal') + '</span></div>';
    if (s.effects && Object.keys(s.effects).length > 0) {
      const effectsStr = Object.entries(s.effects).map(([k, v]) => k + ': ' + v).join(', ');
      extraInfo += '<div class="props-row"><span class="label">Effects</span><span class="value">' + effectsStr + '</span></div>';
    }
    if (s.requirements && s.requirements.length > 0) {
      extraInfo += '<div class="props-row"><span class="label">Requires</span><span class="value mono">' + s.requirements.join(', ') + '</span></div>';
    }
  }

  // Buy tile button for void tiles
  let buyButton = '';
  if (tile.type === 'void') {
    const tilePrice = st.summary?.tile_price || 0;
    const currentGold = st.summary?.resources?.gold || 0;
    const canAfford = currentGold >= tilePrice;
    
    buyButton = 
      '<div class="props-divider"></div>' +
      '<div class="props-row">' +
        '<span class="label">Cost</span>' +
        '<span class="value" style="color:' + (canAfford ? 'var(--text)' : 'var(--danger)') + '">' +
          '💰 ' + Math.round(tilePrice) + ' Gold' +
        '</span>' +
      '</div>' +
      '<button id="buy-tile-btn" class="btn" style="width:100%;margin-top:8px;"' + 
        (canAfford ? '' : ' disabled title="Not enough gold"') + '>Buy Tile</button>' +
      '<div id="buy-tile-msg" style="margin-top:6px;font-size:12px;text-align:center;"></div>';
  }

  const propsHTML = 
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
      buyButton +
    '</div>';
  
  // Update desktop sidebar
  content.innerHTML = propsHTML;
  
  // Update mobile overlay
  if (overlayBody) {
    overlayBody.innerHTML = propsHTML;
    // Show overlay on mobile (will be hidden by CSS on desktop)
    if (window.innerWidth <= 1100) {
      overlay.style.display = 'flex';
    }
  }

  // Attach buy button handler (works for both desktop sidebar and mobile overlay)
  const buyHandler = async (btnElement, msgElement) => {
    btnElement.disabled = true;
    msgElement.textContent = '';
    
    try {
      const resp = await rest.buyTile(q, r);
      if (resp.success) {
        const costText = resp.cost ? ` (${Math.round(resp.cost)} gold)` : '';
        msgElement.textContent = '✓ Tile purchased!' + costText;
        msgElement.style.color = 'var(--success)';
        // Reload summary to update tile_price and gold
        await rest.getSummary();
        // Reload the map immediately based on server response
        await _reloadMap();
        _showProperties(q, r, grid.getTile(q, r));
        // Close mobile overlay after successful purchase
        if (overlay && window.innerWidth <= 1100) {
          overlay.style.display = 'none';
        }
      } else {
        msgElement.textContent = '✗ ' + (resp.error || 'Failed to buy tile');
        msgElement.style.color = 'var(--danger)';
      }
    } catch (err) {
      msgElement.textContent = '✗ ' + err.message;
      msgElement.style.color = 'var(--danger)';
    } finally {
      btnElement.disabled = false;
      setTimeout(() => { msgElement.textContent = ''; }, 3000);
    }
  };

  // Bind handler to desktop sidebar button
  const buyBtn = content.querySelector('#buy-tile-btn');
  const msgEl = content.querySelector('#buy-tile-msg');
  if (buyBtn && msgEl) {
    buyBtn.addEventListener('click', () => buyHandler(buyBtn, msgEl));
  }

  // Bind handler to mobile overlay button
  const overlayBuyBtn = overlayBody?.querySelector('#buy-tile-btn');
  const overlayMsgEl = overlayBody?.querySelector('#buy-tile-msg');
  if (overlayBuyBtn && overlayMsgEl) {
    overlayBuyBtn.addEventListener('click', () => buyHandler(overlayBuyBtn, overlayMsgEl));
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

// ── Export ───────────────────────────────────────────────────

export default {
  id: 'composer',
  title: 'Map Editor',
  init,
  enter,
  leave,
};
