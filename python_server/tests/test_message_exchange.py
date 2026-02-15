"""Tests for message exchange — Router, Handlers, and Server integration.

Verifies that messages are correctly parsed, routed to handlers,
and that handlers produce the expected responses. Also tests the
Server._handle_message() flow with mock WebSocket connections.
"""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass, field
from typing import Any, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from gameserver.models.empire import Empire
from gameserver.models.army import Army, SpyArmy
from gameserver.models.hex import HexCoord
from gameserver.models.structure import Structure
from gameserver.engine.empire_service import EmpireService
from gameserver.engine.attack_service import AttackService
from gameserver.engine.upgrade_provider import UpgradeProvider
from gameserver.network.router import Router
from gameserver.network import handlers
from gameserver.network.handlers import (
    register_all_handlers,
    handle_summary_request,
    handle_item_request,
    handle_military_request,
    handle_new_item,
    handle_new_structure,
    handle_delete_structure,
    handle_citizen_upgrade,
    handle_change_citizen,
    handle_new_army,
    handle_new_attack,
)
from gameserver.models.messages import parse_message, GameMessage
from gameserver.util.events import EventBus


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_services(empire: Optional[Empire] = None) -> Any:
    """Create a minimal Services-like object for handler tests."""
    event_bus = EventBus()
    upgrade_provider = UpgradeProvider()
    empire_service = EmpireService(upgrade_provider, event_bus)
    attack_service = AttackService(event_bus, empire_service=empire_service)
    if empire is not None:
        empire_service.register(empire)

    router = Router()

    # Build a lightweight Services mock with the required attributes
    svc = MagicMock()
    svc.event_bus = event_bus
    svc.upgrade_provider = upgrade_provider
    svc.empire_service = empire_service
    svc.attack_service = attack_service
    svc.router = router
    return svc


def _make_empire(uid: int = 100, name: str = "TestEmpire") -> Empire:
    """Create a test empire with some data."""
    return Empire(
        uid=uid,
        name=name,
        resources={"gold": 500.0, "culture": 1000.0, "life": 10.0},
        citizens={"merchant": 3, "scientist": 2, "artist": 1},
        buildings={"farm": 0.0, "library": 0.0, "workshop": 15.5},
        knowledge={"archery": 0.0, "alchemy": 30.0},
        structures={
            1: Structure(sid=1, iid="tower", position=HexCoord(2, 3), damage=10.0, range=3, reload_time_ms=1000.0, shot_speed=5.0),
        },
        armies=[Army(aid=1, uid=uid, name="Alpha")],
        effects={"speed": 1.5},
        artefacts=["golden_shield"],
        max_life=10.0,
    )


class FakeWebSocket:
    """Fake WebSocket connection for testing Server._handle_message()."""

    def __init__(self) -> None:
        self.sent: list[str] = []
        self.remote_address = ("127.0.0.1", 12345)
        self.closed = False
        self.close_code: Optional[int] = None
        self.close_reason: Optional[str] = None

    async def send(self, data: str) -> None:
        self.sent.append(data)

    async def close(self, code: int = 1000, reason: str = "") -> None:
        self.closed = True
        self.close_code = code
        self.close_reason = reason

    @property
    def last_sent_json(self) -> dict[str, Any]:
        assert self.sent, "No messages sent"
        return json.loads(self.sent[-1])

    @property
    def all_sent_json(self) -> list[dict[str, Any]]:
        return [json.loads(s) for s in self.sent]


# ===================================================================
# Router tests
# ===================================================================


