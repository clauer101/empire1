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
from typing import Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from gameserver.main import Services

from gameserver.models.messages import GameMessage

log = logging.getLogger(__name__)

# Module-level reference set by register_all_handlers()
_services: Optional[Services] = None


def _svc() -> Services:
    """Get the Services container. Raises if not initialized."""
    assert _services is not None, "handlers: services not initialized"
    return _services


# ===================================================================
# Empire queries
# ===================================================================

async def handle_summary_request(
    message: GameMessage, sender_uid: int,
) -> Optional[dict[str, Any]]:
    """Handle ``summary_request`` — return full empire overview.

    Equivalent to the Java ``SummaryRequest`` → ``SummaryResponse`` flow
    that passes through the GameEngine.

    The response contains resources, citizens, buildings, research,
    structures, effects, artefacts, and life status.
    """
    svc = _svc()
    # Use sender_uid from the authenticated session.
    # For unauthenticated (guest) connections, fall back to the
    # ``sender`` field in the message — this allows debug / test access.
    # Once auth is fully implemented, only sender_uid should be trusted.
    target_uid = sender_uid if sender_uid > 0 else message.sender
    empire = svc.empire_service.get(target_uid)
    if empire is None:
        return {
            "type": "summary_response",
            "error": f"No empire found for uid {target_uid}",
        }

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

    return {
        "type": "summary_response",
        "uid": empire.uid,
        "name": empire.name,
        "resources": {k: round(v, 2) for k, v in empire.resources.items()},
        "citizens": dict(empire.citizens),
        "citizen_price": svc.empire_service._citizen_price(sum(empire.citizens.values()) + 1),
        "max_life": empire.max_life,
        "effects": dict(empire.effects),
        "artefacts": list(empire.artefacts),
        "active_buildings": active_buildings,
        "completed_buildings": completed_buildings,
        "active_research": active_research,
        "completed_research": completed_research,
        "structures": structures_list,
        "army_count": len(empire.armies),
        "spy_count": len(empire.spies),
    }


async def handle_item_request(
    message: GameMessage, sender_uid: int,
) -> Optional[dict[str, Any]]:
    """Handle ``item_request`` — return available buildings & research.

    Returns all buildings/knowledge whose prerequisites are satisfied
    by the empire's completed items.
    """
    svc = _svc()
    target_uid = sender_uid if sender_uid > 0 else message.sender
    empire = svc.empire_service.get(target_uid)
    if empire is None:
        return {
            "type": "item_response",
            "buildings": {},
            "knowledge": {},
        }

    # Completed items = buildings done + knowledge done + artefacts owned
    completed: set[str] = set()
    for iid, remaining in empire.buildings.items():
        if remaining <= 0:
            completed.add(iid)
    for iid, remaining in empire.knowledge.items():
        if remaining <= 0:
            completed.add(iid)
    completed.update(empire.artefacts)

    from gameserver.models.items import ItemType
    up = svc.upgrade_provider

    buildings = {}
    for item in up.available_items(ItemType.BUILDING, completed):
        buildings[item.iid] = {
            "name": item.name,
            "effort": item.effort,
            "costs": dict(item.costs),
            "requirements": list(item.requirements),
            "effects": dict(item.effects),
        }

    knowledge = {}
    for item in up.available_items(ItemType.KNOWLEDGE, completed):
        knowledge[item.iid] = {
            "name": item.name,
            "effort": item.effort,
            "costs": dict(item.costs),
            "requirements": list(item.requirements),
            "effects": dict(item.effects),
        }

    return {
        "type": "item_response",
        "buildings": buildings,
        "knowledge": knowledge,
    }


async def handle_military_request(
    message: GameMessage, sender_uid: int,
) -> Optional[dict[str, Any]]:
    """Handle ``military_request`` — return armies and attack status.

    TODO: Implement once ArmyService and AttackService are complete.
    """
    svc = _svc()
    empire = svc.empire_service.get(sender_uid)
    if empire is None:
        return {
            "type": "military_response",
            "error": f"No empire found for uid {sender_uid}",
        }

    armies = []
    for army in empire.armies:
        armies.append({
            "aid": army.aid,
            "name": army.name,
            "direction": army.direction.value,
            "wave_count": len(army.waves),
        })

    return {
        "type": "military_response",
        "armies": armies,
        "attacks_incoming": [],  # TODO: from AttackService
        "attacks_outgoing": [],  # TODO: from AttackService
        "available_critters": [],  # TODO: from UpgradeProvider
    }


# ===================================================================
# Building / Research
# ===================================================================

async def handle_new_item(
    message: GameMessage, sender_uid: int,
) -> Optional[dict[str, Any]]:
    """Handle ``new_item`` — start building or researching an item."""
    svc = _svc()
    iid = getattr(message, "iid", "")
    target_uid = sender_uid if sender_uid > 0 else message.sender
    empire = svc.empire_service.get(target_uid)
    if empire is None:
        return {"type": "item_response_error", "error": "No empire found"}

    error = svc.empire_service.build_item(empire, iid)
    if error:
        log.info("new_item failed uid=%d iid=%s: %s", target_uid, iid, error)
        return {"type": "build_response", "success": False, "iid": iid, "error": error}

    log.info("new_item success uid=%d iid=%s", target_uid, iid)
    return {"type": "build_response", "success": True, "iid": iid, "error": ""}


