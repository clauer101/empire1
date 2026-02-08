"""Authentication service — login, signup, session management.

Validates credentials against the database and manages active sessions.
"""

from __future__ import annotations

import hashlib
import logging
import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from gameserver.loaders.game_config_loader import GameConfig
    from gameserver.persistence.database import Database

log = logging.getLogger(__name__)

_EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def _hash_password(password: str) -> str:
    """Simple SHA-256 hash (sufficient for a game server)."""
    return hashlib.sha256(password.encode()).hexdigest()


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

    async def login(self, username: str, password: str) -> int | None:
        """Authenticate a user. Returns UID on success, None on failure."""
        user = await self._db.get_user(username)
        if user is None:
            log.info("Login failed — unknown user: %s", username)
            return None
        if user["password_hash"] != _hash_password(password):
            log.info("Login failed — wrong password for: %s", username)
            return None
        log.info("Login success: %s (uid=%d)", username, user["uid"])
        return user["uid"]

    async def signup(
        self,
        username: str,
        password: str,
        email: str = "",
        empire_name: str = "",
    ) -> int | str:
        """Create a new account. Returns UID on success, or error string."""
        # Validate fields
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

        # Check for existing user
        existing = await self._db.get_user(username)
        if existing is not None:
            return "Username already taken"

        # Create user
        pw_hash = _hash_password(password)
        uid = await self._db.create_user(username, pw_hash, email, empire_name)
        log.info("Signup success: %s (uid=%d, empire=%s)", username, uid, empire_name)
        return uid