class TestRouter:
    """Unit tests for the Router dispatch logic."""

    def test_register_and_list(self):
        router = Router()
        handler = AsyncMock(return_value=None)
        router.register("foo", handler)
        assert "foo" in router.registered_types

    @pytest.mark.asyncio
    async def test_route_calls_handler(self):
        router = Router()
        handler = AsyncMock(return_value={"type": "bar"})
        router.register("foo", handler)

        result = await router.route({"type": "foo", "sender": 1}, sender_uid=42)
        handler.assert_awaited_once()
        assert result == {"type": "bar"}

    @pytest.mark.asyncio
    async def test_route_passes_parsed_message(self):
        router = Router()
        captured = {}

        async def spy_handler(msg: GameMessage, uid: int) -> None:
            captured["msg"] = msg
            captured["uid"] = uid

        router.register("summary_request", spy_handler)
        await router.route({"type": "summary_request", "sender": 99}, sender_uid=7)

        assert captured["uid"] == 7
        assert captured["msg"].type == "summary_request"
        assert captured["msg"].sender == 99

    @pytest.mark.asyncio
    async def test_route_unknown_type_returns_none(self):
        router = Router()
        result = await router.route({"type": "nonexistent"}, sender_uid=1)
        assert result is None

    @pytest.mark.asyncio
    async def test_route_handler_returns_none(self):
        router = Router()
        router.register("ping", AsyncMock(return_value=None))
        result = await router.route({"type": "ping"}, sender_uid=1)
        assert result is None

    @pytest.mark.asyncio
    async def test_route_handler_returns_dict(self):
        router = Router()
        router.register("ping", AsyncMock(return_value={"type": "pong"}))
        result = await router.route({"type": "ping"}, sender_uid=1)
        assert result == {"type": "pong"}

    def test_register_overwrites(self):
        router = Router()
        h1 = AsyncMock()
        h2 = AsyncMock()
        router.register("x", h1)
        router.register("x", h2)
        assert router.registered_types.count("x") == 1


# ===================================================================
# Handler tests — summary_request
# ===================================================================


class TestHandleSummaryRequest:
    """Tests for the summary_request handler."""

    def setup_method(self):
        self.empire = _make_empire()
        self.svc = _make_services(self.empire)
        register_all_handlers(self.svc)

    @pytest.mark.asyncio
    async def test_returns_summary_response(self):
        msg = parse_message({"type": "summary_request", "sender": 100})
        result = await handle_summary_request(msg, sender_uid=100)

        assert result is not None
        assert result["type"] == "summary_response"
        assert result["uid"] == 100
        assert result["name"] == "TestEmpire"

    @pytest.mark.asyncio
    async def test_resources_are_rounded(self):
        msg = parse_message({"type": "summary_request", "sender": 100})
        result = await handle_summary_request(msg, sender_uid=100)

        assert result["resources"]["gold"] == 500.0
        assert result["resources"]["culture"] == 1000.0

    @pytest.mark.asyncio
    async def test_citizens_included(self):
        msg = parse_message({"type": "summary_request", "sender": 100})
        result = await handle_summary_request(msg, sender_uid=100)

        assert result["citizens"]["merchant"] == 3
        assert result["citizens"]["scientist"] == 2
        assert result["citizens"]["artist"] == 1

    @pytest.mark.asyncio
    async def test_completed_buildings(self):
        msg = parse_message({"type": "summary_request", "sender": 100})
        result = await handle_summary_request(msg, sender_uid=100)

        assert "farm" in result["completed_buildings"]
        assert "library" in result["completed_buildings"]
        assert "workshop" not in result["completed_buildings"]

    @pytest.mark.asyncio
    async def test_active_buildings(self):
        msg = parse_message({"type": "summary_request", "sender": 100})
        result = await handle_summary_request(msg, sender_uid=100)

        assert "workshop" in result["active_buildings"]
        assert result["active_buildings"]["workshop"] == 15.5

    @pytest.mark.asyncio
    async def test_completed_research(self):
        msg = parse_message({"type": "summary_request", "sender": 100})
        result = await handle_summary_request(msg, sender_uid=100)

        assert "archery" in result["completed_research"]
        assert "alchemy" not in result["completed_research"]

    @pytest.mark.asyncio
    async def test_active_research(self):
        msg = parse_message({"type": "summary_request", "sender": 100})
        result = await handle_summary_request(msg, sender_uid=100)

        assert "alchemy" in result["active_research"]
        assert result["active_research"]["alchemy"] == 30.0

    @pytest.mark.asyncio
    async def test_structures_serialized(self):
        msg = parse_message({"type": "summary_request", "sender": 100})
        result = await handle_summary_request(msg, sender_uid=100)

        assert len(result["structures"]) == 1
        s = result["structures"][0]
        assert s["sid"] == 1
        assert s["iid"] == "tower"
        assert s["position"] == {"q": 2, "r": 3}
        assert s["damage"] == 10.0
        assert s["range"] == 3

    @pytest.mark.asyncio
    async def test_army_count(self):
        msg = parse_message({"type": "summary_request", "sender": 100})
        result = await handle_summary_request(msg, sender_uid=100)

        assert result["army_count"] == 1
        assert result["spy_count"] == 0

    @pytest.mark.asyncio
    async def test_effects_and_artefacts(self):
        msg = parse_message({"type": "summary_request", "sender": 100})
        result = await handle_summary_request(msg, sender_uid=100)

        assert result["effects"] == {"speed": 1.5}
        assert result["artefacts"] == ["golden_shield"]

    @pytest.mark.asyncio
    async def test_max_life(self):
        msg = parse_message({"type": "summary_request", "sender": 100})
        result = await handle_summary_request(msg, sender_uid=100)
        assert result["max_life"] == 10.0

    @pytest.mark.asyncio
    async def test_unknown_uid_returns_error(self):
        msg = parse_message({"type": "summary_request", "sender": 999})
        result = await handle_summary_request(msg, sender_uid=999)

        assert result is not None
        assert "error" in result

    @pytest.mark.asyncio
    async def test_guest_uid_falls_back_to_sender(self):
        """When sender_uid < 0 (guest), handler uses message.sender field."""
        msg = parse_message({"type": "summary_request", "sender": 100})
        result = await handle_summary_request(msg, sender_uid=-1)

        assert result is not None
        assert result["uid"] == 100
        assert result["name"] == "TestEmpire"

    @pytest.mark.asyncio
    async def test_guest_uid_unknown_sender_returns_error(self):
        msg = parse_message({"type": "summary_request", "sender": 404})
        result = await handle_summary_request(msg, sender_uid=-1)

        assert result is not None
        assert "error" in result


