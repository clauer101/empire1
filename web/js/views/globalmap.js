import { rest } from '../rest.js';
import { state } from '../state.js';

// ── Constants ──────────────────────────────────────────────────────────────
const HEX = 18; // world hex radius (world units)

// ── Hex math (flat-top axial) — ported from tools/global-map.html ─────────
function hexToPixel(q, r, size) {
  return [size * 1.5 * q, size * (Math.sqrt(3) / 2 * q + Math.sqrt(3) * r)];
}
function pixelToHex(px, py, size) {
  const q = (2 / 3 * px) / size;
  const r = (-1 / 3 * px + Math.sqrt(3) / 3 * py) / size;
  return hexRound(q, r);
}
function hexRound(q, r) {
  const s = -q - r;
  let rq = Math.round(q), rr = Math.round(r), rs = Math.round(s);
  const dq = Math.abs(rq - q), dr = Math.abs(rr - r), ds = Math.abs(rs - s);
  if (dq > dr && dq > ds) rq = -rr - rs;
  else if (dr > ds) rr = -rq - rs;
  return [rq, rr];
}
function hexCorners(cx, cy, size) {
  const pts = [];
  for (let i = 0; i < 6; i++) {
    const a = Math.PI / 3 * i;
    pts.push([cx + size * Math.cos(a), cy + size * Math.sin(a)]);
  }
  return pts;
}

// ── Transform: world → canvas ──────────────────────────────────────────────
function w2c(wx, wy) {
  return [
    canvas.width  / 2 + (wx + view.panX) * view.scale,
    canvas.height / 2 + (wy + view.panY) * view.scale,
  ];
}

// ── Module state ───────────────────────────────────────────────────────────
let container, canvas, ctx;
let _unsub = [];
let empires  = []; // [{uid, name, isSelf, tiles:[{q,r,type}]}]
let tileImg  = null;
let tilePattern = null;
let bbox     = null;
let minScale = 0.05;
let maxScale = 4;
const view   = { scale: 1, panX: 0, panY: 0 };

// ── Viewport sizing (defense.js pattern) ──────────────────────────────────
function _fitCanvas() {
  const wrap = container.querySelector('#gm-wrap');
  if (!wrap) return;
  const top = Math.round(wrap.getBoundingClientRect().top);
  const appEl = document.getElementById('app') || document.body;
  const padBottom = parseFloat(getComputedStyle(appEl).paddingBottom) || 0;
  wrap.style.height = `calc(100dvh - ${top + padBottom}px)`;
  canvas.width  = wrap.clientWidth;
  canvas.height = wrap.clientHeight;
}

// ── Bbox + zoom limits ─────────────────────────────────────────────────────
function _computeBBox() {
  let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
  for (const e of empires) {
    for (const t of e.tiles) {
      const [x, y] = hexToPixel(t.q, t.r, HEX);
      minX = Math.min(minX, x); maxX = Math.max(maxX, x);
      minY = Math.min(minY, y); maxY = Math.max(maxY, y);
    }
  }
  // Pad by one hex radius on all sides
  minX -= HEX; maxX += HEX; minY -= HEX; maxY += HEX;
  bbox = {
    minX, maxX, minY, maxY,
    cx: (minX + maxX) / 2,
    cy: (minY + maxY) / 2,
    w:  maxX - minX,
    h:  maxY - minY,
  };
}

function _computeZoomLimits() {
  const PAD = HEX * 3;
  const bw  = bbox.w + PAD * 2;
  const bh  = bbox.h + PAD * 2;
  minScale = Math.min(canvas.width / bw, canvas.height / bh);
  // Cap so a single on-screen hex is ~50px radius (~100px wide) — tappable and readable
  maxScale = 50 / HEX;
  if (maxScale < minScale) maxScale = minScale; // degenerate single-empire case
}

function _fitView() {
  view.scale = minScale;
  view.panX  = -bbox.cx;
  view.panY  = -bbox.cy;
}

function _clampView() {
  view.scale = Math.max(minScale, Math.min(maxScale, view.scale));
}

// ── Viewport-bounded lazy loading ─────────────────────────────────────────
let _refetchTimer = null;
// Track the bounds already loaded so we only fetch when panning outside them.
let _loadedBounds = null; // { q0, r0, q1, r1 } or null

const PREFETCH_MARGIN = 20; // hex-cells of extra buffer around the viewport

