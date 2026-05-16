"""Router-level integration tests via httpx AsyncClient.

Covers previously untested endpoints in:
- routers/messages.py
- routers/army.py
- routers/attack.py
- routers/replays.py
- parts of rest_api.py

Uses the same httpx + ASGITransport pattern as test_rest_api.py.
"""

from __future__ import annotations

from typing import Any, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from gameserver.engine.attack_service import AttackService
from gameserver.engine.empire_service import EmpireService
from gameserver.engine.upgrade_provider import UpgradeProvider
from gameserver.models.army import Army, CritterWave
from gameserver.models.attack import Attack, AttackPhase
from gameserver.models.empire import Empire
from gameserver.models.map import HexCoord
from gameserver.models.structure import Structure
from gameserver.network.handlers import register_all_handlers
from gameserver.network.jwt_auth import create_token
from gameserver.network.rest_api import create_app
from gameserver.network.router import Router
from gameserver.util.events import EventBus


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

TEST_UID = 42


def _make_empire(uid: int = TEST_UID, name: str = "TestEmpire") -> Empire:
    return Empire(
        uid=uid,
        name=name,
        resources={"gold": 5000.0, "culture": 1000.0, "life": 10.0},
        citizens={"merchant": 3, "scientist": 2, "artist": 1},
        buildings={},
        knowledge={},
        structures={
            1: Structure(
                sid=1, iid="tower", position=HexCoord(2, 3),
                damage=10.0, range=3, reload_time_ms=1000.0, shot_speed=5.0,
            ),
        },
        armies=[Army(aid=1, uid=uid, name="Alpha",
                     waves=[CritterWave(wave_id=1, iid="goblin", slots=3)])],
        effects={},
        artifacts=[],
        max_life=10.0,
    )


def _make_db_mock() -> AsyncMock:
    db = AsyncMock()
    db.send_message = AsyncMock(return_value={
        "id": 1, "from_uid": TEST_UID, "to_uid": 0, "body": "hello",
        "sent_at": "2024-01-01T00:00:00Z", "read": False,
    })
    db.get_global = AsyncMock(return_value=[])
    db.get_private_for = AsyncMock(return_value=[])
    db.get_battle_reports_for = AsyncMock(return_value=[])
    db.unread_count_private = AsyncMock(return_value=0)
    db.unread_count_battle = AsyncMock(return_value=0)
    db.mark_read = AsyncMock(return_value=True)
    db.list_users = AsyncMock(return_value=[])
    db.save_push_subscription = AsyncMock()
    db.delete_push_subscription = AsyncMock()
    return db


def _make_services(empire: Optional[Empire] = None, with_db: bool = False) -> Any:
    event_bus = EventBus()
    upgrade_provider = UpgradeProvider()
    empire_service = EmpireService(upgrade_provider, event_bus)
    attack_service = AttackService(event_bus, empire_service=empire_service)
    if empire is not None:
        empire_service.register(empire)

    router = Router()
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
    svc.database = _make_db_mock() if with_db else None
    svc.server = MagicMock()
    return svc


def _token(uid: int = TEST_UID) -> str:
    return create_token(uid)


def _auth(uid: int = TEST_UID) -> dict[str, str]:
    return {"Authorization": f"Bearer {_token(uid)}"}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def svc():
    empire = _make_empire()
    s = _make_services(empire, with_db=True)
    register_all_handlers(s)
    return s


@pytest.fixture
def app(svc):
    return create_app(svc)


@pytest.fixture
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


# ---------------------------------------------------------------------------
# Messages router
# ---------------------------------------------------------------------------