# ===================================================================
# Handler tests — other handlers
# ===================================================================


class TestHandleItemRequest:
    def setup_method(self):
        self.svc = _make_services(_make_empire())
        register_all_handlers(self.svc)

    @pytest.mark.asyncio
    async def test_returns_item_response(self):
        msg = parse_message({"type": "item_request", "sender": 100})
        result = await handle_item_request(msg, sender_uid=100)
        assert result is not None
        assert result["type"] == "item_response"
        assert "buildings" in result
        assert "knowledge" in result


class TestHandleMilitaryRequest:
    def setup_method(self):
        self.empire = _make_empire()
        self.svc = _make_services(self.empire)
        register_all_handlers(self.svc)

    @pytest.mark.asyncio
    async def test_returns_military_response(self):
        msg = parse_message({"type": "military_request", "sender": 100})
        result = await handle_military_request(msg, sender_uid=100)
        assert result is not None
        assert result["type"] == "military_response"

    @pytest.mark.asyncio
    async def test_includes_armies(self):
        msg = parse_message({"type": "military_request", "sender": 100})
        result = await handle_military_request(msg, sender_uid=100)
        assert len(result["armies"]) == 1
        assert result["armies"][0]["aid"] == 1
        assert result["armies"][0]["name"] == "Alpha"

    @pytest.mark.asyncio
    async def test_unknown_uid_returns_error(self):
        msg = parse_message({"type": "military_request", "sender": 999})
        result = await handle_military_request(msg, sender_uid=999)
        assert "error" in result


