"""Tests for persistence/database.py — async SQLite operations.

Uses an in-memory SQLite database (":memory:") to avoid touching disk.
"""

from __future__ import annotations

import base64
import time
from pathlib import Path

import pytest
import yaml

from gameserver.persistence.database import SPY_REPORT_MAX_AGE_DAYS, Database


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

    async def test_shared_device_id_scores_70(self, db: Database):
        u1 = await db.create_user("d1", "pw")
        u2 = await db.create_user("d2", "pw")
        await db.record_login(u1, "1.1.1.1", "fp_x", "device-abc")
        await db.record_login(u2, "2.2.2.2", "fp_y", "device-abc")  # same device_id, different IP/fp
        clusters = await db.get_device_clusters()
        assert len(clusters) == 1
        assert clusters[0]["score"] == 70
        assert clusters[0]["shared_dids"] == "device-abc"

    async def test_shared_device_id_and_fingerprint_scores_125_capped_at_100(self, db: Database):
        u1 = await db.create_user("e1", "pw")
        u2 = await db.create_user("e2", "pw")
        await db.record_login(u1, "1.1.1.1", "fp_shared", "device-shared")
        await db.record_login(u2, "2.2.2.2", "fp_shared", "device-shared")
        clusters = await db.get_device_clusters()
        assert clusters[0]["score"] == 100

    async def test_below_score_15_excluded(self, db: Database):
        u1 = await db.create_user("f1", "pw")
        u2 = await db.create_user("f2", "pw")
        # only an old (>30d) shared IP -> score 15, which is NOT below 15, so
        # use no shared signal at all instead to confirm no cluster appears
        await db.record_login(u1, "3.3.3.3", "fp_only_u1")
        await db.record_login(u2, "4.4.4.4", "fp_only_u2")
        clusters = await db.get_device_clusters()
        assert clusters == []

    async def test_group_larger_than_guard_is_skipped(self, db: Database):
        """A single IP shared by more than _DEVICE_CLUSTER_MAX_GROUP_SIZE uids
        (e.g. NAT/shared WiFi) must not produce O(n^2) pairs — this is the
        guard that prevents the pairing step itself from hanging on a huge
        shared-signal group, independent of the query-level fix."""
        uids = [await db.create_user(f"g{i}", "pw") for i in range(60)]
        for uid in uids:
            await db.record_login(uid, "9.9.9.9", f"fp_{uid}")
        clusters = await db.get_device_clusters()
        # The shared IP group (60 uids) exceeds the guard and is skipped
        # entirely; since fingerprints are all distinct, no clusters result.
        assert clusters == []

    async def test_multiple_pairs_returned_independently(self, db: Database):
        u1 = await db.create_user("h1", "pw")
        u2 = await db.create_user("h2", "pw")
        u3 = await db.create_user("h3", "pw")
        await db.record_login(u1, "5.5.5.5", "fp_h1", "device-h1h2")
        await db.record_login(u2, "6.6.6.6", "fp_h2", "device-h1h2")  # shares device with u1
        await db.record_login(u3, "5.5.5.5", "fp_h3")  # shares IP with u1 only
        clusters = await db.get_device_clusters()
        pairs = {(c["uid_a"], c["uid_b"]) for c in clusters}
        assert (min(u1, u2), max(u1, u2)) in pairs
        assert (min(u1, u3), max(u1, u3)) in pairs
        assert (min(u2, u3), max(u2, u3)) not in pairs

    async def test_runs_quickly_on_large_login_history(self, db: Database):
        """Regression test for the lifelock this replaced: the old
        self-join-with-OR query degraded to an unindexable O(n^2) scan and
        hung indefinitely on a real login_events table with ~300k rows.
        This seeds a smaller but still substantial history and asserts the
        call completes well within a reasonable bound."""
        import time as _time

        uids = [await db.create_user(f"perf{i}", "pw") for i in range(200)]
        for i, uid in enumerate(uids):
            # small overlapping groups of shared IPs/fingerprints, not one huge group
            await db.record_login(uid, f"10.0.{i % 20}.1", f"fp_{i % 20}", f"device_{i}")
        t0 = _time.monotonic()
        clusters = await db.get_device_clusters()
        elapsed = _time.monotonic() - t0
        assert elapsed < 5.0
        assert isinstance(clusters, list)


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

    async def test_system_message_is_unread(self, db: Database):
        uid = await db.create_user("player", "pw")
        msg = await db.send_message(from_uid=0, to_uid=uid, body="System msg")
        assert msg["read"] is False

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
        uid = await db.create_user("ucb1", "pw")
        await db.send_message(from_uid=0, to_uid=uid, body="battle report")
        count = await db.unread_count_battle(uid)
        assert count == 1



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
        # Acquired a moment ago (real "now"-relative time) — an absolute
        # near-epoch timestamp here would exceed the plausible-hold cap and
        # get filtered out by get_artifact_hold_totals (see that cap's own
        # regression tests below).
        await db.record_artifact_acquired(1, "goblet", time.time() - 10.0)
        rows = await db.get_artifact_hold_totals()
        assert len(rows) == 1
        # held_secs includes the ongoing hold — just verify it's a small,
        # positive, plausible duration.
        assert rows[0]["uid"] == 1
        assert rows[0]["artifact_iid"] == "goblet"
        assert 0 <= rows[0]["held_secs"] < 60

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
        # Empire steals artifact again after losing it. Uses real "now"-
        # relative timestamps — an absolute near-epoch value would exceed
        # the plausible-hold cap and get filtered out entirely.
        now = time.time()
        await db.record_artifact_acquired(1, "goblet", now - 200.0)
        await db.record_artifact_lost(1, "goblet", now - 100.0)   # 100s accrued
        await db.record_artifact_acquired(1, "goblet", now - 10.0)
        # Still holding — total_held_secs=100, plus ongoing ~10s.
        rows = await db.get_artifact_hold_totals()
        assert rows[0]["held_secs"] >= 100.0


