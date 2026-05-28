"""Empire router — /api/empire/*, /api/empires, /api/map/*, /api/era-map."""
from __future__ import annotations

import logging
from typing import Any, TYPE_CHECKING

from fastapi import APIRouter, Depends, Request
from slowapi import Limiter

from gameserver.network.jwt_auth import get_current_uid
from gameserver.engine.global_state import (
    get_season_number, get_season_title,
    get_next_season_start, get_next_season_leadtime, get_next_season_title,
    is_season_reset_triggered,
)
from gameserver.models.hex import HexCoord
from gameserver.network.rest_models import (
    BuildRequest,
    BuyTileRequest,
    CitizenDistribution,
    MapSaveBody,
    ChooseRulerRequest,
    RulerSkillUpRequest,
    RenameEmpireRequest,
)
from gameserver.network.rest_api import (
    _stub_message,
    _is_recently_active,
    _ERA_KEYS,
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


def make_router(services: "Services", limiter: Limiter) -> APIRouter:
    router = APIRouter()
    assert services.empire_service is not None
    empire_service = services.empire_service  # non-optional for closure narrowing

    @router.get("/api/empire/summary")
    @limiter.limit("300/minute")
    async def get_summary(request: Request, uid: int = Depends(get_current_uid)) -> dict[str, Any]:
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
    @limiter.limit("120/minute")
    async def list_empires(request: Request, uid: int = Depends(get_current_uid)) -> dict[str, Any]:
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
            bot_prob = (
                services.bot_detector.get_probability(empire.uid)
                if services.bot_detector else 0.5
            )
            empires.append({
                "uid": empire.uid,
                "name": empire.name,
                "username": uid_to_user.get(empire.uid, ""),
                "culture": round(empire.resources.get("culture", 0.0), 1),
                "is_self": empire.uid == uid,
                "era": era_idx,
                "online": empire.uid in connected_uids or _is_recently_active(uid_to_last_seen.get(empire.uid, ""), 60),
                "artifact_count": len(empire.artifacts),
                "bot_probability": round(bot_prob, 3),
            })
        empires.sort(key=lambda e: float(e.get("culture") or 0),  # type: ignore[arg-type]
                     reverse=True)
        return {"empires": empires}

    @router.post("/api/empire/build")
    @limiter.limit("60/minute")
    async def build_item(request: Request, body: BuildRequest, uid: int = Depends(get_current_uid)) -> dict[str, Any]:
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

    @router.post("/api/empire/rename")
    async def rename_empire(body: RenameEmpireRequest, uid: int = Depends(get_current_uid)) -> dict[str, Any]:
        name = body.name.strip()
        if len(name) < 3:
            return {"success": False, "error": "Name must be at least 3 characters"}
        if len(name) > 40:
            return {"success": False, "error": "Name too long (max 40 characters)"}
        empire = services.empire_service.all_empires.get(uid) if services.empire_service else None
        if empire is None:
            return {"success": False, "error": "Empire not found"}
        empire.name = name
        log.info("Empire renamed: uid=%d new_name=%r", uid, name)
        return {"success": True}

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
            "season_number": get_season_number(),
            "season_title": get_season_title(),
            "next_season_start": get_next_season_start(),
            "next_season_leadtime": get_next_season_leadtime(),
            "next_season_title": get_next_season_title(),
            "season_reset_triggered": is_season_reset_triggered(),
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
        if empire.get_effect("ruler_unlock", 0) <= 0:
            return {"success": False, "error": "Ruler not yet unlocked — research the required knowledge first"}
        rulers = empire_service._rulers if empire_service else {}
        if body.ruler_iid not in rulers:
            return {"success": False, "error": "Unknown ruler"}
        ruler_def = rulers[body.ruler_iid]
        empire.ruler.type = body.ruler_iid
        empire.ruler.name = ruler_def.get("name", body.ruler_iid)
        return {"success": True}

    @router.post("/api/empire/ruler/dismiss")
    async def dismiss_ruler(uid: int = Depends(get_current_uid)) -> dict[str, Any]:
        empire = empire_service.get(uid)
        if empire is None:
            return {"success": False, "error": "Empire not found"}
        if empire.ruler.r > 0:
            return {"success": False, "error": "Ruler cannot be changed once the R skill has been upgraded"}
        from gameserver.models.empire import Ruler
        empire.ruler = Ruler()
        return {"success": True}

    @router.get("/api/map/neighbors")
    async def map_neighbors(
        uid: int = Depends(get_current_uid),
        q0: int | None = None,
        r0: int | None = None,
        q1: int | None = None,
        r1: int | None = None,
        spectating: int = 0,
        defender_uid: int | None = None,
    ) -> dict[str, Any]:
        """Return non-owned tiles within the fog radius of the empire border.

        When viewport bounds ``(q0,r0)-(q1,r1)`` (defender-local axial coords)
        are supplied, only tiles inside that rectangle are returned, so the
        payload stays bounded regardless of territory size or fog radius.
        Owner lookup uses the shared world tile index (O(1) per tile) instead
        of rescanning every empire.
        """
        lookup_uid = defender_uid if spectating and defender_uid is not None else uid
        empire = empire_service.get(lookup_uid)
        if not empire or not empire.hex_map:
            return {"neighbor_tiles": []}

        own_keys: set[str] = set(empire.hex_map.keys())
        own_coords = {HexCoord(*map(int, k.split(","))) for k in own_keys}

        # Border = own tiles that have ≥1 non-own neighbor
        border: set[HexCoord] = set()
        for c in own_coords:
            for nb in c.neighbors():
                if f"{nb.q},{nb.r}" not in own_keys:
                    border.add(c)
                    break

        gc = services.empire_service._gc if services.empire_service else None
        from gameserver.util.effects import MAP_VISION_RADIUS_OFFSET
        if spectating:
            radius = 0
        else:
            base_radius = gc.base_map_vision_radius if gc else 1
            vision_offset = int(empire.effects.get(MAP_VISION_RADIUS_OFFSET, 0))
            radius = base_radius + vision_offset

        # Strict viewport rect (defender-local). Missing → fall back to the
        # territory bounding box padded by the fog radius.
        if q0 is not None and r0 is not None and q1 is not None and r1 is not None:
            lo_q, hi_q = min(q0, q1), max(q0, q1)
            lo_r, hi_r = min(r0, r1), max(r0, r1)
        else:
            qs = [c.q for c in own_coords]
            rs = [c.r for c in own_coords]
            lo_q, hi_q = min(qs) - radius, max(qs) + radius
            lo_r, hi_r = min(rs) - radius, max(rs) + radius

        # BFS is clipped to the viewport padded by `radius`. Any tile within
        # `radius` of the border that lands in the viewport stays reachable
        # via a shortest path inside this region, so cost is O((vp+radius)²)
        # rather than O(radius² · territory).
        blo_q, bhi_q = lo_q - radius, hi_q + radius
        blo_r, bhi_r = lo_r - radius, hi_r + radius

        def _in_bfs(c: HexCoord) -> bool:
            return blo_q <= c.q <= bhi_q and blo_r <= c.r <= bhi_r

        visible: set[HexCoord] = set()
        frontier = {c for c in border if _in_bfs(c)}
        for _ in range(radius):
            next_frontier: set[HexCoord] = set()
            for c in frontier:
                for nb in c.neighbors():
                    if nb in visible or not _in_bfs(nb):
                        continue
                    if f"{nb.q},{nb.r}" in own_keys:
                        continue
                    visible.add(nb)
                    next_frontier.add(nb)
            frontier = next_frontier

        world_owner = empire_service.world_tile_owner()

        # Build a lookup: owner_uid → hex_map for structure rendering
        uid_to_empire = {e.uid: e for e in empire_service.all_empires.values()}

        result = []
        for c in visible:
            if not (lo_q <= c.q <= hi_q and lo_r <= c.r <= hi_r):
                continue
            owner_uid = world_owner.get((c.q, c.r))
            if owner_uid == uid:
                owner_uid = None
            # Include tile type if we can look it up from the owner's hex_map
            iid = None
            tile_type = None
            if owner_uid is not None:
                owner_emp = uid_to_empire.get(owner_uid)
                if owner_emp:
                    tile_val = owner_emp.hex_map.get(f"{c.q},{c.r}")
                    if isinstance(tile_val, dict):
                        tile_type = tile_val.get("type")
                        iid = tile_val.get("iid") or tile_type
                    elif isinstance(tile_val, str):
                        tile_type = tile_val
                        iid = tile_val
            result.append({"q": c.q, "r": c.r, "uid": owner_uid, "iid": iid, "tile_type": tile_type})

        # Compute paths for all visible enemy empires
        from gameserver.engine.hex_pathfinding import find_path_from_spawn_to_castle
        visible_uids = {r["uid"] for r in result if r["uid"] is not None}
        enemy_paths = {}
        for euid in visible_uids:
            owner_emp = uid_to_empire.get(euid)
            if not owner_emp:
                continue
            normalized: dict[str, str] = {}
            for k, v in owner_emp.hex_map.items():
                if isinstance(v, dict):
                    tile_type = v.get("type")
                    normalized[k] = tile_type if isinstance(tile_type, str) else ""
                else:
                    normalized[k] = v
            path = find_path_from_spawn_to_castle(normalized)
            if path:
                enemy_paths[euid] = [{"q": c.q, "r": c.r} for c in path]

        return {"neighbor_tiles": result, "vision_radius": radius, "enemy_paths": enemy_paths}

    @router.get("/api/global-map")
    async def global_map(
        q0: int | None = None,
        r0: int | None = None,
        q1: int | None = None,
        r1: int | None = None,
    ) -> dict[str, Any]:
        """Return empires with their hex_map tiles, offset to world spawn pos.

        When world-space bounds ``(q0,r0)-(q1,r1)`` are supplied only tiles
        inside that rectangle are returned, keeping the payload bounded for
        large worlds; empires with no tile in view are omitted.
        """
        clip = (
            q0 is not None and r0 is not None
            and q1 is not None and r1 is not None
        )
        if clip:
            assert q0 is not None and r0 is not None
            assert q1 is not None and r1 is not None
            lo_q, hi_q = min(q0, q1), max(q0, q1)
            lo_r, hi_r = min(r0, r1), max(r0, r1)

        result = []
        for empire in empire_service.all_empires.values():
            tiles = []
            castle_q, castle_r = 0, 0
            for key, tile_type in empire.hex_map.items():
                try:
                    wq, wr = (int(v) for v in key.split(","))
                except (ValueError, AttributeError):
                    continue
                if tile_type == "castle":
                    castle_q, castle_r = wq, wr
                if clip and not (lo_q <= wq <= hi_q and lo_r <= wr <= hi_r):
                    continue
                tiles.append({"q": wq, "r": wr, "type": tile_type})
            if tiles:
                result.append({
                    "uid": empire.uid,
                    "name": empire.name,
                    "origin": {"q": castle_q, "r": castle_r},
                    "tiles": tiles,
                })
        return {"empires": result}

    @router.get("/api/season-results")
    async def get_season_results(uid: int = Depends(get_current_uid)) -> dict[str, Any]:
        """Return end-of-season leaderboard stats for all player empires."""
        from gameserver.engine.ai_service import AI_UID
        import math

        upgrades = empire_service._upgrades.items  # iid → ItemDetails

        results = []
        for e in empire_service.all_empires.values():
            if e.uid == AI_UID:
                continue

            # Tower gold: sum gold costs of all structures placed on the hex map
            # hex_map values are plain strings (the IID / tile type)
            NON_STRUCTURE = {"path", "castle", "spawnpoint", "empty", "void", "blocked", ""}
            tower_gold = 0.0
            for tile_val in e.hex_map.values():
                iid = tile_val.get("type") if isinstance(tile_val, dict) else tile_val
                if iid and iid not in NON_STRUCTURE and iid in upgrades:
                    tower_gold += upgrades[iid].costs.get("gold", 0.0)

            # Army gold: sum critter value × estimated critter count per wave
            army_gold = 0.0
            for army in e.armies:
                for wave in army.waves:
                    item = upgrades.get(wave.iid)
                    if item:
                        slot_cost = item.slots if item.slots > 0 else 1.0
                        count = math.floor(wave.slots / slot_cost)
                        army_gold += item.value * count

            # Workshop: total gold invested (base_cost × Σn² for n=1..N per item)
            costs_list = empire_service._gc.item_upgrade_base_costs if empire_service._gc else []
            workshop_gold = 0.0
            for iid, stats in e.item_upgrades.items():
                n = sum(stats.values())
                if n <= 0:
                    continue
                era_idx = empire_service._item_era_index.get(iid, 0)
                base_cost = costs_list[era_idx] if era_idx < len(costs_list) else (costs_list[-1] if costs_list else 0.0)
                workshop_gold += base_cost * n * (n + 1) * (2 * n + 1) / 6


            # Research: total effort and count of completed knowledge items
            completed_knowledge = [iid for iid, v in e.knowledge.items() if v == 0.0 and iid in upgrades]
            research_effort = sum(upgrades[iid].effort for iid in completed_knowledge)
            research_count = len(completed_knowledge)

            # Buildings: total effort and count of completed buildings
            completed_buildings = [iid for iid, v in e.buildings.items() if v == 0.0 and iid in upgrades]
            buildings_effort = sum(upgrades[iid].effort for iid in completed_buildings)
            buildings_count = len(completed_buildings)

            # Tile count: non-void, non-empty tiles (actual owned territory)
            tile_count = sum(
                1 for v in e.hex_map.values()
                if (v.get("type") if isinstance(v, dict) else v) not in ("void", "empty", None, "")
            )

            results.append({
                "uid": e.uid,
                "name": e.name,
                "culture": round(e.resources.get("culture", 0.0), 1),
                "artifacts": len(e.artifacts),
                "tower_gold": round(tower_gold, 1),
                "army_gold": round(army_gold, 1),
                "tile_count": tile_count,
                "workshop_gold": round(workshop_gold),
                "research_effort": round(research_effort),
                "research_count": research_count,
                "buildings_effort": round(buildings_effort),
                "buildings_count": buildings_count,
            })

        results.sort(
            key=lambda x: x["culture"] if isinstance(x["culture"], (int, float)) else 0.0,
            reverse=True,
        )

        era_firsts: list[dict[str, Any]] = []
        # Merge runtime stats and supplemental data into each result.
        if services.database is not None:
            all_stats = await services.database.get_all_empire_stats()
            stats_by_uid = {row["uid"]: row for row in all_stats}
            hold_rows = await services.database.get_longest_artifact_hold_per_uid()
            hold_by_uid = {row["uid"]: row["longest_hold_secs"] for row in hold_rows}
            era_firsts = await services.database.get_era_firsts()
            runtime_fields = [
                "critters_killed", "towers_placed", "towers_sold",
                "spies_sent", "artifacts_stolen", "defense_gold_earned",
                "culture_stolen", "research_stolen", "culture_won", "research_won",
                "longest_battle_ms", "first_era_reached", "peak_artifacts_held",
                "attacks_won_human", "attacks_lost_human",
                "defense_won_human", "defense_lost_human",
                "defense_won_ai", "defense_lost_ai",
                "critter_upgrade_levels", "tower_upgrade_levels",
            ]
            for r in results:
                row = stats_by_uid.get(r["uid"]) or {}
                for f in runtime_fields:
                    r[f] = row.get(f, 0) or 0
                r["attacks_sent_human"] = (r["attacks_won_human"] or 0) + (r["attacks_lost_human"] or 0)  # type: ignore[operator]
                r["attacks_received_human"] = (r["defense_won_human"] or 0) + (r["defense_lost_human"] or 0)  # type: ignore[operator]
                r["longest_artifact_hold_secs"] = round(hold_by_uid.get(r["uid"], 0) or 0)

        from gameserver.util.eras import ERA_ORDER as _ERA_ORDER_LIST
        return {
            "season_number": get_season_number(),
            "season_title": get_season_title(),
            "next_season_start": get_next_season_start(),
            "empires": results,
            "era_firsts": era_firsts,
            "era_order": _ERA_ORDER_LIST,
        }

    return router
