"""Tests for persistence/database.py — async SQLite operations.

Uses an in-memory SQLite database (":memory:") to avoid touching disk.
"""

from __future__ import annotations

import base64
from pathlib import Path

import pytest
import yaml

from gameserver.persistence.database import Database


# ---------------------------------------------------------------------------
# Fixture: in-memory database, connected
# ---------------------------------------------------------------------------

@pytest.fixture
async def db() -> Database:
    database = Database(":memory:")
    await database.connect()
    yield database
    await database.close()


# ---------------------------------------------------------------------------
# User CRUD
# ---------------------------------------------------------------------------

class TestUserCRUD:
    async def test_create_and_get_user(self, db: Database):
        uid = await db.create_user("alice", "hash123", email="alice@example.com", empire_name="Alicia")
        assert uid > 0
        user = await db.get_user("alice")
        assert user is not None
        assert user["username"] == "alice"
        assert user["password_hash"] == "hash123"
        assert user["email"] == "alice@example.com"
        assert user["empire_name"] == "Alicia"

    async def test_get_user_case_insensitive(self, db: Database):
        await db.create_user("Bob", "pw", email="", empire_name="")
        user = await db.get_user("bob")
        assert user is not None
        assert user["username"] == "Bob"

    async def test_get_user_not_found_returns_none(self, db: Database):
        assert await db.get_user("nobody") is None

    async def test_get_user_by_uid(self, db: Database):
        uid = await db.create_user("carol", "pw")
        user = await db.get_user_by_uid(uid)
        assert user is not None
        assert user["uid"] == uid
        assert user["username"] == "carol"

    async def test_get_user_by_uid_not_found(self, db: Database):
        assert await db.get_user_by_uid(99999) is None

    async def test_update_password_hash(self, db: Database):
        uid = await db.create_user("dave", "old_hash")
        await db.update_password_hash(uid, "new_hash")
        user = await db.get_user("dave")
        assert user["password_hash"] == "new_hash"

    async def test_delete_user_returns_true(self, db: Database):
        await db.create_user("eve", "pw")
        deleted = await db.delete_user("eve")
        assert deleted is True
        assert await db.get_user("eve") is None

    async def test_delete_nonexistent_user_returns_false(self, db: Database):
        deleted = await db.delete_user("ghost")
        assert deleted is False

    async def test_rename_empire(self, db: Database):
        uid = await db.create_user("frank", "pw", empire_name="OldName")
        ok = await db.rename_empire(uid, "NewName")
        assert ok is True
        user = await db.get_user_by_uid(uid)
        assert user["empire_name"] == "NewName"

    async def test_rename_empire_nonexistent_returns_false(self, db: Database):
        ok = await db.rename_empire(99999, "X")
        assert ok is False

    async def test_update_last_seen(self, db: Database):
        uid = await db.create_user("grace", "pw")
        await db.update_last_seen(uid)  # should not raise

    async def test_list_users(self, db: Database):
        await db.create_user("u1", "pw")
        await db.create_user("u2", "pw")
        users = await db.list_users()
        assert len(users) == 2
        usernames = {u["username"] for u in users}
        assert "u1" in usernames
        assert "u2" in usernames


# ---------------------------------------------------------------------------
# Login events
# ---------------------------------------------------------------------------

class TestLoginEvents:
    async def test_record_login(self, db: Database):
        uid = await db.create_user("loginuser", "pw")
        await db.record_login(uid, "192.168.1.1", "fp123")  # should not raise

    async def test_get_device_clusters_empty(self, db: Database):
        clusters = await db.get_device_clusters()
        assert clusters == []

    async def test_get_device_clusters_shared_ip(self, db: Database):
        u1 = await db.create_user("u1", "pw")
        u2 = await db.create_user("u2", "pw")
        await db.record_login(u1, "10.0.0.1", "fp_a")
        await db.record_login(u2, "10.0.0.1", "fp_b")  # same IP
        clusters = await db.get_device_clusters()
        # Should detect one cluster (u1, u2 share IP)
        assert len(clusters) >= 1


# ---------------------------------------------------------------------------
# Messages
# ---------------------------------------------------------------------------

