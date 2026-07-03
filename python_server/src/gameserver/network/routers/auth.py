"""Auth router — /api/auth/login, /api/auth/signup."""
from __future__ import annotations

import structlog
from typing import Any, TYPE_CHECKING

from fastapi import APIRouter, Request
from slowapi import Limiter

from gameserver.network.jwt_auth import create_token
from gameserver.network.rest_models import LoginRequest, LoginResponse, SignupRequest, SignupResponse

log = structlog.get_logger(__name__)

if TYPE_CHECKING:
    from gameserver.main import Services


def make_router(services: "Services", limiter: Limiter) -> APIRouter:
    router = APIRouter()
    assert services.auth_service is not None
    assert services.empire_service is not None
    auth_service = services.auth_service
    empire_service = services.empire_service

    @router.post("/api/auth/login", response_model=LoginResponse)
    @limiter.limit("30/minute")
    async def login(request: Request, body: LoginRequest) -> dict[str, Any]:
        from gameserver.network.handlers import _build_empire_summary, _build_session_state
        uid = await auth_service.login(body.username, body.password)
        if uid is not None:
            token = create_token(uid)
            session_state = _build_session_state(uid)
            empire = empire_service.get(uid)
            if empire is None and services.database is not None:
                # Empire was wiped (season reset) — recreate fresh empire for this account
                from gameserver.network.handlers import _create_empire_for_new_user
                user_row = await services.database.get_user_by_uid(uid)
                if user_row is not None:
                    await _create_empire_for_new_user(
                        uid, user_row["username"], user_row["empire_name"] or user_row["username"]
                    )
                    empire = empire_service.get(uid)
                    # Restore trophies and apply their effects (including increase_start_gold)
                    if empire is not None:
                        trophy_rows = await services.database.get_trophy_rows(uid)
                        for row in trophy_rows:
                            empire.trophies[row["iid"]] = {
                                "earned_at": row["earned_at"],
                                "season": row["season"],
                            }
                        # Apply trophy effects to starting state
                        extra_gold = 0.0
                        if services.empire_service is not None:
                            for iid in empire.trophies:
                                fx = services.empire_service._upgrades.get_effects(iid)
                                extra_gold += fx.get("increase_start_gold", 0.0)
                        if extra_gold:
                            empire.resources["gold"] = empire.resources.get("gold", 0.0) + extra_gold
                            log.info("Trophy bonus: uid=%d +%g start gold from trophies", uid, extra_gold)
                        empire_service.recalculate_effects(empire)
            summary = _build_empire_summary(empire, uid) if empire else None
            if services.database is not None:
                forwarded = request.headers.get("X-Forwarded-For", "")
                ip = forwarded.split(",")[0].strip() if forwarded else (request.client.host if request.client else "")
                await services.database.record_login(uid, ip, body.fingerprint, body.device_id)
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

    @router.post("/api/auth/signup", response_model=SignupResponse)
    @limiter.limit("30/minute")
    async def signup(request: Request, body: SignupRequest) -> dict[str, Any]:
        result = await auth_service.signup(
            body.username, body.password, body.email, body.empire_name,
        )
        if isinstance(result, int):
            from gameserver.network.handlers import _create_empire_for_new_user
            await _create_empire_for_new_user(result, body.username, body.empire_name)
            if body.is_bot:
                empire = empire_service.get(result)
                if empire is not None:
                    empire.is_bot = True
                if services.bot_detector is not None:
                    services.bot_detector.declare_bot(result)
            return {"success": True, "uid": result, "reason": ""}
        return {"success": False, "uid": 0, "reason": result}

    return router
