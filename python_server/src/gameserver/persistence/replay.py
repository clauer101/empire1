"""Battle replay — records and stores battle replays.

Records all battle events (critter spawns, shots, deaths) as a timeline
and saves them for later playback.
"""

from __future__ import annotations

from typing import Any


class ReplayRecorder:
    """Records battle events for replay.

    Args:
        bid: Battle ID being recorded.
    """

    def __init__(self, bid: int) -> None:
        self.bid = bid
        self._events: list[dict[str, Any]] = []

    def record(self, timestamp_ms: float, event: dict[str, Any]) -> None:
        """Record a battle event with timestamp."""
        self._events.append({"t": timestamp_ms, **event})

    async def save(self, path: str | None = None) -> None:
        """Save the replay to disk."""
        # TODO: implement
        pass