class TestFireAndForgetHandlers:
    """Fire-and-forget handlers return None (no response to sender)."""

    def setup_method(self):
        self.svc = _make_services(_make_empire())
        register_all_handlers(self.svc)

    @pytest.mark.asyncio
    async def test_new_item_unknown_returns_error(self):
        msg = parse_message({"type": "new_item", "iid": "barracks", "sender": 100})
        result = await handle_new_item(msg, sender_uid=100)
        assert result is not None
        assert result["type"] == "build_response"
        assert result["success"] is False
        assert "Unknown item" in result["error"]

    @pytest.mark.asyncio
    async def test_new_structure_returns_none(self):
        msg = parse_message({"type": "new_structure", "iid": "tower", "hex_q": 1, "hex_r": 2, "sender": 100})
        result = await handle_new_structure(msg, sender_uid=100)
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_structure_returns_none(self):
        msg = parse_message({"type": "delete_structure", "sid": 5, "sender": 100})
        result = await handle_delete_structure(msg, sender_uid=100)
        assert result is None

    @pytest.mark.asyncio
    async def test_citizen_upgrade_returns_response(self):
        msg = parse_message({"type": "citizen_upgrade", "sender": 100})
        result = await handle_citizen_upgrade(msg, sender_uid=100)
        assert result is not None
        assert result["type"] == "citizen_upgrade_response"
        assert result["success"] is True
        assert "citizens" in result

    @pytest.mark.asyncio
    async def test_change_citizen_returns_response(self):
        msg = parse_message({"type": "change_citizen", "sender": 100, "citizens": {"merchant": 2}})
        result = await handle_change_citizen(msg, sender_uid=100)
        assert result is not None
        assert result["type"] == "change_citizen_response"
        assert result["success"] is True
        assert "citizens" in result

    @pytest.mark.asyncio
    async def test_new_army_returns_response(self):
        msg = parse_message({"type": "new_army", "sender": 100, "name": "Beta"})
        result = await handle_new_army(msg, sender_uid=100)
        assert result is not None
        assert result["type"] == "new_army_response"
        assert result["success"] is True
        assert "aid" in result

    @pytest.mark.asyncio
    async def test_new_attack_self_attack_fails(self):
        msg = parse_message({"type": "new_attack_request", "sender": 100, "target_uid": 100, "army_aid": 1})
        result = await handle_new_attack(msg, sender_uid=100)
        assert result is not None
        assert result["type"] == "attack_response"
        assert result["success"] is False
        assert "yourself" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_new_attack_unknown_defender_fails(self):
        msg = parse_message({"type": "new_attack_request", "sender": 100, "target_uid": 999, "army_aid": 1})
        result = await handle_new_attack(msg, sender_uid=100)
        assert result is not None
        assert result["type"] == "attack_response"
        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_new_attack_by_name_not_found(self):
        msg = parse_message({"type": "new_attack_request", "sender": 100, "opponent_name": "NonExistent"})
        result = await handle_new_attack(msg, sender_uid=100)
        assert result is not None
        assert result["type"] == "attack_response"
        assert result["success"] is False
        assert "not found" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_new_attack_no_target_fails(self):
        msg = parse_message({"type": "new_attack_request", "sender": 100})
        result = await handle_new_attack(msg, sender_uid=100)
        assert result is not None
        assert result["type"] == "attack_response"
        assert result["success"] is False


# ===================================================================
# Handler registration
# ===================================================================


class TestHandlerRegistration:
    def test_all_handlers_registered(self):
        svc = _make_services()
        register_all_handlers(svc)
        registered = svc.router.registered_types

        expected = [
            "summary_request",
            "item_request",
            "military_request",
            "new_item",
            "new_structure",
            "delete_structure",
            "citizen_upgrade",
            "change_citizen",
            "new_army",
            "new_attack_request",
        ]
        for msg_type in expected:
            assert msg_type in registered, f"Handler missing for {msg_type}"

    def test_register_sets_services(self):
        svc = _make_services()
        register_all_handlers(svc)
        assert handlers._services is svc


# ===================================================================
# Full Router + Handler integration
# ===================================================================


class TestRouterHandlerIntegration:
    """Tests that route() end-to-end calls the handler and returns data."""

    def setup_method(self):
        self.empire = _make_empire()
        self.svc = _make_services(self.empire)
        register_all_handlers(self.svc)

    @pytest.mark.asyncio
    async def test_summary_roundtrip(self):
        raw = {"type": "summary_request", "sender": 100}
        result = await self.svc.router.route(raw, sender_uid=100)
        assert result["type"] == "summary_response"
        assert result["uid"] == 100

    @pytest.mark.asyncio
    async def test_item_roundtrip(self):
        raw = {"type": "item_request", "sender": 100}
        result = await self.svc.router.route(raw, sender_uid=100)
        assert result["type"] == "item_response"

    @pytest.mark.asyncio
    async def test_military_roundtrip(self):
        raw = {"type": "military_request", "sender": 100}
        result = await self.svc.router.route(raw, sender_uid=100)
        assert result["type"] == "military_response"

    @pytest.mark.asyncio
    async def test_fire_and_forget_roundtrip(self):
        """new_item with unknown iid returns error (no longer fire-and-forget stub)."""
        raw = {"type": "new_item", "iid": "workshop", "sender": 100}
        result = await self.svc.router.route(raw, sender_uid=100)
        # workshop already in empire → error
        assert result is not None
        assert result["type"] == "build_response"
        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_unregistered_type(self):
        raw = {"type": "unknown_msg_type", "sender": 100}
        result = await self.svc.router.route(raw, sender_uid=100)
        assert result is None


