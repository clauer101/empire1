/**
 * HexGrid — canvas-based hex grid renderer with pan & zoom.
 *
 * Renders a flat-top hex grid, handles mouse interaction,
 * and emits callbacks for tile events.
 */

import {
  hexToPixel, pixelToHex, hexCorners, hexKey, parseKey, hexNeighbors,
} from './hex.js';

/** Tile type definitions with visual styling. */
export const TILE_TYPES = {
  void:        { id: 'void',        label: 'Void',          color: '#161620', stroke: '#1a1a24', icon: null },
  empty:       { id: 'empty',       label: 'Empty',          color: '#1e1e2e', stroke: '#2a2a3a', icon: null },
  path:        { id: 'path',        label: 'Path',          color: '#5c4a32', stroke: '#7a6545', icon: null },
  spawnpoint:  { id: 'spawnpoint',  label: 'Spawnpoint',    color: '#5a2a2a', stroke: '#8a3a3a', icon: '★' },
  castle:      { id: 'castle',      label: 'Castle (Target)',   color: '#4a4a1a', stroke: '#7a7a30', icon: '🏰' },
};

/**
 * Register a new tile type dynamically (e.g., from server data).
 * @param {string} id  Tile type ID
 * @param {object} def  { label, color, stroke, icon }
 */
export function registerTileType(id, def) {
  TILE_TYPES[id] = { id, ...def };
}

export function getTileType(id) {
  return TILE_TYPES[id] || TILE_TYPES.empty;
}

/**
 * @typedef {Object} HexGridOptions
 * @property {HTMLCanvasElement} canvas
 * @property {number} [cols=8]       Grid columns
 * @property {number} [rows=8]       Grid rows  
 * @property {number} [hexSize=28]   Hex outer radius in px
 * @property {(q:number, r:number, tile:object) => void} [onTileClick]
 * @property {(q:number, r:number) => void} [onTileHover]
 * @property {(q:number, r:number, tileTypeId:string) => void} [onTileDrop]
 */

export class HexGrid {
  /**
   * @param {HexGridOptions} opts
   */
  constructor(opts) {
    this.canvas = opts.canvas;
    this.ctx = this.canvas.getContext('2d');
    this.cols = opts.cols || 8;
    this.rows = opts.rows || 8;
    this.hexSize = opts.hexSize || 28;

    // Callbacks
    this.onTileClick = opts.onTileClick || null;
    this.onTileHover = opts.onTileHover || null;
    this.onTileDrop = opts.onTileDrop || null;

    // Map data: key → { type: string, ...metadata }
    this.tiles = new Map();

    // View state
    this.offsetX = 0;
    this.offsetY = 0;
    this.zoom = 1.0;
    this.hoveredKey = null;
    this.selectedKey = null;

    // Battle state: centralized path + critter registry
    // battlePath: [{q,r}, ...] - shared path for all critters
    // battleCritters: cid → { iid, path_progress, health, max_health, slow_remaining_ms, burn_remaining_ms }
    // battleShots: shot_id → { source_sid, target_cid, shot_type, path_progress, origin_q, origin_r }
    this.battlePath = null;
    this.battleCritters = new Map();
    this.battleShots = new Map();
    this.battleActive = false;

    // Pan state
    this._isPanning = false;
    this._panStartX = 0;
    this._panStartY = 0;
    this._panOffsetX = 0;
    this._panOffsetY = 0;

    // Touch state (for pinch-to-zoom)
    this._touches = [];
    this._lastPinchDistance = 0;
    
    // Tap detection (for mobile tile clicks)
    this._tapStartX = 0;
    this._tapStartY = 0;
    this._tapStartTime = 0;
    this._hasMoved = false;

    // Zoom limits
    this._minZoom = 0.3;  // Will be updated based on map size
    this._maxZoom = 3.0;

    // Map bounds (in world coordinates)
    this._mapMinX = 0;
    this._mapMaxX = 0;
    this._mapMinY = 0;
    this._mapMaxY = 0;
    
    // Track user interaction to prevent auto-centering
    this._hasUserInteracted = false;

    // Animation
    this._rafId = null;
    this._dirty = true;
    
    // Base layer caching (tiles + structures + path)
    this._baseCanvas = null;
    this._baseCached = false;
    this._tilesVersion = 0;
    
    // Resize debouncing
    this._resizeTimeout = null;
    this._lastWidth = 0;
    this._lastHeight = 0;

    this._initGrid();
    this.addVoidNeighbors();
    this._bindEvents();
    this._resize();       // Set canvas size before first render
    this._centerGrid();
    this._startLoop();
  }

