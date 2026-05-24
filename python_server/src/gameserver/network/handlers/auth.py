"""Auth / Account handlers — Strangler Fig domain module.

Contains authentication, signup, and empire-creation handlers.
"""
from __future__ import annotations

import logging
from typing import Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from gameserver.main import Services

from gameserver.models.messages import GameMessage
import gameserver.engine.global_state as _gs

log = logging.getLogger(__name__)

# mypy strict requires explicit __all__ for underscore-prefixed re-exports
__all__ = [
    "handle_auth_request", "handle_signup", "handle_create_empire",
    "_build_empire_summary", "_build_session_state", "_create_empire_for_new_user",
    "_build_end_rally_info", "handle_effect_sources_request",
]


def _svc() -> "Services":
    from gameserver.network.handlers._core import _svc as _core_svc
    return _core_svc()


def _build_end_rally_info(gc: Any, empire_service: Any = None) -> dict[str, Any]:
    """Return end-rally status dict for the client."""
    from gameserver.engine.global_state import (
        get_end_criterion_activated, is_end_rally_active, end_rally_seconds_remaining,
        get_end_criterion_empire_uid, get_end_criterion_empire_name,
    )
    from gameserver.network.rest_api import _item_names
    if gc is None:
        return {"active": False, "effects": {}, "seconds_remaining": 0.0}
    activated = get_end_criterion_activated()
    active = is_end_rally_active(gc)
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
        "effects": dict(gc.end_rally_effects) if active else {},
        "seconds_remaining": round(end_rally_seconds_remaining(gc), 0) if active else 0.0,
        "activated_at": activated.isoformat() if activated else None,
        "end_criterion": gc.end_criterion,
        "end_criterion_name": _item_names.get(gc.end_criterion, gc.end_criterion),
        "triggered_by_uid": get_end_criterion_empire_uid(),
        "triggered_by_name": get_end_criterion_empire_name(),
        "culture_leader_name": culture_leader_name,
    }


def _build_session_state(uid: int) -> dict[str, Any]:
    """Build a dict describing restorable session state for *uid*.

    Includes:
    - ``active_battles``: list of attack IDs the user is involved in
      (so the client can re-register as observer).
    - ``has_active_siege``: whether the user is under siege.
    """
    svc = _svc()
    attack_svc = svc.attack_service
    assert attack_svc is not None

    active_battles: list[dict[str, Any]] = []
    for a in attack_svc.get_incoming(uid):
        active_battles.append({
            "attack_id": a.attack_id,
            "role": "defender",
            "phase": a.phase.value if hasattr(a.phase, "value") else str(a.phase),
        })
    for a in attack_svc.get_outgoing(uid):
        active_battles.append({
            "attack_id": a.attack_id,
            "role": "attacker",
            "phase": a.phase.value if hasattr(a.phase, "value") else str(a.phase),
        })

    return {
        "active_battles": active_battles,
    }


