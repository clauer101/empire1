"""Database access — aiosqlite for users, messages, rankings.

Provides async database operations for:
- User accounts (auth, profile)
- Messages (inbox, sent)
- Rankings (hall of fame)
- Wonders (world wonder progress)
"""

from __future__ import annotations


class Database:
    """Async SQLite database wrapper.

    Args:
        db_path: Path to the SQLite database file.
    """

    def __init__(self, db_path: str = "gameserver.db") -> None:
        self._db_path = db_path
        self._conn = None

    async def connect(self) -> None:
        """Open the database connection and create tables if needed."""
        # TODO: implement with aiosqlite
        pass

    async def close(self) -> None:
        """Close the database connection."""
        # TODO: implement
        pass

    # -- User operations -------------------------------------------------

    async def get_user(self, username: str) -> dict | None:
        """Look up a user by username."""
        # TODO: implement
        return None

    async def create_user(self, username: str, password_hash: str, email: str = "") -> int:
        """Create a new user. Returns the new UID."""
        # TODO: implement
        return 0

    # -- Message operations ----------------------------------------------

    async def get_messages(self, uid: int, limit: int = 50) -> list[dict]:
        """Get messages for a user."""
        # TODO: implement
        return []

    async def send_message(self, from_uid: int, to_uid: int, text: str) -> None:
        """Store a user message."""
        # TODO: implement
        pass

    # -- Ranking operations ----------------------------------------------

    async def update_ranking(self, uid: int, tai: float) -> None:
        """Update a player's ranking score."""
        # TODO: implement
        pass

    async def get_rankings(self, limit: int = 20) -> list[dict]:
        """Get top rankings."""
        # TODO: implement
        return []
