/**
 * HexGrid — canvas-based hex grid renderer with pan & zoom.
 *
 * Renders a flat-top hex grid, handles mouse interaction,
 * and emits callbacks for tile events.
 */

import {
  hexToPixel,
  pixelToHex,
  hexCorners,
  hexKey,
  parseKey,
  hexNeighbors,
  hexAStar,
} from './hex.js';
import { CritterSprite } from './critter_sprite.js';

/** Tile type definitions with visual styling. */
export const TILE_TYPES = {
  void: { id: 'void', label: 'Void', color: '#161620', stroke: '#1a1a24', icon: null },
  empty: { id: 'empty', label: 'Empty', color: '#1e1e2e', stroke: '#2a2a3a', icon: null },
  path: {
    id: 'path',
    label: 'Path',
    color: '#5c4a32',
    stroke: '#7a6545',
    icon: null,
    spriteUrl: '/assets/sprites/maps/path1.webp',
  },
  spawnpoint: {
    id: 'spawnpoint',
    label: 'Spawnpoint',
    color: '#5a2a2a',
    stroke: '#8a3a3a',
    icon: null,
    spriteUrl: '/assets/sprites/bases/spawnpoint.webp',
  },
  castle: {
    id: 'castle',
    label: 'Castle (Target)',
    color: '#4a4a1a',
    stroke: '#7a7a30',
    icon: null,
    spriteUrl: '/assets/sprites/bases/base.webp',
  },
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

    // Range overlay: { q, r, radius } or null
    this.rangeOverlay = null;

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
    this._enemyPaths = new Map(); // uid → [{q,r},...] server-provided enemy paths
    this._partialReachable = null;
    this.battleCritters = new Map();
    this.battleShots = new Map();
    this.battleActive = false;

    // Defender castle health bar
    this._defenderLife = null;
    this._defenderMaxLife = null;
    this._castlePos = null; // {q, r} of castle tile

    // Pan state
    this._isPanning = false;
    this._panStartX = 0;
    this._panStartY = 0;
    this._panOffsetX = 0;
    this._panOffsetY = 0;
    this._hasPanned = false;

    // Touch state (for pinch-to-zoom)
    this._touches = [];
    this._lastPinchDistance = 0;

    // Tap detection (for mobile tile clicks)
    this._tapStartX = 0;
    this._tapStartY = 0;
    this._tapStartTime = 0;
    this._hasMoved = false;

    // Deduplication: prevent double-fire from touch + synthetic click
    this._lastTileClickTime = 0;

    // Zoom limits
    this._minZoom = 0.3; // Will be updated based on map size
    this._maxZoom = 3.0;

    // Map background image
    /** @type {ImageBitmap|null} Decoded map PNG, shared across all tiles. */
    this._mapBitmap = null;
    /** Overall opacity of the map image (0–1). */
    this.mapAlpha = 1.0;
    /** Alpha of the tile-type color overlay on top of the map image (0–1). */
    this.tileOverlayAlpha = 0;
    /** Neighbor tiles outside own empire: Map<"q,r", {uid: number|null}> */
    this._neighborTiles = new Map();
    /** Vision radius for fog of war — tiles within this many steps of the own border are fog-free. */
    this.visionRadius = 1;
    /** Seamless repeating background pattern (built once from _mapBitmap). */
    this._tilePattern = null;
    /**
     * Called (debounced) after pan/zoom with the visible hex bounds, so the
     * view can lazily refetch viewport-bounded neighbor/fog tiles.
     * @type {((bounds:{q0:number,r0:number,q1:number,r1:number}) => void)|null}
     */
    this.onViewportChange = null;
    this._viewportDebounceId = null;

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

    // Static layer caching: grass texture, outlines, fog/neighbor tiles,
    // edges, tints and enemy/structure sprites are all baked into a single
    // offscreen canvas at the *current* zoom resolution. It is only rebuilt
    // when tiles / neighbor tiles / zoom / vision radius change — never on
    // pan and never per battle frame.
    this._staticCanvas = null;
    this._staticDirty = true;
    this._staticWorldOffsetX = 0;
    this._staticWorldOffsetY = 0;
    this._staticZoom = 0;
    this._staticCanvasScale = window.devicePixelRatio || 1;
    this._cachedSpriteTiles = null;
    this._pathCache = null;
    this._staticRebuildTimerId = null;

    // Sprite image cache: url → ImageBitmap | 'loading'
    this._spriteCache = new Map();

    // Critter sprite cache: iid (lowercase) → CritterSprite | 'loading'
    this._critterSprites = new Map();
    // Manifest promise — fetched once
    this._manifestPromise = null;

    // Resize debouncing
    this._resizeTimeout = null;
    this._lastWidth = 0;
    this._lastHeight = 0;

    this._initGrid();
    this.addVoidNeighbors();
    this._bindEvents();
    this._resize(); // Set canvas size before first render
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
    let minX = Infinity,
      maxX = -Infinity,
      minY = Infinity,
      maxY = -Infinity;
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
    const cw = this._logicalWidth || this.canvas.width;
    const ch = this._logicalHeight || this.canvas.height;

    // Store map bounds for pan clamping
    this._mapMinX = minX;
    this._mapMaxX = maxX;
    this._mapMinY = minY;
    this._mapMaxY = maxY;

    // Calculate minimum zoom to fit entire map
    this._updateMinZoom(gridW, gridH, cw, ch);

    // Set zoom to fit map nicely on screen (use calculated min zoom)
    this.zoom = Math.max(this._minZoom, Math.min(1.5, this._minZoom * 1.1));

    // Recalculate center with the new zoom
    // screen_x = offsetX + world_x * zoom  → center: offsetX = cw/2 - worldCenter * zoom
    this.offsetX = cw / 2 - ((minX + maxX) / 2) * this.zoom;
    this.offsetY = ch / 2 - ((minY + maxY) / 2) * this.zoom;

    this._dirty = true;
  }

  _updateMapBounds() {
    // Update map bounds and min zoom without changing offset
    let minX = Infinity,
      maxX = -Infinity,
      minY = Infinity,
      maxY = -Infinity;
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
    const cw = this._logicalWidth || this.canvas.width;
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
    // Prevent map from being pushed completely out of viewport.
    // Screen position of a world point wx: screen_x = offsetX + wx * zoom
    const cw = this._logicalWidth || this.canvas.width;
    const ch = this._logicalHeight || this.canvas.height;

    // One hex radius of extra padding so the edge tile is fully visible
    const pad = this.hexSize * this.zoom;

    // Allow some overshoot (50% of visible area) so the map stays grabbable
    const overshootX = cw * 0.5;
    const overshootY = ch * 0.5;

    // Clamp offsetX:
    //   right edge of map must remain >= -overshootX  (don't scroll map fully off left)
    //     offsetX + (_mapMaxX + hexSize) * zoom >= -overshootX
    //     → minOffsetX = -overshootX - (_mapMaxX + hexSize) * zoom
    //   left edge of map must remain <= cw + overshootX  (don't scroll map fully off right)
    //     offsetX + (_mapMinX - hexSize) * zoom <= cw + overshootX
    //     → maxOffsetX = cw + overshootX - (_mapMinX - hexSize) * zoom
    const minOffsetX = -overshootX - (this._mapMaxX + this.hexSize) * this.zoom;
    const maxOffsetX = cw + overshootX - (this._mapMinX - this.hexSize) * this.zoom;
    this.offsetX = Math.max(minOffsetX, Math.min(maxOffsetX, this.offsetX));

    // Clamp offsetY (same logic for Y axis)
    const minOffsetY = -overshootY - (this._mapMaxY + this.hexSize) * this.zoom;
    const maxOffsetY = ch + overshootY - (this._mapMinY - this.hexSize) * this.zoom;
    this.offsetY = Math.max(minOffsetY, Math.min(maxOffsetY, this.offsetY));
  }

  // ── Event binding ──────────────────────────────────────────

  _bindEvents() {
    // Store bound handlers so destroy() can remove them
    this._handlers = {
      mousemove: (e) => this._onMouseMove(e),
      mousedown: (e) => this._onMouseDown(e),
      mouseup: (e) => this._onMouseUp(e),
      mouseleave: () => this._onMouseLeave(),
      wheel: (e) => this._onWheel(e),
      click: (e) => this._onClick(e),
      touchstart: (e) => this._onTouchStart(e),
      touchmove: (e) => this._onTouchMove(e),
      touchend: (e) => this._onTouchEnd(e),
      touchcancel: (e) => this._onTouchEnd(e),
      dragover: (e) => {
        e.preventDefault();
        e.dataTransfer.dropEffect = 'copy';
        const hex = this._eventToHex(e);
        if (hex) {
          this.hoveredKey = hexKey(hex.q, hex.r);
          this._dirty = true;
        }
      },
      drop: (e) => {
        e.preventDefault();
        const tileTypeId = e.dataTransfer.getData('text/tile-type');
        if (!tileTypeId) return;
        const hex = this._eventToHex(e);
        if (hex) {
          const key = hexKey(hex.q, hex.r);
          if (this.tiles.has(key)) {
            if (this.onTileDrop) this.onTileDrop(hex.q, hex.r, tileTypeId);
          }
        }
      },
    };

    // Mouse events
    this.canvas.addEventListener('mousemove', this._handlers.mousemove);
    this.canvas.addEventListener('mousedown', this._handlers.mousedown);
    this.canvas.addEventListener('mouseup', this._handlers.mouseup);
    this.canvas.addEventListener('mouseleave', this._handlers.mouseleave);
    this.canvas.addEventListener('wheel', this._handlers.wheel, { passive: false });
    this.canvas.addEventListener('click', this._handlers.click);

    // Touch events for mobile
    this.canvas.addEventListener('touchstart', this._handlers.touchstart, { passive: false });
    this.canvas.addEventListener('touchmove', this._handlers.touchmove, { passive: false });
    this.canvas.addEventListener('touchend', this._handlers.touchend, { passive: false });
    this.canvas.addEventListener('touchcancel', this._handlers.touchcancel, { passive: false });

    // Drag-and-drop
    this.canvas.addEventListener('dragover', this._handlers.dragover);
    this.canvas.addEventListener('drop', this._handlers.drop);

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
    const w = parent.clientWidth || 300;
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
    if (this.tiles.has(key) || this._neighborTiles.has(key)) return hex;
    return null;
  }

  /**
   * Visible hex bounds for the current pan/zoom, padded by `margin` tiles.
   * Converts the four screen corners to world space then to axial coords.
   * @returns {{q0:number,r0:number,q1:number,r1:number}}
   */
  getVisibleHexBounds(margin = 2) {
    const w = this._logicalWidth || this.canvas.width;
    const h = this._logicalHeight || this.canvas.height;
    let q0 = Infinity, r0 = Infinity, q1 = -Infinity, r1 = -Infinity;
    for (const [sx, sy] of [[0, 0], [w, 0], [0, h], [w, h]]) {
      const { q, r } = pixelToHex(
        (sx - this.offsetX) / this.zoom,
        (sy - this.offsetY) / this.zoom,
        this.hexSize
      );
      q0 = Math.min(q0, q); q1 = Math.max(q1, q);
      r0 = Math.min(r0, r); r1 = Math.max(r1, r);
    }
    return {
      q0: Math.floor(q0) - margin,
      r0: Math.floor(r0) - margin,
      q1: Math.ceil(q1) + margin,
      r1: Math.ceil(r1) + margin,
    };
  }

  /** Notify `onViewportChange` after pan/zoom settles (debounced ~250ms). */
  _emitViewportChange() {
    if (!this.onViewportChange) return;
    if (this._viewportDebounceId) clearTimeout(this._viewportDebounceId);
    this._viewportDebounceId = setTimeout(() => {
      this._viewportDebounceId = null;
      try {
        this.onViewportChange(this.getVisibleHexBounds());
      } catch { /* view may have been torn down */ }
    }, 250);
  }

  // ── Mouse handlers ─────────────────────────────────────────

  _onMouseMove(e) {
    if (this._isPanning) {
      this._hasUserInteracted = true;
      const dx = e.clientX - this._panStartX;
      const dy = e.clientY - this._panStartY;

      // Check if we've actually moved (not just a static click)
      const panThreshold = 3; // pixels
      if (Math.abs(dx) > panThreshold || Math.abs(dy) > panThreshold) {
        this._hasPanned = true;
      }

      this.offsetX = this._panOffsetX + dx;
      this.offsetY = this._panOffsetY + dy;
      this._clampPanOffset();
      this._dirty = true;
      this._emitViewportChange();
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
    if (e.button === 0 || e.button === 1) {
      // Left-click or middle-click → pan
      this._isPanning = true;
      this._hasPanned = false;
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
    this._scheduleStaticRebuildAfterZoom();
    this._emitViewportChange();
  }

  _fireTileClick(q, r, tile) {
    const now = Date.now();
    if (now - this._lastTileClickTime < 400) return;
    this._lastTileClickTime = now;
    if (this.onTileClick) this.onTileClick(q, r, tile);
  }

  _onClick(e) {
    // Don't trigger click if we just finished panning
    if (this._isPanning || this._hasPanned) {
      this._hasPanned = false;
      return;
    }
    const hex = this._eventToHex(e);
    if (!hex) {
      this.selectedKey = null;
      this._dirty = true;
      return;
    }
    const key = hexKey(hex.q, hex.r);
    this.selectedKey = key;
    this._dirty = true;
    // Enemy neighbor tiles take priority over synthetic void entries from addVoidNeighbors().
    // Unclaimed neighbor tiles (uid == null) fall through to the normal void handler (buy option).
    const neighborData = this._neighborTiles.get(key);
    const tileData = (neighborData?.uid != null)
      ? { type: 'neighbor', ...neighborData }
      : this.tiles.get(key);
    this._fireTileClick(hex.q, hex.r, tileData);
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
      const tapThreshold = 15; // pixels
      if (Math.abs(dx) > tapThreshold || Math.abs(dy) > tapThreshold) {
        this._hasMoved = true;
        this._hasUserInteracted = true;
      }

      this.offsetX = this._panOffsetX + dx;
      this.offsetY = this._panOffsetY + dy;
      this._clampPanOffset();
      this._dirty = true;
      this._emitViewportChange();
    } else if (this._touches.length === 2) {
      // Pinch-to-zoom
      this._hasUserInteracted = true;
      const currentDistance = this._getPinchDistance(this._touches);
      if (this._lastPinchDistance > 0) {
        const rect = this.canvas.getBoundingClientRect();
        // Zoom center = midpoint between two fingers
        const mx = (this._touches[0].clientX + this._touches[1].clientX) / 2 - rect.left;
        const my = (this._touches[0].clientY + this._touches[1].clientY) / 2 - rect.top;

        const oldZoom = this.zoom;
        const factor = currentDistance / this._lastPinchDistance;
        this.zoom = Math.max(this._minZoom, Math.min(this._maxZoom, this.zoom * factor));

        // Zoom toward pinch center
        this.offsetX = mx - (mx - this.offsetX) * (this.zoom / oldZoom);
        this.offsetY = my - (my - this.offsetY) * (this.zoom / oldZoom);
        this._clampPanOffset();
        this._dirty = true;
        this._scheduleStaticRebuildAfterZoom();
        this._emitViewportChange();
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
      if (tapDuration < 300) {
        // 300ms max for tap
        // Simulate click event for tile selection
        const rect = this.canvas.getBoundingClientRect();
        const fakeEvent = {
          clientX: this._tapStartX,
          clientY: this._tapStartY,
        };
        const hex = this._eventToHex(fakeEvent);
        if (hex) {
          const key = hexKey(hex.q, hex.r);
          this.selectedKey = key;
          this._dirty = true;
          const neighborData = this._neighborTiles.get(key);
          const tileData = (neighborData?.uid != null)
            ? { type: 'neighbor', ...neighborData }
            : this.tiles.get(key);
          this._fireTileClick(hex.q, hex.r, tileData);
          // Block any subsequent synthetic click from the browser
          this._hasPanned = true;
          setTimeout(() => {
            this._hasPanned = false;
          }, 500);
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
    const prevType = (this.tiles.get(key) || {}).type;
    this.tiles.set(key, { type: typeId, ...meta });
    if (typeId === 'castle') this._castlePos = { q, r };
    // Path is always computed server-side; no client-side recompute needed.
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
      if (data.type === 'void') continue; // void tiles are client-side only
      if (data.select && data.select !== 'first') {
        tiles[key] = { type: data.type || 'empty', select: data.select };
      } else {
        tiles[key] = data.type || 'empty';
      }
    }
    return {
      version: 1,
      cols: this.cols,
      rows: this.rows,
      hexSize: this.hexSize,
      tiles,
    };
  }

  /**
   * Replace the viewport-bounded set of non-owned (fog/enemy) tiles.
   * Rendered per-frame in `_render()`, so it never invalidates the base
   * cache nor enlarges the base canvas.
   */
  setNeighborTiles(neighborTiles) {
    this._neighborTiles = new Map(
      neighborTiles.map(t => [`${t.q},${t.r}`, { uid: t.uid ?? null, iid: t.iid ?? null, tile_type: t.tile_type ?? null }])
    );
    this._invalidateStatic();
    this._dirty = true;
  }

  fromJSON(data) {
    if (!data || !data.tiles) return;
    // Reset
    this.cols = data.cols || this.cols;
    this.rows = data.rows || this.rows;
    this.hexSize = data.hexSize || this.hexSize;
    this.tiles.clear();

    // Only create tiles that exist in the data — no 6x6 prefill
    this._castlePos = null;
    for (const [key, tileData] of Object.entries(data.tiles)) {
      const td = typeof tileData === 'string' ? { type: tileData } : tileData;
      this.tiles.set(key, td);
      if (td.type === 'castle') {
        const [q, r] = key.split(',').map(Number);
        this._castlePos = { q, r };
      }
    }
    // Add void border tiles around real tiles
    this.addVoidNeighbors();
    this.selectedKey = null;
    if (!this._hasUserInteracted) {
      this._centerGrid();
    } else {
      this._updateMapBounds();
    }
    this._dirty = true;
  }

  // ── Render loop ────────────────────────────────────────────

  _startLoop() {
    const loop = (timestamp) => {
      // During battle, always render for smooth animations
      // Otherwise only render when dirty flag is set
      try {
        if (this.battleCritters.size > 0) {
          this._render();
          this._dirty = false;
        } else if (this._dirty) {
          this._render();
          this._dirty = false;
        }
      } catch (err) {
        // Never let a render error kill the loop (e.g. drawImage with 0-sized canvas
        // throws DOMException on Chrome/Windows — without this catch the loop dies
        // permanently and the canvas stays black forever).
        console.warn('[HexGrid] render error (non-fatal):', err);
        this._dirty = true; // force re-attempt next frame
      }
      this._rafId = requestAnimationFrame(loop);
    };
    loop(performance.now());
  }

  // ── Critter sprite management ──────────────────────────────

  /** Fetch /api/critters manifest once, return Map<name, entry>. */
  _loadManifest() {
    if (this._manifestPromise) return this._manifestPromise;
    this._manifestPromise = fetch('/api/critters')
      .then((r) => r.json())
      .then((data) => {
        const map = new Map();
        for (const entry of data.critters || []) map.set(entry.name, entry);
        return map;
      })
      .catch((e) => {
        console.warn('[HexGrid] critter manifest load failed:', e);
        return new Map();
      });
    return this._manifestPromise;
  }

  /**
   * Load and cache a CritterSprite for the given IID.
   * IID is matched case-insensitively against manifest names.
   */
  _ensureCritterSprite(iid) {
    const key = iid.toLowerCase();
    if (this._critterSprites.has(key)) return;
    this._critterSprites.set(key, 'loading');
    this._loadManifest().then((manifest) => {
      const entry = manifest.get(key);
      if (!entry) {
        this._critterSprites.delete(key);
        return;
      }
      const sprite = CritterSprite.fromManifest(entry);
      sprite
        .load()
        .then(() => {
          this._critterSprites.set(key, sprite);
        })
        .catch((e) => {
          console.warn('[HexGrid] critter sprite load failed:', key, e);
          this._critterSprites.delete(key);
        });
    });
  }

  /**
   * Determine movement direction at path_progress by sampling two nearby points.
   * Returns 'forward' | 'backward' | 'left' | 'right'.
   */
  _getCritterDirection(path_progress) {
    if (!this.battlePath || this.battlePath.length < 2) return 'forward';
    const sz = this.hexSize;
    const delta = 1 / ((this.battlePath.length - 1) * 4); // ~quarter-segment step
    const p1 = this._getCritterPixelPos(path_progress, sz);
    const p2 = this._getCritterPixelPos(Math.min(path_progress + delta, 1.0), sz);
    const dx = p2.x - p1.x;
    const dy = p2.y - p1.y;
    if (Math.abs(dx) < 0.001 && Math.abs(dy) < 0.001) return 'forward';
    if (Math.abs(dy) >= Math.abs(dx)) return dy > 0 ? 'forward' : 'backward';
    return dx > 0 ? 'right' : 'left';
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

  /**
  /**
   * Set the display path received from the server.
   * Works in both editor mode and battle mode (for critter movement).
   * Does NOT change battleActive.
   */
  setDisplayPath(path) {
    // During an active battle with critters moving, the path is owned by the
    // server via setBattlePath() — don't overwrite it.  But if no critters are
    // present yet (e.g. the view just re-entered and loadMap() resolved after a
    // BATTLE_STATUS message already set battleActive), we still need to draw the
    // path so it is visible before the first wave starts.
    if (this.battleActive && this.battleCritters.size > 0) {
      console.log('[HexGrid] setDisplayPath blocked (battle active with critters)');
      return;
    }
    console.log('[HexGrid] setDisplayPath', path ? `${path.length} nodes` : 'null');
    this.battlePath = path; // [{q,r}, ...] or null
    this._partialReachable = null;
    if (path) this._ensureSpriteLoaded('/assets/sprites/maps/path1.webp');
    this._invalidateBase();
    this._dirty = true;
  }

  /** Store server-provided path for a specific enemy uid. */
  setEnemyPath(uid, path) {
    if (path && path.length > 1) {
      this._enemyPaths.set(uid, path);
      this._ensureSpriteLoaded('/assets/sprites/maps/path1.webp');
    } else {
      this._enemyPaths.delete(uid);
    }
    this._invalidateStatic();
    this._dirty = true;
  }

  /** Store the battle path for all critters (also activates battle mode). */
  setBattlePath(path) {
    console.log('[HexGrid] setBattlePath', path ? `${path.length} nodes` : 'null');
    this.battlePath = path; // [{q,r}, ...]
    this.battleActive = true;
    this._ensureSpriteLoaded('/assets/sprites/maps/path1.webp');
    this._invalidateBase();
    this._dirty = true;
  }

  /** Update or add a critter with server data. */
  updateBattleCritter(data) {
    // data: { cid, iid, path_progress, health, max_health, slow_remaining_ms, burn_remaining_ms, scale }
    this.battleCritters.set(data.cid, {
      iid: data.iid,
      path_progress: data.path_progress,
      health: data.health,
      max_health: data.max_health,
      slow_remaining_ms: data.slow_remaining_ms || 0,
      burn_remaining_ms: data.burn_remaining_ms || 0,
      scale: data.scale ?? 1.0,
    });
    this.battleActive = true;
    // No need to set dirty - continuous rendering during battle
  }

  /** Remove a critter (died or finished). */
  removeBattleCritter(cid) {
    this.battleCritters.delete(cid);
    this._dirty = true;
  }

  /** Update the defender's castle life for the health bar. */
  setDefenderLives(life, maxLife) {
    this._defenderLife = life;
    this._defenderMaxLife = maxLife;
    this._dirty = true;
  }

  /** Draw a health bar above the castle tile for defender life. */
  _renderCastleHealthBar() {
    if (!this._castlePos || this._defenderLife == null || !this._defenderMaxLife) return;
    const ctx = this.ctx;
    const sz = this.hexSize;
    const { x, y } = hexToPixel(this._castlePos.q, this._castlePos.r, sz);

    const barWidth = sz * 0.95;
    const barHeight = sz * 0.1;
    const barX = x - barWidth / 2;
    const barY = y - sz * 0.75;
    const lifePercent = Math.max(0, Math.min(1, this._defenderLife / this._defenderMaxLife));

    // Background
    ctx.fillStyle = '#3b0000';
    ctx.fillRect(barX, barY, barWidth, barHeight);
    // Fill — color shifts red→green based on life
    const hue = Math.round(lifePercent * 120);
    ctx.fillStyle = `hsl(${hue}, 90%, 45%)`;
    ctx.fillRect(barX, barY, barWidth * lifePercent, barHeight);
    // Border
    ctx.strokeStyle = '#000';
    ctx.lineWidth = 1;
    ctx.strokeRect(barX, barY, barWidth, barHeight);
    // Label: "N / M"
    ctx.fillStyle = '#ffffff';
    ctx.font = `bold ${Math.max(8, sz * 0.2)}px sans-serif`;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'bottom';
    ctx.fillText(
      `${Math.floor(this._defenderLife)} / ${Math.round(this._defenderMaxLife)}`,
      x,
      barY - 1
    );
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

    const shotSpriteUrl = data.shot_sprite ? '/' + data.shot_sprite : null;
    if (shotSpriteUrl) this._ensureSpriteLoaded(shotSpriteUrl, false);

    this.battleShots.set(shot_id, {
      source_sid: data.source_sid,
      target_cid: data.target_cid,
      shot_type: data.shot_type,
      shot_sprite: shotSpriteUrl,
      shot_sprite_scale: data.shot_sprite_scale ?? 1.0,
      path_progress: data.path_progress,
      origin_q: data.origin_q,
      origin_r: data.origin_r,
      projectile_y_offset: data.projectile_y_offset ?? 0.0,
    });
    this.battleActive = true;
  }

  /** Clear all battle state. */
  clearBattle() {
    this.battleCritters.clear();
    this.battleShots.clear();
    this.battleActive = false;
    // Path stays visible after battle ends (last setDisplayPath value is retained)
    this._dirty = true;
  }

  /** Mark base layer (tiles + path) as dirty - needs re-render. */
  /**
   * Load a sprite URL into _spriteCache.
   * @param {string} url
   * @param {boolean} [invalidateBase=true]  Set false for dynamic sprites (shots, critters)
   *   that are not part of the base layer — they only need _dirty, not a full base re-render.
   */
  _ensureSpriteLoaded(url, invalidateBase = true) {
    if (this._spriteCache.has(url)) return;
    this._spriteCache.set(url, 'loading');
    fetch(url)
      .then((r) => r.blob())
      .then((blob) => createImageBitmap(blob))
      .then((bmp) => {
        this._spriteCache.set(url, bmp);
        if (invalidateBase) this._invalidateBase();
        this._dirty = true;
      })
      .catch((e) => {
        console.warn('[HexGrid] sprite load failed:', url, e.message);
        this._spriteCache.delete(url);
      });
  }

  _invalidateBase() {
    this._baseCached = false;
    this._invalidateStatic();
  }

  /** Mark the cached static layer (grass, outlines, fog, edges, sprites) stale. */
  _invalidateStatic() {
    this._staticDirty = true;
    this._cachedSpriteTiles = null;
    this._pathCache = null;
  }

  /**
   * Schedule a deferred static rebuild after zoom gestures settle.
   * During the zoom gesture _render() reuses the old cache at a rescaled
   * size — correct geometry but slightly blurry / wrong line widths.
   * The rebuild fires once, ~200 ms after the last zoom event.
   */
  _scheduleStaticRebuildAfterZoom() {
    if (this._staticRebuildTimerId !== null) {
      clearTimeout(this._staticRebuildTimerId);
    }
    this._staticRebuildTimerId = setTimeout(() => {
      this._staticRebuildTimerId = null;
      this._invalidateStatic();
      this._dirty = true;
    }, 150);
  }

  /**
   * Load a seamless texture and use it as a repeating background pattern for
   * all hex tiles (own + fog + enemy). The texture must tile cleanly; cost is
   * independent of map size since it is a single repeating pattern fill.
   *
   * @param {string|null} url  Root-relative URL to a seamless WebP/PNG, or null to clear.
   * @returns {Promise<void>}
   */
  async setMapBackground(url) {
    if (this._mapBitmap) {
      this._mapBitmap.close();
      this._mapBitmap = null;
    }
    this._tilePattern = null;
    if (!url) {
      this._invalidateBase();
      this._dirty = true;
      return;
    }
    const blob = await fetch(url).then((r) => {
      if (!r.ok) throw new Error(`HTTP ${r.status} loading map: ${url}`);
      return r.blob();
    });
    this._mapBitmap = await createImageBitmap(blob);
    this._tilePattern = this.ctx.createPattern(this._mapBitmap, 'repeat');
    this._tilePattern.setTransform(new DOMMatrix().scale(0.2));
    this._invalidateBase();
    this._dirty = true;
  }

  /** Render base layer (tiles + battle path) to cache canvas with current zoom. */
  _renderBase() {
    // Nothing to render yet — leave the cached flag false so we retry next frame.
    if (this.tiles.size === 0) return;

    // Create cache canvas if needed
    if (!this._baseCanvas) {
      this._baseCanvas = document.createElement('canvas');
    }

    // Calculate world bounds from OWNED tiles only. Neighbor/fog tiles are
    // viewport-bounded and drawn per-frame in _render(), so they no longer
    // grow this cached canvas (which would explode at large fog radius).
    let minX = Infinity,
      maxX = -Infinity,
      minY = Infinity,
      maxY = -Infinity;
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

    // Size cache canvas at zoom=1 (scaling applied at draw time, not here).
    // This means _renderBase() only re-runs when tiles change, not on every zoom step.
    this._baseCanvas.width = worldW * dpr;
    this._baseCanvas.height = worldH * dpr;
    this._baseWorldOffsetX = minX;
    this._baseWorldOffsetY = minY;

    const ctx = this._baseCanvas.getContext('2d');

    // Clear — reset filter explicitly to avoid bleed from previous render
    ctx.save();
    ctx.filter = 'none';
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.imageSmoothingEnabled = false;
    ctx.clearRect(0, 0, worldW, worldH);

    // Translate so tiles start at (0,0) — zoom applied at draw time in _render()
    ctx.translate(-minX, -minY);

    // Neighbor fog / enemy tiles are no longer baked into the base canvas —
    // they are viewport-bounded and drawn per-frame by _renderNeighborTiles().

    // ── Pass 2: Battle path (behind structures) ───────────────
    ctx.restore();
    this._baseCached = true;
  }

  /**
   * Render path to an offscreen canvas once, composite per-frame with drawImage.
   * Each segment between consecutive tile centers is stamped with the path texture,
   * rotated to the correct angle. Rounded caps drawn per-node blend the joints.
   */
  _buildPathCache(allSegments, pathBmp, pathW) {
    let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
    for (const { points } of allSegments) {
      for (const p of points) {
        minX = Math.min(minX, p.x - pathW);
        minY = Math.min(minY, p.y - pathW);
        maxX = Math.max(maxX, p.x + pathW);
        maxY = Math.max(maxY, p.y + pathW);
      }
    }
    if (!isFinite(minX)) return null;
    const dpr = window.devicePixelRatio || 1;
    const MAX_TEXTURE = 4096;
    const wantScale = dpr * this._maxZoom;
    const pad = pathW;
    const worldW = maxX - minX + pad * 2;
    const worldH = maxY - minY + pad * 2;
    const renderScale = Math.min(wantScale, MAX_TEXTURE / Math.max(worldW, worldH, 1));
    const offW = Math.ceil(worldW * renderScale);
    const offH = Math.ceil(worldH * renderScale);
    const off = document.createElement('canvas');
    off.width = offW;
    off.height = offH;
    const octx = off.getContext('2d');
    // Work in world-space coords; renderScale applied via setTransform
    octx.setTransform(renderScale, 0, 0, renderScale, (-minX + pad) * renderScale, (-minY + pad) * renderScale);

    for (const { points, alpha } of allSegments) {
      if (points.length < 2) continue;
      octx.save();
      octx.globalAlpha = alpha;

      // --- stamp one image per segment, clipped to a rounded rectangle ---
      for (let i = 0; i < points.length - 1; i++) {
        const ax = points[i].x, ay = points[i].y;
        const bx = points[i + 1].x, by = points[i + 1].y;
        const dx = bx - ax, dy = by - ay;
        const len = Math.sqrt(dx * dx + dy * dy);
        if (len < 1) continue;
        // sprite is 1:8 (tall), long axis maps to segment direction
        const angle = Math.atan2(dy, dx) - Math.PI / 2;
        octx.save();
        octx.translate(ax + dx * 0.5, ay + dy * 0.5);
        octx.rotate(angle);
        const stampW = pathW;
        const ext = stampW * 0.1; // overshoot each end to close the gap at caps
        const stampH = len + ext * 2;
        const cornerR = stampW * 0.4; // fully round short ends
        // clip to rounded rect so the ends are semicircular, not sharp
        octx.beginPath();
        octx.roundRect(-stampW / 2, -stampH / 2, stampW, stampH, cornerR);
        octx.clip();
        if (pathBmp) {
          octx.drawImage(pathBmp, -stampW / 2, -stampH / 2, stampW, stampH);
        } else {
          octx.fillStyle = '#c8924a';
          octx.fill();
        }
        // fade left and right edges
        const fadeW = stampW * 0.35;
        octx.globalCompositeOperation = 'destination-out';
        const gL = octx.createLinearGradient(-stampW / 2, 0, -stampW / 2 + fadeW, 0);
        gL.addColorStop(0, 'rgba(0,0,0,1)');
        gL.addColorStop(1, 'rgba(0,0,0,0)');
        octx.fillStyle = gL;
        octx.fillRect(-stampW / 2, -stampH / 2, fadeW, stampH);
        const gR = octx.createLinearGradient(stampW / 2, 0, stampW / 2 - fadeW, 0);
        gR.addColorStop(0, 'rgba(0,0,0,1)');
        gR.addColorStop(1, 'rgba(0,0,0,0)');
        octx.fillStyle = gR;
        octx.fillRect(stampW / 2 - fadeW, -stampH / 2, fadeW, stampH);
        octx.globalCompositeOperation = 'source-over';
        octx.restore();
      }

      octx.restore();
    }
    return { canvas: off, x: minX - pad, y: minY - pad, scale: renderScale };
  }

  _renderPath(ctx) {
    const sz = this.hexSize;
    const pathBmp = this._spriteCache.get('/assets/sprites/maps/path1.webp');
    const pathW = sz * 0.38;

    // Collect all segment groups to render
    const allSegments = [];

    if (!this.battlePath && this._partialReachable && this._partialReachable.size > 1) {
      const visitedEdges = new Set();
      const points = [];
      for (const key of this._partialReachable) {
        const { q, r } = parseKey(key);
        const p1 = hexToPixel(q, r, sz);
        for (const nb of hexNeighbors(q, r)) {
          const nKey = hexKey(nb.q, nb.r);
          if (!this._partialReachable.has(nKey)) continue;
          const edgeKey = key < nKey ? key + '|' + nKey : nKey + '|' + key;
          if (visitedEdges.has(edgeKey)) continue;
          visitedEdges.add(edgeKey);
          points.push(p1, hexToPixel(nb.q, nb.r, sz));
        }
      }
      if (points.length > 1) allSegments.push({ points, alpha: 0.75 });
    }

    // Own path
    if (this.battlePath && this.battlePath.length > 1) {
      allSegments.push({ points: this.battlePath.map((p) => hexToPixel(p.q, p.r, sz)), alpha: 1 });
    } else {
      // Fallback from own tiles when no battlePath set
      const pathTiles = new Set();
      let castleKey = null;
      for (const [key, data] of this.tiles) {
        if (data.type === 'path') pathTiles.add(key);
        if (data.type === 'castle') castleKey = key;
      }
      if (castleKey && pathTiles.size > 0) {
        const chain = [parseKey(castleKey)];
        const visited = new Set([castleKey]);
        let current = castleKey;
        while (true) {
          const { q, r } = parseKey(current);
          let found = null;
          for (const nb of hexNeighbors(q, r)) {
            const nk = `${nb.q},${nb.r}`;
            if (pathTiles.has(nk) && !visited.has(nk)) { found = nk; break; }
          }
          if (!found) break;
          visited.add(found);
          chain.push(parseKey(found));
          current = found;
        }
        if (chain.length > 1)
          allSegments.push({ points: chain.map(({ q, r }) => hexToPixel(q, r, sz)), alpha: 1 });
      }
    }

    // Enemy paths — clipped to visible area
    if (this._enemyPaths.size > 0) {
      const visibleKeys = new Set([...this.tiles.keys(), ...(this._lastInnerKeys ?? new Set())]);
      for (const [, path] of this._enemyPaths) {
        let segment = [];
        for (const p of path) {
          if (visibleKeys.has(`${p.q},${p.r}`)) {
            segment.push(hexToPixel(p.q, p.r, sz));
          } else {
            if (segment.length > 1) allSegments.push({ points: segment, alpha: 0.75 });
            segment = [];
          }
        }
        if (segment.length > 1) allSegments.push({ points: segment, alpha: 0.75 });
      }
    }

    if (allSegments.length === 0) return;

    // Build or reuse offscreen cache — invalidated when tiles/path change via _invalidateStatic()
    if (!this._pathCache) {
      this._pathCache = this._buildPathCache(allSegments, pathBmp, pathW);
    }
    if (!this._pathCache) return;

    const pc = this._pathCache;
    ctx.drawImage(pc.canvas, pc.x, pc.y, pc.canvas.width / pc.scale, pc.canvas.height / pc.scale);
  }

  /** Draw structure sprites + icon/label overlays at full zoom resolution.
   *  Called from _render() after the base canvas is composited, so sprites
   *  are always rasterised at display resolution (no upscale blur).
   *  Uses painter's algorithm (sort by pixel Y) for correct z-ordering. */
  _renderStructures(ctx) {
    const sz = this.hexSize;

    // Icons + coord labels (zoom-dependent, so must be here not in base cache)
    for (const [key, data] of this.tiles) {
      const { q, r } = parseKey(key);
      const tileType = getTileType(data.type);
      const { x, y } = hexToPixel(q, r, sz);

      if (tileType.icon && !tileType.spriteUrl && sz * this.zoom > 12) {
        ctx.fillStyle = '#ccccdd';
        ctx.font = `${Math.max(10, sz * 0.45)}px sans-serif`;
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(tileType.icon, x, y);
      }

      if (sz * this.zoom > 22) {
        ctx.fillStyle = 'rgba(255,255,255,0.2)';
        ctx.font = `${Math.max(7, sz * 0.25)}px monospace`;
        ctx.textAlign = 'center';
        ctx.textBaseline = 'bottom';
        ctx.fillText(`${q},${r}`, x, y + sz * 0.75);
      }
    }

    // Sprites sorted by pixel Y (painter's algorithm) so lower hexes render on
    // top. The list only changes when tiles change, so cache it and rebuild
    // lazily on static invalidation.
    if (!this._cachedSpriteTiles) {
      this._cachedSpriteTiles = [...this.tiles.entries()]
        .filter(([, data]) => {
          const tt = getTileType(data.type);
          return tt.spriteUrl && data.type !== 'void' && data.type !== 'path';
        })
        .map(([key, data]) => {
          const { q, r } = parseKey(key);
          const { x, y } = hexToPixel(q, r, sz);
          return { data, x, y };
        })
        .sort((a, b) => a.y - b.y);
    }
    const spriteTiles = this._cachedSpriteTiles;

    for (const { data, x, y } of spriteTiles) {
      const tileType = getTileType(data.type);
      const bitmap = this._spriteCache.get(tileType.spriteUrl);
      if (!bitmap) {
        this._ensureSpriteLoaded(tileType.spriteUrl);
        continue;
      }
      if (bitmap === 'loading') continue;
      const spriteSize = sz * 2.1;
      const yOffset =
        data.type === 'castle' || data.type === 'spawnpoint' ? spriteSize * 0.1 : spriteSize * 0.15;
      const aspect = bitmap.width / bitmap.height;
      const drawW = aspect >= 1 ? spriteSize : spriteSize * aspect;
      const drawH = aspect >= 1 ? spriteSize / aspect : spriteSize;
      ctx.drawImage(bitmap, x - drawW / 2, y - drawH / 2 - yOffset, drawW, drawH);
    }
  }

  /** Render critters on top of current canvas state (assumes transform already applied). */
  _renderCritters() {
    const ctx = this.ctx;
    const sz = this.hexSize;
    const ts = performance.now();

    for (const [cid, critter] of this.battleCritters) {
      const critterScale = critter.scale ?? 1.0;
      // Base size at scale=1: sz*0.467 (2/3 of sz*0.7), then multiplied by critter scale
      const spriteSize = sz * 0.467 * critterScale;
      const { x, y } = this._getCritterPixelPos(critter.path_progress, sz);
      const spriteKey = critter.iid.toLowerCase();
      const sprite = this._critterSprites.get(spriteKey);

      // Offset draw position upward so feet (bottom of sprite) sit on hex center
      const drawY = y - spriteSize / 2;

      // ── Status effect glow (drawn behind sprite) ──────────
      if (critter.slow_remaining_ms > 0) {
        ctx.save();
        ctx.globalAlpha = 0.4;
        ctx.fillStyle = '#4fc3f7';
        ctx.beginPath();
        ctx.arc(x, drawY, spriteSize * 0.65, 0, Math.PI * 2);
        ctx.fill();
        ctx.restore();
      }
      if (critter.burn_remaining_ms > 0) {
        ctx.save();
        ctx.globalAlpha = 0.2 + 0.15 * Math.sin(ts * 0.008);
        ctx.fillStyle = '#ff5500';
        ctx.beginPath();
        ctx.arc(x, drawY, spriteSize * 0.65, 0, Math.PI * 2);
        ctx.fill();
        ctx.restore();
      }

      if (sprite && sprite !== 'loading') {
        // ── Sprite animation ──────────────────────────────
        const dir = this._getCritterDirection(critter.path_progress);
        sprite.draw(ctx, dir, ts, x, drawY, spriteSize);
      } else {
        // ── Fallback: coloured circle ────────────────────
        if (!sprite) this._ensureCritterSprite(critter.iid);
        const color = critter.iid.toLowerCase().includes('soldier') ? '#4488ff' : '#ff4444';
        const strokeColor = critter.iid.toLowerCase().includes('soldier') ? '#2266dd' : '#dd2222';
        ctx.fillStyle = color;
        ctx.beginPath();
        ctx.arc(x, drawY, sz * 0.3 * critterScale, 0, Math.PI * 2);
        ctx.fill();
        ctx.strokeStyle = strokeColor;
        ctx.lineWidth = 2;
        ctx.stroke();
      }

      // ── Health bar ────────────────────────────────────
      if (critter.health != null && critter.max_health != null) {
        const barWidth = sz * 0.7;
        const barHeight = sz * 0.08;
        const barX = x - barWidth / 2;
        const barY = drawY - spriteSize / 2 - barHeight - 2;
        const healthPercent = Math.max(0, Math.min(1, critter.health / critter.max_health));
        ctx.fillStyle = '#331111';
        ctx.fillRect(barX, barY, barWidth, barHeight);
        ctx.fillStyle = '#44ff44';
        ctx.fillRect(barX, barY, barWidth * healthPercent, barHeight);
        ctx.strokeStyle = '#000000';
        ctx.lineWidth = 1;
        ctx.strokeRect(barX, barY, barWidth, barHeight);

        // ── Status effect icons ──────────────────────────────
        const statusIcons = [];
        if (critter.burn_remaining_ms > 0) statusIcons.push('🔥');
        if (critter.slow_remaining_ms > 0) statusIcons.push('❄');
        if (statusIcons.length) {
          ctx.font = `${Math.round(sz * 0.22)}px sans-serif`;
          ctx.textAlign = 'center';
          ctx.textBaseline = 'bottom';
          ctx.fillText(statusIcons.join(''), x, barY - 1);
        }
      }
    }
  }

  /** Return the visual center (mid-sprite) of a critter — same Y offset used in _renderCritters. */
  _getCritterVisualCenter(critter, sz) {
    const pos = this._getCritterPixelPos(critter.path_progress, sz);
    const spriteSize = sz * 0.467 * (critter.scale ?? 1.0);
    return { x: pos.x, y: pos.y - spriteSize / 2 };
  }

  /** Get interpolated pixel position of a shot between origin and target critter center. */
  _getShotPixelPos(shot, sz) {
    // Get origin position (tower hex), shifted up by projectile_y_offset * tower sprite height
    const originPos = hexToPixel(shot.origin_q, shot.origin_r, sz);
    const towerSpriteH = sz * 1.7;
    const adjustedOrigin = {
      x: originPos.x,
      y: originPos.y - (shot.projectile_y_offset ?? 0.0) * towerSpriteH,
    };

    // Get target critter visual center
    const targetCritter = this.battleCritters.get(shot.target_cid);
    if (!targetCritter) {
      return adjustedOrigin;
    }

    const targetPos = this._getCritterVisualCenter(targetCritter, sz);

    // Interpolate between adjusted origin and target based on path_progress
    const x = adjustedOrigin.x + (targetPos.x - adjustedOrigin.x) * shot.path_progress;
    const y = adjustedOrigin.y + (targetPos.y - adjustedOrigin.y) * shot.path_progress;

    return { x, y };
  }

  _renderShots() {
    const ctx = this.ctx;
    const sz = this.hexSize;

    // Draw battle shots (transform already applied by _render)
    for (const [shot_id, shot] of this.battleShots) {
      // Skip shots whose target has already died
      if (!this.battleCritters.has(shot.target_cid)) continue;

      const { x, y } = this._getShotPixelPos(shot, sz);

      // --- Sprite rendering (rotated toward target) ---
      if (shot.shot_sprite) {
        const bmp = this._spriteCache.get(shot.shot_sprite);
        if (bmp && bmp !== 'loading') {
          // Compute direction angle from adjusted origin to current target visual center
          const rawOrigin = hexToPixel(shot.origin_q, shot.origin_r, sz);
          const towerSpriteH = sz * 1.7;
          const originPos = {
            x: rawOrigin.x,
            y: rawOrigin.y - (shot.projectile_y_offset ?? 0.0) * towerSpriteH,
          };
          const targetCritter = this.battleCritters.get(shot.target_cid);
          let angle = 0;
          if (targetCritter) {
            const targetPos = this._getCritterVisualCenter(targetCritter, sz);
            angle = Math.atan2(targetPos.y - originPos.y, targetPos.x - originPos.x);
          }
          const spriteSize = sz * 0.55 * (shot.shot_sprite_scale ?? 1.0);
          const aspectRatio = bmp.width / bmp.height;
          const spriteW = spriteSize * Math.max(1, aspectRatio);
          const spriteH = spriteSize * Math.max(1, 1 / aspectRatio);
          ctx.save();
          ctx.translate(x, y);
          ctx.rotate(angle);
          ctx.drawImage(bmp, -spriteW / 2, -spriteH / 2, spriteW, spriteH);
          ctx.restore();
          continue;
        }
      }

      // --- Fallback: colored dot ---
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

  /**
   * Draw the viewport-bounded fog / enemy tiles. Runs every frame on the
   * main context (already translated + zoom-scaled by the caller), so the
   * set stays small and never bloats the cached base canvas.
   */
  _renderNeighborTiles(ctx) {
    if (this._neighborTiles.size === 0 && this.tiles.size === 0) return;
    const sz = this.hexSize;

    // BFS: innerKeys = (visionRadius-1) steps outside own tiles, no fog.
    //      ring1Keys  = the visionRadius-th ring, rendered with fog overlay.
    const innerKeys = new Set();
    let frontier = new Set(this.tiles.keys());
    for (let step = 0; step < this.visionRadius - 1; step++) {
      const next = new Set();
      for (const key of frontier) {
        const { q, r } = parseKey(key);
        for (const { q: nq, r: nr } of hexNeighbors(q, r)) {
          const nk = `${nq},${nr}`;
          if (!this.tiles.has(nk) && !innerKeys.has(nk)) { innerKeys.add(nk); next.add(nk); }
        }
      }
      frontier = next;
    }
    const ring1Keys = new Set();
    for (const key of frontier) {
      const { q, r } = parseKey(key);
      for (const { q: nq, r: nr } of hexNeighbors(q, r)) {
        const nk = `${nq},${nr}`;
        if (!this.tiles.has(nk) && !innerKeys.has(nk)) ring1Keys.add(nk);
      }
    }

    const _buildPath = (keys) => {
      const p = new Path2D();
      for (const key of keys) {
        const { q, r } = parseKey(key);
        const { x, y } = hexToPixel(q, r, sz);
        const c = hexCorners(x, y, sz);
        p.moveTo(c[0].x, c[0].y);
        for (let i = 1; i < 6; i++) p.lineTo(c[i].x, c[i].y);
        p.closePath();
      }
      return p;
    };

    // Inner tiles (within vision radius): grass, no fog, no outline
    if (this._tilePattern && innerKeys.size > 0) {
      const innerPath = _buildPath(innerKeys);
      ctx.save();
      ctx.clip(innerPath);
      ctx.globalAlpha = this.mapAlpha;
      ctx.fillStyle = this._tilePattern;
      ctx.fill(innerPath);
      ctx.globalAlpha = 1;
      ctx.restore();
    }

    // Outer fog ring: grass + dark fog overlay
    if (this._tilePattern && ring1Keys.size > 0) {
      const ringPath = _buildPath(ring1Keys);
      ctx.save();
      ctx.clip(ringPath);
      ctx.globalAlpha = this.mapAlpha;
      ctx.fillStyle = this._tilePattern;
      ctx.fill(ringPath);
      ctx.globalAlpha = 0.72;
      ctx.fillStyle = 'rgba(15, 15, 25, 1)';
      ctx.fill(ringPath);
      ctx.globalAlpha = 1;
      ctx.restore();
    }

    // Border edges: draw a colored line segment for each edge where the two
    // adjacent tiles have different owners (void/fog count as "no owner",
    // which differs from "self"). Green = own-empire boundary, red =
    // enemy-empire boundary.
    //
    // Edge-index mapping: neighbor i (= DIRS[i]) does NOT face the edge
    // corner[i]→corner[i+1]. With flat-top hexes and y-down screen coords
    // the correct edge start is (6 - i) % 6 (see plan / hex.js geometry).
    const edgeStart = i => (6 - i) % 6;
    const ownerKey = (q, r) => {
      const k = hexKey(q, r);
      const own = this.tiles.get(k);
      if (own && own.type !== 'void') return 'self';
      const nb = this._neighborTiles.get(k);
      if (nb && nb.uid != null) return 'e:' + nb.uid;
      return 'none';
    };

    const greenEdges = new Path2D();
    const greenClip = new Path2D();
    const redEdges = new Path2D();
    const redClip = new Path2D();

    const addHexToPath = (path, x, y) => {
      const c = hexCorners(x, y, sz);
      path.moveTo(c[0].x, c[0].y);
      for (let i = 1; i < 6; i++) path.lineTo(c[i].x, c[i].y);
      path.closePath();
    };

    // Green pass — own empire boundary, not against fog ring.
    for (const [key, data] of this.tiles) {
      if (data.type === 'void') continue;
      const { q, r } = parseKey(key);
      const { x, y } = hexToPixel(q, r, sz);
      const corners = hexCorners(x, y, sz);
      addHexToPath(greenClip, x, y);
      const neighbors = hexNeighbors(q, r);
      for (let i = 0; i < 6; i++) {
        const nb = neighbors[i];
        const nk = `${nb.q},${nb.r}`;
        if (ownerKey(nb.q, nb.r) === 'self') continue;
        if (ring1Keys.has(nk)) continue;
        const j = edgeStart(i);
        greenEdges.moveTo(corners[j].x, corners[j].y);
        greenEdges.lineTo(corners[(j + 1) % 6].x, corners[(j + 1) % 6].y);
      }
    }
    // Green pass for visible (innerKeys) non-enemy tiles — draw outline on all sides except fog ring.
    for (const key of innerKeys) {
      if (this._neighborTiles.get(key)?.uid != null) continue; // enemy tiles handled in red pass
      const { q, r } = parseKey(key);
      const { x, y } = hexToPixel(q, r, sz);
      const corners = hexCorners(x, y, sz);
      addHexToPath(greenClip, x, y);
      const neighbors = hexNeighbors(q, r);
      for (let i = 0; i < 6; i++) {
        const nb = neighbors[i];
        const nk = `${nb.q},${nb.r}`;
        if (this.tiles.has(nk) || innerKeys.has(nk)) continue; // shared interior
        if (ring1Keys.has(nk)) continue;
        const j = edgeStart(i);
        greenEdges.moveTo(corners[j].x, corners[j].y);
        greenEdges.lineTo(corners[(j + 1) % 6].x, corners[(j + 1) % 6].y);
      }
    }

    // Red pass — enemy cluster boundary, not against fog ring.
    for (const [key, ndata] of this._neighborTiles) {
      if (ndata.uid == null) continue;
      const selfKey = 'e:' + ndata.uid;
      const { q, r } = parseKey(key);
      const { x, y } = hexToPixel(q, r, sz);
      const corners = hexCorners(x, y, sz);
      addHexToPath(redClip, x, y);
      const neighbors = hexNeighbors(q, r);
      for (let i = 0; i < 6; i++) {
        const nb = neighbors[i];
        const nk = `${nb.q},${nb.r}`;
        if (ownerKey(nb.q, nb.r) === selfKey) continue;
        if (ring1Keys.has(nk)) continue;
        const j = edgeStart(i);
        redEdges.moveTo(corners[j].x, corners[j].y);
        redEdges.lineTo(corners[(j + 1) % 6].x, corners[(j + 1) % 6].y);
      }
    }

    const lw = 3 / this.zoom;
    ctx.save();
    ctx.lineWidth = lw;
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    ctx.save();
    ctx.clip(greenClip);
    ctx.strokeStyle = 'rgba(50,170,70,0.75)';
    ctx.stroke(greenEdges);
    ctx.restore();
    ctx.save();
    ctx.clip(redClip);
    ctx.strokeStyle = 'rgba(190,45,45,0.75)';
    ctx.stroke(redEdges);
    ctx.restore();
    ctx.restore();
    ctx.filter = 'none';

    this._lastInnerKeys = innerKeys;
  }

  _renderEnemySprites(ctx) {
    const sz = this.hexSize;
    const NON_STRUCTURE_TILE = new Set(['empty', 'void', 'blocked', 'land']);
    const enemySprites = [];
    for (const [key, data] of this._neighborTiles) {
      if (data.uid == null) continue;
      // tile_type tells us the hex type (path/castle/spawnpoint/empty)
      // iid tells us what structure is on top (tower iid or same as tile_type)
      const tt = (data.tile_type ?? data.iid)?.toLowerCase();
      const spriteIid = data.iid;
      if (!spriteIid || NON_STRUCTURE_TILE.has(tt)) continue;
      const { q, r } = parseKey(key);
      const { x, y } = hexToPixel(q, r, sz);
      enemySprites.push({ iid: spriteIid, x, y });
    }
    enemySprites.sort((a, b) => a.y - b.y);
    for (const { iid, x, y } of enemySprites) {
      const tileType = getTileType(iid);
      if (!tileType?.spriteUrl) continue;
      let bmp = this._spriteCache.get(tileType.spriteUrl);
      if (!bmp) { this._ensureSpriteLoaded(tileType.spriteUrl); continue; }
      if (bmp === 'loading') continue;
      const spriteSize = sz * 2.1;
      const aspect = bmp.width / bmp.height;
      const drawW = aspect >= 1 ? spriteSize : spriteSize * aspect;
      const drawH = aspect >= 1 ? spriteSize / aspect : spriteSize;
      const yOffset = spriteSize * 0.15;
      ctx.save();
      ctx.globalAlpha = 0.75;
      ctx.drawImage(bmp, x - drawW / 2, y - drawH / 2 - yOffset, drawW, drawH);
      ctx.restore();
    }
  }

  /**
   * Render every static layer (grass texture, tile outlines, fog/enemy
   * neighbor tiles + boundary edges, color tints, battle/enemy paths, and
   * enemy + structure sprites) into an offscreen canvas at the current zoom
   * resolution. Composited each frame with a single drawImage in _render().
   * Only rebuilt when tiles / neighbor tiles / zoom / vision radius change.
   */
  _renderStatic() {
    if (this.tiles.size === 0) return; // retry next frame

    if (!this._staticCanvas) {
      this._staticCanvas = document.createElement('canvas');
    }

    // World bounds over owned + neighbor tiles, padded for fog rings beyond
    // the vision radius and for sprite/edge overflow outside the hex.
    let minX = Infinity,
      maxX = -Infinity,
      minY = Infinity,
      maxY = -Infinity;
    const acc = (q, r) => {
      const { x, y } = hexToPixel(q, r, this.hexSize);
      if (x < minX) minX = x;
      if (x > maxX) maxX = x;
      if (y < minY) minY = y;
      if (y > maxY) maxY = y;
    };
    for (const key of this.tiles.keys()) {
      const { q, r } = parseKey(key);
      acc(q, r);
    }
    for (const key of this._neighborTiles.keys()) {
      const { q, r } = parseKey(key);
      acc(q, r);
    }
    const pad = this.hexSize * (this.visionRadius + 3);
    minX -= pad;
    minY -= pad;
    maxX += pad;
    maxY += pad;

    const worldW = maxX - minX;
    const worldH = maxY - minY;
    const dpr = window.devicePixelRatio || 1;
    const MAX_TEXTURE = 8192;
    const wantScale = dpr * this.zoom;
    const actualScale = Math.min(wantScale,
      Math.min(MAX_TEXTURE / (worldW || 1), MAX_TEXTURE / (worldH || 1)));

    this._staticCanvas.width  = Math.max(1, Math.ceil(worldW * actualScale));
    this._staticCanvas.height = Math.max(1, Math.ceil(worldH * actualScale));
    this._staticCanvasScale = actualScale;
    this._staticWorldOffsetX = minX;
    this._staticWorldOffsetY = minY;
    this._staticZoom = this.zoom;

    const ctx = this._staticCanvas.getContext('2d');
    ctx.save();
    ctx.setTransform(actualScale, 0, 0, actualScale, 0, 0);
    ctx.imageSmoothingEnabled = true;
    ctx.imageSmoothingQuality = 'high';
    ctx.clearRect(0, 0, worldW, worldH);
    // World-space transform: translate so world origin (minX,minY) → canvas (0,0).
    // Line widths using 1/zoom and 8/zoom remain correct because when drawn
    // scaled by zoom the result is zoom-invariant screen pixels.
    ctx.translate(-minX, -minY);

    const sz = this.hexSize;

    // Grass texture over all tiles (owned + enemy neighbor tiles)
    if (this._mapBitmap && this.tiles.size > 0) {
      const pattern = this._tilePattern ?? ctx.createPattern(this._mapBitmap, 'repeat');
      const allTilesPath = new Path2D();
      const ownedTilesPath = new Path2D();
      const enemyTilesPath = new Path2D();
      for (const [key, data] of this.tiles) {
        const { q, r } = parseKey(key);
        const { x, y } = hexToPixel(q, r, sz);
        const c = hexCorners(x, y, sz);
        const addTo = (p) => {
          p.moveTo(c[0].x, c[0].y);
          for (let i = 1; i < 6; i++) p.lineTo(c[i].x, c[i].y);
          p.closePath();
        };
        addTo(allTilesPath);
        if (data.type !== 'void') addTo(ownedTilesPath);
      }
      for (const [key, data] of this._neighborTiles) {
        if (data.uid == null) continue;
        const { q, r } = parseKey(key);
        const { x, y } = hexToPixel(q, r, sz);
        const c = hexCorners(x, y, sz);
        const addEnemy = (p) => {
          p.moveTo(c[0].x, c[0].y);
          for (let i = 1; i < 6; i++) p.lineTo(c[i].x, c[i].y);
          p.closePath();
        };
        addEnemy(enemyTilesPath);
        addEnemy(allTilesPath);
      }
      ctx.save();
      ctx.clip(allTilesPath);
      ctx.fillStyle = pattern;
      ctx.fill(allTilesPath);
      ctx.restore();
      this._ownedTilesPath = ownedTilesPath;
      this._enemyTilesPath = enemyTilesPath;
    }

    // Tile outlines (own + enemy)
    if (this.tiles.size > 0 || this._neighborTiles.size > 0) {
      ctx.save();
      ctx.strokeStyle = 'rgba(120,120,120,0.5)';
      ctx.lineWidth = 1 / this.zoom;
      const drawOutline = (q, r) => {
        const { x, y } = hexToPixel(q, r, sz);
        const c = hexCorners(x, y, sz);
        ctx.beginPath();
        ctx.moveTo(c[0].x, c[0].y);
        for (let i = 1; i < 6; i++) ctx.lineTo(c[i].x, c[i].y);
        ctx.closePath();
        ctx.stroke();
      };
      for (const [key] of this.tiles) {
        const { q, r } = parseKey(key);
        drawOutline(q, r);
      }
      for (const [key, data] of this._neighborTiles) {
        if (data.uid == null) continue;
        const { q, r } = parseKey(key);
        drawOutline(q, r);
      }
      ctx.restore();
    }

    // Viewport-bounded fog / enemy tiles + boundary edges
    this._renderNeighborTiles(ctx);

    // Color tints on top of fog/grass
    if (this._ownedTilesPath) {
      ctx.save();
      ctx.globalAlpha = 0.15;
      ctx.fillStyle = 'rgba(60, 180, 80, 1)';
      ctx.fill(this._ownedTilesPath);
      ctx.restore();
    }
    if (this._enemyTilesPath) {
      ctx.save();
      ctx.globalAlpha = 0.15;
      ctx.fillStyle = 'rgba(200, 60, 60, 1)';
      ctx.fill(this._enemyTilesPath);
      ctx.restore();
    }


    ctx.restore();
    this._staticDirty = false;
  }

  _render() {
    const ctx = this.ctx;
    const w = this._logicalWidth || this.canvas.width;
    const h = this._logicalHeight || this.canvas.height;
    const dpr = window.devicePixelRatio || 1;

    // Clear entire canvas
    ctx.save();
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.imageSmoothingEnabled = false;
    ctx.clearRect(0, 0, w, h);

    // Render base layer to cache only when tiles change (not on zoom)
    if (!this._baseCached) {
      this._renderBase();
    }

    // Apply only translation (zoom is already in the base layer)
    ctx.translate(this.offsetX, this.offsetY);

    // Draw cached base layer (already zoomed)
    // Guard: a 0-sized canvas (e.g. when tiles map is empty) would throw a
    // DOMException on Chrome — skip drawing until dimensions are valid.
    if (this._baseCanvas && this._baseCanvas.width > 0 && this._baseCanvas.height > 0) {
      const scale = this.zoom / dpr;
      ctx.drawImage(
        this._baseCanvas,
        this._baseWorldOffsetX * this.zoom,
        this._baseWorldOffsetY * this.zoom,
        this._baseCanvas.width * scale,
        this._baseCanvas.height * scale
      );
    }

    // Composite the cached static layer (grass, outlines, fog/edges, tints,
    // path, enemy + structure sprites).
    // — Content changes (tiles, neighbors, paths): rebuild immediately.
    // — Zoom changes: reuse old cache at a rescaled draw size until the zoom
    //   gesture settles (debounce), then rebuild once. This avoids an expensive
    //   full rebuild on every wheel tick while the user is still zooming.
    if (this._staticDirty || !this._staticCanvas) {
      this._renderStatic();
    }
    if (
      this._staticCanvas &&
      this._staticCanvas.width > 0 &&
      this._staticCanvas.height > 0
    ) {
      // Draw static canvas at the scale it was rendered at.
      // After zoom settles: scs = dpr*zoom → staticScale = 1/dpr (1:1 sharp).
      // During gesture: scs = dpr*oldZoom → staticScale = zoom/(dpr*oldZoom) (rescaled).
      const scs = this._staticCanvasScale || dpr;
      const staticScale = this.zoom / scs;
      // Round position to whole physical pixels to avoid sub-pixel interpolation
      // artifacts that shift visually during pan.
      const drawX = Math.round(this._staticWorldOffsetX * this.zoom * dpr) / dpr;
      const drawY = Math.round(this._staticWorldOffsetY * this.zoom * dpr) / dpr;
      ctx.drawImage(
        this._staticCanvas,
        drawX,
        drawY,
        this._staticCanvas.width  * staticScale,
        this._staticCanvas.height * staticScale
      );
    }

    // Apply zoom for per-frame dynamic layers (not in any cache)
    ctx.scale(this.zoom, this.zoom);

    // Path rendered per-frame so texture stays stable during pan
    this._renderPath(ctx);

    // Enemy sprites above path
    this._renderEnemySprites(ctx);

    // Structures (towers, castle, spawnpoint) above path
    this._renderStructures(ctx);

    // Draw range circle overlay if set
    if (this.rangeOverlay) {
      const { q, r, radius } = this.rangeOverlay;
      const { x, y } = hexToPixel(q, r, this.hexSize);
      const pxRadius = radius * this.hexSize * Math.sqrt(3);
      ctx.save();
      ctx.beginPath();
      ctx.arc(x, y, pxRadius, 0, Math.PI * 2);
      ctx.strokeStyle = 'rgba(100,180,255,0.85)';
      ctx.lineWidth = 2 / this.zoom;
      ctx.setLineDash([6 / this.zoom, 4 / this.zoom]);
      ctx.stroke();
      ctx.fillStyle = 'rgba(100,180,255,0.08)';
      ctx.fill();
      ctx.restore();
    }

    // Draw shots first (behind critters)
    if (this.battleShots.size > 0) {
      this._renderShots();
    }

    // Draw critters on top
    if (this.battleCritters.size > 0) {
      this._renderCritters();
    }

    // Draw castle health bar above all critters
    if (this.battleActive && this._castlePos) {
      this._renderCastleHealthBar();
    }

    ctx.restore();

  }

  // ── Cleanup ────────────────────────────────────────────────

  destroy() {
    if (this._rafId) cancelAnimationFrame(this._rafId);
    if (this._resizeObserver) this._resizeObserver.disconnect();
    if (this._resizeTimeout) clearTimeout(this._resizeTimeout);
    if (this._staticRebuildTimerId !== null) clearTimeout(this._staticRebuildTimerId);

    // Remove all event listeners to prevent stale handlers on re-enter
    if (this._handlers) {
      this.canvas.removeEventListener('mousemove', this._handlers.mousemove);
      this.canvas.removeEventListener('mousedown', this._handlers.mousedown);
      this.canvas.removeEventListener('mouseup', this._handlers.mouseup);
      this.canvas.removeEventListener('mouseleave', this._handlers.mouseleave);
      this.canvas.removeEventListener('wheel', this._handlers.wheel);
      this.canvas.removeEventListener('click', this._handlers.click);
      this.canvas.removeEventListener('touchstart', this._handlers.touchstart);
      this.canvas.removeEventListener('touchmove', this._handlers.touchmove);
      this.canvas.removeEventListener('touchend', this._handlers.touchend);
      this.canvas.removeEventListener('touchcancel', this._handlers.touchcancel);
      this.canvas.removeEventListener('dragover', this._handlers.dragover);
      this.canvas.removeEventListener('drop', this._handlers.drop);
      this._handlers = null;
    }

    // Clear callbacks to release closure references
    this.onTileClick = null;
    this.onTileDrop = null;
  }
}