def _build_empire_summary(empire: Any, uid: int) -> dict[str, Any]:
    """Build a complete empire summary for a given UID.

    Used by both handle_summary_request() and handle_auth_request().
    Returns the full empire state including resources, buildings, research,
    structures, and ongoing attacks.
    """
    svc = _svc()
    assert svc.empire_service is not None
    assert svc.attack_service is not None

    # Active builds: buildings with remaining effort > 0
    active_buildings = {
        iid: round(remaining, 1)
        for iid, remaining in empire.buildings.items()
        if remaining > 0
    }
    completed_buildings = [
        iid for iid, remaining in empire.buildings.items()
        if remaining <= 0
    ]

    # Active research: knowledge with remaining effort > 0
    active_research = {
        iid: round(remaining, 1)
        for iid, remaining in empire.knowledge.items()
        if remaining > 0
    }
    completed_research = [
        iid for iid, remaining in empire.knowledge.items()
        if remaining <= 0
    ]

    # Structures summary
    structures_list = []
    for sid, s in empire.structures.items():
        structures_list.append({
            "sid": sid,
            "iid": s.iid,
            "position": {"q": s.position.q, "r": s.position.r},
            "damage": s.damage,
            "range": s.range,
        })

    # Ongoing attacks
    from gameserver.network.handlers._core import _active_battles

    def _attack_dto(a: Any) -> dict[str, Any]:
        if a.army_name_override:
            _army_name = a.army_name_override
        else:
            assert svc.empire_service is not None
            _att_emp = svc.empire_service.get(a.attacker_uid)
            _army_name = ""
            if _att_emp:
                for _arm in _att_emp.armies:
                    if _arm.aid == a.army_aid:
                        _army_name = _arm.name
                        break
        _battle = _active_battles.get(a.defender_uid)
        _elapsed = round(_battle.elapsed_ms / 1000, 1) if _battle else 0.0
        return {
            "attack_id": a.attack_id,
            "attacker_uid": a.attacker_uid,
            "defender_uid": a.defender_uid,
            "army_aid": a.army_aid,
            "army_name": _army_name,
            "attacker_username": "",  # resolved client-side from empires list
            "phase": a.phase.value,
            "eta_seconds": round(a.eta_seconds, 1),
            "total_eta_seconds": round(a.total_eta_seconds, 1),
            "siege_remaining_seconds": round(a.siege_remaining_seconds, 1),
            "total_siege_seconds": round(a.total_siege_seconds, 1),
            "is_spy": a.is_spy,
            "battle_elapsed_seconds": _elapsed,
        }

    attacks_incoming = [_attack_dto(a) for a in svc.attack_service.get_incoming(uid)]
    attacks_outgoing = [_attack_dto(a) for a in svc.attack_service.get_outgoing(uid)]

    # Count purchased tiles (non-void tiles in hex_map)
    hex_map = getattr(empire, 'hex_map', {}) or {}
    purchased_tile_count = sum(1 for tile_type in hex_map.values() if tile_type != 'void')
    next_tile_price = svc.empire_service.tile_price_for(empire, purchased_tile_count + 1)

    next_citizen_price = svc.empire_service.citizen_price_for(empire, sum(empire.citizens.values()) + 1)

    # Count armies
    army_count = len(empire.armies)
    next_army_price = svc.empire_service._army_price(army_count + 1)

    # Count total waves across all armies
    total_waves = sum(len(army.waves) for army in empire.armies)
    next_wave_price = svc.empire_service.wave_price_for(empire, total_waves + 1)
    # Critter slot price is wave-specific (based on slots in that wave)
    # Show base price for first slot as reference
    base_critter_slot_price = svc.empire_service._critter_slot_price(1)

    return {
        "type": "summary_response",
        "uid": empire.uid,
        "name": empire.name,
        "resources": {k: round(v, 2) for k, v in empire.resources.items()},
        "citizens": dict(empire.citizens),
        "citizen_price": round(next_citizen_price, 2),
        "tile_price": round(next_tile_price, 2),
        "army_price": round(next_army_price, 2),
        "wave_price": round(next_wave_price, 2),
        "critter_slot_price": round(base_critter_slot_price, 2),
        "citizen_effect": svc.empire_service.effective_citizen_effect(empire),
        "base_gold": svc.empire_service._base_gold,
        "base_culture": svc.empire_service._base_culture,
        "base_build_speed": svc.empire_service._base_build_speed,
        "base_research_speed": svc.empire_service._base_research_speed,
        "base_siege_construction_speed_per_army_modifier": svc.empire_service._siege_construction_per_army,
        "base_restore_life": svc.empire_service._base_restore_life,
        "tower_sell_refund": getattr(svc.game_config, 'tower_sell_refund', 0.3) if svc.game_config else 0.3,
        "max_life": empire.max_life,
        "effects": dict(empire.effects),
        "artifacts": list(empire.artifacts),
        "buildings": dict(empire.buildings),  # iid -> remaining effort
        "knowledge": dict(empire.knowledge),  # iid -> remaining effort
        "active_buildings": active_buildings,
        "completed_buildings": completed_buildings,
        "active_research": active_research,
        "completed_research": completed_research,
        "build_queue": empire.build_queue,
        "research_queue": empire.research_queue,
        "structures": structures_list,
        "army_count": len(empire.armies),
        "spy_count": len(empire.spies),
        "attacks_incoming": attacks_incoming,
        "attacks_outgoing": attacks_outgoing,
        "travel_time_seconds": round(max(1.0, (svc.attack_service._era_travel_offset(empire) + empire.get_effect("travel_offset", 0.0)) * (1.0 - empire.get_effect("travel_time_modifier", 0.0))), 0),
        "era_travel_base_seconds": round(svc.attack_service._era_travel_offset(empire), 0),
        "base_artifact_steal_victory": svc.game_config.base_artifact_steal_victory if svc.game_config else 0.0,
        "base_artifact_steal_defeat": svc.game_config.base_artifact_steal_defeat if svc.game_config else 0.0,
        "current_era": svc.empire_service.get_current_era(empire),
        "item_upgrades": {iid: dict(stats) for iid, stats in empire.item_upgrades.items()},
        "end_rally": _build_end_rally_info(svc.game_config, svc.empire_service),
        "ruler": {
            "name": empire.ruler.name,
            "type": empire.ruler.type,
            "xp": empire.ruler.xp,
            "level": svc.empire_service.ruler_level_from_xp(empire.ruler.xp),
            "next_level_xp": svc.empire_service.ruler_xp_for_level(svc.empire_service.ruler_level_from_xp(empire.ruler.xp) + 1),
            "level_xp_start": sum(svc.empire_service.ruler_xp_for_level(lvl) for lvl in range(2, svc.empire_service.ruler_level_from_xp(empire.ruler.xp) + 1)),
            "q": empire.ruler.q,
            "w": empire.ruler.w,
            "e": empire.ruler.e,
            "r": empire.ruler.r,
        },
        "ruler_effects": svc.empire_service.get_ruler_effects(empire),
        "season_number": _gs.get_season_number(),
        "season_title": _gs.get_season_title(),
        "next_season_start": _gs.get_next_season_start(),
        "next_season_leadtime": _gs.get_next_season_leadtime(),
        "next_season_title": _gs.get_next_season_title(),
        "season_reset_triggered": _gs.is_season_reset_triggered(),
    }


