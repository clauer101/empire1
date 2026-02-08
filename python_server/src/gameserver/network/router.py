"""Message router — dispatches incoming messages to handlers.

Replaces the Java acceptRequest() pattern. Routes messages by type
to the appropriate service handler.

Handlers are async callables that receive the parsed message and
the sender UID. They may return an optional response dict that should
be sent back to the sender.
"""

from __future__ import annotations

import logging
from typing import Any, Callable, Awaitable, Optional

from gameserver.models.messages import GameMessage, parse_message

log = logging.getLogger(__name__)

# Handler signature: async (message, sender_uid) -> optional response dict
Handler = Callable[[GameMessage, int], Awaitable[Optional[dict[str, Any]]]]


class Router:
    """Message dispatcher.

    Register handlers for message types, then call route() with raw dicts.
    Handlers may return a response dict to be sent back to the caller.
    """

    def __init__(self) -> None:
        self._handlers: dict[str, Handler] = {}

    def register(self, msg_type: str, handler: Handler) -> None:
        """Register a handler for a message type.

        Args:
            msg_type: The message type string (e.g. ``"summary_request"``).
            handler: Async callable ``(message, sender_uid) -> dict | None``.
        """
        self._handlers[msg_type] = handler
        log.debug("Handler registered: %s", msg_type)

    @property
    def registered_types(self) -> list[str]:
        """List of all message types that have a handler."""
        return list(self._handlers.keys())

    async def route(self, raw: dict[str, Any], sender_uid: int) -> Optional[dict[str, Any]]:
        """Parse and dispatch a raw message dict.

        Args:
            raw: Raw JSON-decoded message dictionary.
            sender_uid: UID of the sending client.

        Returns:
            Response dict from the handler, or None if no handler /
            handler returned nothing.
        """
        message = parse_message(raw)
        handler = self._handlers.get(message.type)
        if handler is None:
            log.debug("No handler for message type: %s", message.type)
            return None
        return await handler(message, sender_uid)
