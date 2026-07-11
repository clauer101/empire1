"""Tests for the deterministic empire spawn spiral (models/hex.py:spiral_slot)
and the one-off migration script that rigidly shifts existing empires onto it."""
from __future__ import annotations

import sys
from pathlib import Path

from gameserver.models.hex import HexCoord, spiral_slot

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from migrate_spiral_spawns import migrate  # noqa: E402


def test_index_zero_is_origin() -> None:
    assert spiral_slot(0) == HexCoord(0, 0)


def test_ring_one_matches_hexcoord_ring() -> None:
    ring1 = HexCoord(0, 0).ring(1)
    assert len(ring1) == 6
    for i, expected in enumerate(ring1, start=1):
        assert spiral_slot(i) == expected


def test_ring_two_matches_hexcoord_ring() -> None:
    ring2 = HexCoord(0, 0).ring(2)
    assert len(ring2) == 12
    for i, expected in enumerate(ring2, start=7):
        assert spiral_slot(i) == expected


def test_ring_three_matches_hexcoord_ring() -> None:
    ring3 = HexCoord(0, 0).ring(3)
    assert len(ring3) == 18
    for i, expected in enumerate(ring3, start=19):
        assert spiral_slot(i) == expected


def test_large_index_falls_in_expected_ring() -> None:
    for n in (50, 100, 250):
        slot = spiral_slot(n)
        dist = HexCoord(0, 0).distance_to(slot)
        # Find k such that 1+3k(k-1) <= n <= 3k(k+1)
        k = 1
        while not (1 + 3 * k * (k - 1) <= n <= 3 * k * (k + 1)):
            k += 1
        assert dist == k


def test_all_indices_unique_up_to_300() -> None:
    seen = {spiral_slot(i) for i in range(300)}
    assert len(seen) == 300


def _tile(q: int, r: int, tile_type: str) -> dict:
    return {"q": q, "r": r, "type": tile_type}


def test_migrate_shifts_tiles_structures_and_battle_rigidly() -> None:
    state = {
        "empires": [
            {
                "uid": 5,
                "name": "Second",
                "hex_map": [_tile(999, 999, "castle"), _tile(999, 1000, "spawnpoint"),
                            _tile(1000, 999, "empty")],
                "structures": {"1": {"sid": 1, "iid": "ARROW_TOWER",
                                     "position": {"q": 1000, "r": 999}}},
            },
            {
                "uid": 2,
                "name": "First",
                "hex_map": [_tile(-500, -500, "castle"), _tile(-500, -499, "spawnpoint")],
                "structures": {},
            },
        ],
        "battles": [
            {
                "defender_uid": 5,
                "structures": {"1": {"position": {"q": 1000, "r": 999}}},
                "critter_path": [{"q": 999, "r": 1000}],
                "critters": {"7": {"path": [{"q": 999, "r": 1000}]}},
                "pending_shots": [{"origin": {"q": 1000, "r": 999}}],
            },
        ],
    }

    summary = migrate(state, spacing=10)

    # uid=2 (lower uid = processed first) gets index 0 -> origin
    first = next(e for e in state["empires"] if e["uid"] == 2)
    first_castle = next(t for t in first["hex_map"] if t["type"] == "castle")
    assert (first_castle["q"], first_castle["r"]) == (0, 0)

    # uid=5 gets index 1 -> first ring slot, scaled by spacing=10
    second = next(e for e in state["empires"] if e["uid"] == 5)
    second_castle = next(t for t in second["hex_map"] if t["type"] == "castle")
    expected = HexCoord(0, 0).ring(1)[0]
    assert (second_castle["q"], second_castle["r"]) == (expected.q * 10, expected.r * 10)

    # Relative layout within uid=5's own map is preserved exactly
    dq = second_castle["q"] - 999
    dr = second_castle["r"] - 999
    spawnpoint = next(t for t in second["hex_map"] if t["type"] == "spawnpoint")
    assert (spawnpoint["q"], spawnpoint["r"]) == (999 + dq, 1000 + dr)
    tower_pos = second["structures"]["1"]["position"]
    assert (tower_pos["q"], tower_pos["r"]) == (1000 + dq, 999 + dr)

    # The persisted battle where uid=5 is defender shifted by the same delta
    battle = state["battles"][0]
    assert battle["structures"]["1"]["position"] == {"q": 1000 + dq, "r": 999 + dr}
    assert battle["critter_path"][0] == {"q": 999 + dq, "r": 1000 + dr}
    assert battle["critters"]["7"]["path"][0] == {"q": 999 + dq, "r": 1000 + dr}
    assert battle["pending_shots"][0]["origin"] == {"q": 1000 + dq, "r": 999 + dr}

    assert len(summary) == 2
