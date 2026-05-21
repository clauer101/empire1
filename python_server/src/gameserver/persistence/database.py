"""Database access — aiosqlite for users, messages, rankings.

Provides async database operations for:
- User accounts (auth, profile)
- Messages (inbox, sent)
- Rankings (hall of fame)
- Wonders (world wonder progress)
"""

from __future__ import annotations

import logging
from typing import Any

import aiosqlite

log = logging.getLogger(__name__)

_SCHEMA = """\
CREATE TABLE IF NOT EXISTS empire_stats (
    uid              INTEGER PRIMARY KEY,
    attacks_won_human   INTEGER DEFAULT 0,
    attacks_lost_human  INTEGER DEFAULT 0,
    attacks_won_ai      INTEGER DEFAULT 0,
    attacks_lost_ai     INTEGER DEFAULT 0,
    defense_won_human   INTEGER DEFAULT 0,
    defense_lost_human  INTEGER DEFAULT 0,
    defense_won_ai      INTEGER DEFAULT 0,
    defense_lost_ai     INTEGER DEFAULT 0,
    spies_sent          INTEGER DEFAULT 0,
    towers_sold         INTEGER DEFAULT 0,
    towers_placed       INTEGER DEFAULT 0,
    artifacts_stolen         INTEGER DEFAULT 0,
    longest_battle_ms        INTEGER DEFAULT 0,
    critters_killed          INTEGER DEFAULT 0,
    culture_stolen           REAL    DEFAULT 0,
    research_stolen          REAL    DEFAULT 0,
    culture_won              REAL    DEFAULT 0,
    research_won             REAL    DEFAULT 0,
    defense_gold_earned      REAL    DEFAULT 0,
    first_era_reached        INTEGER DEFAULT 0,
    peak_artifacts_held      INTEGER DEFAULT 0,
    critter_upgrade_levels   INTEGER DEFAULT 0,
    tower_upgrade_levels     INTEGER DEFAULT 0
);
CREATE TABLE IF NOT EXISTS era_firsts (
    era_key     TEXT PRIMARY KEY,
    uid         INTEGER NOT NULL,
    empire_name TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS artifact_holds (
    uid               INTEGER NOT NULL,
    artifact_iid      TEXT NOT NULL,
    acquired_at       REAL,
    total_held_secs   REAL DEFAULT 0,
    PRIMARY KEY (uid, artifact_iid)
);
CREATE TABLE IF NOT EXISTS last_season_artifacts (
    uid          INTEGER NOT NULL,
    artifact_iid TEXT NOT NULL,
    PRIMARY KEY (uid, artifact_iid)
);
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
CREATE TABLE IF NOT EXISTS push_subscriptions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    uid INTEGER NOT NULL,
    endpoint TEXT NOT NULL UNIQUE,
    subscription_json TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS login_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    uid INTEGER NOT NULL,
    ip TEXT NOT NULL DEFAULT '',
    fingerprint TEXT NOT NULL DEFAULT '',
    device_id TEXT NOT NULL DEFAULT '',
    logged_in_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_login_events_uid ON login_events(uid);
CREATE INDEX IF NOT EXISTS ix_login_events_ip  ON login_events(ip);
CREATE INDEX IF NOT EXISTS ix_login_events_fp  ON login_events(fingerprint);
CREATE TABLE IF NOT EXISTS ai_battle_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    bid INTEGER NOT NULL,
    defender_name TEXT NOT NULL,
    defender_era TEXT NOT NULL,
    army_name TEXT NOT NULL,
    result TEXT NOT NULL,
    path_length INTEGER NOT NULL,
    life_start REAL NOT NULL,
    life_end REAL NOT NULL,
    tower_count INTEGER NOT NULL,
    tower_gold REAL NOT NULL,
    towers_by_era TEXT NOT NULL,
    critters_total INTEGER NOT NULL,
    critters_reached INTEGER NOT NULL,
    critters_killed INTEGER NOT NULL,
    critters_by_era TEXT NOT NULL,
    battle_duration_s REAL NOT NULL
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
        # Migrate: add peak_artifacts_held column to empire_stats if missing
        try:
            await self._conn.execute("SELECT peak_artifacts_held FROM empire_stats LIMIT 1")
        except aiosqlite.OperationalError:
            await self._conn.execute(
                "ALTER TABLE empire_stats ADD COLUMN peak_artifacts_held INTEGER DEFAULT 0"
            )
        # Migrate: add critter/tower upgrade level columns to empire_stats if missing
        try:
            await self._conn.execute("SELECT critter_upgrade_levels FROM empire_stats LIMIT 1")
        except aiosqlite.OperationalError:
            await self._conn.execute(
                "ALTER TABLE empire_stats ADD COLUMN critter_upgrade_levels INTEGER DEFAULT 0"
            )
        try:
            await self._conn.execute("SELECT tower_upgrade_levels FROM empire_stats LIMIT 1")
        except aiosqlite.OperationalError:
            await self._conn.execute(
                "ALTER TABLE empire_stats ADD COLUMN tower_upgrade_levels INTEGER DEFAULT 0"
            )
        # Migrate: add last_seen column if missing
        try:
            await self._conn.execute("SELECT last_seen FROM users LIMIT 1")
        except aiosqlite.OperationalError:
            await self._conn.execute("ALTER TABLE users ADD COLUMN last_seen TIMESTAMP")
        # Migrate: add device_id column to login_events if missing
        try:
            await self._conn.execute("SELECT device_id FROM login_events LIMIT 1")
        except aiosqlite.OperationalError:
            await self._conn.execute("ALTER TABLE login_events ADD COLUMN device_id TEXT NOT NULL DEFAULT ''")
        # Index on device_id is created here (not in _SCHEMA) so it runs *after*
        # the migration above adds the column to pre-existing tables.
        await self._conn.execute(
            "CREATE INDEX IF NOT EXISTS ix_login_events_did ON login_events(device_id)"
        )
        await self._conn.commit()
        log.info("Database connected: %s", self._db_path)

    async def close(self) -> None:
        """Close the database connection."""
        if self._conn:
            await self._conn.close()
            self._conn = None

    # -- User operations -------------------------------------------------

    async def get_user_by_uid(self, uid: int) -> dict[str, Any] | None:
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

    async def get_user(self, username: str) -> dict[str, Any] | None:
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
            uid = cursor.lastrowid or 0
        await self._conn.commit()
        log.info("Created user %s (uid=%d)", username, uid)
        return uid

    async def update_password_hash(self, uid: int, password_hash: str) -> None:
        """Update the stored password hash for a user (used for lazy argon2 upgrade)."""
        assert self._conn is not None
        await self._conn.execute(
            "UPDATE users SET password_hash = ? WHERE uid = ?",
            (password_hash, uid),
        )
        await self._conn.commit()

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

    async def rename_empire(self, uid: int, empire_name: str) -> bool:
        """Update the empire_name for a user by uid. Returns True if updated."""
        assert self._conn is not None
        async with self._conn.execute(
            "UPDATE users SET empire_name = ? WHERE uid = ?",
            (empire_name, uid),
        ) as cursor:
            updated = cursor.rowcount > 0
        await self._conn.commit()
        return updated

    async def update_last_seen(self, uid: int) -> None:
        """Update the last_seen timestamp for a user."""
        assert self._conn is not None
        await self._conn.execute(
            "UPDATE users SET last_seen = CURRENT_TIMESTAMP WHERE uid = ?",
            (uid,),
        )
        await self._conn.commit()

    async def list_users(self) -> list[dict[str, Any]]:
        """Return all user accounts (without password hashes)."""
        assert self._conn is not None
        async with self._conn.execute(
            "SELECT uid, username, email, empire_name, created_at, last_seen FROM users ORDER BY created_at ASC, uid ASC",
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

    async def record_login(self, uid: int, ip: str, fingerprint: str, device_id: str = "") -> None:
        """Record a login event with IP, browser fingerprint, and persistent device UUID."""
        assert self._conn is not None
        await self._conn.execute(
            "INSERT INTO login_events (uid, ip, fingerprint, device_id) VALUES (?, ?, ?, ?)",
            (uid, ip or '', fingerprint or '', device_id or ''),
        )
        await self._conn.commit()

    async def get_device_clusters(self) -> list[dict[str, Any]]:
        """Return pairs of UIDs that share device signals, with a risk score.

        Score weights:
          +70  shared device_id (localStorage UUID — strong signal)
          +55  shared fingerprint (canvas+hardware hash — strong signal)
          +30  shared IP, recent (within 30 days)
          +15  shared IP, older
        Max score is capped at 100. Pairs with score < 15 are excluded.
        """
        assert self._conn is not None
        sql = """
        SELECT
            a.uid AS uid_a,
            b.uid AS uid_b,
            GROUP_CONCAT(DISTINCT CASE WHEN a.ip != '' AND a.ip = b.ip THEN a.ip END)
                AS shared_ips,
            GROUP_CONCAT(DISTINCT CASE WHEN a.fingerprint != '' AND a.fingerprint = b.fingerprint THEN a.fingerprint END)
                AS shared_fps,
            GROUP_CONCAT(DISTINCT CASE WHEN a.device_id != '' AND a.device_id = b.device_id THEN a.device_id END)
                AS shared_dids,
            MAX(CASE WHEN a.device_id != '' AND a.device_id = b.device_id THEN 1 ELSE 0 END)
                AS has_did,
            MAX(CASE WHEN a.fingerprint != '' AND a.fingerprint = b.fingerprint THEN 1 ELSE 0 END)
                AS has_fp,
            MAX(CASE WHEN a.ip != '' AND a.ip = b.ip
                          AND a.logged_in_at >= datetime('now', '-30 days')
                          AND b.logged_in_at >= datetime('now', '-30 days') THEN 1 ELSE 0 END)
                AS has_recent_ip,
            MAX(CASE WHEN a.ip != '' AND a.ip = b.ip
                          AND NOT (a.logged_in_at >= datetime('now', '-30 days')
                               AND b.logged_in_at >= datetime('now', '-30 days')) THEN 1 ELSE 0 END)
                AS has_old_ip
        FROM login_events a
        JOIN login_events b
            ON (a.ip = b.ip OR a.fingerprint = b.fingerprint OR a.device_id = b.device_id)
            AND a.uid < b.uid
        WHERE a.device_id != '' OR a.fingerprint != '' OR a.ip != ''
        GROUP BY a.uid, b.uid
        """
        async with self._conn.execute(sql) as cursor:
            rows = await cursor.fetchall()
        results = []
        for r in rows:
            score = min(100,
                int(r[5]) * 70 +   # shared device_id
                int(r[6]) * 55 +   # shared fingerprint
                int(r[7]) * 30 +   # shared recent IP
                int(r[8]) * 15     # shared old IP
            )
            if score < 15:
                continue
            results.append({
                "uid_a": r[0],
                "uid_b": r[1],
                "shared_ips": r[2] or "",
                "shared_fps": r[3] or "",
                "shared_dids": r[4] or "",
                "score": score,
            })
        results.sort(key=lambda x: x["score"], reverse=True)
        return results


    # -- Message operations ----------------------------------------------

    async def send_message(self, from_uid: int, to_uid: int, body: str) -> dict[str, Any]:
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

    async def get_inbox(self, uid: int) -> list[dict[str, Any]]:
        """Return all messages received by uid, newest first."""
        assert self._conn is not None
        async with self._conn.execute(
            "SELECT id, from_uid, to_uid, body, sent_at, read FROM messages WHERE to_uid = ? ORDER BY id DESC",
            (uid,),
        ) as cursor:
            rows = await cursor.fetchall()
        return [self._msg_row_to_dict(r) for r in rows]

    async def get_sent(self, uid: int) -> list[dict[str, Any]]:
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

    async def get_global(self, limit: int = 200) -> list[dict[str, Any]]:
        """Return global chat messages (to_uid=0, from real players), oldest first."""
        assert self._conn is not None
        async with self._conn.execute(
            "SELECT id, from_uid, to_uid, body, sent_at, read FROM messages "
            "WHERE to_uid = 0 AND from_uid != 0 ORDER BY id DESC LIMIT ?",
            (limit,),
        ) as cursor:
            rows = await cursor.fetchall()
        return list(reversed([self._msg_row_to_dict(r) for r in rows]))

    async def get_private_for(self, uid: int) -> list[dict[str, Any]]:
        """Return private messages where uid is sender or receiver (no global, no battle reports)."""
        assert self._conn is not None
        async with self._conn.execute(
            "SELECT id, from_uid, to_uid, body, sent_at, read FROM messages "
            "WHERE (to_uid = ? OR from_uid = ?) AND to_uid != 0 AND from_uid != 0 ORDER BY id DESC",
            (uid, uid),
        ) as cursor:
            rows = await cursor.fetchall()
        return [self._msg_row_to_dict(r) for r in rows]

    async def get_battle_reports_for(self, uid: int) -> list[dict[str, Any]]:
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
            except (ValueError, UnicodeDecodeError):
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

    def _msg_row_to_dict(self, row: Any) -> dict[str, Any]:
        return {
            "id": row[0],
            "from_uid": row[1],
            "to_uid": row[2],
            "body": row[3],
            "sent_at": (str(row[4]).rstrip("Z") + "Z") if row[4] else "",
            "read": bool(row[5]),
        }

    # -- Ranking operations ----------------------------------------------

    async def update_ranking(self, uid: int, tai: float) -> None:
        """Update a player's ranking score."""
        # TODO: implement
        pass

    async def get_rankings(self, limit: int = 20) -> list[dict[str, Any]]:
        """Get top rankings."""
        # TODO: implement
        return []

    # -- Push subscription operations ------------------------------------

    async def save_push_subscription(self, uid: int, subscription: dict[str, Any]) -> None:
        assert self._conn is not None
        import json
        endpoint = subscription.get("endpoint", "")
        await self._conn.execute(
            "INSERT INTO push_subscriptions (uid, endpoint, subscription_json) VALUES (?, ?, ?)"
            " ON CONFLICT(endpoint) DO UPDATE SET uid=excluded.uid, subscription_json=excluded.subscription_json",
            (uid, endpoint, json.dumps(subscription)),
        )
        await self._conn.commit()

    async def delete_push_subscription(self, uid: int, endpoint: str) -> None:
        assert self._conn is not None
        await self._conn.execute(
            "DELETE FROM push_subscriptions WHERE uid=? AND endpoint=?", (uid, endpoint)
        )
        await self._conn.commit()

    async def get_push_subscriptions(self, uid: int) -> list[dict[str, Any]]:
        assert self._conn is not None
        import json
        async with self._conn.execute(
            "SELECT subscription_json FROM push_subscriptions WHERE uid=?", (uid,)
        ) as cur:
            rows = await cur.fetchall()
        return [json.loads(r[0]) for r in rows]

    async def insert_ai_battle_log(
        self,
        bid: int,
        defender_name: str,
        defender_era: str,
        army_name: str,
        result: str,
        path_length: int,
        life_start: float,
        life_end: float,
        tower_count: int,
        tower_gold: float,
        towers_by_era: str,
        critters_total: int,
        critters_reached: int,
        critters_killed: int,
        critters_by_era: str,
        battle_duration_s: float,
    ) -> None:
        assert self._conn is not None
        await self._conn.execute(
            """INSERT INTO ai_battle_log (
                bid, defender_name, defender_era, army_name, result,
                path_length, life_start, life_end,
                tower_count, tower_gold, towers_by_era,
                critters_total, critters_reached, critters_killed, critters_by_era,
                battle_duration_s
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                bid, defender_name, defender_era, army_name, result,
                path_length, life_start, life_end,
                tower_count, tower_gold, towers_by_era,
                critters_total, critters_reached, critters_killed, critters_by_era,
                battle_duration_s,
            ),
        )
        await self._conn.commit()

    # -- Empire stats --------------------------------------------------------

    async def record_empire_stat(self, uid: int, **increments: int) -> None:
        """Upsert empire_stats row, incrementing the given counters."""
        assert self._conn is not None
        try:
            cols = ", ".join(increments.keys())
            placeholders = ", ".join("?" for _ in increments)
            updates = ", ".join(f"{k} = {k} + ?" for k in increments)
            await self._conn.execute(
                f"INSERT INTO empire_stats (uid, {cols}) VALUES (?, {placeholders})"
                f" ON CONFLICT(uid) DO UPDATE SET {updates}",
                (uid, *increments.values(), *increments.values()),
            )
            await self._conn.commit()
        except Exception:
            log.warning("record_empire_stat failed uid=%d", uid, exc_info=True)

    async def record_empire_stat_float(self, uid: int, field: str, value: float) -> None:
        """Upsert empire_stats row, adding a float value to the given field."""
        assert self._conn is not None
        try:
            await self._conn.execute(
                f"INSERT INTO empire_stats (uid, {field}) VALUES (?, ?)"
                f" ON CONFLICT(uid) DO UPDATE SET {field} = {field} + excluded.{field}",
                (uid, value),
            )
            await self._conn.commit()
        except Exception:
            log.warning("record_empire_stat_float failed uid=%d field=%s", uid, field, exc_info=True)

    async def record_empire_stat_max(self, uid: int, field: str, value: int) -> None:
        """Update field only if value > current."""
        assert self._conn is not None
        try:
            await self._conn.execute(
                f"INSERT INTO empire_stats (uid, {field}) VALUES (?, ?)"
                f" ON CONFLICT(uid) DO UPDATE SET {field} = MAX({field}, excluded.{field})",
                (uid, value),
            )
            await self._conn.commit()
        except Exception:
            log.warning("record_empire_stat_max failed uid=%d field=%s", uid, field, exc_info=True)

    async def record_artifact_acquired(self, uid: int, artifact_iid: str, ts: float) -> None:
        """Upsert artifact_holds row, setting acquired_at = ts, and update peak_artifacts_held."""
        assert self._conn is not None
        try:
            await self._conn.execute(
                "INSERT INTO artifact_holds (uid, artifact_iid, acquired_at) VALUES (?, ?, ?)"
                " ON CONFLICT(uid, artifact_iid) DO UPDATE SET acquired_at = excluded.acquired_at",
                (uid, artifact_iid, ts),
            )
            # Count how many artifacts this empire currently holds (acquired_at IS NOT NULL)
            async with self._conn.execute(
                "SELECT COUNT(*) FROM artifact_holds WHERE uid = ? AND acquired_at IS NOT NULL",
                (uid,),
            ) as cur:
                row = await cur.fetchone()
            current_count = row[0] if row else 1
            # Update peak if current count exceeds previous peak
            await self._conn.execute(
                "INSERT INTO empire_stats (uid, peak_artifacts_held) VALUES (?, ?)"
                " ON CONFLICT(uid) DO UPDATE SET"
                " peak_artifacts_held = MAX(peak_artifacts_held, excluded.peak_artifacts_held)",
                (uid, current_count),
            )
            await self._conn.commit()
        except Exception:
            log.warning("record_artifact_acquired failed uid=%d iid=%s", uid, artifact_iid, exc_info=True)

    async def record_artifact_lost(self, uid: int, artifact_iid: str, ts: float) -> None:
        """Accumulate hold duration into total_held_secs and clear acquired_at."""
        assert self._conn is not None
        try:
            async with self._conn.execute(
                "SELECT acquired_at FROM artifact_holds WHERE uid = ? AND artifact_iid = ?",
                (uid, artifact_iid),
            ) as cur:
                row = await cur.fetchone()
            if row and row[0] is not None:
                delta = max(0.0, ts - row[0])
                await self._conn.execute(
                    "UPDATE artifact_holds SET total_held_secs = total_held_secs + ?, acquired_at = NULL"
                    " WHERE uid = ? AND artifact_iid = ?",
                    (delta, uid, artifact_iid),
                )
                await self._conn.commit()
        except Exception:
            log.warning("record_artifact_lost failed uid=%d iid=%s", uid, artifact_iid, exc_info=True)

    async def get_empire_stats(self, uid: int) -> dict[str, Any] | None:
        assert self._conn is not None
        async with self._conn.execute(
            "SELECT * FROM empire_stats WHERE uid = ?", (uid,)
        ) as cur:
            row = await cur.fetchone()
            return dict(row) if row else None

    async def get_all_empire_stats(self) -> list[dict[str, Any]]:
        assert self._conn is not None
        async with self._conn.execute("SELECT * FROM empire_stats") as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]

    async def get_artifact_hold_totals(self) -> list[dict[str, Any]]:
        """Return (uid, artifact_iid, held_secs) including ongoing holds."""
        assert self._conn is not None
        async with self._conn.execute(
            "SELECT uid, artifact_iid,"
            " total_held_secs + CASE WHEN acquired_at IS NOT NULL"
            " THEN (unixepoch() - acquired_at) ELSE 0 END AS held_secs"
            " FROM artifact_holds"
        ) as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]

    async def get_longest_artifact_hold_per_uid(self) -> list[dict[str, Any]]:
        """Return the longest single-artifact hold duration per uid."""
        assert self._conn is not None
        async with self._conn.execute(
            "SELECT uid, MAX("
            "  total_held_secs + CASE WHEN acquired_at IS NOT NULL"
            "  THEN (unixepoch() - acquired_at) ELSE 0 END"
            ") AS longest_hold_secs"
            " FROM artifact_holds GROUP BY uid"
        ) as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]

    async def record_era_first(self, era_key: str, uid: int, empire_name: str) -> None:
        """Record which empire was the first to reach a given era."""
        assert self._conn is not None
        try:
            await self._conn.execute(
                "INSERT OR IGNORE INTO era_firsts (era_key, uid, empire_name) VALUES (?, ?, ?)",
                (era_key, uid, empire_name),
            )
            await self._conn.commit()
        except Exception:
            log.warning("record_era_first failed era=%s uid=%d", era_key, uid, exc_info=True)

    async def get_era_firsts(self) -> list[dict[str, Any]]:
        """Return all era_firsts rows ordered by ERA_ORDER."""
        assert self._conn is not None
        async with self._conn.execute("SELECT era_key, uid, empire_name FROM era_firsts") as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]

    async def save_last_season_artifacts(self, uid_to_artifacts: dict[int, list[str]]) -> None:
        """Replace last_season_artifacts with the current season's end-state artifacts."""
        assert self._conn is not None
        await self._conn.execute("DELETE FROM last_season_artifacts")
        for uid, iids in uid_to_artifacts.items():
            for iid in iids:
                await self._conn.execute(
                    "INSERT OR IGNORE INTO last_season_artifacts (uid, artifact_iid) VALUES (?, ?)",
                    (uid, iid),
                )
        await self._conn.commit()

    async def get_last_season_artifacts(self, uid: int) -> list[str]:
        """Return artifact IIDs this user held at the end of the previous season."""
        assert self._conn is not None
        async with self._conn.execute(
            "SELECT artifact_iid FROM last_season_artifacts WHERE uid = ?", (uid,)
        ) as cur:
            rows = await cur.fetchall()
            return [r["artifact_iid"] for r in rows]

    async def wipe_season_stats(self) -> None:
        """Delete all per-season runtime stats (empire_stats, era_firsts, artifact_holds).
        User accounts are preserved."""
        assert self._conn is not None
        await self._conn.execute("DELETE FROM empire_stats")
        await self._conn.execute("DELETE FROM era_firsts")
        await self._conn.execute("DELETE FROM artifact_holds")
        await self._conn.commit()
        log.info("Season stats wiped (empire_stats, era_firsts, artifact_holds)")