  // ── Grid init ──────────────────────────────────────────────

  _initGrid() {
    // Offset-coord → axial for a "rectangular" hex map.
    // Even-q offset for flat-top hexagons.
    for (let col = 0; col < this.cols; col++) {
      for (let row = 0; row < this.rows; row++) {
        const q = col;
        const r = row - Math.floor(col / 2);
        const key = hexKey(q, r);
        if (!this.tiles.has(key)) {
          this.tiles.set(key, { type: 'empty' });
        }
      }
    }
  }

  /** Return all valid tile keys. */
  get validKeys() {
    return new Set(this.tiles.keys());
  }

  /**
   * Add void tiles around all non-void tiles.
   * Void tiles are purely visual (client-side) and not persisted.
   */
  addVoidNeighbors() {
    const realKeys = new Set();
    for (const [key, data] of this.tiles) {
      if (data.type !== 'void') realKeys.add(key);
    }
    for (const key of realKeys) {
      const { q, r } = parseKey(key);
      for (const nb of hexNeighbors(q, r)) {
        const nbKey = hexKey(nb.q, nb.r);
        if (!this.tiles.has(nbKey)) {
          this.tiles.set(nbKey, { type: 'void' });
        }
      }
    }
    this._invalidateBase();
    this._dirty = true;
  }

  // ── Centering ──────────────────────────────────────────────

  _centerGrid() {
    // Compute bounding box of all tiles
    let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
    for (const key of this.tiles.keys()) {
      const { q, r } = parseKey(key);
      const { x, y } = hexToPixel(q, r, this.hexSize);
      minX = Math.min(minX, x);
      maxX = Math.max(maxX, x);
      minY = Math.min(minY, y);
      maxY = Math.max(maxY, y);
    }
    const gridW = maxX - minX + this.hexSize * 2;
    const gridH = maxY - minY + this.hexSize * 2;
    const cw = this._logicalWidth  || this.canvas.width;
    const ch = this._logicalHeight || this.canvas.height;
    this.offsetX = (cw / 2 - (minX + maxX) / 2);
    this.offsetY = (ch / 2 - (minY + maxY) / 2);
    
    // Store map bounds for pan clamping
    this._mapMinX = minX;
    this._mapMaxX = maxX;
    this._mapMinY = minY;
    this._mapMaxY = maxY;
    
    // Calculate minimum zoom to fit entire map
    this._updateMinZoom(gridW, gridH, cw, ch);
    
    this._dirty = true;
  }

  _updateMapBounds() {
    // Update map bounds and min zoom without changing offset
    let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
    for (const key of this.tiles.keys()) {
      const { q, r } = parseKey(key);
      const { x, y } = hexToPixel(q, r, this.hexSize);
      minX = Math.min(minX, x);
      maxX = Math.max(maxX, x);
      minY = Math.min(minY, y);
      maxY = Math.max(maxY, y);
    }
    const gridW = maxX - minX + this.hexSize * 2;
    const gridH = maxY - minY + this.hexSize * 2;
    const cw = this._logicalWidth  || this.canvas.width;
    const ch = this._logicalHeight || this.canvas.height;
    
    this._mapMinX = minX;
    this._mapMaxX = maxX;
    this._mapMinY = minY;
    this._mapMaxY = maxY;
    
    this._updateMinZoom(gridW, gridH, cw, ch);
    this._dirty = true;
  }

  _updateMinZoom(gridW, gridH, canvasW, canvasH) {
    // Calculate zoom needed to fit entire map with some padding
    const padding = 40; // pixels
    const zoomW = (canvasW - padding) / gridW;
    const zoomH = (canvasH - padding) / gridH;
    this._minZoom = Math.max(0.1, Math.min(zoomW, zoomH));
  }