class TestMessages:
    async def test_send_and_get_inbox(self, db: Database):
        uid1 = await db.create_user("sender", "pw")
        uid2 = await db.create_user("receiver", "pw")
        msg = await db.send_message(from_uid=uid1, to_uid=uid2, body="Hello!")
        assert msg["body"] == "Hello!"
        assert msg["from_uid"] == uid1
        assert msg["to_uid"] == uid2
        assert msg["read"] is False

        inbox = await db.get_inbox(uid2)
        assert len(inbox) == 1
        assert inbox[0]["body"] == "Hello!"

    async def test_system_message_is_pre_read(self, db: Database):
        uid = await db.create_user("player", "pw")
        msg = await db.send_message(from_uid=0, to_uid=uid, body="System msg")
        assert msg["read"] is True

    async def test_get_sent(self, db: Database):
        uid1 = await db.create_user("s1", "pw")
        uid2 = await db.create_user("s2", "pw")
        await db.send_message(uid1, uid2, "msg1")
        sent = await db.get_sent(uid1)
        assert len(sent) == 1

    async def test_mark_read(self, db: Database):
        uid1 = await db.create_user("mr1", "pw")
        uid2 = await db.create_user("mr2", "pw")
        msg = await db.send_message(uid1, uid2, "unread")
        msg_id = msg["id"]
        ok = await db.mark_read(uid2, msg_id)
        assert ok is True
        inbox = await db.get_inbox(uid2)
        assert inbox[0]["read"] is True

    async def test_mark_read_wrong_uid_returns_false(self, db: Database):
        uid1 = await db.create_user("wr1", "pw")
        uid2 = await db.create_user("wr2", "pw")
        uid3 = await db.create_user("wr3", "pw")
        msg = await db.send_message(uid1, uid2, "msg")
        # uid3 tries to mark a message addressed to uid2
        ok = await db.mark_read(uid3, msg["id"])
        assert ok is False

    async def test_unread_count(self, db: Database):
        uid1 = await db.create_user("uc1", "pw")
        uid2 = await db.create_user("uc2", "pw")
        await db.send_message(uid1, uid2, "msg1")
        await db.send_message(uid1, uid2, "msg2")
        count = await db.unread_count(uid2)
        assert count == 2

    async def test_get_global(self, db: Database):
        uid = await db.create_user("chatuser", "pw")
        await db.send_message(from_uid=uid, to_uid=0, body="global msg")
        msgs = await db.get_global()
        assert any(m["body"] == "global msg" for m in msgs)

    async def test_get_private_for(self, db: Database):
        uid1 = await db.create_user("pv1", "pw")
        uid2 = await db.create_user("pv2", "pw")
        await db.send_message(uid1, uid2, "private")
        msgs = await db.get_private_for(uid1)
        assert any(m["body"] == "private" for m in msgs)

    async def test_get_battle_reports_for(self, db: Database):
        uid = await db.create_user("br1", "pw")
        await db.send_message(from_uid=0, to_uid=uid, body="battle report")
        reports = await db.get_battle_reports_for(uid)
        assert len(reports) == 1
        assert reports[0]["body"] == "battle report"

    async def test_unread_count_private(self, db: Database):
        uid1 = await db.create_user("ucp1", "pw")
        uid2 = await db.create_user("ucp2", "pw")
        await db.send_message(uid1, uid2, "private msg")
        count = await db.unread_count_private(uid2)
        assert count == 1

    async def test_unread_count_battle(self, db: Database):
        # system messages (from_uid=0) are pre-marked as read, so count stays 0
        uid = await db.create_user("ucb1", "pw")
        await db.send_message(from_uid=0, to_uid=uid, body="battle report")
        count = await db.unread_count_battle(uid)
        assert count == 0  # auto-read



# ---------------------------------------------------------------------------
# Push subscriptions
# ---------------------------------------------------------------------------

