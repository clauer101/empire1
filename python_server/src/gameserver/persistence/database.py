"""Database access — aiosqlite for users, messages, rankings.

Provides async database operations for:
- User accounts (auth, profile)
- Messages (inbox, sent)
- Rankings (hall of fame)
- Wonders (world wonder progress)
"""

from __future__ import annotations

import logging

import aiosqlite

log = logging.getLogger(__name__)

_SCHEMA = """\
CREATE TABLE IF NOT EXISTS users (
    uid INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    email TEXT NOT NULL DEFAULT '',
    empire_name TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""


class Database:
    """Async SQLite database wrapper.

    Args:
        db_path: Path to the SQLite database file.
    """

    def __init__(self, db_path: str = "gameserver.db") -> None:
        self._db_path = db_path
        self._conn: aiosqlite.Connection | None = None

    async def connect(self) -> None:
        """Open the database connection and create tables if needed."""
        self._conn = await aiosqlite.connect(self._db_path)
        self._conn.row_factory = aiosqlite.Row
        await self._conn.executescript(_SCHEMA)
        await self._conn.commit()
        log.info("Database connected: %s", self._db_path)

    async def close(self) -> None:
        """Close the database connection."""
        if self._conn:
            await self._conn.close()
            self._conn = None

    # -- User operations -------------------------------------------------

    async def get_user(self, username: str) -> dict | None:
        """Look up a user by username."""
        assert self._conn is not None
        async with self._conn.execute(
            "SELECT uid, username, password_hash, email, empire_name FROM users WHERE username = ?",
            (username,),
        ) as cursor:
            row = await cursor.fetchone()
            if row is None:
                return None
            return {
                "uid": row[0],
                "username": row[1],
                "password_hash": row[2],
                "email": row[3],
                "empire_name": row[4],
            }

    async def create_user(
        self, username: str, password_hash: str, email: str = "", empire_name: str = ""
    ) -> int:
        """Create a new user. Returns the new UID."""
        assert self._conn is not None
        async with self._conn.execute(
            "INSERT INTO users (username, password_hash, email, empire_name) VALUES (?, ?, ?, ?)",
            (username, password_hash, email, empire_name),
        ) as cursor:
            uid = cursor.lastrowid
        await self._conn.commit()
        log.info("Created user %s (uid=%d)", username, uid)
        return uid

    async def delete_user(self, username: str) -> bool:
        """Delete a user by username. Returns True if deleted."""
        assert self._conn is not None
        async with self._conn.execute(
            "DELETE FROM users WHERE username = ?",
            (username,),
        ) as cursor:
            deleted = cursor.rowcount > 0
        await self._conn.commit()
        if deleted:
            log.info("Deleted user %s", username)
        return deleted

    async def list_users(self) -> list[dict]:
        """Return all user accounts (without password hashes)."""
        assert self._conn is not None
        async with self._conn.execute(
            "SELECT uid, username, email, empire_name, created_at FROM users ORDER BY uid",
        ) as cursor:
            rows = await cursor.fetchall()
            return [
                {
                    "uid": r[0],
                    "username": r[1],
                    "email": r[2],
                    "empire_name": r[3],
                    "created_at": str(r[4]) if r[4] else "",
                }
                for r in rows
            ]

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