  _clampPanOffset() {
    // Prevent map from being pushed completely out of viewport
    const cw = this._logicalWidth || this.canvas.width;
    const ch = this._logicalHeight || this.canvas.height;
    
    // Calculate map bounds in screen space (with current zoom)
    const mapScreenMinX = this._mapMinX * this.zoom;
    const mapScreenMaxX = this._mapMaxX * this.zoom;
    const mapScreenMinY = this._mapMinY * this.zoom;
    const mapScreenMaxY = this._mapMaxY * this.zoom;
    const mapScreenW = mapScreenMaxX - mapScreenMinX + this.hexSize * 2 * this.zoom;
    const mapScreenH = mapScreenMaxY - mapScreenMinY + this.hexSize * 2 * this.zoom;
    
    // Allow some overshoot (50% of visible area)
    const overshoot = 0.5;
    const overshootX = cw * overshoot;
    const overshootY = ch * overshoot;
    
    // Clamp offsetX: map must be at least partially visible
    // offsetX range: from showing only right edge to showing only left edge
    const minOffsetX = -mapScreenW + overshootX;
    const maxOffsetX = cw - overshootX;
    this.offsetX = Math.max(minOffsetX, Math.min(maxOffsetX, this.offsetX));
    
    // Clamp offsetY: map must be at least partially visible
    const minOffsetY = -mapScreenH + overshootY;
    const maxOffsetY = ch - overshootY;
    this.offsetY = Math.max(minOffsetY, Math.min(maxOffsetY, this.offsetY));
  }

  // ── Event binding ──────────────────────────────────────────

  _bindEvents() {
    // Mouse events
    this.canvas.addEventListener('mousemove', (e) => this._onMouseMove(e));
    this.canvas.addEventListener('mousedown', (e) => this._onMouseDown(e));
    this.canvas.addEventListener('mouseup', (e) => this._onMouseUp(e));
    this.canvas.addEventListener('mouseleave', () => this._onMouseLeave());
    this.canvas.addEventListener('wheel', (e) => this._onWheel(e), { passive: false });
    this.canvas.addEventListener('click', (e) => this._onClick(e));

    // Touch events for mobile
    this.canvas.addEventListener('touchstart', (e) => this._onTouchStart(e), { passive: false });
    this.canvas.addEventListener('touchmove', (e) => this._onTouchMove(e), { passive: false });
    this.canvas.addEventListener('touchend', (e) => this._onTouchEnd(e), { passive: false });
    this.canvas.addEventListener('touchcancel', (e) => this._onTouchEnd(e), { passive: false });

    // Drag-and-drop
    this.canvas.addEventListener('dragover', (e) => {
      e.preventDefault();
      e.dataTransfer.dropEffect = 'copy';
      const hex = this._eventToHex(e);
      if (hex) {
        this.hoveredKey = hexKey(hex.q, hex.r);
        this._dirty = true;
      }
    });
    this.canvas.addEventListener('drop', (e) => {
      e.preventDefault();
      const tileTypeId = e.dataTransfer.getData('text/tile-type');
      if (!tileTypeId) return;
      const hex = this._eventToHex(e);
      if (hex) {
        const key = hexKey(hex.q, hex.r);
        if (this.tiles.has(key)) {
          this.setTile(hex.q, hex.r, tileTypeId);
          if (this.onTileDrop) this.onTileDrop(hex.q, hex.r, tileTypeId);
        }
      }
    });

    // Resize
    this._resizeObserver = new ResizeObserver(() => {
      // Debounce resize to prevent excessive calls during animations
      if (this._resizeTimeout) clearTimeout(this._resizeTimeout);
      this._resizeTimeout = setTimeout(() => this._resize(), 100);
    });
    this._resizeObserver.observe(this.canvas.parentElement);
  }

  _resize() {
    const parent = this.canvas.parentElement;
    const dpr = window.devicePixelRatio || 1;
    const w = parent.clientWidth  || 300;
    const h = parent.clientHeight || 300;
    
    // Only resize if dimensions actually changed (threshold: 2px to avoid sub-pixel changes)
    if (Math.abs(w - this._lastWidth) < 2 && Math.abs(h - this._lastHeight) < 2) {
      return;
    }
    
    this._lastWidth = w;
    this._lastHeight = h;
    
    this.canvas.width = w * dpr;
    this.canvas.height = h * dpr;
    this.canvas.style.width = w + 'px';
    this.canvas.style.height = h + 'px';
    this.ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    this._logicalWidth = w;
    this._logicalHeight = h;
    
    // Only auto-center on first load, not after user has interacted
    if (!this._hasUserInteracted) {
      this._centerGrid();
    } else {
      // Update map bounds and min zoom without re-centering
      this._updateMapBounds();
    }
  }

  // ── Coordinate conversion ──────────────────────────────────

