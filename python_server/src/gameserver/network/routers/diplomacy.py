"""Diplomacy router — /api/diplomacy/*."""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

from fastapi import APIRouter, Depends, Request
from slowapi import Limiter

from gameserver.network.jwt_auth import get_current_uid
from gameserver.network.rest_models import AllianceRequest

if TYPE_CHECKING:
    from gameserver.main import Services


async def dissolve_alliances_for_inactive(services: "Services", uid: int) -> None:
    """Break every mutual alliance an inactive/hidden empire still holds.

    Called from the empire-list endpoints (network/routers/empire.py,
    network/routers/admin.py) wherever they compute the "hidden due to
    inactivity" filter (>1 week without login and <=0 culture — see
    `_is_recently_active`) — an inactive player can't act to break an
    alliance themselves, so this does it for them. Idempotent: an empire
    with no remaining mutual alliance is a cheap no-op, so it's safe to call
    on every request rather than only once on the transition into hidden.

    Unlike the player-initiated toggle_alliance break path, this charges no
    `alliance_culture_cost` — becoming inactive isn't a decision the player
    made, and the trigger condition (<=0 culture) usually leaves nothing to
    charge anyway.
    """
    assert services.database is not None
    declared_to, declared_by = await services.database.get_alliance_declarations_for(uid)
    partners = declared_to & declared_by  # mutual = declared in both directions
    if not partners:
        return
    for partner_uid in partners:
        # Both directions must go — removing only uid's own declaration would
        # leave the partner's declaration standing as a dangling pending
        # request instead of a clean break.
        await services.database.remove_alliance_declaration(uid, partner_uid)
        await services.database.remove_alliance_declaration(partner_uid, uid)
        if services.empire_service is not None:
            empire = services.empire_service.get(uid)
            partner = services.empire_service.get(partner_uid)
            if empire is not None:
                empire.allied_uids.discard(partner_uid)
                services.empire_service.recalculate_effects(empire)
            if partner is not None:
                partner.allied_uids.discard(uid)
                services.empire_service.recalculate_effects(partner)


def _alliance_status(target_uid: int, declared_to: set[int], declared_by: set[int]) -> str:
    """Derive the viewer's relationship status toward target_uid.

    declared_to: uids the viewer has declared toward.
    declared_by: uids that have declared toward the viewer.
    """
    sent = target_uid in declared_to
    received = target_uid in declared_by
    if sent and received:
        return "allied"
    if sent:
        return "pending_sent"
    if received:
        return "pending_received"
    return "none"


def _alliances_disabled(services: "Services") -> bool:
    """True while the season runs without diplomacy (game.yaml alliances_enabled).

    The feature is switched off per season rather than removed: the endpoints
    below stay intact and simply refuse, so turning the flag back on restores
    diplomacy without touching this code.
    """
    gc = services.game_config
    return gc is not None and not gc.alliances_enabled


_DISABLED_RESPONSE = {"success": False, "error": "Alliances are disabled this season"}