def handle_effect_sources_request(uid: int) -> dict[str, Any]:
    """Return a per-effect-key breakdown of all effect sources for the empire."""
    svc = _svc()
    assert svc.empire_service is not None
    empire = svc.empire_service.get(uid)
    if empire is None:
        return {}

    # result[effect_key][category] = value or dict[iid, value]
    result: dict[str, dict[str, Any]] = {}

    def _add(key: str, category: str, value: float, iid: Optional[str] = None) -> None:
        if value == 0.0:
            return
        if key not in result:
            result[key] = {}
        if iid is not None:
            bucket = result[key].setdefault(category, {})
            bucket[iid] = round(bucket.get(iid, 0.0) + value, 6)
        else:
            result[key][category] = round(result[key].get(category, 0.0) + value, 6)

    upgrades = svc.empire_service._upgrades

    # Buildings
    for iid, remaining in empire.buildings.items():
        if remaining <= 0:
            for key, value in upgrades.get_effects(iid).items():
                _add(key, "buildings", value, iid)

    # Knowledge / research
    for iid, remaining in empire.knowledge.items():
        if remaining <= 0:
            for key, value in upgrades.get_effects(iid).items():
                _add(key, "knowledge", value, iid)

    # Artifacts
    for iid in empire.artifacts:
        for key, value in upgrades.get_effects(iid).items():
            _add(key, "artifacts", value, iid)

    # Era effects
    era_key = svc.empire_service.get_current_era(empire)
    era_effects_all = getattr(svc.empire_service._gc, "era_effects", {})
    for key, value in era_effects_all.get(era_key, {}).items():
        _add(key, "era", float(value))

    # End-rally effects
    if svc.game_config is not None:
        from gameserver.engine.global_state import is_end_rally_active
        if is_end_rally_active(svc.game_config):
            for key, value in svc.game_config.end_rally_effects.items():
                _add(key, "end_rally", float(value))

    # Ruler effects
    for key, value in svc.empire_service.get_ruler_effects(empire).items():
        _add(key, "ruler", value)

    # Citizens
    citizen_effect = svc.empire_service.effective_citizen_effect(empire)
    merchant = empire.citizens.get("merchant", 0)
    artist = empire.citizens.get("artist", 0)
    scientist = empire.citizens.get("scientist", 0)
    if merchant:
        _add("gold_modifier", "citizens", merchant * citizen_effect)
    if artist:
        _add("culture_modifier", "citizens", artist * citizen_effect)
    if scientist:
        _add("research_speed_modifier", "citizens", scientist * citizen_effect)

    return result


async def _create_empire_for_new_user(uid: int, username: str, empire_name: str) -> None:
    """Create and register a fresh Empire for a newly signed-up user.

    Starting resources and max_life are taken from game_config so that
    changes to game.yaml are reflected without touching handler code.
    Called by both the WebSocket handler and the REST signup endpoint.
    The initial tiles are shifted to the empire's assigned global spawn position.
    """
    from gameserver.models.empire import Empire
    from gameserver.models.hex import HexCoord
    svc = _svc()
    assert svc.empire_service is not None
    starting_res = dict(svc.game_config.starting_resources) if svc.game_config else {"gold": 0.0, "culture": 0.0, "life": 10.0}
    starting_max_life = svc.game_config.starting_max_life if svc.game_config else 10.0

    # Compute global spawn position for this new empire
    spawn_offset = HexCoord(0, 0)
    try:
        spacing = svc.game_config.empire_spawn_spacing if svc.game_config else 11
        existing_castles: list[tuple[int, int]] = []
        for emp in svc.empire_service.all_empires.values():
            for key, tile_type in emp.hex_map.items():
                if tile_type == "castle":
                    q, r = map(int, key.split(","))
                    existing_castles.append((q, r))
        spawn_offset = _next_spawn_point(spacing=spacing, existing_castles=existing_castles)
        log.info("New empire uid=%d spawn offset q=%d r=%d (spacing=%d, existing=%d)", uid, spawn_offset.q, spawn_offset.r, spacing, len(existing_castles))
    except Exception as exc:
        log.warning("Could not compute spawn position for uid=%d: %s", uid, exc)

    oq, or_ = spawn_offset.q, spawn_offset.r
    empire = Empire(
        uid=uid,
        name=empire_name or f"{username}'s Empire",
        buildings={"INIT": 0.0},
        resources=starting_res,
        max_life=starting_max_life,
        hex_map={
            f"{oq},{or_}": "castle",
            f"{oq},{or_ + 1}": "spawnpoint",
            f"{oq + 1},{or_}": "empty",
        },
    )
    svc.empire_service.register(empire)