  _eventToHex(e) {
    const rect = this.canvas.getBoundingClientRect();
    const mx = e.clientX - rect.left;
    const my = e.clientY - rect.top;
    const wx = (mx - this.offsetX) / this.zoom;
    const wy = (my - this.offsetY) / this.zoom;
    const hex = pixelToHex(wx, wy, this.hexSize);
    const key = hexKey(hex.q, hex.r);
    if (this.tiles.has(key)) return hex;
    return null;
  }

  // ── Mouse handlers ─────────────────────────────────────────

  _onMouseMove(e) {
    if (this._isPanning) {
      this._hasUserInteracted = true;
      const dx = e.clientX - this._panStartX;
      const dy = e.clientY - this._panStartY;
      this.offsetX = this._panOffsetX + dx;
      this.offsetY = this._panOffsetY + dy;
      this._clampPanOffset();
      this._dirty = true;
      return;
    }
    const hex = this._eventToHex(e);
    const newKey = hex ? hexKey(hex.q, hex.r) : null;
    if (newKey !== this.hoveredKey) {
      this.hoveredKey = newKey;
      this._dirty = true;
      if (hex && this.onTileHover) this.onTileHover(hex.q, hex.r);
    }
  }

  _onMouseDown(e) {
    if (e.button === 1 || (e.button === 0 && e.shiftKey)) {
      // Middle-click or shift+click → pan
      this._isPanning = true;
      this._panStartX = e.clientX;
      this._panStartY = e.clientY;
      this._panOffsetX = this.offsetX;
      this._panOffsetY = this.offsetY;
      this.canvas.style.cursor = 'grabbing';
      e.preventDefault();
    }
  }

  _onMouseUp(e) {
    if (this._isPanning) {
      this._isPanning = false;
      this.canvas.style.cursor = '';
    }
  }

  _onMouseLeave() {
    this.hoveredKey = null;
    this._isPanning = false;
    this.canvas.style.cursor = '';
    this._dirty = true;
  }

  _onWheel(e) {
    e.preventDefault();
    this._hasUserInteracted = true;
    const rect = this.canvas.getBoundingClientRect();
    const mx = e.clientX - rect.left;
    const my = e.clientY - rect.top;

    const oldZoom = this.zoom;
    const factor = e.deltaY < 0 ? 1.08 : 0.92;
    this.zoom = Math.max(this._minZoom, Math.min(this._maxZoom, this.zoom * factor));

    // Zoom toward cursor
    this.offsetX = mx - (mx - this.offsetX) * (this.zoom / oldZoom);
    this.offsetY = my - (my - this.offsetY) * (this.zoom / oldZoom);
    this._clampPanOffset();
    this._dirty = true;
  }

  _onClick(e) {
    if (this._isPanning) return;
    const hex = this._eventToHex(e);
    if (!hex) {
      this.selectedKey = null;
      this._dirty = true;
      return;
    }
    const key = hexKey(hex.q, hex.r);
    this.selectedKey = key;
    this._dirty = true;
    if (this.onTileClick) {
      const tile = this.tiles.get(key);
      this.onTileClick(hex.q, hex.r, tile);
    }
  }

  // ── Touch handlers (mobile support) ────────────────────────

  _onTouchStart(e) {
    e.preventDefault();
    this._touches = Array.from(e.touches);

    if (this._touches.length === 1) {
      // Single touch → start panning (or tap)
      this._isPanning = true;
      this._panStartX = this._touches[0].clientX;
      this._panStartY = this._touches[0].clientY;
      this._panOffsetX = this.offsetX;
      this._panOffsetY = this.offsetY;
      
      // Track for tap detection
      this._tapStartX = this._touches[0].clientX;
      this._tapStartY = this._touches[0].clientY;
      this._tapStartTime = Date.now();
      this._hasMoved = false;
    } else if (this._touches.length === 2) {
      // Two fingers → pinch-to-zoom
      this._isPanning = false;
      this._lastPinchDistance = this._getPinchDistance(this._touches);
      this._hasMoved = true; // Pinch is not a tap
    }
  }

