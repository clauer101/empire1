"""REST API — FastAPI application for economy endpoints.

All economy request/response communication goes through REST.
Battle push events use WebSocket via /ws on the same port.

Usage::

    from gameserver.network.rest_api import create_app

    app = create_app(services)
    # Start with uvicorn as an asyncio task alongside the WS server
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, TYPE_CHECKING

from fastapi import Depends, FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from gameserver.network.jwt_auth import create_token, get_current_uid
from gameserver.network.rest_models import (
    ArmyCreateRequest,
    ArmyRenameRequest,
    AttackRequest,
    BuildRequest,
    BuyCritterSlotRequest,
    BuyTileRequest,
    BuyWaveRequest,
    CitizenDistribution,
    LoginRequest,
    LoginResponse,
    MapSaveBody,
    SignupRequest,
    SignupResponse,
    WaveChangeRequest,
)
from gameserver.models.messages import GameMessage

if TYPE_CHECKING:
    from gameserver.main import Services

log = logging.getLogger(__name__)


def _stub_message(**fields: Any) -> GameMessage:
    """Create a minimal GameMessage with extra attributes.

    The existing handlers read attributes via ``getattr(message, ...)``,
    so we just set them on a base GameMessage instance.
    """
    msg = GameMessage(type="rest", sender=0)
    for k, v in fields.items():
        object.__setattr__(msg, k, v)
    return msg


def create_app(services: "Services") -> FastAPI:
    """Factory: create and return a configured FastAPI application.

    The ``services`` reference is captured by closure so every endpoint
    can access game logic without global state.
    """
    from gameserver.network.handlers import (
        _build_empire_summary,
        _build_session_state,
        handle_buy_critter_slot_request,
        handle_buy_tile_request,
        handle_buy_wave_request,
        handle_change_army,
        handle_change_citizen,
        handle_change_wave,
        handle_citizen_upgrade,
        handle_item_request,
        handle_map_load_request,
        handle_map_save_request,
        handle_military_request,
        handle_new_army,
        handle_new_attack,
        handle_new_item,
        handle_new_wave,
        handle_summary_request,
    )

    app = FastAPI(title="E3 Game Server", version="1.0.0")

    # CORS — allow browser access from any origin (game is single-player-ish)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # =================================================================
    # Auth (unprotected)
    # =================================================================

    @app.post("/api/auth/login", response_model=LoginResponse)
    async def login(body: LoginRequest) -> dict[str, Any]:
        uid = await services.auth_service.login(body.username, body.password)
        if uid is not None:
            token = create_token(uid)
            session_state = _build_session_state(uid)
            empire = services.empire_service.get(uid)
            summary = _build_empire_summary(empire, uid) if empire else None
            return {
                "success": True,
                "uid": uid,
                "token": token,
                "reason": "",
                "session_state": session_state,
                "summary": summary,
            }
        return {
            "success": False,
            "uid": 0,
            "token": "",
            "reason": "Invalid username or password",
        }

    @app.post("/api/auth/signup", response_model=SignupResponse)
    async def signup(body: SignupRequest) -> dict[str, Any]:
        result = await services.auth_service.signup(
            body.username, body.password, body.email, body.empire_name,
        )
        if isinstance(result, int):
            # Create empire
            from gameserver.models.empire import Empire
            empire = Empire(
                uid=result,
                name=body.empire_name or f"{body.username}'s Empire",
                buildings={"INIT": 0.0},
            )
            services.empire_service.register(empire)
            return {"success": True, "uid": result, "reason": ""}
        return {"success": False, "uid": 0, "reason": result}

    # =================================================================
    # Empire queries (protected)
    # =================================================================

    @app.get("/api/empire/summary")
    async def get_summary(uid: int = Depends(get_current_uid)) -> dict[str, Any]:
        msg = _stub_message()
        resp = await handle_summary_request(msg, uid)
        return resp or {"error": "No data"}

    @app.get("/api/empire/items")
    async def get_items(uid: int = Depends(get_current_uid)) -> dict[str, Any]:
        msg = _stub_message()
        resp = await handle_item_request(msg, uid)
        return resp or {"error": "No data"}

    @app.get("/api/empire/military")
    async def get_military(uid: int = Depends(get_current_uid)) -> dict[str, Any]:
        msg = _stub_message()
        resp = await handle_military_request(msg, uid)
        return resp or {"error": "No data"}

    # =================================================================
    # Building / Research
    # =================================================================

    @app.post("/api/empire/build")
    async def build_item(body: BuildRequest, uid: int = Depends(get_current_uid)) -> dict[str, Any]:
        msg = _stub_message(iid=body.iid)
        resp = await handle_new_item(msg, uid)
        return resp or {"success": False, "error": "No response"}

    # =================================================================
    # Citizens
    # =================================================================

    @app.post("/api/empire/citizen/upgrade")
    async def citizen_upgrade(uid: int = Depends(get_current_uid)) -> dict[str, Any]:
        msg = _stub_message()
        resp = await handle_citizen_upgrade(msg, uid)
        return resp or {"success": False, "error": "No response"}

    @app.put("/api/empire/citizen")
    async def change_citizen(body: CitizenDistribution, uid: int = Depends(get_current_uid)) -> dict[str, Any]:
        msg = _stub_message(citizens=body.model_dump())
        resp = await handle_change_citizen(msg, uid)
        return resp or {"success": False, "error": "No response"}

    # =================================================================
    # Map
    # =================================================================

    @app.get("/api/map")
    async def load_map(uid: int = Depends(get_current_uid)) -> dict[str, Any]:
        msg = _stub_message()
        resp = await handle_map_load_request(msg, uid)
        return resp or {"tiles": {}}

    @app.put("/api/map")
    async def save_map(body: MapSaveBody, uid: int = Depends(get_current_uid)) -> dict[str, Any]:
        # MapSaveRequest needs special handling — the handler reads message.tiles
        from gameserver.models.messages import MapSaveRequest
        msg = MapSaveRequest(type="map_save_request", sender=uid, tiles=body.tiles)
        resp = await handle_map_save_request(msg, uid)
        return resp or {"success": False, "error": "No response"}

    @app.post("/api/map/buy-tile")
    async def buy_tile(body: BuyTileRequest, uid: int = Depends(get_current_uid)) -> dict[str, Any]:
        msg = _stub_message(q=body.q, r=body.r)
        resp = await handle_buy_tile_request(msg, uid)
        return resp or {"success": False, "error": "No response"}

    # =================================================================
    # Army
    # =================================================================

    @app.post("/api/army")
    async def create_army(body: ArmyCreateRequest, uid: int = Depends(get_current_uid)) -> dict[str, Any]:
        msg = _stub_message(name=body.name)
        resp = await handle_new_army(msg, uid)
        return resp or {"success": False, "error": "No response"}

    @app.put("/api/army/{aid}")
    async def rename_army(aid: int, body: ArmyRenameRequest, uid: int = Depends(get_current_uid)) -> dict[str, Any]:
        msg = _stub_message(aid=aid, name=body.name)
        resp = await handle_change_army(msg, uid)
        return resp or {"success": False, "error": "No response"}

    @app.post("/api/army/{aid}/wave")
    async def add_wave(aid: int, uid: int = Depends(get_current_uid)) -> dict[str, Any]:
        msg = _stub_message(aid=aid)
        resp = await handle_new_wave(msg, uid)
        return resp or {"success": False, "error": "No response"}

    @app.put("/api/army/{aid}/wave/{wave_number}")
    async def change_wave(aid: int, wave_number: int, body: WaveChangeRequest, uid: int = Depends(get_current_uid)) -> dict[str, Any]:
        msg = _stub_message(aid=aid, wave_number=wave_number, critter_iid=body.critter_iid, slots=body.slots)
        resp = await handle_change_wave(msg, uid)
        return resp or {"success": False, "error": "No response"}

    @app.post("/api/army/buy-wave")
    async def buy_wave(body: BuyWaveRequest, uid: int = Depends(get_current_uid)) -> dict[str, Any]:
        msg = _stub_message(aid=body.aid)
        resp = await handle_buy_wave_request(msg, uid)
        return resp or {"success": False, "error": "No response"}

    @app.post("/api/army/buy-critter-slot")
    async def buy_critter_slot(body: BuyCritterSlotRequest, uid: int = Depends(get_current_uid)) -> dict[str, Any]:
        msg = _stub_message(aid=body.aid, wave_number=body.wave_number)
        resp = await handle_buy_critter_slot_request(msg, uid)
        return resp or {"success": False, "error": "No response"}

    # =================================================================
    # Attack
    # =================================================================

    @app.post("/api/attack")
    async def attack(body: AttackRequest, uid: int = Depends(get_current_uid)) -> dict[str, Any]:
        msg = _stub_message(target_uid=body.target_uid, opponent_name=body.opponent_name, army_aid=body.army_aid)
        resp = await handle_new_attack(msg, uid)
        return resp or {"success": False, "error": "No response"}

    # =================================================================
    # WebSocket proxy — /ws on the same port as REST
    # =================================================================

    @app.websocket("/ws")
    async def websocket_endpoint(ws: WebSocket):
        """Bridge a FastAPI WebSocket to the game server's message router.

        This allows mobile clients to connect on the same port as REST,
        avoiding blocked secondary ports.  The game server's Session
        tracking is used so send_to / broadcast work normally.
        """
        # Authenticate via query param ?token=...
        token = ws.query_params.get("token")
        uid: int | None = None
        if token:
            try:
                from gameserver.network.jwt_auth import verify_token
                uid = verify_token(token)
            except Exception:
                await ws.close(code=4001, reason="Invalid token")
                return

        if uid is None:
            uid = services.server._next_guest_uid
            services.server._next_guest_uid -= 1

        await ws.accept()

        # Create a thin adapter so Server.send_to / broadcast work
        # with this FastAPI websocket as if it were a ``websockets`` connection.
        adapter = _FastAPIWSAdapter(ws)
        services.server.register_session(uid, adapter)

        # Send welcome message
        await ws.send_json({
            "type": "welcome",
            "temp_uid": uid,
            "via": "rest_ws",
        })

        log.info("REST-WS client connected: uid=%d", uid)

        try:
            while True:
                raw = await ws.receive_text()
                try:
                    data = json.loads(raw)
                except json.JSONDecodeError:
                    await ws.send_json({"type": "error", "message": "Invalid JSON"})
                    continue

                if not isinstance(data, dict):
                    await ws.send_json({"type": "error", "message": "Must be JSON object"})
                    continue

                request_id = data.get("request_id")
                msg_type = data.get("type", "")

                try:
                    response = await services.server._router.route(data, uid)
                except Exception as exc:
                    log.exception("REST-WS handler error: type=%s uid=%d", msg_type, uid)
                    err = {"type": "error", "message": str(exc)}
                    if request_id is not None:
                        err["request_id"] = request_id
                    await ws.send_json(err)
                    continue

                if response is not None:
                    if request_id is not None:
                        response["request_id"] = request_id
                    await ws.send_json(response)

                    # Re-register on auth upgrade
                    if msg_type == "auth_request" and response.get("success") and response.get("uid"):
                        real_uid = response["uid"]
                        services.server.unregister_session(adapter)
                        services.server.register_session(real_uid, adapter)
                        uid = real_uid

        except WebSocketDisconnect:
            log.info("REST-WS client disconnected: uid=%d", uid)
        except Exception as e:
            log.error("REST-WS error: uid=%d error=%s", uid, e)
        finally:
            services.server.unregister_session(adapter)

    log.info("REST API created with %d routes", len(app.routes))
    return app


class _FastAPIWSAdapter:
    """Minimal wrapper so FastAPI WebSocket looks like a ``websockets`` ServerConnection
    for the Server's send_to / broadcast methods."""

    def __init__(self, ws: WebSocket):
        self._ws = ws
        self._closed = False

    async def send(self, data: str) -> None:
        if not self._closed:
            try:
                await self._ws.send_text(data)
            except Exception:
                self._closed = True

    async def close(self, code: int = 1000, reason: str = "") -> None:
        if not self._closed:
            self._closed = True
            try:
                await self._ws.close(code=code, reason=reason)
            except Exception:
                pass

    @property
    def remote_address(self):
        client = self._ws.client
        return (client.host, client.port) if client else ("unknown", 0)
