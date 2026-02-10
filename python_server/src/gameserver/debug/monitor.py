"""State snapshot collector — gathers engine state for the debug dashboard.

Pulls data from all services into a plain dict that can be serialised
to JSON and rendered in the browser.
"""

from __future__ import annotations

import os
import time
from typing import Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from gameserver.main import Services


def collect_snapshot(services: Services) -> dict[str, Any]:
    """Build a JSON-serialisable snapshot of the entire engine state.

    Args:
        services: The Services container from main.py.

    Returns:
        Nested dict with all relevant runtime data.
    """
    snap: dict[str, Any] = {}

    # -- Server info ---
    snap["server"] = _server_info(services)

    # -- Game loop ---
    snap["game_loop"] = _game_loop_info(services)

    # -- Event bus ---
    snap["event_bus"] = _event_bus_info(services)

    # -- Empires (stub — filled when empires are tracked) ---
    snap["empires"] = _empires_info(services)

    # -- Battles ---
    snap["battles"] = _battles_info(services)

    # -- Attacks ---
    snap["attacks"] = _attacks_info(services)

    # -- Upgrade provider ---
    snap["upgrade_provider"] = _upgrade_provider_info(services)

    # -- Process ---
    snap["process"] = _process_info()

    return snap


# -------------------------------------------------------------------
# Section collectors
# -------------------------------------------------------------------


def _server_info(services: Services) -> dict[str, Any]:
    srv = services.server
    if srv is None:
        return {"status": "not created"}
    return {
        "host": srv._host,
        "port": srv._port,
        "connections": len(srv._connections),
        "connected_uids": sorted(srv._connections.keys()),
    }


def _game_loop_info(services: Services) -> dict[str, Any]:
    gl = services.game_loop
    if gl is None:
        return {"status": "not created"}
    return {
        "running": gl.is_running,
        "tick_count": gl.tick_count,
        "uptime_s": round(gl.uptime_seconds, 1),
        "uptime_fmt": _fmt_duration(gl.uptime_seconds),
        "last_tick_dt_ms": round(gl.last_tick_dt * 1000, 2),
        "last_tick_work_ms": round(gl.last_tick_duration_ms, 3),
        "avg_tick_work_ms": round(gl.avg_tick_duration_ms, 3),
    }


def _event_bus_info(services: Services) -> dict[str, Any]:
    bus = services.event_bus
    if bus is None:
        return {"status": "not created"}
    handlers = bus._handlers
    return {
        "registered_events": len(handlers),
        "events": {
            (et.__name__ if isinstance(et, type) else str(et)): len(hl)
            for et, hl in handlers.items()
        },
        "total_handlers": sum(len(hl) for hl in handlers.values()),
    }


def _empires_info(services: Services) -> dict[str, Any]:
    es = services.empire_service
    if es is None:
        return {"status": "not created"}
    empires: dict[str, Any] = {}
    for uid, emp in es.all_empires.items():
        # Resources
        res = {k: round(v, 2) for k, v in emp.resources.items()}
        # Buildings in progress
        building_progress = {
            iid: round(remaining, 1)
            for iid, remaining in emp.buildings.items()
        }
        active_builds = sum(1 for r in emp.buildings.values() if r > 0)
        # Knowledge in progress
        knowledge_progress = {
            iid: round(remaining, 1)
            for iid, remaining in emp.knowledge.items()
        }
        active_research = sum(1 for r in emp.knowledge.values() if r > 0)
        empires[str(uid)] = {
            "name": emp.name,
            "resources": res,
            "citizens": emp.citizens,
            "buildings": building_progress,
            "active_builds": active_builds,
            "knowledge": knowledge_progress,
            "active_research": active_research,
            "structures": len(emp.structures),
            "armies": len(emp.armies),
            "effects": dict(emp.effects) if emp.effects else {},
            "artefacts": len(emp.artefacts),
            "life": round(emp.resources.get("life", 0), 2),
            "max_life": emp.max_life,
        }
    return {
        "count": len(empires),
        "details": empires,
    }


def _battles_info(services: Services) -> dict[str, Any]:
    bs = services.battle_service
    if bs is None:
        return {"status": "not created"}
    battles: list[dict[str, Any]] = []
    if hasattr(bs, "_active_battles"):
        for b in bs._active_battles:
            battles.append({
                "critters": len(getattr(b, "critters", {})),
                "structures": len(getattr(b, "structures", {})),
                "pending_shots": len(getattr(b, "pending_shots", [])),
                "observers": len(getattr(b, "observer_uids", set())),
            })
    return {
        "active": len(battles),
        "details": battles,
    }


def _attacks_info(services: Services) -> dict[str, Any]:
    at = services.attack_service
    if at is None:
        return {"status": "not created"}
    attacks: list[dict[str, Any]] = []
    all_attacks = at.get_all_attacks()
    for a in all_attacks:
        attacker = services.empire_service.get(a.attacker_uid)
        defender = services.empire_service.get(a.defender_uid)
        attacks.append({
            "id": a.attack_id,
            "attacker": attacker.name if attacker else f"uid{a.attacker_uid}",
            "defender": defender.name if defender else f"uid{a.defender_uid}",
            "army_aid": a.army_aid,
            "phase": a.phase.value,
            "eta_seconds": round(a.eta_seconds, 1),
            "total_eta_seconds": round(a.total_eta_seconds, 1),
            "siege_remaining_seconds": round(a.siege_remaining_seconds, 1),
            "total_siege_seconds": round(a.total_siege_seconds, 1),
        })
    return {
        "active": len(attacks),
        "details": attacks,
    }


def _upgrade_provider_info(services: Services) -> dict[str, Any]:
    up = services.upgrade_provider
    if up is None:
        return {"status": "not created"}
    items_count = 0
    by_type: dict[str, int] = {}
    if hasattr(up, "_items"):
        items_count = len(up._items)
    if hasattr(up, "_by_type"):
        by_type = {str(k): len(v) for k, v in up._by_type.items()}
    return {
        "items_loaded": items_count,
        "by_type": by_type,
    }


def _process_info() -> dict[str, Any]:
    try:
        import resource
        usage = resource.getrusage(resource.RUSAGE_SELF)
        mem_mb = usage.ru_maxrss / 1024  # Linux: kilobytes → MB
    except Exception:
        mem_mb = 0.0
    return {
        "pid": os.getpid(),
        "memory_mb": round(mem_mb, 1),
        "time": time.strftime("%Y-%m-%d %H:%M:%S"),
    }


# -------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------


def _fmt_duration(seconds: float) -> str:
    """Format seconds into 'Xh Ym Zs'."""
    s = int(seconds)
    h, s = divmod(s, 3600)
    m, s = divmod(s, 60)
    if h:
        return f"{h}h {m:02d}m {s:02d}s"
    if m:
        return f"{m}m {s:02d}s"
    return f"{s}s"
