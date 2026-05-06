"""Admin router — /api/admin/*, /health, /metrics."""
from __future__ import annotations

import asyncio
from typing import Any, TYPE_CHECKING

from fastapi import APIRouter, Depends, HTTPException

from gameserver.network.jwt_auth import get_current_uid
from gameserver.network.rest_models import SavedMapRenameBody
from gameserver.network.rest_api import (
    _is_recently_active,
    _ERA_LABELS_EN,
    _STRUCTURE_ERAS,
    _CRITTER_ERAS,
    _CONFIG_DIR,
    _SAVED_MAPS_PATH,
    _load_saved_maps,
    _write_saved_maps,
    _update_effects_in_yaml,
    _load_era_effects,
)
import gameserver.network.rest_api as _rest_api
import structlog

if TYPE_CHECKING:
    from gameserver.main import Services

log = structlog.get_logger(__name__)

ADMIN_USERNAME = "eem"


def make_router(services: "Services") -> APIRouter:
    router = APIRouter()

    async def require_admin(uid: int = Depends(get_current_uid)) -> int:
        if services.database is not None:
            user = await services.database.get_user_by_uid(uid)
            if user is None or user.get("username", "").lower() != ADMIN_USERNAME:
                raise HTTPException(status_code=403, detail="Admin only")
        return uid

    @router.get("/api/admin/whoami")
    async def whoami(uid: int = Depends(get_current_uid)) -> Any:
        """Return username for the authenticated user (used by tools nav guard)."""
        if services.database is None:
            raise HTTPException(status_code=503, detail="Database unavailable")
        user = await services.database.get_user_by_uid(uid)
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        return {"uid": uid, "username": user.get("username", "")}

    # =================================================================
    # Health
    # =================================================================

    @router.get("/health", include_in_schema=False)
    async def health_liveness() -> dict[str, str]:
        return {"status": "ok"}

    @router.get("/health/ready", include_in_schema=False)
    async def health_readiness() -> Any:
        import time
        try:
            assert services.database is not None
            await services.database.get_user("__health_check__")
        except Exception as exc:
            from fastapi.responses import JSONResponse
            return JSONResponse({"status": "not_ready", "reason": f"db: {exc}"}, status_code=503)
        last_tick = getattr(services, "_last_tick_time", None)
        if last_tick is not None and (time.time() - last_tick) > 10:
            from fastapi.responses import JSONResponse
            return JSONResponse({"status": "not_ready", "reason": "game loop stalled"}, status_code=503)
        return {"status": "ok"}

    # =================================================================
    # Metrics
    # =================================================================

    @router.get("/metrics", include_in_schema=False)
    async def prometheus_metrics() -> Any:
        from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
        from fastapi.responses import Response
        from gameserver.network.metrics import (
            ws_connections, empires_total, attacks_active,
            tick_duration_ms, server_info,
        )
        server_info.info({"version": "1.0"})
        if services.server:
            ws_connections.set(services.server.connection_count)
        if services.empire_service:
            count = sum(1 for e in services.empire_service.all_empires.values() if e.uid > 0)
            empires_total.set(count)
        if services.attack_service:
            attacks_active.set(len(services.attack_service.get_all_attacks()))
        if services.game_loop:
            tick_duration_ms.set(services.game_loop.avg_tick_duration_ms)
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

    # =================================================================
    # Admin endpoints
    # =================================================================

    @router.get("/api/admin/status")
    async def admin_status(_uid: int = Depends(require_admin)) -> dict[str, Any]:
        uid_to_user: dict[int, str] = {}
        uid_to_last_seen: dict[int, str] = {}
        if services.database is not None:
            for row in await services.database.list_users():
                uid_to_user[row["uid"]] = row["username"]
                uid_to_last_seen[row["uid"]] = row.get("last_seen", "")

        connected_uids: list[int] = (
            services.server.connected_uids if services.server else []
        )

        from gameserver.engine.power_service import compute_power
        assert services.empire_service is not None
        assert services.attack_service is not None
        up = services.empire_service._upgrades
        _gc = services.empire_service._gc

        empires_out: list[dict[str, Any]] = []
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
                _path_result = _find_path(_nm)
                _pl = len(_path_result) - 1 if _path_result else None
            except Exception:
                # Pathfinding may fail on incomplete/malformed maps — treat as unknown length
                _pl = None
            power = compute_power(empire, up, path_length=_pl, gc=_gc).to_dict() if up else {"economy": 0, "attack": 0, "defense": 0, "total": 0}

            empires_out.append({
                "uid": empire.uid,
                "name": empire.name,
                "username": uid_to_user.get(empire.uid, ""),
                "online": empire.uid in connected_uids or _is_recently_active(uid_to_last_seen.get(empire.uid, ""), 60),
                "resources": {k: round(v, 1) for k, v in empire.resources.items()},
                "max_life": round(empire.max_life, 1),
                "citizens": empire.citizens,
                "artefact_count": len(empire.artefacts),
                "build_queue": empire.build_queue,
                "research_queue": empire.research_queue,
                "buildings_done": buildings_done,
                "buildings_wip": buildings_wip,
                "knowledge_done": knowledge_done,
                "knowledge_wip": knowledge_wip,
                "armies": armies_out,
                "hex_tiles": hex_tiles,
                "path_length": _pl,
                "power": power,
            })
        empires_out.sort(key=lambda e: e["resources"].get("culture", 0), reverse=True)

        all_armies: dict[tuple[int, int], Any] = {}
        for emp in services.empire_service.all_empires.values():
            for army in emp.armies:
                all_armies[(emp.uid, army.aid)] = army

        attacks_out = []
        for atk in services.attack_service.get_all_attacks():
            attacker_name = uid_to_user.get(atk.attacker_uid, f"uid:{atk.attacker_uid}")
            if atk.attacker_uid == 0:
                attacker_name = "AI"
            atk_army = all_armies.get((atk.attacker_uid, atk.army_aid))
            waves_out = []
            army_name = ""
            if atk_army:
                army_name = atk_army.name or ""
                waves_out = [
                    {"iid": w.iid, "slots": w.slots}
                    for w in atk_army.waves
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

    @router.post("/api/admin/save-state")
    async def admin_save_state(_uid: int = Depends(require_admin)) -> dict[str, Any]:
        if services.empire_service is None:
            return {"ok": False, "error": "empire_service not initialized"}
        assert services.attack_service is not None
        from gameserver.persistence.state_save import save_state
        await save_state(
            empires=services.empire_service.all_empires,
            attacks=services.attack_service.get_all_attacks(),
            battles=[],
        )
        return {"ok": True, "message": "State saved"}

    @router.post("/api/admin/restart")
    async def admin_restart(_uid: int = Depends(require_admin)) -> dict[str, Any]:
        import os
        import sys

        async def _do_restart() -> None:
            await asyncio.sleep(0.5)
            if services.empire_service is not None:
                try:
                    from gameserver.persistence.state_save import save_state
                    assert services.attack_service is not None
                    await save_state(
                        empires=services.empire_service.all_empires,
                        attacks=services.attack_service.get_all_attacks(),
                        battles=[],
                    )
                except Exception:
                    # Save failure must not block restart — log and proceed
                    log.exception("State save failed before restart")
            log.info("Restarting server process via os.execv …")
            os.execv(sys.executable, [sys.executable, '-m', 'gameserver.main'] + sys.argv[1:])

        asyncio.create_task(_do_restart())
        return {"ok": True, "message": "State saved — restarting …"}



    @router.get("/api/admin/users")
    async def admin_list_users(_uid: int = Depends(require_admin)) -> list[dict[str, Any]]:
        if services.database is None:
            return []
        return await services.database.list_users()

    @router.delete("/api/admin/users/{username}")
    async def admin_delete_user(username: str, _uid: int = Depends(require_admin)) -> dict[str, Any]:
        if services.database is None:
            return {"ok": False, "error": "no database"}
        user = await services.database.get_user(username)
        if user is not None:
            uid_to_remove = user["uid"]
            if services.empire_service is not None:
                services.empire_service.unregister(uid_to_remove)
        deleted = await services.database.delete_user(username)
        return {"ok": deleted}

    @router.post("/api/admin/users")
    async def admin_create_user(body: dict[str, Any], _uid: int = Depends(require_admin)) -> dict[str, Any]:
        if services.database is None:
            return {"ok": False, "error": "no database"}
        import bcrypt  # type: ignore[import-not-found]
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

    @router.put("/api/admin/users/{username}/password")
    async def admin_reset_password(username: str, body: dict[str, Any], _uid: int = Depends(require_admin)) -> dict[str, Any]:
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

    @router.put("/api/admin/users/{uid}/empire_name")
    async def admin_rename_empire(uid: int, body: dict[str, Any], _uid: int = Depends(require_admin)) -> dict[str, Any]:
        if services.database is None:
            return {"ok": False, "error": "no database"}
        name = body.get("empire_name", "").strip()
        if not name:
            return {"ok": False, "error": "empire_name required"}
        updated = await services.database.rename_empire(uid, name)
        if updated and services.empire_service is not None and uid in services.empire_service.all_empires:
            services.empire_service.all_empires[uid].name = name
        return {"ok": updated}

    @router.get("/api/admin/catalog")
    async def admin_catalog(_uid: int = Depends(require_admin)) -> dict[str, Any]:
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

    @router.get("/api/admin/structures")
    async def admin_structures(_uid: int = Depends(require_admin)) -> dict[str, Any]:
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

    @router.get("/api/admin/analyze-empire/{uid}")
    async def admin_analyze_empire(uid: int, _uid: int = Depends(require_admin)) -> dict[str, Any]:
        from collections import deque as _deque, Counter as _Counter

        assert services.empire_service is not None
        empire = services.empire_service.get(uid)
        if empire is None:
            raise HTTPException(status_code=404, detail=f"Empire uid={uid} not found")

        raw_map = empire.hex_map

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
                # Malformed hex_map key (e.g. non-integer) — skip tile
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
        total_cost: float = 0.0
        age_counts: dict[str, int] = {}

        for tile_type in raw_map.values():
            if isinstance(tile_type, dict):
                tile_type = tile_type.get("type", "")
            if tile_type in ("path", "castle", "spawnpoint", "", None):
                continue
            item = up.items.get(tile_type) if up else None
            if item is None:
                continue
            cost = float(item.costs.get("gold", 0))
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

    @router.get("/api/admin/map-overview")
    async def admin_map_overview(_uid: int = Depends(require_admin)) -> list[dict[str, Any]]:
        import yaml as _yaml
        from collections import Counter as _Cnt, deque as _dq2
        assert services.empire_service is not None

        HEX_DIRS = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, -1), (-1, 1)]
        NON_TOWER = {"path", "castle", "spawnpoint", "empty", "", None}

        from gameserver.engine.power_service import defense_power as _defense_power
        from gameserver.models.empire import Empire as _Empire

        def _defense_power_for_tiles(tiles: list[dict[str, Any]], life: float, path_length: int | None = None) -> float | None:
            try:
                up = services.empire_service._upgrades  # type: ignore[union-attr]
                if up is None:
                    return None
                e = _Empire(uid=0, name="")
                e.hex_map = {f"{t['q']},{t['r']}": {"type": t["type"]} for t in tiles}
                e.max_life = life
                return round(_defense_power(e, up, path_length=path_length), 1)
            except Exception:
                # Defense power computation is optional — return None if map data is invalid
                return None

        def _analyze(tiles: list[dict[str, Any]], source: str, empire_name: str, uid: int, life: float = 10.0) -> dict[str, Any]:
            tile_map: dict[tuple[int, int], str] = {}
            for t in tiles:
                tt = t["type"]
                if isinstance(tt, dict):
                    tt = tt.get("type", "")
                tile_map[(t["q"], t["r"])] = tt or ""

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

            TOWER_AGE: dict[str, str] = {
                iid: _ERA_LABELS_EN[era]
                for era, iids in _STRUCTURE_ERAS
                for iid in iids
            }

            up = services.empire_service._upgrades  # type: ignore[union-attr]
            tower_names: list[str] = []
            total_cost: float = 0.0
            age_counts: dict[str, int] = {}
            for tt in tile_map.values():
                if tt in NON_TOWER:
                    continue
                item = up.items.get(tt) if up else None
                if item is None:
                    continue
                cost = float(item.costs.get("gold", 0))
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

        results: list[dict[str, Any]] = []

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
                # Corrupt or missing saved_maps.yaml — skip and return live empires only
                log.warning("admin_map_overview: failed to load saved maps", exc_info=True)

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

    @router.post("/api/admin/saved-maps/from-live/{uid}")
    async def admin_save_live_map(uid: int, _uid: int = Depends(require_admin)) -> dict[str, Any]:
        import time as _time
        assert services.empire_service is not None
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

    @router.delete("/api/admin/saved-maps/{map_id}")
    async def admin_delete_saved_map(map_id: str, _uid: int = Depends(require_admin)) -> dict[str, Any]:
        maps = _load_saved_maps()
        new_maps = [m for m in maps if m.get("id") != map_id]
        if len(new_maps) == len(maps):
            raise HTTPException(status_code=404, detail=f"map_id '{map_id}' not found")
        _write_saved_maps(new_maps)
        return {"ok": True, "deleted": map_id}

    @router.patch("/api/admin/saved-maps/{map_id}")
    async def admin_rename_saved_map(map_id: str, body: SavedMapRenameBody,
                                     _uid: int = Depends(require_admin)) -> dict[str, Any]:
        maps = _load_saved_maps()
        for m in maps:
            if m.get("id") == map_id:
                m["name"] = body.name.strip()
                if body.life is not None:
                    m["life"] = float(body.life)
                _write_saved_maps(maps)
                return {"ok": True, "id": map_id, "name": m["name"], "life": m.get("life")}
        raise HTTPException(status_code=404, detail=f"map_id '{map_id}' not found")

    @router.post("/api/admin/saved-maps/{map_id}/activate")
    async def admin_activate_saved_map(map_id: str, _uid: int = Depends(require_admin)) -> dict[str, Any]:
        import time as _time
        TARGET_UID = 4
        assert services.empire_service is not None
        empire = services.empire_service.get(TARGET_UID)
        if empire is None:
            raise HTTPException(status_code=404, detail=f"Empire uid={TARGET_UID} not found")

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

        maps = _load_saved_maps()
        target_map = next((m for m in maps if m.get("id") == map_id), None)
        if target_map is None:
            raise HTTPException(status_code=404, detail=f"map_id '{map_id}' not found")

        new_hex_map = {}
        for tile in target_map.get("hex_map", []):
            new_hex_map[f"{tile['q']},{tile['r']}"] = tile.get("type", "")
        empire.hex_map = new_hex_map

        return {"ok": True, "backup_id": backup_id}

    @router.get("/api/admin/ai-armies")
    async def admin_ai_armies(_uid: int = Depends(require_admin)) -> dict[str, Any]:
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
                    tower_item = up.items.get(iid)
                    if tower_item is None:
                        continue
                    efx = tower_item.effects or {}
                    towers[iid] = {
                        "damage": tower_item.damage,
                        "range": tower_item.range,
                        "reload": tower_item.reload_time_ms,
                        "burn_dps": efx.get("burn_dps", 0),
                        "burn_dur": efx.get("burn_duration", 0),
                        "slow_dur": efx.get("slow_duration", 0),
                        "era": era_label,
                        "sprite": tower_item.sprite or "",
                    }
        return {"armies": armies, "critters": critters, "towers": towers}

    @router.post("/api/admin/send-ai-attack")
    async def admin_send_ai_attack(
        body: dict[str, Any], _uid: int = Depends(require_admin)
    ) -> dict[str, Any]:
        from gameserver.models.army import Army, CritterWave
        assert services.empire_service is not None
        assert services.attack_service is not None

        defender_uid: int = body.get("defender_uid", 0)
        if not defender_uid:
            raise HTTPException(status_code=400, detail="defender_uid required")

        if services.empire_service.get(defender_uid) is None:
            raise HTTPException(status_code=404, detail=f"Empire uid={defender_uid} not found")

        travel_time: float | None = body.get("travel_time")
        army_name: str = body.get("army_name") or "Admin Attack"

        waves_raw: list[dict[str, Any]] = body.get("waves") or []
        if not waves_raw:
            hw = services.ai_service._hardcoded_waves if services.ai_service else []
            entry = next((e for e in hw if e.get("name") == army_name), None)
            if entry is None:
                raise HTTPException(status_code=404, detail=f"Army '{army_name}' not found in ai_waves.yaml")
            waves_raw = entry.get("waves") or []
            if travel_time is None:
                travel_time = float(entry.get("travel_time") or 0) or None

        if not waves_raw:
            raise HTTPException(status_code=400, detail="No waves defined")

        assert services.ai_service is not None
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

        defender_empire = services.empire_service.get(defender_uid)
        if services.ai_service:
            services.ai_service._send_army(
                defender_uid=defender_uid,
                empire=defender_empire,  # type: ignore[arg-type]
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

    @router.patch("/api/admin/structures/{iid}/effects")
    async def update_structure_effects(
        iid: str, body: dict[str, Any], _uid: int = Depends(require_admin)
    ) -> dict[str, Any]:
        from pathlib import Path as _Path
        new_effects: dict[str, Any] = body.get("effects", {})
        for k, v in new_effects.items():
            if not isinstance(k, str):
                raise HTTPException(status_code=400, detail="Effect keys must be strings")
            if not isinstance(v, (int, float)):
                raise HTTPException(status_code=400, detail=f"Effect value for '{k}' must be a number")

        config_path = _Path(__file__).parent.parent.parent.parent.parent / "config" / "structures.yaml"
        if not config_path.exists():
            raise HTTPException(status_code=500, detail="structures.yaml not found")

        ok = _update_effects_in_yaml(config_path, iid, new_effects)
        if not ok:
            raise HTTPException(status_code=404, detail=f"IID '{iid}' not found in structures.yaml")
        return {"success": True, "iid": iid, "effects": new_effects}

    @router.get("/api/admin/era-effects")
    async def get_era_effects_admin(_uid: int = Depends(require_admin)) -> dict[str, Any]:
        import yaml as _yaml
        p = _CONFIG_DIR / "game.yaml"
        with p.open() as f:
            raw = _yaml.safe_load(f) or {}
        return {"era_effects": raw.get("era_effects", {})}

    @router.patch("/api/admin/era-effects/{era_key}")
    async def patch_era_effects(
        era_key: str, body: dict[str, Any], _uid: int = Depends(require_admin)
    ) -> dict[str, Any]:
        import yaml as _yaml
        effects: dict[str, Any] = body.get("effects", {})
        for k, v in effects.items():
            if not isinstance(k, str):
                raise HTTPException(status_code=400, detail="Effect keys must be strings")
            if not isinstance(v, (int, float)):
                raise HTTPException(status_code=400, detail=f"Value for '{k}' must be a number")

        p = _CONFIG_DIR / "game.yaml"
        with p.open() as f:
            raw = _yaml.safe_load(f) or {}

        if "era_effects" not in raw:
            raw["era_effects"] = {}
        if effects:
            raw["era_effects"][era_key] = effects
        else:
            raw["era_effects"].pop(era_key, None)

        with p.open("w") as f:
            _yaml.dump(raw, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

        # Reload in-memory era_effects in the shared rest_api module
        _rest_api._era_effects_data = _load_era_effects()
        if services.empire_service:
            from gameserver.loaders.game_config_loader import load_game_config
            new_gc = load_game_config(str(_CONFIG_DIR / "game.yaml"))
            services.empire_service._gc = new_gc
        return {"success": True, "era_key": era_key, "effects": effects}

    @router.get("/api/admin/workshop-config")
    async def get_workshop_config(_uid: int = Depends(require_admin)) -> dict[str, Any]:
        import yaml as _yaml
        p = _CONFIG_DIR / "game.yaml"
        with p.open() as f:
            raw = _yaml.safe_load(f) or {}
        return {
            "structure_upgrades": raw.get("structure_upgrades", {}),
            "critter_upgrades": raw.get("critter_upgrades", {}),
            "item_upgrade_base_costs": raw.get("item_upgrade_base_costs", []),
        }

    @router.patch("/api/admin/workshop-config")
    async def patch_workshop_config(body: dict[str, Any], _uid: int = Depends(require_admin)) -> dict[str, Any]:
        import yaml as _yaml
        p = _CONFIG_DIR / "game.yaml"
        with p.open() as f:
            raw = _yaml.safe_load(f) or {}
        if "structure_upgrades" in body:
            raw["structure_upgrades"] = {k: float(v) for k, v in body["structure_upgrades"].items()}
        if "critter_upgrades" in body:
            raw["critter_upgrades"] = {k: float(v) for k, v in body["critter_upgrades"].items()}
        if "item_upgrade_base_costs" in body:
            raw["item_upgrade_base_costs"] = [float(v) for v in body["item_upgrade_base_costs"]]
        with p.open("w") as f:
            _yaml.dump(raw, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
        if services.empire_service:
            from gameserver.loaders.game_config_loader import load_game_config
            new_gc = load_game_config(str(_CONFIG_DIR / "game.yaml"))
            services.empire_service._gc = new_gc
        if services.attack_service and services.empire_service and services.empire_service._gc:
            services.attack_service._game_config = services.empire_service._gc
        return {"success": True}

    @router.post("/api/admin/claude-start")
    async def claude_start(_uid: int = Depends(require_admin)) -> Any:
        """Start claude --remote-control in a new detached tmux session (admin only)."""
        import subprocess
        session = "claude-rc"
        try:
            subprocess.run(["tmux", "kill-session", "-t", session], capture_output=True)
            proc = await asyncio.create_subprocess_exec(
                "tmux", "new-session", "-d", "-s", session,
                "claude", "--remote-control",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            _, stderr = await proc.communicate()
            if proc.returncode != 0:
                from fastapi.responses import JSONResponse
                return JSONResponse({"ok": False, "detail": stderr.decode().strip()}, status_code=500)
            return {"ok": True, "message": f"tmux session '{session}' started."}
        except FileNotFoundError as exc:
            from fastapi.responses import JSONResponse
            return JSONResponse({"ok": False, "detail": str(exc)}, status_code=500)

    return router
