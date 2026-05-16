"""Empire router — /api/empire/*, /api/empires, /api/map/*, /api/era-map."""
from __future__ import annotations

import logging
from typing import Any, TYPE_CHECKING

from fastapi import APIRouter, Depends

from gameserver.network.jwt_auth import get_current_uid
from gameserver.network.rest_models import (
    BuildRequest,
    BuyTileRequest,
    CitizenDistribution,
    MapSaveBody,
    ChooseRulerRequest,
    RulerSkillUpRequest,
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

log = logging.getLogger(__name__)

if TYPE_CHECKING:
    from gameserver.main import Services


def _build_end_rally_info_for_era_map(gc: Any, empire_service: Any = None) -> dict[str, Any]:
    from gameserver.engine.global_state import (
        get_end_criterion_activated, is_end_rally_active, end_rally_seconds_remaining,
        get_end_criterion_empire_uid, get_end_criterion_empire_name,
    )
    from gameserver.network.rest_api import _item_names
    if gc is None:
        return {"active": False, "effects": {}, "duration": 0.0, "end_criterion": "", "end_criterion_name": ""}
    active = is_end_rally_active(gc)
    activated = get_end_criterion_activated()
    culture_leader_name = ""
    if empire_service is not None:
        try:
            from gameserver.engine.ai_service import AI_UID
            empires = [e for e in empire_service.all_empires.values() if e.uid != AI_UID]
            if empires:
                top = max(empires, key=lambda e: e.resources.get("culture", 0.0))
                culture_leader_name = top.name
        except Exception as exc:
            log.warning("culture_leader_name failed: %s", exc)
    return {
        "active": active,
        "effects": dict(gc.end_rally_effects),
        "duration": gc.end_rally_duration,
        "end_criterion": gc.end_criterion,
        "end_criterion_name": _item_names.get(gc.end_criterion, gc.end_criterion),
        "seconds_remaining": round(end_rally_seconds_remaining(gc), 0),
        "activated_at": activated.isoformat() if activated else None,
        "triggered_by_uid": get_end_criterion_empire_uid(),
        "triggered_by_name": get_end_criterion_empire_name(),
        "culture_leader_name": culture_leader_name,
    }


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

    @router.get("/api/empire/effect-sources")
    async def get_effect_sources(uid: int = Depends(get_current_uid)) -> dict[str, Any]:
        from gameserver.network.handlers.auth import handle_effect_sources_request
        return handle_effect_sources_request(uid)

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
                "artifact_count": len(empire.artifacts),
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
            "end_rally": _build_end_rally_info_for_era_map(gc, services.empire_service),
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

    @router.post("/api/empire/ruler/skill-up")
    async def ruler_skill_up(body: RulerSkillUpRequest, uid: int = Depends(get_current_uid)) -> dict[str, Any]:
        skill = body.skill
        if skill not in ("q", "w", "e", "r"):
            return {"success": False, "error": "Invalid skill"}
        empire = empire_service.get(uid)
        if empire is None:
            return {"success": False, "error": "Empire not found"}
        ruler = empire.ruler
        level = empire_service.ruler_level_from_xp(ruler.xp)
        total_points = ruler.q + ruler.w + ruler.e + ruler.r
        if total_points >= level:
            return {"success": False, "error": "No skill points available"}
        current = getattr(ruler, skill)
        if skill in ("q", "w", "e"):
            if current >= 5:
                return {"success": False, "error": "Skill already at maximum level"}
            if current + 1 == 5 and level < 9:
                return {"success": False, "error": "Ruler level 9 required for skill level 5"}
        else:  # r
            unlock_levels = [6, 11, 16]
            if current >= len(unlock_levels):
                return {"success": False, "error": "Skill already at maximum level"}
            if level < unlock_levels[current]:
                return {"success": False, "error": f"Ruler level {unlock_levels[current]} required"}
        setattr(ruler, skill, current + 1)
        # Pay out one-shot lump sums from the newly reached skill level
        ruler_def = empire_service._rulers.get(ruler.type, {})
        new_level_list: list[dict[str, object]] = ruler_def.get(skill, [])
        if current < len(new_level_list):  # current = old level = index of new level
            lvl_fx = new_level_list[current]
            gold_lump = float(lvl_fx.get("gold_lump_sum_on_skill_up", 0.0))
            culture_lump = float(lvl_fx.get("culture_lump_sum_on_skill_up", 0.0))
            if gold_lump > 0:
                empire.resources["gold"] = empire.resources.get("gold", 0.0) + gold_lump
            if culture_lump > 0:
                empire.resources["culture"] = empire.resources.get("culture", 0.0) + culture_lump
        empire_service.recalculate_effects(empire)
        return {"success": True}

    @router.post("/api/empire/ruler/choose")
    async def choose_ruler(body: ChooseRulerRequest, uid: int = Depends(get_current_uid)) -> dict[str, Any]:
        empire = empire_service.get(uid)
        if empire is None:
            return {"success": False, "error": "Empire not found"}
        if empire.ruler.type:
            return {"success": False, "error": "Ruler already chosen"}
        rulers = empire_service._rulers if empire_service else {}
        if body.ruler_iid not in rulers:
            return {"success": False, "error": "Unknown ruler"}
        ruler_def = rulers[body.ruler_iid]
        empire.ruler.type = body.ruler_iid
        empire.ruler.name = ruler_def.get("name", body.ruler_iid)
        return {"success": True}

    @router.get("/api/global-map")
    async def global_map() -> dict[str, Any]:
        """Return all empires with their hex_map tiles for the global map view."""
        result = []
        for empire in empire_service.all_empires.values():
            tiles = []
            for key, tile_type in empire.hex_map.items():
                try:
                    q, r = (int(v) for v in key.split(","))
                    tiles.append({"q": q, "r": r, "type": tile_type})
                except (ValueError, AttributeError):
                    continue
            if tiles:
                result.append({"uid": empire.uid, "name": empire.name, "tiles": tiles})
        return {"empires": result}

    return router