async def handle_new_structure(
    message: GameMessage, sender_uid: int,
) -> Optional[dict[str, Any]]:
    """Handle ``new_structure`` — place a tower on the map.

    TODO: Implement in EmpireService.place_structure().
    """
    log.info("new_structure from uid=%d (not yet implemented)", sender_uid)
    return None


async def handle_delete_structure(
    message: GameMessage, sender_uid: int,
) -> Optional[dict[str, Any]]:
    """Handle ``delete_structure`` — remove a tower from the map.

    TODO: Implement in EmpireService.remove_structure().
    """
    log.info("delete_structure from uid=%d (not yet implemented)", sender_uid)
    return None


# ===================================================================
# Citizens
# ===================================================================

async def handle_citizen_upgrade(
    message: GameMessage, sender_uid: int,
) -> Optional[dict[str, Any]]:
    """Handle ``citizen_upgrade`` — add one citizen.

    TODO: Implement in EmpireService.upgrade_citizen().
    """
    svc = _svc()
    empire = svc.empire_service.get(sender_uid)
    if empire is None:
        return {"type": "citizen_upgrade_response", "success": False, "error": "No empire found"}
    error = svc.empire_service.upgrade_citizen(empire)
    if error:
        log.info("citizen_upgrade failed uid=%d: %s", sender_uid, error)
        return {"type": "citizen_upgrade_response", "success": False, "error": error}
    log.info("citizen_upgrade success uid=%d", sender_uid)
    return {"type": "citizen_upgrade_response", "success": True, "error": ""}


async def handle_change_citizen(
    message: GameMessage, sender_uid: int,
) -> Optional[dict[str, Any]]:
    """Handle ``change_citizen`` — redistribute citizens.

    TODO: Implement in EmpireService.change_citizens().
    """
    log.info("change_citizen from uid=%d (not yet implemented)", sender_uid)
    return None


# ===================================================================
# Military / Army
# ===================================================================

async def handle_new_army(
    message: GameMessage, sender_uid: int,
) -> Optional[dict[str, Any]]:
    """Handle ``new_army`` — create a new army.

    TODO: Implement in ArmyService.create_army().
    """
    log.info("new_army from uid=%d (not yet implemented)", sender_uid)
    return None


async def handle_new_attack(
    message: GameMessage, sender_uid: int,
) -> Optional[dict[str, Any]]:
    """Handle ``new_attack_request`` — launch an attack.

    TODO: Implement in AttackService.start_attack().
    """
    log.info("new_attack_request from uid=%d (not yet implemented)", sender_uid)
    return None


async def handle_change_army(
    message: GameMessage, sender_uid: int,
) -> Optional[dict[str, Any]]:
    """Handle ``change_army`` — rename army or change direction.

    TODO: Validate army not in battle/travelling, update name + direction.
    """
    log.info("change_army from uid=%d (not yet implemented)", sender_uid)
    return None


async def handle_new_wave(
    message: GameMessage, sender_uid: int,
) -> Optional[dict[str, Any]]:
    """Handle ``new_wave`` — add a critter wave to an army.

    TODO: Check max waves, gold cost for extra slots, boss uniqueness.
    """
    log.info("new_wave from uid=%d (not yet implemented)", sender_uid)
    return None


async def handle_change_wave(
    message: GameMessage, sender_uid: int,
) -> Optional[dict[str, Any]]:
    """Handle ``change_wave`` — change critter type of an existing wave.

    TODO: Validate army not in battle, swap IID on wave number.
    """
    log.info("change_wave from uid=%d (not yet implemented)", sender_uid)
    return None


async def handle_end_siege(
    message: GameMessage, sender_uid: int,
) -> Optional[dict[str, Any]]:
    """Handle ``end_siege`` — end the ongoing siege on sender's empire.

    TODO: Call empire.end_siege().
    """
    log.info("end_siege from uid=%d (not yet implemented)", sender_uid)
    return None


# ===================================================================
# Structures (additional)
# ===================================================================

async def handle_upgrade_structure(
    message: GameMessage, sender_uid: int,
) -> Optional[dict[str, Any]]:
    """Handle ``upgrade_structure`` — upgrade a tower on the map.

    TODO: Check requirements & resources, replace structure with upgrade.
    """
    log.info("upgrade_structure from uid=%d (not yet implemented)", sender_uid)
    return None


# ===================================================================
# Life
# ===================================================================

async def handle_increase_life(
    message: GameMessage, sender_uid: int,
) -> Optional[dict[str, Any]]:
    """Handle ``increase_life`` — increase max life by 1.

    TODO: Check culture cost (progressive), check life cap from effects.
    """
    log.info("increase_life from uid=%d (not yet implemented)", sender_uid)
    return None


# ===================================================================
# Battle
# ===================================================================