class TestPushSubscriptions:
    async def test_save_and_get(self, db: Database):
        uid = await db.create_user("pushuser", "pw")
        sub = {"endpoint": "https://example.com/push", "keys": {"auth": "abc", "p256dh": "xyz"}}
        await db.save_push_subscription(uid, sub)
        subs = await db.get_push_subscriptions(uid)
        assert len(subs) == 1
        assert subs[0]["endpoint"] == "https://example.com/push"

    async def test_delete_subscription(self, db: Database):
        uid = await db.create_user("pushdel", "pw")
        sub = {"endpoint": "https://example.com/del", "keys": {}}
        await db.save_push_subscription(uid, sub)
        await db.delete_push_subscription(uid, "https://example.com/del")
        subs = await db.get_push_subscriptions(uid)
        assert subs == []

    async def test_upsert_on_duplicate_endpoint(self, db: Database):
        uid1 = await db.create_user("up1", "pw")
        uid2 = await db.create_user("up2", "pw")
        sub = {"endpoint": "https://same.com/push", "keys": {}}
        await db.save_push_subscription(uid1, sub)
        sub2 = {"endpoint": "https://same.com/push", "keys": {"new": "data"}}
        await db.save_push_subscription(uid2, sub2)
        # Should have only one subscription for this endpoint
        subs1 = await db.get_push_subscriptions(uid1)
        subs2 = await db.get_push_subscriptions(uid2)
        assert len(subs1) + len(subs2) == 1


# ---------------------------------------------------------------------------
# AI battle log
# ---------------------------------------------------------------------------

class TestInsertAiBattleLog:
    async def test_insert_succeeds(self, db: Database):
        await db.insert_ai_battle_log(
            bid=1,
            defender_name="TestDefender",
            defender_era="Stone Age",
            army_name="Goblin Horde",
            result="AI_WIN",
            path_length=5,
            life_start=10.0,
            life_end=0.0,
            tower_count=3,
            tower_gold=150.0,
            towers_by_era='{"Stone Age": 3}',
            critters_total=20,
            critters_reached=10,
            critters_killed=10,
            critters_by_era='{"Stone Age": 20}',
            battle_duration_s=45.3,
        )
        # Verify by querying directly
        assert db._conn is not None
        async with db._conn.execute("SELECT COUNT(*) FROM ai_battle_log") as cur:
            row = await cur.fetchone()
        assert row[0] == 1


# ---------------------------------------------------------------------------
# Rankings stubs
# ---------------------------------------------------------------------------

class TestRankingStubs:
    async def test_update_ranking_noop(self, db: Database):
        await db.update_ranking(uid=1, tai=42.0)  # should not raise

    async def test_get_rankings_returns_empty(self, db: Database):
        result = await db.get_rankings()
        assert result == []


# ---------------------------------------------------------------------------
# YAML migration
# ---------------------------------------------------------------------------

class TestMigrateMessagesFromYaml:
    async def test_nonexistent_file_returns_zero(self, db: Database):
        count = await db.migrate_messages_from_yaml("/tmp/__nonexistent_path__.yaml")
        assert count == 0

    async def test_migration_imports_messages(self, db: Database, tmp_path: Path):
        body_b64 = base64.b64encode("Hello world".encode()).decode()
        data = {
            "messages": [
                {"id": 1, "from_uid": 0, "to_uid": 2, "body_b64": body_b64,
                 "read": True, "sent_at": "2024-01-01 12:00:00"},
            ]
        }
        f = tmp_path / "messages.yaml"
        f.write_text(yaml.dump(data))
        count = await db.migrate_messages_from_yaml(str(f))
        assert count == 1

    async def test_migration_skipped_if_db_has_data(self, db: Database, tmp_path: Path):
        uid1 = await db.create_user("skip1", "pw")
        uid2 = await db.create_user("skip2", "pw")
        await db.send_message(uid1, uid2, "existing")
        body_b64 = base64.b64encode("new".encode()).decode()
        data = {"messages": [{"id": 99, "from_uid": 0, "to_uid": uid2,
                               "body_b64": body_b64, "read": False, "sent_at": None}]}
        f = tmp_path / "msgs.yaml"
        f.write_text(yaml.dump(data))
        count = await db.migrate_messages_from_yaml(str(f))
        assert count == 0


# ---------------------------------------------------------------------------
# Empire stats
# ---------------------------------------------------------------------------

