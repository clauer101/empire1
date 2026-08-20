"""Integration tests for buy_tile_request handler."""

import asyncio
from pathlib import Path

import pytest

from gameserver.models.empire import Empire
from gameserver.network.handlers import handle_buy_tile_request
from gameserver.network.rest_api import _stub_message
from gameserver.main import Services


@pytest.fixture(autouse=True)
def _reset_season_freeze():
    """global_state.game_frozen is a module-level global — another test in
    the full suite may leave it True, which would short-circuit every
    handler in this file before its own validation ever runs (see the same
    pattern/rationale in test_routers.py's buy-upgrade tests)."""
    from gameserver.engine.global_state import set_season_reset_triggered
    set_season_reset_triggered(False)
    yield
    set_season_reset_triggered(False)


@pytest.fixture
def mock_services():
    """Create minimal mock services with one empire owning a single tile."""
    from gameserver.engine.empire_service import EmpireService
    from gameserver.engine.upgrade_provider import UpgradeProvider
    from gameserver.util.events import EventBus
    from gameserver.loaders.item_loader import load_items

    svc = Services()
    svc.event_bus = EventBus()

    config_dir = Path(__file__).resolve().parent.parent / "config"
    items = load_items(config_dir)
    svc.upgrade_provider = UpgradeProvider()
    svc.upgrade_provider.load(items)
    svc.empire_service = EmpireService(svc.upgrade_provider, svc.event_bus)

    empire = Empire(
        uid=42,
        name="TestEmpire",
        resources={"gold": 10_000_000.0, "culture": 0.0, "life": 10.0},
        hex_map={"0,0": "castle"},
    )
    svc.empire_service.register(empire)
    return svc


@pytest.mark.asyncio
async def test_buy_tile_success_deducts_gold_and_claims_tile(mock_services):
    import gameserver.network.handlers
    gameserver.network.handlers._services = mock_services

    empire = mock_services.empire_service.get(42)
    gold_before = empire.resources["gold"]

    msg = _stub_message(q=1, r=0)
    response = await handle_buy_tile_request(msg, sender_uid=42)

    assert response["success"] is True
    assert empire.hex_map["1,0"] == "empty"
    assert empire.resources["gold"] < gold_before


@pytest.mark.asyncio
async def test_buy_tile_already_owned_rejected_no_gold_charged(mock_services):
    """Buying an already-owned tile is rejected and gold is left untouched."""
    import gameserver.network.handlers
    gameserver.network.handlers._services = mock_services

    empire = mock_services.empire_service.get(42)
    gold_before = empire.resources["gold"]

    # 0,0 is already 'castle', not void.
    msg = _stub_message(q=0, r=0)
    response = await handle_buy_tile_request(msg, sender_uid=42)

    assert response["success"] is False
    assert "not a void tile" in response["error"]
    assert empire.resources["gold"] == gold_before


@pytest.mark.asyncio
async def test_buy_tile_not_adjacent_rejected_no_gold_charged(mock_services):
    import gameserver.network.handlers
    gameserver.network.handlers._services = mock_services

    empire = mock_services.empire_service.get(42)
    gold_before = empire.resources["gold"]

    msg = _stub_message(q=50, r=50)
    response = await handle_buy_tile_request(msg, sender_uid=42)

    assert response["success"] is False
    assert "adjacent" in response["error"]
    assert empire.resources["gold"] == gold_before


@pytest.mark.asyncio
async def test_buy_tile_owned_by_another_empire_rejected_no_gold_charged(mock_services):
    import gameserver.network.handlers
    gameserver.network.handlers._services = mock_services

    neighbor = Empire(uid=43, name="Neighbor", hex_map={"1,0": "empty"})
    mock_services.empire_service.register(neighbor)

    empire = mock_services.empire_service.get(42)
    gold_before = empire.resources["gold"]

    msg = _stub_message(q=1, r=0)
    response = await handle_buy_tile_request(msg, sender_uid=42)

    assert response["success"] is False
    assert "belongs to another empire" in response["error"]
    assert empire.resources["gold"] == gold_before


@pytest.mark.asyncio
async def test_concurrent_duplicate_buy_requests_only_charge_gold_once(mock_services):
    """Regression test for the prod double-charge incident (2026-08-01, uid=26):
    two racing buy_tile requests for the same tile must not both succeed —
    the second must see the tile as already owned and charge no gold.
    """
    import gameserver.network.handlers
    gameserver.network.handlers._services = mock_services

    empire = mock_services.empire_service.get(42)
    gold_before = empire.resources["gold"]

    msg1 = _stub_message(q=1, r=0)
    msg2 = _stub_message(q=1, r=0)

    responses = await asyncio.gather(
        handle_buy_tile_request(msg1, sender_uid=42),
        handle_buy_tile_request(msg2, sender_uid=42),
    )

    successes = [r for r in responses if r["success"]]
    failures = [r for r in responses if not r["success"]]

    assert len(successes) == 1
    assert len(failures) == 1
    assert "not a void tile" in failures[0]["error"]

    gold_spent = gold_before - empire.resources["gold"]
    assert gold_spent == successes[0]["cost"]


@pytest.mark.asyncio
async def test_buy_tile_rejected_while_season_frozen(mock_services):
    """No map changes while a season transition has frozen the game."""
    from gameserver.engine import global_state
    import gameserver.network.handlers
    gameserver.network.handlers._services = mock_services

    global_state.set_season_reset_triggered(True)
    try:
        empire = mock_services.empire_service.get(42)
        gold_before = empire.resources["gold"]

        msg = _stub_message(q=1, r=0)
        response = await handle_buy_tile_request(msg, sender_uid=42)

        assert response["success"] is False
        assert "frozen" in response["error"].lower()
        assert "1,0" not in empire.hex_map
        assert empire.resources["gold"] == gold_before
    finally:
        global_state.set_season_reset_triggered(False)


@pytest.mark.asyncio
async def test_mutation_lock_serializes_interleaved_check_then_act(mock_services):
    """Directly proves EmpireService.mutation_lock() provides the mutual
    exclusion handle_buy_tile_request relies on.

    handle_buy_tile_request itself has no internal await, so two calls
    started via asyncio.gather never actually interleave inside it — each
    runs to completion once started, which is why the test above passes
    even without the lock. In production, two independent ASGI request
    tasks reach the "call the handler" point via their own scheduling, and
    can interleave *before* either enters the handler body — a window this
    in-process test can't reproduce by calling the handler directly. This
    test instead forces that interleaving explicitly (via a real await
    inside the critical section) to confirm the lock — not incidental
    non-preemption — is what prevents two racing check-then-act sequences
    from both reading state 'before' the other's write.
    """
    lock = mock_services.empire_service.mutation_lock(42)
    log: list[str] = []

    async def critical_section(tag: str) -> None:
        async with lock:
            log.append(f"{tag}:enter")
            await asyncio.sleep(0)  # force a real yield mid-critical-section
            log.append(f"{tag}:exit")

    await asyncio.gather(critical_section("A"), critical_section("B"))

    # Without the lock, both "enter" events could land before either "exit"
    # (A:enter, B:enter, A:exit, B:exit). With the lock, one task's full
    # enter/exit pair must complete before the other's enter.
    assert log in (["A:enter", "A:exit", "B:enter", "B:exit"],
                   ["B:enter", "B:exit", "A:enter", "A:exit"])