# ===================================================================
# Server._handle_message() tests using FakeWebSocket
# ===================================================================


class TestServerHandleMessage:
    """Tests for Server._handle_message() — JSON parsing + routing + response."""

    def setup_method(self):
        self.empire = _make_empire()
        self.svc = _make_services(self.empire)
        register_all_handlers(self.svc)
        from gameserver.network.server import Server
        self.server = Server(self.svc.router, host="127.0.0.1", port=0)
        self.ws = FakeWebSocket()
        # Register the fake ws as uid=100
        self.server._connections[100] = self.ws
        self.server._ws_to_uid[id(self.ws)] = 100

    @pytest.mark.asyncio
    async def test_valid_summary_request(self):
        raw = json.dumps({"type": "summary_request", "sender": 100})
        await self.server._handle_message(self.ws, raw)

        resp = self.ws.last_sent_json
        assert resp["type"] == "summary_response"
        assert resp["uid"] == 100
        assert resp["name"] == "TestEmpire"

    @pytest.mark.asyncio
    async def test_request_id_preserved(self):
        raw = json.dumps({
            "type": "summary_request",
            "sender": 100,
            "request_id": "abc-123",
        })
        await self.server._handle_message(self.ws, raw)

        resp = self.ws.last_sent_json
        assert resp["request_id"] == "abc-123"

    @pytest.mark.asyncio
    async def test_request_id_not_added_when_absent(self):
        raw = json.dumps({"type": "summary_request", "sender": 100})
        await self.server._handle_message(self.ws, raw)

        resp = self.ws.last_sent_json
        assert "request_id" not in resp

    @pytest.mark.asyncio
    async def test_invalid_json_returns_error(self):
        await self.server._handle_message(self.ws, "not valid json {{{")

        resp = self.ws.last_sent_json
        assert resp["type"] == "error"
        assert "Invalid JSON" in resp["message"]

    @pytest.mark.asyncio
    async def test_non_dict_json_returns_error(self):
        await self.server._handle_message(self.ws, '"just a string"')

        resp = self.ws.last_sent_json
        assert resp["type"] == "error"
        assert "JSON object" in resp["message"]

    @pytest.mark.asyncio
    async def test_json_array_returns_error(self):
        await self.server._handle_message(self.ws, '[1, 2, 3]')

        resp = self.ws.last_sent_json
        assert resp["type"] == "error"
        assert "JSON object" in resp["message"]

    @pytest.mark.asyncio
    async def test_bytes_input_decoded(self):
        raw = json.dumps({"type": "summary_request", "sender": 100}).encode("utf-8")
        await self.server._handle_message(self.ws, raw)

        resp = self.ws.last_sent_json
        assert resp["type"] == "summary_response"

    @pytest.mark.asyncio
    async def test_build_existing_item_returns_error(self):
        """Building an already started/completed item returns an error response."""
        raw = json.dumps({"type": "new_item", "iid": "farm", "sender": 100})
        await self.server._handle_message(self.ws, raw)

        assert len(self.ws.sent) == 1
        resp = self.ws.last_sent_json
        assert resp["type"] == "build_response"
        assert resp["success"] is False

    @pytest.mark.asyncio
    async def test_unknown_type_no_response(self):
        raw = json.dumps({"type": "completely_unknown", "sender": 100})
        await self.server._handle_message(self.ws, raw)

        assert len(self.ws.sent) == 0

    @pytest.mark.asyncio
    async def test_handler_exception_returns_error(self):
        """If a handler raises, the server catches and returns an error."""
        async def boom(msg, uid):
            raise ValueError("test explosion")

        self.svc.router.register("boom_type", boom)
        raw = json.dumps({"type": "boom_type", "sender": 100})
        await self.server._handle_message(self.ws, raw)

        resp = self.ws.last_sent_json
        assert resp["type"] == "error"
        assert "test explosion" in resp["message"]

    @pytest.mark.asyncio
    async def test_handler_exception_preserves_request_id(self):
        async def boom(msg, uid):
            raise RuntimeError("kaboom")

        self.svc.router.register("boom_type", boom)
        raw = json.dumps({
            "type": "boom_type",
            "sender": 100,
            "request_id": "req-99",
        })
        await self.server._handle_message(self.ws, raw)

        resp = self.ws.last_sent_json
        assert resp["type"] == "error"
        assert resp["request_id"] == "req-99"

    @pytest.mark.asyncio
    async def test_military_request_roundtrip(self):
        raw = json.dumps({"type": "military_request", "sender": 100})
        await self.server._handle_message(self.ws, raw)

        resp = self.ws.last_sent_json
        assert resp["type"] == "military_response"
        assert len(resp["armies"]) == 1

    @pytest.mark.asyncio
    async def test_item_request_roundtrip(self):
        raw = json.dumps({"type": "item_request", "sender": 100})
        await self.server._handle_message(self.ws, raw)

        resp = self.ws.last_sent_json
        assert resp["type"] == "item_response"


