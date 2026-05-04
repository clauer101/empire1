"""Empire router — /api/empire/*, /api/empires, /api/map/*, /api/era-map."""
from __future__ import annotations

from typing import Any, TYPE_CHECKING

from fastapi import APIRouter, Depends

from gameserver.network.jwt_auth import get_current_uid
from gameserver.network.rest_models import (
    BuildRequest,
    BuyTileRequest,
    CitizenDistribution,
    MapSaveBody,
)
from gameserver.network.rest_api import (
    _stub_message,
    _is_recently_active,
    _ERA_KEYS,
    _ERA_LABELS_DE,
    _ERA_LABELS_EN,
    _critter_groups,
    _structure_groups,
    _knowledge_groups,
    _building_groups,
)
import gameserver.network.rest_api as _rest_api

if TYPE_CHECKING:
    from gameserver.main import Services


def make_router(services: "Services") -> APIRouter:
    router = APIRouter()
    assert services.empire_service is not None
    empire_service = services.empire_service  # non-optional for closure narrowing

    @router.get("/api/empire/summary")
    async def get_summary(uid: int = Depends(get_current_uid)) -> dict[str, Any]:
        from gameserver.network.handlers import handle_summary_request
        msg = _stub_message()
        resp = await handle_summary_request(msg, uid)
        if resp and services.database:
            resp["unread_messages"] = await services.database.unread_count(uid)
        return resp or {"error": "No data"}

    @router.get("/api/empire/items")
    async def get_items(uid: int = Depends(get_current_uid)) -> dict[str, Any]:
        from gameserver.network.handlers import handle_item_request
        msg = _stub_message()
        resp = await handle_item_request(msg, uid)
        return resp or {"error": "No data"}

    @router.get("/api/empire/military")
    async def get_military(uid: int = Depends(get_current_uid)) -> dict[str, Any]:
        from gameserver.network.handlers import handle_military_request
        msg = _stub_message()
        resp = await handle_military_request(msg, uid)
        return resp or {"error": "No data"}

    @router.get("/api/empires")
    async def list_empires(uid: int = Depends(get_current_uid)) -> dict[str, Any]:
        """Return all known empires sorted by culture points descending."""
        uid_to_user: dict[int, str] = {}
        uid_to_last_seen: dict[int, str] = {}
        if services.database is not None:
            for row in await services.database.list_users():
                uid_to_user[row["uid"]] = row["username"]
                uid_to_last_seen[row["uid"]] = row.get("last_seen", "")
        connected_uids: list[int] = services.server.connected_uids if services.server else []
        empires = []
        for empire in empire_service.all_empires.values():
            if empire.uid != uid and empire.uid not in uid_to_user:
                continue
            era_key = empire_service.get_current_era(empire)
            era_idx = empire_service._ERA_ORDER.index(era_key) + 1 if era_key in empire_service._ERA_ORDER else 1
            empires.append({
                "uid": empire.uid,
                "name": empire.name,
                "username": uid_to_user.get(empire.uid, ""),
                "culture": round(empire.resources.get("culture", 0.0), 1),
                "is_self": empire.uid == uid,
                "era": era_idx,
                "online": empire.uid in connected_uids or _is_recently_active(uid_to_last_seen.get(empire.uid, ""), 60),
                "artefact_count": len(empire.artefacts),
            })
        empires.sort(key=lambda e: float(e.get("culture") or 0),  # type: ignore[arg-type]
                     reverse=True)
        return {"empires": empires}

    @router.post("/api/empire/build")
    async def build_item(body: BuildRequest, uid: int = Depends(get_current_uid)) -> dict[str, Any]:
        from gameserver.network.handlers import handle_new_item
        msg = _stub_message(iid=body.iid)
        resp = await handle_new_item(msg, uid)
        return resp or {"success": False, "error": "No response"}

    @router.post("/api/empire/citizen/upgrade")
    async def citizen_upgrade(uid: int = Depends(get_current_uid)) -> dict[str, Any]:
        from gameserver.network.handlers import handle_citizen_upgrade
        msg = _stub_message()
        resp = await handle_citizen_upgrade(msg, uid)
        return resp or {"success": False, "error": "No response"}

    @router.put("/api/empire/citizen")
    async def change_citizen(body: CitizenDistribution, uid: int = Depends(get_current_uid)) -> dict[str, Any]:
        from gameserver.network.handlers import handle_change_citizen
        msg = _stub_message(citizens=body.model_dump())
        resp = await handle_change_citizen(msg, uid)
        return resp or {"success": False, "error": "No response"}

    @router.get("/api/map")
    async def load_map(uid: int = Depends(get_current_uid)) -> dict[str, Any]:
        from gameserver.network.handlers import handle_map_load_request
        msg = _stub_message()
        resp = await handle_map_load_request(msg, uid)
        return resp or {"tiles": {}}

    @router.put("/api/map")
    async def save_map(body: MapSaveBody, uid: int = Depends(get_current_uid)) -> dict[str, Any]:
        from gameserver.network.handlers import handle_map_save_request
        from gameserver.models.messages import MapSaveRequest
        msg = MapSaveRequest(type="map_save_request", sender=uid, tiles=body.tiles)
        resp = await handle_map_save_request(msg, uid)
        return resp or {"success": False, "error": "No response"}

    @router.post("/api/map/buy-tile")
    async def buy_tile(body: BuyTileRequest, uid: int = Depends(get_current_uid)) -> dict[str, Any]:
        from gameserver.network.handlers import handle_buy_tile_request
        msg = _stub_message(q=body.q, r=body.r)
        resp = await handle_buy_tile_request(msg, uid)
        return resp or {"success": False, "error": "No response"}

    @router.get("/api/era-map")
    async def get_era_map() -> dict[str, Any]:
        """Return era order + per-era item IIDs for all categories (no auth required)."""
        gc = services.empire_service._gc if services.empire_service else None
        su = gc.structure_upgrades if gc else None
        cu = gc.critter_upgrades if gc else None
        return {
            "eras": _ERA_KEYS,
            "labels_de": _ERA_LABELS_DE,
            "labels_en": _ERA_LABELS_EN,
            "critters":   _critter_groups,
            "structures": _structure_groups,
            "knowledge":  _knowledge_groups,
            "buildings":  _building_groups,
            "era_effects": _rest_api._era_effects_data,
            "structure_upgrade_def": {
                "damage": su.damage, "range": su.range, "reload": su.reload,
                "effect_duration": su.effect_duration, "effect_value": su.effect_value,
            } if su else {},
            "critter_upgrade_def": {
                "health": cu.health, "speed": cu.speed, "armour": cu.armour,
            } if cu else {},
            "item_upgrade_base_costs": gc.item_upgrade_base_costs if gc else [],
            "wave_era_costs": gc.prices.wave_era_costs if gc else [],
            "critter_slot_params": {"u": gc.prices.critter_slot.u, "y": gc.prices.critter_slot.y, "z": gc.prices.critter_slot.z, "v": gc.prices.critter_slot.v} if gc else {},
        }

    return router
