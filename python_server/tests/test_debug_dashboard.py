"""Tests for the debug dashboard — monitor snapshot + HTTP server."""

from __future__ import annotations

import asyncio
import json
from typing import Optional
from unittest.mock import MagicMock

import pytest

from gameserver.debug.monitor import collect_snapshot, _fmt_duration
from gameserver.debug.dashboard import DebugDashboard
from gameserver.engine.empire_service import EmpireService
from gameserver.engine.game_loop import GameLoop
from gameserver.engine.upgrade_provider import UpgradeProvider
from gameserver.models.empire import Empire
from gameserver.network.router import Router
from gameserver.network.server import Server
from gameserver.util.events import EventBus


# -------------------------------------------------------------------
# Helper — build a minimal Services dataclass with real objects
# -------------------------------------------------------------------

def _make_services(**overrides):
    """Create a Services-like object with real lightweight instances."""
    from gameserver.main import Services

    event_bus = EventBus()
    upgrade_provider = UpgradeProvider()
    attack_service = MagicMock()
    statistics = MagicMock()
    empire_service = EmpireService(upgrade_provider, event_bus)
    game_loop = GameLoop(event_bus, empire_service, attack_service, statistics)
    router = Router()
    server = Server(router, host="127.0.0.1", port=0)

    defaults = dict(
        event_bus=event_bus,
        upgrade_provider=upgrade_provider,
        empire_service=empire_service,
        battle_service=MagicMock(),
        attack_service=attack_service,
        army_service=MagicMock(),
        ai_service=MagicMock(),
        statistics=statistics,
        game_loop=game_loop,
        auth_service=MagicMock(),
        router=router,
        server=server,
        database=None,
        debug_dashboard=None,
    )
    defaults.update(overrides)
    return Services(**defaults)


# ===================================================================
# Monitor: _fmt_duration
# ===================================================================


class TestFmtDuration:
    def test_seconds_only(self):
        assert _fmt_duration(0) == "0s"
        assert _fmt_duration(42) == "42s"
        assert _fmt_duration(59.9) == "59s"

    def test_minutes_seconds(self):
        assert _fmt_duration(60) == "1m 00s"
        assert _fmt_duration(125) == "2m 05s"
        assert _fmt_duration(3599) == "59m 59s"

    def test_hours_minutes_seconds(self):
        assert _fmt_duration(3600) == "1h 00m 00s"
        assert _fmt_duration(3661) == "1h 01m 01s"
        assert _fmt_duration(86399) == "23h 59m 59s"


# ===================================================================
# Monitor: collect_snapshot — structure and keys
# ===================================================================


