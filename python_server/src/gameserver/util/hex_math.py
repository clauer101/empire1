"""Hex math utilities — geometry functions for hexagonal grids.

All functions operate on HexCoord (axial coordinates).
Reference: https://www.redblobgames.com/grids/hexagons/
"""

from __future__ import annotations

from gameserver.models.hex import HexCoord


def hex_distance(a: HexCoord, b: HexCoord) -> int:
    """Compute the hex grid distance between two coordinates."""
    return a.distance_to(b)


def hex_linedraw(a: HexCoord, b: HexCoord) -> list[HexCoord]:
    """Draw a line between two hex coordinates using linear interpolation.

    Returns a list of hex coordinates from a to b (inclusive).
    Uses cube coordinate interpolation with rounding.
    """
    n = a.distance_to(b)
    if n == 0:
        return [a]

    results: list[HexCoord] = []
    for i in range(n + 1):
        t = i / n
        # Interpolate in cube space
        fq = a.q + (b.q - a.q) * t
        fr = a.r + (b.r - a.r) * t
        fs = a.s + (b.s - a.s) * t
        results.append(_cube_round(fq, fr, fs))
    return results


def hex_ring(center: HexCoord, radius: int) -> list[HexCoord]:
    """Return all hexes at exactly `radius` distance from center."""
    return center.ring(radius)


def hex_disk(center: HexCoord, radius: int) -> set[HexCoord]:
    """Return all hexes within `radius` distance from center (inclusive)."""
    return center.disk(radius)


def hex_neighbors(coord: HexCoord) -> list[HexCoord]:
    """Return the 6 neighbors of a hex coordinate."""
    return coord.neighbors()


def _cube_round(fq: float, fr: float, fs: float) -> HexCoord:
    """Round fractional cube coordinates to the nearest hex."""
    q = round(fq)
    r = round(fr)
    s = round(fs)

    q_diff = abs(q - fq)
    r_diff = abs(r - fr)
    s_diff = abs(s - fs)

    if q_diff > r_diff and q_diff > s_diff:
        q = -r - s
    elif r_diff > s_diff:
        r = -q - s
    # else: s = -q - r (implicit, not stored)

    return HexCoord(q, r)