  _onTouchMove(e) {
    e.preventDefault();
    this._touches = Array.from(e.touches);

    if (this._touches.length === 1 && this._isPanning) {
      // Single touch pan
      const dx = this._touches[0].clientX - this._panStartX;
      const dy = this._touches[0].clientY - this._panStartY;
      
      // Check if touch has moved beyond tap threshold
      const tapThreshold = 10; // pixels
      if (Math.abs(dx) > tapThreshold || Math.abs(dy) > tapThreshold) {
        this._hasMoved = true;
        this._hasUserInteracted = true;
      }
      
      this.offsetX = this._panOffsetX + dx;
      this.offsetY = this._panOffsetY + dy;
      this._clampPanOffset();
      this._dirty = true;
    } else if (this._touches.length === 2) {
      // Pinch-to-zoom
      this._hasUserInteracted = true;
      const currentDistance = this._getPinchDistance(this._touches);
      if (this._lastPinchDistance > 0) {
        const rect = this.canvas.getBoundingClientRect();
        // Zoom center = midpoint between two fingers
        const mx = ((this._touches[0].clientX + this._touches[1].clientX) / 2) - rect.left;
        const my = ((this._touches[0].clientY + this._touches[1].clientY) / 2) - rect.top;

        const oldZoom = this.zoom;
        const factor = currentDistance / this._lastPinchDistance;
        this.zoom = Math.max(this._minZoom, Math.min(this._maxZoom, this.zoom * factor));

        // Zoom toward pinch center
        this.offsetX = mx - (mx - this.offsetX) * (this.zoom / oldZoom);
        this.offsetY = my - (my - this.offsetY) * (this.zoom / oldZoom);
        this._clampPanOffset();
        this._dirty = true;
      }
      this._lastPinchDistance = currentDistance;
    }
  }

  _onTouchEnd(e) {
    e.preventDefault();
    const endTouches = Array.from(e.touches);
    
    // Detect tap: single touch, no movement, short duration
    if (this._touches.length === 1 && endTouches.length === 0 && !this._hasMoved) {
      const tapDuration = Date.now() - this._tapStartTime;
      if (tapDuration < 300) { // 300ms max for tap
        // Simulate click event for tile selection
        const rect = this.canvas.getBoundingClientRect();
        const fakeEvent = {
          clientX: this._tapStartX,
          clientY: this._tapStartY
        };
        const hex = this._eventToHex(fakeEvent);
        if (hex) {
          const key = hexKey(hex.q, hex.r);
          this.selectedKey = key;
          this._dirty = true;
          if (this.onTileClick) {
            const tile = this.tiles.get(key);
            this.onTileClick(hex.q, hex.r, tile);
          }
        }
      }
    }
    
    this._touches = endTouches;

    if (this._touches.length === 0) {
      // All fingers lifted
      this._isPanning = false;
      this._lastPinchDistance = 0;
    } else if (this._touches.length === 1) {
      // One finger remaining → restart pan
      this._isPanning = true;
      this._panStartX = this._touches[0].clientX;
      this._panStartY = this._touches[0].clientY;
      this._panOffsetX = this.offsetX;
      this._panOffsetY = this.offsetY;
      this._lastPinchDistance = 0;
      this._hasMoved = false;
    }
  }

  _getPinchDistance(touches) {
    if (touches.length < 2) return 0;
    const dx = touches[0].clientX - touches[1].clientX;
    const dy = touches[0].clientY - touches[1].clientY;
    return Math.sqrt(dx * dx + dy * dy);
  }

  // ── Tile manipulation ──────────────────────────────────────

  setTile(q, r, typeId, meta = {}) {
    const key = hexKey(q, r);
    if (!this.tiles.has(key)) return;
    this.tiles.set(key, { type: typeId, ...meta });
    this._invalidateBase();
    this._dirty = true;
  }

  getTile(q, r) {
    return this.tiles.get(hexKey(q, r)) || null;
  }

  clearAll() {
    for (const [key] of this.tiles) {
      this.tiles.set(key, { type: 'empty' });
    }
    this.selectedKey = null;
    this._invalidateBase();
    this._dirty = true;
  }

  // ── Serialization ──────────────────────────────────────────

  /** Export map as JSON-serializable object. Excludes void tiles. */
  toJSON() {
    const tiles = {};
    for (const [key, data] of this.tiles) {
      if (data.type === 'void') continue;  // void tiles are client-side only
      tiles[key] = data.type || 'empty';
    }
    return {
      version: 1,
      cols: this.cols,
      rows: this.rows,
      hexSize: this.hexSize,
      tiles,
    };
  }

  /** Load map from JSON object. */
  fromJSON(data) {
    if (!data || !data.tiles) return;
    // Reset
    this.cols = data.cols || this.cols;
    this.rows = data.rows || this.rows;
    this.hexSize = data.hexSize || this.hexSize;
    this.tiles.clear();

    // Only create tiles that exist in the data — no 6x6 prefill
    for (const [key, tileData] of Object.entries(data.tiles)) {
      this.tiles.set(key, typeof tileData === 'string' ? { type: tileData } : tileData);
    }
    // Add void border tiles around real tiles
    this.addVoidNeighbors();
    this.selectedKey = null;
    this._centerGrid();
    this._dirty = true;
  }

