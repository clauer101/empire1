"""Season archive — read-only access to finished-season snapshots.

At the end of every season ``GameLoop._take_season_snapshot()`` copies the
live ``state.yaml`` to ``<data_dir>/results/season<N>/state.yaml`` before all
empires are wiped. Those snapshots are the only record of what a player
achieved in a past season, and this module reads the part the eternal
ranking needs: culture and empire name per uid.

Snapshots are immutable once written, so every file is parsed at most once
per server process and kept in a module-level cache keyed by
``(mtime, size)``.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

try:  # libyaml is ~10x faster and is present in the runtime image
    from yaml import CSafeLoader as _Loader
except ImportError:  # pragma: no cover - pure-python fallback
    from yaml import SafeLoader as _Loader  # type: ignore[assignment]

log = logging.getLogger(__name__)

# Overwritten at startup in main._start() to point at the persisted data dir
DEFAULT_RESULTS_DIR = "data/results"


@dataclass
class SeasonCulture:
    """Culture and names of one finished season, keyed by empire uid."""

    season_number: int
    season_title: str
    culture_by_uid: dict[int, float] = field(default_factory=dict)
    name_by_uid: dict[int, str] = field(default_factory=dict)
    bots: set[int] = field(default_factory=set)


# path -> (mtime, size, parsed snapshot)
_cache: dict[str, tuple[float, int, SeasonCulture]] = {}


def _parse_snapshot(path: Path) -> SeasonCulture | None:
    """Parse one season snapshot. Returns None if it is unreadable or malformed."""
    from gameserver.engine.ai_service import AI_UID

    try:
        raw = yaml.load(path.read_text(encoding="utf-8"), Loader=_Loader)
    except (OSError, yaml.YAMLError):
        log.exception("Season archive: could not read %s — skipping", path)
        return None
    if not isinstance(raw, dict):
        log.warning("Season archive: %s is not a mapping — skipping", path)
        return None

    global_dict = raw.get("global") or {}
    raw_number: Any = global_dict.get("season_number")
    try:
        season_number = int(raw_number)
    except (TypeError, ValueError):
        log.warning("Season archive: %s has no usable season_number — skipping", path)
        return None

    result = SeasonCulture(
        season_number=season_number,
        season_title=str(global_dict.get("season_title") or ""),
    )
    for empire in raw.get("empires") or []:
        if not isinstance(empire, dict):
            continue
        raw_uid: Any = empire.get("uid")
        try:
            uid = int(raw_uid)
        except (TypeError, ValueError):
            continue
        if uid == AI_UID:
            continue  # the AI out-cultures every player by an order of magnitude
        culture = (empire.get("resources") or {}).get("culture", 0.0)
        try:
            result.culture_by_uid[uid] = float(culture)
        except (TypeError, ValueError):
            result.culture_by_uid[uid] = 0.0
        result.name_by_uid[uid] = str(empire.get("name") or "")
        if empire.get("is_bot"):
            result.bots.add(uid)
    return result


def _load_cached(path: Path) -> SeasonCulture | None:
    """Parse ``path``, reusing the cached result while the file is unchanged."""
    try:
        stat = path.stat()
    except OSError:
        log.warning("Season archive: cannot stat %s — skipping", path)
        return None
    key = str(path)
    cached = _cache.get(key)
    if cached is not None and cached[0] == stat.st_mtime and cached[1] == stat.st_size:
        return cached[2]
    parsed = _parse_snapshot(path)
    if parsed is not None:
        _cache[key] = (stat.st_mtime, stat.st_size, parsed)
    return parsed


def load_finished_seasons(
    current_season: int,
    *,
    current_season_ended: bool = False,
) -> list[SeasonCulture]:
    """Return every archived season that is over, oldest first.

    A snapshot is identified by the ``season_number`` stored inside it, not by
    its folder name — that keeps the in-progress season out of the result and
    ignores stray folders left over from testing.

    The season counter only advances when the *next* season starts, which can
    be days after the running one actually ended. ``current_season_ended``
    (the caller passes the season wipe flag) closes that gap: once the empires
    have been wiped, the snapshot carrying the current number counts as
    finished too. Before the wipe it must not — the empires still hold that
    culture live, and counting both would double it.
    """
    results_dir = Path(DEFAULT_RESULTS_DIR)
    if not results_dir.is_dir():
        return []

    last_finished = current_season if current_season_ended else current_season - 1
    seasons: dict[int, SeasonCulture] = {}
    for state_path in sorted(results_dir.glob("season*/state.yaml")):
        parsed = _load_cached(state_path)
        if parsed is None or parsed.season_number > last_finished:
            continue
        seasons[parsed.season_number] = parsed
    return [seasons[n] for n in sorted(seasons)]


def clear_cache() -> None:
    """Drop the parsed-snapshot cache (tests)."""
    _cache.clear()

