"""Battle replay — records and stores battle replays.

Records all battle events (setup, updates, summary) as a timeline
and saves them as JSON for later playback.

File format (replays/{bid}.json):
    {
        "bid": 42,
        "defender_uid": 4,
        "attacker_uid": 0,
        "created_at": 1774415000.0,
        "events": [
            {"t": 0, "type": "battle_setup", ...},
            {"t": 250, "type": "battle_update", ...},
            ...
            {"t": 95000, "type": "battle_summary", ...}
        ]
    }
"""

from __future__ import annotations

import json
import logging
import os
import time
from pathlib import Path
from typing import Any

log = logging.getLogger(__name__)

DEFAULT_REPLAY_DIR = "replays"
REPLAY_MAX_AGE_DAYS = 7


class ReplayRecorder:
    """Records battle events for replay.

    Args:
        bid: Battle ID being recorded.
        defender_uid: UID of the defending player.
        attacker_uid: UID of the attacking player.
        replay_dir: Directory to save replay files.
    """

    def __init__(self, bid: int, defender_uid: int = 0,
                 attacker_uid: int = 0,
                 replay_dir: str = DEFAULT_REPLAY_DIR) -> None:
        self.bid = bid
        self.defender_uid = defender_uid
        self.attacker_uid = attacker_uid
        self._replay_dir = Path(replay_dir)
        self._events: list[dict[str, Any]] = []

    def record(self, timestamp_ms: float, event: dict[str, Any]) -> None:
        """Record a battle event with timestamp."""
        self._events.append({"t": timestamp_ms, **event})

    def save(self) -> Path | None:
        """Save the replay to disk as JSON. Returns the file path or None on error."""
        self._replay_dir.mkdir(parents=True, exist_ok=True)
        target = self._replay_dir / f"{self.bid}.json"
        tmp = target.with_suffix(".tmp")
        payload = {
            "bid": self.bid,
            "defender_uid": self.defender_uid,
            "attacker_uid": self.attacker_uid,
            "created_at": time.time(),
            "events": self._events,
        }
        try:
            tmp.write_text(json.dumps(payload, separators=(",", ":")), encoding="utf-8")
            tmp.replace(target)
            log.info("Replay saved: %s (%d events)", target, len(self._events))
            return target
        except Exception:
            log.exception("Failed to save replay %s", target)
            if tmp.exists():
                tmp.unlink(missing_ok=True)
            return None


def load_replay(bid: int, replay_dir: str = DEFAULT_REPLAY_DIR) -> dict[str, Any] | None:
    """Load a replay from disk by battle ID. Returns parsed JSON or None."""
    path = Path(replay_dir) / f"{bid}.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        log.exception("Failed to load replay %s", path)
        return None


def list_replays(replay_dir: str = DEFAULT_REPLAY_DIR) -> list[dict[str, Any]]:
    """List available replays (metadata only, no events)."""
    d = Path(replay_dir)
    if not d.is_dir():
        return []
    result = []
    for f in sorted(d.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        try:
            raw = json.loads(f.read_text(encoding="utf-8"))
            result.append({
                "bid": raw.get("bid"),
                "defender_uid": raw.get("defender_uid"),
                "attacker_uid": raw.get("attacker_uid"),
                "created_at": raw.get("created_at"),
                "event_count": len(raw.get("events", [])),
            })
        except Exception:
            continue
    return result


def cleanup_old_replays(replay_dir: str = DEFAULT_REPLAY_DIR,
                        max_age_days: int = REPLAY_MAX_AGE_DAYS) -> int:
    """Delete replay files older than max_age_days. Returns count deleted."""
    d = Path(replay_dir)
    if not d.is_dir():
        return 0
    cutoff = time.time() - max_age_days * 86400
    deleted = 0
    for f in d.glob("*.json"):
        try:
            if f.stat().st_mtime < cutoff:
                f.unlink()
                deleted += 1
        except Exception:
            continue
    if deleted:
        log.info("Replay cleanup: deleted %d files older than %d days", deleted, max_age_days)
    return deleted
