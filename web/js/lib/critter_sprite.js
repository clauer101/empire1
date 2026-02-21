/**
 * critter_sprite.js — Unified critter animation loader.
 *
 * Handles two animation formats transparently:
 *
 *  1. Sprite sheet (PNG, 4×4 grid)
 *     Row 0 → forward  (towards viewer)
 *     Row 1 → left
 *     Row 2 → right
 *     Row 3 → backward (away from viewer)
 *     Each row has 4 animation frames.
 *     Near-white background is keyed out automatically.
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

// ─── Constants ────────────────────────────────────────────────────────────────

export const COLS = 4;
export const ROWS = 4;
export const DEFAULT_FPS = 8;

/** Direction name → sprite-sheet row index. */
export const DIRECTION_ROW = {
  forward:  0,
  left:     1,
  right:    2,
  backward: 3,
};

/** Ordered direction names (matches row 0-3). */
export const DIRECTIONS = ['forward', 'left', 'right', 'backward'];

/** Near-white background keying parameters (for sprite sheets). */
const BG_R = 252, BG_G = 252, BG_B = 252, BG_TOL = 20;

// ─── Background removal (sprite sheets) ────────────────────────────────────

function removeBackground(imageData) {
  const d = imageData.data;
  for (let i = 0; i < d.length; i += 4) {
    if (
      Math.abs(d[i]     - BG_R) <= BG_TOL &&
      Math.abs(d[i + 1] - BG_G) <= BG_TOL &&
      Math.abs(d[i + 2] - BG_B) <= BG_TOL
    ) {
      d[i + 3] = 0;
    }
  }
}

// ─── Sprite-sheet backend ────────────────────────────────────────────────────

/**
 * Load a sprite-sheet PNG, key out the near-white background, and return the
 * processed sheet as a single OffscreenCanvas together with per-frame dimensions.
 *
 * We intentionally avoid slicing the sheet into individual ImageBitmaps because
 * createImageBitmap(offscreenCanvas) transfers the underlying bitmap in Chromium,
 * leaving the source canvas neutered and triggering the
 * "object is not, or is no longer, usable" DOMException.
 *
 * Instead, frames are clipped at draw time via the 9-argument ctx.drawImage() form.
 *
 * @param {string} url
 * @returns {Promise<{sheet: OffscreenCanvas, frameW: number, frameH: number}>}
 */
async function loadSheetFrames(url) {
  const blob = await fetch(url).then(r => {
    if (!r.ok) throw new Error(`HTTP ${r.status} loading ${url}`);
    return r.blob();
  });
  const img = await createImageBitmap(blob);

  const frameW = Math.floor(img.width  / COLS);
  const frameH = Math.floor(img.height / ROWS);

  // Draw the full sheet onto a single OffscreenCanvas so we can manipulate pixels
  const sheet = new OffscreenCanvas(img.width, img.height);
  const ctx   = sheet.getContext('2d');
  ctx.drawImage(img, 0, 0);

  // Key out near-white background in-place
  const raw = ctx.getImageData(0, 0, img.width, img.height);
  removeBackground(raw);
  ctx.putImageData(raw, 0, 0);

  // Free the source ImageBitmap — we no longer need it
  img.close();

  return { sheet, frameW, frameH };
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
  let frameW = 0, frameH = 0;

  await Promise.all(DIRECTIONS.map(dir => new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = () => {
      imgs[dir] = img;
      frameW    = Math.max(frameW, img.naturalWidth);
      frameH    = Math.max(frameH, img.naturalHeight);
      resolve();
    };
    img.onerror = () => reject(new Error(`Failed to load GIF: ${img.src}`));
    img.src = urls[dir];
  })));

  return { imgs, frameW, frameH };
}

// ─── Unified CritterSprite class ────────────────────────────────────────────

export class CritterSprite {
  /**
   * @param {'spritesheet'|'gifs'} type
   * @param {string|{forward:string,left:string,right:string,backward:string}} src
   *        For 'spritesheet': URL to the PNG.
   *        For 'gifs': object mapping direction → GIF URL.
   * @param {number} [fps]  Only relevant for sprite sheets.
   */
  constructor(type, src, fps = DEFAULT_FPS) {
    this.type = type;
    this._src  = src;
    this.fps   = fps;

    // Set after load()
    this.frameW = 0;
    this.frameH = 0;
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
        ? Object.fromEntries(DIRECTIONS.map(d => [d, `${base}/${entry.files[d]}`]))
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
      this._loadPromise = loadSheetFrames(this._src).then(({ sheet, frameW, frameH }) => {
        this._sheet = sheet;
        this.frameW = frameW;
        this.frameH = frameH;
        this._ready = true;
      });
    } else {
      // GIF: src is already a map of direction → absolute URL
      this._loadPromise = loadGifImgs(this._src).then(({ imgs, frameW, frameH }) => {
        this._imgs  = imgs;
        this.frameW = frameW;
        this.frameH = frameH;
        this._ready = true;
      });
    }

    return this._loadPromise;
  }

  /** True once load() has completed successfully. */
  get ready() { return this._ready; }

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
      const col = Math.floor((timestamp / 1000) * this.fps) % COLS;
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
   * @param {number} col  Frame column index (0-3).
   * @param {number} x
   * @param {number} y
   * @param {number} [size=64]
   */
  drawFrame(ctx, row, col, x, y, size = 64) {
    if (!this._ready) return;

    if (this.type === 'spritesheet') {
      this._drawSheetFrame(ctx, row % ROWS, col % COLS, x, y, size);
    } else {
      const dir = DIRECTIONS[row % ROWS];
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
    const w  = size;
    const h  = (this.frameH / this.frameW) * size;
    ctx.drawImage(this._sheet, sx, sy, this.frameW, this.frameH, x - w / 2, y - h / 2, w, h);
  }

  _drawImg(ctx, img, x, y, size) {
    const w = size;
    const h = (img.naturalHeight / img.naturalWidth) * size;
    ctx.drawImage(img, x - w / 2, y - h / 2, w, h);
  }
}
