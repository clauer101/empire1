"""Attack router — /api/attack/*, /api/spy-attack."""
from __future__ import annotations

from typing import Any, TYPE_CHECKING

from fastapi import APIRouter, Depends

from gameserver.network.jwt_auth import get_current_uid
from gameserver.network.rest_models import AttackRequest, SpyAttackRequest
from gameserver.network.rest_api import _stub_message

if TYPE_CHECKING:
    from gameserver.main import Services


def make_router(services: "Services") -> APIRouter:
    router = APIRouter()

    @router.post("/api/attack")
    async def attack(body: AttackRequest, uid: int = Depends(get_current_uid)) -> dict[str, Any]:
        from gameserver.network.handlers import handle_new_attack
        msg = _stub_message(target_uid=body.target_uid, opponent_name=body.opponent_name, army_aid=body.army_aid)
        resp = await handle_new_attack(msg, uid)
        return resp or {"success": False, "error": "No response"}

    @router.post("/api/spy-attack")
    async def spy_attack(body: SpyAttackRequest, uid: int = Depends(get_current_uid)) -> dict[str, Any]:
        from gameserver.network.handlers import handle_spy_attack
        msg = _stub_message(target_uid=body.target_uid, opponent_name=body.opponent_name)
        resp = await handle_spy_attack(msg, uid)
        return resp or {"success": False, "error": "No response"}

    @router.post("/api/attack/{attack_id}/skip-siege")
    async def skip_siege(attack_id: int, uid: int = Depends(get_current_uid)) -> dict[str, Any]:
        """Immediately end the siege phase — only callable by the defender."""
        result = services.attack_service.skip_siege(attack_id, uid)
        if isinstance(result, str):
            return {"success": False, "error": result}
        return {"success": True, "attack_id": result.attack_id, "phase": result.phase.value}

    return router
