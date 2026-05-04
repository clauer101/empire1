/**
 * sprite.js — Sprite sheet animation module.
 *
 * Works with any sprite sheet that uses a 4×4 grid.
 * Frame dimensions are computed dynamically from the image size.
 *
 * Animation rows
 *   0 → 'forward'   (walk towards viewer)
 *   1 → 'left'      (walk left)
 *   2 → 'right'     (walk right)
 *   3 → 'backward'  (walk away from viewer)
 *
 * Usage (battle.js integration):
 *   import { Sprite } from './lib/sprite.js';
 *
 *   const goblin = new Sprite('/tools/goblin.jpg');
 *   await goblin.load();
 *
 *   // inside requestAnimationFrame loop:
 *   goblin.draw(ctx, 'forward', timestamp, x, y, scale);
 *
 * The draw() call is stateless — the caller owns time & position.
 */

// ── Constants ───────────────────────────────────────────────

/** Number of columns / rows in the sheet (always 4×4). */
const COLS = 4;
const ROWS = 4;

/** Fallback frame dimensions (overridden per image at load time). */
const FRAME_W = 256;
const FRAME_H = 256;

/** Frames per second for playback. */
const DEFAULT_FPS = 8;

/** Map direction name → row index. */
const DIRECTION_ROW = {
  forward: 0,
  left: 1,
  right: 2,
  backward: 3,
};

/**
 * Load an image URL and return an object with frames and computed frame size.
 * Frame dimensions are derived from the image: frameW = img.width/COLS, frameH = img.height/ROWS.
 * @param {string} url
 * @returns {Promise<{frames: ImageBitmap[][], frameW: number, frameH: number}>}
 */
async function loadFrames(url) {
  // 1. Fetch the raw image
  const img = await createImageBitmap(await fetch(url).then((r) => r.blob()));

  // 2. Compute per-frame dimensions from actual image size
  const frameW = Math.floor(img.width / COLS);
  const frameH = Math.floor(img.height / ROWS);

  // 3. Slice into individual frame ImageBitmaps (for fast canvas blitting)
  const frames = [];
  for (let row = 0; row < ROWS; row++) {
    frames[row] = [];
    for (let col = 0; col < COLS; col++) {
      frames[row][col] = await createImageBitmap(img, col * frameW, row * frameH, frameW, frameH);
    }
  }
  return { frames, frameW, frameH };
}

// ── Sprite class ────────────────────────────────────────────

export class Sprite {
  /**
   * @param {string} url   Path to the sprite sheet image.
   * @param {number} fps   Animation speed in frames per second.
   */
  constructor(url, fps = DEFAULT_FPS) {
    this.url = url;
    this.fps = fps;
    /** @type {ImageBitmap[][]|null} */
    this._frames = null;
    /** Natural frame dimensions (set after load). */
    this.frameW = FRAME_W;
    this.frameH = FRAME_H;
    this._loading = false;
    this._loadPromise = null;
  }

  /**
   * Load and process the sprite sheet.
   * Safe to call multiple times — only loads once.
   * @returns {Promise<void>}
   */
  load() {
    if (this._loadPromise) return this._loadPromise;
    this._loading = true;
    this._loadPromise = loadFrames(this.url).then(({ frames, frameW, frameH }) => {
      this._frames = frames;
      this.frameW = frameW;
      this.frameH = frameH;
      this._loading = false;
    });
    return this._loadPromise;
  }

  /** True once the sheet has been loaded and processed. */
  get ready() {
    return this._frames !== null;
  }

  /**
   * Draw one animation frame onto a canvas context.
   * The frame is rendered at `size` width; height scales to preserve aspect ratio.
   *
   * @param {CanvasRenderingContext2D} ctx      Target canvas context.
   * @param {'forward'|'left'|'right'|'backward'} direction
   * @param {number} timestamp   Current time in ms (from requestAnimationFrame).
   * @param {number} x           Center X on canvas.
   * @param {number} y           Center Y on canvas.
   * @param {number} [size=64]   Rendered width in pixels; height preserves aspect ratio.
   */
  draw(ctx, direction, timestamp, x, y, size = 64) {
    if (!this._frames) return;

    const row = DIRECTION_ROW[direction] ?? 0;
    const col = Math.floor((timestamp / 1000) * this.fps) % COLS;
    const frame = this._frames[row][col];

    const w = size;
    const h = (this.frameH / this.frameW) * size;
    ctx.drawImage(frame, x - w / 2, y - h / 2, w, h);
  }

  /**
   * Draw a specific frame by row/col index (useful for previews).
   * The frame is rendered at `size` width; height scales to preserve aspect ratio.
   *
   * @param {CanvasRenderingContext2D} ctx
   * @param {number} row
   * @param {number} col
   * @param {number} x
   * @param {number} y
   * @param {number} [size=64]   Rendered width; height preserves natural aspect ratio.
   */
  drawFrame(ctx, row, col, x, y, size = 64) {
    if (!this._frames) return;
    const frame = this._frames[row % ROWS][col % COLS];
    const w = size;
    const h = (this.frameH / this.frameW) * size;
    ctx.drawImage(frame, x - w / 2, y - h / 2, w, h);
  }
}

/** Direction names in row order — useful for UIs. */
export const DIRECTIONS = ['forward', 'left', 'right', 'backward'];

/** Frame size constants for external callers. */
export { FRAME_W, FRAME_H, COLS, ROWS, DEFAULT_FPS };
