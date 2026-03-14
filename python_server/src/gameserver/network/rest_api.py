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

from fastapi import Depends, FastAPI, HTTPException, WebSocket, WebSocketDisconnect
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
    SendMessageRequest,
    BattleFeedbackRequest,
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
            from gameserver.network.handlers import _create_empire_for_new_user
            _create_empire_for_new_user(result, body.username, body.empire_name)
            return {"success": True, "uid": result, "reason": ""}
        return {"success": False, "uid": 0, "reason": result}

    # =================================================================
    # Empire queries (protected)
    # =================================================================

    @app.get("/api/empire/summary")
    async def get_summary(uid: int = Depends(get_current_uid)) -> dict[str, Any]:
        msg = _stub_message()
        resp = await handle_summary_request(msg, uid)
        if resp and services.message_store:
            resp["unread_messages"] = services.message_store.unread_count(uid)
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

    @app.get("/api/empires")
    async def list_empires(uid: int = Depends(get_current_uid)) -> dict[str, Any]:
        """Return all known empires sorted by culture points descending."""
        # Build uid → username map from DB
        uid_to_user: dict[int, str] = {}
        if services.database is not None:
            for row in await services.database.list_users():
                uid_to_user[row["uid"]] = row["username"]
        empires = []
        for empire in services.empire_service.all_empires.values():
            if empire.uid == 0:  # skip AI empire
                continue
            empires.append({
                "uid": empire.uid,
                "name": empire.name,
                "username": uid_to_user.get(empire.uid, ""),
                "culture": round(empire.resources.get("culture", 0.0), 1),
                "is_self": empire.uid == uid,
            })
        empires.sort(key=lambda e: e["culture"], reverse=True)
        return {"empires": empires}

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

    @app.post("/api/attack/{attack_id}/skip-siege")
    async def skip_siege(attack_id: int, uid: int = Depends(get_current_uid)) -> dict[str, Any]:
        """Immediately end the siege phase — only callable by the defender."""
        result = services.attack_service.skip_siege(attack_id, uid)
        if isinstance(result, str):
            return {"success": False, "error": result}
        return {"success": True, "attack_id": result.attack_id, "phase": result.phase.value}

    # =================================================================
    # Messages
    # =================================================================

    @app.post("/api/messages")
    async def send_message(body: SendMessageRequest, uid: int = Depends(get_current_uid)) -> dict[str, Any]:
        """Send a message to another player."""
        if not body.body.strip():
            return {"success": False, "error": "Message body cannot be empty"}
        if body.to_uid == uid:
            return {"success": False, "error": "Cannot send message to yourself"}
        msg = services.message_store.send(from_uid=uid, to_uid=body.to_uid, body=body.body.strip())
        return {"success": True, "message": msg}

    @app.get("/api/messages")
    async def get_messages(uid: int = Depends(get_current_uid)) -> dict[str, Any]:
        """Return inbox + sent messages for the current player."""
        # 1. Empire names from live game state (most accurate)
        uid_to_name: dict[int, str] = {
            e.uid: e.name
            for e in services.empire_service.all_empires.values()
        }
        # 2. Fill gaps with DB usernames / empire_name
        if services.database is not None:
            for row in await services.database.list_users():
                if row["uid"] not in uid_to_name:
                    uid_to_name[row["uid"]] = (
                        row.get("empire_name") or row.get("username") or f"UID {row['uid']}"
                    )

        def _name(u: int) -> str:
            return uid_to_name.get(u) or f"UID {u}"

        inbox = services.message_store.get_inbox(uid)
        sent = services.message_store.get_sent(uid)
        unread = services.message_store.unread_count(uid)

        def _annotate(m: dict) -> dict:
            return {
                **m,
                "from_name": _name(m["from_uid"]),
                "to_name":   _name(m["to_uid"]),
            }
        return {
            "inbox": [_annotate(m) for m in inbox],
            "sent":  [_annotate(m) for m in sent],
            "unread": unread,
        }

    @app.post("/api/messages/{msg_id}/read")
    async def mark_read(msg_id: int, uid: int = Depends(get_current_uid)) -> dict[str, Any]:
        """Mark a message as read."""
        ok = services.message_store.mark_read(uid, msg_id)
        return {"success": ok}

    @app.post("/api/battle-feedback")
    async def battle_feedback(body: BattleFeedbackRequest, uid: int = Depends(get_current_uid)) -> dict[str, Any]:
        """Send AI battle difficulty feedback as a message from AI (UID 0) to admin (UID 4)."""
        AI_UID = 0
        ADMIN_UID = 4
        text = f"[{body.rating}] Army: {body.army_name} (reported by UID {uid})"
        msg = services.message_store.send(from_uid=AI_UID, to_uid=ADMIN_UID, body=text)
        return {"success": True, "message": msg}


    # =================================================================
    # Admin / Dev status — no auth required
    # =================================================================

    ADMIN_USERNAME = "eem"

    async def require_admin(uid: int = Depends(get_current_uid)) -> int:
        if services.database is not None:
            user = await services.database.get_user_by_uid(uid)
            if user is None or user.get("username", "").lower() != ADMIN_USERNAME:
                raise HTTPException(status_code=403, detail="Admin only")
        return uid

    @app.get("/api/admin/status")
    async def admin_status(_uid: int = Depends(require_admin)) -> dict[str, Any]:
        """Unauthenticated overview for dev tools."""
        uid_to_user: dict[int, str] = {}
        if services.database is not None:
            for row in await services.database.list_users():
                uid_to_user[row["uid"]] = row["username"]

        connected_uids: list[int] = (
            services.server.connected_uids if services.server else []
        )

        empires_out = []
        for empire in services.empire_service.all_empires.values():
            if empire.uid == 0:
                continue

            buildings_done = [iid for iid, v in empire.buildings.items() if v == 0.0]
            buildings_wip  = {iid: round(v, 1) for iid, v in empire.buildings.items() if v != 0.0}
            knowledge_done = [iid for iid, v in empire.knowledge.items() if v == 0.0]
            knowledge_wip  = {iid: round(v, 1) for iid, v in empire.knowledge.items() if v != 0.0}

            armies_out = []
            for army in empire.armies:
                armies_out.append({
                    "aid": army.aid,
                    "name": army.name,
                    "waves": [
                        {"iid": w.iid, "slots": w.slots}
                        for w in army.waves
                    ],
                })

            empires_out.append({
                "uid": empire.uid,
                "name": empire.name,
                "username": uid_to_user.get(empire.uid, ""),
                "online": empire.uid in connected_uids,
                "resources": {k: round(v, 1) for k, v in empire.resources.items()},
                "max_life": round(empire.max_life, 1),
                "citizens": empire.citizens,
                "artefacts": empire.artefacts,
                "build_queue": empire.build_queue,
                "research_queue": empire.research_queue,
                "buildings_done": buildings_done,
                "buildings_wip": buildings_wip,
                "knowledge_done": knowledge_done,
                "knowledge_wip": knowledge_wip,
                "armies": armies_out,
            })
        empires_out.sort(key=lambda e: e["resources"].get("culture", 0), reverse=True)

        attacks_out = []
        for atk in services.attack_service.get_all_attacks():
            attacker_name = uid_to_user.get(atk.attacker_uid, f"uid:{atk.attacker_uid}")
            if atk.attacker_uid == 0:
                attacker_name = "AI"
            attacks_out.append({
                "id": atk.attack_id,
                "attacker_uid": atk.attacker_uid,
                "attacker": attacker_name,
                "defender": uid_to_user.get(atk.defender_uid, f"uid:{atk.defender_uid}"),
                "phase": atk.phase.value,
                "eta_s": round(atk.eta_seconds, 0),
                "total_eta_s": round(atk.total_eta_seconds, 0),
                "siege_s": round(atk.siege_remaining_seconds, 0),
                "total_siege_s": round(atk.total_siege_seconds, 0),
            })

        return {
            "connections": len(connected_uids),
            "connected_uids": connected_uids,
            "empire_count": len(empires_out),
            "empires": empires_out,
            "attacks": attacks_out,
        }

    @app.get("/api/admin/users")
    async def admin_list_users(_uid: int = Depends(require_admin)) -> list[dict]:
        """List all user accounts (no password hashes)."""
        if services.database is None:
            return []
        return await services.database.list_users()

    @app.delete("/api/admin/users/{username}")
    async def admin_delete_user(username: str, _uid: int = Depends(require_admin)) -> dict:
        """Delete a user account by username."""
        if services.database is None:
            return {"ok": False, "error": "no database"}
        deleted = await services.database.delete_user(username)
        return {"ok": deleted}

    @app.post("/api/admin/users")
    async def admin_create_user(body: dict, _uid: int = Depends(require_admin)) -> dict:
        """Create a user account. Body: {username, password, email?, empire_name?}"""
        if services.database is None:
            return {"ok": False, "error": "no database"}
        import bcrypt
        pw = body.get("password", "")
        if not pw or not body.get("username"):
            return {"ok": False, "error": "username and password required"}
        pw_hash = bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()
        try:
            uid = await services.database.create_user(
                username=body["username"],
                password_hash=pw_hash,
                email=body.get("email", ""),
                empire_name=body.get("empire_name", ""),
            )
            return {"ok": True, "uid": uid}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    @app.put("/api/admin/users/{username}/password")
    async def admin_reset_password(username: str, body: dict, _uid: int = Depends(require_admin)) -> dict:
        """Reset a user's password. Body: {password}"""
        if services.database is None:
            return {"ok": False, "error": "no database"}
        import bcrypt
        pw = body.get("password", "")
        if not pw:
            return {"ok": False, "error": "password required"}
        pw_hash = bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()
        assert services.database._conn is not None
        async with services.database._conn.execute(
            "UPDATE users SET password_hash = ? WHERE username = ?", (pw_hash, username)
        ) as cur:
            updated = cur.rowcount > 0
        await services.database._conn.commit()
        return {"ok": updated}

    @app.get("/api/admin/catalog")
    async def admin_catalog(_uid: int = Depends(require_admin)) -> dict[str, Any]:
        """Return full item catalog (buildings + knowledge) with effects."""
        from gameserver.models.items import ItemType
        up = services.empire_service._upgrades if services.empire_service else None
        if up is None:
            return {"buildings": {}, "knowledge": {}}
        buildings, knowledge = {}, {}
        for iid, item in up.items.items():
            entry = {
                "name": item.name,
                "effects": dict(item.effects),
            }
            if item.item_type == ItemType.BUILDING:
                buildings[iid] = entry
            elif item.item_type == ItemType.KNOWLEDGE:
                knowledge[iid] = entry
        return {"buildings": buildings, "knowledge": knowledge}

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
