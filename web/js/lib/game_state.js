/** Shared game-phase state — imported by views without circular dependency. */

let _endRally = null;
let _seasonResetActive = false;

export function setEndRally(rally) {
  _endRally = rally;
}

export function setSeasonResetActive(value) {
  _seasonResetActive = value;
}

export function isSeasonResetActive() {
  return _seasonResetActive;
}

/** True when end-criterion was triggered AND the rally has expired — game is frozen. */
export function isGameFrozen() {
  if (_seasonResetActive) return true;
  if (!_endRally) return false;
  if (!_endRally.activated_at) return false;
  if (_endRally.active) return false;
  return true;
}
