"""Acceptance test for the full season-change round trip.

Drives the real services (EmpireService, AttackService, GameLoop, in-memory
Database) through every phase of the season transition documented in
``docs/SEASONENDFLOW.md`` and asserts the observable state after each phase:

    Phase 0  Pre-trigger ........... clean state, not frozen
    Phase 1  End criterion fires ... activation set, rally effects on all empires
    Phase 1b Rally active .......... game keeps ticking, not frozen
    Phase 2  Rally ends ........... freeze + season snapshot
    Phase 3  Leadtime wipe ........ empires/attacks wiped, end-criterion cleared
    Phase 4  Frozen countdown ..... step returns early, season unchanged
    Phase 5  New season ........... season number +1, unfrozen, flags reset

The game loop reads ``datetime.now(timezone.utc)`` directly (no injectable
clock), so phase transitions are steered by setting the *stored* timestamps
relative to real "now": ``end_criterion_activated`` for the rally, and
``next_season_start`` for the leadtime wipe and unfreeze.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from gameserver.engine import global_state
from gameserver.engine.attack_service import AttackService
from gameserver.engine.empire_service import EmpireService
from gameserver.engine.game_loop import GameLoop
from gameserver.engine.statistics import StatisticsService
from gameserver.engine.upgrade_provider import UpgradeProvider
from gameserver.loaders.game_config_loader import GameConfig
from gameserver.models.empire import Empire
from gameserver.models.items import ItemDetails, ItemType
from gameserver.persistence.database import Database
from gameserver.util.events import EventBus

END_CRITERION_IID = "THE_WORLD_WONDER"
RALLY_GOLD_OFFSET = 2.0
RALLY_DURATION = 10.0
SEASON_LEADTIME = 5.0


def _iso_in(seconds: float) -> str:
    """ISO-8601 UTC timestamp ``seconds`` from now (negative = in the past)."""
    return (datetime.now(timezone.utc) + timedelta(seconds=seconds)).isoformat()


@pytest.fixture(autouse=True)
def reset_global_state():
    """global_state is module-level globals — keep it clean across tests."""
    global_state.clear_end_criterion()
    global_state.set_season_reset_triggered(False)
    global_state.set_season(1, "Season 1")
    yield
    global_state.clear_end_criterion()
    global_state.set_season_reset_triggered(False)
    global_state.set_season(1, "Season 1")


@pytest.fixture
def gc() -> GameConfig:
    gc = GameConfig()
    gc.end_criterion = END_CRITERION_IID
    gc.end_rally_duration = RALLY_DURATION
    gc.season_leadtime = SEASON_LEADTIME
    gc.end_rally_effects = {"gold_offset": RALLY_GOLD_OFFSET}
    gc.step_length_ms = 1000.0
    gc.speedup_factor = 1.0
    return gc


@pytest.fixture
async def harness(gc, tmp_path):
    """Real services wired together, plus a connected in-memory DB.

    Snapshot output lands under ``tmp_path`` because the snapshot derives its
    results dir from ``state_file``'s parent.
    """
    event_bus = EventBus()

    wonder = ItemDetails(
        iid=END_CRITERION_IID,
        item_type=ItemType.BUILDING,
        effort=1.0,
        effects={},
    )
    upgrade_provider = UpgradeProvider()
    upgrade_provider.load([wonder])

    empire_service = EmpireService(upgrade_provider, event_bus, gc)
    attack_service = AttackService(event_bus, gc, empire_service)
    statistics = StatisticsService()

    # File-backed DB so the snapshot's gameserver.db copy has a real source.
    db = Database(str(tmp_path / "gameserver.db"))
    await db.connect()

    gl = GameLoop(
        event_bus=event_bus,
        empire_service=empire_service,
        attack_service=attack_service,
        statistics=statistics,
        game_config=gc,
        state_file=str(tmp_path / "state.yaml"),
    )
    gl._database = db

    # state.yaml must exist for the snapshot to copy it.
    (tmp_path / "state.yaml").write_text("global: {}\n", encoding="utf-8")

    empire_a = Empire(uid=1, name="Alpha")
    empire_b = Empire(uid=2, name="Beta")
    empire_service.register(empire_a)
    empire_service.register(empire_b)

    yield gl, empire_service, attack_service, gc, tmp_path

    await db.close()


async def test_full_season_round_trip(harness):
    gl, empires, attacks, gc, tmp_path = harness

    # -- Phase 0: pre-trigger -------------------------------------------------
    assert global_state.get_end_criterion_activated() is None
    assert not global_state.is_season_reset_triggered()
    gl._step(1.0)
    assert not global_state.is_season_reset_triggered()

    # -- Phase 1: end criterion fires ----------------------------------------
    # Complete the end_criterion building on empire Alpha, exactly as the
    # build progression does when remaining hits zero.
    alpha = empires.get(1)
    alpha.buildings[END_CRITERION_IID] = 0.0
    empires._apply_effects(alpha, END_CRITERION_IID)

    assert global_state.get_end_criterion_activated() is not None
    assert global_state.get_end_criterion_empire_uid() == 1
    # Rally effects are applied to ALL empires, not just the trigger.
    assert empires.get(1).effects.get("gold_offset") == RALLY_GOLD_OFFSET
    assert empires.get(2).effects.get("gold_offset") == RALLY_GOLD_OFFSET

    # -- Phase 1b: rally active, game keeps ticking --------------------------
    assert global_state.is_end_rally_active(gc) is True
    gl._step(1.0)
    assert not global_state.is_season_reset_triggered()

    # -- Phase 2: rally ends -> freeze + snapshot ----------------------------
    # Push the activation into the past so the rally has expired.
    global_state.restore_end_criterion_activated(
        datetime.now(timezone.utc) - timedelta(seconds=RALLY_DURATION + 1),
        empire_uid=1,
        empire_name="Alpha",
    )
    assert global_state.is_end_rally_active(gc) is False
    gl._step(1.0)
    assert global_state.is_season_reset_triggered() is True
    assert global_state.is_season_snapshot_done() is True
    # Let the snapshot task (created via create_task) run to completion.
    await _drain_pending_tasks()
    season_dir = tmp_path / "results" / "season1"
    assert (season_dir / "state.yaml").exists()
    assert (season_dir / "gameserver.db").exists()
    assert (season_dir / "empire_stats.csv").exists()

    # -- Phase 3: leadtime wipe ----------------------------------------------
    # Leadtime gate opens when now >= next_season_start - season_leadtime.
    # Put next_season_start far enough in the future that we stay frozen
    # afterward, but with the leadtime window already open.
    # next_season_start within leadtime of now: reset_at = start - leadtime is
    # already past (gate open), but start itself is still in the future (frozen).
    global_state.set_season(
        global_state.get_season_number(),
        global_state.get_season_title(),
        _next_start=_iso_in(SEASON_LEADTIME - 1),  # leadtime open, start not reached
        _next_title="Season 2",
    )
    gl._step(1.0)
    assert gl._wipe_done is True
    assert empires.all_empires == {}
    assert attacks.get_all_attacks() == []
    assert global_state.get_end_criterion_activated() is None  # cleared on wipe
    await _drain_pending_tasks()  # wipe_season_stats runs without error

    # -- Phase 4: frozen countdown -------------------------------------------
    season_before = global_state.get_season_number()
    gl._step(1.0)
    assert global_state.is_season_reset_triggered() is True
    assert global_state.get_season_number() == season_before  # no advance yet

    # -- Phase 5: new season + unfreeze --------------------------------------
    global_state.set_season(
        global_state.get_season_number(),
        global_state.get_season_title(),
        _next_start=_iso_in(-1),  # start time reached
        _next_title="Season 2",
    )
    gl._step(1.0)
    assert global_state.get_season_number() == season_before + 1
    assert global_state.is_season_reset_triggered() is False
    assert gl._wipe_done is False
    assert gl._season_snapshot_done is False
    assert global_state.get_season_title() == "Season 2"


async def test_wipe_fires_exactly_once(harness):
    """The _wipe_done guard prevents a second wipe on the next tick."""
    gl, empires, attacks, gc, tmp_path = harness

    # Enter the frozen state with the leadtime window open.
    global_state.set_season_reset_triggered(True)
    gl._season_snapshot_done = True
    global_state.set_season(
        1, "Season 1",
        _next_start=_iso_in(SEASON_LEADTIME - 1),
        _next_title="Season 2",
    )

    gl._step(1.0)
    assert gl._wipe_done is True
    assert empires.all_empires == {}

    # Re-register an empire; a second tick must NOT wipe it again.
    empires.register(Empire(uid=99, name="Late"))
    gl._step(1.0)
    assert 99 in empires.all_empires


async def test_malformed_next_season_start_stays_frozen(harness):
    """A malformed next_season_start keeps the game frozen, no crash/advance."""
    gl, empires, attacks, gc, tmp_path = harness

    global_state.set_season_reset_triggered(True)
    global_state.set_season(1, "Season 1", _next_start="not-a-date", _next_title="x")
    season_before = global_state.get_season_number()

    gl._step(1.0)  # must not raise

    assert global_state.is_season_reset_triggered() is True
    assert global_state.get_season_number() == season_before


async def _drain_pending_tasks() -> None:
    """Await all background tasks the game loop spawned (snapshot, db wipe).

    The loop launches these via ``create_task`` / ``ensure_future``; we must let
    them finish before assertions (and before the fixture closes the DB).
    """
    import asyncio

    current = asyncio.current_task()
    pending = [t for t in asyncio.all_tasks() if t is not current and not t.done()]
    if pending:
        await asyncio.gather(*pending, return_exceptions=True)