class TestArtifactHoldPlausibilityCap:
    """Season-end stats must filter out implausible (>1 year) hold durations.

    Regression coverage for the era-3 grant bug that recorded acquired_at=0.0
    (Unix epoch 1970), producing ~56-year "held" durations that dwarfed every
    real entry on the "Longest Artifact Hold" leaderboard.
    """

    async def test_get_artifact_hold_totals_excludes_epoch_zero_row(self, db: Database):
        # acquired_at=0.0 -> held_secs ~= decades. Must not appear at all.
        await db.record_artifact_acquired(1, "cursed_relic", 0.0)
        await db.record_artifact_acquired(2, "goblet", time.time() - 10.0)
        rows = await db.get_artifact_hold_totals()
        uids = {r["uid"] for r in rows}
        assert 1 not in uids
        assert 2 in uids

    async def test_get_artifact_hold_totals_keeps_plausible_row(self, db: Database):
        # A hold just under the 1-year cap must still be reported.
        just_under_a_year = time.time() - (364 * 24 * 3600)
        await db.record_artifact_acquired(1, "goblet", just_under_a_year)
        rows = await db.get_artifact_hold_totals()
        assert len(rows) == 1
        assert rows[0]["held_secs"] < 365 * 24 * 3600

    async def test_get_longest_artifact_hold_per_uid_ignores_implausible_row(self, db: Database):
        # uid=1 has one implausible (epoch-zero) hold and one plausible one —
        # the reported "longest hold" must be the plausible value, not the
        # implausible one, and MAX() must not let the bad row leak through.
        now = time.time()
        await db.record_artifact_acquired(1, "cursed_relic", 0.0)
        await db.record_artifact_acquired(1, "goblet", now - 500.0)
        rows = await db.get_longest_artifact_hold_per_uid()
        by_uid = {r["uid"]: r["longest_hold_secs"] for r in rows}
        assert by_uid[1] < 600.0

    async def test_get_longest_artifact_hold_per_uid_omits_uid_when_only_implausible(
        self, db: Database,
    ):
        # If a uid's ONLY hold is implausible, that uid must be absent from
        # the results entirely — not present with a bogus 56-year value.
        await db.record_artifact_acquired(1, "cursed_relic", 0.0)
        rows = await db.get_longest_artifact_hold_per_uid()
        assert 1 not in {r["uid"] for r in rows}


class TestLongestSingleArtifactHolds:
    """get_longest_single_artifact_holds: ranked individual holds, any artifact."""

    async def test_returns_empty_when_no_holds(self, db: Database):
        assert await db.get_longest_single_artifact_holds() == []

    async def test_returns_rows_ordered_longest_first(self, db: Database):
        now = time.time()
        await db.record_artifact_acquired(1, "goblet", now - 100.0)
        await db.record_artifact_acquired(2, "book_of_heroes", now - 500.0)
        await db.record_artifact_acquired(3, "crown", now - 300.0)
        rows = await db.get_longest_single_artifact_holds()
        assert [r["uid"] for r in rows] == [2, 3, 1]
        assert rows[0]["artifact_iid"] == "book_of_heroes"
        assert rows[0]["held_secs"] >= 495.0

    async def test_limit_caps_row_count(self, db: Database):
        now = time.time()
        await db.record_artifact_acquired(1, "goblet", now - 100.0)
        await db.record_artifact_acquired(2, "book_of_heroes", now - 500.0)
        rows = await db.get_longest_single_artifact_holds(limit=1)
        assert len(rows) == 1
        assert rows[0]["uid"] == 2

    async def test_excludes_implausible_row(self, db: Database):
        # The epoch-zero row would otherwise dwarf every real hold.
        now = time.time()
        await db.record_artifact_acquired(1, "cursed_relic", 0.0)
        await db.record_artifact_acquired(2, "goblet", now - 50.0)
        rows = await db.get_longest_single_artifact_holds()
        assert [r["uid"] for r in rows] == [2]
        assert rows[0]["artifact_iid"] == "goblet"


