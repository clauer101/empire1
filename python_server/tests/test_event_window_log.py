"""Tests for the generic event-window tracker in persistence/database.py.

Covers record_window_event / count_recent_window_events /
get_active_window_event_keys / get_window_event_stats_for_key — the shared
substrate for skip-siege abuse detection and BotDetector's timing signal.
"""

from __future__ import annotations

import pytest

from gameserver.persistence.database import Database


@pytest.fixture
async def db() -> Database:
    database = Database(":memory:")
    await database.connect()
    yield database
    await database.close()


class TestRecordAndCount:
    async def test_counts_recent_events(self, db: Database):
        now = 1_000_000
        for i in range(4):
            await db.record_window_event("skip_siege", 20, now + i)
        count = await db.count_recent_window_events("skip_siege", 20, now - 100)
        assert count == 4

    async def test_events_outside_window_not_counted(self, db: Database):
        now = 1_000_000
        await db.record_window_event("skip_siege", 20, now - 200)  # old, outside window
        await db.record_window_event("skip_siege", 20, now)  # recent
        count = await db.count_recent_window_events("skip_siege", 20, since_ts=now - 100)
        assert count == 1

    async def test_different_key_not_counted(self, db: Database):
        now = 1_000_000
        await db.record_window_event("skip_siege", 20, now)
        await db.record_window_event("skip_siege", 21, now)  # different key_uid
        count = await db.count_recent_window_events("skip_siege", 20, since_ts=now - 100)
        assert count == 1

    async def test_different_kind_not_counted(self, db: Database):
        """Two kinds sharing the same key_uid must not cross-contaminate counts —
        the main new risk from sharing one table across event families."""
        now = 1_000_000
        await db.record_window_event("skip_siege", 20, now)
        await db.record_window_event("api_call", 20, now)  # same key_uid, different kind
        count = await db.count_recent_window_events("skip_siege", 20, since_ts=now - 100)
        assert count == 1

    async def test_record_prunes_old_rows_for_key(self, db: Database):
        now = 1_000_000
        await db.record_window_event("skip_siege", 20, now - 200_000)  # older than 48h prune window
        await db.record_window_event("skip_siege", 20, now)  # triggers the prune
        count = await db.count_recent_window_events("skip_siege", 20, since_ts=0)
        assert count == 1

    async def test_prune_scoped_to_same_kind_and_key(self, db: Database):
        now = 1_000_000
        await db.record_window_event("skip_siege", 20, now - 200_000)
        await db.record_window_event("api_call", 20, now)  # different kind — must not prune the skip_siege row
        count = await db.count_recent_window_events("skip_siege", 20, since_ts=0)
        assert count == 1


class TestGetActiveWindowEventKeys:
    async def test_below_threshold_not_returned(self, db: Database):
        await db.record_window_event("skip_siege", 20, 1000)
        await db.record_window_event("skip_siege", 20, 1010)
        active = await db.get_active_window_event_keys("skip_siege", since_ts=0, threshold=5)
        assert active == []

    async def test_at_threshold_returned_with_stats(self, db: Database):
        for i, ts in enumerate([1000, 1010, 1020, 1030, 1040]):
            await db.record_window_event("skip_siege", 20, ts, ref_id=10 + (i % 2), magnitude=90.0 - i)
        active = await db.get_active_window_event_keys("skip_siege", since_ts=0, threshold=5)
        assert len(active) == 1
        a = active[0]
        assert a["key_uid"] == 20
        assert a["event_count"] == 5
        assert a["last_ts"] == 1040
        assert a["mean_interval_s"] == 10.0
        assert a["stddev_interval_s"] == 0.0
        assert a["max_magnitude"] == 90.0
        assert a["distinct_ref_ids"] == 2

    async def test_sorted_by_count_desc(self, db: Database):
        for ts in [1000, 1010, 1020, 1030, 1040]:
            await db.record_window_event("skip_siege", 20, ts)
        for ts in [1000, 1010, 1020, 1030, 1040, 1050]:
            await db.record_window_event("skip_siege", 21, ts)
        active = await db.get_active_window_event_keys("skip_siege", since_ts=0, threshold=5)
        assert [a["key_uid"] for a in active] == [21, 20]

    async def test_only_matches_requested_kind(self, db: Database):
        for ts in [1000, 1010, 1020, 1030, 1040]:
            await db.record_window_event("api_call", 20, ts)
        active = await db.get_active_window_event_keys("skip_siege", since_ts=0, threshold=5)
        assert active == []

    async def test_no_magnitude_yields_none(self, db: Database):
        for ts in [1000, 1010, 1020, 1030, 1040]:
            await db.record_window_event("api_call", 20, ts)
        active = await db.get_active_window_event_keys("api_call", since_ts=0, threshold=5)
        assert active[0]["max_magnitude"] is None
        assert active[0]["distinct_ref_ids"] == 0


class TestGetWindowEventStatsForKey:
    async def test_returns_none_when_no_events(self, db: Database):
        stats = await db.get_window_event_stats_for_key("api_call", 99, since_ts=0)
        assert stats is None

    async def test_returns_stats_for_single_key(self, db: Database):
        for ts in [1000, 1010, 1020]:
            await db.record_window_event("api_call", 42, ts)
        stats = await db.get_window_event_stats_for_key("api_call", 42, since_ts=0)
        assert stats is not None
        assert stats["key_uid"] == 42
        assert stats["event_count"] == 3
        assert stats["mean_interval_s"] == 10.0
        assert stats["stddev_interval_s"] == 0.0

    async def test_ignores_other_keys(self, db: Database):
        for ts in [1000, 1010, 1020]:
            await db.record_window_event("api_call", 42, ts)
        await db.record_window_event("api_call", 43, 1005)
        stats = await db.get_window_event_stats_for_key("api_call", 42, since_ts=0)
        assert stats["event_count"] == 3
