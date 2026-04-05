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
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_seen TIMESTAMP
);
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    from_uid INTEGER NOT NULL,
    to_uid INTEGER NOT NULL,
    body TEXT NOT NULL DEFAULT '',
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    read INTEGER NOT NULL DEFAULT 0
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
        # Migrate: add last_seen column if missing
        try:
            await self._conn.execute("SELECT last_seen FROM users LIMIT 1")
        except Exception:
            await self._conn.execute("ALTER TABLE users ADD COLUMN last_seen TIMESTAMP")
        await self._conn.commit()
        log.info("Database connected: %s", self._db_path)

    async def close(self) -> None:
        """Close the database connection."""
        if self._conn:
            await self._conn.close()
            self._conn = None

    # -- User operations -------------------------------------------------

    async def get_user_by_uid(self, uid: int) -> dict | None:
        """Look up a user by UID."""
        assert self._conn is not None
        async with self._conn.execute(
            "SELECT uid, username, email, empire_name FROM users WHERE uid = ?",
            (uid,),
        ) as cursor:
            row = await cursor.fetchone()
            if row is None:
                return None
            return {"uid": row[0], "username": row[1], "email": row[2], "empire_name": row[3]}

    async def get_user(self, username: str) -> dict | None:
        """Look up a user by username (case-insensitive)."""
        assert self._conn is not None
        async with self._conn.execute(
            "SELECT uid, username, password_hash, email, empire_name FROM users WHERE LOWER(username) = LOWER(?)",
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

    async def update_last_seen(self, uid: int) -> None:
        """Update the last_seen timestamp for a user."""
        assert self._conn is not None
        await self._conn.execute(
            "UPDATE users SET last_seen = CURRENT_TIMESTAMP WHERE uid = ?",
            (uid,),
        )
        await self._conn.commit()

    async def list_users(self) -> list[dict]:
        """Return all user accounts (without password hashes)."""
        assert self._conn is not None
        async with self._conn.execute(
            "SELECT uid, username, email, empire_name, created_at, last_seen FROM users ORDER BY uid",
        ) as cursor:
            rows = await cursor.fetchall()
            return [
                {
                    "uid": r[0],
                    "username": r[1],
                    "email": r[2],
                    "empire_name": r[3],
                    "created_at": str(r[4]) if r[4] else "",
                    "last_seen": str(r[5]) if r[5] else "",
                }
                for r in rows
            ]

    async def delete_old_messages(self, max_age_days: int = 7) -> int:
        """Delete messages older than max_age_days. Returns number of deleted rows."""
        assert self._conn is not None
        async with self._conn.execute(
            "DELETE FROM messages WHERE sent_at < datetime('now', ?)",
            (f"-{max_age_days} days",),
        ) as cursor:
            deleted = cursor.rowcount
        await self._conn.commit()
        if deleted:
            log.info("MessageStore: deleted %d messages older than %d days", deleted, max_age_days)
        return deleted

    # -- Message operations ----------------------------------------------

    async def send_message(self, from_uid: int, to_uid: int, body: str) -> dict:
        """Store a new message and return it as a dict."""
        assert self._conn is not None
        read = 1 if from_uid == 0 else 0  # system/AI messages pre-read
        async with self._conn.execute(
            "INSERT INTO messages (from_uid, to_uid, body, read) VALUES (?, ?, ?, ?)",
            (from_uid, to_uid, body, read),
        ) as cursor:
            msg_id = cursor.lastrowid
        await self._conn.commit()
        log.info("MessageStore: message %d from uid=%d to uid=%d", msg_id, from_uid, to_uid)
        async with self._conn.execute(
            "SELECT id, from_uid, to_uid, body, sent_at, read FROM messages WHERE id = ?",
            (msg_id,),
        ) as cursor:
            row = await cursor.fetchone()
        return self._msg_row_to_dict(row)

    async def get_inbox(self, uid: int) -> list[dict]:
        """Return all messages received by uid, newest first."""
        assert self._conn is not None
        async with self._conn.execute(
            "SELECT id, from_uid, to_uid, body, sent_at, read FROM messages WHERE to_uid = ? ORDER BY id DESC",
            (uid,),
        ) as cursor:
            rows = await cursor.fetchall()
        return [self._msg_row_to_dict(r) for r in rows]

    async def get_sent(self, uid: int) -> list[dict]:
        """Return all messages sent by uid, newest first."""
        assert self._conn is not None
        async with self._conn.execute(
            "SELECT id, from_uid, to_uid, body, sent_at, read FROM messages WHERE from_uid = ? ORDER BY id DESC",
            (uid,),
        ) as cursor:
            rows = await cursor.fetchall()
        return [self._msg_row_to_dict(r) for r in rows]

    async def mark_read(self, uid: int, msg_id: int) -> bool:
        """Mark a message as read. Returns True if found."""
        assert self._conn is not None
        async with self._conn.execute(
            "UPDATE messages SET read = 1 WHERE id = ? AND to_uid = ?",
            (msg_id, uid),
        ) as cursor:
            updated = cursor.rowcount > 0
        if updated:
            await self._conn.commit()
        return updated

    async def unread_count(self, uid: int) -> int:
        """Number of unread inbox messages for uid."""
        assert self._conn is not None
        async with self._conn.execute(
            "SELECT COUNT(*) FROM messages WHERE to_uid = ? AND read = 0",
            (uid,),
        ) as cursor:
            row = await cursor.fetchone()
        return row[0] if row else 0

    async def get_global(self, limit: int = 200) -> list[dict]:
        """Return global chat messages (to_uid=0, from real players), oldest first."""
        assert self._conn is not None
        async with self._conn.execute(
            "SELECT id, from_uid, to_uid, body, sent_at, read FROM messages "
            "WHERE to_uid = 0 AND from_uid != 0 ORDER BY id DESC LIMIT ?",
            (limit,),
        ) as cursor:
            rows = await cursor.fetchall()
        return list(reversed([self._msg_row_to_dict(r) for r in rows]))

    async def get_private_for(self, uid: int) -> list[dict]:
        """Return private messages where uid is sender or receiver (no global, no battle reports)."""
        assert self._conn is not None
        async with self._conn.execute(
            "SELECT id, from_uid, to_uid, body, sent_at, read FROM messages "
            "WHERE (to_uid = ? OR from_uid = ?) AND to_uid != 0 AND from_uid != 0 ORDER BY id DESC",
            (uid, uid),
        ) as cursor:
            rows = await cursor.fetchall()
        return [self._msg_row_to_dict(r) for r in rows]

    async def get_battle_reports_for(self, uid: int) -> list[dict]:
        """Return system/battle-report messages sent to uid (from_uid=0)."""
        assert self._conn is not None
        async with self._conn.execute(
            "SELECT id, from_uid, to_uid, body, sent_at, read FROM messages "
            "WHERE to_uid = ? AND from_uid = 0 ORDER BY id DESC",
            (uid,),
        ) as cursor:
            rows = await cursor.fetchall()
        return [self._msg_row_to_dict(r) for r in rows]

    async def unread_count_private(self, uid: int) -> int:
        """Unread private messages for uid (excludes battle reports and global)."""
        assert self._conn is not None
        async with self._conn.execute(
            "SELECT COUNT(*) FROM messages WHERE to_uid = ? AND from_uid != 0 AND read = 0",
            (uid,),
        ) as cursor:
            row = await cursor.fetchone()
        return row[0] if row else 0

    async def unread_count_battle(self, uid: int) -> int:
        """Unread battle report messages for uid."""
        assert self._conn is not None
        async with self._conn.execute(
            "SELECT COUNT(*) FROM messages WHERE to_uid = ? AND from_uid = 0 AND read = 0",
            (uid,),
        ) as cursor:
            row = await cursor.fetchone()
        return row[0] if row else 0

    async def migrate_messages_from_yaml(self, yaml_path: str) -> int:
        """Import messages from the old YAML file. Returns number of messages imported."""
        import base64
        from pathlib import Path
        import yaml as _yaml

        path = Path(yaml_path)
        if not path.exists():
            return 0
        assert self._conn is not None

        # Check if messages table already has data
        async with self._conn.execute("SELECT COUNT(*) FROM messages") as cursor:
            row = await cursor.fetchone()
        if row and row[0] > 0:
            log.info("MessageStore: DB already has %d messages, skipping YAML migration", row[0])
            return 0

        try:
            data = _yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            messages = data.get("messages", []) or []
        except Exception:
            log.exception("MessageStore: failed to read YAML for migration")
            return 0

        count = 0
        for m in messages:
            try:
                body_b64 = m.get("body_b64", "")
                body = base64.b64decode(body_b64.encode("ascii")).decode("utf-8")
            except Exception:
                body = ""
            read = 1 if m.get("read", False) else 0
            sent_at = m.get("sent_at", None)
            await self._conn.execute(
                "INSERT INTO messages (id, from_uid, to_uid, body, sent_at, read) VALUES (?, ?, ?, ?, ?, ?)",
                (m["id"], m["from_uid"], m["to_uid"], body, sent_at, read),
            )
            count += 1
        await self._conn.commit()
        log.info("MessageStore: migrated %d messages from %s", count, yaml_path)
        return count

    def _msg_row_to_dict(self, row) -> dict:
        return {
            "id": row[0],
            "from_uid": row[1],
            "to_uid": row[2],
            "body": row[3],
            "sent_at": str(row[4]) if row[4] else "",
            "read": bool(row[5]),
        }

    # -- Ranking operations ----------------------------------------------

    async def update_ranking(self, uid: int, tai: float) -> None:
        """Update a player's ranking score."""
        # TODO: implement
        pass

    async def get_rankings(self, limit: int = 20) -> list[dict]:
        """Get top rankings."""
        # TODO: implement
        return []
