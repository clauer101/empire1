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

    // Pan state
    this._isPanning = false;
    this._panStartX = 0;
    this._panStartY = 0;
    this._panOffsetX = 0;
    this._panOffsetY = 0;

    // Animation
    this._rafId = null;
    this._dirty = true;

    this._initGrid();
    this.addVoidNeighbors();
    this._bindEvents();
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
    this.offsetX = (this.canvas.width / 2 - (minX + maxX) / 2);
    this.offsetY = (this.canvas.height / 2 - (minY + maxY) / 2);
    this._dirty = true;
  }

  // ── Event binding ──────────────────────────────────────────

  _bindEvents() {
    this.canvas.addEventListener('mousemove', (e) => this._onMouseMove(e));
    this.canvas.addEventListener('mousedown', (e) => this._onMouseDown(e));
    this.canvas.addEventListener('mouseup', (e) => this._onMouseUp(e));
    this.canvas.addEventListener('mouseleave', () => this._onMouseLeave());
    this.canvas.addEventListener('wheel', (e) => this._onWheel(e), { passive: false });
    this.canvas.addEventListener('click', (e) => this._onClick(e));

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
    this._resizeObserver = new ResizeObserver(() => this._resize());
    this._resizeObserver.observe(this.canvas.parentElement);
  }

  _resize() {
    const parent = this.canvas.parentElement;
    const dpr = window.devicePixelRatio || 1;
    const w = parent.clientWidth;
    const h = parent.clientHeight;
    this.canvas.width = w * dpr;
    this.canvas.height = h * dpr;
    this.canvas.style.width = w + 'px';
    this.canvas.style.height = h + 'px';
    this.ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    this._logicalWidth = w;
    this._logicalHeight = h;
    this._centerGrid();
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
      const dx = e.clientX - this._panStartX;
      const dy = e.clientY - this._panStartY;
      this.offsetX = this._panOffsetX + dx;
      this.offsetY = this._panOffsetY + dy;
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
    const rect = this.canvas.getBoundingClientRect();
    const mx = e.clientX - rect.left;
    const my = e.clientY - rect.top;

    const oldZoom = this.zoom;
    const factor = e.deltaY < 0 ? 1.08 : 0.92;
    this.zoom = Math.max(0.3, Math.min(3.0, this.zoom * factor));

    // Zoom toward cursor
    this.offsetX = mx - (mx - this.offsetX) * (this.zoom / oldZoom);
    this.offsetY = my - (my - this.offsetY) * (this.zoom / oldZoom);
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

  // ── Tile manipulation ──────────────────────────────────────

  setTile(q, r, typeId, meta = {}) {
    const key = hexKey(q, r);
    if (!this.tiles.has(key)) return;
    this.tiles.set(key, { type: typeId, ...meta });
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
    const loop = () => {
      if (this._dirty) {
        this._render();
        this._dirty = false;
      }
      this._rafId = requestAnimationFrame(loop);
    };
    loop();
  }

  _render() {
    const ctx = this.ctx;
    const w = this._logicalWidth || this.canvas.width;
    const h = this._logicalHeight || this.canvas.height;

    // Clear
    ctx.save();
    ctx.setTransform(window.devicePixelRatio || 1, 0, 0, window.devicePixelRatio || 1, 0, 0);
    ctx.clearRect(0, 0, w, h);

    // Apply camera
    ctx.translate(this.offsetX, this.offsetY);
    ctx.scale(this.zoom, this.zoom);

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

    ctx.restore();
  }

  // ── Cleanup ────────────────────────────────────────────────

  destroy() {
    if (this._rafId) cancelAnimationFrame(this._rafId);
    if (this._resizeObserver) this._resizeObserver.disconnect();
  }
}
