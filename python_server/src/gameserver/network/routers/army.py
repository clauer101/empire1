"""Army router — /api/army/*, /api/item/buy-upgrade."""
from __future__ import annotations

from typing import Any, TYPE_CHECKING

from fastapi import APIRouter, Depends

from gameserver.network.jwt_auth import get_current_uid
from gameserver.network.rest_models import (
    ArmyCreateRequest,
    ArmyRenameRequest,
    BuyCritterSlotRequest,
    BuyItemUpgradeRequest,
    BuyWaveEraRequest,
    BuyWaveRequest,
    WaveChangeRequest,
)
from gameserver.network.rest_api import _stub_message

if TYPE_CHECKING:
    from gameserver.main import Services


def make_router(services: "Services") -> APIRouter:
    router = APIRouter()

    @router.post("/api/army")
    async def create_army(body: ArmyCreateRequest, uid: int = Depends(get_current_uid)) -> dict[str, Any]:
        from gameserver.network.handlers import handle_new_army
        msg = _stub_message(name=body.name)
        resp = await handle_new_army(msg, uid)
        return resp or {"success": False, "error": "No response"}

    @router.put("/api/army/{aid}")
    async def rename_army(aid: int, body: ArmyRenameRequest, uid: int = Depends(get_current_uid)) -> dict[str, Any]:
        from gameserver.network.handlers import handle_change_army
        msg = _stub_message(aid=aid, name=body.name)
        resp = await handle_change_army(msg, uid)
        return resp or {"success": False, "error": "No response"}

    @router.post("/api/army/{aid}/wave")
    async def add_wave(aid: int, uid: int = Depends(get_current_uid)) -> dict[str, Any]:
        from gameserver.network.handlers import handle_new_wave
        msg = _stub_message(aid=aid)
        resp = await handle_new_wave(msg, uid)
        return resp or {"success": False, "error": "No response"}

    @router.put("/api/army/{aid}/wave/{wave_number}")
    async def change_wave(aid: int, wave_number: int, body: WaveChangeRequest, uid: int = Depends(get_current_uid)) -> dict[str, Any]:
        from gameserver.network.handlers import handle_change_wave
        msg = _stub_message(aid=aid, wave_number=wave_number, critter_iid=body.critter_iid, slots=body.slots)
        resp = await handle_change_wave(msg, uid)
        return resp or {"success": False, "error": "No response"}

    @router.post("/api/army/buy-wave")
    async def buy_wave(body: BuyWaveRequest, uid: int = Depends(get_current_uid)) -> dict[str, Any]:
        from gameserver.network.handlers import handle_buy_wave_request
        msg = _stub_message(aid=body.aid)
        resp = await handle_buy_wave_request(msg, uid)
        return resp or {"success": False, "error": "No response"}

    @router.post("/api/army/buy-critter-slot")
    async def buy_critter_slot(body: BuyCritterSlotRequest, uid: int = Depends(get_current_uid)) -> dict[str, Any]:
        from gameserver.network.handlers import handle_buy_critter_slot_request
        msg = _stub_message(aid=body.aid, wave_number=body.wave_number)
        resp = await handle_buy_critter_slot_request(msg, uid)
        return resp or {"success": False, "error": "No response"}

    @router.post("/api/army/buy-wave-era")
    async def buy_wave_era(body: BuyWaveEraRequest, uid: int = Depends(get_current_uid)) -> dict[str, Any]:
        from gameserver.network.handlers import handle_buy_wave_era_request
        msg = _stub_message(aid=body.aid, wave_number=body.wave_number)
        resp = await handle_buy_wave_era_request(msg, uid)
        return resp or {"success": False, "error": "No response"}

    @router.post("/api/item/buy-upgrade")
    async def buy_item_upgrade(body: BuyItemUpgradeRequest, uid: int = Depends(get_current_uid)) -> dict[str, Any]:
        from gameserver.network.handlers import handle_buy_item_upgrade
        return await handle_buy_item_upgrade(body.iid, body.stat, uid)

    return router
