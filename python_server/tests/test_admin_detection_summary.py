"""Tests for GET /api/admin/detection-summary."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from gameserver.models.empire import Empire
from gameserver.network.jwt_auth import get_current_uid_admin
from gameserver.network.routers.admin import make_router


ADMIN_UID = 1
UID_A = 20
UID_B = 21
UID_C = 22


def _breakdown(bot_probability=0.5, is_bot=False, **overrides):
    base = {
        "user_agent": "", "header_score": None, "reaction_sample_count": 0,
        "reaction_score": None, "timing_score": None, "declared_bot": False,
        "bot_probability": bot_probability, "is_bot": is_bot,
    }
    base.update(overrides)
    return base


@pytest.fixture
def client():
    empire_a = Empire(uid=UID_A, name="Vanitas", resources={})
    empire_b = Empire(uid=UID_B, name="Nocturne", resources={})
    empire_c = Empire(uid=UID_C, name="Clean", resources={})
    empires = {UID_A: empire_a, UID_B: empire_b, UID_C: empire_c}
    empire_service = SimpleNamespace(
        get=lambda uid: empires.get(uid),
        all_empires=empires,
        _gc=None,
    )
    database = AsyncMock()
    database.get_user_by_uid = AsyncMock(return_value={"username": "eem"})
    database.get_active_anti_farm_pairs = AsyncMock(return_value=[])
    database.get_active_window_event_keys = AsyncMock(return_value=[])
    bot_detector = SimpleNamespace(get_signal_breakdown=lambda uid: _breakdown())
    services = SimpleNamespace(
        empire_service=empire_service,
        database=database,
        bot_detector=bot_detector,
    )

    app = FastAPI()
    app.include_router(make_router(services))
    app.dependency_overrides[get_current_uid_admin] = lambda: ADMIN_UID

    return TestClient(app), services


def test_returns_empty_when_nothing_flagged(client):
    tc, _services = client
    r = tc.get("/api/admin/detection-summary")
    assert r.status_code == 200
    assert r.json() == {"summary": []}


def test_high_bot_probability_included_with_full_breakdown(client):
    tc, services = client
    services.bot_detector = SimpleNamespace(
        get_signal_breakdown=lambda uid: _breakdown(
            bot_probability=0.9, is_bot=True, user_agent="python-requests/2.31",
            header_score=0.92, reaction_score=1.0, reaction_sample_count=5, timing_score=0.8,
        ) if uid == UID_A else _breakdown(),
    )
    r = tc.get("/api/admin/detection-summary")
    assert r.status_code == 200
    body = r.json()
    assert len(body["summary"]) == 1
    row = body["summary"][0]
    assert row["uid"] == UID_A
    assert row["name"] == "Vanitas"
    assert row["bot_probability"] == 0.9
    assert row["is_bot"] is True
    assert row["user_agent"] == "python-requests/2.31"
    assert row["header_score"] == 0.92
    assert row["reaction_score"] == 1.0
    assert row["reaction_sample_count"] == 5
    assert row["timing_score"] == 0.8
    assert row["anti_farm_win_count"] == 0
    assert row["skip_siege_count"] == 0
    assert "device_cluster_score" not in row


def test_anti_farm_involvement_included_even_at_neutral_bot_probability(client):
    tc, services = client
    services.database.get_active_anti_farm_pairs = AsyncMock(return_value=[
        {"attacker_uid": UID_A, "defender_uid": UID_B, "win_count": 5, "last_win_ts": 1234},
    ])
    r = tc.get("/api/admin/detection-summary")
    body = r.json()
    by_uid = {row["uid"]: row for row in body["summary"]}
    assert by_uid[UID_A]["anti_farm_win_count"] == 5
    assert by_uid[UID_B]["anti_farm_win_count"] == 5
    assert UID_C not in by_uid


def test_skip_siege_involvement_included(client):
    tc, services = client
    services.database.get_active_window_event_keys = AsyncMock(return_value=[
        {"key_uid": UID_B, "event_count": 7, "last_ts": 1234, "mean_interval_s": 2.0,
         "stddev_interval_s": 0.0, "max_magnitude": 90.0, "distinct_ref_ids": 2},
    ])
    r = tc.get("/api/admin/detection-summary")
    body = r.json()
    by_uid = {row["uid"]: row for row in body["summary"]}
    assert by_uid[UID_B]["skip_siege_count"] == 7


def test_declared_bot_flag_passthrough(client):
    tc, services = client
    services.bot_detector = SimpleNamespace(
        get_signal_breakdown=lambda uid: _breakdown(
            bot_probability=1.0, is_bot=True, declared_bot=True,
        ) if uid == UID_A else _breakdown(),
    )
    r = tc.get("/api/admin/detection-summary")
    body = r.json()
    by_uid = {row["uid"]: row for row in body["summary"]}
    assert by_uid[UID_A]["declared_bot"] is True


def test_sorted_by_bot_probability_desc(client):
    tc, services = client
    services.bot_detector = SimpleNamespace(
        get_signal_breakdown=lambda uid: _breakdown(
            bot_probability={UID_A: 0.9, UID_B: 0.95}.get(uid, 0.5),
        ),
    )
    r = tc.get("/api/admin/detection-summary")
    body = r.json()
    assert [row["uid"] for row in body["summary"]] == [UID_B, UID_A]
