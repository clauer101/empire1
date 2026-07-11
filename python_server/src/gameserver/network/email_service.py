"""Transactional email via Resend (https://resend.com).

Failures (missing API key, network errors, non-2xx responses) are logged
and never raised — email delivery must not break the calling request flow
(e.g. password reset must stay silent about whether an account exists).
"""

from __future__ import annotations

import os

import httpx
import structlog

log = structlog.get_logger(__name__)

RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")
RESEND_FROM = os.environ.get("RESEND_FROM_EMAIL", "Relics'n'Rockets <onboarding@resend.dev>")
_RESEND_URL = "https://api.resend.com/emails"


async def send_password_reset_email(to_email: str, reset_link: str) -> bool:
    """Send a password reset email. Returns True on success, False on failure."""
    if not RESEND_API_KEY:
        log.warning("RESEND_API_KEY not configured — password reset email not sent")
        return False
    html = (
        "<p>Someone requested a password reset for your Relics'n'Rockets account.</p>"
        f'<p><a href="{reset_link}">Click here to reset your password</a></p>'
        "<p>This link expires in 1 hour. If you didn't request this, you can ignore this email.</p>"
    )
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                _RESEND_URL,
                headers={"Authorization": f"Bearer {RESEND_API_KEY}"},
                json={
                    "from": RESEND_FROM,
                    "to": [to_email],
                    "subject": "Reset your password",
                    "html": html,
                },
            )
        if resp.status_code >= 300:
            log.warning("Resend send failed: status=%d body=%s", resp.status_code, resp.text)
            return False
        return True
    except httpx.HTTPError as e:
        log.warning("Resend send failed: %s", e)
        return False
