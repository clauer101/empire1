"""Tests for tower sell refund on map save."""

import pytest

from gameserver.models.empire import Empire
from gameserver.models.messages import MapSaveRequest
from gameserver.network.handlers import handle_map_save_request
from gameserver.main import Services


@pytest.fixture
def mock_services():
    from gameserver.engine.empire_service import EmpireService
    from gameserver.engine.upgrade_provider import UpgradeProvider
    from gameserver.util.events import EventBus
    from gameserver.loaders.item_loader import load_items

    svc = Services()
    svc.event_bus = EventBus()
    items = load_items()
    svc.upgrade_provider = UpgradeProvider()
    svc.upgrade_provider.load(items)
    svc.empire_service = EmpireService(svc.upgrade_provider, svc.event_bus)

    empire = Empire(uid=42, name="TestEmpire")
    empire.resources = {"gold": 10000.0}
    svc.empire_service.register(empire)
    return svc


def _patch(svc):
    import gameserver.network.handlers
    gameserver.network.handlers._services = svc


def _empire(svc) -> Empire:
    return svc.empire_service.get(42)


def _base_map():
    return {"0,0": "spawnpoint", "1,0": "path", "2,0": "castle"}


def _cheapest_tower(svc) -> tuple[str, float]:
    """Return (iid, gold_cost) for the cheapest tower in the catalog."""
    from gameserver.models.items import ItemType
    candidates = [
        (item.iid, item.costs.get("gold", 0.0))
        for item in svc.upgrade_provider.get_by_type(ItemType.STRUCTURE)
        if item.costs.get("gold", 0.0) > 0
    ]
    return min(candidates, key=lambda x: x[1])


@pytest.mark.asyncio
async def test_sell_tower_refunds_gold(mock_services):
    """Selling a tower refunds the correct fraction of its build cost."""
    _patch(mock_services)
    tower_iid, tower_cost = _cheapest_tower(mock_services)

    # Place tower on an extra tile
    map_with_tower = {**_base_map(), "3,0": tower_iid}
    msg = MapSaveRequest(type="map_save_request", tiles=map_with_tower)
    resp = await handle_map_save_request(msg, sender_uid=42)
    assert resp["success"], resp.get("error")

    gold_after_buy = _empire(mock_services).resources["gold"]
    assert gold_after_buy == pytest.approx(10000.0 - tower_cost, abs=0.01)

    # Sell tower: replace tile with empty
    map_without_tower = {**_base_map(), "3,0": "empty"}
    msg2 = MapSaveRequest(type="map_save_request", tiles=map_without_tower)
    resp2 = await handle_map_save_request(msg2, sender_uid=42)
    assert resp2["success"], resp2.get("error")

    cfg = mock_services.empire_service._gc
    refund_rate = getattr(cfg, "tower_sell_refund", 0.5)
    expected_gold = gold_after_buy + tower_cost * refund_rate
    assert _empire(mock_services).resources["gold"] == pytest.approx(expected_gold, abs=0.01)


@pytest.mark.asyncio
async def test_sell_tower_no_double_refund(mock_services):
    """Removing two different towers gives independent refunds."""
    _patch(mock_services)
    tower_iid, tower_cost = _cheapest_tower(mock_services)

    map_with_two = {**_base_map(), "3,0": tower_iid, "4,0": tower_iid}
    msg = MapSaveRequest(type="map_save_request", tiles=map_with_two)
    resp = await handle_map_save_request(msg, sender_uid=42)
    assert resp["success"], resp.get("error")
    gold_after_buy = _empire(mock_services).resources["gold"]

    map_sell_one = {**_base_map(), "3,0": "empty", "4,0": tower_iid}
    msg2 = MapSaveRequest(type="map_save_request", tiles=map_sell_one)
    resp2 = await handle_map_save_request(msg2, sender_uid=42)
    assert resp2["success"], resp2.get("error")

    cfg = mock_services.empire_service._gc
    refund_rate = getattr(cfg, "tower_sell_refund", 0.5)
    expected = gold_after_buy + tower_cost * refund_rate
    assert _empire(mock_services).resources["gold"] == pytest.approx(expected, abs=0.01)


@pytest.mark.asyncio
async def test_replace_tower_charges_new_and_refunds_old(mock_services):
    """Replacing a tower on the same tile refunds the old and charges the new."""
    _patch(mock_services)
    from gameserver.models.items import ItemType

    # Pick two different towers
    candidates = sorted(
        [(item.iid, item.costs.get("gold", 0.0))
         for item in mock_services.upgrade_provider.get_by_type(ItemType.STRUCTURE)
         if item.costs.get("gold", 0.0) > 0],
        key=lambda x: x[1],
    )
    if len(candidates) < 2:
        pytest.skip("Need at least 2 towers with gold cost")
    tower_a_iid, cost_a = candidates[0]
    tower_b_iid, cost_b = candidates[1]

    map_a = {**_base_map(), "3,0": tower_a_iid}
    await handle_map_save_request(MapSaveRequest(type="map_save_request", tiles=map_a), sender_uid=42)
    gold_after_a = _empire(mock_services).resources["gold"]

    map_b = {**_base_map(), "3,0": tower_b_iid}
    resp = await handle_map_save_request(MapSaveRequest(type="map_save_request", tiles=map_b), sender_uid=42)
    assert resp["success"], resp.get("error")

    cfg = mock_services.empire_service._gc
    refund_rate = getattr(cfg, "tower_sell_refund", 0.5)
    expected = gold_after_a + cost_a * refund_rate - cost_b
    assert _empire(mock_services).resources["gold"] == pytest.approx(expected, abs=0.01)
