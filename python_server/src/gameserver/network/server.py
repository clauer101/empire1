"""WebSocket server — manages client connections.

Accepts WebSocket connections, handles connection lifecycle,
and dispatches incoming messages to the router.
Uses the ``websockets`` library with asyncio.
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Optional, TYPE_CHECKING

import websockets
from websockets.asyncio.server import ServerConnection, Server as WSServer

if TYPE_CHECKING:
    from gameserver.network.router import Router

log = logging.getLogger(__name__)


class Server:
    """asyncio WebSocket server with session tracking.

    Each connected client goes through:
    1. WebSocket handshake
    2. First message must be ``{"type": "auth_request", ...}`` or
       the connection is assigned a guest/debug UID.
    3. Messages are routed via the Router; responses sent back.

    Args:
        router: Message router for dispatching incoming messages.
        host: Bind address.
        port: Bind port.
    """

    def __init__(self, router: Router, host: str = "0.0.0.0", port: int = 8765,
                 ping_interval: int = 30, ping_timeout: int = 10,
                 max_size: int = 1_048_576) -> None:
        self._router = router
        self._host = host
        self._port = port
        self._ping_interval = ping_interval
        self._ping_timeout = ping_timeout
        self._max_size = max_size
        self._connections: dict[int, ServerConnection] = {}  # uid → ws
        self._ws_to_uid: dict[int, int] = {}  # id(ws) → uid
        self._server: Optional[WSServer] = None
        self._next_guest_uid = -1  # negative UIDs for unauthenticated

    # -- Lifecycle -------------------------------------------------------

    async def start(self) -> None:
        """Start the WebSocket server."""
        self._server = await websockets.serve(
            self._on_connect,
            self._host,
            self._port,
            origins=None,  # Accept any origin (matches REST CORS policy)
            ping_interval=self._ping_interval,
            ping_timeout=self._ping_timeout,
            max_size=self._max_size,
        )
        log.info("WebSocket server listening on ws://%s:%d", self._host, self._port)

    async def stop(self) -> None:
        """Stop the WebSocket server and close all connections."""
        if self._server is not None:
            self._server.close()
            await self._server.wait_closed()
            log.info("WebSocket server stopped")

    # -- Session management ----------------------------------------------

    def register_session(self, uid: int, ws: ServerConnection) -> None:
        """Bind a UID to a WebSocket connection (called after auth).

        Handles two cases:
        1. **Session upgrade** (guest → real UID): removes the old guest
           UID entry so it doesn't linger in ``_connections``.
        2. **Supersede** (same UID, different ws): closes the old ws
           with code 1008.
        """
        # 1) Clean up old guest UID mapping for this ws (guest → real upgrade)
        old_uid = self._ws_to_uid.get(id(ws))
        if old_uid is not None and old_uid != uid:
            self._connections.pop(old_uid, None)
            log.debug("Cleaned up old guest mapping: uid=%d for ws=%s", old_uid, id(ws))

        # 2) Close any *other* ws that currently owns this UID (different device)
        old_ws = self._connections.get(uid)
        if old_ws is not None and old_ws is not ws:
            log.info("Superseding existing session: uid=%d", uid)
            asyncio.ensure_future(old_ws.close(1008, "Superseded by new connection"))

        self._connections[uid] = ws
        self._ws_to_uid[id(ws)] = uid
        log.info("Session registered: uid=%d", uid)

    def unregister_session(self, ws: ServerConnection) -> Optional[int]:
        """Remove a WebSocket from the session table. Returns the UID.

        Only removes the ``_connections`` entry if this *ws* is still the
        active connection for the UID.  This prevents a disconnecting old
        session from removing a newer session that has already taken over
        the same UID (the root cause of the multi-device login bug).
        """
        uid = self._ws_to_uid.pop(id(ws), None)
        if uid is not None:
            # Only remove from _connections if *this* ws is still the registered one
            if self._connections.get(uid) is ws:
                self._connections.pop(uid, None)
            else:
                log.info("Session unregister: uid=%d already taken over by new connection — keeping", uid)
        return uid

    def get_uid(self, ws: ServerConnection) -> Optional[int]:
        """Look up the UID for a WebSocket connection."""
        return self._ws_to_uid.get(id(ws))

    @property
    def connected_uids(self) -> list[int]:
        """List of all connected UIDs."""
        return sorted(self._connections.keys())

    @property
    def connection_count(self) -> int:
        return len(self._connections)

    # -- Sending ---------------------------------------------------------

    async def send_to(self, uid: int, data: dict[str, Any]) -> bool:
        """Send a message to a specific connected client.

        Returns True if the message was sent, False if client not connected.
        """
        ws = self._connections.get(uid)
        if ws is None:
            return False
        try:
            raw = json.dumps(data, ensure_ascii=False, default=str)
            await ws.send(raw)
            return True
        except websockets.ConnectionClosed:
            log.debug("send_to uid=%d failed — connection closed", uid)
            return False

    async def broadcast(self, uids: set[int], data: dict[str, Any]) -> int:
        """Send a message to multiple clients.

        Returns the number of clients that received the message.
        """
        raw = json.dumps(data, ensure_ascii=False, default=str)
        sent = 0
        for uid in uids:
            ws = self._connections.get(uid)
            if ws is None:
                continue
            try:
                await ws.send(raw)
                sent += 1
            except websockets.ConnectionClosed:
                pass
        return sent

    async def broadcast_all(self, data: dict[str, Any]) -> int:
        """Send a message to ALL connected clients."""
        return await self.broadcast(set(self._connections.keys()), data)

    # -- Connection handler ----------------------------------------------

    async def _on_connect(self, ws: ServerConnection) -> None:
        """Handle a new WebSocket connection lifecycle.

        If the client provides a ``?token=<jwt>`` query parameter, the
        connection is immediately authenticated with the real UID from
        the token.  Otherwise a temporary negative guest UID is assigned
        (legacy behaviour).
        """
        # Check for JWT token in query string
        initial_uid: int | None = None
        try:
            req = ws.request
            if req and req.path:
                from urllib.parse import urlparse, parse_qs
                qs = parse_qs(urlparse(req.path).query)
                token_list = qs.get("token")
                if token_list:
                    from gameserver.network.jwt_auth import verify_token
                    initial_uid = verify_token(token_list[0])
                    log.info("WS authenticated via JWT: uid=%d", initial_uid)
        except Exception as e:
            log.debug("JWT WS auth failed (%s) — falling back to guest", e)

        if initial_uid is not None:
            guest_uid = initial_uid
        else:
            guest_uid = self._next_guest_uid
            self._next_guest_uid -= 1

        self.register_session(guest_uid, ws)
        remote = ws.remote_address

        # Log request headers for debugging (iOS subprotocol issues)
        try:
            req = ws.request
            if req and hasattr(req, 'headers'):
                ua = req.headers.get('User-Agent', '(unknown)')
                origin = req.headers.get('Origin', '(none)')
                subproto = req.headers.get('Sec-WebSocket-Protocol', '(none)')
                log.info(
                    "Client connected: uid=%d remote=%s UA=%s origin=%s subprotocol=%s",
                    guest_uid, remote, ua[:80], origin, subproto,
                )
            else:
                log.info("Client connected: uid=%d remote=%s (no request headers)", guest_uid, remote)
        except Exception:
            log.info("Client connected: uid=%d remote=%s", guest_uid, remote)

        try:
            async for raw_msg in ws:
                await self._handle_message(ws, raw_msg)
        except websockets.ConnectionClosed as e:
            real_uid = self.get_uid(ws) or guest_uid
            log.info(
                "Client disconnected: uid=%d code=%s reason=%s remote=%s",
                real_uid, e.code, e.reason or "(none)", remote,
            )
        except Exception as e:
            real_uid = self.get_uid(ws) or guest_uid
            log.error(
                "Client connection error: uid=%d remote=%s error=%s",
                real_uid, remote, e,
            )
        else:
            # async for exited normally = clean close, no exception
            real_uid = self.get_uid(ws) or guest_uid
            log.info(
                "Client closed cleanly: uid=%d remote=%s",
                real_uid, remote,
            )
        finally:
            removed_uid = self.unregister_session(ws)
            log.info("Session removed: uid=%s", removed_uid)

    async def _handle_message(self, ws: ServerConnection, raw_msg: Any) -> None:
        """Parse and route a single incoming message."""
        uid = self.get_uid(ws) or 0

        # Parse JSON
        if isinstance(raw_msg, bytes):
            raw_msg = raw_msg.decode("utf-8")
        try:
            data = json.loads(raw_msg)
        except json.JSONDecodeError as e:
            await ws.send(json.dumps({
                "type": "error",
                "message": f"Invalid JSON: {e}",
            }))
            return

        if not isinstance(data, dict):
            await ws.send(json.dumps({
                "type": "error",
                "message": "Message must be a JSON object",
            }))
            return

        # Preserve request_id for response correlation
        request_id = data.get("request_id")
        msg_type = data.get("type", "")
        log.debug("Received: type=%s uid=%d", msg_type, uid)

        # Route through the Router
        try:
            response = await self._router.route(data, uid)
        except Exception as exc:
            log.exception("Handler error: type=%s uid=%d", msg_type, uid)
            error_resp: dict[str, Any] = {
                "type": "error",
                "message": str(exc),
            }
            if request_id is not None:
                error_resp["request_id"] = request_id
            await ws.send(json.dumps(error_resp))
            return

        # Send response back to sender if handler returned one
        if response is not None:
            if request_id is not None:
                response["request_id"] = request_id
            await ws.send(json.dumps(response, ensure_ascii=False, default=str))
            
            # After successful auth, re-register the session with the real UID
            if msg_type == "auth_request" and response.get("success") and response.get("uid"):
                real_uid = response["uid"]
                self.register_session(real_uid, ws)
                log.info("Session upgraded: guest=%s → uid=%d", uid, real_uid)
