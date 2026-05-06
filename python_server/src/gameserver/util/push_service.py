"""Web Push notification helper."""
from __future__ import annotations

from typing import Any

import json
import logging
import pathlib

log = logging.getLogger(__name__)

_VAPID_PRIVATE = str(pathlib.Path(__file__).parent.parent.parent.parent.parent / "vapid_private.pem")
_VAPID_CLAIMS = {"sub": "mailto:lauer.christoph@gmail.com"}


async def send_push(subscription: dict[str, Any], title: str, body: str) -> bool:
    """Send a Web Push notification. Returns True on success."""
    import asyncio
    from pywebpush import webpush, WebPushException  # type: ignore[import-not-found]
    data = json.dumps({"title": title, "body": body})
    try:
        await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: webpush(
                subscription_info=subscription,
                data=data,
                vapid_private_key=_VAPID_PRIVATE,
                vapid_claims=_VAPID_CLAIMS,
            ),
        )
        return True
    except WebPushException as e:
        status = e.response.status_code if e.response is not None else "?"
        if status == 410:
            log.info("Push subscription gone (410): %s", subscription.get("endpoint", "")[:60])
        else:
            log.warning("Push failed (status=%s): %s", status, e)
        return False
    except Exception as e:
        log.warning("Push error: %s", e)
        return False


async def notify_under_siege(db: Any, defender_uid: int, attacker_name: str) -> None:
    """Send 'under siege' push to all subscriptions of defender_uid."""
    subs = await db.get_push_subscriptions(defender_uid)
    if not subs:
        return
    title = "⚔ Under Siege!"
    body = f"{attacker_name} is attacking your empire!"
    for sub in subs:
        ok = await send_push(sub, title, body)
        if not ok and sub.get("endpoint"):
            await db.delete_push_subscription(defender_uid, sub["endpoint"])


async def notify_siege_started(db: Any, attacker_uid: int, defender_name: str) -> None:
    """Send 'army arrived' push to attacker when traveling → in_siege."""
    subs = await db.get_push_subscriptions(attacker_uid)
    if not subs:
        return
    title = "🏰 Army Arrived!"
    body = f"Your army reached {defender_name} and the siege has begun!"
    for sub in subs:
        ok = await send_push(sub, title, body)
        if not ok and sub.get("endpoint"):
            await db.delete_push_subscription(attacker_uid, sub["endpoint"])
