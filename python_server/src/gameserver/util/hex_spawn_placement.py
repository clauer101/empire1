"""Hex spawn placement — assigns global map positions to empires.

Placement algorithm:
  Hex tiles are enumerated ring by ring outward from the origin (ring 0 = origin,
  ring 1 = the 6 immediate neighbours, etc.).  Each empire is assigned the next
  tile in this inside-out, clockwise sequence that satisfies the minimum
  separation constraint (>= `min_separation` hex steps from every previously
  assigned tile).  The grid is unbounded — rings are generated on demand so any
  number of empires can be placed.

Empire ordering: sorted by account `created_at` ascending (first registered
  empire gets index 0, i.e. the origin tile).

Coordinate system: axial (q, r), identical to the in-game hex system.
"""

from __future__ import annotations

import math
from typing import Generator, Sequence

from gameserver.models.hex import HexCoord


# ---------------------------------------------------------------------------
# Pure geometry helpers
# ---------------------------------------------------------------------------

def _hex_distance(aq: int, ar: int, bq: int, br: int) -> int:
    return (abs(aq - bq) + abs(aq + ar - bq - br) + abs(ar - br)) // 2


def _ring(radius: int) -> list[tuple[int, int]]:
    """Return all hex tiles at exactly *radius* steps from origin, clockwise."""
    if radius == 0:
        return [(0, 0)]
    # Standard hex ring: start at (radius, -radius) [top-right], walk 6 sides.
    # Each side moves radius steps in one of the 6 cube directions.
    cube_directions = [(-1, 0), (-1, 1), (0, 1), (1, 0), (1, -1), (0, -1)]
    q, r = radius, -radius
    tiles: list[tuple[int, int]] = []
    for dq, dr in cube_directions:
        for _ in range(radius):
            tiles.append((q, r))
            q += dq
            r += dr
    # Sort clockwise from top using angle
    def _angle(qr: tuple[int, int]) -> float:
        px = 1.5 * qr[0]
        py = math.sqrt(3) / 2 * qr[0] + math.sqrt(3) * qr[1]
        return math.atan2(px, -py)
    tiles.sort(key=_angle)
    return tiles


def _hex_candidates() -> Generator[HexCoord, None, None]:
    """Yield hex tiles ring by ring, inside-out, clockwise — unbounded."""
    ring = 0
    while True:
        for q, r in _ring(ring):
            yield HexCoord(q, r)
        ring += 1


def build_candidate_list(grid_radius: int) -> list[HexCoord]:
    """Return all hexes within *grid_radius* sorted inside-out, clockwise."""
    tiles: list[HexCoord] = []
    for ring in range(grid_radius + 1):
        tiles.extend(HexCoord(q, r) for q, r in _ring(ring))
    return tiles


# ---------------------------------------------------------------------------
# Core placement function
# ---------------------------------------------------------------------------

def spawn_position_for_index(
    empire_index: int,
    *,
    min_separation: int = 13,
) -> HexCoord:
    """Return the global hex spawn position for the empire at *empire_index*.

    Args:
        empire_index: 0-based position in the creation-time-sorted empire list.
        min_separation: Minimum hex distance between any two spawn points.

    Returns:
        HexCoord (axial) for the requested empire index.
    """
    placed: list[HexCoord] = []
    placed_count = 0

    for cand in _hex_candidates():
        ok = all(
            _hex_distance(cand.q, cand.r, p.q, p.r) >= min_separation
            for p in placed
        )
        if ok:
            if placed_count == empire_index:
                return cand
            placed.append(cand)
            placed_count += 1

    raise RuntimeError("unreachable")  # generator is infinite


# ---------------------------------------------------------------------------
# Batch assignment: all empires sorted by creation time
# ---------------------------------------------------------------------------

def assign_spawn_positions(
    empire_uids_by_creation: Sequence[int],
    *,
    min_separation: int = 13,
    empire_footprints: dict[int, int] | None = None,
) -> dict[int, HexCoord]:
    """Assign spawn positions to all empires in creation order.

    The grid grows outward without bound — any number of empires can be placed.

    Args:
        empire_uids_by_creation: UIDs sorted oldest-first by account creation.
        min_separation: Minimum hex distance between castle positions when no
            footprint data is available.
        empire_footprints: Optional dict uid → max tile radius from castle.
            When provided, the exclusion zone between two empires A and B is
            ``footprint_A + footprint_B + 1`` so their actual tiles never
            overlap.  Falls back to ``min_separation`` for empires without
            footprint data.

    Returns:
        Dict mapping uid → HexCoord.
    """
    result: dict[int, HexCoord] = {}
    placed_footprints: list[tuple[HexCoord, int]] = []

    fp = empire_footprints or {}

    for uid in empire_uids_by_creation:
        my_fp = fp.get(uid, 0)
        placed_coords = {c for c, _ in placed_footprints}

        for cand in _hex_candidates():
            if cand in placed_coords:
                continue
            ok = all(
                _hex_distance(cand.q, cand.r, coord.q, coord.r) >= max(my_fp + pfp + 1, min_separation)
                for coord, pfp in placed_footprints
            )
            if ok:
                result[uid] = cand
                placed_footprints.append((cand, my_fp))
                break

    return result
