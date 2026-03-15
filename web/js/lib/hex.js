/**
 * Hex geometry — axial coordinate system for flat-top hexagons.
 *
 * Mirrors python_server/src/gameserver/models/hex.py
 * Reference: https://www.redblobgames.com/grids/hexagons/
 */

// ── Directions (axial: dq, dr) ──────────────────────────────
export const DIRS = [
  [1, 0],   // E
  [1, -1],  // NE
  [0, -1],  // NW
  [-1, 0],  // W
  [-1, 1],  // SW
  [0, 1],   // SE
];

// ── Core functions ──────────────────────────────────────────

/** Create a hex key string for Maps/Sets. */
export function hexKey(q, r) {
  return `${q},${r}`;
}

/** Parse a hex key back to {q, r}. */
export function parseKey(key) {
  const [q, r] = key.split(',').map(Number);
  return { q, r };
}

/** Hex distance (cube metric). */
export function hexDistance(a, b) {
  const dq = Math.abs(a.q - b.q);
  const dr = Math.abs(a.r - b.r);
  const ds = Math.abs((-a.q - a.r) - (-b.q - b.r));
  return Math.max(dq, dr, ds);
}

/** Return 6 neighbor coordinates. */
export function hexNeighbors(q, r) {
  return DIRS.map(([dq, dr]) => ({ q: q + dq, r: r + dr }));
}

/** All hexes within radius (inclusive). */
export function hexDisk(cq, cr, radius) {
  const result = [];
  for (let dq = -radius; dq <= radius; dq++) {
    const rMin = Math.max(-radius, -dq - radius);
    const rMax = Math.min(radius, -dq + radius);
    for (let dr = rMin; dr <= rMax; dr++) {
      result.push({ q: cq + dq, r: cr + dr });
    }
  }
  return result;
}

/** All hexes at exactly radius distance. */
export function hexRing(cq, cr, radius) {
  if (radius <= 0) return [{ q: cq, r: cr }];
  const result = [];
  let q = cq - radius, r = cr + radius;
  for (const [dq, dr] of DIRS) {
    for (let i = 0; i < radius; i++) {
      result.push({ q, r });
      q += dq;
      r += dr;
    }
  }
  return result;
}

// ── Pixel conversion (flat-top hexagons) ────────────────────

/**
 * Convert axial (q, r) → pixel (x, y).
 * @param {number} q
 * @param {number} r
 * @param {number} size  Distance from center to corner (outer radius).
 * @returns {{x: number, y: number}}
 */
export function hexToPixel(q, r, size) {
  const x = size * (3 / 2 * q);
  const y = size * (Math.sqrt(3) / 2 * q + Math.sqrt(3) * r);
  return { x, y };
}

/**
 * Convert pixel (x, y) → axial (q, r), rounded to nearest hex.
 * @param {number} px
 * @param {number} py
 * @param {number} size
 * @returns {{q: number, r: number}}
 */
export function pixelToHex(px, py, size) {
  const q = (2 / 3 * px) / size;
  const r = (-1 / 3 * px + Math.sqrt(3) / 3 * py) / size;
  return cubeRound(q, r);
}

/**
 * 6 corner points for drawing a flat-top hex.
 * @param {number} cx  Center x
 * @param {number} cy  Center y
 * @param {number} size
 * @returns {Array<{x: number, y: number}>}
 */
export function hexCorners(cx, cy, size) {
  const corners = [];
  for (let i = 0; i < 6; i++) {
    const angle = (Math.PI / 3) * i;
    corners.push({
      x: cx + size * Math.cos(angle),
      y: cy + size * Math.sin(angle),
    });
  }
  return corners;
}

// ── Internal ────────────────────────────────────────────────

function cubeRound(fq, fr) {
  const fs = -fq - fr;
  let q = Math.round(fq);
  let r = Math.round(fr);
  let s = Math.round(fs);

  const qd = Math.abs(q - fq);
  const rd = Math.abs(r - fr);
  const sd = Math.abs(s - fs);

  if (qd > rd && qd > sd) q = -r - s;
  else if (rd > sd) r = -q - s;

  return { q, r };
}

// ── A* Pathfinding on hex grid ──────────────────────────────