class TestCollectSnapshot:
    def test_snapshot_has_all_toplevel_keys(self):
        services = _make_services()
        snap = collect_snapshot(services)
        expected_keys = {
            "server", "game_loop", "event_bus",
            "empires", "battles", "attacks",
            "upgrade_provider", "process",
        }
        assert expected_keys == set(snap.keys())

    def test_snapshot_is_json_serialisable(self):
        services = _make_services()
        snap = collect_snapshot(services)
        # Must not raise
        text = json.dumps(snap, default=str)
        assert isinstance(text, str)
        roundtrip = json.loads(text)
        assert set(roundtrip.keys()) == set(snap.keys())

    def test_game_loop_section_before_run(self):
        services = _make_services()
        snap = collect_snapshot(services)
        gl = snap["game_loop"]
        assert gl["running"] is False
        assert gl["tick_count"] == 0
        assert gl["uptime_s"] == 0.0

    def test_game_loop_section_after_ticks(self):
        services = _make_services()
        gl = services.game_loop
        # Simulate a few ticks manually
        gl._running = True
        gl.started_at = 100.0
        gl.tick_count = 5
        gl.last_tick_dt = 1.002
        gl.last_tick_duration_ms = 0.12
        gl.avg_tick_duration_ms = 0.1

        snap = collect_snapshot(services)
        info = snap["game_loop"]
        assert info["running"] is True
        assert info["tick_count"] == 5
        assert info["last_tick_dt_ms"] == 1002.0
        assert info["last_tick_work_ms"] == 0.12
        assert info["avg_tick_work_ms"] == 0.1

    def test_server_section(self):
        services = _make_services()
        snap = collect_snapshot(services)
        srv = snap["server"]
        assert srv["host"] == "127.0.0.1"
        assert srv["connections"] == 0
        assert srv["connected_uids"] == []

    def test_event_bus_section_empty(self):
        services = _make_services()
        snap = collect_snapshot(services)
        bus = snap["event_bus"]
        assert bus["registered_events"] == 0
        assert bus["total_handlers"] == 0

    def test_event_bus_section_with_handlers(self):
        services = _make_services()
        from gameserver.util.events import CritterDied, BattleFinished
        services.event_bus.on(CritterDied, lambda e: None)
        services.event_bus.on(CritterDied, lambda e: None)
        services.event_bus.on(BattleFinished, lambda e: None)

        snap = collect_snapshot(services)
        bus = snap["event_bus"]
        assert bus["registered_events"] == 2
        assert bus["total_handlers"] == 3
        assert bus["events"]["CritterDied"] == 2
        assert bus["events"]["BattleFinished"] == 1

    def test_process_section_has_pid(self):
        import os
        services = _make_services()
        snap = collect_snapshot(services)
        assert snap["process"]["pid"] == os.getpid()
        assert "memory_mb" in snap["process"]
        assert "time" in snap["process"]

    def test_upgrade_provider_empty(self):
        services = _make_services()
        snap = collect_snapshot(services)
        up = snap["upgrade_provider"]
        assert up["items_loaded"] == 0

    def test_battles_section_empty(self):
        services = _make_services()
        snap = collect_snapshot(services)
        assert snap["battles"]["active"] == 0
        assert snap["battles"]["details"] == []

    def test_attacks_section_empty(self):
        services = _make_services()
        snap = collect_snapshot(services)
        assert snap["attacks"]["active"] == 0
        assert snap["attacks"]["details"] == []


# ===================================================================
# Monitor: empire snapshot
# ===================================================================


class TestEmpireSnapshot:
    def test_no_empires(self):
        services = _make_services()
        snap = collect_snapshot(services)
        assert snap["empires"]["count"] == 0
        assert snap["empires"]["details"] == {}

    def test_single_empire(self):
        services = _make_services()
        emp = Empire(
            uid=42,
            name="TestReich",
            resources={"gold": 100.5, "culture": 20.3, "life": 8.0},
            citizens={"merchant": 3, "scientist": 1, "artist": 0},
            buildings={"barracks": 15.0, "wall": 0.0},
            knowledge={"fire": 10.0},
            max_life=10.0,
        )
        services.empire_service.register(emp)

        snap = collect_snapshot(services)
        assert snap["empires"]["count"] == 1

        detail = snap["empires"]["details"]["42"]
        assert detail["name"] == "TestReich"
        assert detail["resources"]["gold"] == 100.5
        assert detail["resources"]["culture"] == 20.3
        assert detail["life"] == 8.0
        assert detail["max_life"] == 10.0
        assert detail["citizens"]["merchant"] == 3
        assert detail["active_builds"] == 1  # only barracks > 0
        assert detail["buildings"]["barracks"] == 15.0
        assert detail["buildings"]["wall"] == 0.0
        assert detail["active_research"] == 1
        assert detail["knowledge"]["fire"] == 10.0
        assert detail["structures"] == 0
        assert detail["armies"] == 0
        assert detail["artefacts"] == 0

    def test_multiple_empires(self):
        services = _make_services()
        services.empire_service.register(Empire(uid=1, name="Alpha"))
        services.empire_service.register(Empire(uid=2, name="Beta"))
        services.empire_service.register(Empire(uid=3, name="Gamma"))

        snap = collect_snapshot(services)
        assert snap["empires"]["count"] == 3
        assert set(snap["empires"]["details"].keys()) == {"1", "2", "3"}

    def test_empire_resources_rounded(self):
        services = _make_services()
        emp = Empire(uid=1, resources={"gold": 1.23456789, "culture": 0.0, "life": 5.0})
        services.empire_service.register(emp)

        snap = collect_snapshot(services)
        res = snap["empires"]["details"]["1"]["resources"]
        assert res["gold"] == 1.23  # rounded to 2 decimal places


# ===================================================================
# Monitor: None services (graceful degradation)
# ===================================================================