async def _maybe_grant_last_season_artifact(uid: int, empire: Any) -> None:
    """If the user held artifacts at the end of last season, grant one randomly."""
    import random

    svc = _svc()
    if svc.database is None:
        return
    last_arts = await svc.database.get_last_season_artifacts(uid)
    if not last_arts:
        return
    chosen = random.choice(last_arts)
    if chosen not in empire.artifacts:
        empire.artifacts.append(chosen)
    log.info(
        "Last-season artifact bonus: uid=%d had %d artifact(s), granted %s",
        uid, len(last_arts), chosen,
    )



def _next_spawn_point(spacing: int, existing_castles: list[tuple[int, int]]) -> Any:
    """Return the nearest grid point (multiples of spacing) that is >= spacing hex steps from all existing castles."""
    import math
    from gameserver.models.hex import HexCoord

    def _hex_dist(aq: int, ar: int, bq: int, br: int) -> int:
        return (abs(aq - bq) + abs(aq + ar - bq - br) + abs(ar - br)) // 2

    radius = 0
    while True:
        pts: list[tuple[int, float, int, int]] = []
        for gq in range(-radius, radius + 1):
            for gr in range(-radius, radius + 1):
                q, r = gq * spacing, gr * spacing
                d = _hex_dist(0, 0, q, r)
                angle = math.atan2(q, -r)
                pts.append((d, angle, q, r))
        pts.sort()
        for _, _, q, r in pts:
            if all(_hex_dist(q, r, eq, er) >= spacing for eq, er in existing_castles):
                return HexCoord(q, r)
        radius += 1


async def handle_auth_request(
    message: GameMessage, sender_uid: int,
) -> Optional[dict[str, Any]]:
    """Handle ``auth_request`` — authenticate a player.

    On successful auth the response includes ``session_state`` so
    the client knows which subscriptions to restore (e.g. battle
    observer registrations that were lost during a reconnect).
    """
    svc = _svc()
    assert svc.auth_service is not None
    assert svc.empire_service is not None
    username = getattr(message, "username", "")
    password = getattr(message, "password", "")

    uid = await svc.auth_service.login(username, password)
    if uid is not None:
        # Gather restorable session state for the reconnecting client
        session_state = _build_session_state(uid)

        # Fetch summary immediately so client has fresh state after login
        empire = svc.empire_service.get(uid)
        summary_data = _build_empire_summary(empire, uid) if empire else None

        return {
            "type": "auth_response",
            "success": True,
            "uid": uid,
            "reason": "",
            "session_state": session_state,
            "summary": summary_data,
        }
    return {
        "type": "auth_response",
        "success": False,
        "uid": 0,
        "reason": "Invalid username or password",
    }


async def handle_signup(
    message: GameMessage, sender_uid: int,
) -> Optional[dict[str, Any]]:
    """Handle ``signup`` — create a new account."""
    svc = _svc()
    assert svc.auth_service is not None
    username = getattr(message, "username", "")
    password = getattr(message, "password", "")
    email = getattr(message, "email", "")
    empire_name = getattr(message, "empire_name", "")

    result = await svc.auth_service.signup(username, password, email, empire_name)
    if isinstance(result, int):
        log.info("Signup success: user=%s uid=%d", username, result)
        await _create_empire_for_new_user(result, username, empire_name)
        return {
            "type": "signup_response",
            "success": True,
            "uid": result,
            "reason": "",
        }
    # result is an error string
    log.info("Signup failed: user=%s reason=%s", username, result)
    return {
        "type": "signup_response",
        "success": False,
        "uid": 0,
        "reason": result,
    }


async def handle_create_empire(
    message: GameMessage, sender_uid: int,
) -> Optional[dict[str, Any]]:
    """Handle ``create_empire`` — create a fresh empire for a UID.

    TODO: Create Empire object, register in EmpireService.
    """
    log.info("create_empire from uid=%d (not yet implemented)", sender_uid)
    return None
