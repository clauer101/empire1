"""Eternal ranking — season archive parsing and the /api/empires/eternal endpoint."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock

import pytest
import yaml
from httpx import ASGITransport, AsyncClient

from gameserver.engine import global_state
from gameserver.engine.ai_service import AI_UID
from gameserver.network.jwt_auth import create_token
from gameserver.network.rest_api import create_app
from gameserver.persistence import season_archive

from conftest import make_empire, make_services

TEST_UID = 42


def _write_snapshot(
    results_dir,
    season_number: int,
    empires: list[dict[str, Any]],
    *,
    title: str = "",
) -> None:
    """Write a minimal season snapshot in the shape _take_season_snapshot produces."""
    folder = results_dir / f"season{season_number}"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "state.yaml").write_text(
        yaml.safe_dump({
            "global": {"season_number": season_number, "season_title": title},
            "empires": empires,
        }),
        encoding="utf-8",
    )


def _empire_entry(uid: int, name: str, culture: float, is_bot: bool = False) -> dict[str, Any]:
    entry: dict[str, Any] = {"uid": uid, "name": name, "resources": {"culture": culture}}
    if is_bot:
        entry["is_bot"] = True
    return entry


@pytest.fixture
def results_dir(tmp_path, monkeypatch):
    """A results directory with three archived seasons plus a stray future folder."""
    d = tmp_path / "results"
    _write_snapshot(d, 1, [
        _empire_entry(AI_UID, "AI", 999_000_000.0),
        _empire_entry(7, "Old Name", 1_000_000.0),
        _empire_entry(8, "Quitter", 2_000_000.0),
    ], title="The Dawn of Empires")
    _write_snapshot(d, 2, [
        _empire_entry(7, "New Name", 2_000_000.0),
        _empire_entry(9, "Botty", 1_500_000.0, is_bot=True),
    ], title="The Rise of Kingdoms")
    # Left over from testing — must be ignored while season 3 is running
    _write_snapshot(d, 20, [_empire_entry(7, "Bogus", 50_000_000.0)])
    monkeypatch.setattr(season_archive, "DEFAULT_RESULTS_DIR", str(d))
    season_archive.clear_cache()
    # The endpoint derives "finished" from the running season number
    previous = (global_state.get_season_number(), global_state.get_season_title())
    global_state.set_season(3, "The Rise of the Robots")
    yield d
    global_state.set_season(*previous)
    season_archive.clear_cache()


# ---------------------------------------------------------------------------
# season_archive
# ---------------------------------------------------------------------------

class TestSeasonArchive:
    def test_only_finished_seasons_are_returned(self, results_dir):
        seasons = season_archive.load_finished_seasons(current_season=3)
        assert [s.season_number for s in seasons] == [1, 2]
        assert seasons[0].season_title == "The Dawn of Empires"

    def test_ai_uid_excluded(self, results_dir):
        seasons = season_archive.load_finished_seasons(current_season=3)
        assert AI_UID not in seasons[0].culture_by_uid

    def test_bot_flag_collected(self, results_dir):
        seasons = season_archive.load_finished_seasons(current_season=3)
        assert seasons[1].bots == {9}

    def test_current_season_counts_once_its_empires_are_wiped(self, results_dir):
        # The season counter only advances when the next season starts, so
        # between wipe and new season the finished season carries the current
        # number — it must still land in the table.
        seasons = season_archive.load_finished_seasons(
            current_season=2, current_season_ended=True
        )
        assert [s.season_number for s in seasons] == [1, 2]

    def test_current_season_withheld_until_the_wipe(self, results_dir):
        # Before the wipe the empires still hold that culture live; counting
        # the snapshot too would double it.
        seasons = season_archive.load_finished_seasons(
            current_season=2, current_season_ended=False
        )
        assert [s.season_number for s in seasons] == [1]

    def test_missing_results_dir_is_empty(self, tmp_path, monkeypatch):
        monkeypatch.setattr(season_archive, "DEFAULT_RESULTS_DIR", str(tmp_path / "nope"))
        assert season_archive.load_finished_seasons(current_season=3) == []

    def test_malformed_snapshot_skipped(self, results_dir):
        (results_dir / "season5").mkdir()
        (results_dir / "season5" / "state.yaml").write_text("{{ not yaml", encoding="utf-8")
        seasons = season_archive.load_finished_seasons(current_season=9)
        assert [s.season_number for s in seasons] == [1, 2]

    def test_snapshot_without_season_number_skipped(self, results_dir):
        folder = results_dir / "season6"
        folder.mkdir()
        (folder / "state.yaml").write_text(
            yaml.safe_dump({"global": {}, "empires": []}), encoding="utf-8"
        )
        seasons = season_archive.load_finished_seasons(current_season=9)
        assert [s.season_number for s in seasons] == [1, 2]

    def test_parsed_snapshot_is_cached(self, results_dir):
        first = season_archive.load_finished_seasons(current_season=3)
        second = season_archive.load_finished_seasons(current_season=3)
        assert first[0] is second[0]


# ---------------------------------------------------------------------------
# GET /api/empires/eternal
# ---------------------------------------------------------------------------

def _services(*empires):
    svc = make_services()
    for empire in empires:
        svc.empire_service.register(empire)
    svc.database = AsyncMock()
    svc.database.list_users = AsyncMock(return_value=[])
    svc.server = None
    return svc


@pytest.fixture
async def client_factory():
    clients: list[AsyncClient] = []

    async def _make(svc):
        c = AsyncClient(transport=ASGITransport(app=create_app(svc)), base_url="http://test")
        clients.append(c)
        return c

    yield _make
    for c in clients:
        await c.aclose()


def _auth(uid: int = TEST_UID) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_token(uid)}"}


class TestEternalRankingEndpoint:
    async def test_sums_past_and_current_culture(self, results_dir, client_factory):
        # uid 7 scored 1M + 2M in the archive and holds 50k right now
        svc = _services(make_empire(uid=7, name="Live Name", culture=50_000.0))
        client = await client_factory(svc)

        resp = await client.get("/api/empires/eternal", headers=_auth(uid=7))
        assert resp.status_code == 200
        data = resp.json()

        row = next(r for r in data["ranking"] if r["uid"] == 7)
        assert row["current_culture"] == 50_000.0
        assert row["total_culture"] == 3_050_000.0
        assert row["seasons_played"] == 3  # two archived + the running one
        assert row["is_self"] is True
        assert row["name"] == "Live Name"  # live name wins over the archived one

    async def test_ranks_are_contiguous_and_sorted(self, results_dir, client_factory):
        svc = _services(make_empire(uid=7, name="Live", culture=50_000.0))
        client = await client_factory(svc)

        data = (await client.get("/api/empires/eternal", headers=_auth(uid=7))).json()
        ranks = [r["rank"] for r in data["ranking"]]
        totals = [r["total_culture"] for r in data["ranking"]]

        assert ranks == list(range(1, len(ranks) + 1))
        assert totals == sorted(totals, reverse=True)
        assert data["total"] == len(ranks)
        assert data["self_rank"] == 1

    async def test_archived_only_player_keeps_archived_name(self, results_dir, client_factory):
        # uid 8 played season 1 and never came back
        svc = _services(make_empire(uid=7, name="Live", culture=50_000.0))
        client = await client_factory(svc)

        data = (await client.get("/api/empires/eternal", headers=_auth(uid=7))).json()
        row = next(r for r in data["ranking"] if r["uid"] == 8)
        assert row["name"] == "Quitter"
        assert row["current_culture"] == 0.0
        assert row["seasons_played"] == 1

    async def test_account_name_used_when_empire_is_gone(self, results_dir, client_factory):
        svc = _services(make_empire(uid=7, name="Live", culture=50_000.0))
        svc.database.list_users = AsyncMock(
            return_value=[{"uid": 8, "username": "quitter", "empire_name": "Renamed Later"}]
        )
        client = await client_factory(svc)

        data = (await client.get("/api/empires/eternal", headers=_auth(uid=7))).json()
        row = next(r for r in data["ranking"] if r["uid"] == 8)
        assert row["name"] == "Renamed Later"

    async def test_ai_and_sub_threshold_empires_absent(self, results_dir, client_factory):
        svc = _services(
            make_empire(uid=7, name="Live", culture=50_000.0),
            make_empire(uid=AI_UID, name="AI", culture=10_000_000.0),
            make_empire(uid=99, name="Newcomer", culture=0.0),
            make_empire(uid=98, name="Almost There", culture=999_999.0),
        )
        client = await client_factory(svc)

        data = (await client.get("/api/empires/eternal", headers=_auth(uid=7))).json()
        uids = {r["uid"] for r in data["ranking"]}
        assert AI_UID not in uids
        assert 99 not in uids  # no culture at all
        assert 98 not in uids  # just under the entry threshold

    async def test_entry_threshold_is_reported_and_enforced(self, results_dir, client_factory):
        svc = _services(
            make_empire(uid=7, name="Live", culture=50_000.0),
            make_empire(uid=98, name="Exactly At Bar", culture=1_000_000.0),
            make_empire(uid=96, name="Just Over Bar", culture=1_000_001.0),
        )
        client = await client_factory(svc)

        data = (await client.get("/api/empires/eternal", headers=_auth(uid=7))).json()
        uids = {r["uid"] for r in data["ranking"]}
        assert data["min_culture"] == 1_000_000.0
        assert 98 not in uids  # "more than 1M" — exactly at the bar is not enough
        assert 96 in uids
        assert all(r["total_culture"] > data["min_culture"] for r in data["ranking"])

    async def test_bots_are_flagged_not_hidden(self, results_dir, client_factory):
        svc = _services(make_empire(uid=7, name="Live", culture=50_000.0))
        client = await client_factory(svc)

        data = (await client.get("/api/empires/eternal", headers=_auth(uid=7))).json()
        row = next(r for r in data["ranking"] if r["uid"] == 9)
        assert row["is_bot"] is True

    async def test_stray_future_season_not_listed(self, results_dir, client_factory):
        svc = _services(make_empire(uid=7, name="Live", culture=50_000.0))
        client = await client_factory(svc)

        data = (await client.get("/api/empires/eternal", headers=_auth(uid=7))).json()
        assert [s["number"] for s in data["seasons"]] == [1, 2]
        # season20's 50M culture must not leak into the totals
        assert max(r["total_culture"] for r in data["ranking"]) == 3_050_000.0

    async def test_ended_season_enters_the_table_during_the_transition(
        self, results_dir, client_factory, monkeypatch
    ):
        # Season 3 has ended: snapshot written, empires wiped (0 culture), but
        # the counter still says 3 because season 4 has not started yet.
        _write_snapshot(results_dir, 3, [
            _empire_entry(7, "Live Name", 4_000_000.0),
        ], title="The Robot Uprising")
        season_archive.clear_cache()
        monkeypatch.setattr(global_state, "_season_wipe_done", True)

        svc = _services(make_empire(uid=7, name="Live Name", culture=0.0))
        client = await client_factory(svc)

        data = (await client.get("/api/empires/eternal", headers=_auth(uid=7))).json()
        assert [s["number"] for s in data["seasons"]] == [1, 2, 3]
        row = next(r for r in data["ranking"] if r["uid"] == 7)
        assert row["total_culture"] == 7_000_000.0  # 1M + 2M + 4M, all archived
        assert row["current_culture"] == 0.0
        # Scored in three seasons; the wiped empire sitting at 0 is not a 4th
        assert row["seasons_played"] == 3
        # The "current" column now points at the season about to start
        assert data["current_season"] == 4

    async def test_unwiped_season_is_not_counted_twice(
        self, results_dir, client_factory, monkeypatch
    ):
        # Same snapshot, but the wipe has not run: the empire still holds its
        # culture live, so only the older seasons may be summed.
        _write_snapshot(results_dir, 3, [
            _empire_entry(7, "Live Name", 4_000_000.0),
        ], title="The Robot Uprising")
        season_archive.clear_cache()
        monkeypatch.setattr(global_state, "_season_wipe_done", False)

        svc = _services(make_empire(uid=7, name="Live Name", culture=4_000_000.0))
        client = await client_factory(svc)

        data = (await client.get("/api/empires/eternal", headers=_auth(uid=7))).json()
        assert [s["number"] for s in data["seasons"]] == [1, 2]
        row = next(r for r in data["ranking"] if r["uid"] == 7)
        assert row["current_culture"] == 4_000_000.0
        assert row["total_culture"] == 7_000_000.0  # counted once, not 11M
        assert data["current_season"] == 3  # still the running season

    async def test_seasons_counts_only_seasons_with_points(self, results_dir, client_factory):
        # uid 8 sat in the season-1 snapshot at 0 culture and scored only in
        # season 2 — that is one season, not two.
        _write_snapshot(results_dir, 1, [
            _empire_entry(7, "Old Name", 1_000_000.0),
            _empire_entry(8, "Idle", 0.0),
        ], title="The Dawn of Empires")
        _write_snapshot(results_dir, 2, [
            _empire_entry(7, "New Name", 2_000_000.0),
            _empire_entry(8, "Idle", 2_000_000.0),
        ], title="The Rise of Kingdoms")
        season_archive.clear_cache()

        svc = _services(make_empire(uid=7, name="Live", culture=50_000.0))
        client = await client_factory(svc)

        data = (await client.get("/api/empires/eternal", headers=_auth(uid=7))).json()
        row = next(r for r in data["ranking"] if r["uid"] == 8)
        assert row["total_culture"] == 2_000_000.0
        assert row["seasons_played"] == 1

    async def test_past_culture_is_no_longer_reported(self, results_dir, client_factory):
        # The table shows Total / Current / Seasons — "past" was the confusing
        # fourth column and is derivable as total - current anyway.
        svc = _services(make_empire(uid=7, name="Live", culture=50_000.0))
        client = await client_factory(svc)

        data = (await client.get("/api/empires/eternal", headers=_auth(uid=7))).json()
        assert all("past_culture" not in r for r in data["ranking"])

    async def test_self_rank_none_for_player_below_the_threshold(self, results_dir, client_factory):
        svc = _services(make_empire(uid=7, name="Live", culture=50_000.0))
        client = await client_factory(svc)

        data = (await client.get("/api/empires/eternal", headers=_auth(uid=1234))).json()
        assert data["self_rank"] is None
        assert data["self_uid"] == 1234