  // ── Render loop ────────────────────────────────────────────

  _startLoop() {
    const loop = (timestamp) => {
      // During battle, always render for smooth animations
      // Otherwise only render when dirty flag is set
      if (this.battleCritters.size > 0) {
        this._render();
        this._dirty = false;
      } else if (this._dirty) {
        this._render();
        this._dirty = false;
      }
      this._rafId = requestAnimationFrame(loop);
    };
    loop(performance.now());
  }

  /** Get interpolated pixel position of a critter along battlePath. */
  _getCritterPixelPos(path_progress, sz) {
    if (!this.battlePath || this.battlePath.length < 2) return { x: 0, y: 0 };
    
    // path_progress is [0.0, 1.0] normalized over entire path
    const maxIdx = this.battlePath.length - 1;
    const floatIdx = path_progress * maxIdx;
    const idx = Math.min(Math.floor(floatIdx), maxIdx - 1);
    const frac = floatIdx - idx;
    
    const a = this.battlePath[idx];
    const b = this.battlePath[Math.min(idx + 1, maxIdx)];
    
    // Interpolate in hex space, then convert to pixel
    const q = a.q + (b.q - a.q) * frac;
    const r = a.r + (b.r - a.r) * frac;
    return hexToPixel(q, r, sz);
  }

  /** Store the battle path for all critters. */
  setBattlePath(path) {
    this.battlePath = path; // [{q,r}, ...]
    this.battleActive = true;
    this._invalidateBase();
    this._dirty = true;
  }

  /** Update or add a critter with server data. */
  updateBattleCritter(data) {
    // data: { cid, iid, path_progress, health, max_health, slow_remaining_ms, burn_remaining_ms }
    this.battleCritters.set(data.cid, {
      iid: data.iid,
      path_progress: data.path_progress,
      health: data.health,
      max_health: data.max_health,
      slow_remaining_ms: data.slow_remaining_ms || 0,
      burn_remaining_ms: data.burn_remaining_ms || 0,
    });
    this.battleActive = true;
    // No need to set dirty - continuous rendering during battle
  }

  /** Remove a critter (died or finished). */
  removeBattleCritter(cid) {
    this.battleCritters.delete(cid);
    this._dirty = true;
  }

  /** Update or add a shot with server data. */
  updateBattleShot(data) {
    // data: { source_sid, target_cid, shot_type, path_progress, origin_q, origin_r }
    const shot_id = `${data.source_sid}_${data.target_cid}`;
    
    // Remove shot if path_progress >= 1.0 (arrived)
    if (data.path_progress >= 1.0) {
      this.battleShots.delete(shot_id);
      return;
    }
    
    this.battleShots.set(shot_id, {
      source_sid: data.source_sid,
      target_cid: data.target_cid,
      shot_type: data.shot_type,
      path_progress: data.path_progress,
      origin_q: data.origin_q,
      origin_r: data.origin_r,
    });
    this.battleActive = true;
  }

  /** Clear all battle state. */
  clearBattle() {
    this.battlePath = null;
    this.battleCritters.clear();
    this.battleShots.clear();
    this.battleActive = false;
    this._invalidateBase();
    this._dirty = true;
  }

  /** Mark base layer (tiles + path) as dirty - needs re-render. */
  _invalidateBase() {
    this._baseCached = false;
  }

  /** Render base layer (tiles + battle path) to cache canvas with current zoom. */
  _renderBase() {
    // Create cache canvas if needed
    if (!this._baseCanvas) {
      this._baseCanvas = document.createElement('canvas');
    }

    // Calculate world bounds
    let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
    for (const key of this.tiles.keys()) {
      const { q, r } = parseKey(key);
      const { x, y } = hexToPixel(q, r, this.hexSize);
      minX = Math.min(minX, x - this.hexSize);
      maxX = Math.max(maxX, x + this.hexSize);
      minY = Math.min(minY, y - this.hexSize);
      maxY = Math.max(maxY, y + this.hexSize);
    }

    const worldW = maxX - minX;
    const worldH = maxY - minY;
    const dpr = window.devicePixelRatio || 1;

    // Size cache canvas to hold entire world at current zoom level
    this._baseCanvas.width = worldW * this.zoom * dpr;
    this._baseCanvas.height = worldH * this.zoom * dpr;
    this._baseWorldOffsetX = minX;
    this._baseWorldOffsetY = minY;
    this._baseCachedZoom = this.zoom;

    const ctx = this._baseCanvas.getContext('2d');

    // Clear
    ctx.save();
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, worldW * this.zoom, worldH * this.zoom);

