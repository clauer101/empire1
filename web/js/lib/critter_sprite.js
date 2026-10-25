/**
 * critter_sprite.js — Unified critter animation loader.
 *
 * Handles two animation formats transparently:
 *
 *  1. Sprite sheet (4 rows × 4 or 8 columns, detected by sprite_grid.js)
 *     Row 0 → forward  (towards viewer)
 *     Row 1 → left
 *     Row 2 → right
 *     Row 3 → backward (away from viewer)
 *     Each row holds one animation cycle (4 or 8 frames).
 *
 *  2. GIF set — four separate animated GIFs:
 *       front.gif  → forward
 *       left.gif   → left
 *       right.gif  → right
 *       back.gif   → backward
 *     GIFs cannot be sampled frame-by-frame via ctx.drawImage() in Chromium.
 *     Use getImg(direction) to obtain the raw <img> element and display it
 *     directly in the DOM — the browser animates it natively.
 *
 * Usage:
 *   const sprite = CritterSprite.fromManifest(entry);
 *   await sprite.load();
 *
 *   // Sprite sheet — inside requestAnimationFrame loop:
 *   sprite.draw(ctx, 'forward', timestamp, x, y, 64);
 *
 *   // GIF — display the live <img> directly:
 *   const img = sprite.getImg('forward');  // HTMLImageElement, animated by browser
 *   img.style.width = '96px';
 *   someContainer.appendChild(img);
 *
 *   // Query type:
 *   sprite.type  // 'spritesheet' | 'gifs'
 *   sprite.ready // true once loaded
 */

import { detectSheetGrid, frameIndex } from './sprite_grid.js';

// ─── Constants ────────────────────────────────────────────────────────────────

export const DEFAULT_FPS = 8;

/** Critter sprite width at scale 1, as a fraction of the hex radius. */
const CRITTER_BASE_WIDTH = 0.467;

/**
 * Rendered critter sprite width in px — the single source for battle and tools.
 * @param {number} hexSize  Hex outer radius in px.
 * @param {number} [scale=1]  Critter scale from the backend.
 * @returns {number}
 */
export function critterSpriteWidth(hexSize, scale = 1.0) {
  return hexSize * CRITTER_BASE_WIDTH * scale;
}

/**
 * Center Y of a critter sprite standing on the point (x, y) — shared by battle and tools.
 * In battle the sprite center sits half a width above the hex center; `yOffset`
 * (backend `sprite_y_offset`) shifts it further by a fraction of the rendered
 * sprite height, positive = up.
 *
 * @param {number} y          Ground point Y (hex center on the path).
 * @param {number} width      Rendered sprite width (critterSpriteWidth).
 * @param {CritterSprite|null} sprite  Loaded sprite (null → treat as square).
 * @param {number} [yOffset=0]
 * @returns {number}
 */
export function critterSpriteCenterY(y, width, sprite, yOffset = 0) {
  const aspect = sprite?.frameW > 0 ? sprite.frameH / sprite.frameW : 1;
  return y - width / 2 - yOffset * width * aspect;
}

/** Direction name → sprite-sheet row index. */
export const DIRECTION_ROW = {
  forward: 0,
  left: 1,
  right: 2,
  backward: 3,
};

/** Ordered direction names (matches row 0-3). */
export const DIRECTIONS = ['forward', 'left', 'right', 'backward'];

// ─── Sprite-sheet backend ────────────────────────────────────────────────────

/**
 * Load a sprite-sheet PNG and return the sheet as a single OffscreenCanvas
 * together with the detected grid.
 *
 * We intentionally avoid slicing the sheet into individual ImageBitmaps because
 * createImageBitmap(offscreenCanvas) transfers the underlying bitmap in Chromium,
 * leaving the source canvas neutered and triggering the
 * "object is not, or is no longer, usable" DOMException.
 *
 * Instead, frames are clipped at draw time via the 9-argument ctx.drawImage() form.
 *
 * @param {string} url
 * @returns {Promise<{sheet: OffscreenCanvas, cols: number, rows: number, frameW: number, frameH: number}>}
 */
async function loadSheetFrames(url) {
  const blob = await fetch(url).then((r) => {
    if (!r.ok) throw new Error(`HTTP ${r.status} loading ${url}`);
    return r.blob();
  });
  const img = await createImageBitmap(blob);

  const grid = detectSheetGrid(img);

  // Draw the full sheet onto a single OffscreenCanvas
  const sheet = new OffscreenCanvas(img.width, img.height);
  const ctx = sheet.getContext('2d');
  ctx.drawImage(img, 0, 0);

  // Free the source ImageBitmap — we no longer need it
  img.close();

  return { sheet, ...grid };
}

// ─── GIF backend ─────────────────────────────────────────────────────────────

/**
 * Load four GIF URLs.
 * We only need the src and natural dimensions here; actual animation is handled
 * by a visible <img> element in the DOM (via getImg() / preview page wiring).
 *
 * @param {{forward:string, left:string, right:string, backward:string}} urls
 * @returns {Promise<{imgs: Object, frameW: number, frameH: number}>}
 */
async function loadGifImgs(urls) {
  const imgs = {};
  let frameW = 0,
    frameH = 0;

  await Promise.all(
    DIRECTIONS.map(
      (dir) =>
        new Promise((resolve, reject) => {
          const img = new Image();
          img.onload = () => {
            imgs[dir] = img;
            frameW = Math.max(frameW, img.naturalWidth);
            frameH = Math.max(frameH, img.naturalHeight);
            resolve();
          };
          img.onerror = () => reject(new Error(`Failed to load GIF: ${img.src}`));
          img.src = urls[dir];
        })
    )
  );

  return { imgs, frameW, frameH };
}

// ─── Unified CritterSprite class ────────────────────────────────────────────