async def handle_battle_register(
    message: GameMessage, sender_uid: int,
) -> Optional[dict[str, Any]]:
    """Handle ``battle_register`` — register as battle observer.

    TODO: Register sender as observer of the battle for given UID.
    """
    log.info("battle_register from uid=%d (not yet implemented)", sender_uid)
    return None


async def handle_battle_unregister(
    message: GameMessage, sender_uid: int,
) -> Optional[dict[str, Any]]:
    """Handle ``battle_unregister`` — unregister from battle observation.

    TODO: Remove sender from battle observer list.
    """
    log.info("battle_unregister from uid=%d (not yet implemented)", sender_uid)
    return None


async def handle_battle_next_wave(
    message: GameMessage, sender_uid: int,
) -> Optional[dict[str, Any]]:
    """Handle ``battle_next_wave_request`` — trigger next wave in battle.

    TODO: Call battle.next_wave_requested(), return wave preview.
    """
    log.info("battle_next_wave from uid=%d (not yet implemented)", sender_uid)
    return None


# ===================================================================
# Social / Messaging
# ===================================================================

async def handle_notification_request(
    message: GameMessage, sender_uid: int,
) -> Optional[dict[str, Any]]:
    """Handle ``notification_request`` — fetch pending notification.

    TODO: Return pending notification or fallback to summary_request.
    """
    log.info("notification_request from uid=%d (not yet implemented)", sender_uid)
    return None


async def handle_user_message(
    message: GameMessage, sender_uid: int,
) -> Optional[dict[str, Any]]:
    """Handle ``user_message`` — send a private message to another player.

    TODO: Store message in DB with sender, receiver, body, timestamp.
    """
    log.info("user_message from uid=%d (not yet implemented)", sender_uid)
    return None


async def handle_timeline_request(
    message: GameMessage, sender_uid: int,
) -> Optional[dict[str, Any]]:
    """Handle ``timeline_request`` — fetch mailbox / message history.

    TODO: Mark messages read, return last 25 messages (max 10 days).
    """
    log.info("timeline_request from uid=%d (not yet implemented)", sender_uid)
    return None


# ===================================================================
# User Info / Hall of Fame
# ===================================================================

async def handle_userinfo_request(
    message: GameMessage, sender_uid: int,
) -> Optional[dict[str, Any]]:
    """Handle ``userinfo_request`` — return info about players.

    TODO: Return UserInfo (TAI, currBuilding, citizens, etc.) for requested UIDs.
    """
    log.info("userinfo_request from uid=%d (not yet implemented)", sender_uid)
    return None


async def handle_hall_of_fame(
    message: GameMessage, sender_uid: int,
) -> Optional[dict[str, Any]]:
    """Handle ``hall_of_fame_request`` — return rankings and trophies.

    TODO: Load ranking, winners, prosperity, defense god, treasure hunter, world wonder.
    """
    log.info("hall_of_fame_request from uid=%d (not yet implemented)", sender_uid)
    return None


# ===================================================================
# Preferences
# ===================================================================

async def handle_preferences_request(
    message: GameMessage, sender_uid: int,
) -> Optional[dict[str, Any]]:
    """Handle ``preferences_request`` — return player preferences.

    TODO: Load e-mail/statement from DB.
    """
    log.info("preferences_request from uid=%d (not yet implemented)", sender_uid)
    return None


async def handle_change_preferences(
    message: GameMessage, sender_uid: int,
) -> Optional[dict[str, Any]]:
    """Handle ``change_preferences`` — update player profile.

    TODO: Update statement + e-mail in DB.
    """
    log.info("change_preferences from uid=%d (not yet implemented)", sender_uid)
    return None


# ===================================================================
# Auth / Account
# ===================================================================

async def handle_auth_request(
    message: GameMessage, sender_uid: int,
) -> Optional[dict[str, Any]]:
    """Handle ``auth_request`` — authenticate a player."""
    svc = _svc()
    username = getattr(message, "username", "")
    password = getattr(message, "password", "")

    uid = await svc.auth_service.login(username, password)
    if uid is not None:
        return {
            "type": "auth_response",
            "success": True,
            "uid": uid,
            "reason": "",
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
    username = getattr(message, "username", "")
    password = getattr(message, "password", "")
    email = getattr(message, "email", "")
    empire_name = getattr(message, "empire_name", "")

    result = await svc.auth_service.signup(username, password, email, empire_name)
    if isinstance(result, int):
        log.info("Signup success: user=%s uid=%d", username, result)
        # Create empire for the new user — INIT is auto-completed (effort 0)
        from gameserver.models.empire import Empire
        empire = Empire(
            uid=result,
            name=empire_name or f"{username}'s Empire",
            buildings={"INIT": 0.0},
        )
        svc.empire_service.register(empire)
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
    global _services
    _services = services

    router = services.router

    # -- Empire queries --------------------------------------------------
    router.register("summary_request", handle_summary_request)
    router.register("item_request", handle_item_request)
    router.register("military_request", handle_military_request)

    # -- Building / Research (fire-and-forget) ---------------------------
    router.register("new_item", handle_new_item)
    router.register("new_structure", handle_new_structure)
    router.register("delete_structure", handle_delete_structure)
    router.register("upgrade_structure", handle_upgrade_structure)

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
