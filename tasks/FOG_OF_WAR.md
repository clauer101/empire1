# Fog of War — Neighbor Tile Visibility

## What Was Implemented

### Backend: `/api/map/neighbors`
New endpoint in `python_server/src/gameserver/network/routers/empire.py`.

**Algorithm:**
1. Find all border tiles — own tiles that have at least one non-own neighbor
2. BFS outward from border tiles for `neighbor_fog_radius` steps, excluding own tiles
3. Build a `tile_owner` lookup: for each other empire, translate their hex coords into defender-local coordinates
4. Return `{q, r, uid}` for every visible tile — `uid` is non-null if the tile belongs to another empire

**Config:** `neighbor_fog_radius` in `python_server/config/game.yaml` (currently 1).

### Frontend: `hex_grid.js`

**`setNeighborTiles(neighborTiles)`** — stores neighbor tiles as `Map<"q,r", {uid}>` and marks base layer dirty.

**Bounding box** includes neighbor tile coordinates so the base canvas is sized large enough to contain them.

**Pass 1b** in `_renderBase()` renders two groups using `Path2D`:
- **Fog tiles** (`uid == null`): map bitmap at 45% alpha + dark overlay `rgba(10,10,20,0.65)`
- **Enemy tiles** (`uid != null`): map bitmap at 85% alpha + red overlay `rgba(210,30,30,0.55)` + bright red stroke

**Call sites:** `defense.js` (hex editor) and `defense/battle_ui.js` (battle view) both call `rest.getMapNeighbors()` after `grid.fromJSON()`.

---

## Performance Optimizations Done

### 1. Batch Path2D instead of per-tile clip
**Problem:** Original implementation did `save() → clip() → drawImage() → fill() → restore()` for every single tile. At radius 10 with ~300 tiles that means 300 expensive GPU clip+drawImage operations per render frame.

**Fix:** All fog tiles are combined into one `Path2D`, all enemy tiles into another. Then `clip()` + `drawImage()` runs exactly **twice** regardless of tile count.

### 2. Base canvas rendered at zoom=1
**Problem:** `_renderBase()` was triggered on every zoom change (`_baseCachedZoom !== this.zoom`). The base canvas was sized at `worldW * zoom` pixels — re-rendering hundreds of tiles on every pinch-zoom step caused visible lag on mobile.

**Fix:** Base canvas is now rendered at zoom=1 and cached until tiles change. In `_render()`, the base canvas is drawn with `drawImage(..., width * zoom/dpr, height * zoom/dpr)` — a single GPU blit operation that scales the pre-rendered image to the current zoom. `_renderBase()` only runs when `_baseCached` is false (tile changes), not on zoom.

---

## Scaling Problem at 1000 Empires / Radius 500

At these dimensions the current architecture breaks down at multiple layers:

### Backend — O(empires × radius²)
- BFS at radius 500 generates ~750,000 hex tiles per request
- `tile_owner` dict is rebuilt from scratch on every call by iterating all empires × all their tiles
- At 1000 empires × 100 tiles each = 100,000 iterations per request, per user

### Network
- JSON response with 750,000 `{q, r, uid}` objects ≈ 30–50 MB per response
- Unacceptable for mobile

### Frontend
- `Path2D` with 750,000 `moveTo/lineTo/closePath` sequences takes hundreds of ms to construct
- Base canvas bounding box at radius 500 ≈ 40,000 × 40,000 px at hexSize=40 → ~6 GB canvas memory

---

## Solution Approaches for Large Scale

### 1. Viewport-culling (most impactful)
Only return tiles that fall within the client's current viewport. Client sends its visible q/r bounds with the request. Backend filters BFS results to that rectangle before returning. Reduces payload from 750k to ~hundreds of tiles regardless of radius.

### 2. Incremental/delta updates
Cache the neighbor tile set server-side per empire. On first load send the full set; on subsequent requests send only added/removed tiles. Works well since empires expand slowly.

### 3. Tile region compression (RLE)
Instead of individual `{q, r}` coordinates, encode runs of tiles along hex rows. A contiguous fog region of 500 tiles in a row becomes one `{q_start, r, length, uid}` entry. Reduces payload by 10–50×.

### 4. Pre-built spatial index
Replace the per-request `tile_owner` loop with a shared spatial hash map (`{q,r} → uid`) maintained incrementally as empires expand/shrink. Lookup becomes O(1) per tile instead of O(empires × tiles).

### 5. Separate fog layer canvas
Instead of including fog tiles in the base canvas (which forces a full re-render when they change), render fog tiles to a dedicated offscreen canvas. The fog layer can be re-rendered independently without invalidating the tile layer, and can be re-used across zoom levels by scaling it the same way as the base canvas.
