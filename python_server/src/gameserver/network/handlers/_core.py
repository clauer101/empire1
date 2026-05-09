"""Message handlers — central registry of all message type handlers.

Each handler is an async function that receives a parsed GameMessage
and the sender UID, and returns an optional response dict.

This module is the single place where handler logic lives. To add
a new message handler:

1. Write the handler function below (grouped by category).
2. Register it in :func:`register_all_handlers` at the bottom.

The handler signature is::

    async def handle_xyz(message: GameMessage, sender_uid: int) -> dict | None:
        ...

Returning a dict sends it back to the sender as a JSON response.
Returning None means no response to the sender (fire-and-forget).
"""

from __future__ import annotations

import logging
import time
from typing import Any, Optional, TYPE_CHECKING, cast

if TYPE_CHECKING:
    from gameserver.main import Services
    from gameserver.models.battle import BattleState
    from gameserver.network.router import Handler as _RouterHandler

from gameserver.models.messages import GameMessage
from gameserver.network.handlers.social import (  # noqa: F401 — social domain re-export
    handle_notification_request,
    handle_user_message,
    handle_timeline_request,
    handle_userinfo_request,
    handle_hall_of_fame,
    handle_preferences_request,
    handle_change_preferences,
)

log = logging.getLogger(__name__)

# ===================================================================
# Global counters
# ===================================================================

_next_cid: int = 1  # Critter ID counter
_next_wid: int = 1  # Wave ID counter

# Module-level reference set by register_all_handlers()
_services: Optional[Services] = None


def _svc() -> Services:
    """Get the Services container. Raises if not initialized."""
    assert _services is not None, "handlers: services not initialized"
    return _services


# ===================================================================
# Connection / Keepalive
# ===================================================================

async def handle_ping(message: GameMessage, sender_uid: int) -> dict[str, Any]:
    """Simple ping handler to keep connections alive.

    iOS Safari and other mobile browsers can aggressively close
    inactive WebSocket connections. This handler allows clients
    to send a keepalive ping.
    """
    log.info("Ping received from uid=%d", sender_uid)
    return {"type": "pong", "timestamp": time.time()}


# ===================================================================
# Map validation helpers
# ===================================================================

def _tile_type(v: Any) -> str:
    """Extract tile type from a string or dict tile value."""
    return v if isinstance(v, str) else v.get('type', 'empty')


def _tile_select(v: Any, item_default: str = 'first') -> str:
    """Return per-tile select override, or fall back to the item-level default."""
    if isinstance(v, dict):
        sel: str = v.get('select', item_default)
        return sel
    return item_default


def _has_path_from_spawn_to_castle(tiles: Any) -> bool:
    """Check if there's a path from any spawnpoint to the castle.

    Uses the centralized pathfinding logic from hex_pathfinding module.

    Args:
        tiles: Dict of {"q,r": tile_value} where tile_value is a type string
               or a dict {"type": ..., "select": ...}.

    Returns:
        True if at least one path exists, False otherwise.
    """
    from gameserver.engine.hex_pathfinding import find_path_from_spawn_to_castle
    normalized = {k: _tile_type(v) for k, v in tiles.items()}
    return find_path_from_spawn_to_castle(normalized) is not None


# ===================================================================
# Battle globals
# ===================================================================

_active_battles: "dict[int, BattleState]" = {}  # uid → BattleState
_next_bid: int = 1


# ===================================================================
# Domain submodule imports (Strangler Fig)
# ===================================================================

from gameserver.network.handlers.auth import *  # noqa: E402,F401,F403
from gameserver.network.handlers.auth import (  # noqa: E402,F401
    _build_session_state,
    _build_empire_summary,
    _create_empire_for_new_user,
)
from gameserver.network.handlers.economy import *  # noqa: E402,F401,F403
from gameserver.network.handlers.military import *  # noqa: E402,F401,F403
from gameserver.network.handlers.battle import *  # noqa: E402,F401,F403
from gameserver.network.handlers.battle import (  # noqa: E402,F401
    _evict_observer_from_all,
    _apply_artifact_steal,
    _compute_and_apply_loot,
)


# ===================================================================
# Registration — THE central place to add all handlers
# ===================================================================

