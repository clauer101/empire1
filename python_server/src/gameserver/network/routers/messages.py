"""Messages router — /api/messages/*, /api/battle-feedback, /api/push/*."""
from __future__ import annotations

from typing import Any, TYPE_CHECKING

from fastapi import APIRouter, Depends

from gameserver.network.jwt_auth import get_current_uid
from gameserver.network.rest_models import (
    BattleFeedbackRequest,
    PushSubscribeRequest,
    SendMessageRequest,
)

if TYPE_CHECKING:
    from gameserver.main import Services


def make_router(services: "Services") -> APIRouter:
    router = APIRouter()

    @router.post("/api/messages")
    async def send_message(body: SendMessageRequest, uid: int = Depends(get_current_uid)) -> dict[str, Any]:
        """Send a message. to_uid=None/0 = global chat, otherwise private."""
        if not body.body.strip():
            return {"success": False, "error": "Message body cannot be empty"}
        to_uid = body.to_uid or 0
        if to_uid != 0 and to_uid == uid:
            return {"success": False, "error": "Cannot send message to yourself"}
        assert services.database is not None
        msg = await services.database.send_message(from_uid=uid, to_uid=to_uid, body=body.body.strip())
        return {"success": True, "message": msg}

    @router.get("/api/messages")
    async def get_messages(uid: int = Depends(get_current_uid)) -> dict[str, Any]:
        """Return global chat, private messages and battle reports for the current player."""
        assert services.empire_service is not None
        uid_to_name: dict[int, str] = {
            e.uid: e.name
            for e in services.empire_service.all_empires.values()
        }
        uid_to_username: dict[int, str] = {}
        if services.database is not None:
            for row in await services.database.list_users():
                if row["uid"] not in uid_to_name:
                    uid_to_name[row["uid"]] = (
                        row.get("empire_name") or row.get("username") or f"UID {row['uid']}"
                    )
                uid_to_username[row["uid"]] = row.get("username") or ""

        def _name(u: int) -> str:
            if u == 0:
                return "System"
            return uid_to_name.get(u) or f"UID {u}"

        def _username(u: int) -> str:
            return uid_to_username.get(u) or ""

        def _annotate(m: dict) -> dict:
            return {
                **m,
                "from_name": _name(m["from_uid"]),
                "to_name": _name(m["to_uid"]),
                "from_username": _username(m["from_uid"]),
                "to_username": _username(m["to_uid"]),
            }

        assert services.database is not None
        global_msgs    = await services.database.get_global()
        private_msgs   = await services.database.get_private_for(uid)
        battle_reports = await services.database.get_battle_reports_for(uid)
        unread_private = await services.database.unread_count_private(uid)
        unread_battle  = await services.database.unread_count_battle(uid)

        return {
            "global":         [_annotate(m) for m in global_msgs],
            "private":        [_annotate(m) for m in private_msgs],
            "battle_reports": [_annotate(m) for m in battle_reports],
            "unread_private": unread_private,
            "unread_battle":  unread_battle,
        }

    @router.post("/api/messages/{msg_id}/read")
    async def mark_read(msg_id: int, uid: int = Depends(get_current_uid)) -> dict[str, Any]:
        """Mark a message as read."""
        assert services.database is not None
        ok = await services.database.mark_read(uid, msg_id)
        return {"success": ok}

    @router.post("/api/battle-feedback")
    async def battle_feedback(body: BattleFeedbackRequest, uid: int = Depends(get_current_uid)) -> dict[str, Any]:
        """Log AI battle difficulty feedback to a file."""
        import datetime
        import pathlib
        text = f"[{body.rating}] Army: {body.army_name} (reported by UID {uid})"
        ts = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        log_path = pathlib.Path(__file__).parent.parent.parent.parent.parent / "battle_feedback.log"
        with log_path.open("a", encoding="utf-8") as fh:
            fh.write(f"{ts} {text}\n")
        return {"success": True}

    @router.post("/api/push/subscribe")
    async def push_subscribe(body: PushSubscribeRequest, uid: int = Depends(get_current_uid)) -> dict[str, Any]:
        """Save a Web Push subscription for the current user."""
        assert services.database is not None
        await services.database.save_push_subscription(uid, body.subscription)
        return {"success": True}

    @router.delete("/api/push/subscribe")
    async def push_unsubscribe(body: PushSubscribeRequest, uid: int = Depends(get_current_uid)) -> dict[str, Any]:
        """Remove a Web Push subscription."""
        assert services.database is not None
        endpoint = body.subscription.get("endpoint", "")
        await services.database.delete_push_subscription(uid, endpoint)
        return {"success": True}

    @router.get("/api/push/vapid-public-key")
    async def push_vapid_key() -> dict[str, Any]:
        """Return the VAPID public key for client-side subscription setup."""
        return {"key": "BLnzsQBECw6mNgNpX04wtQiOCVDtPmysmcsWk2Iym9eeDmZ5lcx9fEZ0lEJfPc5Pmp5t-pFHJQbJWNptfeA8TZw"}

    return router
