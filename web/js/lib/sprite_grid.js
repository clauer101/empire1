/**
 * sprite_grid.js — Sprite-sheet grid detection.
 *
 * Every sheet has 4 rows (forward, left, right, backward), but the number of
 * frames per row varies: the classic layout has 4 columns, newer sheets have 8.
 * The column count is detected from the pixels: a sheet has N columns when the
 * vertical seams between N equal-width frames are (almost) pure background.
 * Frame aspect ratios differ between sheets (square, 2:3, landscape), so the
 * image size alone cannot tell the layouts apart.
 */

/** Rows per sheet — one per direction. */
const SHEET_ROWS = 4;

/** Column count used when no other layout is detected. */
const DEFAULT_COLS = 4;

/** Alternative column counts, checked in order before falling back to DEFAULT_COLS. */
const CANDIDATE_COLS = [8];

/** Max share of foreground pixels on a seam that still counts as a frame border. */
const SEAM_MAX_FOREGROUND = 0.02;

/**
 * Detect the frame grid of a sprite sheet.
 *
 * @param {ImageBitmap|HTMLImageElement|HTMLCanvasElement|OffscreenCanvas} img  Loaded sheet.
 * @returns {{cols: number, rows: number, frameW: number, frameH: number}}
 */
export function detectSheetGrid(img) {
  const w = img.naturalWidth || img.width;
  const h = img.naturalHeight || img.height;
  const cols = _detectCols(img, w, h);
  return {
    cols,
    rows: SHEET_ROWS,
    frameW: Math.floor(w / cols),
    frameH: Math.floor(h / SHEET_ROWS),
  };
}

/**
 * Column to show at `timestamp`. `fps` is defined for a DEFAULT_COLS-frame cycle;
 * sheets with more frames play proportionally faster so one walk cycle always
 * takes the same time.
 *
 * @param {number} timestamp  Current time in ms.
 * @param {number} fps
 * @param {number} cols       Frames per row of the sheet.
 * @returns {number}
 */
export function frameIndex(timestamp, fps, cols) {
  return Math.floor((timestamp / 1000) * fps * (cols / DEFAULT_COLS)) % cols;
}

function _detectCols(img, w, h) {
  const canvas = new OffscreenCanvas(w, h);
  const ctx = canvas.getContext('2d', { willReadFrequently: true });
  ctx.drawImage(img, 0, 0);
  const bg = ctx.getImageData(0, 0, 1, 1).data;
  const isBackground = (d, i) =>
    bg[3] < 128
      ? d[i + 3] < 32
      : d[i + 3] >= 128 &&
        Math.abs(d[i] - bg[0]) < 40 &&
        Math.abs(d[i + 1] - bg[1]) < 40 &&
        Math.abs(d[i + 2] - bg[2]) < 40;

  const seamIsClear = (x) => {
    const d = ctx.getImageData(x, 0, 1, h).data;
    let foreground = 0;
    for (let i = 0; i < d.length; i += 4) if (!isBackground(d, i)) foreground++;
    return foreground <= h * SEAM_MAX_FOREGROUND;
  };

  for (const n of CANDIDATE_COLS) {
    let clear = true;
    for (let k = 1; k < n && clear; k++) clear = seamIsClear(Math.round((k * w) / n));
    if (clear) return n;
  }
  return DEFAULT_COLS;
}
