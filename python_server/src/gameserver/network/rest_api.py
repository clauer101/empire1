"""REST API — FastAPI application for economy endpoints.

All economy request/response communication goes through REST.
Battle push events use WebSocket via /ws on the same port.

Usage::

    from gameserver.network.rest_api import create_app

    app = create_app(services)
    # Start with uvicorn as an asyncio task alongside the WS server
"""

from __future__ import annotations

import datetime
import json
import time
import uuid
from pathlib import Path
from typing import Any, TYPE_CHECKING

import structlog
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from gameserver.network.jwt_auth import verify_token
from gameserver.models.messages import GameMessage
from gameserver.util.eras import ERA_ORDER as _ERA_KEYS, ERA_LABELS_DE as _ERA_LABELS_DE, ERA_LABELS_EN as _ERA_LABELS_EN  # noqa: F401 — re-exported for routers

if TYPE_CHECKING:
    from gameserver.main import Services

log = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# Module-level constants — importable by routers
# ---------------------------------------------------------------------------

ERA_KEYS = _ERA_KEYS  # alias kept for back-compat; routers use _ERA_KEYS directly
_CONFIG_DIR = Path(__file__).resolve().parents[3] / "config"
_SAVED_MAPS_PATH = Path(__file__).resolve().parents[4] / "config" / "saved_maps.yaml"


# ---------------------------------------------------------------------------
# Shared helper functions — importable by routers
# ---------------------------------------------------------------------------

def _stub_message(**fields: Any) -> GameMessage:
    """Create a minimal GameMessage with extra attributes.

    The existing handlers read attributes via ``getattr(message, ...)``,
    so we just set them on a base GameMessage instance.
    """
    msg = GameMessage(type="rest", sender=0)
    for k, v in fields.items():
        object.__setattr__(msg, k, v)
    return msg


def _is_recently_active(last_seen_str: str, threshold_s: int) -> bool:
    if not last_seen_str:
        return False
    try:
        dt = datetime.datetime.fromisoformat(last_seen_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=datetime.timezone.utc)
        return (time.time() - dt.timestamp()) < threshold_s
    except Exception:
        # Malformed ISO timestamp from DB — treat as not recently active
        return False


def _parse_yaml_era_groups_gs(path: Path) -> dict[str, list[str]]:
    import yaml as _yaml
    result: dict[str, list[str]] = {k: [] for k in _ERA_KEYS}
    data = _yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    for iid, item in data.items():
        if not isinstance(item, dict):
            continue
        key = item.get("era", _ERA_KEYS[0])
        if key in result:
            result[key].append(iid)
    return result


_critter_groups = _parse_yaml_era_groups_gs(_CONFIG_DIR / "critters.yaml")
_structure_groups = _parse_yaml_era_groups_gs(_CONFIG_DIR / "structures.yaml")
_knowledge_groups = _parse_yaml_era_groups_gs(_CONFIG_DIR / "knowledge.yaml")
_building_groups = _parse_yaml_era_groups_gs(_CONFIG_DIR / "buildings.yaml")

# iid → English era label
_CRITTER_ERAS: dict[str, str] = {
    iid: _ERA_LABELS_EN[era]
    for era, iids in _critter_groups.items()
    for iid in iids
}

# ordered [(UPPERCASE_ERA_KEY, [iid, ...]), ...]
_STRUCTURE_ERAS: list[tuple[str, list[str]]] = [
    (era, iids) for era, iids in _structure_groups.items() if iids
]

_TOWER_ERAS: dict[str, str] = {
    iid: _ERA_LABELS_EN.get(era_key, era_key)
    for era_key, iids in _STRUCTURE_ERAS
    for iid in iids
}

# Era keys are already lowercase English — no remapping needed
_ERA_KEY_TO_EFFECT_KEY = {k: k for k in _ERA_KEYS}


