"""Global game state — values that persist across empires/services.

Currently holds end_criterion_activated, set once when the end-game
condition triggers.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

_end_criterion_activated: Optional[datetime] = None


def get_end_criterion_activated() -> Optional[datetime]:
    return _end_criterion_activated


def try_set_end_criterion_activated(dt: Optional[datetime] = None) -> bool:
    """Set end_criterion_activated if not already set.

    Args:
        dt: The activation time. Defaults to now (UTC) if None.

    Returns:
        True if the value was set, False if it was already set.
    """
    global _end_criterion_activated
    if _end_criterion_activated is not None:
        return False
    _end_criterion_activated = dt or datetime.now(timezone.utc)
    return True


def restore_end_criterion_activated(dt: Optional[datetime]) -> None:
    """Called on startup to restore the persisted value. Does not guard against overwrite."""
    global _end_criterion_activated
    _end_criterion_activated = dt
