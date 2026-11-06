"""Global game state — values that persist across empires/services.

Currently holds end_criterion_activated, set once when the end-game
condition triggers.
"""

from __future__ import annotations

from datetime import datetime, time, timedelta, timezone
from typing import TYPE_CHECKING, Optional
from zoneinfo import ZoneInfo

if TYPE_CHECKING:
    from gameserver.loaders.game_config_loader import GameConfig

_NEXT_SEASON_TZ = ZoneInfo("Europe/Berlin")
_NEXT_SEASON_WEEKDAY = 4  # Friday (datetime.weekday())
_NEXT_SEASON_TIME = time(14, 0)
_NEXT_SEASON_MIN_DAYS_AFTER_RALLY_START = 14

_end_criterion_activated: Optional[datetime] = None
_eras_first_reached: set[str] = set()  # era keys already claimed by some empire
_end_criterion_empire_uid: Optional[int] = None
_end_criterion_empire_name: str = ""
_season_number: int = 1
_season_title: str = ""
_this_season_start_date: str = ""  # ISO-8601 UTC start of the currently running season
_next_season_start: str = ""
_next_season_title: str = ""
_game_frozen: bool = False
_season_wipe_time: float = 0.0  # unix timestamp of last empire wipe
_season_snapshot_done: bool = False
_season_wipe_done: bool = False  # wipe already performed for the pending season transition
_season_leadtime: Optional[float] = None  # None = use game.yaml default


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


def clear_end_criterion() -> None:
    """Reset end criterion state after a season wipe."""
    global _end_criterion_activated, _end_criterion_empire_uid, _end_criterion_empire_name
    _end_criterion_activated = None
    _end_criterion_empire_uid = None
    _end_criterion_empire_name = ""


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


def get_season_number() -> int:
    return _season_number


def get_season_title() -> str:
    return _season_title


def get_next_season_start() -> str:
    return _next_season_start


def get_this_season_start_date() -> str:
    """ISO-8601 UTC timestamp of when the currently running season started."""
    return _this_season_start_date


def set_this_season_start_date(value: str) -> None:
    global _this_season_start_date
    _this_season_start_date = value


def parse_iso_utc(value: str) -> Optional[datetime]:
    """Parse an ISO-8601 timestamp as UTC. Returns None if empty or malformed."""
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value)
    except (ValueError, OverflowError):
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def get_next_season_leadtime(season_leadtime: float) -> str:
    """Leadtime is derived: next_season_start minus season_leadtime seconds.

    Returns the ISO-8601 UTC leadtime, or "" if next_season_start is unset/malformed.
    """
    start = parse_iso_utc(_next_season_start)
    if start is None:
        return ""
    return (start - timedelta(seconds=season_leadtime)).isoformat()


def default_next_season_start(rally_start: datetime) -> str:
    """First Friday 14:00 Berlin time at least 14 days after the rally started.

    Returns an ISO-8601 UTC timestamp.
    """
    earliest = (
        rally_start + timedelta(days=_NEXT_SEASON_MIN_DAYS_AFTER_RALLY_START)
    ).astimezone(_NEXT_SEASON_TZ)
    days_ahead = (_NEXT_SEASON_WEEKDAY - earliest.weekday()) % 7
    candidate = datetime.combine(
        earliest.date() + timedelta(days=days_ahead),
        _NEXT_SEASON_TIME,
        tzinfo=_NEXT_SEASON_TZ,
    )
    if candidate < earliest:
        candidate += timedelta(days=7)  # wall-clock arithmetic, stays 14:00 across DST
    return candidate.astimezone(timezone.utc).isoformat()


def get_next_season_title() -> str:
    return _next_season_title


def set_season(
    _number: int,
    _title: str,
    _next_start: str = "",
    _next_title: str = "",
) -> None:
    global _season_number, _season_title, _next_season_start, _next_season_title
    _season_number = _number
    _season_title = _title
    _next_season_start = _next_start
    _next_season_title = _next_title


def is_season_reset_triggered() -> bool:
    return _game_frozen


def set_season_reset_triggered(value: bool) -> None:
    global _game_frozen
    _game_frozen = value


def get_season_wipe_time() -> float:
    return _season_wipe_time


def set_season_wipe_time(t: float) -> None:
    global _season_wipe_time
    _season_wipe_time = t


def is_season_snapshot_done() -> bool:
    return _season_snapshot_done


def set_season_snapshot_done(value: bool) -> None:
    global _season_snapshot_done
    _season_snapshot_done = value


def is_season_wipe_done() -> bool:
    return _season_wipe_done


def set_season_wipe_done(value: bool) -> None:
    global _season_wipe_done
    _season_wipe_done = value


def get_season_leadtime() -> Optional[float]:
    return _season_leadtime


def set_season_leadtime(value: Optional[float]) -> None:
    global _season_leadtime
    _season_leadtime = value


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


def reset() -> None:
    """Reset all module-level state to defaults.

    Intended for test isolation — global_state is a bag of module globals, so
    tests that exercise the season/end-criterion flow must start from a clean
    slate regardless of what ran before them.
    """
    global _end_criterion_activated, _eras_first_reached
    global _end_criterion_empire_uid, _end_criterion_empire_name
    global _season_number, _season_title, _this_season_start_date
    global _next_season_start, _next_season_title, _game_frozen
    global _season_wipe_time, _season_snapshot_done, _season_leadtime, _season_wipe_done
    _end_criterion_activated = None
    _eras_first_reached = set()
    _end_criterion_empire_uid = None
    _end_criterion_empire_name = ""
    _season_number = 1
    _season_title = ""
    _this_season_start_date = ""
    _next_season_start = ""
    _next_season_title = ""
    _game_frozen = False
    _season_wipe_time = 0.0
    _season_snapshot_done = False
    _season_wipe_done = False
    _season_leadtime = None


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
