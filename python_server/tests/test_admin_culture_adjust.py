"""Tests for POST /api/admin/empire/{uid}/culture-adjust (admin culture bonus/malus)."""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from gameserver.models.empire import Empire
from gameserver.network.jwt_auth import get_current_uid_admin
from gameserver.network.routers.admin import make_router


ADMIN_UID = 1
EMPIRE_UID = 26


@pytest.fixture
def client():
    empire = Empire(uid=EMPIRE_UID, name="Vanitas", resources={"culture": 100.0})
    empire_service = SimpleNamespace(get=lambda uid: empire if uid == EMPIRE_UID else None)
    services = SimpleNamespace(
        empire_service=empire_service,
        database=None,
    )

    app = FastAPI()
    app.include_router(make_router(services))
    app.dependency_overrides[get_current_uid_admin] = lambda: ADMIN_UID

    return TestClient(app), empire


def test_culture_bonus_increases_balance(client):
    tc, empire = client
    r = tc.post(f"/api/admin/empire/{EMPIRE_UID}/culture-adjust", json={"amount": 50.0})
    assert r.status_code == 200
    body = r.json()
    assert body["culture_before"] == 100.0
    assert body["culture_after"] == 150.0
    assert empire.resources["culture"] == 150.0


def test_culture_malus_decreases_balance(client):
    tc, empire = client
    r = tc.post(f"/api/admin/empire/{EMPIRE_UID}/culture-adjust", json={"amount": -30.0})
    assert r.status_code == 200
    body = r.json()
    assert body["culture_after"] == 70.0
    assert empire.resources["culture"] == 70.0


def test_culture_malus_clamped_at_zero(client):
    tc, empire = client
    r = tc.post(f"/api/admin/empire/{EMPIRE_UID}/culture-adjust", json={"amount": -1000.0})
    assert r.status_code == 200
    body = r.json()
    assert body["culture_after"] == 0.0
    assert empire.resources["culture"] == 0.0


def test_unknown_empire_returns_404(client):
    tc, _empire = client
    r = tc.post("/api/admin/empire/9999/culture-adjust", json={"amount": 10.0})
    assert r.status_code == 404