/** Visible world-hex bounds for the current pan/zoom, padded by `margin`. */
function _visibleWorldBounds(margin = PREFETCH_MARGIN) {
  const W = canvas.width, H = canvas.height;
  let q0 = Infinity, r0 = Infinity, q1 = -Infinity, r1 = -Infinity;
  for (const [sx, sy] of [[0, 0], [W, 0], [0, H], [W, H]]) {
    const wx = (sx - W / 2) / view.scale - view.panX;
    const wy = (sy - H / 2) / view.scale - view.panY;
    const [q, r] = pixelToHex(wx, wy, HEX);
    q0 = Math.min(q0, q); q1 = Math.max(q1, q);
    r0 = Math.min(r0, r); r1 = Math.max(r1, r);
  }
  return {
    q0: Math.floor(q0) - margin, r0: Math.floor(r0) - margin,
    q1: Math.ceil(q1) + margin, r1: Math.ceil(r1) + margin,
  };
}

/** True when the current viewport (no extra margin) is fully inside already-loaded bounds. */
function _viewportCovered() {
  if (!_loadedBounds) return false;
  const vb = _visibleWorldBounds(0);
  return vb.q0 >= _loadedBounds.q0 && vb.q1 <= _loadedBounds.q1
      && vb.r0 >= _loadedBounds.r0 && vb.r1 <= _loadedBounds.r1;
}

/** Merge new empire data into the existing set (add/update, never remove). */
function _applyEmpires(data) {
  const selfUid = state.auth.uid;
  const incoming = (data.empires || [])
    .filter(e => e.tiles && e.tiles.length > 0)
    .map(e => ({
      uid: e.uid,
      name: e.name || `uid ${e.uid}`,
      isSelf: e.uid === selfUid,
      tiles: e.tiles,
    }));
  // Merge: replace existing entries by uid, append new ones.
  const byUid = new Map(empires.map(e => [e.uid, e]));
  for (const e of incoming) byUid.set(e.uid, e);
  empires = [...byUid.values()];
}

/** Debounced refetch — skipped when the viewport is already covered by loaded data. */
function _scheduleRefetch() {
  if (_refetchTimer) clearTimeout(_refetchTimer);
  _refetchTimer = setTimeout(async () => {
    _refetchTimer = null;
    if (_viewportCovered()) return; // nothing new to load
    const bounds = _visibleWorldBounds();
    try {
      _applyEmpires(await rest.getGlobalMap(bounds));
      _loadedBounds = _loadedBounds ? {
        q0: Math.min(_loadedBounds.q0, bounds.q0),
        r0: Math.min(_loadedBounds.r0, bounds.r0),
        q1: Math.max(_loadedBounds.q1, bounds.q1),
        r1: Math.max(_loadedBounds.r1, bounds.r1),
      } : { ...bounds };
      render();
    } catch { /* transient — keep last good frame */ }
  }, 250);
}

// ── Render ─────────────────────────────────────────────────────────────────
function render() {
  if (!canvas) return;
  const W = canvas.width, H = canvas.height;
  ctx.clearRect(0, 0, W, H);
  ctx.fillStyle = '#0d0d14';
  ctx.fillRect(0, 0, W, H);

  // Tiled grass4 background anchored to world origin
  if (tileImg) {
    const tilePx = 512 * view.scale; // tileWorldSize=512 at scale=1
    if (!tilePattern) tilePattern = ctx.createPattern(tileImg, 'repeat');
    const offX = ((W / 2 + view.panX * view.scale) % tilePx + tilePx) % tilePx;
    const offY = ((H / 2 + view.panY * view.scale) % tilePx + tilePx) % tilePx;
    ctx.save();
    ctx.globalAlpha = 0.4;
    tilePattern.setTransform(new DOMMatrix().translate(offX, offY).scale(tilePx / 512));
    ctx.fillStyle = tilePattern;
    ctx.fillRect(0, 0, W, H);
    ctx.globalAlpha = 1;
    ctx.restore();
  }

  if (!empires.length) return;

  const pxSz = HEX * view.scale;
  const YEL  = '255,213,79';
  const BLU  = '79,195,247';

  for (const e of empires) {
    const rgb = e.isSelf ? YEL : BLU;
    for (const t of e.tiles) {
      const [wx, wy] = hexToPixel(t.q, t.r, HEX);
      const [cx, cy] = w2c(wx, wy);
      // Cull tiles outside viewport
      if (cx < -pxSz || cx > W + pxSz || cy < -pxSz || cy > H + pxSz) continue;

      const isCastle = t.type === 'castle';
      const corners  = hexCorners(cx, cy, pxSz * 0.97);
      ctx.beginPath();
      ctx.moveTo(...corners[0]);
      for (let i = 1; i < 6; i++) ctx.lineTo(...corners[i]);
      ctx.closePath();

      ctx.fillStyle   = `rgba(${rgb},${isCastle ? 0.95 : 0.45})`;
      ctx.fill();
      ctx.strokeStyle = `rgba(${rgb},0.7)`;
      ctx.lineWidth   = isCastle ? 1.6 : 0.7;
      ctx.stroke();

      // Castle marker glyph
      if (isCastle && pxSz > 5) {
        ctx.fillStyle    = 'rgba(20,14,0,0.9)';
        ctx.font         = `bold ${Math.max(8, pxSz * 0.5)}px sans-serif`;
        ctx.textAlign    = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText('♜', cx, cy);
      }
    }
  }

  const statusEl = container.querySelector('#gm-status');
  if (statusEl) {
    statusEl.textContent =
      `empires: ${empires.length} | tiles: ${empires.reduce((s, e) => s + e.tiles.length, 0)}`;
  }
}

