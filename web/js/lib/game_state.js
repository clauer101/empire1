/** Shared game-phase state — imported by views without circular dependency. */

let _endRally = null;

export function setEndRally(rally) {
  _endRally = rally;
}

/** True when end-criterion was triggered AND the rally has expired — game is frozen. */
export function isGameFrozen() {
  if (!_endRally) return false;
  if (!_endRally.activated_at) return false;
  if (_endRally.active) return false;
  return true;
}
