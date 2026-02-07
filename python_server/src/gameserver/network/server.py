"""WebSocket server — manages client connections.

Accepts WebSocket connections, handles connection lifecycle,
and dispatches incoming messages to the router.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from gameserver.network.router import Router


class Server:
    """asyncio WebSocket server.

    Args:
        host: Bind address.
        port: Bind port.
        router: Message router for dispatching incoming messages.
    """

    def __init__(self, router: Router, host: str = "0.0.0.0", port: int = 8765) -> None:
        self._router = router
        self._host = host
        self._port = port
        self._connections: dict[int, object] = {}  # uid → websocket

    async def start(self) -> None:
        """Start the WebSocket server."""
        # TODO: implement with websockets library
        pass

    async def send_to(self, uid: int, data: dict) -> None:
        """Send a message to a specific connected client."""
        # TODO: implement
        pass

    async def broadcast(self, uids: set[int], data: dict) -> None:
        """Send a message to multiple clients."""
        # TODO: implement
        pass