class TestEmpireStats:
    async def test_get_empire_stats_returns_none_for_unknown_uid(self, db: Database):
        assert await db.get_empire_stats(9999) is None

    async def test_get_all_empire_stats_empty(self, db: Database):
        assert await db.get_all_empire_stats() == []

    async def test_record_empire_stat_creates_row(self, db: Database):
        await db.record_empire_stat(1, attacks_won_human=1)
        row = await db.get_empire_stats(1)
        assert row is not None
        assert row["attacks_won_human"] == 1

    async def test_record_empire_stat_increments(self, db: Database):
        await db.record_empire_stat(1, attacks_won_human=1)
        await db.record_empire_stat(1, attacks_won_human=1)
        await db.record_empire_stat(1, attacks_won_human=1)
        row = await db.get_empire_stats(1)
        assert row["attacks_won_human"] == 3

    async def test_record_empire_stat_multiple_columns(self, db: Database):
        await db.record_empire_stat(1, attacks_won_human=2, spies_sent=5)
        row = await db.get_empire_stats(1)
        assert row["attacks_won_human"] == 2
        assert row["spies_sent"] == 5

    async def test_record_empire_stat_independent_uids(self, db: Database):
        await db.record_empire_stat(10, critters_killed=100)
        await db.record_empire_stat(20, critters_killed=50)
        r10 = await db.get_empire_stats(10)
        r20 = await db.get_empire_stats(20)
        assert r10["critters_killed"] == 100
        assert r20["critters_killed"] == 50

    async def test_record_empire_stat_float_creates_row(self, db: Database):
        await db.record_empire_stat_float(1, "culture_stolen", 123.5)
        row = await db.get_empire_stats(1)
        assert row is not None
        assert abs(row["culture_stolen"] - 123.5) < 0.001

    async def test_record_empire_stat_float_accumulates(self, db: Database):
        await db.record_empire_stat_float(1, "culture_won", 100.0)
        await db.record_empire_stat_float(1, "culture_won", 50.5)
        row = await db.get_empire_stats(1)
        assert abs(row["culture_won"] - 150.5) < 0.001

    async def test_record_empire_stat_float_research(self, db: Database):
        await db.record_empire_stat_float(1, "research_stolen", 200.0)
        await db.record_empire_stat_float(1, "research_won", 75.0)
        row = await db.get_empire_stats(1)
        assert abs(row["research_stolen"] - 200.0) < 0.001
        assert abs(row["research_won"] - 75.0) < 0.001

    async def test_record_empire_stat_max_creates_row(self, db: Database):
        await db.record_empire_stat_max(1, "longest_battle_ms", 30_000)
        row = await db.get_empire_stats(1)
        assert row["longest_battle_ms"] == 30_000

    async def test_record_empire_stat_max_keeps_higher(self, db: Database):
        await db.record_empire_stat_max(1, "longest_battle_ms", 30_000)
        await db.record_empire_stat_max(1, "longest_battle_ms", 60_000)
        row = await db.get_empire_stats(1)
        assert row["longest_battle_ms"] == 60_000

    async def test_record_empire_stat_max_does_not_lower(self, db: Database):
        await db.record_empire_stat_max(1, "longest_battle_ms", 60_000)
        await db.record_empire_stat_max(1, "longest_battle_ms", 10_000)
        row = await db.get_empire_stats(1)
        assert row["longest_battle_ms"] == 60_000

    async def test_get_all_empire_stats_returns_all_rows(self, db: Database):
        await db.record_empire_stat(1, attacks_won_human=1)
        await db.record_empire_stat(2, defense_won_ai=3)
        await db.record_empire_stat(3, spies_sent=2)
        rows = await db.get_all_empire_stats()
        uids = {r["uid"] for r in rows}
        assert {1, 2, 3} == uids

    async def test_unset_columns_default_to_zero(self, db: Database):
        await db.record_empire_stat(1, attacks_won_human=1)
        row = await db.get_empire_stats(1)
        assert row["attacks_lost_human"] == 0
        assert row["critters_killed"] == 0
        assert row["spies_sent"] == 0
        assert row["defense_gold_earned"] == 0.0


# ---------------------------------------------------------------------------
# Artifact hold tracking
# ---------------------------------------------------------------------------

