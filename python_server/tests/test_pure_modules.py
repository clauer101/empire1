"""Tests for zero-coverage pure utility modules:
- util/hex_spawn_placement.py
- util/ai_battle_log.py
- loaders/string_loader.py
"""

from __future__ import annotations

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

from gameserver.loaders.string_loader import load_strings
from gameserver.models.hex import HexCoord
from gameserver.util.ai_battle_log import log_ai_battle
from gameserver.util.hex_spawn_placement import (
    _hex_distance,
    _sort_key,
    build_candidate_list,
    spawn_position_for_index,
    assign_spawn_positions,
)


class TestHexDistance:
    def test_same_cell(self):
        assert _hex_distance(0, 0, 0, 0) == 0

    def test_adjacent(self):
        assert _hex_distance(0, 0, 1, 0) == 1
        assert _hex_distance(0, 0, 0, 1) == 1

    def test_two_steps(self):
        assert _hex_distance(0, 0, 2, 0) == 2
        assert _hex_distance(0, 0, 1, 1) == 2

    def test_negative_coords(self):
        assert _hex_distance(0, 0, -1, 0) == 1
        assert _hex_distance(-2, 1, 1, -1) == 3


class TestSortKey:
    def test_origin_is_first(self):
        dist, angle = _sort_key(0, 0)
        assert dist == 0

    def test_ring_distance_matches_hex_distance(self):
        for q, r in [(1, 0), (0, 1), (-1, 1)]:
            dist, _ = _sort_key(q, r)
            assert dist == 1

    def test_angle_is_float(self):
        _, angle = _sort_key(1, 0)
        assert isinstance(angle, float)


class TestBuildCandidateList:
    def test_radius_0_single_cell(self):
        result = build_candidate_list(0)
        assert result == [HexCoord(0, 0)]

    def test_radius_1_has_seven_cells(self):
        result = build_candidate_list(1)
        assert len(result) == 7

    def test_radius_2_has_nineteen_cells(self):
        result = build_candidate_list(2)
        assert len(result) == 19

    def test_origin_is_first(self):
        result = build_candidate_list(3)
        assert result[0] == HexCoord(0, 0)

    def test_all_within_radius(self):
        radius = 3
        result = build_candidate_list(radius)
        for coord in result:
            assert _hex_distance(0, 0, coord.q, coord.r) <= radius

    def test_sorted_inside_out(self):
        result = build_candidate_list(3)
        dists = [_hex_distance(0, 0, c.q, c.r) for c in result]
        assert dists == sorted(dists)


class TestSpawnPositionForIndex:
    def test_index_0_is_origin(self):
        pos = spawn_position_for_index(0, grid_radius=5, min_separation=1)
        assert pos == HexCoord(0, 0)

    def test_index_1_is_adjacent(self):
        p0 = spawn_position_for_index(0, grid_radius=5, min_separation=1)
        p1 = spawn_position_for_index(1, grid_radius=5, min_separation=1)
        assert p0 != p1
        assert _hex_distance(p0.q, p0.r, p1.q, p1.r) >= 1

    def test_separation_enforced(self):
        sep = 4
        p0 = spawn_position_for_index(0, grid_radius=10, min_separation=sep)
        p1 = spawn_position_for_index(1, grid_radius=10, min_separation=sep)
        assert _hex_distance(p0.q, p0.r, p1.q, p1.r) >= sep

    def test_raises_when_grid_full(self):
        with pytest.raises(ValueError, match="Grid.*cannot place empire"):
            # radius=1 gives 7 tiles; with min_sep=2 can't place many empires
            for i in range(10):
                spawn_position_for_index(i, grid_radius=1, min_separation=2)

    def test_multiple_indices_unique(self):
        positions = [spawn_position_for_index(i, grid_radius=20, min_separation=3) for i in range(5)]
        assert len(set(positions)) == 5