# ===================================================================
# Server session management
# ===================================================================


class TestServerSessions:
    """Tests for Server session tracking."""

    def setup_method(self):
        router = Router()
        from gameserver.network.server import Server
        self.server = Server(router, host="127.0.0.1", port=0)

    def test_register_and_get_uid(self):
        ws = FakeWebSocket()
        self.server.register_session(42, ws)
        assert self.server.get_uid(ws) == 42
        assert 42 in self.server.connected_uids

    def test_unregister_returns_uid(self):
        ws = FakeWebSocket()
        self.server.register_session(42, ws)
        uid = self.server.unregister_session(ws)
        assert uid == 42
        assert 42 not in self.server.connected_uids

    def test_unregister_unknown_returns_none(self):
        ws = FakeWebSocket()
        uid = self.server.unregister_session(ws)
        assert uid is None

    def test_get_uid_unknown_returns_none(self):
        ws = FakeWebSocket()
        assert self.server.get_uid(ws) is None

    def test_connection_count(self):
        assert self.server.connection_count == 0
        ws1 = FakeWebSocket()
        ws2 = FakeWebSocket()
        self.server.register_session(1, ws1)
        self.server.register_session(2, ws2)
        assert self.server.connection_count == 2

    def test_connected_uids_sorted(self):
        ws1 = FakeWebSocket()
        ws2 = FakeWebSocket()
        ws3 = FakeWebSocket()
        self.server.register_session(30, ws1)
        self.server.register_session(10, ws2)
        self.server.register_session(20, ws3)
        assert self.server.connected_uids == [10, 20, 30]

    def test_guest_uids_are_negative(self):
        """Guest UIDs start at -1 and decrement."""
        assert self.server._next_guest_uid == -1
        # Simulate two guests connecting
        ws1 = FakeWebSocket()
        ws2 = FakeWebSocket()
        uid1 = self.server._next_guest_uid
        self.server._next_guest_uid -= 1
        uid2 = self.server._next_guest_uid
        self.server._next_guest_uid -= 1
        assert uid1 == -1
        assert uid2 == -2

    def test_session_upgrade_cleans_guest_uid(self):
        """When a guest session upgrades to a real UID, the old guest
        mapping should be removed from _connections."""
        ws = FakeWebSocket()
        self.server.register_session(-1, ws)  # guest
        assert self.server.get_uid(ws) == -1
        assert -1 in self.server.connected_uids

        # Upgrade to real uid
        self.server.register_session(42, ws)
        assert self.server.get_uid(ws) == 42
        # Guest entry should be cleaned up
        assert -1 not in self.server.connected_uids
        assert 42 in self.server.connected_uids

    def test_superseded_unregister_does_not_remove_new_session(self):
        """The core multi-device bug: when device A supersedes device B,
        device B's unregister_session must NOT remove device A's mapping.

        Sequence:
        1. iOS connects as guest -1, upgrades to uid=2
        2. Desktop connects as guest -2, upgrades to uid=2 (supersedes iOS)
        3. iOS's finally block calls unregister_session(ws_ios)
        4. uid=2 must still map to ws_desktop (NOT be removed)
        """
        ws_ios = FakeWebSocket()
        ws_desktop = FakeWebSocket()

        # iOS logs in as uid=2
        self.server.register_session(-1, ws_ios)
        self.server.register_session(2, ws_ios)
        assert self.server.get_uid(ws_ios) == 2

        # Desktop logs in as uid=2 → supersedes iOS
        self.server.register_session(-2, ws_desktop)
        self.server.register_session(2, ws_desktop)
        assert self.server.get_uid(ws_desktop) == 2

        # iOS disconnects — unregister must NOT kill desktop's session
        removed = self.server.unregister_session(ws_ios)
        # The UID returned should still be 2 (from the ws_to_uid map)
        # but _connections[2] must still point to ws_desktop
        assert 2 in self.server.connected_uids
        assert self.server.get_uid(ws_desktop) == 2

        # Desktop can still send/receive
        assert self.server.connection_count >= 1

    def test_multi_device_rapid_supersede(self):
        """Rapid back-and-forth supersedes (A→B→A) should leave the last
        connection standing."""
        ws_a = FakeWebSocket()
        ws_b = FakeWebSocket()
        ws_a2 = FakeWebSocket()

        # A logs in
        self.server.register_session(-1, ws_a)
        self.server.register_session(5, ws_a)
        # B logs in, supersedes A
        self.server.register_session(-2, ws_b)
        self.server.register_session(5, ws_b)
        # A reconnects, supersedes B
        self.server.register_session(-3, ws_a2)
        self.server.register_session(5, ws_a2)

        # Old connections unregister (order doesn't matter)
        self.server.unregister_session(ws_a)
        self.server.unregister_session(ws_b)

        # Only ws_a2 should hold uid=5
        assert self.server.get_uid(ws_a2) == 5
        assert 5 in self.server.connected_uids
        assert self.server.connection_count == 1


