"""Tests for the snail-shell spiral maze geometry and planner."""

from __future__ import annotations

from bot.defense_analysis import (
    HEX_DIRS, _hex_distance, bfs_path, hex_ring, next_spiral_action,
    spiral_is_wall,
)

START_TILES = {"0,0": "castle", "0,1": "spawnpoint", "1,0": "empty"}


# ── hex_ring geometry ────────────────────────────────────────────────────────

def test_hex_ring_sizes_and_distance():
    assert hex_ring(0) == [(0, 0)]
    for k in range(1, 8):
        ring = hex_ring(k)
        assert len(ring) == 6 * k
        assert all(_hex_distance(q, r) == k for q, r in ring)
        assert len(set(ring)) == 6 * k          # no duplicates


def test_hex_ring_tiles_are_contiguous():
    """Consecutive tiles in the ring walk are hex-adjacent (a closed loop)."""
    ring = hex_ring(3)
    dirset = set(HEX_DIRS)
    for i in range(len(ring)):
        a, b = ring[i], ring[(i + 1) % len(ring)]
        assert (b[0] - a[0], b[1] - a[1]) in dirset


# ── snail wall classification ────────────────────────────────────────────────

def test_castle_is_never_a_wall():
    assert spiral_is_wall(0, 0) is False


def test_spiral_wall_is_deterministic_and_seed_varies():
    sample = [(q, r) for q in range(-6, 7) for r in range(-6, 7)
              if 0 < _hex_distance(q, r) <= 6]
    a = {t for t in sample if spiral_is_wall(*t, 0)}
    a2 = {t for t in sample if spiral_is_wall(*t, 0)}
    b = {t for t in sample if spiral_is_wall(*t, 137)}
    assert a == a2                # deterministic
    assert a != b                 # seed rotates the coil
    assert 0 < len(a) < len(sample)   # both walls and corridors exist


# ── next_spiral_action build sequence ────────────────────────────────────────

def _play(tiles, *, seed, steps):
    """Drive next_spiral_action like the planner: one action per cycle."""
    tiles = dict(tiles)
    log = []
    for _ in range(steps):
        action = next_spiral_action(tiles, seed=seed)
        if action is None:
            break
        q, r, kind = action["q"], action["r"], action["kind"]
        key = f"{q},{r}"
        if kind == "buy":
            tiles[key] = "empty"
        elif kind == "spawn":
            old = next((k for k, v in tiles.items() if v == "spawnpoint"), None)
            if old:
                tiles[old] = "empty"
            tiles[key] = "spawnpoint"
        else:  # tower
            tiles[key] = "TOWER"
        log.append(action)
        assert bfs_path(tiles) is not None, f"path severed after {action}"
    return tiles, log


def test_snail_grows_places_towers_and_keeps_path_valid():
    tiles, log = _play(START_TILES, seed=0, steps=800)
    assert any(a["kind"] == "buy" for a in log)
    assert any(a["kind"] == "tower" for a in log)
    assert any(a["kind"] == "spawn" for a in log)
    assert bfs_path(tiles) is not None


def test_path_is_long_snail_maximizes_it():
    """A snail coil should force a long spawn→castle path."""
    tiles, _ = _play(START_TILES, seed=0, steps=800)
    assert len(bfs_path(tiles)) >= 30


def test_tower_first_priority():
    """A 'buy' is only emitted when no empty-triangle tile can be toweled."""
    from bot.defense_analysis import _empty_triangle_tiles
    tiles = dict(START_TILES)
    for _ in range(800):
        action = next_spiral_action(tiles, seed=0)
        if action is None:
            break
        if action["kind"] == "buy":
            # No tile of any empty triangle may be placeable without severing.
            placeable = []
            for q, r in _empty_triangle_tiles(tiles):
                sim = dict(tiles)
                sim[f"{q},{r}"] = "blocked"
                if bfs_path(sim) is not None:
                    placeable.append((q, r))
            assert not placeable, f"bought while towers placeable: {placeable}"
        # apply
        q, r, kind = action["q"], action["r"], action["kind"]
        key = f"{q},{r}"
        if kind == "buy":
            tiles[key] = "empty"
        elif kind == "spawn":
            old = next((kk for kk, vv in tiles.items() if vv == "spawnpoint"), None)
            if old:
                tiles[old] = "empty"
            tiles[key] = "spawnpoint"
        else:
            tiles[key] = "TOWER"


def test_snail_terminates():
    tiles, _ = _play(START_TILES, seed=0, steps=4000)
    assert next_spiral_action(tiles, seed=0) is None
