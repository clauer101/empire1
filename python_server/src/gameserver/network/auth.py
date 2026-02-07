"""Authentication service — login, signup, session management.

Validates credentials against the database and manages active sessions.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from gameserver.persistence.database import Database


class AuthService:
    """Authentication and session management.

    Args:
        database: Database instance for user queries.
    """

    def __init__(self, database: Database) -> None:
        self._db = database

    async def login(self, username: str, password: str) -> int | None:
        """Authenticate a user. Returns UID on success, None on failure."""
        # TODO: implement
        return None

    async def signup(self, username: str, password: str, email: str = "") -> int | str:
        """Create a new account. Returns UID or error string."""
        # TODO: implement
        return "not implemented"