// ── Hit test + overlay ─────────────────────────────────────────────────────
function _hitTest(clientX, clientY) {
  const r  = canvas.getBoundingClientRect();
  const sx = clientX - r.left;
  const sy = clientY - r.top;
  const wx = (sx - canvas.width  / 2) / view.scale - view.panX;
  const wy = (sy - canvas.height / 2) / view.scale - view.panY;
  const [hq, hr] = pixelToHex(wx, wy, HEX);
  for (const e of empires) {
    const t = e.tiles.find(t => t.q === hq && t.r === hr);
    if (t) return { empire: e, tile: t, q: hq, r: hr };
  }
  return null;
}

function _showOverlay(hit) {
  const ov = container.querySelector('#gm-overlay');
  container.querySelector('#gm-overlay-body').innerHTML = `
    <div class="gm-row"><span>Empire</span><b>${hit.empire.name}</b></div>
    <div class="gm-row"><span>Owner</span><b>${hit.empire.isSelf ? 'You' : 'Enemy'}</b></div>
    <div class="gm-row"><span>Coords</span><b>q=${hit.q}, r=${hit.r}</b></div>
    <div class="gm-row"><span>Tile</span><b>${hit.tile.type}</b></div>`;
  ov.style.display = 'flex';
}

// ── Input handling (Pointer Events — mouse + touch) ────────────────────────
const _pointers = new Map();

function _attachInputs() {
  canvas.style.touchAction = 'none';

  // ── Pointer down ──
  const onPointerDown = (e) => {
    canvas.setPointerCapture(e.pointerId);
    _pointers.set(e.pointerId, {
      x: e.clientX, y: e.clientY,
      startX: e.clientX, startY: e.clientY,
      startT: Date.now(),
      panX: view.panX, panY: view.panY,
    });
    canvas.classList.add('dragging');
  };

  // ── Pointer move ──
  const onPointerMove = (e) => {
    if (!_pointers.has(e.pointerId)) return;
    const p = _pointers.get(e.pointerId);
    p.x = e.clientX;
    p.y = e.clientY;

    if (_pointers.size === 1) {
      // Single-pointer pan
      view.panX = p.panX + (e.clientX - p.startX) / view.scale;
      view.panY = p.panY + (e.clientY - p.startY) / view.scale;
      render();
      _scheduleRefetch();
    } else if (_pointers.size === 2) {
      // Two-finger pinch zoom
      const pts = [..._pointers.values()];
      const dx = pts[1].x - pts[0].x;
      const dy = pts[1].y - pts[0].y;
      const dist = Math.sqrt(dx * dx + dy * dy);
      if (p._prevDist) {
        const factor = dist / p._prevDist;
        const next   = Math.max(minScale, Math.min(maxScale, view.scale * factor));
        const eff    = next / view.scale;
        if (eff !== 1) {
          const mid = [(pts[0].x + pts[1].x) / 2, (pts[0].y + pts[1].y) / 2];
          const r   = canvas.getBoundingClientRect();
          const sx  = mid[0] - r.left - canvas.width  / 2;
          const sy  = mid[1] - r.top  - canvas.height / 2;
          view.panX -= sx / view.scale * (1 - 1 / eff);
          view.panY -= sy / view.scale * (1 - 1 / eff);
          view.scale = next;
          render();
          _scheduleRefetch();
        }
      }
      p._prevDist = dist;
    }
  };

  // ── Pointer up ──
  const onPointerUp = (e) => {
    const p = _pointers.get(e.pointerId);
    if (p) {
      const dx = e.clientX - p.startX;
      const dy = e.clientY - p.startY;
      const moved = Math.sqrt(dx * dx + dy * dy);
      const elapsed = Date.now() - p.startT;
      if (_pointers.size === 1 && moved < 5 && elapsed < 400) {
        // Tap → show overlay
        const hit = _hitTest(e.clientX, e.clientY);
        if (hit) _showOverlay(hit);
      }
    }
    _pointers.delete(e.pointerId);
    if (_pointers.size === 0) canvas.classList.remove('dragging');
  };

  // ── Wheel zoom ──
  const onWheel = (e) => {
    e.preventDefault();
    const factor = e.deltaY < 0 ? 1.12 : 1 / 1.12;
    const next   = Math.max(minScale, Math.min(maxScale, view.scale * factor));
    const eff    = next / view.scale;
    if (eff === 1) return;
    const r  = canvas.getBoundingClientRect();
    const sx = e.clientX - r.left - canvas.width  / 2;
    const sy = e.clientY - r.top  - canvas.height / 2;
    view.panX -= sx / view.scale * (1 - 1 / eff);
    view.panY -= sy / view.scale * (1 - 1 / eff);
    view.scale = next;
    render();
    _scheduleRefetch();
  };

  // ── Escape closes overlay ──
  const onKeyDown = (e) => {
    if (e.key === 'Escape') {
      const ov = container.querySelector('#gm-overlay');
      if (ov) ov.style.display = 'none';
    }
  };

  canvas.addEventListener('pointerdown',  onPointerDown);
  canvas.addEventListener('pointermove',  onPointerMove);
  canvas.addEventListener('pointerup',    onPointerUp);
  canvas.addEventListener('pointercancel',onPointerUp);
  canvas.addEventListener('wheel', onWheel, { passive: false });
  document.addEventListener('keydown', onKeyDown);

  _unsub.push(() => {
    canvas.removeEventListener('pointerdown',  onPointerDown);
    canvas.removeEventListener('pointermove',  onPointerMove);
    canvas.removeEventListener('pointerup',    onPointerUp);
    canvas.removeEventListener('pointercancel',onPointerUp);
    canvas.removeEventListener('wheel', onWheel);
    document.removeEventListener('keydown', onKeyDown);
  });
}

