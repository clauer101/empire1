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

from fastapi import Depends, FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from gameserver.network.jwt_auth import create_token, get_current_uid, verify_token
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
    SavedMapRenameBody,
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

    # -- last_seen tracker (throttled to once per 60s per user) ----------
    _last_seen_cache: dict[int, float] = {}

    @app.middleware("http")
    async def track_last_seen(request: Request, call_next):
        response = await call_next(request)
        if services.database is not None:
            auth = request.headers.get("authorization", "")
            if auth.startswith("Bearer "):
                try:
                    uid = verify_token(auth[7:])
                    import time
                    now = time.time()
                    if now - _last_seen_cache.get(uid, 0) > 60:
                        _last_seen_cache[uid] = now
                        await services.database.update_last_seen(uid)
                except Exception:
                    pass
        return response

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
        if resp and services.database:
            resp["unread_messages"] = await services.database.unread_count(uid)
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
            # Skip AI / NPC empires: no registered user account in the DB
            if empire.uid != uid and empire.uid not in uid_to_user:
                continue
            era_key = services.empire_service.get_current_era(empire)
            era_idx = services.empire_service._ERA_ORDER.index(era_key) + 1 if era_key in services.empire_service._ERA_ORDER else 1
            empires.append({
                "uid": empire.uid,
                "name": empire.name,
                "username": uid_to_user.get(empire.uid, ""),
                "culture": round(empire.resources.get("culture", 0.0), 1),
                "is_self": empire.uid == uid,
                "era": era_idx,
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
        """Send a message. to_uid=None/0 = global chat, otherwise private."""
        if not body.body.strip():
            return {"success": False, "error": "Message body cannot be empty"}
        to_uid = body.to_uid or 0
        if to_uid != 0 and to_uid == uid:
            return {"success": False, "error": "Cannot send message to yourself"}
        msg = await services.database.send_message(from_uid=uid, to_uid=to_uid, body=body.body.strip())
        return {"success": True, "message": msg}

    @app.get("/api/messages")
    async def get_messages(uid: int = Depends(get_current_uid)) -> dict[str, Any]:
        """Return global chat, private messages and battle reports for the current player."""
        # Empire names from live game state + DB fallback
        uid_to_name: dict[int, str] = {
            e.uid: e.name
            for e in services.empire_service.all_empires.values()
        }
        uid_to_username: dict[int, str] = {}
        if services.database is not None:
            for row in await services.database.list_users():
                if row["uid"] not in uid_to_name:
                    uid_to_name[row["uid"]] = (
                        row.get("empire_name") or row.get("username") or f"UID {row['uid']}"
                    )
                uid_to_username[row["uid"]] = row.get("username") or ""

        def _name(u: int) -> str:
            if u == 0:
                return "System"
            return uid_to_name.get(u) or f"UID {u}"

        def _username(u: int) -> str:
            return uid_to_username.get(u) or ""

        def _annotate(m: dict) -> dict:
            return {
                **m,
                "from_name": _name(m["from_uid"]),
                "to_name": _name(m["to_uid"]),
                "from_username": _username(m["from_uid"]),
                "to_username": _username(m["to_uid"]),
            }

        global_msgs   = await services.database.get_global()
        private_msgs  = await services.database.get_private_for(uid)
        battle_reports = await services.database.get_battle_reports_for(uid)
        unread_private = await services.database.unread_count_private(uid)
        unread_battle  = await services.database.unread_count_battle(uid)

        return {
            "global":         [_annotate(m) for m in global_msgs],
            "private":        [_annotate(m) for m in private_msgs],
            "battle_reports": [_annotate(m) for m in battle_reports],
            "unread_private": unread_private,
            "unread_battle":  unread_battle,
        }

    @app.post("/api/messages/{msg_id}/read")
    async def mark_read(msg_id: int, uid: int = Depends(get_current_uid)) -> dict[str, Any]:
        """Mark a message as read."""
        ok = await services.database.mark_read(uid, msg_id)
        return {"success": ok}

    @app.post("/api/battle-feedback")
    async def battle_feedback(body: BattleFeedbackRequest, uid: int = Depends(get_current_uid)) -> dict[str, Any]:
        """Send AI battle difficulty feedback as a message from AI (UID 0) to admin (UID 4)."""
        AI_UID = 0
        ADMIN_UID = 4
        text = f"[{body.rating}] Army: {body.army_name} (reported by UID {uid})"
        msg = await services.database.send_message(from_uid=AI_UID, to_uid=ADMIN_UID, body=text)
        return {"success": True, "message": msg}

    # =================================================================
    # Replay endpoints
    # =================================================================

    @app.get("/api/replays")
    async def get_replays(uid: int = Depends(get_current_uid)) -> dict[str, Any]:
        """List available battle replays."""
        from gameserver.persistence.replay import list_replays
        replays = list_replays()
        return {"replays": replays}

    @app.get("/api/replays/{key}")
    async def get_replay(key: str, uid: int = Depends(get_current_uid)):
        """Get a full battle replay by replay key (e.g. '20260101_120000_42').

        Returns raw gzip bytes for .json.gz files (client decompresses via
        DecompressionStream) or plain JSON for legacy .json files.
        """
        from gameserver.persistence.replay import get_replay_path
        from starlette.responses import Response, JSONResponse
        path = get_replay_path(key)
        if path is None:
            raise HTTPException(status_code=404, detail="Replay not found")
        if path.suffix == ".gz":
            data = path.read_bytes()
            return Response(
                content=data,
                media_type="application/gzip",
                headers={"Content-Length": str(len(data))},
            )
        # Legacy plain JSON
        import json as _json
        return JSONResponse(content=_json.loads(path.read_text(encoding="utf-8")))


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

        from gameserver.engine.power_service import compute_power
        up = services.empire_service._upgrades if services.empire_service else None

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

            hex_tiles = []
            for key, val in empire.hex_map.items():
                try:
                    q, r = map(int, key.split(','))
                    tile_type = val.get('type', '') if isinstance(val, dict) else val
                    hex_tiles.append({"q": q, "r": r, "type": tile_type})
                except (ValueError, AttributeError):
                    pass

            from gameserver.engine.hex_pathfinding import find_path_from_spawn_to_castle as _find_path
            try:
                _nm = {f"{t['q']},{t['r']}": (t["type"] if t["type"] else "empty") for t in hex_tiles}
                _pl = len(_find_path(_nm)) - 1 if _find_path(_nm) else None
            except Exception:
                _pl = None
            power = compute_power(empire, up, path_length=_pl).to_dict() if up else {"economy": 0, "attack": 0, "defense": 0, "total": 0}

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
                "hex_tiles": hex_tiles,
                "power": power,
            })
        empires_out.sort(key=lambda e: e["resources"].get("culture", 0), reverse=True)

        # Build a lookup: (uid, aid) → army
        all_armies: dict[tuple[int, int], Any] = {}
        for emp in services.empire_service.all_empires.values():
            for army in emp.armies:
                all_armies[(emp.uid, army.aid)] = army

        attacks_out = []
        for atk in services.attack_service.get_all_attacks():
            attacker_name = uid_to_user.get(atk.attacker_uid, f"uid:{atk.attacker_uid}")
            if atk.attacker_uid == 0:
                attacker_name = "AI"
            army = all_armies.get((atk.attacker_uid, atk.army_aid))
            waves_out = []
            army_name = ""
            if army:
                army_name = army.name or ""
                waves_out = [
                    {"iid": w.iid, "slots": w.slots}
                    for w in army.waves
                ]
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
                "army_name": army_name,
                "waves": waves_out,
            })

        return {
            "connections": len(connected_uids),
            "connected_uids": connected_uids,
            "empire_count": len(empires_out),
            "empires": empires_out,
            "attacks": attacks_out,
        }

    @app.post("/api/admin/restart")
    async def admin_restart(_uid: int = Depends(require_admin)) -> dict[str, Any]:
        """Save state and restart the server process via os.execv."""
        import os
        import sys

        async def _do_restart() -> None:
            await asyncio.sleep(0.5)
            if services.empire_service is not None:
                try:
                    from gameserver.persistence.state_save import save_state
                    await save_state(
                        empires=services.empire_service.all_empires,
                        attacks=services.attack_service.get_all_attacks(),
                        battles=[],
                    )
                except Exception:
                    log.exception("State save failed before restart")
            log.info("Restarting server process via os.execv …")
            os.execv(sys.executable, [sys.executable, '-m', 'gameserver.main'] + sys.argv[1:])

        asyncio.create_task(_do_restart())
        return {"ok": True, "message": "State saved — restarting …"}

    @app.get("/api/admin/users")
    async def admin_list_users(_uid: int = Depends(require_admin)) -> list[dict]:
        """List all user accounts (no password hashes)."""
        if services.database is None:
            return []
        return await services.database.list_users()

    @app.delete("/api/admin/users/{username}")
    async def admin_delete_user(username: str, _uid: int = Depends(require_admin)) -> dict:
        """Delete a user account and their in-memory empire by username."""
        if services.database is None:
            return {"ok": False, "error": "no database"}
        user = await services.database.get_user(username)
        if user is not None:
            uid_to_remove = user["uid"]
            if services.empire_service is not None:
                services.empire_service.unregister(uid_to_remove)
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

    @app.put("/api/admin/users/{uid}/empire_name")
    async def admin_rename_empire(uid: int, body: dict, _uid: int = Depends(require_admin)) -> dict:
        """Rename a player's empire. Body: {empire_name}"""
        if services.database is None:
            return {"ok": False, "error": "no database"}
        name = body.get("empire_name", "").strip()
        if not name:
            return {"ok": False, "error": "empire_name required"}
        updated = await services.database.rename_empire(uid, name)
        if updated and uid in services.empires:
            services.empires[uid].name = name
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

    # ── Era mapping derived from YAML section comments ──────────────────
    import re as _re
    from pathlib import Path as _Path

    from gameserver.util.eras import ERA_ORDER as _ERA_KEYS, ERA_LABELS_DE as _ERA_LABELS_DE, ERA_LABELS_EN as _ERA_LABELS_EN
    _ERA_PATTERNS_KEYS = [
        ("STEINZEIT",          _re.compile(r'#\s+STEINZEIT')),
        ("NEOLITHIKUM",        _re.compile(r'#\s+NEOLITHIKUM')),
        ("BRONZEZEIT",         _re.compile(r'#\s+BRONZEZEIT')),
        ("EISENZEIT",          _re.compile(r'#\s+EISENZEIT')),
        ("MITTELALTER",        _re.compile(r'#\s+MITTELALTER')),
        ("RENAISSANCE",        _re.compile(r'#\s+RENAISSANCE')),
        ("INDUSTRIALISIERUNG", _re.compile(r'#\s+INDUSTRIALIS')),
        ("MODERNE",            _re.compile(r'#\s+MODERNE')),
        ("ZUKUNFT",            _re.compile(r'#\s+ZUKUNFT')),
    ]
    _CONFIG_DIR = _Path(__file__).resolve().parents[3] / "config"
    _ITEM_IID_RE = _re.compile(r'^([A-Z][A-Z0-9_]+):')

    def _parse_yaml_era_groups_gs(path: "_Path") -> "dict[str, list[str]]":
        result: dict[str, list[str]] = {k: [] for k in _ERA_KEYS}
        current = _ERA_KEYS[0]
        for line in path.read_text(encoding="utf-8").split("\n"):
            for key, pat in _ERA_PATTERNS_KEYS:
                if pat.search(line):
                    current = key
                    break
            m = _ITEM_IID_RE.match(line)
            if m:
                result[current].append(m.group(1))
        return result

    _critter_groups = _parse_yaml_era_groups_gs(_CONFIG_DIR / "critters.yaml")
    _structure_groups = _parse_yaml_era_groups_gs(_CONFIG_DIR / "structures.yaml")
    _knowledge_groups = _parse_yaml_era_groups_gs(_CONFIG_DIR / "knowledge.yaml")
    _building_groups = _parse_yaml_era_groups_gs(_CONFIG_DIR / "buildings.yaml")

    # iid → English era label (used by ai-armies and map-overview endpoints)
    _CRITTER_ERAS: dict[str, str] = {
        iid: _ERA_LABELS_EN[era]
        for era, iids in _critter_groups.items()
        for iid in iids
    }

    # ordered [(UPPERCASE_ERA_KEY, [iid, ...]), ...] (used by structures endpoint)
    _STRUCTURE_ERAS: list[tuple[str, list[str]]] = [
        (era, iids) for era, iids in _structure_groups.items() if iids
    ]

    # Map game.yaml era_effects keys (lowercase English) → uppercase German era keys
    from gameserver.util.eras import ERA_YAML_TO_KEY as _ERA_EFFECT_KEY_MAP

    def _load_era_effects() -> dict[str, dict[str, float]]:
        """Read era_effects from game.yaml, keyed by uppercase era key."""
        import yaml as _yaml
        p = _CONFIG_DIR / "game.yaml"
        if not p.exists():
            return {}
        with p.open() as f:
            raw = _yaml.safe_load(f) or {}
        effects_raw = raw.get("era_effects", {})
        result: dict[str, dict[str, float]] = {}
        for eng_key, vals in effects_raw.items():
            era_key = _ERA_EFFECT_KEY_MAP.get(eng_key)
            if era_key and isinstance(vals, dict):
                result[era_key] = vals
        return result

    _era_effects_data = _load_era_effects()

    @app.get("/api/era-map")
    async def get_era_map() -> dict[str, Any]:
        """Return era order + per-era item IIDs for all categories (no auth required)."""
        return {
            "eras": _ERA_KEYS,
            "labels_de": _ERA_LABELS_DE,
            "labels_en": _ERA_LABELS_EN,
            "critters":   _critter_groups,
            "structures": _structure_groups,
            "knowledge":  _knowledge_groups,
            "buildings":  _building_groups,
            "era_effects": _era_effects_data,
        }

    @app.get("/api/admin/structures")
    async def admin_structures(_uid: int = Depends(require_admin)) -> dict[str, Any]:
        """Return all structure definitions grouped by era."""
        from gameserver.models.items import ItemType
        up = services.empire_service._upgrades if services.empire_service else None
        if up is None:
            return {"structures": {}}
        result: dict[str, Any] = {}
        for era, iids in _STRUCTURE_ERAS:
            for iid in iids:
                item = up.items.get(iid)
                if item and item.item_type == ItemType.STRUCTURE:
                    result[iid] = {
                        "name": item.name,
                        "era": era,
                        "damage": item.damage,
                        "range": item.range,
                        "reload_time_ms": item.reload_time_ms,
                        "effects": dict(item.effects),
                        "costs": dict(item.costs),
                        "sprite": item.sprite or "",
                    }
        return {"structures": result}

    def _update_effects_in_yaml(yaml_path: "Path", iid: str, new_effects: dict[str, Any]) -> bool:
        """Replace the `effects:` line for *iid* in a YAML file, preserving inline comments."""
        from pathlib import Path as _Path
        text = _Path(yaml_path).read_text()
        lines = text.splitlines()

        # Format new effects as YAML flow mapping
        if new_effects:
            pairs = ", ".join(f"{k}: {v}" for k, v in new_effects.items())
            new_line_value = f"  effects: {{{pairs}}}"
        else:
            new_line_value = "  effects: {}"

        # Locate the root `IID:` line
        iid_idx: int | None = None
        for i, line in enumerate(lines):
            if line.startswith(f"{iid}:"):
                iid_idx = i
                break
        if iid_idx is None:
            return False

        # Find `effects:` key within this IID's indented block
        for i in range(iid_idx + 1, len(lines)):
            line = lines[i]
            # Leaving this IID's block (new root key or EOF)
            if line and not line.startswith(" ") and not line.startswith("#"):
                break
            stripped = line.lstrip()
            if stripped.startswith("effects:"):
                # Preserve trailing inline comment
                comment = ""
                rest = line[line.index("effects:"):]
                hash_pos = rest.find("#")
                if hash_pos != -1:
                    comment = "   " + rest[hash_pos:]
                lines[i] = new_line_value + comment
                _Path(yaml_path).write_text("\n".join(lines) + "\n")
                return True
        return False

    @app.get("/api/admin/analyze-empire/{uid}")
    async def admin_analyze_empire(uid: int, _uid: int = Depends(require_admin)) -> dict[str, Any]:
        """Run hex-map analysis for a given empire: path length, tower costs, age distribution."""
        from collections import deque as _deque, Counter as _Counter

        empire = services.empire_service.get(uid)
        if empire is None:
            raise HTTPException(status_code=404, detail=f"Empire uid={uid} not found")

        # hex_map is stored as {"q,r": type_value}
        raw_map = empire.hex_map  # dict[str, str|dict]

        # ── BFS path length ──
        HEX_DIRS = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, -1), (-1, 1)]
        walkable: set[tuple[int, int]] = set()
        start: tuple[int, int] | None = None
        goal:  tuple[int, int] | None = None

        for key, tile_type in raw_map.items():
            if isinstance(tile_type, dict):
                tile_type = tile_type.get("type", "")
            try:
                q, r = map(int, key.split(","))
            except Exception:
                continue
            if tile_type in ("path", "spawnpoint", "castle"):
                walkable.add((q, r))
            if tile_type == "spawnpoint":
                start = (q, r)
            if tile_type == "castle":
                goal = (q, r)

        path_length: int | None = None
        if start and goal:
            queue = _deque([(start, 0)])
            visited = {start}
            while queue:
                (q, r), dist = queue.popleft()
                if (q, r) == goal:
                    path_length = dist
                    break
                for dq, dr in HEX_DIRS:
                    nb = (q + dq, r + dr)
                    if nb not in visited and nb in walkable:
                        visited.add(nb)
                        queue.append((nb, dist + 1))

        # ── Tower analysis ──
        # Ages derived from sections in config/structures.yaml
        TOWER_AGE: dict[str, str] = {
            "BASIC_TOWER": "Stone Age", "SLING_TOWER": "Stone Age",
            "DOUBLE_SLING_TOWER": "Neolithic", "SPIKE_TRAP": "Neolithic",
            "ARROW_TOWER": "Bronze Age", "BALLISTA_TOWER": "Bronze Age", "FIRE_TOWER": "Bronze Age",
            "CATAPULTS": "Iron Age", "ARBELESTE_TOWER": "Iron Age",
            "TAR_TOWER": "Middle Ages", "HEAVY_TOWER": "Middle Ages", "BOILING_OIL": "Middle Ages",
            "CANNON_TOWER": "Renaissance", "RIFLE_TOWER": "Renaissance",
            "COLD_TOWER": "Renaissance", "ICE_TOWER": "Renaissance",
            "FLAME_THROWER": "Industrial", "SHOCK_TOWER": "Industrial",
            "PARALYZNG_TOWER": "Industrial", "NAPALM_THROWER": "Industrial",
            "MG_TOWER": "Modern", "RAPID_FIRE_MG_BUNKER": "Modern",
            "RADAR_TOWER": "Modern", "ANTI_AIR_TOWER": "Modern", "LASER_TOWER": "Modern",
            "SNIPER_TOWER": "Future", "ROCKET_TOWER": "Future",
        }

        up = services.empire_service._upgrades
        tower_names: list[str] = []
        total_cost = 0
        age_counts: dict[str, int] = {}

        for tile_type in raw_map.values():
            if isinstance(tile_type, dict):
                tile_type = tile_type.get("type", "")
            if tile_type in ("path", "castle", "spawnpoint", "", None):
                continue
            item = up.items.get(tile_type) if up else None
            if item is None:
                continue
            cost = item.costs.get("gold", 0)
            total_cost += cost
            tower_names.append(tile_type)
            age = TOWER_AGE.get(tile_type, "Unknown")
            age_counts[age] = age_counts.get(age, 0) + 1

        tower_counts = dict(_Counter(tower_names))
        num_towers = len(tower_names)
        age_pct = {
            age: round(cnt / num_towers * 100, 1)
            for age, cnt in age_counts.items()
        } if num_towers else {}

        return {
            "uid": uid,
            "path_length": path_length,
            "num_towers": num_towers,
            "total_cost": total_cost,
            "avg_cost": round(total_cost / num_towers) if num_towers else 0,
            "tower_counts": tower_counts,
            "age_counts": age_counts,
            "age_pct": age_pct,
        }

    @app.get("/api/admin/map-overview")
    async def admin_map_overview(_uid: int = Depends(require_admin)) -> list[dict[str, Any]]:
        """Hex-map + power stats for all fixture empires and live empires."""
        import yaml as _yaml
        import math as _math
        from pathlib import Path as _Path
        from collections import Counter as _Cnt, deque as _dq2

        HEX_DIRS = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, -1), (-1, 1)]
        NON_TOWER = {"path", "castle", "spawnpoint", "empty", "", None}

        from gameserver.engine.power_service import defense_power as _defense_power
        from gameserver.models.empire import Empire as _Empire

        def _defense_power_for_tiles(tiles: list[dict], life: float, path_length: int | None = None) -> float | None:
            try:
                up = services.empire_service._upgrades
                if up is None:
                    return None
                e = _Empire(uid=0, name="")
                e.hex_map = {f"{t['q']},{t['r']}": {"type": t["type"]} for t in tiles}
                e.max_life = life
                return round(_defense_power(e, up, path_length=path_length), 1)
            except Exception:
                return None

        def _analyze(tiles: list[dict], source: str, empire_name: str, uid: int, life: float = 10.0) -> dict:
            # Build dict
            tile_map: dict[tuple, str] = {}
            for t in tiles:
                tt = t["type"]
                if isinstance(tt, dict):
                    tt = tt.get("type", "")
                tile_map[(t["q"], t["r"])] = tt or ""

            # BFS path length
            walkable = {pos for pos, tt in tile_map.items() if tt in ("path", "spawnpoint", "castle")}
            start = next((pos for pos, tt in tile_map.items() if tt == "spawnpoint"), None)
            goal  = next((pos for pos, tt in tile_map.items() if tt == "castle"), None)
            path_length: int | None = None
            if start and goal:
                queue = _dq2([(start, 0)])
                visited = {start}
                while queue:
                    pos, dist = queue.popleft()
                    if pos == goal:
                        path_length = dist
                        break
                    q, r = pos
                    for dq, dr in HEX_DIRS:
                        nb = (q + dq, r + dr)
                        if nb not in visited and nb in walkable:
                            visited.add(nb)
                            queue.append((nb, dist + 1))

            # Tower costs + age distribution — derived from structures.yaml sections
            TOWER_AGE: dict[str, str] = {
                iid: _ERA_LABELS_EN[era]
                for era, iids in _STRUCTURE_ERAS
                for iid in iids
            }

            up = services.empire_service._upgrades
            tower_names: list[str] = []
            total_cost = 0
            age_counts: dict[str, int] = {}
            for tt in tile_map.values():
                if tt in NON_TOWER:
                    continue
                item = up.items.get(tt) if up else None
                if item is None:
                    continue
                cost = item.costs.get("gold", 0)
                total_cost += cost
                tower_names.append(tt)
                age = TOWER_AGE.get(tt, "Unknown")
                age_counts[age] = age_counts.get(age, 0) + 1

            num_towers = len(tower_names)
            age_pct = {
                age: round(cnt / num_towers * 100, 1)
                for age, cnt in age_counts.items()
            } if num_towers else {}
            power = _defense_power_for_tiles(tiles, life, path_length=path_length)

            return {
                "source":      source,
                "empire_name": empire_name,
                "uid":         uid,
                "tiles":       [{"q": q, "r": r, "type": tt} for (q, r), tt in tile_map.items()],
                "path_length": path_length,
                "num_towers":  num_towers,
                "total_cost":  total_cost,
                "avg_cost":    round(total_cost / num_towers) if num_towers else 0,
                "tower_counts": dict(_Cnt(tower_names)),
                "age_counts":  age_counts,
                "age_pct":     age_pct,
                "power":       power,
            }

        _SAVED_MAPS_PATH = _Path(__file__).parent.parent.parent.parent / "config" / "saved_maps.yaml"

        results: list[dict] = []

        # ── saved_maps.yaml ──
        if _SAVED_MAPS_PATH.exists():
            try:
                data = _yaml.safe_load(_SAVED_MAPS_PATH.read_text())
                for m in (data.get("maps") or []):
                    tiles = m.get("hex_map") or []
                    if tiles:
                        life_val = float(m.get("life") or 10.0)
                        entry = _analyze(tiles, "saved", m.get("name", m.get("id", "?")), 0, life=life_val)
                        entry["map_id"] = m.get("id", "")
                        entry["empire_name"] = m.get("name", entry["empire_name"])
                        entry["life"] = m.get("life")
                        results.append(entry)
            except Exception:
                pass

        # ── Live empires ──
        for empire in services.empire_service.all_empires.values():
            if empire.uid in (0, 100):
                continue
            raw = empire.hex_map or {}
            tiles = []
            for key, tt in raw.items():
                q, r = map(int, key.split(","))
                if isinstance(tt, dict):
                    tt = tt.get("type", "")
                tiles.append({"q": q, "r": r, "type": tt or ""})
            if tiles:
                life_val = float(empire.max_life or 10.0)
                results.append(_analyze(tiles, "live", empire.name, empire.uid, life=life_val))

        return results

    _SAVED_MAPS_PATH = (
        __import__("pathlib").Path(__file__).parent.parent.parent.parent
        / "config" / "saved_maps.yaml"
    )

    def _load_saved_maps() -> list[dict]:
        import yaml as _y
        if not _SAVED_MAPS_PATH.exists():
            return []
        return _y.safe_load(_SAVED_MAPS_PATH.read_text()).get("maps") or []

    def _write_saved_maps(maps: list[dict]) -> None:
        import yaml as _y
        _SAVED_MAPS_PATH.write_text(_y.dump({"maps": maps}, allow_unicode=True,
                                             default_flow_style=False, sort_keys=False))

    @app.post("/api/admin/saved-maps/from-live/{uid}")
    async def admin_save_live_map(uid: int, _uid: int = Depends(require_admin)) -> dict:
        """Copy the live hex_map of empire uid into saved_maps.yaml as a new entry."""
        import time as _time
        empire = services.empire_service.get(uid)
        if empire is None:
            raise HTTPException(status_code=404, detail=f"Empire uid={uid} not found")
        raw = empire.hex_map or {}
        if not raw:
            raise HTTPException(status_code=400, detail="Empire has no map")

        tiles = []
        for key, tt in raw.items():
            q, r = map(int, key.split(","))
            if isinstance(tt, dict):
                tt = tt.get("type", "")
            tiles.append({"q": q, "r": r, "type": tt or ""})

        map_id = f"live_{uid}_{int(_time.time())}"
        name = f"{empire.name} (Kopie)"
        maps = _load_saved_maps()
        maps.append({"id": map_id, "name": name, "hex_map": tiles})
        _write_saved_maps(maps)
        return {"ok": True, "map_id": map_id, "name": name}

    @app.delete("/api/admin/saved-maps/{map_id}")
    async def admin_delete_saved_map(map_id: str, _uid: int = Depends(require_admin)) -> dict:
        """Delete a map from saved_maps.yaml by id."""
        maps = _load_saved_maps()
        new_maps = [m for m in maps if m.get("id") != map_id]
        if len(new_maps) == len(maps):
            raise HTTPException(status_code=404, detail=f"map_id '{map_id}' not found")
        _write_saved_maps(new_maps)
        return {"ok": True, "deleted": map_id}

    @app.patch("/api/admin/saved-maps/{map_id}")
    async def admin_rename_saved_map(map_id: str, body: SavedMapRenameBody,
                                     _uid: int = Depends(require_admin)) -> dict:
        """Rename a map in saved_maps.yaml."""
        maps = _load_saved_maps()
        for m in maps:
            if m.get("id") == map_id:
                m["name"] = body.name.strip()
                if body.life is not None:
                    m["life"] = float(body.life)
                _write_saved_maps(maps)
                return {"ok": True, "id": map_id, "name": m["name"], "life": m.get("life")}
        raise HTTPException(status_code=404, detail=f"map_id '{map_id}' not found")

    @app.post("/api/admin/saved-maps/{map_id}/activate")
    async def admin_activate_saved_map(map_id: str, _uid: int = Depends(require_admin)) -> dict:
        """Activate a saved map for uid 4 (eem), auto-saving their current map first."""
        import time as _time
        TARGET_UID = 4

        empire = services.empire_service.get(TARGET_UID)
        if empire is None:
            raise HTTPException(status_code=404, detail=f"Empire uid={TARGET_UID} not found")

        # 1. Backup current map of uid 4
        raw = empire.hex_map or {}
        backup_id = None
        if raw:
            tiles_backup = []
            for key, tt in raw.items():
                q, r = map(int, key.split(","))
                if isinstance(tt, dict):
                    tt = tt.get("type", "")
                tiles_backup.append({"q": q, "r": r, "type": tt or ""})
            backup_id = f"backup_{TARGET_UID}_{int(_time.time())}"
            backup_name = f"{empire.name} (Backup {_time.strftime('%Y-%m-%d %H:%M')})"
            maps = _load_saved_maps()
            maps.append({"id": backup_id, "name": backup_name, "hex_map": tiles_backup})
            _write_saved_maps(maps)

        # 2. Load the target map
        maps = _load_saved_maps()
        target_map = next((m for m in maps if m.get("id") == map_id), None)
        if target_map is None:
            raise HTTPException(status_code=404, detail=f"map_id '{map_id}' not found")

        # 3. Apply map to empire (list of tiles → "q,r" dict)
        new_hex_map = {}
        for tile in target_map.get("hex_map", []):
            new_hex_map[f"{tile['q']},{tile['r']}"] = tile.get("type", "")
        empire.hex_map = new_hex_map

        return {"ok": True, "backup_id": backup_id}

    _TOWER_ERAS: dict[str, str] = {
        iid: _ERA_LABELS_EN.get(era_key, era_key)
        for era_key, iids in _STRUCTURE_ERAS
        for iid in iids
    }

    @app.get("/api/admin/ai-armies")
    async def admin_ai_armies(_uid: int = Depends(require_admin)) -> dict[str, Any]:
        """Return all hardcoded AI army definitions + critter stats for strength calc."""
        from gameserver.models.items import ItemType
        hw = services.ai_service._hardcoded_waves if services.ai_service else []
        armies = []
        for entry in hw:
            armies.append({
                "name": entry.get("name", ""),
                "travel_time": entry.get("travel_time"),
                "main_age": entry.get("main_age", ""),
                "trigger": entry.get("trigger") or {},
                "waves": [
                    {"critter": w.get("critter", ""), "slots": w.get("slots", 1)}
                    for w in (entry.get("waves") or [])
                ],
            })
        # Include critter + tower stats for frontend visualisation
        up = services.empire_service._upgrades if services.empire_service else None
        critters: dict[str, Any] = {}
        towers: dict[str, Any] = {}
        if up:
            for iid, item in up.items.items():
                if item.item_type == ItemType.CRITTER:
                    critters[iid] = {
                        "health": item.health,
                        "armour": item.armour,
                        "slots": item.slots,
                        "speed": item.speed,
                        "era": _CRITTER_ERAS.get(iid, "Unbekannt"),
                        "sprite": f"assets/sprites/critters/{iid.lower()}/{iid.lower()}.png",
                    }
            for era_key, iids in _STRUCTURE_ERAS:
                era_label = _ERA_LABELS_EN.get(era_key, era_key)
                for iid in iids:
                    item = up.items.get(iid)
                    if item is None:
                        continue
                    efx = item.effects or {}
                    towers[iid] = {
                        "damage": item.damage,
                        "range": item.range,
                        "reload": item.reload_time_ms,
                        "burn_dps": efx.get("burn_dps", 0),
                        "burn_dur": efx.get("burn_duration", 0),
                        "slow_dur": efx.get("slow_duration", 0),
                        "era": era_label,
                        "sprite": item.sprite or "",
                    }
        return {"armies": armies, "critters": critters, "towers": towers}

    @app.post("/api/admin/send-ai-attack")
    async def admin_send_ai_attack(
        body: dict[str, Any], _uid: int = Depends(require_admin)
    ) -> dict[str, Any]:
        """Send a specific AI army to a target empire (admin only).

        Body::

            {
                "defender_uid": 3,
                "army_name": "Early Barbarians Raid",   # from ai_waves.yaml
                "waves": [                               # OR manual waves
                    {"critter": "SLAVE", "slots": 6}
                ],
                "travel_time": 10   # optional, seconds
            }
        """
        from gameserver.models.army import Army, CritterWave

        defender_uid: int = body.get("defender_uid", 0)
        if not defender_uid:
            raise HTTPException(status_code=400, detail="defender_uid required")

        if services.empire_service.get(defender_uid) is None:
            raise HTTPException(status_code=404, detail=f"Empire uid={defender_uid} not found")

        travel_time: float | None = body.get("travel_time")
        army_name: str = body.get("army_name") or "Admin Attack"

        # Build waves either from explicit list or from ai_waves.yaml by name
        waves_raw: list[dict] = body.get("waves") or []
        if not waves_raw:
            # look up by name in hardcoded waves
            hw = services.ai_service._hardcoded_waves if services.ai_service else []
            entry = next((e for e in hw if e.get("name") == army_name), None)
            if entry is None:
                raise HTTPException(status_code=404, detail=f"Army '{army_name}' not found in ai_waves.yaml")
            waves_raw = entry.get("waves") or []
            if travel_time is None:
                travel_time = float(entry.get("travel_time") or 0) or None

        if not waves_raw:
            raise HTTPException(status_code=400, detail="No waves defined")

        initial_delay_ms = services.ai_service._game_config.initial_wave_delay_ms

        aid = services.empire_service.next_army_id()

        waves = []
        for i, w in enumerate(waves_raw):
            waves.append(CritterWave(
                wave_id=i + 1,
                iid=str(w.get("critter", "")).upper(),
                slots=int(w.get("slots", 1)),
                num_critters_spawned=0,
                next_critter_ms=int(i * initial_delay_ms),
            ))

        army = Army(aid=aid, uid=0, name=army_name, waves=waves)

        if services.ai_service:
            services.ai_service._send_army(
                defender_uid=defender_uid,
                empire=services.empire_service.get(defender_uid),
                empire_service=services.empire_service,
                attack_service=services.attack_service,
                army=army,
                travel_seconds=travel_time,
            )
        else:
            services.attack_service.start_ai_attack(
                defender_uid=defender_uid,
                army=army,
                travel_seconds=travel_time or 30.0,
            )

        return {
            "success": True,
            "defender_uid": defender_uid,
            "army_name": army_name,
            "waves": [{"critter": w.iid, "slots": w.slots} for w in waves],
        }

    @app.patch("/api/admin/structures/{iid}/effects")
    async def update_structure_effects(
        iid: str, body: dict[str, Any], _uid: int = Depends(require_admin)
    ) -> dict[str, Any]:
        """Write updated effects for *iid* to structures.yaml."""
        from pathlib import Path as _Path
        new_effects: dict[str, Any] = body.get("effects", {})
        for k, v in new_effects.items():
            if not isinstance(k, str):
                raise HTTPException(status_code=400, detail="Effect keys must be strings")
            if not isinstance(v, (int, float)):
                raise HTTPException(status_code=400, detail=f"Effect value for '{k}' must be a number")

        config_path = _Path(__file__).parent.parent.parent.parent / "config" / "structures.yaml"
        if not config_path.exists():
            raise HTTPException(status_code=500, detail="structures.yaml not found")

        ok = _update_effects_in_yaml(config_path, iid, new_effects)
        if not ok:
            raise HTTPException(status_code=404, detail=f"IID '{iid}' not found in structures.yaml")
        return {"success": True, "iid": iid, "effects": new_effects}

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
