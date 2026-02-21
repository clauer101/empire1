/**
 * sprite.js — Sprite sheet animation module.
 *
 * Works with any sprite sheet that uses a 4×4 grid.
 * Frame dimensions are computed dynamically from the image size.
 * The near-white background (RGB ~252,252,252) is
 * stripped to transparency at load time using an OffscreenCanvas, so sprites
 * can be drawn directly onto the battle canvas without a white box.
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

/** Background color (near-white) tolerance for keying. */
const BG_R = 252;
const BG_G = 252;
const BG_B = 252;
const BG_TOLERANCE = 20;

/** Map direction name → row index. */
const DIRECTION_ROW = {
  forward:  0,
  left:     1,
  right:    2,
  backward: 3,
};

// ── Background removal ──────────────────────────────────────

/**
 * Remove near-white background pixels from an ImageData in-place,
 * setting their alpha to 0.
 * @param {ImageData} imageData
 */
function removeBackground(imageData) {
  const d = imageData.data;
  for (let i = 0; i < d.length; i += 4) {
    const r = d[i], g = d[i + 1], b = d[i + 2];
    if (
      Math.abs(r - BG_R) <= BG_TOLERANCE &&
      Math.abs(g - BG_G) <= BG_TOLERANCE &&
      Math.abs(b - BG_B) <= BG_TOLERANCE
    ) {
      d[i + 3] = 0; // fully transparent
    }
  }
}

/**
 * Load an image URL and return an object with frames and computed frame size.
 * Frame dimensions are derived from the image: frameW = img.width/COLS, frameH = img.height/ROWS.
 * @param {string} url
 * @returns {Promise<{frames: ImageBitmap[][], frameW: number, frameH: number}>}
 */
async function loadFrames(url) {
  // 1. Fetch the raw image
  const img = await createImageBitmap(
    await fetch(url).then(r => r.blob())
  );

  // 2. Compute per-frame dimensions from actual image size
  const frameW = Math.floor(img.width  / COLS);
  const frameH = Math.floor(img.height / ROWS);

  // 3. Draw full sheet onto OffscreenCanvas to access pixel data
  const oc = new OffscreenCanvas(img.width, img.height);
  const octx = oc.getContext('2d');
  octx.drawImage(img, 0, 0);
  const raw = octx.getImageData(0, 0, img.width, img.height);
  removeBackground(raw);

  // 4. Slice into individual frame ImageBitmaps (for fast canvas blitting)
  const frames = [];
  for (let row = 0; row < ROWS; row++) {
    frames[row] = [];
    for (let col = 0; col < COLS; col++) {
      const fc = new OffscreenCanvas(frameW, frameH);
      const fctx = fc.getContext('2d');
      const frameData = fctx.createImageData(frameW, frameH);
      for (let fy = 0; fy < frameH; fy++) {
        const srcY = row * frameH + fy;
        for (let fx = 0; fx < frameW; fx++) {
          const srcX = col * frameW + fx;
          const srcIdx = (srcY * img.width + srcX) * 4;
          const dstIdx = (fy * frameW + fx) * 4;
          frameData.data[dstIdx]     = raw.data[srcIdx];
          frameData.data[dstIdx + 1] = raw.data[srcIdx + 1];
          frameData.data[dstIdx + 2] = raw.data[srcIdx + 2];
          frameData.data[dstIdx + 3] = raw.data[srcIdx + 3];
        }
      }
      fctx.putImageData(frameData, 0, 0);
      frames[row][col] = await createImageBitmap(fc);
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
      this.frameW  = frameW;
      this.frameH  = frameH;
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