class TestNoneServices:
    """Snapshot collector must not crash when services are None."""

    def test_all_none(self):
        from gameserver.main import Services
        services = Services()  # all fields default to None
        snap = collect_snapshot(services)
        assert snap["server"] == {"status": "not created"}
        assert snap["game_loop"] == {"status": "not created"}
        assert snap["event_bus"] == {"status": "not created"}
        assert snap["empires"] == {"status": "not created"}
        assert "process" in snap  # process always works


# ===================================================================
# Dashboard HTTP server: routes
# ===================================================================


class TestDashboardHTTP:
    """Integration tests for the async HTTP dashboard server."""

    @pytest.fixture
    async def dashboard(self):
        """Start a dashboard on a random port, yield (dashboard, port), stop."""
        services = _make_services()
        # Register a test empire so the snapshot has data
        services.empire_service.register(
            Empire(uid=99, name="HTTPTestEmpire", resources={"gold": 42.0, "culture": 0.0, "life": 10.0})
        )
        # Port 0 = OS picks a free port
        db = DebugDashboard(services, host="127.0.0.1", port=0)
        await db.start()
        port = db._server.sockets[0].getsockname()[1]
        yield db, port
        await db.stop()

    async def _http_get(self, port: int, path: str) -> tuple:
        """Minimal HTTP GET client. Returns (status_code, headers_str, body_bytes)."""
        reader, writer = await asyncio.open_connection("127.0.0.1", port)
        request = f"GET {path} HTTP/1.1\r\nHost: 127.0.0.1:{port}\r\n\r\n"
        writer.write(request.encode())
        await writer.drain()

        # Read response
        data = b""
        try:
            while True:
                chunk = await asyncio.wait_for(reader.read(65536), timeout=3.0)
                if not chunk:
                    break
                data += chunk
        except asyncio.TimeoutError:
            pass

        writer.close()
        try:
            await writer.wait_closed()
        except Exception:
            pass

        # Parse status code
        header_end = data.find(b"\r\n\r\n")
        headers = data[:header_end].decode("utf-8", errors="replace")
        body = data[header_end + 4:]
        status_line = headers.split("\r\n")[0]
        status_code = int(status_line.split(" ")[1])
        return status_code, headers, body

    @pytest.mark.asyncio
    async def test_root_returns_html(self, dashboard):
        db, port = dashboard
        status, headers, body = await self._http_get(port, "/")
        assert status == 200
        assert "text/html" in headers
        assert b"GameServer Debug" in body
        assert b"</html>" in body

    @pytest.mark.asyncio
    async def test_api_state_returns_json(self, dashboard):
        db, port = dashboard
        status, headers, body = await self._http_get(port, "/api/state")
        assert status == 200
        assert "application/json" in headers
        snap = json.loads(body)
        assert "game_loop" in snap
        assert "empires" in snap
        assert snap["empires"]["count"] == 1
        assert snap["empires"]["details"]["99"]["name"] == "HTTPTestEmpire"

    @pytest.mark.asyncio
    async def test_api_state_is_valid_json(self, dashboard):
        db, port = dashboard
        status, _, body = await self._http_get(port, "/api/state")
        assert status == 200
        snap = json.loads(body)
        # Re-serialise to prove full roundtrip
        text = json.dumps(snap)
        assert json.loads(text) == snap

    @pytest.mark.asyncio
    async def test_404_on_unknown_path(self, dashboard):
        db, port = dashboard
        status, _, body = await self._http_get(port, "/does/not/exist")
        assert status == 404

    @pytest.mark.asyncio
    async def test_index_html_alias(self, dashboard):
        db, port = dashboard
        status, headers, body = await self._http_get(port, "/index.html")
        assert status == 200
        assert b"GameServer Debug" in body

    @pytest.mark.asyncio
    async def test_server_start_stop(self):
        """Dashboard can be started and stopped cleanly."""
        services = _make_services()
        db = DebugDashboard(services, host="127.0.0.1", port=0)
        await db.start()
        assert db._server is not None
        assert db._server.is_serving()
        await db.stop()
        assert not db._server.is_serving()

    @pytest.mark.asyncio
    async def test_concurrent_requests(self, dashboard):
        """Multiple concurrent requests don't crash the server."""
        db, port = dashboard
        tasks = [self._http_get(port, "/api/state") for _ in range(5)]
        results = await asyncio.gather(*tasks)
        for status, _, body in results:
            assert status == 200
            snap = json.loads(body)
            assert "game_loop" in snap
