"""Global game state — values that persist across empires/services.

Currently holds end_criterion_activated, set once when the end-game
condition triggers.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from gameserver.loaders.game_config_loader import GameConfig

_end_criterion_activated: Optional[datetime] = None
_eras_first_reached: set[str] = set()  # era keys already claimed by some empire
_end_criterion_empire_uid: Optional[int] = None
_end_criterion_empire_name: str = ""


def get_end_criterion_activated() -> Optional[datetime]:
    return _end_criterion_activated


def get_end_criterion_empire_uid() -> Optional[int]:
    return _end_criterion_empire_uid


def get_end_criterion_empire_name() -> str:
    return _end_criterion_empire_name


def try_set_end_criterion_activated(
    dt: Optional[datetime] = None,
    empire_uid: Optional[int] = None,
    empire_name: str = "",
) -> bool:
    """Set end_criterion_activated if not already set.

    Args:
        dt: The activation time. Defaults to now (UTC) if None.
        empire_uid: UID of the empire that triggered the rally.
        empire_name: Display name of that empire.

    Returns:
        True if the value was set, False if it was already set.
    """
    global _end_criterion_activated, _end_criterion_empire_uid, _end_criterion_empire_name
    if _end_criterion_activated is not None:
        return False
    _end_criterion_activated = dt or datetime.now(timezone.utc)
    _end_criterion_empire_uid = empire_uid
    _end_criterion_empire_name = empire_name
    return True


def restore_end_criterion_activated(
    dt: Optional[datetime],
    empire_uid: Optional[int] = None,
    empire_name: str = "",
) -> None:
    """Called on startup to restore the persisted value. Does not guard against overwrite."""
    global _end_criterion_activated, _end_criterion_empire_uid, _end_criterion_empire_name
    _end_criterion_activated = dt
    _end_criterion_empire_uid = empire_uid
    _end_criterion_empire_name = empire_name


def try_claim_first_era(era_key: str) -> bool:
    """Return True (and record it) if this era has not been reached by anyone yet."""
    global _eras_first_reached
    if era_key in _eras_first_reached:
        return False
    _eras_first_reached.add(era_key)
    return True


def restore_first_eras(era_keys: set[str]) -> None:
    """Called on startup to restore persisted first-era claims."""
    global _eras_first_reached
    _eras_first_reached = set(era_keys)


def is_end_rally_active(cfg: GameConfig) -> bool:
    """Return True if the end rally has been triggered and has not yet expired."""
    if _end_criterion_activated is None:
        return False
    elapsed = (datetime.now(timezone.utc) - _end_criterion_activated).total_seconds()
    return elapsed < cfg.end_rally_duration


def end_rally_seconds_remaining(cfg: GameConfig) -> float:
    """Seconds until the end rally expires. Returns 0.0 if not active."""
    if _end_criterion_activated is None:
        return 0.0
    elapsed = (datetime.now(timezone.utc) - _end_criterion_activated).total_seconds()
    return max(0.0, cfg.end_rally_duration - elapsed)