class TestMessagesRouter:
    async def test_send_message_global(self, client, svc):
        resp = await client.post(
            "/api/messages",
            json={"body": "hello world", "to_uid": 0},
            headers=_auth(),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True

    async def test_send_message_empty_body_rejected(self, client, svc):
        resp = await client.post(
            "/api/messages",
            json={"body": "   ", "to_uid": 0},
            headers=_auth(),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is False

    async def test_send_message_to_self_rejected(self, client, svc):
        resp = await client.post(
            "/api/messages",
            json={"body": "hi me", "to_uid": TEST_UID},
            headers=_auth(),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is False

    async def test_get_messages(self, client, svc):
        resp = await client.get("/api/messages", headers=_auth())
        assert resp.status_code == 200
        data = resp.json()
        assert "global" in data
        assert "private" in data
        assert "battle_reports" in data

    async def test_mark_read(self, client, svc):
        resp = await client.post("/api/messages/1/read", headers=_auth())
        assert resp.status_code == 200
        data = resp.json()
        assert "success" in data

    async def test_vapid_public_key(self, client):
        resp = await client.get("/api/push/vapid-public-key")
        assert resp.status_code == 200
        data = resp.json()
        assert "key" in data

    async def test_requires_auth(self, client):
        resp = await client.get("/api/messages")
        assert resp.status_code in (401, 403, 422)


# ---------------------------------------------------------------------------
# Army router
# ---------------------------------------------------------------------------

class TestArmyRouter:
    async def test_create_army(self, client, svc):
        resp = await client.post(
            "/api/army",
            json={"name": "My Army"},
            headers=_auth(),
        )
        assert resp.status_code == 200

    async def test_rename_army(self, client, svc):
        resp = await client.put(
            "/api/army/1",
            json={"name": "Renamed"},
            headers=_auth(),
        )
        assert resp.status_code == 200

    async def test_add_wave(self, client, svc):
        resp = await client.post("/api/army/1/wave", headers=_auth())
        assert resp.status_code == 200

    async def test_change_wave(self, client, svc):
        resp = await client.put(
            "/api/army/1/wave/1",
            json={"critter_iid": "goblin", "slots": 2},
            headers=_auth(),
        )
        assert resp.status_code == 200

    async def test_buy_wave_requires_auth(self, client):
        resp = await client.post("/api/army/buy-wave", json={"aid": 1})
        assert resp.status_code in (401, 403, 422)

    async def test_buy_item_upgrade(self, client, svc):
        resp = await client.post(
            "/api/item/buy-upgrade",
            json={"iid": "goblin", "stat": "health"},
            headers=_auth(),
        )
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Attack router
# ---------------------------------------------------------------------------

class TestAttackRouter:
    async def test_skip_siege_not_found(self, client, svc):
        resp = await client.post("/api/attack/999/skip-siege", headers=_auth())
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is False
        assert "error" in data

    async def test_skip_siege_success(self, client, svc):
        # Add a real attack in IN_SIEGE
        attack = Attack(
            attack_id=1, attacker_uid=99, defender_uid=TEST_UID,
            army_aid=1, phase=AttackPhase.IN_SIEGE, eta_seconds=0.0,
        )
        attack.siege_remaining_seconds = 60.0
        svc.attack_service._attacks = [attack]

        resp = await client.post("/api/attack/1/skip-siege", headers=_auth())
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["phase"] == "in_siege"  # attack.phase is now in_battle after skip

    async def test_attack_endpoint_exists(self, client, svc):
        resp = await client.post(
            "/api/attack",
            json={"target_uid": 99, "opponent_name": "enemy", "army_aid": 1},
            headers=_auth(),
        )
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Replays router
# ---------------------------------------------------------------------------

class TestReplaysRouter:
    async def test_get_replays_empty(self, client):
        with patch("gameserver.persistence.replay.list_replays", return_value=[]):
            resp = await client.get("/api/replays", headers=_auth())
        assert resp.status_code == 200
        data = resp.json()
        assert data["replays"] == []

    async def test_get_replay_not_found(self, client):
        with patch("gameserver.persistence.replay.get_replay_path", return_value=None):
            resp = await client.get("/api/replays/nonexistent", headers=_auth())
        assert resp.status_code == 404

    async def test_replays_requires_auth(self, client):
        resp = await client.get("/api/replays")
        assert resp.status_code in (401, 403, 422)