class TestAssignSpawnPositions:
    def test_empty_list(self):
        result = assign_spawn_positions([], grid_radius=10, min_separation=3)
        assert result == {}

    def test_single_empire(self):
        result = assign_spawn_positions([42], grid_radius=10, min_separation=3)
        assert 42 in result
        assert isinstance(result[42], HexCoord)

    def test_multiple_empires_unique_positions(self):
        uids = [1, 2, 3, 4]
        result = assign_spawn_positions(uids, grid_radius=20, min_separation=3)
        assert set(result.keys()) == set(uids)
        positions = list(result.values())
        assert len(set(positions)) == 4

    def test_separation_respected(self):
        uids = [10, 20, 30]
        sep = 5
        result = assign_spawn_positions(uids, grid_radius=20, min_separation=sep)
        coords = list(result.values())
        for i, a in enumerate(coords):
            for b in coords[i + 1:]:
                assert _hex_distance(a.q, a.r, b.q, b.r) >= sep

    def test_with_footprints(self):
        uids = [1, 2]
        result = assign_spawn_positions(
            uids, grid_radius=20, min_separation=3,
            empire_footprints={1: 5, 2: 3}
        )
        assert set(result.keys()) == {1, 2}

    def test_grid_full_some_empires_skipped(self):
        # Very tight grid: only origin fits with large separation
        result = assign_spawn_positions(
            [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            grid_radius=1,
            min_separation=10,
        )
        # At least one empire should fail to be placed — grid is too small
        assert len(result) < 10


# ---------------------------------------------------------------------------
# ai_battle_log
# ---------------------------------------------------------------------------

def _make_mock_battle(defender_won: bool = False) -> MagicMock:
    battle = MagicMock()
    battle.bid = 99
    battle.elapsed_ms = 5000.0
    battle.critters_spawned = 10
    battle.critters_reached = 3
    battle.critters_killed = 7
    battle.defender_won = defender_won
    battle.critter_path = [MagicMock()] * 5

    defender = MagicMock()
    defender.name = "TestDefender"
    defender.max_life = 10.0
    defender.resources = {"life": 3.5}
    battle.defender = defender

    structure = MagicMock()
    structure.iid = "ARROW_TOWER"
    battle.structures = {1: structure}

    wave = MagicMock()
    wave.iid = "GOBLIN"
    wave.slots = 2
    army = MagicMock()
    army.waves = [wave]
    battle.armies = {1: army}

    return battle


def _make_mock_empire_service() -> MagicMock:
    svc = MagicMock()
    svc.get_current_era.return_value = "stone"

    item = MagicMock()
    item.costs = {"gold": 50.0}
    item.slots = 1
    svc._upgrades.get.return_value = item
    svc._item_era_index = {"ARROW_TOWER": 0, "GOBLIN": 0}

    return svc


class TestLogAiBattle:
    async def test_normal_case_calls_db(self):
        battle = _make_mock_battle()
        empire_svc = _make_mock_empire_service()
        db = AsyncMock()

        await log_ai_battle(battle, empire_svc, db, army_name="TestArmy")

        db.insert_ai_battle_log.assert_awaited_once()
        call_kwargs = db.insert_ai_battle_log.call_args
        assert call_kwargs.kwargs["bid"] == 99
        assert call_kwargs.kwargs["army_name"] == "TestArmy"
        assert call_kwargs.kwargs["result"] == "AI_WIN"

    async def test_defender_won_result(self):
        battle = _make_mock_battle(defender_won=True)
        empire_svc = _make_mock_empire_service()
        db = AsyncMock()

        await log_ai_battle(battle, empire_svc, db, army_name="AI")

        call_kwargs = db.insert_ai_battle_log.call_args
        assert call_kwargs.kwargs["result"] == "DEFENDER_WIN"

    async def test_none_defender_returns_early(self):
        battle = MagicMock()
        battle.defender = None
        db = AsyncMock()
        empire_svc = MagicMock()

        await log_ai_battle(battle, empire_svc, db, army_name="AI")

        db.insert_ai_battle_log.assert_not_called()

    async def test_exception_is_swallowed(self):
        battle = _make_mock_battle()
        empire_svc = _make_mock_empire_service()
        db = AsyncMock()
        db.insert_ai_battle_log.side_effect = RuntimeError("db down")

        # Should not raise
        await log_ai_battle(battle, empire_svc, db, army_name="AI")

    async def test_tower_with_unknown_item(self):
        battle = _make_mock_battle()
        empire_svc = _make_mock_empire_service()
        # Item not found — should handle gracefully
        empire_svc._upgrades.get.return_value = None
        db = AsyncMock()

        await log_ai_battle(battle, empire_svc, db, army_name="AI")

        db.insert_ai_battle_log.assert_awaited_once()


# ---------------------------------------------------------------------------
# string_loader
# ---------------------------------------------------------------------------

class TestLoadStrings:
    def test_loads_key_value_pairs(self, tmp_path: Path):
        f = tmp_path / "strings.yaml"
        f.write_text("hello: world\nfoo: bar\n")
        result = load_strings(f)
        assert result == {"hello": "world", "foo": "bar"}

    def test_empty_file_returns_empty_dict(self, tmp_path: Path):
        f = tmp_path / "empty.yaml"
        f.write_text("")
        result = load_strings(f)
        assert result == {}

    def test_values_are_strings(self, tmp_path: Path):
        f = tmp_path / "nums.yaml"
        f.write_text("count: 42\nprice: 3.14\n")
        result = load_strings(f)
        assert result["count"] == "42"
        assert result["price"] == "3.14"

    def test_accepts_path_string(self, tmp_path: Path):
        f = tmp_path / "s.yaml"
        f.write_text("a: b\n")
        result = load_strings(str(f))
        assert result == {"a": "b"}
