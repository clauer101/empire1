"""Regression test: era-3 auto-granted artifacts must record a real
acquisition timestamp in the DB, not a bogus epoch-zero value.

Bug: `_maybe_grant_artifact_for_era3` called
`database.record_artifact_acquired(uid, iid, 0.0)` — a literal `0.0`, which
the DB stores as Unix epoch 1970-01-01. The "Longest Artifact Hold" season
stat (`now - acquired_at`) then reported ~56 YEARS of hold time for any
empire that received an era-3 grant, dwarfing all real (stolen-artifact)
entries on the leaderboard.
"""
from __future__ import annotations

import asyncio
import time
from unittest.mock import AsyncMock, MagicMock

import pytest

from gameserver.engine.empire_service import EmpireService
from gameserver.loaders.game_config_loader import GameConfig
from gameserver.models.empire import Empire
from gameserver.models.items import ItemDetails, ItemType
from gameserver.util.events import EventBus

ARTIFACT_IID = "TEST_ARTIFACT"


@pytest.fixture
def upgrade_provider():
    from gameserver.engine.upgrade_provider import UpgradeProvider
    provider = UpgradeProvider()
    provider.load([
        ItemDetails(iid=ARTIFACT_IID, item_type=ItemType.ARTIFACT, effort=0.0, effects={}),
    ])
    return provider


@pytest.fixture
def service(upgrade_provider):
    gc = GameConfig()
    gc.accounts_per_artifact = 1  # force the grant condition to trigger
    svc = EmpireService(upgrade_provider, EventBus(), gc)
    svc._database = MagicMock()
    svc._database.record_artifact_acquired = AsyncMock()
    svc._database.record_empire_stat_max = AsyncMock()
    svc._database.send_message = AsyncMock()
    return svc


async def test_era3_grant_records_real_timestamp_not_zero(service, monkeypatch):
    empire = Empire(uid=1, name="Test")
    service.register(empire)
    # Grant logic gates on era >= bronze; a fresh Empire starts at "stone".
    monkeypatch.setattr(service, "get_current_era", lambda e: "bronze")

    before = time.time()
    await service._maybe_grant_artifact_for_era3(empire)
    await _drain_pending_tasks()
    after = time.time()

    service._database.record_artifact_acquired.assert_awaited_once()
    call_args = service._database.record_artifact_acquired.call_args
    recorded_uid, recorded_iid, recorded_ts = call_args.args
    assert recorded_uid == 1
    assert recorded_iid == ARTIFACT_IID
    # Must be a real "now" timestamp, not the 0.0 (1970 epoch) bug value.
    assert recorded_ts != 0.0
    assert before <= recorded_ts <= after


async def test_era3_grant_db_timestamp_matches_in_memory_acquired_at(service, monkeypatch):
    """The SQL-side timestamp and the in-memory ISO string must agree —
    they're two representations of the same acquisition moment."""
    empire = Empire(uid=1, name="Test")
    service.register(empire)
    monkeypatch.setattr(service, "get_current_era", lambda e: "bronze")

    await service._maybe_grant_artifact_for_era3(empire)
    await _drain_pending_tasks()

    recorded_ts = service._database.record_artifact_acquired.call_args.args[2]
    iso_str = empire.artifact_acquired_at[ARTIFACT_IID]
    from datetime import datetime
    iso_ts = datetime.fromisoformat(iso_str).timestamp()
    assert abs(iso_ts - recorded_ts) < 1.0


async def _drain_pending_tasks() -> None:
    """Await background tasks spawned via create_task (the DB write)."""
    current = asyncio.current_task()
    pending = [t for t in asyncio.all_tasks() if t is not current and not t.done()]
    if pending:
        await asyncio.gather(*pending, return_exceptions=True)


async def test_era3_grant_skips_artifact_held_by_other_empire(service, monkeypatch):
    """Artifacts are unique: the grant must not duplicate one another empire holds.

    Bug: candidates only excluded the receiving empire's own artifacts, so a
    relic already held elsewhere could be granted again. Once both copies were
    stolen into one empire it held the same artifact twice (double effects).
    """
    holder = Empire(uid=2, name="Holder", artifacts=[ARTIFACT_IID])
    empire = Empire(uid=1, name="Test")
    service.register(holder)
    service.register(empire)
    monkeypatch.setattr(service, "get_current_era", lambda e: "bronze")

    await service._maybe_grant_artifact_for_era3(empire)
    await _drain_pending_tasks()

    assert empire.artifacts == []
    service._database.record_artifact_acquired.assert_not_awaited()



async def test_era3_grant_records_peak_artifacts_held(service, monkeypatch):
    empire = Empire(uid=1, name="Test")
    service.register(empire)
    monkeypatch.setattr(service, "get_current_era", lambda e: "bronze")

    await service._maybe_grant_artifact_for_era3(empire)
    await _drain_pending_tasks()

    service._database.record_empire_stat_max.assert_awaited_once_with(1, "peak_artifacts_held", 1)
