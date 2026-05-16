"""Hex spawn placement — assigns global map positions to empires.

Placement algorithm:
  All hex tiles within `grid_radius` of the origin are ordered inside-out
  (ascending hex distance from origin, then clockwise within each ring).
  Each empire is assigned the next tile in this sequence that satisfies the
  minimum separation constraint (>= `min_separation` hex steps from every
  previously assigned tile).

Empire ordering: sorted by account `created_at` ascending (first registered
  empire gets index 0, i.e. the innermost available tile).

Coordinate system: axial (q, r), identical to the in-game hex system.
"""

from __future__ import annotations

import math
from typing import Sequence

from gameserver.models.hex import HexCoord


# ---------------------------------------------------------------------------
# Pure geometry helpers
# ---------------------------------------------------------------------------

def _hex_distance(aq: int, ar: int, bq: int, br: int) -> int:
    return (abs(aq - bq) + abs(aq + ar - bq - br) + abs(ar - br)) // 2


def _sort_key(q: int, r: int) -> tuple[int, float]:
    """Sort key: (ring_distance, clockwise_angle_from_top)."""
    dist = _hex_distance(0, 0, q, r)
    # Flat-top pixel coords for angle; top = angle 0, clockwise positive.
    px = 1.5 * q
    py = math.sqrt(3) / 2 * q + math.sqrt(3) * r
    angle = math.atan2(px, -py)  # clockwise from top
    return (dist, angle)


def build_candidate_list(grid_radius: int) -> list[HexCoord]:
    """Return all hexes within *grid_radius* sorted inside-out, clockwise."""
    hexes: list[tuple[int, int]] = []
    for q in range(-grid_radius, grid_radius + 1):
        for r in range(-grid_radius, grid_radius + 1):
            if _hex_distance(0, 0, q, r) <= grid_radius:
                hexes.append((q, r))
    hexes.sort(key=lambda h: _sort_key(h[0], h[1]))
    return [HexCoord(q, r) for q, r in hexes]


# ---------------------------------------------------------------------------
# Core placement function
# ---------------------------------------------------------------------------

def spawn_position_for_index(
    empire_index: int,
    *,
    grid_radius: int = 50,
    min_separation: int = 13,
) -> HexCoord:
    """Return the global hex spawn position for the empire at *empire_index*.

    Iterates from index 0 up to *empire_index*, placing each empire on the
    next valid candidate tile.  O(n * candidates) but n is small in practice.

    Args:
        empire_index: 0-based position in the creation-time-sorted empire list.
        grid_radius:  Radius of the global hex map in tiles.
        min_separation: Minimum hex distance between any two spawn points.

    Returns:
        HexCoord (axial) for the requested empire index.

    Raises:
        ValueError: If the grid cannot accommodate *empire_index + 1* empires.
    """
    candidates = build_candidate_list(grid_radius)
    placed: list[HexCoord] = []
    # Track which candidates are still available (parallel bool list)
    available = [True] * len(candidates)

    for _ in range(empire_index + 1):
        assigned: HexCoord | None = None
        for i, (cand, avail) in enumerate(zip(candidates, available)):
            if not avail:
                continue
            placed_here = cand
            available[i] = False
            # Mark neighbours within min_separation as taken
            for j, other in enumerate(candidates):
                if available[j] and _hex_distance(cand.q, cand.r, other.q, other.r) < min_separation:
                    available[j] = False
            assigned = placed_here
            placed.append(placed_here)
            break

        if assigned is None:
            raise ValueError(
                f"Grid (radius={grid_radius}, min_sep={min_separation}) "
                f"cannot place empire index {empire_index}: grid is full."
            )

    return placed[-1]


# ---------------------------------------------------------------------------
# Batch assignment: all empires sorted by creation time
# ---------------------------------------------------------------------------

def assign_spawn_positions(
    empire_uids_by_creation: Sequence[int],
    *,
    grid_radius: int = 50,
    min_separation: int = 13,
    empire_footprints: dict[int, int] | None = None,
) -> dict[int, HexCoord]:
    """Assign spawn positions to all empires in creation order.

    Args:
        empire_uids_by_creation: UIDs sorted oldest-first by account creation.
        grid_radius:  Radius of the global hex map.
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
    candidates = build_candidate_list(grid_radius)
    result: dict[int, HexCoord] = {}
    placed_footprints: list[tuple[HexCoord, int]] = []  # (coord, footprint_radius)

    fp = empire_footprints or {}

    for uid in empire_uids_by_creation:
        my_fp = fp.get(uid, 0)

        placed = False
        for cand in candidates:
            if cand in result.values():
                continue
            # Check against every placed empire: tiles must not overlap
            ok = True
            for placed_coord, placed_fp in placed_footprints:
                needed = max(my_fp + placed_fp + 1, min_separation)
                if _hex_distance(cand.q, cand.r, placed_coord.q, placed_coord.r) < needed:
                    ok = False
                    break
            if ok:
                result[uid] = cand
                placed_footprints.append((cand, my_fp))
                placed = True
                break

        if not placed:
            import logging
            logging.getLogger(__name__).warning(
                "Hex grid full: could not assign spawn position for uid=%d", uid
            )

    return result