    // Apply zoom, then translate so tiles start at (0,0)
    ctx.scale(this.zoom, this.zoom);
    ctx.translate(-minX, -minY);

    const sz = this.hexSize;

    // Draw tiles
    for (const [key, data] of this.tiles) {
      const { q, r } = parseKey(key);
      const tileType = getTileType(data.type);

      const { x, y } = hexToPixel(q, r, sz);
      const corners = hexCorners(x, y, sz);

      const isHovered = key === this.hoveredKey;
      const isSelected = key === this.selectedKey;

      // Fill
      ctx.beginPath();
      ctx.moveTo(corners[0].x, corners[0].y);
      for (let i = 1; i < 6; i++) ctx.lineTo(corners[i].x, corners[i].y);
      ctx.closePath();

      if (isSelected) {
        ctx.fillStyle = '#4fc3f7';
        ctx.globalAlpha = 0.35;
        ctx.fill();
        ctx.globalAlpha = 1;
        ctx.fillStyle = tileType.color;
        ctx.fill();
      } else if (isHovered) {
        ctx.fillStyle = tileType.color;
        ctx.fill();
        ctx.fillStyle = 'rgba(255,255,255,0.08)';
        ctx.fill();
      } else {
        ctx.fillStyle = tileType.color;
        ctx.fill();
      }

      // Stroke
      ctx.strokeStyle = isSelected ? '#4fc3f7' : isHovered ? '#6a6a8a' : tileType.stroke;
      ctx.lineWidth = isSelected ? 2 : 1;
      ctx.stroke();

      // Icon / label
      if (tileType.icon && sz * this.zoom > 12) {
        ctx.fillStyle = '#ccccdd';
        ctx.font = `${Math.max(10, sz * 0.45)}px sans-serif`;
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(tileType.icon, x, y);
      }

      // Coordinate labels (only when zoomed in enough)
      if (sz * this.zoom > 22) {
        ctx.fillStyle = 'rgba(255,255,255,0.2)';
        ctx.font = `${Math.max(7, sz * 0.25)}px monospace`;
        ctx.textAlign = 'center';
        ctx.textBaseline = 'bottom';
        ctx.fillText(`${q},${r}`, x, y + sz * 0.75);
      }
    }

    // Draw battle path
    if (this.battlePath && this.battlePath.length > 1) {
      ctx.strokeStyle = 'rgba(255, 255, 255, 0.3)';
      ctx.lineWidth = 2;
      ctx.beginPath();
      const start = hexToPixel(this.battlePath[0].q, this.battlePath[0].r, sz);
      ctx.moveTo(start.x, start.y);
      for (let i = 1; i < this.battlePath.length; i++) {
        const { x, y } = hexToPixel(this.battlePath[i].q, this.battlePath[i].r, sz);
        ctx.lineTo(x, y);
      }
      ctx.stroke();
    }

