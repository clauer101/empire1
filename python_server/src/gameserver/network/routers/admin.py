"""Admin router — /api/admin/*, /health, /metrics."""
from __future__ import annotations

import asyncio
from typing import Any, TYPE_CHECKING

from fastapi import APIRouter, Depends, HTTPException

from gameserver.network.jwt_auth import get_current_uid_admin
from gameserver.network.rest_models import SavedMapRenameBody, GoldAdjustBody, CultureAdjustBody
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
    router = APIRouter(include_in_schema=False)

    async def require_admin(uid: int = Depends(get_current_uid_admin)) -> int:
        if services.database is not None:
            user = await services.database.get_user_by_uid(uid)
            if user is None or user.get("username", "").lower() != ADMIN_USERNAME:
                raise HTTPException(status_code=403, detail="Admin only")
        return uid

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
        winner_place: dict[int, int] = {}
        past_champions: set[int] = set()
        if services.database is not None:
            for row in await services.database.list_users():
                uid_to_user[row["uid"]] = row["username"]
                uid_to_last_seen[row["uid"]] = row.get("last_seen", "")
            all_winners = await services.database.get_season_winners()
            if all_winners:
                latest = max(w["season_number"] for w in all_winners)
                for w in all_winners:
                    if w["season_number"] == latest:
                        winner_place[w["empire_uid"]] = w["place"]
                    elif w["place"] == 1:
                        past_champions.add(w["empire_uid"])

        connected_uids: list[int] = (
            services.server.connected_uids if services.server else []
        )

        from gameserver.engine.power_service import compute_power
        assert services.empire_service is not None
        assert services.attack_service is not None
        up = services.empire_service._upgrades
        _gc = services.empire_service._gc

        _week_s = 7 * 24 * 3600
        empires_out: list[dict[str, Any]] = []
        for empire in services.empire_service.all_empires.values():
            if empire.uid == 0:
                continue
            # Hide inactive accounts with 0 culture (> 1 week without login)
            culture = empire.resources.get("culture", 0.0)
            last_seen = uid_to_last_seen.get(empire.uid, "")
            if culture <= 0 and not _is_recently_active(last_seen, _week_s):
                continue

            buildings_done = [iid for iid, v in empire.buildings.items() if v == 0.0]
            buildings_wip  = {iid: round(v, 1) for iid, v in empire.buildings.items() if v != 0.0}
            knowledge_done = [iid for iid, v in empire.knowledge.items() if v == 0.0]
            knowledge_wip  = {iid: round(v, 1) for iid, v in empire.knowledge.items() if v != 0.0}

            from gameserver.network.handlers.battle_task import _army_power as _ap
            items_by_iid = up.items if up else {}
            armies_out = []
            for army in empire.armies:
                armies_out.append({
                    "aid": army.aid,
                    "name": army.name,
                    "waves": [
                        {"iid": w.iid, "slots": w.slots}
                        for w in army.waves
                    ],
                    "power": round(_ap(army, items_by_iid)),
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

            bot_prob = (
                services.bot_detector.get_probability(empire.uid)
                if services.bot_detector else 0.5
            )
            empires_out.append({
                "uid": empire.uid,
                "name": empire.name,
                "username": uid_to_user.get(empire.uid, ""),
                "season_place": winner_place.get(empire.uid),
                "past_champion": empire.uid in past_champions,
                "online": empire.uid in connected_uids or _is_recently_active(uid_to_last_seen.get(empire.uid, ""), 60),
                "bot_probability": round(bot_prob, 3),
                "resources": {k: round(v, 1) for k, v in empire.resources.items()},
                "max_life": round(empire.max_life, 1),
                "citizens": empire.citizens,
                "artifact_count": len(empire.artifacts),
                "artifacts": list(empire.artifacts),
                "build_queue": empire.build_queue,
                "research_queue": empire.research_queue,
                "buildings_done": buildings_done,
                "buildings_wip": buildings_wip,
                "knowledge_done": knowledge_done,
                "knowledge_wip": knowledge_wip,
                "armies": armies_out,
                "item_upgrades": empire.item_upgrades,
                "item_era_index": {iid: services.empire_service._item_era_index.get(iid, 0) for iid in empire.item_upgrades},
                "hex_tiles": hex_tiles,
                "path_length": _pl,
                "power": power,
                "ruler": {
                    "name": empire.ruler.name,
                    "type": empire.ruler.type,
                    "xp": empire.ruler.xp,
                    "level": empire.ruler.level,
                    "q": empire.ruler.q,
                    "w": empire.ruler.w,
                    "e": empire.ruler.e,
                    "r": empire.ruler.r,
                },
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
            "speedup": services.game_loop.speedup if services.game_loop else 1.0,
        }

    @router.get("/api/admin/trophies")
    async def admin_trophies(_uid: int = Depends(require_admin)) -> dict[str, Any]:
        """Return earned trophies grouped per empire, plus full trophy catalog."""
        from gameserver.models.items import ItemType

        assert services.empire_service is not None
        assert services.database is not None

        uid_to_user: dict[int, str] = {}
        uid_to_name: dict[int, str] = {}
        for row in await services.database.list_users():
            uid_to_user[row["uid"]] = row["username"]
        for empire in services.empire_service.all_empires.values():
            uid_to_name[empire.uid] = empire.name

        up = services.empire_service._upgrades
        catalog = [
            {
                "iid": item.iid,
                "name": item.name,
                "image": item.image,
                "description": item.description,
                "effects": item.effects,
                "condition": item.condition,
            }
            for item in up.items.values()
            if item.item_type == ItemType.TROPHY
        ]
        catalog.sort(key=lambda t: str(t["name"]))
        total = len(catalog)

        rows = await services.database.get_all_trophy_rows()
        by_uid: dict[int, list[dict[str, Any]]] = {}
        for row in rows:
            by_uid.setdefault(row["uid"], []).append(row)

        empires_out: list[dict[str, Any]] = []
        for euid, trophy_rows in by_uid.items():
            if euid <= 0:
                continue
            empires_out.append({
                "uid": euid,
                "username": uid_to_user.get(euid, ""),
                "name": uid_to_name.get(euid, ""),
                "earned": [
                    {"iid": r["iid"], "earned_at": r["earned_at"], "season": r["season"]}
                    for r in trophy_rows
                ],
                "earned_count": len(trophy_rows),
            })
        empires_out.sort(key=lambda e: e["earned_count"], reverse=True)

        return {"total_trophies": total, "catalog": catalog, "empires": empires_out}

    @router.post("/api/admin/speedup")
    async def admin_set_speedup(body: dict[str, Any], _uid: int = Depends(require_admin)) -> dict[str, Any]:
        """Set the game-time multiplier at runtime.

        Not persisted: after a server restart the speedup_factor from
        game.yaml applies again.
        """
        import os as _os
        if _os.environ.get("IS_DEV", "").lower() not in ("1", "true", "yes"):
            from fastapi import HTTPException
            raise HTTPException(status_code=403, detail="speedup is only available in dev environments")

        if services.game_loop is None:
            return {"success": False, "error": "game loop not initialized"}
        try:
            factor = float(body.get("factor", 1.0))
        except (TypeError, ValueError):
            return {"success": False, "error": "factor must be a number"}
        if not 0.01 <= factor <= 1000:
            return {"success": False, "error": "factor must be between 0.01 and 1000"}
        services.game_loop.set_speedup(factor)
        return {"success": True, "speedup": services.game_loop.speedup}

    def _state_file_path() -> str:
        from gameserver.persistence.state_save import DEFAULT_STATE_PATH
        gl = services.game_loop
        return gl._state_file if gl is not None else DEFAULT_STATE_PATH

    @router.post("/api/admin/save-state")
    async def admin_save_state(_uid: int = Depends(require_admin)) -> dict[str, Any]:
        gl = services.game_loop
        if gl is None:
            return {"ok": False, "error": "game_loop not initialized"}
        await gl._save_state()
        return {"ok": True, "message": "State saved"}

    @router.post("/api/admin/restart")
    async def admin_restart(_uid: int = Depends(require_admin)) -> dict[str, Any]:
        import os
        import sys

        async def _do_restart() -> None:
            await asyncio.sleep(0.5)
            if services.empire_service is not None:
                try:
                    if services.game_loop is not None:
                        await services.game_loop._save_state()
                except Exception:
                    # Save failure must not block restart — log and proceed
                    log.exception("State save failed before restart")
            log.info("Restarting server process via os.execv …")
            os.execv(sys.executable, [sys.executable, '-m', 'gameserver.main'] + sys.argv[1:])

        asyncio.create_task(_do_restart())
        return {"ok": True, "message": "State saved — restarting …"}



    @router.get("/api/admin/device-clusters")
    async def admin_device_clusters(_uid: int = Depends(require_admin)) -> dict[str, Any]:
        """Return every pair of UIDs sharing login-device signals (device_id,
        fingerprint, or IP), with resolved empire names, for manual
        multi-account review.
        """
        assert services.empire_service is not None
        assert services.database is not None

        clusters = await services.database.get_device_clusters()
        result = []
        for c in clusters:
            empire_a = services.empire_service.get(c["uid_a"])
            empire_b = services.empire_service.get(c["uid_b"])
            result.append({
                **c,
                "name_a": empire_a.name if empire_a else f"uid {c['uid_a']}",
                "name_b": empire_b.name if empire_b else f"uid {c['uid_b']}",
            })
        return {"active": result}

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
        from gameserver.network.auth import _hash_password
        pw = body.get("password", "")
        if not pw:
            return {"ok": False, "error": "password required"}
        pw_hash = _hash_password(pw)
        assert services.database._conn is not None
        async with services.database._conn.execute(
            "UPDATE users SET password_hash = ? WHERE username = ?", (pw_hash, username)
        ) as cur:
            updated = cur.rowcount > 0
        await services.database._conn.commit()
        return {"ok": updated}

    @router.put("/api/admin/users/{username}/email")
    async def admin_update_email(username: str, body: dict[str, Any], _uid: int = Depends(require_admin)) -> dict[str, Any]:
        if services.database is None:
            return {"ok": False, "error": "no database"}
        from gameserver.network.auth import _EMAIL_RE
        email = body.get("email", "").strip()
        if email and not _EMAIL_RE.match(email):
            return {"ok": False, "error": "invalid email format"}
        assert services.database._conn is not None
        async with services.database._conn.execute(
            "UPDATE users SET email = ? WHERE username = ?", (email, username)
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
                "era": item.era,
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

    @router.delete("/api/admin/empire/{uid}/tile")
    async def admin_remove_tile(uid: int, q: int, r: int, _uid: int = Depends(require_admin)) -> dict[str, Any]:
        """Remove a single tile from an empire's hex_map.

        Tiles are simply absent from hex_map when void, so this un-claims the
        tile outright — useful for resolving a cross-empire tile collision
        (world_tile_owner() indexes every hex_map key, so the same q,r can end
        up in two empires' maps if a claim path skips that check).
        """
        assert services.empire_service is not None
        empire = services.empire_service.get(uid)
        if empire is None:
            raise HTTPException(status_code=404, detail=f"Empire uid={uid} not found")
        tile_key = f"{q},{r}"
        removed = empire.hex_map.pop(tile_key, None)
        if removed is None:
            return {"ok": False, "error": f"Tile {tile_key} not found in empire {uid}'s hex_map"}
        services.empire_service.invalidate_tile_index()
        log.info("Admin removed tile %s from empire uid=%d (was %r)", tile_key, uid, removed)
        return {"ok": True, "removed": removed}

    @router.post("/api/admin/empire/{uid}/gold-adjust")
    async def admin_adjust_gold(uid: int, body: GoldAdjustBody, _uid: int = Depends(require_admin)) -> dict[str, Any]:
        """Apply a one-off gold bonus (positive) or malus (negative) to an empire.

        Instant adjustment to the current gold balance — not a persistent
        per-second modifier. Result is clamped to never go below 0.
        """
        assert services.empire_service is not None
        empire = services.empire_service.get(uid)
        if empire is None:
            raise HTTPException(status_code=404, detail=f"Empire uid={uid} not found")
        before = empire.resources.get("gold", 0.0)
        after = max(0.0, before + body.amount)
        empire.resources["gold"] = after
        log.info(
            "Admin gold adjustment: uid=%d amount=%.1f gold %.1f → %.1f%s",
            uid, body.amount, before, after,
            f" (reason: {body.reason})" if body.reason else "",
        )
        return {"ok": True, "uid": uid, "gold_before": before, "gold_after": after, "amount_applied": after - before}

    @router.post("/api/admin/empire/{uid}/culture-adjust")
    async def admin_adjust_culture(uid: int, body: CultureAdjustBody, _uid: int = Depends(require_admin)) -> dict[str, Any]:
        """Apply a one-off culture bonus (positive) or malus (negative) to an empire.

        Instant adjustment to the current culture balance — not a persistent
        per-second modifier. Result is clamped to never go below 0.
        """
        assert services.empire_service is not None
        empire = services.empire_service.get(uid)
        if empire is None:
            raise HTTPException(status_code=404, detail=f"Empire uid={uid} not found")
        before = empire.resources.get("culture", 0.0)
        after = max(0.0, before + body.amount)
        empire.resources["culture"] = after
        log.info(
            "Admin culture adjustment: uid=%d amount=%.1f culture %.1f → %.1f%s",
            uid, body.amount, before, after,
            f" (reason: {body.reason})" if body.reason else "",
        )
        return {"ok": True, "uid": uid, "culture_before": before, "culture_after": after, "amount_applied": after - before}

    @router.post("/api/admin/anti-farm/backfill")
    async def admin_backfill_anti_farm(hours: float = 24.0, _uid: int = Depends(require_admin)) -> dict[str, Any]:
        """Reconstruct attacker_win_log rows from historical "You Won!" battle
        report messages, so the anti-farming protection has context immediately
        instead of starting from zero on launch day.

        Best-effort: a defender name only resolves if that empire is still
        registered (in-memory, via empire_service.find_by_name) — renamed or
        deleted empires are skipped and reported back as unmatched.
        """
        import re
        from datetime import datetime, timedelta, timezone

        assert services.empire_service is not None
        assert services.database is not None

        since = (datetime.now(timezone.utc) - timedelta(hours=hours)).strftime("%Y-%m-%d %H:%M:%S")
        rows = await services.database.get_attacker_win_messages(since)

        inserted = 0
        unmatched: set[str] = set()
        for row in rows:
            m = re.search(r"🛡 Defender:\s*(.+)", row["body"])
            if not m:
                continue
            def_name = m.group(1).strip()
            defender = services.empire_service.find_by_name(def_name)
            if defender is None:
                unmatched.add(def_name)
                continue
            try:
                ts = int(
                    datetime.strptime(row["sent_at"], "%Y-%m-%d %H:%M:%S")
                    .replace(tzinfo=timezone.utc).timestamp()
                )
            except ValueError:
                continue
            await services.database.record_attacker_win(row["to_uid"], defender.uid, ts)
            inserted += 1

        log.info(
            "Anti-farm backfill: inserted=%d unmatched=%d (last %.1fh)",
            inserted, len(unmatched), hours,
        )
        return {"ok": True, "inserted": inserted, "unmatched_defender_names": sorted(unmatched)}

    @router.get("/api/admin/anti-farm/active")
    async def admin_anti_farm_active(_uid: int = Depends(require_admin)) -> dict[str, Any]:
        """Return every (attacker, defender) pair for which anti-farm protection
        is currently active, with resolved empire names for the admin dashboard.
        """
        from datetime import datetime, timezone

        assert services.empire_service is not None
        assert services.database is not None
        gc = services.empire_service._gc
        threshold = int(getattr(gc, "anti_farm_win_threshold", 4)) if gc else 4
        window_s = int(getattr(gc, "anti_farm_window_hours", 24.0) * 3600) if gc else 86400
        since_ts = int(datetime.now(timezone.utc).timestamp()) - window_s

        pairs = await services.database.get_active_anti_farm_pairs(since_ts, threshold)
        result = []
        for p in pairs:
            attacker = services.empire_service.get(p["attacker_uid"])
            defender = services.empire_service.get(p["defender_uid"])
            result.append({
                **p,
                "attacker_name": attacker.name if attacker else f"uid {p['attacker_uid']}",
                "defender_name": defender.name if defender else f"uid {p['defender_uid']}",
            })
        return {
            "threshold": threshold,
            "window_hours": window_s / 3600,
            "active": result,
        }

    @router.get("/api/admin/skip-siege-abuse/active")
    async def admin_skip_siege_abuse_active(_uid: int = Depends(require_admin)) -> dict[str, Any]:
        """Return every defender currently over the skip-siege abuse threshold
        within the trailing window, with resolved empire names and timing
        stats for the admin dashboard.

        A defender who calls skip-siege many times in a short window, with
        near-zero variance between calls, is unlikely to be a human clicking
        a button — this surfaces that pattern for manual review. Detection
        only; no automated penalty is applied.
        """
        from datetime import datetime, timezone

        assert services.empire_service is not None
        assert services.database is not None
        gc = services.empire_service._gc
        threshold = int(getattr(gc, "skip_siege_abuse_count_threshold", 5)) if gc else 5
        window_s = int(getattr(gc, "skip_siege_abuse_window_minutes", 10.0) * 60) if gc else 600
        since_ts = int(datetime.now(timezone.utc).timestamp()) - window_s

        rows = await services.database.get_active_window_event_keys("skip_siege", since_ts, threshold)
        abusers = [
            {
                "defender_uid": r["key_uid"],
                "skip_count": r["event_count"],
                "last_skip_ts": r["last_ts"],
                "mean_interval_s": r["mean_interval_s"],
                "stddev_interval_s": r["stddev_interval_s"],
                "max_siege_remaining_at_skip": r["max_magnitude"],
                "distinct_attackers": r["distinct_ref_ids"],
            }
            for r in rows
        ]
        result = []
        for a in abusers:
            defender = services.empire_service.get(a["defender_uid"])
            result.append({
                **a,
                "defender_name": defender.name if defender else f"uid {a['defender_uid']}",
            })
        return {
            "threshold": threshold,
            "window_minutes": window_s / 60,
            "active": result,
        }

    @router.get("/api/admin/detection-summary")
    async def admin_detection_summary(_uid: int = Depends(require_admin)) -> dict[str, Any]:
        """Merge every scripted-access/abuse signal into one row per empire:
        every raw factor BotDetector uses to compute bot_probability/is_bot
        (header score, reaction-latency score, timing-regularity score, and
        their sample counts), plus anti-farm involvement (as attacker or
        defender) and skip-siege abuse (as defender).

        One-stop summary for the admin dashboard — the two dedicated cards
        (Anti-Farm / Skip-Siege Abuse) remain the detailed per-mechanism
        views; this endpoint answers "which empires look suspicious overall
        and why" without cross-referencing tables by hand.
        """
        from datetime import datetime, timezone

        assert services.empire_service is not None
        assert services.database is not None
        gc = services.empire_service._gc

        anti_farm_threshold = int(getattr(gc, "anti_farm_win_threshold", 4)) if gc else 4
        anti_farm_window_s = int(getattr(gc, "anti_farm_window_hours", 24.0) * 3600) if gc else 86400
        skip_siege_threshold = int(getattr(gc, "skip_siege_abuse_count_threshold", 5)) if gc else 5
        skip_siege_window_s = int(getattr(gc, "skip_siege_abuse_window_minutes", 10.0) * 60) if gc else 600
        now_ts = int(datetime.now(timezone.utc).timestamp())

        anti_farm_pairs = await services.database.get_active_anti_farm_pairs(
            now_ts - anti_farm_window_s, anti_farm_threshold,
        )
        skip_siege_rows = await services.database.get_active_window_event_keys(
            "skip_siege", now_ts - skip_siege_window_s, skip_siege_threshold,
        )

        anti_farm_by_uid: dict[int, int] = {}
        for p in anti_farm_pairs:
            anti_farm_by_uid[p["attacker_uid"]] = max(anti_farm_by_uid.get(p["attacker_uid"], 0), p["win_count"])
            anti_farm_by_uid[p["defender_uid"]] = max(anti_farm_by_uid.get(p["defender_uid"], 0), p["win_count"])

        skip_siege_by_uid: dict[int, int] = {r["key_uid"]: r["event_count"] for r in skip_siege_rows}

        flagged_uids = set(anti_farm_by_uid) | set(skip_siege_by_uid)

        result: list[dict[str, Any]] = []
        for empire in services.empire_service.all_empires.values():
            if services.bot_detector is not None:
                breakdown = services.bot_detector.get_signal_breakdown(empire.uid)
            else:
                breakdown = {
                    "user_agent": "", "header_score": None, "reaction_sample_count": 0,
                    "reaction_score": None, "timing_score": None, "declared_bot": False,
                    "bot_probability": 0.5, "is_bot": False,
                }
            if empire.uid not in flagged_uids and breakdown["bot_probability"] <= 0.5:
                continue  # only include empires with at least one non-trivial signal
            result.append({
                "uid": empire.uid,
                "name": empire.name,
                **breakdown,
                "anti_farm_win_count": anti_farm_by_uid.get(empire.uid, 0),
                "skip_siege_count": skip_siege_by_uid.get(empire.uid, 0),
            })
        result.sort(key=lambda r: r["bot_probability"], reverse=True)
        return {"summary": result}

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

        from gameserver.util.eras import ERA_LABELS_EN

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
            age = ERA_LABELS_EN.get(item.era, "Unknown")
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
        from collections import Counter as _Cnt
        assert services.empire_service is not None

        NON_TOWER = {"path", "castle", "spawnpoint", "empty", "", None}

        from gameserver.engine.hex_pathfinding import find_path_from_spawn_to_castle
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

            key_map = {f"{q},{r}": tt for (q, r), tt in tile_map.items()}
            found_path = find_path_from_spawn_to_castle(key_map)
            path_length = len(found_path) - 1 if found_path else None

            TOWER_AGE: dict[str, str] = {
                iid: _ERA_LABELS_EN[era]
                for era, iids in _STRUCTURE_ERAS
                for iid in iids
            }
            TOWER_AGE_INDEX: dict[str, int] = {
                iid: idx
                for idx, (era, iids) in enumerate(_STRUCTURE_ERAS)
                for iid in iids
            }

            up = services.empire_service._upgrades  # type: ignore[union-attr]
            tower_names: list[str] = []
            total_cost: float = 0.0
            age_counts: dict[str, int] = {}
            max_era_index = -1
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
                max_era_index = max(max_era_index, TOWER_AGE_INDEX.get(tt, -1))

            num_towers = len(tower_names)
            age_pct = {
                age: round(cnt / num_towers * 100, 1)
                for age, cnt in age_counts.items()
            } if num_towers else {}
            power = _defense_power_for_tiles(tiles, life, path_length=path_length)
            max_era = _STRUCTURE_ERAS[max_era_index][0] if max_era_index >= 0 else None

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
                "max_era":       _ERA_LABELS_EN.get(max_era, "Unknown") if max_era else "Unknown",
                "max_era_index": max_era_index,
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
                slots=float(w.get("slots", 1)),
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

    @router.get("/api/admin/game-config")
    async def get_game_config_full(_uid: int = Depends(require_admin)) -> dict[str, Any]:
        import yaml as _yaml
        p = _CONFIG_DIR / "game.yaml"
        with p.open() as f:
            raw = _yaml.safe_load(f) or {}
        return raw

    @router.patch("/api/admin/game-config")
    async def patch_game_config_full(body: dict[str, Any], _uid: int = Depends(require_admin)) -> dict[str, Any]:
        import yaml as _yaml
        p = _CONFIG_DIR / "game.yaml"
        with p.open() as f:
            raw = _yaml.safe_load(f) or {}

        def _deep_merge(dst: dict[str, Any], src: dict[str, Any]) -> None:
            for k, v in src.items():
                if isinstance(v, dict) and isinstance(dst.get(k), dict):
                    _deep_merge(dst[k], v)
                else:
                    dst[k] = v

        _deep_merge(raw, body)
        with p.open("w") as f:
            _yaml.dump(raw, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

        from gameserver.loaders.game_config_loader import load_game_config
        new_gc = load_game_config(str(p))
        if services.game_config is not None:
            services.game_config = new_gc
        if services.empire_service:
            services.empire_service._gc = new_gc
        if services.battle_service:
            services.battle_service._gc = new_gc
        if services.ai_service:
            services.ai_service._game_config = new_gc
        if services.game_loop:
            services.game_loop._gc = new_gc
        if services.attack_service:
            services.attack_service._game_config = new_gc
        return {"success": True}

    @router.get("/api/admin/trophy-config")
    async def get_trophy_config(_uid: int = Depends(require_admin)) -> dict[str, Any]:
        import yaml as _yaml
        p = _CONFIG_DIR / "trophies.yaml"
        with p.open() as f:
            raw = _yaml.safe_load(f) or {}
        trophies = []
        for key, t in raw.items():
            entry: dict[str, Any] = {"key": key, **t}
            trophies.append(entry)
        return {"trophies": trophies}

    @router.patch("/api/admin/trophy-config/{key}")
    async def patch_trophy_config(
        key: str, body: dict[str, Any], _uid: int = Depends(require_admin)
    ) -> dict[str, Any]:
        import yaml as _yaml
        p = _CONFIG_DIR / "trophies.yaml"
        with p.open() as f:
            raw = _yaml.safe_load(f) or {}
        if key not in raw:
            raise HTTPException(status_code=404, detail=f"Trophy '{key}' not found")
        trophy = raw[key]
        if "name" in body:
            trophy["name"] = str(body["name"])
        if "description" in body:
            trophy["description"] = str(body["description"])
        if "condition" in body:
            cond_patch: dict[str, Any] = body["condition"]
            if "condition" not in trophy or not isinstance(trophy["condition"], dict):
                trophy["condition"] = {}
            if "type" in cond_patch:
                trophy["condition"]["type"] = str(cond_patch["type"])
            if "threshold" in cond_patch:
                if cond_patch["threshold"] is None:
                    trophy["condition"].pop("threshold", None)
                else:
                    trophy["condition"]["threshold"] = cond_patch["threshold"]
            if "era" in cond_patch:
                if cond_patch["era"] is None:
                    trophy["condition"].pop("era", None)
                else:
                    trophy["condition"]["era"] = str(cond_patch["era"])
        if "effects" in body:
            effects_patch: dict[str, Any] = body["effects"]
            if not isinstance(effects_patch, dict):
                raise HTTPException(status_code=422, detail="effects must be a dict")
            trophy["effects"] = {
                str(k): float(v) for k, v in effects_patch.items()
                if k and v is not None
            }
        raw[key] = trophy
        with p.open("w") as f:
            _yaml.dump(raw, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
        return {"success": True, "key": key}

    @router.delete("/api/admin/trophy-config/{key}")
    async def delete_trophy_config(
        key: str, _uid: int = Depends(require_admin)
    ) -> dict[str, Any]:
        import yaml as _yaml
        p = _CONFIG_DIR / "trophies.yaml"
        with p.open() as f:
            raw = _yaml.safe_load(f) or {}
        if key not in raw:
            raise HTTPException(status_code=404, detail=f"Trophy '{key}' not found")
        del raw[key]
        with p.open("w") as f:
            _yaml.dump(raw, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
        return {"success": True, "key": key}

    @router.get("/api/admin/runtime-stats")
    async def get_runtime_stats(_uid: int = Depends(require_admin)) -> dict[str, Any]:
        assert services.database is not None
        empire_stats = await services.database.get_all_empire_stats()
        artifact_holds = await services.database.get_artifact_hold_totals()
        uid_to_name: dict[int, str] = {}
        for row in await services.database.list_users():
            uid_to_name[row["uid"]] = row["username"]
        for row in empire_stats:
            row["username"] = uid_to_name.get(row["uid"], f"uid:{row['uid']}")
        for row in artifact_holds:
            row["username"] = uid_to_name.get(row["uid"], f"uid:{row['uid']}")
        era_firsts = await services.database.get_era_firsts()
        from gameserver.engine.global_state import get_this_season_start_date
        return {
            "empire_stats": empire_stats,
            "artifact_holds": artifact_holds,
            "era_firsts": era_firsts,
            "this_season_start_date": get_this_season_start_date(),
        }

    @router.get("/api/admin/ai-battle-log")
    async def get_ai_battle_log(limit: int = 500, _uid: int = Depends(require_admin)) -> dict[str, Any]:
        assert services.database is not None
        assert services.database._conn is not None
        async with services.database._conn.execute(
            "SELECT * FROM ai_battle_log ORDER BY logged_at DESC LIMIT ?", (limit,)
        ) as cur:
            rows = await cur.fetchall()
        import json as _json
        keys = [d[0] for d in cur.description]
        result = []
        for row in rows:
            r = dict(zip(keys, row))
            r["towers_by_era"] = _json.loads(r["towers_by_era"] or "{}")
            r["critters_by_era"] = _json.loads(r["critters_by_era"] or "{}")
            result.append(r)
        return {"battles": result}

    # ── Season admin ────────────────────────────────────────────────────────

    @router.get("/api/admin/season")
    async def get_season_state(_uid: int = Depends(require_admin)) -> dict[str, Any]:
        """Return the full season transition state."""
        from gameserver.engine.global_state import (
            get_season_number, get_season_title, get_this_season_start_date,
            get_next_season_start, get_next_season_title, get_next_season_leadtime,
            get_end_criterion_activated, get_end_criterion_empire_uid,
            get_end_criterion_empire_name, is_season_reset_triggered,
            is_end_rally_active, end_rally_seconds_remaining,
        )
        gc = services.empire_service._gc if services.empire_service else None
        season_leadtime = gc.season_leadtime if gc else 259200.0
        end_rally_duration = gc.end_rally_duration if gc else 604800.0
        next_season_start_after_end = gc.next_season_start_after_end if gc else 1209600.0
        end_criterion = gc.end_criterion if gc else ""
        eca = get_end_criterion_activated()
        return {
            "season_number": get_season_number(),
            "season_title": get_season_title(),
            "this_season_start_date": get_this_season_start_date(),
            "next_season_start": get_next_season_start(),
            "next_season_title": get_next_season_title(),
            "next_season_leadtime": get_next_season_leadtime(season_leadtime),
            "season_leadtime_secs": season_leadtime,
            "end_rally_duration_secs": end_rally_duration,
            "next_season_start_after_end_secs": next_season_start_after_end,
            "end_criterion": end_criterion,
            "end_criterion_activated": eca.isoformat() if eca else None,
            "end_criterion_empire_uid": get_end_criterion_empire_uid(),
            "end_criterion_empire_name": get_end_criterion_empire_name(),
            "game_frozen": is_season_reset_triggered(),
            "end_rally_active": is_end_rally_active(gc) if gc else False,
            "end_rally_seconds_remaining": end_rally_seconds_remaining(gc) if gc else 0.0,
        }

    @router.patch("/api/admin/season")
    async def patch_season_state(
        body: dict[str, Any],
        _uid: int = Depends(require_admin),
    ) -> dict[str, Any]:
        """Update editable season fields: next_season_start, next_season_title, season_leadtime_secs."""
        from gameserver.engine.global_state import (
            get_season_number, get_season_title, get_next_season_start,
            get_next_season_title, set_season,
        )
        changed: list[str] = []

        new_next_start = body.get("next_season_start")
        new_next_title = body.get("next_season_title")
        new_leadtime   = body.get("season_leadtime_secs")

        if new_next_start is not None or new_next_title is not None:
            set_season(
                get_season_number(),
                get_season_title(),
                str(new_next_start) if new_next_start is not None else get_next_season_start(),
                str(new_next_title) if new_next_title is not None else get_next_season_title(),
            )
            if new_next_start is not None:
                changed.append("next_season_start")
            if new_next_title is not None:
                changed.append("next_season_title")

        if new_leadtime is not None:
            from gameserver.engine.global_state import set_season_leadtime
            gc = services.empire_service._gc if services.empire_service else None
            if gc is not None:
                gc.season_leadtime = float(new_leadtime)
                set_season_leadtime(float(new_leadtime))
                changed.append("season_leadtime_secs")

        # Persist immediately so a crash doesn't lose the change
        if changed and services.empire_service and services.attack_service:
            from gameserver.persistence.state_save import save_state
            from gameserver.network.handlers._core import _active_battles
            _gc = services.empire_service._gc
            try:
                await save_state(
                    empires=services.empire_service.all_empires,
                    attacks=services.attack_service.get_all_attacks(),
                    battles=list(_active_battles.values()),
                    path=_state_file_path(),
                )
            except Exception:
                pass

        return {"changed": changed}

    @router.post("/api/admin/season/force-new")
    async def force_new_season(
        body: dict[str, Any],
        _uid: int = Depends(require_admin),
    ) -> dict[str, Any]:
        """Dev-only: immediately wipe all empires and start a new season.

        Blocked unless IS_DEV=true is set in the environment.

        Skips the snapshot, rally, and leadtime phases entirely.
        Accepts optional 'new_title' in the request body.
        """
        import os as _os
        if _os.environ.get("IS_DEV", "").lower() not in ("1", "true", "yes"):
            from fastapi import HTTPException
            raise HTTPException(status_code=403, detail="force-new-season is only available in dev environments")

        import asyncio as _asyncio
        from gameserver.engine.global_state import (
            get_season_number, get_season_title,
            get_next_season_title,
            set_season, set_season_reset_triggered,
            set_this_season_start_date, clear_end_criterion,
        )
        from datetime import datetime, timezone

        new_title = body.get("new_title") or get_next_season_title() or get_season_title()
        new_number = get_season_number() + 1

        # Wipe empires and attacks
        wiped_empires = 0
        wiped_attacks = 0
        if services.empire_service:
            uids = services.empire_service.wipe_all_empires()
            wiped_empires = len(uids)
        if services.attack_service:
            wiped_attacks = services.attack_service.wipe_all_attacks()

        # Reset DB season stats
        if services.database:
            _asyncio.ensure_future(services.database.wipe_season_stats())

        # Clear rally / freeze state
        clear_end_criterion()
        set_season_reset_triggered(False)

        # Advance season
        now_iso = datetime.now(timezone.utc).isoformat()
        set_season(new_number, new_title)
        set_this_season_start_date(now_iso)

        log.info(
            "[force-new-season] Season %d '%s' started; wiped %d empires, %d attacks",
            new_number, new_title, wiped_empires, wiped_attacks,
        )

        # Persist new state
        if services.empire_service and services.attack_service:
            from gameserver.persistence.state_save import save_state
            from gameserver.network.handlers._core import _active_battles
            try:
                await save_state(
                    empires=services.empire_service.all_empires,
                    attacks=services.attack_service.get_all_attacks(),
                    battles=list(_active_battles.values()),
                    path=_state_file_path(),
                )
            except Exception:
                pass

        return {
            "ok": True,
            "season_number": new_number,
            "season_title": new_title,
            "wiped_empires": wiped_empires,
            "wiped_attacks": wiped_attacks,
            "started_at": now_iso,
        }

    return router
