"""Attack router — /api/attack/*, /api/spy-attack, /api/spy-reports."""
from __future__ import annotations

import time
from typing import Any, TYPE_CHECKING

from fastapi import APIRouter, Depends, Request
from slowapi import Limiter

from gameserver.network.jwt_auth import get_current_uid
from gameserver.network.rest_models import AttackRequest, SpyAttackRequest
from gameserver.network.rest_api import _stub_message

if TYPE_CHECKING:
    from gameserver.main import Services


def make_router(services: "Services", limiter: Limiter) -> APIRouter:
    router = APIRouter()
    assert services.attack_service is not None
    attack_service = services.attack_service  # non-optional for closure narrowing

    @router.post("/api/attack")
    @limiter.limit("20/minute")
    async def attack(request: Request, body: AttackRequest, uid: int = Depends(get_current_uid)) -> dict[str, Any]:
        from gameserver.network.handlers import handle_new_attack
        msg = _stub_message(target_uid=body.target_uid, opponent_name=body.opponent_name, army_aid=body.army_aid)
        resp = await handle_new_attack(msg, uid)
        return resp or {"success": False, "error": "No response"}

    @router.post("/api/spy-attack")
    @limiter.limit("20/minute")
    async def spy_attack(request: Request, body: SpyAttackRequest, uid: int = Depends(get_current_uid)) -> dict[str, Any]:
        from gameserver.network.handlers import handle_spy_attack
        msg = _stub_message(target_uid=body.target_uid, opponent_name=body.opponent_name)
        resp = await handle_spy_attack(msg, uid)
        return resp or {"success": False, "error": "No response"}

    @router.get("/api/spy-reports")
    async def get_spy_reports(uid: int = Depends(get_current_uid)) -> dict[str, Any]:
        """Return the current player's latest-per-target stored spy reports."""
        assert services.database is not None
        reports = await services.database.get_spy_reports_for(uid)
        return {"reports": reports}

    @router.post("/api/attack/{attack_id}/skip-siege")
    async def skip_siege(attack_id: int, uid: int = Depends(get_current_uid)) -> dict[str, Any]:
        """Immediately end the siege phase — only callable by the defender."""
        result = attack_service.skip_siege(attack_id, uid)
        if isinstance(result, str):
            return {"success": False, "error": result}
        attack, remaining_before_skip = result
        if services.database:
            await services.database.record_window_event(
                kind="skip_siege", key_uid=attack.defender_uid, ts=int(time.time()),
                ref_id=attack.attacker_uid, magnitude=remaining_before_skip,
            )
        return {"success": True, "attack_id": attack.attack_id, "phase": attack.phase.value}

    return router