    ctx.restore();
    this._baseCached = true;
  }

  /** Render critters on top of current canvas state (assumes transform already applied). */
  _renderCritters() {
    const ctx = this.ctx;
    const sz = this.hexSize;

    // Draw battle critters (transform already applied by _render)
    for (const [cid, critter] of this.battleCritters) {
      const { x, y } = this._getCritterPixelPos(critter.path_progress, sz);

      // Color by critter type: soldier=blue, slave=red
      const color = critter.iid.includes('soldier') ? '#4488ff' : '#ff4444';
      const strokeColor = critter.iid.includes('soldier') ? '#2266dd' : '#dd2222';

      // Filled circle
      ctx.fillStyle = color;
      ctx.beginPath();
      ctx.arc(x, y, sz * 0.3, 0, Math.PI * 2);
      ctx.fill();
      ctx.strokeStyle = strokeColor;
      ctx.lineWidth = 2;
      ctx.stroke();
      
      // Draw health bar if critter has health data and is damaged
      if (critter.health != null && critter.max_health != null && critter.health < critter.max_health) {
        const barWidth = sz * 0.6;
        const barHeight = sz * 0.08;
        const barX = x - barWidth / 2;
        const barY = y - sz * 0.5; // Above the critter
        
        // Health percentage
        const healthPercent = Math.max(0, Math.min(1, critter.health / critter.max_health));
        
        // Background (lost health) - dark red
        ctx.fillStyle = '#331111';
        ctx.fillRect(barX, barY, barWidth, barHeight);
        
        // Foreground (remaining health) - green
        ctx.fillStyle = '#44ff44';
        ctx.fillRect(barX, barY, barWidth * healthPercent, barHeight);
        
        // Border
        ctx.strokeStyle = '#000000';
        ctx.lineWidth = 1;
        ctx.strokeRect(barX, barY, barWidth, barHeight);
      }
    }
  }

  /** Get interpolated pixel position of a shot between origin and target critter. */
  _getShotPixelPos(shot, sz) {
    // Get origin position (tower hex)
    const originPos = hexToPixel(shot.origin_q, shot.origin_r, sz);
    
    // Get target critter position
    const targetCritter = this.battleCritters.get(shot.target_cid);
    if (!targetCritter) {
      // Target critter not found (died?) - use origin
      return originPos;
    }
    
    const targetPos = this._getCritterPixelPos(targetCritter.path_progress, sz);
    
    // Interpolate between origin and target based on path_progress
    const x = originPos.x + (targetPos.x - originPos.x) * shot.path_progress;
    const y = originPos.y + (targetPos.y - originPos.y) * shot.path_progress;
    
    return { x, y };
  }

  _renderShots() {
    const ctx = this.ctx;
    const sz = this.hexSize;

    // Draw battle shots (transform already applied by _render)
    for (const [shot_id, shot] of this.battleShots) {
      const { x, y } = this._getShotPixelPos(shot, sz);
      
      // Shot appearance based on shot_type
      // shot_type: 0=NORMAL, 1=SLOW, 2=BURN, 3=SPLASH
      let color, glowColor;
      switch (shot.shot_type) {
        case 1: // SLOW/COLD
          color = '#6eb5ff';
          glowColor = 'rgba(110, 181, 255, 0.4)';
          break;
        case 2: // BURN/FIRE
          color = '#ff6b35';
          glowColor = 'rgba(255, 107, 53, 0.4)';
          break;
        case 3: // SPLASH
          color = '#9b59b6';
          glowColor = 'rgba(155, 89, 182, 0.4)';
          break;
        default: // NORMAL
          color = '#f1c40f';
          glowColor = 'rgba(241, 196, 15, 0.4)';
      }
      
      // Draw glow
      ctx.shadowBlur = sz * 0.4;
      ctx.shadowColor = glowColor;
      
      // Draw projectile
      ctx.fillStyle = color;
      ctx.beginPath();
      ctx.arc(x, y, sz * 0.15, 0, Math.PI * 2);
      ctx.fill();
      
      // Reset shadow
      ctx.shadowBlur = 0;
    }
  }

  _render() {
    const ctx = this.ctx;
    const w = this._logicalWidth || this.canvas.width;
    const h = this._logicalHeight || this.canvas.height;
    const dpr = window.devicePixelRatio || 1;

    // Clear entire canvas
    ctx.save();
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, w, h);

    // Render base layer to cache if needed, or if zoom changed
    if (!this._baseCached || this._baseCachedZoom !== this.zoom) {
      this._renderBase();
    }

    // Apply only translation (zoom is already in the base layer)
    ctx.translate(this.offsetX, this.offsetY);

    // Draw cached base layer (already zoomed)
    if (this._baseCanvas) {
      const scale = 1 / dpr;
      ctx.drawImage(
        this._baseCanvas,
        this._baseWorldOffsetX * this.zoom,
        this._baseWorldOffsetY * this.zoom,
        this._baseCanvas.width * scale,
        this._baseCanvas.height * scale
      );
    }

    // Apply zoom for critters and shots (they are not in the cache)
    ctx.scale(this.zoom, this.zoom);

    // Draw shots first (behind critters)
    if (this.battleShots.size > 0) {
      this._renderShots();
    }

    // Draw critters on top
    if (this.battleCritters.size > 0) {
      this._renderCritters();
    }

    ctx.restore();
  }

  // ── Cleanup ────────────────────────────────────────────────

  destroy() {
    if (this._rafId) cancelAnimationFrame(this._rafId);
    if (this._resizeObserver) this._resizeObserver.disconnect();
  }
}