// ── View lifecycle ─────────────────────────────────────────────────────────
function init(el) {
  container = el;
  container.innerHTML = `
    <div id="gm-wrap">
      <canvas id="gm-canvas"></canvas>
      <div id="gm-status"></div>
      <div id="gm-error" style="display:none"></div>
      <div id="gm-overlay" class="gm-overlay" style="display:none">
        <div class="gm-overlay-card">
          <button class="gm-overlay-close">✕</button>
          <div id="gm-overlay-body"></div>
        </div>
      </div>
    </div>`;

  const ov = container.querySelector('#gm-overlay');
  ov.querySelector('.gm-overlay-close').addEventListener('click', () => {
    ov.style.display = 'none';
  });
  ov.addEventListener('click', (e) => {
    if (e.target === ov) ov.style.display = 'none';
  });

  canvas = container.querySelector('#gm-canvas');
  ctx    = canvas.getContext('2d');
}

async function enter() {
  _fitCanvas();

  const onResize = () => { _fitCanvas(); if (bbox) { _computeZoomLimits(); _clampView(); } render(); };
  window.addEventListener('resize', onResize);
  _unsub.push(() => window.removeEventListener('resize', onResize));

  // Load grass4 background tile
  const img = new Image();
  img.src = '/assets/sprites/maps/grass4.webp';
  img.onload = () => { tileImg = img; tilePattern = null; render(); };

  const errEl = container.querySelector('#gm-error');
  try {
    // First load is the full overview (no bounds) — mark everything as loaded.
    _applyEmpires(await rest.getGlobalMap());
    _loadedBounds = { q0: -Infinity, r0: -Infinity, q1: Infinity, r1: Infinity };
    if (empires.length) {
      _computeBBox();
      _computeZoomLimits();
      _fitView();
    }
    _attachInputs();
    render();
  } catch (err) {
    errEl.textContent = `Failed to load: ${err.message}`;
    errEl.style.display = 'block';
  }
}

function leave() {
  _unsub.forEach(fn => fn());
  _unsub = [];
  if (_refetchTimer) { clearTimeout(_refetchTimer); _refetchTimer = null; }
  _pointers.clear();
  empires       = [];
  _loadedBounds = null;
  tileImg     = null;
  tilePattern = null;
  bbox        = null;
  canvas.classList.remove('dragging');
  const ov = container?.querySelector('#gm-overlay');
  if (ov) ov.style.display = 'none';
}

export default { id: 'globalmap', title: 'Global Map', init, enter, leave };
