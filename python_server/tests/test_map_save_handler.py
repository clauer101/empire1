"""Integration tests for map_save_request handler validation."""

from pathlib import Path

import pytest

from gameserver.models.empire import Empire
from gameserver.models.messages import MapSaveRequest
from gameserver.network.handlers import handle_map_save_request
from gameserver.main import Services


@pytest.fixture
def mock_services():
    """Create minimal mock services."""
    from gameserver.engine.empire_service import EmpireService
    from gameserver.engine.upgrade_provider import UpgradeProvider
    from gameserver.util.events import EventBus
    from gameserver.loaders.item_loader import load_items

    svc = Services()
    svc.event_bus = EventBus()

    # Load items for upgrade provider
    config_dir = Path(__file__).resolve().parent.parent / "config"
    items = load_items(config_dir)
    svc.upgrade_provider = UpgradeProvider()
    svc.upgrade_provider.load(items)
    svc.empire_service = EmpireService(svc.upgrade_provider, svc.event_bus)
    
    # Add a test empire
    empire = Empire(uid=42, name="TestEmpire")
    svc.empire_service.register(empire)
    return svc


@pytest.mark.asyncio
async def test_map_save_valid_simple(mock_services):
    """Valid simple map saves successfully."""
    # Import and patch globalbhandlers._services
    import gameserver.network.handlers
    gameserver.network.handlers._services = mock_services
    
    message = MapSaveRequest(
        type="map_save_request",
        tiles={
            "0,0": "spawnpoint",
            "1,0": "path",
            "2,0": "castle",
        }
    )
    
    response = await handle_map_save_request(message, sender_uid=42)
    assert response["success"] is True
    assert mock_services.empire_service.get(42).hex_map == message.tiles


@pytest.mark.asyncio
async def test_map_save_invalid_no_castle(mock_services):
    """Map without castle is rejected."""
    import gameserver.network.handlers
    gameserver.network.handlers._services = mock_services
    
    message = MapSaveRequest(
        type="map_save_request",
        tiles={
            "0,0": "spawnpoint",
            "1,0": "path",
        }
    )
    
    response = await handle_map_save_request(message, sender_uid=42)
    assert response["success"] is False
    assert "Kein Castle" in response["error"]


@pytest.mark.asyncio
async def test_map_save_invalid_multiple_castles(mock_services):
    """Map with multiple castles is rejected."""
    import gameserver.network.handlers
    gameserver.network.handlers._services = mock_services
    
    message = MapSaveRequest(
        type="map_save_request",
        tiles={
            "0,0": "spawnpoint",
            "1,0": "castle",
            "2,0": "castle",
        }
    )
    
    response = await handle_map_save_request(message, sender_uid=42)
    assert response["success"] is False
    assert "at most 1 castle" in response["error"]


@pytest.mark.asyncio
async def test_map_save_invalid_no_path(mock_services):
    """Map with disconnected spawn and castle is rejected."""
    import gameserver.network.handlers
    gameserver.network.handlers._services = mock_services
    
    message = MapSaveRequest(
        type="map_save_request",
        tiles={
            "0,0": "spawnpoint",
            "5,0": "path",
            "10,10": "castle",
        }
    )
    
    response = await handle_map_save_request(message, sender_uid=42)
    assert response["success"] is False
    assert "Weg verbaut" in response["error"]


@pytest.mark.asyncio
async def test_map_save_rejects_tile_owned_by_another_empire(mock_services):
    """Claiming a void-for-me tile that another empire already owns is rejected.

    Regression test: handle_map_save_request previously only checked the
    submitting empire's own previous hex_map for void tiles, never the global
    world_tile_owner() index — so the map editor could claim a neighbor's
    tile in one save, unlike handle_buy_tile_request which already checked
    this correctly for single-tile purchases.
    """
    import gameserver.network.handlers
    gameserver.network.handlers._services = mock_services

    neighbor = Empire(uid=43, name="Neighbor", hex_map={"5,0": "empty"})
    mock_services.empire_service.register(neighbor)

    message = MapSaveRequest(
        type="map_save_request",
        tiles={
            "0,0": "spawnpoint",
            "1,0": "path",
            "2,0": "castle",
            "5,0": "empty",  # already owned by uid=43
        },
    )

    response = await handle_map_save_request(message, sender_uid=42)
    assert response["success"] is False
    assert "belongs to another empire" in response["error"]


@pytest.mark.asyncio
async def test_map_save_during_battle_returns_frozen_path_not_recomputed(mock_services):
    """During an active battle, saving the map (e.g. selling a tower) must return
    the battle's frozen critter_path, never a path recomputed from the
    just-saved tiles — critters mid-battle keep walking the original route
    for the rest of the battle even if the new tile layout would produce a
    different (e.g. shorter) path.
    """
    import gameserver.network.handlers
    gameserver.network.handlers._services = mock_services

    from gameserver.models.battle import BattleState
    from gameserver.models.hex import HexCoord
    import gameserver.network.handlers._core as _core

    empire = mock_services.empire_service.get(42)
    frozen_path = [HexCoord(0, 0), HexCoord(1, 0), HexCoord(2, 0), HexCoord(3, 0)]
    battle = BattleState(bid=1, defender=empire, critter_path=frozen_path)
    _core._active_battles[42] = battle

    try:
        message = MapSaveRequest(
            type="map_save_request",
            tiles={
                "0,0": "spawnpoint",
                "1,0": "path",
                "2,0": "castle",
            },
        )
        response = await handle_map_save_request(message, sender_uid=42)
    finally:
        _core._active_battles.pop(42, None)

    assert response["success"] is True
    assert response["path"] == [[c.q, c.r] for c in frozen_path]


@pytest.mark.asyncio
async def test_map_save_empire_not_found(mock_services):
    """Nonexistent empire returns error."""
    import gameserver.network.handlers
    gameserver.network.handlers._services = mock_services
    
    message = MapSaveRequest(
        type="map_save_request",
        tiles={
            "0,0": "spawnpoint",
            "1,0": "castle",
        }
    )
    
    response = await handle_map_save_request(message, sender_uid=999)
    assert response["success"] is False
    assert "No empire found" in response["error"]