def _load_era_effects() -> dict[str, dict[str, float]]:
    """Read era_effects from game.yaml, keyed by lowercase English era key."""
    import yaml as _yaml
    p = _CONFIG_DIR / "game.yaml"
    if not p.exists():
        return {}
    with p.open() as f:
        raw = _yaml.safe_load(f) or {}
    effects_raw = raw.get("era_effects", {})
    return {k: v for k, v in effects_raw.items() if isinstance(v, dict) and k in _ERA_KEYS}


_era_effects_data = _load_era_effects()


def _update_effects_in_yaml(yaml_path: Any, iid: str, new_effects: dict[str, Any]) -> bool:
    """Replace the `effects:` line for *iid* in a YAML file, preserving inline comments."""
    text = Path(yaml_path).read_text()
    lines = text.splitlines()

    if new_effects:
        pairs = ", ".join(f"{k}: {v}" for k, v in new_effects.items())
        new_line_value = f"  effects: {{{pairs}}}"
    else:
        new_line_value = "  effects: {}"

    iid_idx: int | None = None
    for i, line in enumerate(lines):
        if line.startswith(f"{iid}:"):
            iid_idx = i
            break
    if iid_idx is None:
        return False

    for i in range(iid_idx + 1, len(lines)):
        line = lines[i]
        if line and not line.startswith(" ") and not line.startswith("#"):
            break
        stripped = line.lstrip()
        if stripped.startswith("effects:"):
            comment = ""
            rest = line[line.index("effects:"):]
            hash_pos = rest.find("#")
            if hash_pos != -1:
                comment = "   " + rest[hash_pos:]
            lines[i] = new_line_value + comment
            Path(yaml_path).write_text("\n".join(lines) + "\n")
            return True
    return False


def _load_saved_maps() -> list[dict[str, Any]]:
    import yaml as _y
    if not _SAVED_MAPS_PATH.exists():
        return []
    return _y.safe_load(_SAVED_MAPS_PATH.read_text()).get("maps") or []


def _write_saved_maps(maps: list[dict[str, Any]]) -> None:
    import yaml as _y
    _SAVED_MAPS_PATH.write_text(_y.dump({"maps": maps}, allow_unicode=True,
                                         default_flow_style=False, sort_keys=False))


# Re-exports for routers (mypy strict requires explicit __all__ for underscore names)
__all__ = [
    "create_app",
    "_ERA_KEYS", "_ERA_LABELS_DE", "_ERA_LABELS_EN",
    "_STRUCTURE_ERAS", "_CRITTER_ERAS", "_TOWER_ERAS",
    "_CONFIG_DIR", "_SAVED_MAPS_PATH",
    "_load_saved_maps", "_write_saved_maps",
    "_update_effects_in_yaml", "_load_era_effects",
    "_is_recently_active", "_stub_message",
    "_critter_groups", "_structure_groups", "_knowledge_groups", "_building_groups",
]


# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------