class TestArtifactHolds:
    async def test_acquired_sets_timestamp(self, db: Database):
        await db.record_artifact_acquired(1, "goblet", 1_000_000.0)
        rows = await db.get_artifact_hold_totals()
        assert len(rows) == 1
        # held_secs includes ongoing hold: unixepoch() - 1_000_000 (a past time)
        # We only verify the row exists and held_secs is positive
        assert rows[0]["uid"] == 1
        assert rows[0]["artifact_iid"] == "goblet"
        assert rows[0]["held_secs"] >= 0

    async def test_lost_accumulates_duration(self, db: Database):
        t0 = 1_000_000.0
        t1 = t0 + 3600.0  # held for 1 hour
        await db.record_artifact_acquired(1, "goblet", t0)
        await db.record_artifact_lost(1, "goblet", t1)
        rows = await db.get_artifact_hold_totals()
        assert len(rows) == 1
        assert abs(rows[0]["held_secs"] - 3600.0) < 1.0

    async def test_lost_clears_acquired_at(self, db: Database):
        await db.record_artifact_acquired(1, "goblet", 1_000_000.0)
        await db.record_artifact_lost(1, "goblet", 1_003_600.0)
        # After losing, held_secs should be stable (no ongoing hold)
        r1 = await db.get_artifact_hold_totals()
        r2 = await db.get_artifact_hold_totals()
        assert abs(r1[0]["held_secs"] - r2[0]["held_secs"]) < 0.1

    async def test_multiple_acquire_lose_cycles_accumulate(self, db: Database):
        await db.record_artifact_acquired(1, "goblet", 0.0)
        await db.record_artifact_lost(1, "goblet", 1000.0)       # +1000s
        await db.record_artifact_acquired(1, "goblet", 5000.0)
        await db.record_artifact_lost(1, "goblet", 5500.0)       # +500s
        rows = await db.get_artifact_hold_totals()
        assert abs(rows[0]["held_secs"] - 1500.0) < 1.0

    async def test_lost_without_acquired_is_noop(self, db: Database):
        # record_artifact_lost on a row with acquired_at=NULL should not crash
        await db.record_artifact_acquired(1, "goblet", 0.0)
        await db.record_artifact_lost(1, "goblet", 100.0)
        # call lost again without a new acquired — should be silent no-op
        await db.record_artifact_lost(1, "goblet", 200.0)
        rows = await db.get_artifact_hold_totals()
        assert abs(rows[0]["held_secs"] - 100.0) < 1.0

    async def test_lost_on_nonexistent_row_is_noop(self, db: Database):
        await db.record_artifact_lost(99, "ghost", 1_000_000.0)  # must not raise
        rows = await db.get_artifact_hold_totals()
        assert rows == []

    async def test_multiple_empires_same_artifact(self, db: Database):
        await db.record_artifact_acquired(1, "crown", 0.0)
        await db.record_artifact_lost(1, "crown", 500.0)
        await db.record_artifact_acquired(2, "crown", 600.0)
        await db.record_artifact_lost(2, "crown", 700.0)
        rows = await db.get_artifact_hold_totals()
        by_uid = {r["uid"]: r["held_secs"] for r in rows}
        assert abs(by_uid[1] - 500.0) < 1.0
        assert abs(by_uid[2] - 100.0) < 1.0

    async def test_same_empire_multiple_artifacts(self, db: Database):
        await db.record_artifact_acquired(1, "crown", 0.0)
        await db.record_artifact_lost(1, "crown", 200.0)
        await db.record_artifact_acquired(1, "goblet", 0.0)
        await db.record_artifact_lost(1, "goblet", 300.0)
        rows = await db.get_artifact_hold_totals()
        by_iid = {r["artifact_iid"]: r["held_secs"] for r in rows}
        assert abs(by_iid["crown"] - 200.0) < 1.0
        assert abs(by_iid["goblet"] - 300.0) < 1.0

    async def test_reacquire_overwrites_timestamp(self, db: Database):
        # Empire steals artifact again after losing it
        await db.record_artifact_acquired(1, "goblet", 1000.0)
        await db.record_artifact_lost(1, "goblet", 1100.0)   # 100s accrued
        await db.record_artifact_acquired(1, "goblet", 2000.0)
        # Still holding — total_held_secs=100, plus ongoing from ts=2000
        rows = await db.get_artifact_hold_totals()
        assert rows[0]["held_secs"] >= 100.0