def make_router(services: "Services", limiter: Limiter) -> APIRouter:
    router = APIRouter()

    @router.post("/api/diplomacy/alliance")
    @limiter.limit("20/minute")
    async def toggle_alliance(
        request: Request, body: AllianceRequest, uid: int = Depends(get_current_uid),
    ) -> dict[str, Any]:
        """Toggle the current player's alliance declaration toward target_uid.

        When the toggle completes a mutual (two-way) declaration, both empires
        immediately pay `alliance_culture_cost` (fraction of their own culture,
        from game.yaml) to each other as a one-time alliance formation cost.

        When the toggle breaks a previously-active (mutual) alliance, the
        breaking player alone pays `alliance_culture_cost` again — this
        amount is destroyed, not transferred to the ex-partner.

        Rejects completing a new mutual alliance if either side is already at
        their alliance capacity (see EmpireService.get_max_alliances — flat
        1 for now, extensible later via a per-empire effect).

        Refuses outright while `alliances_enabled` is false in game.yaml.
        """
        if _alliances_disabled(services):
            return dict(_DISABLED_RESPONSE)
        if body.target_uid == uid or body.target_uid <= 0:
            return {"success": False, "error": "Invalid target"}
        assert services.database is not None
        declared_to_before, declared_by_before = await services.database.get_alliance_declarations_for(uid)
        was_allied = _alliance_status(body.target_uid, declared_to_before, declared_by_before) == "allied"

        # Would this toggle create a NEW mutual alliance? Block it if either
        # side is already at capacity with a different partner.
        would_complete = not was_allied and body.target_uid in declared_by_before
        if would_complete and services.empire_service is not None:
            empire = services.empire_service.get(uid)
            partner = services.empire_service.get(body.target_uid)
            if empire is not None and len(empire.allied_uids - {body.target_uid}) >= services.empire_service.get_max_alliances(empire):
                return {
                    "success": False,
                    "error": "You already have an active alliance. Break it before forming a new one.",
                }
            if partner is not None and len(partner.allied_uids - {uid}) >= services.empire_service.get_max_alliances(partner):
                return {
                    "success": False,
                    "error": f"{partner.name} already has an active alliance and cannot accept another right now.",
                }

        declared = await services.database.toggle_alliance_declaration(uid, body.target_uid)
        declared_to, declared_by = await services.database.get_alliance_declarations_for(uid)
        status = _alliance_status(body.target_uid, declared_to, declared_by)

        if services.empire_service is not None:
            empire = services.empire_service.get(uid)
            partner = services.empire_service.get(body.target_uid)
            cost_ratio = services.game_config.alliance_culture_cost if services.game_config is not None else 0.0

            if status == "allied" and cost_ratio > 0 and empire is not None and partner is not None:
                empire_payment = empire.resources.get("culture", 0.0) * cost_ratio
                partner_payment = partner.resources.get("culture", 0.0) * cost_ratio
                empire.resources["culture"] -= empire_payment
                partner.resources["culture"] += empire_payment
                partner.resources["culture"] -= partner_payment
                empire.resources["culture"] += partner_payment
            elif was_allied and not declared and cost_ratio > 0 and empire is not None:
                # This player broke a previously-active alliance: they alone
                # pay the cost again, destroyed (not sent to the ex-partner).
                penalty = empire.resources.get("culture", 0.0) * cost_ratio
                empire.resources["culture"] -= penalty

            # Keep the in-memory allied_uids cache (used for ally ruler
            # effects) in sync with the DB, and recompute effects for both
            # sides whenever the mutual status actually changed.
            if (status == "allied") != was_allied:
                if empire is not None:
                    if status == "allied":
                        empire.allied_uids.add(body.target_uid)
                    else:
                        empire.allied_uids.discard(body.target_uid)
                    services.empire_service.recalculate_effects(empire)
                if partner is not None:
                    if status == "allied":
                        partner.allied_uids.add(uid)
                    else:
                        partner.allied_uids.discard(uid)
                    services.empire_service.recalculate_effects(partner)

        return {"success": True, "declared": declared, "alliance_status": status}

    @router.post("/api/diplomacy/alliance/decline")
    @limiter.limit("20/minute")
    async def decline_alliance(
        request: Request, body: AllianceRequest, uid: int = Depends(get_current_uid),
    ) -> dict[str, Any]:
        """Decline an alliance request received from body.target_uid.

        Removes only target_uid's outgoing declaration toward uid — the
        caller's own declarations (e.g. an existing mutual alliance
        elsewhere) are untouched. Unlike toggle_alliance, this never forms
        or breaks an alliance and never charges the culture cost, since
        declining isn't breaking anything the caller declared.
        """
        if _alliances_disabled(services):
            return dict(_DISABLED_RESPONSE)
        if body.target_uid == uid or body.target_uid <= 0:
            return {"success": False, "error": "Invalid target"}
        assert services.database is not None
        declared_to, declared_by = await services.database.get_alliance_declarations_for(uid)
        if _alliance_status(body.target_uid, declared_to, declared_by) != "pending_received":
            return {"success": False, "error": "No pending request from this empire"}
        removed = await services.database.remove_alliance_declaration(body.target_uid, uid)
        return {"success": True, "declined": removed}

    return router