export class CritterSprite {
  /**
   * @param {'spritesheet'|'gifs'|'single'} type
   * @param {string|{forward:string,left:string,right:string,backward:string}} src
   *        For 'spritesheet'/'single': URL to the image.
   *        For 'gifs': object mapping direction → GIF URL.
   * @param {number} [fps]  Only relevant for sprite sheets; refers to a 4-frame cycle.
   */
  constructor(type, src, fps = DEFAULT_FPS) {
    this.type = type;
    this._src = src;
    this.fps = fps;

    // Set after load()
    this.frameW = 0;
    this.frameH = 0;
    /** Sheet grid (sprite sheets only; GIFs keep the defaults). */
    this.cols = 1;
    this.rows = DIRECTIONS.length;
    this._ready = false;

    // Sprite-sheet internals — single processed OffscreenCanvas
    /** @type {OffscreenCanvas|null} */
    this._sheet = null;

    // GIF internals
    /** @type {Object|null} */
    this._imgs = null;

    this._loadPromise = null;
  }

  // ── Factory ──────────────────────────────────────────────

  /**
   * Create a CritterSprite from a /api/critters manifest entry.
   *
   * @param {{name:string, type:string, file?:string, files?:Object}} entry
   * @param {string} [base='']  URL prefix prepended to relative paths (e.g. '/').
   * @param {number} [fps]
   * @returns {CritterSprite}
   */
  static fromManifest(entry, base = '', fps = DEFAULT_FPS) {
    if (entry.type === 'gifs') {
      const files = base
        ? Object.fromEntries(DIRECTIONS.map((d) => [d, `${base}/${entry.files[d]}`]))
        : entry.files;
      return new CritterSprite('gifs', files, fps);
    }
    const url = base ? `${base}/${entry.file}` : entry.file;
    return new CritterSprite('spritesheet', url, fps);
  }

  // ── Loading ──────────────────────────────────────────────

  /**
   * Load the animation data.  Safe to await multiple times.
   * @returns {Promise<void>}
   */
  load() {
    if (this._loadPromise) return this._loadPromise;

    if (this.type === 'spritesheet') {
      this._loadPromise = loadSheetFrames(this._src).then(({ sheet, cols, rows, frameW, frameH }) => {
        this._sheet = sheet;
        this.cols = cols;
        this.rows = rows;
        this.frameW = frameW;
        this.frameH = frameH;
        this._ready = true;
      });
    } else {
      // GIF: src is already a map of direction → absolute URL
      this._loadPromise = loadGifImgs(this._src).then(({ imgs, frameW, frameH }) => {
        this._imgs = imgs;
        this.frameW = frameW;
        this.frameH = frameH;
        this._ready = true;
      });
    }

    return this._loadPromise;
  }

  /** True once load() has completed successfully. */
  get ready() {
    return this._ready;
  }

  /**
   * For GIF critters: return the live <img> element for a direction.
   * The browser animates it natively — just insert it into the DOM.
   * Returns null for spritesheet critters.
   * @param {'forward'|'left'|'right'|'backward'} direction
   * @returns {HTMLImageElement|null}
   */
  getImg(direction) {
    return this._imgs?.[direction] ?? null;
  }

  // ── Drawing ──────────────────────────────────────────────

  /**
   * Draw the current animation frame for a given direction.
   *
   * @param {CanvasRenderingContext2D} ctx
   * @param {'forward'|'left'|'right'|'backward'} direction
   * @param {number} timestamp  Current time in ms (from requestAnimationFrame).
   * @param {number} x          Center X on the canvas.
   * @param {number} y          Center Y on the canvas.
   * @param {number} [size=64]  Rendered width in px; height preserves aspect ratio.
   */
  draw(ctx, direction, timestamp, x, y, size = 64) {
    if (!this._ready) return;

    if (this.type === 'spritesheet') {
      const row = DIRECTION_ROW[direction] ?? 0;
      const col = frameIndex(timestamp, this.fps, this.cols);
      this._drawSheetFrame(ctx, row, col, x, y, size);
    } else {
      const img = this._imgs[direction];
      if (img) this._drawImg(ctx, img, x, y, size);
    }
  }

  /**
   * Draw a specific frame by row / column (useful for sprite-sheet previews).
   * For GIF critters, `row` selects the direction and `col` is ignored.
   *
   * @param {CanvasRenderingContext2D} ctx
   * @param {number} row  Direction row index (0-3).
   * @param {number} col  Frame column index (0 to cols-1).
   * @param {number} x
   * @param {number} y
   * @param {number} [size=64]
   */
  drawFrame(ctx, row, col, x, y, size = 64) {
    if (!this._ready) return;

    if (this.type === 'spritesheet') {
      this._drawSheetFrame(ctx, row % this.rows, col % this.cols, x, y, size);
    } else {
      const dir = DIRECTIONS[row % this.rows];
      const img = this._imgs[dir];
      if (img) this._drawImg(ctx, img, x, y, size);
    }
  }

  // ── Helpers ───────────────────────────────────────────────

  /**
   * Clip one frame from the sheet canvas and draw it scaled.
   * Uses the 9-argument drawImage form to avoid any ImageBitmap ownership issues.
   */
  _drawSheetFrame(ctx, row, col, x, y, size) {
    const sx = col * this.frameW;
    const sy = row * this.frameH;
    const w = size;
    const h = (this.frameH / this.frameW) * size;
    ctx.drawImage(this._sheet, sx, sy, this.frameW, this.frameH, x - w / 2, y - h / 2, w, h);
  }

  _drawImg(ctx, img, x, y, size) {
    const w = size;
    const h = (img.naturalHeight / img.naturalWidth) * size;
    ctx.drawImage(img, x - w / 2, y - h / 2, w, h);
  }
}
