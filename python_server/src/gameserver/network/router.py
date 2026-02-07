"""Message router — dispatches incoming messages to handlers.

Replaces the Java acceptRequest() pattern. Routes messages by type
to the appropriate service handler.
"""

from __future__ import annotations

from typing import Any, Callable, Awaitable

from gameserver.models.messages import GameMessage, parse_message


class Router:
    """Message dispatcher.

    Register handlers for message types, then call route() with raw dicts.
    """

    def __init__(self) -> None:
        self._handlers: dict[str, Callable[[GameMessage, int], Awaitable[None]]] = {}

    def register(
        self, msg_type: str, handler: Callable[[GameMessage, int], Awaitable[None]]
    ) -> None:
        """Register a handler for a message type.

        Args:
            msg_type: The message type string.
            handler: Async callable(message, sender_uid).
        """
        self._handlers[msg_type] = handler

    async def route(self, raw: dict[str, Any], sender_uid: int) -> None:
        """Parse and dispatch a raw message dict.

        Args:
            raw: Raw JSON-decoded message dictionary.
            sender_uid: UID of the sending client.
        """
        message = parse_message(raw)
        handler = self._handlers.get(message.type)
        if handler:
            await handler(message, sender_uid)
