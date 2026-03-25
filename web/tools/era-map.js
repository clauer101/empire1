/**
 * era-map.js — shared era metadata loader for dev tools (fastapi_server.py, port 8000).
 *
 * Fetches /api/era-map once and caches it.  Response shape:
 *   {eras, info, critters, structures, buildings_knowledge}
 * where `eras` is the ordered list of German era display names (Steinzeit…Zukunft).
 *
 * Usage:
 *   <script src="era-map.js"></script>
 *   const em = await fetchEraMap();
 *   console.log(em.eras);          // ["Steinzeit", ...]
 *   console.log(em.critters);      // {Steinzeit: ["SLAVE", ...], ...}
 */

let _eraMapCache = null;

async function fetchEraMap() {
  if (_eraMapCache) return _eraMapCache;
  const r = await fetch('/api/era-map');
  if (!r.ok) throw new Error(`era-map: HTTP ${r.status}`);
  _eraMapCache = await r.json();
  return _eraMapCache;
}

window.fetchEraMap = fetchEraMap;