# ===================================================================
# Server send_to / broadcast
# ===================================================================


class TestServerSending:
    """Tests for send_to and broadcast methods."""

    def setup_method(self):
        router = Router()
        from gameserver.network.server import Server
        self.server = Server(router, host="127.0.0.1", port=0)

    @pytest.mark.asyncio
    async def test_send_to_connected(self):
        ws = FakeWebSocket()
        self.server.register_session(1, ws)
        ok = await self.server.send_to(1, {"type": "ping"})
        assert ok is True
        assert ws.last_sent_json == {"type": "ping"}

    @pytest.mark.asyncio
    async def test_send_to_unknown_uid(self):
        ok = await self.server.send_to(999, {"type": "ping"})
        assert ok is False

    @pytest.mark.asyncio
    async def test_broadcast(self):
        ws1 = FakeWebSocket()
        ws2 = FakeWebSocket()
        ws3 = FakeWebSocket()
        self.server.register_session(1, ws1)
        self.server.register_session(2, ws2)
        self.server.register_session(3, ws3)

        count = await self.server.broadcast({1, 3}, {"type": "alert"})
        assert count == 2
        assert ws1.last_sent_json == {"type": "alert"}
        assert len(ws2.sent) == 0
        assert ws3.last_sent_json == {"type": "alert"}

    @pytest.mark.asyncio
    async def test_broadcast_all(self):
        ws1 = FakeWebSocket()
        ws2 = FakeWebSocket()
        self.server.register_session(1, ws1)
        self.server.register_session(2, ws2)

        count = await self.server.broadcast_all({"type": "tick"})
        assert count == 2

    @pytest.mark.asyncio
    async def test_broadcast_skips_unknown_uids(self):
        ws1 = FakeWebSocket()
        self.server.register_session(1, ws1)

        count = await self.server.broadcast({1, 99}, {"type": "alert"})
        assert count == 1


# ===================================================================
# Empire state in response — edge cases
# ===================================================================