/**
 * A* pathfinding on hex grid.
 *
 * @param {{q:number,r:number}} start
 * @param {{q:number,r:number}} goal
 * @param {(q:number, r:number) => boolean} isWalkable  Returns true if tile can be walked.
 * @returns {Array<{q:number,r:number}>|null}  Path from start to goal (inclusive), or null.
 */
export function hexAStar(start, goal, isWalkable) {
  const sk = hexKey(start.q, start.r);
  const gk = hexKey(goal.q, goal.r);

  const openSet = new Map();   // key → { q, r, g, f, parent }
  const closedSet = new Set();

  const h = (a) => hexDistance(a, goal);

  openSet.set(sk, { q: start.q, r: start.r, g: 0, f: h(start), parent: null });

  while (openSet.size > 0) {
    // Pick node with lowest f
    let bestKey = null, bestF = Infinity;
    for (const [key, node] of openSet) {
      if (node.f < bestF) { bestF = node.f; bestKey = key; }
    }

    const current = openSet.get(bestKey);
    if (bestKey === gk) {
      // Reconstruct path
      const path = [];
      let n = current;
      while (n) { path.unshift({ q: n.q, r: n.r }); n = n.parent; }
      return path;
    }

    openSet.delete(bestKey);
    closedSet.add(bestKey);

    for (const nb of hexNeighbors(current.q, current.r)) {
      const nk = hexKey(nb.q, nb.r);
      if (closedSet.has(nk)) continue;
      if (!isWalkable(nb.q, nb.r)) continue;

      const g = current.g + 1;

      const existing = openSet.get(nk);
      if (existing && g >= existing.g) continue;

      openSet.set(nk, {
        q: nb.q, r: nb.r,
        g,
        f: g + h(nb),
        parent: current,
      });
    }
  }

  return null; // No path found
}

// ── Critter position & world-space distance ─────────────────

const _SQRT3 = Math.sqrt(3);

/**
 * Interpolated continuous hex-coordinate of a critter on its path.
 *
 * path_progress is normalized [0.0, 1.0] over the whole path.
 * Returns sub-tile-precise floating-point hex coordinates — the critter
 * is between two hex centers, not snapped to a grid tile.
 *
 * @param {Array<{q:number, r:number}>} path  Ordered tile centers.
 * @param {number} path_progress              Normalized [0, 1].
 * @returns {{q: number, r: number}}
 */
export function critterHexPos(path, path_progress) {
  if (!path || path.length === 0) return { q: 0, r: 0 };
  if (path.length === 1) return { q: path[0].q, r: path[0].r };
  const maxIdx = path.length - 1;
  const floatIdx = path_progress * maxIdx;
  const idx = Math.min(Math.floor(floatIdx), maxIdx - 1);
  const frac = floatIdx - idx;
  const a = path[idx];
  const b = path[idx + 1];
  return { q: a.q + (b.q - a.q) * frac, r: a.r + (b.r - a.r) * frac };
}

/**
 * Euclidean distance between two positions in hex-world space.
 *
 * Works for any combination of integer tile coords and fractional critter
 * positions.  1 unit = distance between two adjacent tile centers
 * (flat-top hex layout, independent of canvas hexSize).
 *
 * Formula:  hexToPixel maps (q,r) → (1.5q, √3/2·q + √3·r) at size=1.
 * All six neighbors are exactly √3 pixels away → hex_dist = px_dist / √3.
 *
 * Examples:
 *   hexWorldDistance(0,0, 1,0)  === 1   (E neighbor)
 *   hexWorldDistance(0,0, 0,1)  === 1   (SE neighbor)
 *   hexWorldDistance(0,0, 2,0)  === 2
 *
 * @param {number} q1
 * @param {number} r1
 * @param {number} q2
 * @param {number} r2
 * @returns {number}  Distance in hex units.
 */
export function hexWorldDistance(q1, r1, q2, r2) {
  const dq = q2 - q1;
  const dr = r2 - r1;
  const dx = 1.5 * dq;
  const dy = 0.5 * _SQRT3 * dq + _SQRT3 * dr;
  return Math.sqrt(dx * dx + dy * dy) / _SQRT3;
}
