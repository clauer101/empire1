"""Tests for the REST API and JWT authentication.

Uses httpx AsyncClient with FastAPI TestClient transport to test
REST endpoints end-to-end without starting a real server.
"""

from __future__ import annotations

import asyncio
from typing import Any, Optional
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

from gameserver.models.empire import Empire
from gameserver.models.army import Army
from gameserver.models.map import HexCoord
from gameserver.models.structure import Structure
from gameserver.engine.empire_service import EmpireService
from gameserver.engine.attack_service import AttackService
from gameserver.engine.upgrade_provider import UpgradeProvider
from gameserver.network.router import Router
from gameserver.network.handlers import register_all_handlers
from gameserver.network.jwt_auth import create_token, verify_token
from gameserver.network.rest_api import create_app
from gameserver.util.events import EventBus


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

TEST_UID = 42


def _make_empire(uid: int = TEST_UID, name: str = "TestEmpire") -> Empire:
    """Create a test empire with pre-populated data."""
    return Empire(
        uid=uid,
        name=name,
        resources={"gold": 500.0, "culture": 1000.0, "life": 10.0},
        citizens={"merchant": 3, "scientist": 2, "artist": 1},
        buildings={"farm": 0.0, "library": 0.0},
        knowledge={"archery": 0.0},
        structures={
            1: Structure(
                sid=1, iid="tower", position=HexCoord(2, 3),
                damage=10.0, range=3, reload_time_ms=1000.0, shot_speed=5.0,
            ),
        },
        armies=[Army(aid=1, uid=uid, name="Alpha")],
        effects={"speed": 1.5},
        artefacts=["golden_shield"],
        max_life=10.0,
    )


def _make_services(empire: Optional[Empire] = None) -> Any:
    """Create a minimal Services-like object for REST tests."""
    event_bus = EventBus()
    upgrade_provider = UpgradeProvider()
    empire_service = EmpireService(upgrade_provider, event_bus)
    attack_service = AttackService(event_bus, empire_service=empire_service)
    if empire is not None:
        empire_service.register(empire)

    router = Router()

    # Auth service mock
    auth_service = AsyncMock()
    auth_service.login = AsyncMock(return_value=TEST_UID)
    auth_service.signup = AsyncMock(return_value=TEST_UID)

    svc = MagicMock()
    svc.event_bus = event_bus
    svc.upgrade_provider = upgrade_provider
    svc.empire_service = empire_service
    svc.attack_service = attack_service
    svc.router = router
    svc.auth_service = auth_service
    svc.game_config = None
    svc.server = MagicMock()
    return svc


@pytest.fixture
def services():
    empire = _make_empire()
    svc = _make_services(empire)
    register_all_handlers(svc)
    return svc


@pytest.fixture
def app(services):
    return create_app(services)


@pytest.fixture
def token():
    """A valid JWT token for TEST_UID."""
    return create_token(TEST_UID)