# ---------------------------------------------------------------------------
# Spy reports
# ---------------------------------------------------------------------------

class TestSpyReports:
    async def test_save_and_get_spy_report(self, db: Database):
        await db.save_spy_report(1, 99, "Enemy", {"era": "stone", "era_idx": 0, "placed_towers": [], "path_length": 5})
        reports = await db.get_spy_reports_for(1)
        assert len(reports) == 1
        assert reports[0]["defender_uid"] == 99
        assert reports[0]["defender_name"] == "Enemy"
        assert reports[0]["era"] == "stone"
        assert reports[0]["path_length"] == 5

    async def test_get_spy_reports_empty_for_unknown_attacker(self, db: Database):
        reports = await db.get_spy_reports_for(1)
        assert reports == []

    async def test_repeated_spy_on_same_target_overwrites(self, db: Database):
        await db.save_spy_report(1, 99, "Enemy", {"era": "stone", "era_idx": 0, "placed_towers": [], "path_length": 5})
        await db.save_spy_report(1, 99, "Enemy", {"era": "medieval", "era_idx": 2, "placed_towers": [], "path_length": 8})
        reports = await db.get_spy_reports_for(1)
        assert len(reports) == 1
        assert reports[0]["era"] == "medieval"
        assert reports[0]["path_length"] == 8

    async def test_multiple_targets_kept_separately(self, db: Database):
        await db.save_spy_report(1, 99, "Enemy A", {"era": "stone", "era_idx": 0, "placed_towers": [], "path_length": 5})
        await db.save_spy_report(1, 100, "Enemy B", {"era": "medieval", "era_idx": 2, "placed_towers": [], "path_length": 8})
        reports = await db.get_spy_reports_for(1)
        assert len(reports) == 2
        by_uid = {r["defender_uid"]: r for r in reports}
        assert by_uid[99]["defender_name"] == "Enemy A"
        assert by_uid[100]["defender_name"] == "Enemy B"

    async def test_reports_scoped_to_attacker(self, db: Database):
        await db.save_spy_report(1, 99, "Enemy", {"era": "stone", "era_idx": 0, "placed_towers": [], "path_length": 5})
        reports = await db.get_spy_reports_for(2)
        assert reports == []

    async def test_reports_older_than_max_age_are_hidden(self, db: Database):
        await db.save_spy_report(1, 99, "Enemy", {"era": "stone", "era_idx": 0, "placed_towers": [], "path_length": 5})
        await db._conn.execute(
            "UPDATE spy_reports SET created_at = datetime('now', ?) WHERE attacker_uid = 1 AND defender_uid = 99",
            (f"-{SPY_REPORT_MAX_AGE_DAYS} days -1 second",),
        )
        await db._conn.commit()
        reports = await db.get_spy_reports_for(1)
        assert reports == []

# Skip-siege abuse detection is now covered by the generic event-window
# tracker's tests in test_event_window_log.py (kind="skip_siege") — the
# bespoke record_skip_siege/count_recent_skip_sieges/get_active_skip_siege_abusers
# methods have been removed.


# ---------------------------------------------------------------------------
# Alliance declarations
# ---------------------------------------------------------------------------

class TestAllianceDeclarations:
    async def test_toggle_inserts_then_deletes(self, db: Database):
        declared = await db.toggle_alliance_declaration(1, 2)
        assert declared is True
        declared_to, _ = await db.get_alliance_declarations_for(1)
        assert declared_to == {2}

        declared = await db.toggle_alliance_declaration(1, 2)
        assert declared is False
        declared_to, _ = await db.get_alliance_declarations_for(1)
        assert declared_to == set()

    async def test_mutual_declarations_visible_both_directions(self, db: Database):
        await db.toggle_alliance_declaration(1, 2)
        await db.toggle_alliance_declaration(2, 1)

        declared_to_1, declared_by_1 = await db.get_alliance_declarations_for(1)
        assert declared_to_1 == {2}
        assert declared_by_1 == {2}

        declared_to_2, declared_by_2 = await db.get_alliance_declarations_for(2)
        assert declared_to_2 == {1}
        assert declared_by_2 == {1}

    async def test_declarations_scoped_per_pair(self, db: Database):
        await db.toggle_alliance_declaration(1, 2)
        await db.toggle_alliance_declaration(1, 3)

        declared_to, _ = await db.get_alliance_declarations_for(1)
        assert declared_to == {2, 3}

        declared_to_2, declared_by_2 = await db.get_alliance_declarations_for(2)
        assert declared_to_2 == set()
        assert declared_by_2 == {1}

    async def test_empty_for_unknown_uid(self, db: Database):
        declared_to, declared_by = await db.get_alliance_declarations_for(42)
        assert declared_to == set()
        assert declared_by == set()
