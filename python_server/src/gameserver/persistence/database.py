"""Database access — aiosqlite for users, messages, rankings.

Provides async database operations for:
- User accounts (auth, profile)
- Messages (inbox, sent)
- Rankings (hall of fame)
- Wonders (world wonder progress)
"""

from __future__ import annotations

import json
import logging
from typing import Any

import aiosqlite

log = logging.getLogger(__name__)

SPY_REPORT_MAX_AGE_DAYS = 3

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
    tower_upgrade_levels     INTEGER DEFAULT 0,
    coward_attacks                    INTEGER DEFAULT 0,
    max_lucky_punch_levels            INTEGER DEFAULT 0,
    max_artifacts_stolen_one_battle   INTEGER DEFAULT 0,
    max_artifacts_lost_one_battle     INTEGER DEFAULT 0,
    one_hp_def_wins                   INTEGER DEFAULT 0,
    peak_incoming_attacks             INTEGER DEFAULT 0,
    peak_incoming                     INTEGER DEFAULT 0
);
CREATE TABLE IF NOT EXISTS era_firsts (
    era_key     TEXT PRIMARY KEY,
    uid         INTEGER NOT NULL,
    empire_name TEXT NOT NULL DEFAULT '',
    reached_at  INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS attacker_win_log (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    attacker_uid  INTEGER NOT NULL,
    defender_uid  INTEGER NOT NULL,
    ts            INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_attacker_win_log_pair ON attacker_win_log(attacker_uid, defender_uid, ts);
CREATE TABLE IF NOT EXISTS artifact_holds (
    uid               INTEGER NOT NULL,
    artifact_iid      TEXT NOT NULL,
    acquired_at       REAL,
    total_held_secs   REAL DEFAULT 0,
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
CREATE TABLE IF NOT EXISTS bot_signals (
    uid                 INTEGER PRIMARY KEY,
    reaction_times_json TEXT    NOT NULL DEFAULT '[]',
    header_bot_score    REAL    NOT NULL DEFAULT -1.0,
    bot_probability     REAL    NOT NULL DEFAULT 0.5,
    user_agent          TEXT    NOT NULL DEFAULT '',
    updated_at          TEXT    NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS player_trophies (
    uid         INTEGER NOT NULL,
    iid         TEXT    NOT NULL,
    earned_at   INTEGER NOT NULL,
    PRIMARY KEY (uid, iid)
);
CREATE TABLE IF NOT EXISTS password_resets (
    token       TEXT PRIMARY KEY,
    uid         INTEGER NOT NULL,
    expires_at  INTEGER NOT NULL,
    used        INTEGER NOT NULL DEFAULT 0,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_password_resets_uid ON password_resets(uid);
-- skip_siege_log is superseded by the generic event_window_log below
-- (kind="skip_siege") and is no longer written to. Left in place unused —
-- this codebase has no destructive-migration precedent (only additive
-- CREATE TABLE IF NOT EXISTS / ALTER TABLE ADD COLUMN), and the data was a
-- rolling 48h-pruned window anyway, so there is nothing worth migrating.
CREATE TABLE IF NOT EXISTS skip_siege_log (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    defender_uid            INTEGER NOT NULL,
    attacker_uid            INTEGER NOT NULL,
    attack_id               INTEGER NOT NULL,
    siege_remaining_at_skip REAL NOT NULL,
    ts                      INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_skip_siege_log_defender ON skip_siege_log(defender_uid, ts);
CREATE TABLE IF NOT EXISTS event_window_log (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    kind        TEXT    NOT NULL,
    key_uid     INTEGER NOT NULL,
    ref_id      INTEGER,
    magnitude   REAL,
    ts          INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_event_window_log_kind_key ON event_window_log(kind, key_uid, ts);
CREATE TABLE IF NOT EXISTS spy_reports (
    attacker_uid   INTEGER NOT NULL,
    defender_uid   INTEGER NOT NULL,
    defender_name  TEXT    NOT NULL DEFAULT '',
    report_json    TEXT    NOT NULL DEFAULT '{}',
    created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (attacker_uid, defender_uid)
);
CREATE TABLE IF NOT EXISTS alliance_declarations (
    from_uid    INTEGER NOT NULL,
    to_uid      INTEGER NOT NULL,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (from_uid, to_uid)
);
CREATE INDEX IF NOT EXISTS ix_alliance_declarations_to ON alliance_declarations(to_uid);
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
        # Migrate: add season column to player_trophies if missing
        try:
            await self._conn.execute("SELECT season FROM player_trophies LIMIT 1")
        except aiosqlite.OperationalError:
            await self._conn.execute(
                "ALTER TABLE player_trophies ADD COLUMN season INTEGER NOT NULL DEFAULT 1"
            )
        # Migrate: add new empire_stats columns for era-comparison and multi-artifact trophies
        for _col, _type in [
            ("coward_attacks", "INTEGER DEFAULT 0"),
            ("max_lucky_punch_levels", "INTEGER DEFAULT 0"),
            ("max_artifacts_stolen_one_battle", "INTEGER DEFAULT 0"),
            ("max_artifacts_lost_one_battle", "INTEGER DEFAULT 0"),
            ("one_hp_def_wins", "INTEGER DEFAULT 0"),
            ("peak_incoming_attacks", "INTEGER DEFAULT 0"),
            ("peak_incoming", "INTEGER DEFAULT 0"),
        ]:
            try:
                await self._conn.execute(f"SELECT {_col} FROM empire_stats LIMIT 1")
            except aiosqlite.OperationalError:
                await self._conn.execute(
                    f"ALTER TABLE empire_stats ADD COLUMN {_col} {_type}"
                )
        try:
            await self._conn.execute("SELECT peak_army_cost FROM empire_stats LIMIT 1")
        except aiosqlite.OperationalError:
            await self._conn.execute(
                "ALTER TABLE empire_stats ADD COLUMN peak_army_cost REAL DEFAULT 0"
            )
        # Migrate: add reached_at column to era_firsts if missing
        try:
            await self._conn.execute("SELECT reached_at FROM era_firsts LIMIT 1")
        except aiosqlite.OperationalError:
            await self._conn.execute(
                "ALTER TABLE era_firsts ADD COLUMN reached_at INTEGER NOT NULL DEFAULT 0"
            )
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
            "SELECT uid, username, password_hash, email, empire_name FROM users WHERE uid = ?",
            (uid,),
        ) as cursor:
            row = await cursor.fetchone()
            if row is None:
                return None
            return {"uid": row[0], "username": row[1], "password_hash": row[2],
                    "email": row[3], "empire_name": row[4]}

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

    async def update_email(self, uid: int, email: str) -> None:
        """Update the stored email for a user."""
        assert self._conn is not None
        await self._conn.execute(
            "UPDATE users SET email = ? WHERE uid = ?",
            (email, uid),
        )
        await self._conn.commit()

    async def get_user_by_email(self, email: str) -> dict[str, Any] | None:
        """Look up a user by email (exact match, empty emails never match)."""
        assert self._conn is not None
        async with self._conn.execute(
            "SELECT uid, username, email, empire_name FROM users "
            "WHERE email = ? AND email != '' LIMIT 1",
            (email,),
        ) as cursor:
            row = await cursor.fetchone()
            if row is None:
                return None
            return {"uid": row[0], "username": row[1], "email": row[2], "empire_name": row[3]}

    async def create_password_reset(self, token: str, uid: int, expires_at: int) -> None:
        """Store a password reset token."""
        assert self._conn is not None
        await self._conn.execute(
            "INSERT INTO password_resets (token, uid, expires_at) VALUES (?, ?, ?)",
            (token, uid, expires_at),
        )
        await self._conn.commit()

    async def get_password_reset(self, token: str) -> dict[str, Any] | None:
        """Look up a password reset token."""
        assert self._conn is not None
        async with self._conn.execute(
            "SELECT token, uid, expires_at, used FROM password_resets WHERE token = ?",
            (token,),
        ) as cursor:
            row = await cursor.fetchone()
            if row is None:
                return None
            return {"token": row[0], "uid": row[1], "expires_at": row[2], "used": row[3]}

    async def mark_password_reset_used(self, token: str) -> None:
        """Mark a password reset token as used."""
        assert self._conn is not None
        await self._conn.execute(
            "UPDATE password_resets SET used = 1 WHERE token = ?",
            (token,),
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

    # -- Bot detection signals -------------------------------------------

    async def upsert_bot_signal(
        self,
        uid: int,
        reaction_times_json: str,
        header_bot_score: float,
        bot_probability: float,
        user_agent: str,
    ) -> None:
        """Insert or update bot detection signals for a user."""
        assert self._conn is not None
        await self._conn.execute(
            """INSERT INTO bot_signals
               (uid, reaction_times_json, header_bot_score, bot_probability, user_agent, updated_at)
               VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
               ON CONFLICT(uid) DO UPDATE SET
                 reaction_times_json = excluded.reaction_times_json,
                 header_bot_score    = excluded.header_bot_score,
                 bot_probability     = excluded.bot_probability,
                 user_agent          = excluded.user_agent,
                 updated_at          = excluded.updated_at""",
            (uid, reaction_times_json, header_bot_score, bot_probability, user_agent),
        )
        await self._conn.commit()

    async def list_bot_signals(self) -> list[dict[str, Any]]:
        """Return all stored bot signals."""
        assert self._conn is not None
        async with self._conn.execute(
            "SELECT uid, reaction_times_json, header_bot_score, bot_probability, user_agent FROM bot_signals"
        ) as cursor:
            rows = await cursor.fetchall()
            return [
                {
                    "uid": r[0],
                    "reaction_times_json": r[1],
                    "header_bot_score": r[2],
                    "bot_probability": r[3],
                    "user_agent": r[4],
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

    # Groups sharing a single IP/fingerprint/device_id larger than this are
    # skipped entirely — almost certainly a NAT/shared-WiFi/proxy IP rather
    # than a real multi-account signal, and without this guard a single huge
    # group turns the O(group_size^2) pairing below into a hang (this is
    # exactly what caused the game-freezing lifelock this replaces: the old
    # SQL used a self-join with an OR across three columns, which forced
    # SQLite into an unindexable O(n^2) scan across the entire login_events
    # table — 295k+ rows in prod, effectively unbounded runtime on the single
    # asyncio event loop thread).
    _DEVICE_CLUSTER_MAX_GROUP_SIZE = 50

    async def _device_cluster_pairs_for_column(
        self, column: str, recent_only: bool = False,
    ) -> dict[tuple[int, int], set[str]]:
        """Group login_events by one signal column and return, for every
        pair of uids that share a value, the set of shared values.

        Linear in the number of login_events rows (one query, one pass in
        Python) — no self-join, no per-row cross product across columns.
        """
        assert self._conn is not None
        if recent_only:
            sql = (
                f"SELECT {column}, uid FROM login_events"
                f" WHERE {column} != '' AND logged_in_at >= datetime('now', '-30 days')"
            )
        else:
            sql = f"SELECT {column}, uid FROM login_events WHERE {column} != ''"
        groups: dict[str, set[int]] = {}
        async with self._conn.execute(sql) as cursor:
            async for value, uid in cursor:
                groups.setdefault(value, set()).add(uid)

        pairs: dict[tuple[int, int], set[str]] = {}
        for value, uids in groups.items():
            if len(uids) < 2 or len(uids) > self._DEVICE_CLUSTER_MAX_GROUP_SIZE:
                continue
            sorted_uids = sorted(uids)
            for i in range(len(sorted_uids)):
                for j in range(i + 1, len(sorted_uids)):
                    key = (sorted_uids[i], sorted_uids[j])
                    pairs.setdefault(key, set()).add(value)
        return pairs

    async def get_device_clusters(self) -> list[dict[str, Any]]:
        """Return pairs of UIDs that share device signals, with a risk score.

        Score weights:
          +70  shared device_id (localStorage UUID — strong signal)
          +55  shared fingerprint (canvas+hardware hash — strong signal)
          +30  shared IP, recent (within 30 days)
          +15  shared IP, older
        Max score is capped at 100. Pairs with score < 15 are excluded.
        """
        did_pairs = await self._device_cluster_pairs_for_column("device_id")
        fp_pairs = await self._device_cluster_pairs_for_column("fingerprint")
        ip_recent_pairs = await self._device_cluster_pairs_for_column("ip", recent_only=True)
        ip_all_pairs = await self._device_cluster_pairs_for_column("ip", recent_only=False)
        ip_old_pairs = {k: v for k, v in ip_all_pairs.items() if k not in ip_recent_pairs}

        all_keys = set(did_pairs) | set(fp_pairs) | set(ip_recent_pairs) | set(ip_old_pairs)
        results: list[dict[str, Any]] = []
        for uid_a, uid_b in all_keys:
            score = min(100,
                (70 if (uid_a, uid_b) in did_pairs else 0) +
                (55 if (uid_a, uid_b) in fp_pairs else 0) +
                (30 if (uid_a, uid_b) in ip_recent_pairs else 0) +
                (15 if (uid_a, uid_b) in ip_old_pairs else 0)
            )
            if score < 15:
                continue
            shared_ips = ip_recent_pairs.get((uid_a, uid_b), set()) | ip_old_pairs.get((uid_a, uid_b), set())
            results.append({
                "uid_a": uid_a,
                "uid_b": uid_b,
                "shared_ips": ",".join(sorted(shared_ips)),
                "shared_fps": ",".join(sorted(fp_pairs.get((uid_a, uid_b), set()))),
                "shared_dids": ",".join(sorted(did_pairs.get((uid_a, uid_b), set()))),
                "score": score,
            })
        results.sort(key=lambda x: x["score"], reverse=True)
        return results


    # -- Message operations ----------------------------------------------

    async def send_message(self, from_uid: int, to_uid: int, body: str) -> dict[str, Any]:
        """Store a new message and return it as a dict."""
        assert self._conn is not None
        read = 0
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

    async def get_attacker_win_messages(self, since_iso: str) -> list[dict[str, Any]]:
        """Return {to_uid, body, sent_at} for system "You Won!" attacker battle
        reports sent at/after since_iso.

        Used to backfill attacker_win_log (anti-farming protection) from
        message history, so already-repeated attacks aren't forgotten just
        because the feature launched mid-stream.
        """
        assert self._conn is not None
        async with self._conn.execute(
            "SELECT to_uid, body, sent_at FROM messages"
            " WHERE from_uid = 0 AND sent_at >= ? AND body LIKE '⚔ You Won!%'"
            " ORDER BY sent_at",
            (since_iso,),
        ) as cursor:
            rows = await cursor.fetchall()
        return [{"to_uid": r[0], "body": r[1], "sent_at": r[2]} for r in rows]

    async def get_active_anti_farm_pairs(
        self, since_ts: int, threshold: int,
    ) -> list[dict[str, Any]]:
        """Return {attacker_uid, defender_uid, win_count, last_win_ts} for every
        (attacker, defender) pair currently at/over the anti-farm win threshold
        within the trailing window — i.e. protection is active for that pair.
        """
        assert self._conn is not None
        async with self._conn.execute(
            "SELECT attacker_uid, defender_uid, COUNT(*) AS win_count, MAX(ts) AS last_win_ts"
            " FROM attacker_win_log WHERE ts >= ?"
            " GROUP BY attacker_uid, defender_uid"
            " HAVING win_count >= ?"
            " ORDER BY win_count DESC",
            (since_ts, threshold),
        ) as cursor:
            rows = await cursor.fetchall()
        return [
            {"attacker_uid": r[0], "defender_uid": r[1], "win_count": r[2], "last_win_ts": r[3]}
            for r in rows
        ]

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

    # -- Spy report operations --------------------------------------------

    async def save_spy_report(
        self, attacker_uid: int, defender_uid: int, defender_name: str, report_data: dict[str, Any],
    ) -> None:
        """Upsert the latest spy report for this (attacker, defender) pair."""
        assert self._conn is not None
        await self._conn.execute(
            "INSERT INTO spy_reports (attacker_uid, defender_uid, defender_name, report_json, created_at)"
            " VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)"
            " ON CONFLICT(attacker_uid, defender_uid) DO UPDATE SET"
            " defender_name = excluded.defender_name,"
            " report_json = excluded.report_json,"
            " created_at = excluded.created_at",
            (attacker_uid, defender_uid, defender_name, json.dumps(report_data)),
        )
        await self._conn.commit()

    async def get_spy_reports_for(self, attacker_uid: int) -> list[dict[str, Any]]:
        """Return latest-per-target spy reports sent by attacker_uid within
        SPY_REPORT_MAX_AGE_DAYS, newest first. Older reports are hidden."""
        assert self._conn is not None
        async with self._conn.execute(
            "SELECT defender_uid, defender_name, report_json, created_at FROM spy_reports"
            " WHERE attacker_uid = ? AND created_at >= datetime('now', ?) ORDER BY created_at DESC",
            (attacker_uid, f"-{SPY_REPORT_MAX_AGE_DAYS} days"),
        ) as cursor:
            rows = await cursor.fetchall()
        out = []
        for r in rows:
            data = json.loads(r["report_json"])
            out.append({
                "defender_uid": r["defender_uid"],
                "defender_name": r["defender_name"],
                "created_at": r["created_at"],
                **data,
            })
        return out

    # -- Alliance/diplomacy operations -------------------------------------

    async def toggle_alliance_declaration(self, from_uid: int, to_uid: int) -> bool:
        """Toggle from_uid's declaration toward to_uid: insert if absent, delete if present.

        Returns True if a declaration now exists (inserted), False if it was removed (deleted).
        """
        assert self._conn is not None
        async with self._conn.execute(
            "SELECT 1 FROM alliance_declarations WHERE from_uid = ? AND to_uid = ?",
            (from_uid, to_uid),
        ) as cursor:
            exists = await cursor.fetchone() is not None
        if exists:
            await self._conn.execute(
                "DELETE FROM alliance_declarations WHERE from_uid = ? AND to_uid = ?",
                (from_uid, to_uid),
            )
        else:
            await self._conn.execute(
                "INSERT INTO alliance_declarations (from_uid, to_uid, created_at)"
                " VALUES (?, ?, CURRENT_TIMESTAMP)",
                (from_uid, to_uid),
            )
        await self._conn.commit()
        return not exists

    async def remove_alliance_declaration(self, from_uid: int, to_uid: int) -> bool:
        """Delete a specific one-directional alliance declaration, if present.

        Unlike toggle_alliance_declaration, this never inserts — used to
        decline an incoming request (from_uid's declaration toward to_uid)
        without touching to_uid's own outgoing declarations.

        Returns True if a row was removed.
        """
        assert self._conn is not None
        cursor = await self._conn.execute(
            "DELETE FROM alliance_declarations WHERE from_uid = ? AND to_uid = ?",
            (from_uid, to_uid),
        )
        await self._conn.commit()
        return cursor.rowcount > 0

    async def clear_all_alliance_declarations(self) -> int:
        """Delete every alliance declaration. Returns the number of rows removed.

        Used at startup when a season runs with alliances disabled: unlike the
        per-season stat wipe, declarations otherwise survive an empire wipe and
        would carry teams from the previous season into the new one.
        """
        assert self._conn is not None
        cursor = await self._conn.execute("DELETE FROM alliance_declarations")
        await self._conn.commit()
        return int(cursor.rowcount or 0)

    async def get_alliance_declarations_for(self, uid: int) -> tuple[set[int], set[int]]:
        """Return (declared_to, declared_by) uid sets for uid's alliance declarations."""
        assert self._conn is not None
        async with self._conn.execute(
            "SELECT to_uid FROM alliance_declarations WHERE from_uid = ?", (uid,)
        ) as cursor:
            declared_to = {r["to_uid"] for r in await cursor.fetchall()}
        async with self._conn.execute(
            "SELECT from_uid FROM alliance_declarations WHERE to_uid = ?", (uid,)
        ) as cursor:
            declared_by = {r["from_uid"] for r in await cursor.fetchall()}
        return declared_to, declared_by

    async def get_all_mutual_alliances(self) -> dict[int, set[int]]:
        """Return {uid: {allied_uid, ...}} for every uid with at least one mutual (two-way) declaration."""
        assert self._conn is not None
        async with self._conn.execute("SELECT from_uid, to_uid FROM alliance_declarations") as cursor:
            pairs = {(r["from_uid"], r["to_uid"]) for r in await cursor.fetchall()}
        mutual: dict[int, set[int]] = {}
        for from_uid, to_uid in pairs:
            if (to_uid, from_uid) in pairs:
                mutual.setdefault(from_uid, set()).add(to_uid)
                mutual.setdefault(to_uid, set()).add(from_uid)
        return mutual

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

    async def record_empire_stat_max(self, uid: int, field: str, value: int | float) -> None:
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

    async def record_empire_stat_min(self, uid: int, field: str, value: float) -> None:
        """Update field only if value < current."""
        assert self._conn is not None
        try:
            await self._conn.execute(
                f"INSERT INTO empire_stats (uid, {field}) VALUES (?, ?)"
                f" ON CONFLICT(uid) DO UPDATE SET {field} = MIN({field}, excluded.{field})",
                (uid, value),
            )
            await self._conn.commit()
        except Exception:
            log.warning("record_empire_stat_min failed uid=%d field=%s", uid, field, exc_info=True)

    async def record_artifact_acquired(self, uid: int, artifact_iid: str, ts: float) -> None:
        """Upsert artifact_holds row, setting acquired_at = ts.

        peak_artifacts_held is recorded separately by the caller from the
        empire's in-memory artifact list: artifact_holds has one row per
        (uid, iid) and would undercount an empire holding duplicates.
        """
        assert self._conn is not None
        try:
            await self._conn.execute(
                "INSERT INTO artifact_holds (uid, artifact_iid, acquired_at) VALUES (?, ?, ?)"
                " ON CONFLICT(uid, artifact_iid) DO UPDATE SET acquired_at = excluded.acquired_at",
                (uid, artifact_iid, ts),
            )
            await self._conn.commit()
        except Exception:
            log.warning("record_artifact_acquired failed uid=%d iid=%s", uid, artifact_iid, exc_info=True)

    async def count_recent_attacker_wins(
        self, attacker_uid: int, defender_uid: int, since_ts: int,
    ) -> int:
        """Count attacker_uid's wins against defender_uid at/after since_ts.

        Used by the anti-farming protection to decide, once at battle
        creation, whether this attacker has already beaten this defender too
        often within the rolling window.
        """
        assert self._conn is not None
        async with self._conn.execute(
            "SELECT COUNT(*) FROM attacker_win_log WHERE attacker_uid = ? AND defender_uid = ? AND ts >= ?",
            (attacker_uid, defender_uid, since_ts),
        ) as cur:
            row = await cur.fetchone()
        return row[0] if row else 0

    async def record_attacker_win(self, attacker_uid: int, defender_uid: int, ts: int) -> None:
        """Record a PvP win for the anti-farming rolling-window count.

        Also prunes this pair's rows older than 48h (well past the anti-farm
        window) so the table can't grow unbounded.
        """
        assert self._conn is not None
        try:
            await self._conn.execute(
                "DELETE FROM attacker_win_log WHERE attacker_uid = ? AND defender_uid = ? AND ts < ?",
                (attacker_uid, defender_uid, ts - 172800),
            )
            await self._conn.execute(
                "INSERT INTO attacker_win_log (attacker_uid, defender_uid, ts) VALUES (?, ?, ?)",
                (attacker_uid, defender_uid, ts),
            )
            await self._conn.commit()
        except Exception:
            log.warning("record_attacker_win failed attacker=%d defender=%d", attacker_uid, defender_uid, exc_info=True)

    # -- Generic event-window tracker --------------------------------------
    #
    # A shared substrate for "record event X for key Y, prune old rows, count
    # events in a trailing window, list keys currently over a threshold with
    # timing-interval statistics" — the pattern skip-siege abuse detection and
    # BotDetector's timing-regularity signal both need. `kind` discriminates
    # between event families sharing this one table (e.g. "skip_siege",
    # "api_call"); rows of different kinds never cross-contaminate counts.
    # Anti-farm protection is NOT built on this — it's pair-keyed
    # (attacker_uid, defender_uid) rather than single-key, and already has
    # its own well-tested table (attacker_win_log) tied to gameplay rewards.

    async def record_window_event(
        self, kind: str, key_uid: int, ts: int,
        ref_id: int | None = None, magnitude: float | None = None,
        prune_older_than_s: int = 172_800,
    ) -> None:
        """Record one (kind, key_uid) event; prunes this (kind, key_uid)'s
        rows older than prune_older_than_s (default 48h) before inserting."""
        assert self._conn is not None
        try:
            await self._conn.execute(
                "DELETE FROM event_window_log WHERE kind = ? AND key_uid = ? AND ts < ?",
                (kind, key_uid, ts - prune_older_than_s),
            )
            await self._conn.execute(
                "INSERT INTO event_window_log (kind, key_uid, ref_id, magnitude, ts)"
                " VALUES (?, ?, ?, ?, ?)",
                (kind, key_uid, ref_id, magnitude, ts),
            )
            await self._conn.commit()
        except Exception:
            log.warning("record_window_event failed kind=%s key_uid=%d", kind, key_uid, exc_info=True)

    async def count_recent_window_events(self, kind: str, key_uid: int, since_ts: int) -> int:
        """Count (kind, key_uid) events at/after since_ts."""
        assert self._conn is not None
        async with self._conn.execute(
            "SELECT COUNT(*) FROM event_window_log WHERE kind = ? AND key_uid = ? AND ts >= ?",
            (kind, key_uid, since_ts),
        ) as cur:
            row = await cur.fetchone()
        return row[0] if row else 0

    @staticmethod
    def _window_event_stats(rows: Any) -> dict[str, Any]:
        """Compute count/last_ts/mean/stddev-interval/distinct_ref_ids/max_magnitude
        from a list of (ref_id, magnitude, ts) rows for one key, ordered by ts."""
        timestamps = [r["ts"] for r in rows]
        intervals = [b - a for a, b in zip(timestamps, timestamps[1:])]
        if intervals:
            mean_interval = sum(intervals) / len(intervals)
            variance = sum((x - mean_interval) ** 2 for x in intervals) / len(intervals)
            stddev_interval = variance ** 0.5
        else:
            mean_interval = 0.0
            stddev_interval = 0.0
        ref_ids = {r["ref_id"] for r in rows if r["ref_id"] is not None}
        magnitudes = [r["magnitude"] for r in rows if r["magnitude"] is not None]
        return {
            "event_count": len(rows),
            "last_ts": timestamps[-1],
            "mean_interval_s": mean_interval,
            "stddev_interval_s": stddev_interval,
            "distinct_ref_ids": len(ref_ids),
            "max_magnitude": max(magnitudes) if magnitudes else None,
        }

    async def get_active_window_event_keys(
        self, kind: str, since_ts: int, threshold: int,
    ) -> list[dict[str, Any]]:
        """Return per-key_uid stats for every key_uid at/over threshold event
        count within the trailing window, for a given kind."""
        assert self._conn is not None
        async with self._conn.execute(
            "SELECT key_uid, ref_id, magnitude, ts FROM event_window_log"
            " WHERE kind = ? AND ts >= ? ORDER BY key_uid, ts",
            (kind, since_ts),
        ) as cursor:
            rows = await cursor.fetchall()

        by_key: dict[int, list[Any]] = {}
        for r in rows:
            by_key.setdefault(r["key_uid"], []).append(r)

        result: list[dict[str, Any]] = []
        for key_uid, events in by_key.items():
            if len(events) < threshold:
                continue
            result.append({"key_uid": key_uid, **self._window_event_stats(events)})
        result.sort(key=lambda r: r["event_count"], reverse=True)
        return result

    async def get_window_event_stats_for_key(
        self, kind: str, key_uid: int, since_ts: int,
    ) -> dict[str, Any] | None:
        """Return stats for a single (kind, key_uid) within the trailing
        window, or None if there are no events — a single-key variant of
        get_active_window_event_keys that avoids fetching every key's rows
        just to read one."""
        assert self._conn is not None
        async with self._conn.execute(
            "SELECT key_uid, ref_id, magnitude, ts FROM event_window_log"
            " WHERE kind = ? AND key_uid = ? AND ts >= ? ORDER BY ts",
            (kind, key_uid, since_ts),
        ) as cursor:
            rows = await cursor.fetchall()
        if not rows:
            return None
        return {"key_uid": key_uid, **self._window_event_stats(rows)}

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

    # Sanity cap for artifact hold durations shown in season-end stats. A
    # corrupted/epoch-zero `acquired_at` (see the era-3 grant bug, now fixed
    # in EmpireService._maybe_grant_artifact_for_era3) can otherwise produce
    # multi-decade "held" durations that dwarf all real entries. No single
    # legitimate hold can exceed a season's lifetime, so anything past one
    # year is filtered out rather than displayed.
    _MAX_PLAUSIBLE_HOLD_SECS = 365 * 24 * 3600

    async def get_artifact_hold_totals(self) -> list[dict[str, Any]]:
        """Return (uid, artifact_iid, held_secs) including ongoing holds.

        Excludes holds exceeding _MAX_PLAUSIBLE_HOLD_SECS (see constant).
        """
        assert self._conn is not None
        async with self._conn.execute(
            "SELECT uid, artifact_iid, held_secs FROM ("
            "  SELECT uid, artifact_iid,"
            "    total_held_secs + CASE WHEN acquired_at IS NOT NULL"
            "    THEN (unixepoch() - acquired_at) ELSE 0 END AS held_secs"
            "  FROM artifact_holds"
            ") WHERE held_secs <= ?",
            (self._MAX_PLAUSIBLE_HOLD_SECS,),
        ) as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]

    async def get_longest_artifact_hold_per_uid(self) -> list[dict[str, Any]]:
        """Return the longest single-artifact hold duration per uid.

        Excludes holds exceeding _MAX_PLAUSIBLE_HOLD_SECS (see constant) —
        filtered per-row, before the MAX() aggregation, so one implausible
        hold can't mask (or masquerade as) a uid's real longest hold.
        """
        assert self._conn is not None
        async with self._conn.execute(
            "SELECT uid, MAX(held_secs) AS longest_hold_secs FROM ("
            "  SELECT uid,"
            "    total_held_secs + CASE WHEN acquired_at IS NOT NULL"
            "    THEN (unixepoch() - acquired_at) ELSE 0 END AS held_secs"
            "  FROM artifact_holds"
            ") WHERE held_secs <= ?"
            " GROUP BY uid",
            (self._MAX_PLAUSIBLE_HOLD_SECS,),
        ) as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]

    async def get_longest_single_artifact_holds(self, limit: int = 100) -> list[dict[str, Any]]:
        """Return the longest individual artifact holds, across all empires and
        artifacts, ordered longest-first.

        Unlike get_longest_artifact_hold_per_uid (best hold per player, any
        artifact), this answers "which artifact was held longest by a single
        player, and by whom" — e.g. "Book of Heroes held by Alice for 3 days".
        Excludes holds exceeding _MAX_PLAUSIBLE_HOLD_SECS (see constant).
        `limit` caps the row count (season-end stats only need the top few
        plus enough rows to find the requesting player's own rank).
        """
        assert self._conn is not None
        async with self._conn.execute(
            "SELECT uid, artifact_iid, held_secs FROM ("
            "  SELECT uid, artifact_iid,"
            "    total_held_secs + CASE WHEN acquired_at IS NOT NULL"
            "    THEN (unixepoch() - acquired_at) ELSE 0 END AS held_secs"
            "  FROM artifact_holds"
            ") WHERE held_secs <= ?"
            " ORDER BY held_secs DESC LIMIT ?",
            (self._MAX_PLAUSIBLE_HOLD_SECS, limit),
        ) as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]

    async def record_era_first(self, era_key: str, uid: int, empire_name: str) -> None:
        """Record which empire was the first to reach a given era."""
        assert self._conn is not None
        import time
        try:
            await self._conn.execute(
                "INSERT OR IGNORE INTO era_firsts (era_key, uid, empire_name, reached_at) VALUES (?, ?, ?, ?)",
                (era_key, uid, empire_name, int(time.time())),
            )
            await self._conn.commit()
        except Exception:
            log.warning("record_era_first failed era=%s uid=%d", era_key, uid, exc_info=True)

    async def get_era_firsts(self) -> list[dict[str, Any]]:
        """Return all era_firsts rows ordered by ERA_ORDER."""
        assert self._conn is not None
        async with self._conn.execute("SELECT era_key, uid, empire_name, reached_at FROM era_firsts") as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]


    # -- Trophy operations ---------------------------------------------------

    async def get_earned_trophy_iids(self, uid: int) -> set[str]:
        """Return IIDs of all trophies earned by this player."""
        assert self._conn is not None
        async with self._conn.execute(
            "SELECT iid FROM player_trophies WHERE uid = ?", (uid,)
        ) as cur:
            rows = await cur.fetchall()
        return {r["iid"] for r in rows}

    async def award_trophy(self, uid: int, iid: str, earned_at: int, season: int = 1) -> None:
        """Record a newly earned trophy. No-op if already earned (each trophy is earned once)."""
        assert self._conn is not None
        try:
            await self._conn.execute(
                "INSERT OR IGNORE INTO player_trophies (uid, iid, earned_at, season) VALUES (?, ?, ?, ?)",
                (uid, iid, earned_at, season),
            )
            await self._conn.commit()
        except Exception:
            log.warning("award_trophy failed uid=%d iid=%s", uid, iid, exc_info=True)

    async def get_trophy_rows(self, uid: int) -> list[dict[str, Any]]:
        """Return full rows (iid, earned_at, season) for all trophies earned by uid."""
        assert self._conn is not None
        async with self._conn.execute(
            "SELECT iid, earned_at, season FROM player_trophies WHERE uid = ? ORDER BY earned_at",
            (uid,),
        ) as cur:
            rows = await cur.fetchall()
        return [dict(r) for r in rows]

    async def get_all_trophy_rows(self) -> list[dict[str, Any]]:
        """Return full trophy rows (uid, iid, earned_at, season) for all players."""
        assert self._conn is not None
        async with self._conn.execute(
            "SELECT uid, iid, earned_at, season FROM player_trophies ORDER BY uid, earned_at",
        ) as cur:
            rows = await cur.fetchall()
        return [dict(r) for r in rows]

    async def record_season_winners(
        self,
        season_number: int,
        season_title: str,
        winners: list[dict[str, Any]],  # list of {place, empire_uid, empire_name, culture}
    ) -> None:
        """Insert top-3 season results into season_winners. Skips if already recorded."""
        assert self._conn is not None
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc).isoformat()
        existing = await self._conn.execute(
            "SELECT COUNT(*) FROM season_winners WHERE season_number = ?", (season_number,)
        )
        row = await existing.fetchone()
        if row and row[0] > 0:
            log.info("Season %d winners already recorded — skipping", season_number)
            return
        for w in winners:
            await self._conn.execute(
                "INSERT INTO season_winners (season_number, season_title, place, empire_uid, empire_name, culture, recorded_at)"
                " VALUES (?, ?, ?, ?, ?, ?, ?)",
                (season_number, season_title, w["place"], w["empire_uid"], w["empire_name"], w["culture"], now),
            )
        await self._conn.commit()
        log.info("Season %d winners recorded (%d entries)", season_number, len(winners))

    async def get_season_winners(self, season_number: int | None = None) -> list[dict[str, Any]]:
        """Return season winners, optionally filtered to one season."""
        assert self._conn is not None
        if season_number is not None:
            async with self._conn.execute(
                "SELECT * FROM season_winners WHERE season_number = ? ORDER BY place", (season_number,)
            ) as cur:
                rows = await cur.fetchall()
        else:
            async with self._conn.execute(
                "SELECT * FROM season_winners ORDER BY season_number, place"
            ) as cur:
                rows = await cur.fetchall()
        return [dict(r) for r in rows]

    async def wipe_season_stats(self) -> None:
        """Delete all per-season runtime state at the season wipe.

        Covers empire_stats, era_firsts, artifact_holds and the alliance
        declarations — alliances belong to the season that formed them and
        must not carry last season's teams into the new one. User accounts
        are preserved.
        """
        assert self._conn is not None
        await self._conn.execute("DELETE FROM empire_stats")
        await self._conn.execute("DELETE FROM era_firsts")
        await self._conn.execute("DELETE FROM artifact_holds")
        await self._conn.execute("DELETE FROM alliance_declarations")
        await self._conn.commit()
        log.info(
            "Season stats wiped (empire_stats, era_firsts, artifact_holds, alliance_declarations)"
        )
