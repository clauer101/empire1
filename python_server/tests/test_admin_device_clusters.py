"""Tests for GET /api/admin/device-clusters."""

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


@pytest.fixture
def client():
    empire_a = Empire(uid=UID_A, name="Vanitas", resources={})
    empire_b = Empire(uid=UID_B, name="Nocturne", resources={})
    empires = {UID_A: empire_a, UID_B: empire_b}
    empire_service = SimpleNamespace(get=lambda uid: empires.get(uid))
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


def test_returns_empty_when_no_clusters(client):
    tc, database = client
    database.get_device_clusters = AsyncMock(return_value=[])
    r = tc.get("/api/admin/device-clusters")
    assert r.status_code == 200
    assert r.json() == {"active": []}


def test_resolves_both_empire_names(client):
    tc, database = client
    database.get_device_clusters = AsyncMock(return_value=[
        {"uid_a": UID_A, "uid_b": UID_B, "shared_ips": "1.2.3.4", "shared_fps": "", "shared_dids": "", "score": 30},
    ])
    r = tc.get("/api/admin/device-clusters")
    assert r.status_code == 200
    body = r.json()
    assert len(body["active"]) == 1
    assert body["active"][0]["name_a"] == "Vanitas"
    assert body["active"][0]["name_b"] == "Nocturne"


def test_unknown_uid_falls_back_to_uid_label(client):
    tc, database = client
    database.get_device_clusters = AsyncMock(return_value=[
        {"uid_a": UID_A, "uid_b": 9999, "shared_ips": "", "shared_fps": "", "shared_dids": "abc", "score": 70},
    ])
    r = tc.get("/api/admin/device-clusters")
    assert r.status_code == 200
    body = r.json()
    assert body["active"][0]["name_a"] == "Vanitas"
    assert body["active"][0]["name_b"] == "uid 9999"


def test_score_and_shared_fields_passthrough(client):
    tc, database = client
    database.get_device_clusters = AsyncMock(return_value=[
        {"uid_a": UID_A, "uid_b": UID_B, "shared_ips": "1.2.3.4", "shared_fps": "fp1", "shared_dids": "dev1", "score": 100},
    ])
    r = tc.get("/api/admin/device-clusters")
    assert r.status_code == 200
    row = r.json()["active"][0]
    assert row["score"] == 100
    assert row["shared_ips"] == "1.2.3.4"
    assert row["shared_fps"] == "fp1"
    assert row["shared_dids"] == "dev1"