def register_all_handlers(services: Services) -> None:
    """Register all message handlers on the router.

    Called once during startup from ``main.py``.
    To add a new handler, add a ``router.register(...)`` line below.

    Args:
        services: Fully initialized Services container.
    """
    # Explicit imports from domain submodules to avoid F405 (star-import ambiguity)
    from gameserver.network.handlers.auth import (  # noqa: PLC0415
        handle_auth_request, handle_signup, handle_create_empire,
    )
    from gameserver.network.handlers.economy import (  # noqa: PLC0415
        handle_summary_request, handle_item_request,
        handle_map_load_request, handle_map_save_request,
        handle_new_item, handle_new_structure, handle_delete_structure,
        handle_upgrade_structure, handle_set_structure_select,
        handle_citizen_upgrade, handle_change_citizen, handle_increase_life,
    )
    from gameserver.network.handlers.military import (  # noqa: PLC0415
        handle_military_request,
        handle_new_army, handle_new_attack, handle_change_army,
        handle_new_wave, handle_change_wave, handle_end_siege,
    )
    from gameserver.network.handlers.battle import (  # noqa: PLC0415
        handle_battle_register, handle_battle_unregister, handle_battle_next_wave,
        _create_battle_start_handler, _create_attack_phase_handler,
        _create_battle_observer_broadcast_handler, _create_item_completed_handler,
        _create_spy_arrived_handler,
    )

    global _services
    _services = services

    router = services.router
    assert router is not None

    # -- Connection / Keepalive ------------------------------------------
    router.register("ping", handle_ping)

    # -- Empire queries --------------------------------------------------
    router.register("summary_request", handle_summary_request)
    router.register("item_request", handle_item_request)
    router.register("military_request", handle_military_request)

    # -- Map (Composer) --------------------------------------------------
    router.register("map_load_request", handle_map_load_request)
    router.register("map_save_request", cast("_RouterHandler", handle_map_save_request))

    # -- Building / Research (fire-and-forget) ---------------------------
    router.register("new_item", handle_new_item)
    router.register("new_structure", handle_new_structure)
    router.register("delete_structure", handle_delete_structure)
    router.register("upgrade_structure", handle_upgrade_structure)
    router.register("set_structure_select", handle_set_structure_select)

    # -- Citizens / Life (fire-and-forget) -------------------------------
    router.register("citizen_upgrade", handle_citizen_upgrade)
    router.register("change_citizen", handle_change_citizen)
    router.register("increase_life", handle_increase_life)

    # -- Military (fire-and-forget) --------------------------------------
    router.register("new_army", handle_new_army)
    router.register("new_attack_request", handle_new_attack)
    router.register("change_army", handle_change_army)
    router.register("new_wave", handle_new_wave)
    router.register("change_wave", handle_change_wave)
    router.register("end_siege", handle_end_siege)

    # -- Battle ----------------------------------------------------------
    router.register("battle_register", handle_battle_register)
    router.register("battle_unregister", handle_battle_unregister)
    router.register("battle_next_wave_request", handle_battle_next_wave)

    # -- Battle event handlers (internal) --------------------------------
    from gameserver.util.events import BattleStartRequested, AttackPhaseChanged, BattleObserverBroadcast, ItemCompleted, SpyArrived
    if services.event_bus:
        services.event_bus.on(BattleStartRequested, _create_battle_start_handler())
        services.event_bus.on(AttackPhaseChanged, _create_attack_phase_handler())
        services.event_bus.on(BattleObserverBroadcast, _create_battle_observer_broadcast_handler())
        services.event_bus.on(ItemCompleted, _create_item_completed_handler())
        services.event_bus.on(SpyArrived, _create_spy_arrived_handler())

    # -- Social / Messaging ----------------------------------------------
    router.register("notification_request", handle_notification_request)
    router.register("user_message", handle_user_message)
    router.register("timeline_request", handle_timeline_request)

    # -- User Info / Hall of Fame ----------------------------------------
    router.register("userinfo_request", handle_userinfo_request)
    router.register("hall_of_fame_request", handle_hall_of_fame)

    # -- Preferences -----------------------------------------------------
    router.register("preferences_request", handle_preferences_request)
    router.register("change_preferences", handle_change_preferences)

    # -- Auth / Account --------------------------------------------------
    router.register("auth_request", handle_auth_request)
    router.register("signup", handle_signup)
    router.register("create_empire", handle_create_empire)

    registered = router.registered_types
    log.info("Registered %d message handlers: %s", len(registered), ", ".join(registered))
