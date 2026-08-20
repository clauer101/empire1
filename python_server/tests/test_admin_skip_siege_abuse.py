"""Tests for GET /api/admin/skip-siege-abuse/active."""

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
DEFENDER_UID = 20


@pytest.fixture
def client():
    defender = Empire(uid=DEFENDER_UID, name="Vanitas", resources={})
    empire_service = SimpleNamespace(
        get=lambda uid: defender if uid == DEFENDER_UID else None,
        _gc=None,
    )
    database = AsyncMock()
    database.get_user_by_uid = AsyncMock(return_value={"username": "eem"})
    services = SimpleNamespace(
        empire_service=empire_service,
        database=database,
    )

    app = FastAPI()
    app.include_router(make_router(services))
    app.dependency_overrides[get_current_uid_admin] = lambda: ADMIN_UID

    return TestClient(app), database


def test_returns_empty_when_no_abusers(client):
    tc, database = client
    database.get_active_window_event_keys = AsyncMock(return_value=[])
    r = tc.get("/api/admin/skip-siege-abuse/active")
    assert r.status_code == 200
    body = r.json()
    assert body["active"] == []
    assert body["threshold"] == 5
    assert body["window_minutes"] == 10.0


def test_resolves_defender_name(client):
    tc, database = client
    database.get_active_window_event_keys = AsyncMock(return_value=[
        {
            "key_uid": DEFENDER_UID,
            "event_count": 6,
            "last_ts": 1234,
            "mean_interval_s": 2.0,
            "stddev_interval_s": 0.0,
            "max_magnitude": 300.0,
            "distinct_ref_ids": 3,
        },
    ])
    r = tc.get("/api/admin/skip-siege-abuse/active")
    assert r.status_code == 200
    body = r.json()
    assert len(body["active"]) == 1
    assert body["active"][0]["defender_name"] == "Vanitas"
    assert body["active"][0]["skip_count"] == 6
    assert body["active"][0]["max_siege_remaining_at_skip"] == 300.0
    assert body["active"][0]["distinct_attackers"] == 3


def test_unknown_defender_falls_back_to_uid_label(client):
    tc, database = client
    database.get_active_window_event_keys = AsyncMock(return_value=[
        {
            "key_uid": 9999,
            "event_count": 6,
            "last_ts": 1234,
            "mean_interval_s": 2.0,
            "stddev_interval_s": 0.0,
            "max_magnitude": 300.0,
            "distinct_ref_ids": 3,
        },
    ])
    r = tc.get("/api/admin/skip-siege-abuse/active")
    assert r.status_code == 200
    body = r.json()
    assert body["active"][0]["defender_name"] == "uid 9999"
