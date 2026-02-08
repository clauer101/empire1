"""Integration tests for map_save_request handler validation."""

import pytest

from gameserver.models.empire import Empire
from gameserver.models.messages import MapSaveRequest
from gameserver.network.handlers import handle_map_save_request
from gameserver.services import Services
from gameserver.network.handlers import _services as handlers_services


@pytest.fixture
def mock_services():
    """Create minimal mock services."""
    svc = Services()
    # Add a test empire
    empire = Empire(uid=42, name="TestEmpire")
    svc.empire_service._empires[42] = empire
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
    assert "exactly 1 castle" in response["error"]


@pytest.mark.asyncio
async def test_map_save_invalid_no_spawnpoint(mock_services):
    """Map without spawnpoint is rejected."""
    import gameserver.network.handlers
    gameserver.network.handlers._services = mock_services
    
    message = MapSaveRequest(
        type="map_save_request",
        tiles={
            "0,0": "path",
            "1,0": "castle",
        }
    )
    
    response = await handle_map_save_request(message, sender_uid=42)
    assert response["success"] is False
    assert "at least 1 spawnpoint" in response["error"]


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
    assert "exactly 1 castle" in response["error"]


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
    assert "No passable path" in response["error"]


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