def create_app(services: "Services") -> FastAPI:
    """Factory: create and return a configured FastAPI application.

    The ``services`` reference is passed to each sub-router factory so every
    endpoint can access game logic without global state.
    """
    app = FastAPI(title="E3 Game Server", version="1.0.0")

    limiter = Limiter(key_func=get_remote_address, default_limits=["120/minute"])
    app.state.limiter = limiter

    @app.exception_handler(RateLimitExceeded)
    async def _rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
        return JSONResponse({"detail": "Rate limit exceeded. Please slow down."}, status_code=429)

    app.add_middleware(SlowAPIMiddleware)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def request_id_middleware(request: Request, call_next: Any) -> Any:
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=request_id)
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

    @app.middleware("http")
    async def security_headers(request: Request, call_next: Any) -> Any:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "connect-src 'self' wss: ws:; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: blob:; "
            "font-src 'self' data:; "
            "frame-ancestors 'none'"
        )
        return response

    _last_seen_cache: dict[int, float] = {}

    @app.middleware("http")
    async def track_last_seen(request: Request, call_next: Any) -> Any:
        response = await call_next(request)
        if services.database is not None:
            auth = request.headers.get("authorization", "")
            if auth.startswith("Bearer "):
                try:
                    uid = verify_token(auth[7:])
                    now = time.time()
                    if now - _last_seen_cache.get(uid, 0) > 60:
                        _last_seen_cache[uid] = now
                        await services.database.update_last_seen(uid)
                except Exception:
                    # Invalid/expired token in header — last_seen update is best-effort
                    pass
        return response

    # Wire up sub-routers
    from gameserver.network.routers.auth import make_router as _auth_router
    from gameserver.network.routers.empire import make_router as _empire_router
    from gameserver.network.routers.army import make_router as _army_router
    from gameserver.network.routers.attack import make_router as _attack_router
    from gameserver.network.routers.messages import make_router as _messages_router
    from gameserver.network.routers.replays import make_router as _replays_router
    from gameserver.network.routers.admin import make_router as _admin_router

    app.include_router(_auth_router(services, limiter))
    app.include_router(_empire_router(services))
    app.include_router(_army_router(services))
    app.include_router(_attack_router(services))
    app.include_router(_messages_router(services))
    app.include_router(_replays_router(services))
    app.include_router(_admin_router(services))

    # WebSocket endpoint — stays here
    @app.websocket("/ws")
    async def websocket_endpoint(ws: WebSocket) -> None:
        """Bridge a FastAPI WebSocket to the game server's message router."""
        token = ws.query_params.get("token")
        uid: int | None = None
        if token:
            try:
                uid = verify_token(token)
            except Exception:
                # verify_token raises ValueError (expired) or DecodeError — both mean reject
                await ws.close(code=4001, reason="Invalid token")
                return

        assert services.server is not None
        if uid is None:
            uid = services.server._next_guest_uid
            services.server._next_guest_uid -= 1
        sender_uid: int = uid  # narrows int | None → int for mypy

        await ws.accept()

        adapter = _FastAPIWSAdapter(ws)
        services.server.register_session(sender_uid, adapter)  # type: ignore[arg-type]

        await ws.send_json({
            "type": "welcome",
            "temp_uid": sender_uid,
            "via": "rest_ws",
        })

        log.info("REST-WS client connected: uid=%d", sender_uid)

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
                    response = await services.server._router.route(data, sender_uid)
                except Exception as exc:
                    log.exception("REST-WS handler error: type=%s uid=%d", msg_type, sender_uid)
                    err = {"type": "error", "message": str(exc)}
                    if request_id is not None:
                        err["request_id"] = request_id
                    await ws.send_json(err)
                    continue

                if response is not None:
                    if request_id is not None:
                        response["request_id"] = request_id
                    await ws.send_json(response)

                    if msg_type == "auth_request" and response.get("success") and response.get("uid"):
                        real_uid = response["uid"]
                        services.server.unregister_session(adapter)  # type: ignore[arg-type]
                        services.server.register_session(real_uid, adapter)  # type: ignore[arg-type]
                        sender_uid = real_uid

        except WebSocketDisconnect:
            log.info("REST-WS client disconnected: uid=%d", sender_uid)
        except Exception as e:
            log.error("REST-WS error: uid=%d error=%s", sender_uid, e)
        finally:
            services.server.unregister_session(adapter)  # type: ignore[arg-type]

    # Register web client routes + static file mount (must be last — catch-all)
    import os as _os
    from gameserver.network.web_server import register_web_routes as _reg
    _web_dir = Path(_os.environ.get("WEB_DIR", "")) if _os.environ.get("WEB_DIR") else (
        Path(__file__).resolve().parent.parent.parent.parent.parent / "web"
    )
    if not _web_dir.is_dir():
        _web_dir = Path(__file__).resolve().parent.parent.parent.parent / "web"
    _reg(app, _web_dir)

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
                # WebSocket may close mid-send — mark closed and stop further sends
                self._closed = True

    async def close(self, code: int = 1000, reason: str = "") -> None:
        if not self._closed:
            self._closed = True
            try:
                await self._ws.close(code=code, reason=reason)
            except Exception:
                # Already closed by the client — nothing to do
                pass

    @property
    def remote_address(self) -> tuple[str, int]:
        client = self._ws.client
        return (client.host, client.port) if client else ("unknown", 0)