class TestSummaryEdgeCases:
    """Edge-case tests for the summary_request handler."""

    def setup_method(self):
        self.svc = _make_services()
        register_all_handlers(self.svc)

    @pytest.mark.asyncio
    async def test_empty_empire(self):
        """An empire with defaults should still produce a valid response."""
        empire = Empire(uid=50, name="Minimal")
        self.svc.empire_service.register(empire)

        msg = parse_message({"type": "summary_request", "sender": 50})
        result = await handle_summary_request(msg, sender_uid=50)

        assert result["uid"] == 50
        assert result["name"] == "Minimal"
        assert result["completed_buildings"] == []
        assert result["active_buildings"] == {}
        assert result["completed_research"] == []
        assert result["active_research"] == {}
        assert result["structures"] == []
        assert result["army_count"] == 0
        assert result["spy_count"] == 0
        assert result["artefacts"] == []
        assert result["effects"] == {}

    @pytest.mark.asyncio
    async def test_multiple_empires_isolated(self):
        """Querying one empire should not return data from another."""
        e1 = Empire(uid=1, name="Empire1", resources={"gold": 100.0})
        e2 = Empire(uid=2, name="Empire2", resources={"gold": 999.0})
        self.svc.empire_service.register(e1)
        self.svc.empire_service.register(e2)

        msg1 = parse_message({"type": "summary_request", "sender": 1})
        r1 = await handle_summary_request(msg1, sender_uid=1)
        msg2 = parse_message({"type": "summary_request", "sender": 2})
        r2 = await handle_summary_request(msg2, sender_uid=2)

        assert r1["name"] == "Empire1"
        assert r1["resources"]["gold"] == 100.0
        assert r2["name"] == "Empire2"
        assert r2["resources"]["gold"] == 999.0

    @pytest.mark.asyncio
    async def test_resource_rounding(self):
        """Resources with many decimals should be rounded to 2 places."""
        empire = Empire(uid=7, name="RoundTest", resources={
            "gold": 123.456789,
            "culture": 0.001,
        })
        self.svc.empire_service.register(empire)

        msg = parse_message({"type": "summary_request", "sender": 7})
        result = await handle_summary_request(msg, sender_uid=7)

        assert result["resources"]["gold"] == 123.46
        assert result["resources"]["culture"] == 0.0


# ===================================================================
# Multiple messages in sequence
# ===================================================================


class TestMessageSequence:
    """Test sending multiple messages in sequence through Server._handle_message."""

    def setup_method(self):
        empire = _make_empire()
        self.svc = _make_services(empire)
        register_all_handlers(self.svc)
        from gameserver.network.server import Server
        self.server = Server(self.svc.router, host="127.0.0.1", port=0)
        self.ws = FakeWebSocket()
        self.server._connections[100] = self.ws
        self.server._ws_to_uid[id(self.ws)] = 100

    @pytest.mark.asyncio
    async def test_multiple_requests_in_sequence(self):
        """Sending multiple requests should each produce its own response."""
        # First: summary
        await self.server._handle_message(
            self.ws,
            json.dumps({"type": "summary_request", "sender": 100, "request_id": "r1"}),
        )
        # Second: item
        await self.server._handle_message(
            self.ws,
            json.dumps({"type": "item_request", "sender": 100, "request_id": "r2"}),
        )
        # Third: military
        await self.server._handle_message(
            self.ws,
            json.dumps({"type": "military_request", "sender": 100, "request_id": "r3"}),
        )

        responses = self.ws.all_sent_json
        assert len(responses) == 3
        assert responses[0]["type"] == "summary_response"
        assert responses[0]["request_id"] == "r1"
        assert responses[1]["type"] == "item_response"
        assert responses[1]["request_id"] == "r2"
        assert responses[2]["type"] == "military_response"
        assert responses[2]["request_id"] == "r3"

    @pytest.mark.asyncio
    async def test_error_does_not_break_subsequent_messages(self):
        """After an error, the next message should still be processed."""
        # Send invalid JSON
        await self.server._handle_message(self.ws, "broken!!!")
        # Send valid request
        await self.server._handle_message(
            self.ws,
            json.dumps({"type": "summary_request", "sender": 100}),
        )

        responses = self.ws.all_sent_json
        assert len(responses) == 2
        assert responses[0]["type"] == "error"
        assert responses[1]["type"] == "summary_response"

    @pytest.mark.asyncio
    async def test_mixed_response_and_fire_and_forget(self):
        """Mix of response-generating and fire-and-forget messages."""
        await self.server._handle_message(
            self.ws,
            json.dumps({"type": "summary_request", "sender": 100}),
        )
        await self.server._handle_message(
            self.ws,
            json.dumps({"type": "new_item", "iid": "farm", "sender": 100}),
        )
        await self.server._handle_message(
            self.ws,
            json.dumps({"type": "item_request", "sender": 100}),
        )

        responses = self.ws.all_sent_json
        # summary_response, build_response (farm already built), item_response
        assert len(responses) == 3
        assert responses[0]["type"] == "summary_response"
        assert responses[1]["type"] == "build_response"
        assert responses[2]["type"] == "item_response"
