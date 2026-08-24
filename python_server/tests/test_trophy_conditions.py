"""Unit tests for TrophyService._check_condition.

Each condition type gets at least one passing and one failing test so we know
the logic is correct in both directions.

TrophyService is exercised at the _check_condition level (synchronous) to keep
tests fast — no real DB required.  The async check_and_award path is covered by
a separate integration test at the bottom.
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from gameserver.engine.trophy_service import TrophyService
from gameserver.models.empire import Empire
from gameserver.models.items import ItemDetails, ItemType


# ── Helpers ────────────────────────────────────────────────────────────────────

def _svc(empire_service: "object | None" = None) -> TrophyService:
    """Build a TrophyService with no real DB or upgrade_provider."""
    svc = TrophyService.__new__(TrophyService)
    svc._database = MagicMock()
    svc._upgrade_provider = MagicMock()
    svc._upgrade_provider.items = {}
    svc._empire_service = empire_service
    return svc


def _empire(uid: int = 1, *, hex_map: dict | None = None, trophies: dict | None = None,
            ruler_xp: float = 0.0) -> Empire:
    e = Empire(uid=uid, name=f"E{uid}")
    if hex_map is not None:
        e.hex_map = hex_map
    if trophies is not None:
        e.trophies = trophies
    if ruler_xp and e.ruler is not None:
        e.ruler.xp = ruler_xp
    return e


def _cond(ctype: str, threshold: "int | float | None" = None, **kwargs: object) -> dict:
    c: dict = {"type": ctype}
    if threshold is not None:
        c["threshold"] = threshold
    c.update(kwargs)
    return c


def _check(svc: TrophyService, condition: dict, stats: dict,
           empire: "Empire | None" = None, era_firsts: "dict | None" = None) -> bool:
    return svc._check_condition(condition, stats, empire, era_firsts)


def _progress(svc: TrophyService, condition: dict, stats: dict,
              empire: "Empire | None" = None, era_firsts: "dict | None" = None) -> tuple[float, float]:
    return svc._condition_progress(condition, stats, empire, era_firsts)


# ── Legacy combined counters ───────────────────────────────────────────────────

class TestDefenseWon:
    def test_combined_passes(self):
        svc = _svc()
        stats = {"defense_won_human": 3, "defense_won_ai": 0}
        assert _check(svc, _cond("defense_won", 3), stats)

    def test_combined_sums_ai_and_human(self):
        svc = _svc()
        stats = {"defense_won_human": 1, "defense_won_ai": 2}
        assert _check(svc, _cond("defense_won", 3), stats)

    def test_combined_fails(self):
        svc = _svc()
        stats = {"defense_won_human": 1, "defense_won_ai": 0}
        assert not _check(svc, _cond("defense_won", 3), stats)

    def test_missing_keys(self):
        svc = _svc()
        assert not _check(svc, _cond("defense_won", 1), {})


class TestAttacksWon:
    def test_passes(self):
        svc = _svc()
        stats = {"attacks_won_human": 5, "attacks_won_ai": 0}
        assert _check(svc, _cond("attacks_won", 5), stats)

    def test_sums_ai_and_human(self):
        svc = _svc()
        stats = {"attacks_won_human": 2, "attacks_won_ai": 3}
        assert _check(svc, _cond("attacks_won", 5), stats)

    def test_fails(self):
        svc = _svc()
        stats = {"attacks_won_human": 4, "attacks_won_ai": 0}
        assert not _check(svc, _cond("attacks_won", 5), stats)


class TestCrittersKilled:
    def test_passes(self):
        svc = _svc()
        assert _check(svc, _cond("critters_killed", 1000), {"critters_killed": 1000})

    def test_fails(self):
        svc = _svc()
        assert not _check(svc, _cond("critters_killed", 1000), {"critters_killed": 999})


class TestHexesOwned:
    def test_passes(self):
        svc = _svc()
        empire = _empire(hex_map={str(i): "path" for i in range(20)})
        assert _check(svc, _cond("hexes_owned", 20), {}, empire)

    def test_fails(self):
        svc = _svc()
        empire = _empire(hex_map={str(i): "path" for i in range(19)})
        assert not _check(svc, _cond("hexes_owned", 20), {}, empire)

    def test_no_empire_returns_false(self):
        svc = _svc()
        assert not _check(svc, _cond("hexes_owned", 1), {}, None)


# ── 1 HP defense win (counter) ────────────────────────────────────────────────

class TestOneHpDefenseWin:
    def test_passes_at_threshold(self):
        svc = _svc()
        assert _check(svc, _cond("one_hp_def_wins", 1), {"one_hp_def_wins": 1})

    def test_passes_above_threshold(self):
        svc = _svc()
        assert _check(svc, _cond("one_hp_def_wins", 1), {"one_hp_def_wins": 3})

    def test_fails_below_threshold(self):
        svc = _svc()
        assert not _check(svc, _cond("one_hp_def_wins", 2), {"one_hp_def_wins": 1})

    def test_fails_when_column_missing(self):
        svc = _svc()
        assert not _check(svc, _cond("one_hp_def_wins", 1), {})


# ── Per-type win/loss (direct stat columns) ────────────────────────────────────

class TestDirectStatConditions:
    """All condition types that map directly to an empire_stats column."""

    @pytest.mark.parametrize("ctype,col,val,threshold,expect", [
        ("defense_won_ai",    "defense_won_ai",    5,   5,   True),
        ("defense_won_ai",    "defense_won_ai",    4,   5,   False),
        ("defense_won_human", "defense_won_human", 10,  10,  True),
        ("defense_won_human", "defense_won_human", 9,   10,  False),
        ("attacks_won_ai",    "attacks_won_ai",    5,   5,   True),
        ("attacks_won_ai",    "attacks_won_ai",    4,   5,   False),
        ("attacks_won_human", "attacks_won_human", 15,  15,  True),
        ("attacks_won_human", "attacks_won_human", 14,  15,  False),
        ("artifacts_stolen",  "artifacts_stolen",  5,   5,   True),
        ("artifacts_stolen",  "artifacts_stolen",  4,   5,   False),
        ("spies_sent",        "spies_sent",        10,  10,  True),
        ("spies_sent",        "spies_sent",        9,   10,  False),
        ("culture_won",       "culture_won",       500, 500, True),
        ("culture_won",       "culture_won",       499, 500, False),
        ("culture_stolen",    "culture_stolen",    500, 500, True),
        ("culture_stolen",    "culture_stolen",    499, 500, False),
        ("research_won",      "research_won",      1000, 1000, True),
        ("research_won",      "research_won",      999,  1000, False),
        ("research_stolen",   "research_stolen",   1000, 1000, True),
        ("research_stolen",   "research_stolen",   999,  1000, False),
        ("longest_battle_ms", "longest_battle_ms", 180000, 180000, True),
        ("longest_battle_ms", "longest_battle_ms", 179999, 180000, False),
        ("coward_attacks",    "coward_attacks",    5,   5,   True),
        ("coward_attacks",    "coward_attacks",    4,   5,   False),
        ("max_lucky_punch_levels", "max_lucky_punch_levels", 2, 2, True),
        ("max_lucky_punch_levels", "max_lucky_punch_levels", 1, 2, False),
        ("max_artifacts_stolen_one_battle", "max_artifacts_stolen_one_battle", 2, 2, True),
        ("max_artifacts_stolen_one_battle", "max_artifacts_stolen_one_battle", 1, 2, False),
        ("max_artifacts_lost_one_battle",   "max_artifacts_lost_one_battle",   2, 2, True),
        ("max_artifacts_lost_one_battle",   "max_artifacts_lost_one_battle",   1, 2, False),
    ])
    def test_direct_stat(self, ctype, col, val, threshold, expect):
        svc = _svc()
        result = _check(svc, _cond(ctype, threshold), {col: val})
        assert result is expect

    def test_missing_stat_column_is_zero(self):
        svc = _svc()
        assert not _check(svc, _cond("coward_attacks", 1), {})


# ── Single-battle peak conditions report binary progress ───────────────────────

class TestSingleEventThresholdProgress:
    """max_artifacts_stolen_one_battle / max_artifacts_lost_one_battle /
    max_lucky_punch_levels must reach their threshold within one battle, so
    progress should read 0/1 or 1/1 — never e.g. 1/2, which would misleadingly
    suggest accumulating across battles (or, for the era-gap trophy, "do this
    N times" instead of "reach an N-era gap once")."""

    @pytest.mark.parametrize("ctype", [
        "max_artifacts_stolen_one_battle",
        "max_artifacts_lost_one_battle",
        "max_lucky_punch_levels",
    ])
    def test_below_threshold_reports_zero_of_one(self, ctype):
        svc = _svc()
        current, target = _progress(svc, _cond(ctype, 2), {ctype: 1})
        assert (current, target) == (0.0, 1.0)

    @pytest.mark.parametrize("ctype", [
        "max_artifacts_stolen_one_battle",
        "max_artifacts_lost_one_battle",
        "max_lucky_punch_levels",
    ])
    def test_at_threshold_reports_one_of_one(self, ctype):
        svc = _svc()
        current, target = _progress(svc, _cond(ctype, 2), {ctype: 2})
        assert (current, target) == (1.0, 1.0)

    def test_missing_stat_reports_zero_of_one(self):
        svc = _svc()
        current, target = _progress(svc, _cond("max_artifacts_stolen_one_battle", 2), {})
        assert (current, target) == (0.0, 1.0)


# ── Ruler level ───────────────────────────────────────────────────────────────

class TestRulerLevel:
    def _empire_service_stub(self, level: int) -> MagicMock:
        es = MagicMock()
        es.ruler_level_from_xp.return_value = level
        return es

    def test_passes_at_threshold(self):
        es = self._empire_service_stub(18)
        svc = _svc(es)
        empire = _empire()
        assert _check(svc, _cond("ruler_level", 18), {}, empire)

    def test_fails_below_threshold(self):
        es = self._empire_service_stub(17)
        svc = _svc(es)
        empire = _empire()
        assert not _check(svc, _cond("ruler_level", 18), {}, empire)

    def test_no_empire_returns_false(self):
        es = self._empire_service_stub(18)
        svc = _svc(es)
        assert not _check(svc, _cond("ruler_level", 18), {}, None)

    def test_no_empire_service_returns_false(self):
        svc = _svc(None)
        empire = _empire()
        assert not _check(svc, _cond("ruler_level", 18), {}, empire)


# ── Path length ───────────────────────────────────────────────────────────────

class TestPathLength:
    def test_passes(self):
        svc = _svc()
        empire = _empire()
        fake_path = [object()] * 20
        with patch("gameserver.engine.hex_pathfinding.find_path_from_spawn_to_castle",
                   return_value=fake_path):
            result = _check(svc, _cond("path_length", 20), {}, empire)
        assert result

    def test_fails(self):
        svc = _svc()
        empire = _empire()
        fake_path = [object()] * 19
        with patch("gameserver.engine.hex_pathfinding.find_path_from_spawn_to_castle",
                   return_value=fake_path):
            result = _check(svc, _cond("path_length", 20), {}, empire)
        assert not result

    def test_no_path_returns_false(self):
        svc = _svc()
        empire = _empire()
        with patch("gameserver.engine.hex_pathfinding.find_path_from_spawn_to_castle",
                   return_value=None):
            result = _check(svc, _cond("path_length", 1), {}, empire)
        assert not result

    def test_no_empire_returns_false(self):
        svc = _svc()
        assert not _check(svc, _cond("path_length", 1), {}, None)


# ── First in era ──────────────────────────────────────────────────────────────

class TestFirstInEra:
    def test_passes_when_uid_matches(self):
        svc = _svc()
        empire = _empire(uid=42)
        era_firsts = {"stone": 42, "neolithic": 7}
        assert _check(svc, _cond("first_in_era", era="stone"), {}, empire, era_firsts)

    def test_fails_when_different_uid(self):
        svc = _svc()
        empire = _empire(uid=42)
        era_firsts = {"stone": 99}
        assert not _check(svc, _cond("first_in_era", era="stone"), {}, empire, era_firsts)

    def test_fails_when_era_not_in_firsts(self):
        svc = _svc()
        empire = _empire(uid=42)
        assert not _check(svc, _cond("first_in_era", era="bronze"), {}, empire, {})

    def test_no_empire_returns_false(self):
        svc = _svc()
        assert not _check(svc, _cond("first_in_era", era="stone"), {}, None, {"stone": 1})

    def test_no_era_firsts_returns_false(self):
        svc = _svc()
        empire = _empire(uid=1)
        assert not _check(svc, _cond("first_in_era", era="stone"), {}, empire, None)

    @pytest.mark.parametrize("era", [
        "stone", "neolithic", "bronze", "iron",
        "medieval", "renaissance", "industrial", "modern", "future",
    ])
    def test_all_nine_eras(self, era):
        svc = _svc()
        empire = _empire(uid=1)
        era_firsts = {era: 1}
        assert _check(svc, _cond("first_in_era", era=era), {}, empire, era_firsts)


# ── Meta: all_era_firsts ──────────────────────────────────────────────────────

_ERA_FIRST_IIDS = [
    "FIRST_STONE", "FIRST_NEOLITHIC", "FIRST_BRONZE", "FIRST_IRON",
    "FIRST_MEDIEVAL", "FIRST_RENAISSANCE", "FIRST_INDUSTRIAL",
    "FIRST_MODERN", "FIRST_FUTURE",
]


def _svc_with_trophies(trophy_iids: list[str]) -> TrophyService:
    svc = _svc()

    def _make_trophy(iid: str, ctype: str, **ckwargs: object) -> ItemDetails:
        item = MagicMock(spec=ItemDetails)
        item.iid = iid
        item.item_type = ItemType.TROPHY
        item.condition = {"type": ctype, **ckwargs}
        return item

    era_keys = ["stone", "neolithic", "bronze", "iron", "medieval",
                "renaissance", "industrial", "modern", "future"]
    items = {}
    for iid, era in zip(_ERA_FIRST_IIDS, era_keys):
        items[iid] = _make_trophy(iid, "first_in_era", era=era)
    items["ALL_ERA"] = _make_trophy("ALL_ERA", "all_era_firsts")
    items["ALL_T"]   = _make_trophy("ALL_T",   "all_trophies")
    for extra_iid in trophy_iids:
        if extra_iid not in items:
            items[extra_iid] = _make_trophy(extra_iid, "defense_won", threshold=1)
    svc._upgrade_provider.items = items
    return svc


class TestAllEraFirsts:
    def test_passes_when_all_nine_earned(self):
        svc = _svc_with_trophies([])
        empire = _empire(trophies={iid: {} for iid in _ERA_FIRST_IIDS})
        assert _check(svc, _cond("all_era_firsts"), {}, empire)

    def test_fails_when_one_missing(self):
        svc = _svc_with_trophies([])
        earned = {iid: {} for iid in _ERA_FIRST_IIDS[:-1]}  # missing FIRST_FUTURE
        empire = _empire(trophies=earned)
        assert not _check(svc, _cond("all_era_firsts"), {}, empire)

    def test_fails_when_none_earned(self):
        svc = _svc_with_trophies([])
        empire = _empire(trophies={})
        assert not _check(svc, _cond("all_era_firsts"), {}, empire)

    def test_no_empire_returns_false(self):
        svc = _svc_with_trophies([])
        assert not _check(svc, _cond("all_era_firsts"), {}, None)


# ── Meta: all_trophies ────────────────────────────────────────────────────────

class TestAllTrophies:
    def test_passes_when_all_non_meta_earned(self):
        extra = ["UNBROKEN", "IRON_WALL"]
        svc = _svc_with_trophies(extra)
        # all non-meta trophies: the 9 era-firsts + 2 extra
        earned = {iid: {} for iid in _ERA_FIRST_IIDS + extra}
        empire = _empire(trophies=earned)
        assert _check(svc, _cond("all_trophies"), {}, empire)

    def test_fails_when_one_non_meta_missing(self):
        extra = ["UNBROKEN", "IRON_WALL"]
        svc = _svc_with_trophies(extra)
        earned = {iid: {} for iid in _ERA_FIRST_IIDS + ["UNBROKEN"]}  # IRON_WALL missing
        empire = _empire(trophies=earned)
        assert not _check(svc, _cond("all_trophies"), {}, empire)

    def test_meta_trophies_themselves_excluded_from_requirement(self):
        """all_trophies should NOT require ALL_ERA or ALL_T themselves."""
        svc = _svc_with_trophies([])
        # Earn only era-firsts — no ALL_ERA or ALL_T in earned set
        earned = {iid: {} for iid in _ERA_FIRST_IIDS}
        empire = _empire(trophies=earned)
        # Only non-meta trophies are the 9 era-first ones — should pass
        assert _check(svc, _cond("all_trophies"), {}, empire)

    def test_no_empire_returns_false(self):
        svc = _svc_with_trophies([])
        assert not _check(svc, _cond("all_trophies"), {}, None)


# ── Unknown condition type ─────────────────────────────────────────────────────

class TestUnknownCondition:
    def test_returns_false_and_logs_warning(self, caplog):
        import logging
        svc = _svc()
        with caplog.at_level(logging.WARNING):
            result = _check(svc, _cond("totally_made_up", 1), {})
        assert not result
        assert "totally_made_up" in caplog.text


# ── check_and_award integration (async) ──────────────────────────────────────

class TestCheckAndAward:
    """Light integration: award logic writes to DB and empire.trophies."""

    def _make_svc_with_one_trophy(self, ctype: str, threshold: int = 1) -> TrophyService:
        svc = TrophyService.__new__(TrophyService)
        svc._database = MagicMock()
        svc._database.get_trophy_rows = AsyncMock(return_value=[])
        svc._database.get_empire_stats = AsyncMock(return_value={"defense_won_human": threshold})
        svc._database.get_era_firsts = AsyncMock(return_value=[])
        svc._database.award_trophy = AsyncMock()
        item = MagicMock(spec=ItemDetails)
        item.iid = "TEST_TROPHY"
        item.item_type = ItemType.TROPHY
        item.condition = {"type": ctype, "threshold": threshold}
        svc._upgrade_provider = MagicMock()
        svc._upgrade_provider.items = {"TEST_TROPHY": item}
        svc._empire_service = None
        return svc

    async def test_awards_when_condition_met(self):
        svc = self._make_svc_with_one_trophy("defense_won_human", threshold=1)
        empire = _empire()
        newly = await svc.check_and_award(uid=1, empire=empire)
        assert "TEST_TROPHY" in newly
        assert "TEST_TROPHY" in empire.trophies
        svc._database.award_trophy.assert_awaited_once()

    async def test_skips_already_earned(self):
        svc = self._make_svc_with_one_trophy("defense_won_human", threshold=1)
        empire = _empire(trophies={"TEST_TROPHY": {"earned_at": 0, "season": 1}})
        newly = await svc.check_and_award(uid=1, empire=empire)
        assert newly == []
        svc._database.award_trophy.assert_not_awaited()

    async def test_does_not_award_when_condition_not_met(self):
        svc = self._make_svc_with_one_trophy("defense_won_human", threshold=5)
        # stats only have 1 win but we need 5
        svc._database.get_empire_stats = AsyncMock(return_value={"defense_won_human": 1})
        empire = _empire()
        newly = await svc.check_and_award(uid=1, empire=empire)
        assert newly == []
        svc._database.award_trophy.assert_not_awaited()

    async def test_no_empire_returns_empty(self):
        svc = self._make_svc_with_one_trophy("defense_won_human")
        newly = await svc.check_and_award(uid=1, empire=None)
        assert newly == []

    async def test_meta_awarded_after_non_meta(self):
        """all_era_firsts is awarded in the same call that completes the last era-first."""
        svc = TrophyService.__new__(TrophyService)
        svc._database = MagicMock()
        era_keys = ["stone", "neolithic", "bronze", "iron", "medieval",
                    "renaissance", "industrial", "modern", "future"]
        era_first_iids = ["FIRST_STONE", "FIRST_NEOLITHIC", "FIRST_BRONZE", "FIRST_IRON",
                          "FIRST_MEDIEVAL", "FIRST_RENAISSANCE", "FIRST_INDUSTRIAL",
                          "FIRST_MODERN", "FIRST_FUTURE"]

        def _make_first_in_era(iid: str, era: str) -> MagicMock:
            m = MagicMock(spec=ItemDetails)
            m.iid = iid
            m.item_type = ItemType.TROPHY
            m.condition = {"type": "first_in_era", "era": era}
            return m

        meta_item = MagicMock(spec=ItemDetails)
        meta_item.iid = "TRAILBLAZER"
        meta_item.item_type = ItemType.TROPHY
        meta_item.condition = {"type": "all_era_firsts"}

        items = {iid: _make_first_in_era(iid, era)
                 for iid, era in zip(era_first_iids, era_keys)}
        items["TRAILBLAZER"] = meta_item
        svc._upgrade_provider = MagicMock()
        svc._upgrade_provider.items = items

        uid = 5
        # All 9 era-firsts belong to uid=5
        era_firsts_rows = [{"era_key": era, "uid": uid} for era in era_keys]
        svc._database.get_trophy_rows = AsyncMock(return_value=[])
        svc._database.get_empire_stats = AsyncMock(return_value={})
        svc._database.get_era_firsts = AsyncMock(return_value=era_firsts_rows)
        svc._database.award_trophy = AsyncMock()
        svc._empire_service = None

        empire = _empire(uid=uid)
        newly = await svc.check_and_award(uid=uid, empire=empire)

        assert set(newly) == set(era_first_iids) | {"TRAILBLAZER"}
        assert "TRAILBLAZER" in empire.trophies


# ── get_condition_progress_all ─────────────────────────────────────────────────

class TestGetConditionProgressAll:
    """Progress fraction (current/target) for the /api/empire/trophies REST response."""

    def _make_svc(self) -> TrophyService:
        svc = TrophyService.__new__(TrophyService)
        svc._database = MagicMock()
        svc._database.get_empire_stats = AsyncMock(return_value={"defense_won_human": 7})
        svc._database.get_era_firsts = AsyncMock(return_value=[])
        item = MagicMock(spec=ItemDetails)
        item.iid = "TEST_TROPHY"
        item.item_type = ItemType.TROPHY
        item.condition = {"type": "defense_won_human", "threshold": 50}
        svc._upgrade_provider = MagicMock()
        svc._upgrade_provider.items = {"TEST_TROPHY": item}
        svc._empire_service = None
        return svc

    async def test_returns_current_and_target_for_unearned_trophy(self):
        svc = self._make_svc()
        empire = _empire()
        progress = await svc.get_condition_progress_all(uid=1, empire=empire)
        assert progress["TEST_TROPHY"] == (7.0, 50.0)
