"""Authentication service — login, signup, session management.

Validates credentials against the database and manages active sessions.
"""

from __future__ import annotations

import logging
import os
import re
import secrets
import time
from typing import TYPE_CHECKING

import argon2
from argon2.exceptions import VerifyMismatchError

from gameserver.network.email_service import send_password_reset_email

if TYPE_CHECKING:
    from gameserver.loaders.game_config_loader import GameConfig
    from gameserver.persistence.database import Database

log = logging.getLogger(__name__)

_EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
_hasher = argon2.PasswordHasher()


def _hash_password(password: str) -> str:
    return _hasher.hash(password)


def _verify_password(password: str, stored: str) -> bool:
    """Verify password against stored hash.

    Handles both argon2 hashes and legacy SHA-256 hex hashes.
    Returns True if the password matches.
    """
    if stored.startswith("$argon2"):
        try:
            return _hasher.verify(stored, password)
        except VerifyMismatchError:
            return False
    # Legacy SHA-256 (unsalted hex digest)
    import hashlib
    return hashlib.sha256(password.encode()).hexdigest() == stored


class AuthService:
    """Authentication and session management.

    Args:
        database: Database instance for user queries.
    """

    def __init__(self, database: Database, game_config: GameConfig | None = None) -> None:
        self._db = database
        self._min_user = game_config.min_username_length if game_config else 2
        self._max_user = game_config.max_username_length if game_config else 20
        self._min_pass = game_config.min_password_length if game_config else 4
        self._site_url = os.environ.get("SITE_URL", "").rstrip("/")

    async def login(self, username: str, password: str) -> int | None:
        """Authenticate a user. Returns UID on success, None on failure."""
        user = await self._db.get_user(username.strip().lower())
        if user is None:
            log.info("Login failed — unknown user: %s", username)
            return None
        stored = user["password_hash"]
        if not _verify_password(password, stored):
            log.info("Login failed — wrong password for: %s", username)
            return None
        # Lazy upgrade: re-hash legacy SHA-256 passwords to argon2 on successful login
        if not stored.startswith("$argon2"):
            new_hash = _hash_password(password)
            await self._db.update_password_hash(user["uid"], new_hash)
            log.info("Upgraded password hash to argon2 for: %s", username)
        log.info("Login success: %s (uid=%d)", username, user["uid"])
        return int(user["uid"])

    async def signup(
        self,
        username: str,
        password: str,
        email: str = "",
        empire_name: str = "",
    ) -> int | str:
        """Create a new account. Returns UID on success, or error string."""
        if not username or len(username) < self._min_user:
            return f"Username must be at least {self._min_user} characters"
        if len(username) > self._max_user:
            return f"Username must be at most {self._max_user} characters"
        if not password or len(password) < self._min_pass:
            return f"Password must be at least {self._min_pass} characters"
        if email and not _EMAIL_RE.match(email):
            return "Invalid email format"
        if not empire_name:
            empire_name = f"{username}'s Empire"

        existing = await self._db.get_user(username)
        if existing is not None:
            return "Username already taken"

        pw_hash = _hash_password(password)
        uid = await self._db.create_user(username, pw_hash, email, empire_name)
        log.info("Signup success: %s (uid=%d, empire=%s)", username, uid, empire_name)
        return uid

    async def change_password(self, uid: int, current_password: str,
                              new_password: str) -> str | None:
        """Change a logged-in user's own password. Returns None on success,
        or an error string."""
        user = await self._db.get_user_by_uid(uid)
        if user is None:
            return "User not found"
        if not _verify_password(current_password, user["password_hash"]):
            return "Current password is incorrect"
        if not new_password or len(new_password) < self._min_pass:
            return f"Password must be at least {self._min_pass} characters"
        await self._db.update_password_hash(uid, _hash_password(new_password))
        log.info("Password changed: uid=%d", uid)
        return None

    async def change_email(self, uid: int, current_password: str, new_email: str) -> str | None:
        """Change a logged-in user's own email. Returns None on success,
        or an error string. Empty email clears it (email is optional)."""
        user = await self._db.get_user_by_uid(uid)
        if user is None:
            return "User not found"
        if not _verify_password(current_password, user["password_hash"]):
            return "Current password is incorrect"
        new_email = new_email.strip()
        if new_email and not _EMAIL_RE.match(new_email):
            return "Invalid email format"
        await self._db.update_email(uid, new_email)
        log.info("Email changed: uid=%d", uid)
        return None

    async def request_password_reset(self, identifier: str) -> None:
        """Send a password reset email, looked up by email or username.

        Never raises and never reveals whether the account exists — the
        caller must always return the same generic response regardless
        of outcome. Accounts without an email on file have no reset path.
        """
        identifier = identifier.strip()
        user = await self._db.get_user_by_email(identifier.lower())
        if user is None:
            by_username = await self._db.get_user(identifier)
            if by_username is not None and by_username["email"]:
                user = by_username
        if user is None:
            return
        token = secrets.token_urlsafe(32)
        expires_at = int(time.time()) + 3600
        await self._db.create_password_reset(token, user["uid"], expires_at)
        reset_link = f"{self._site_url}/#reset-password/{token}"
        await send_password_reset_email(user["email"], reset_link)
        log.info("Password reset requested: uid=%d", user["uid"])

    async def reset_password(self, token: str, new_password: str) -> str | None:
        """Set a new password using a reset token. Returns None on success,
        or an error string."""
        row = await self._db.get_password_reset(token)
        if row is None or row["used"] or row["expires_at"] < time.time():
            return "Reset link is invalid or has expired"
        if not new_password or len(new_password) < self._min_pass:
            return f"Password must be at least {self._min_pass} characters"
        await self._db.update_password_hash(row["uid"], _hash_password(new_password))
        await self._db.mark_password_reset_used(token)
        log.info("Password reset completed: uid=%d", row["uid"])
        return None