@pytest.fixture
async def client(app):
    """httpx async client wired to the FastAPI app."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


def _auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# JWT unit tests
# ---------------------------------------------------------------------------


class TestJWT:
    def test_create_and_verify(self):
        tok = create_token(123)
        assert verify_token(tok) == 123

    def test_invalid_token(self):
        with pytest.raises(ValueError):
            verify_token("not.a.valid.token")

    def test_tampered_token(self):
        tok = create_token(99)
        # Flip a character in the payload
        parts = tok.split(".")
        parts[1] = parts[1][:5] + "X" + parts[1][6:]
        tampered = ".".join(parts)
        with pytest.raises(ValueError):
            verify_token(tampered)


# ---------------------------------------------------------------------------
# Auth endpoints
# ---------------------------------------------------------------------------


class TestAuthEndpoints:
    @pytest.mark.asyncio
    async def test_login_success(self, client, services):
        resp = await client.post("/api/auth/login", json={
            "username": "testuser",
            "password": "testpass",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["uid"] == TEST_UID
        assert data["token"]  # non-empty JWT
        # Verify the returned token is valid
        uid = verify_token(data["token"])
        assert uid == TEST_UID

    @pytest.mark.asyncio
    async def test_login_failure(self, client, services):
        services.auth_service.login.return_value = None
        resp = await client.post("/api/auth/login", json={
            "username": "wrong",
            "password": "wrong",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is False
        assert data["token"] == ""

    @pytest.mark.asyncio
    async def test_signup_success(self, client, services):
        resp = await client.post("/api/auth/signup", json={
            "username": "newuser",
            "password": "newpass",
            "email": "a@b.com",
            "empire_name": "New Empire",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["uid"] == TEST_UID

    @pytest.mark.asyncio
    async def test_signup_failure(self, client, services):
        services.auth_service.signup.return_value = "Username already taken"
        resp = await client.post("/api/auth/signup", json={
            "username": "taken",
            "password": "pass",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is False
        assert "taken" in data["reason"].lower()


# ---------------------------------------------------------------------------
# Protected endpoints — no token
# ---------------------------------------------------------------------------


class TestProtectedEndpointsNoToken:
    @pytest.mark.asyncio
    async def test_summary_requires_auth(self, client):
        resp = await client.get("/api/empire/summary")
        assert resp.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_items_requires_auth(self, client):
        resp = await client.get("/api/empire/items")
        assert resp.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_build_requires_auth(self, client):
        resp = await client.post("/api/empire/build", json={"iid": "farm"})
        assert resp.status_code in (401, 403)


# ---------------------------------------------------------------------------
# Empire query endpoints
# ---------------------------------------------------------------------------


class TestEmpireQueries:
    @pytest.mark.asyncio
    async def test_get_summary(self, client, token):
        resp = await client.get("/api/empire/summary", headers=_auth_header(token))
        assert resp.status_code == 200
        data = resp.json()
        # Summary should include empire data
        assert data.get("type") == "summary_response" or "resources" in data or "gold" in str(data)

    @pytest.mark.asyncio
    async def test_get_items(self, client, token):
        resp = await client.get("/api/empire/items", headers=_auth_header(token))
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_get_military(self, client, token):
        resp = await client.get("/api/empire/military", headers=_auth_header(token))
        assert resp.status_code == 200
        data = resp.json()
        assert "armies" in data or "type" in data


# ---------------------------------------------------------------------------
# Build / Citizens
# ---------------------------------------------------------------------------


class TestBuildAndCitizens:
    @pytest.mark.asyncio
    async def test_build_item(self, client, token):
        resp = await client.post(
            "/api/empire/build",
            json={"iid": "farm"},
            headers=_auth_header(token),
        )
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_citizen_upgrade(self, client, token):
        resp = await client.post(
            "/api/empire/citizen/upgrade",
            json={},
            headers=_auth_header(token),
        )
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_change_citizen(self, client, token):
        resp = await client.put(
            "/api/empire/citizen",
            json={"merchant": 2, "scientist": 2, "artist": 2},
            headers=_auth_header(token),
        )
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Map endpoints
# ---------------------------------------------------------------------------


class TestMapEndpoints:
    @pytest.mark.asyncio
    async def test_load_map(self, client, token):
        resp = await client.get("/api/map", headers=_auth_header(token))
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_save_map(self, client, token):
        resp = await client.put(
            "/api/map",
            json={"tiles": {"0,0": {"type": "grass"}}},
            headers=_auth_header(token),
        )
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Army endpoints
# ---------------------------------------------------------------------------


class TestArmyEndpoints:
    @pytest.mark.asyncio
    async def test_create_army(self, client, token):
        resp = await client.post(
            "/api/army",
            json={"name": "Bravo"},
            headers=_auth_header(token),
        )
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_rename_army(self, client, token):
        resp = await client.put(
            "/api/army/1",
            json={"name": "Renamed"},
            headers=_auth_header(token),
        )
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_add_wave(self, client, token):
        resp = await client.post(
            "/api/army/1/wave",
            json={},
            headers=_auth_header(token),
        )
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_change_wave(self, client, token):
        resp = await client.put(
            "/api/army/1/wave/0",
            json={"critter_iid": "WARRIOR", "slots": 5},
            headers=_auth_header(token),
        )
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Attack endpoint
# ---------------------------------------------------------------------------


class TestAttackEndpoint:
    @pytest.mark.asyncio
    async def test_attack(self, client, token, services):
        # Create a target empire so the attack handler can find it
        target = _make_empire(uid=99, name="EnemyEmpire")
        services.empire_service.register(target)

        resp = await client.post(
            "/api/attack",
            json={"target_uid": 99, "army_aid": 1},
            headers=_auth_header(token),
        )
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Round-trip: login → get summary
# ---------------------------------------------------------------------------


class TestRoundTrip:
    @pytest.mark.asyncio
    async def test_login_then_summary(self, client, services):
        """Full flow: login, get token, use it to fetch summary."""
        # Login
        login_resp = await client.post("/api/auth/login", json={
            "username": "player1",
            "password": "secret",
        })
        assert login_resp.status_code == 200
        token = login_resp.json()["token"]
        assert token

        # Use token to get summary
        summary_resp = await client.get(
            "/api/empire/summary",
            headers=_auth_header(token),
        )
        assert summary_resp.status_code == 200
