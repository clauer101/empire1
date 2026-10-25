"""Battle replay — records and stores battle replays.

Records all battle events (setup, updates, summary) as a timeline and
streams them to disk incrementally so an in-progress battle never has to
hold its full event history in memory.

On-disk format (replays/{YYYYMMDD_HHMMSS}_{bid}.ndjson.gz):
    gzip-compressed newline-delimited JSON. The first line is a header
    object, every following line is one event:
        {"bid": 42, "replay_key": "...", "defender_uid": 4, ...}
        {"t": 0, "type": "battle_setup", ...}
        {"t": 250, "type": "battle_update", ...}
        ...
        {"t": 95000, "type": "battle_summary", ...}

    Buffered events are flushed to disk every FLUSH_INTERVAL_MS of battle
    time (and once more on final save()), each flush appending a new gzip
    member — concatenated gzip members decompress transparently as one
    stream, so no read-modify-write of prior data is ever needed.

    Replays written before this format existed are plain single-JSON
    gzip files (*.json.gz) with a top-level "events" array; load_replay()
    and get_replay_path() still read those for backward compatibility.
"""

from __future__ import annotations

import datetime
import gzip
import json
import logging
import time
from pathlib import Path
from typing import Any

log = logging.getLogger(__name__)

DEFAULT_REPLAY_DIR = "data/replays"
REPLAY_MAX_AGE_DAYS = 7

# How often (in battle elapsed time) buffered events are flushed to disk.
# Bounds the in-memory event buffer to at most one flush interval's worth
# of events, regardless of total battle duration.
FLUSH_INTERVAL_MS = 15 * 60 * 1000.0


class ReplayRecorder:
    """Records battle events for replay, flushing to disk periodically.

    Args:
        bid: Battle ID being recorded.
        defender_uid: UID of the defending player.
        attacker_uid: UID of the attacking player.
        replay_dir: Directory to save replay files.
    """

    def __init__(self, bid: int, defender_uid: int = 0,
                 attacker_uid: int = 0,
                 attacker_uids: list[int] | None = None,
                 replay_dir: str = DEFAULT_REPLAY_DIR) -> None:
        self.bid = bid
        self.defender_uid = defender_uid
        self.attacker_uid = attacker_uid
        self.attacker_uids: list[int] = attacker_uids if attacker_uids is not None else ([attacker_uid] if attacker_uid else [])
        self._replay_dir = Path(replay_dir)
        self.created_at = time.time()
        dt = datetime.datetime.utcfromtimestamp(self.created_at)
        self.replay_key = dt.strftime("%Y%m%d_%H%M%S") + f"_{bid}"

        self._ndjson_path = self._replay_dir / f"{self.replay_key}.ndjson.gz"
        self._events: list[dict[str, Any]] = []  # buffered, not yet flushed to disk
        self._header_written = False
        self._flushed_event_count = 0
        self._last_flush_elapsed_ms = 0.0

    @classmethod
    def from_existing(cls, replay_key: str, bid: int,
                      defender_uid: int = 0, attacker_uid: int = 0,
                      attacker_uids: list[int] | None = None,
                      replay_dir: str = DEFAULT_REPLAY_DIR) -> "ReplayRecorder":
        """Resume recording into an existing partial replay file.

        Continues appending to the same on-disk NDJSON file rather than
        reloading prior events into memory — resuming a very long battle
        must not re-introduce the unbounded-memory problem this class
        exists to avoid.
        """
        rec = cls.__new__(cls)
        rec.bid = bid
        rec.defender_uid = defender_uid
        rec.attacker_uid = attacker_uid
        rec.attacker_uids = attacker_uids if attacker_uids is not None else ([attacker_uid] if attacker_uid else [])
        rec._replay_dir = Path(replay_dir)
        rec.replay_key = replay_key
        rec.created_at = time.time()
        rec._ndjson_path = rec._replay_dir / f"{replay_key}.ndjson.gz"
        rec._events = []
        rec._flushed_event_count = 0
        rec._last_flush_elapsed_ms = 0.0

        if rec._ndjson_path.exists():
            rec._header_written = True
            rec._flushed_event_count = max(0, _count_ndjson_lines(rec._ndjson_path) - 1)
            log.info("ReplayRecorder resumed: key=%s (%d previously flushed events, appending)",
                     replay_key, rec._flushed_event_count)
        else:
            rec._header_written = False
            legacy = load_replay(replay_key, replay_dir)
            if legacy:
                log.warning(
                    "ReplayRecorder resumed: key=%s has a legacy .json.gz partial "
                    "(%d events) — new events continue in a fresh ndjson stream; "
                    "legacy events are preserved on disk but not merged",
                    replay_key, len(legacy.get("events", [])),
                )
            else:
                log.info("ReplayRecorder resumed (no existing file): key=%s", replay_key)
        return rec

    def record(self, timestamp_ms: float, event: dict[str, Any]) -> None:
        """Record a battle event with timestamp."""
        self._events.append({"t": timestamp_ms, **event})

    def maybe_flush(self, elapsed_ms: float) -> None:
        """Flush buffered events to disk once FLUSH_INTERVAL_MS has elapsed.

        Call this periodically (e.g. once per broadcast) from the battle
        loop. Keeps the in-memory buffer bounded for arbitrarily long
        battles instead of accumulating the whole event history in RAM.
        """
        if elapsed_ms - self._last_flush_elapsed_ms >= FLUSH_INTERVAL_MS:
            self.flush()
            self._last_flush_elapsed_ms = elapsed_ms

    def flush(self) -> None:
        """Append buffered events to disk as NDJSON and clear the buffer."""
        if not self._events:
            return
        self._replay_dir.mkdir(parents=True, exist_ok=True)

        lines: list[str] = []
        if not self._header_written:
            header = {
                "bid": self.bid,
                "replay_key": self.replay_key,
                "defender_uid": self.defender_uid,
                "attacker_uid": self.attacker_uid,
                "attacker_uids": self.attacker_uids,
                "created_at": self.created_at,
            }
            lines.append(json.dumps(header, separators=(",", ":")))
            self._header_written = True
        lines.extend(json.dumps(ev, separators=(",", ":")) for ev in self._events)
        payload = ("\n".join(lines) + "\n").encode("utf-8")

        try:
            with gzip.open(self._ndjson_path, "ab", compresslevel=6) as f:
                f.write(payload)
        except Exception:
            log.exception("Failed to flush replay %s", self._ndjson_path)
            return

        self._flushed_event_count += len(self._events)
        log.debug("[replay] bid=%d flushed %d events (total flushed: %d)",
                  self.bid, len(self._events), self._flushed_event_count)
        self._events = []

    def save(self) -> Path | None:
        """Flush any remaining buffered events and return the replay file path.

        Unlike the old implementation this never re-serializes the full
        event history — at most FLUSH_INTERVAL_MS worth of events are
        written here, the rest is already on disk from periodic flush()es.
        """
        self.flush()
        if not self._ndjson_path.exists():
            return None
        log.info("Replay saved: %s (%d events total)", self._ndjson_path, self._flushed_event_count)
        return self._ndjson_path


def _count_ndjson_lines(path: Path) -> int:
    """Count non-empty lines in a gzip NDJSON file without parsing them."""
    raw = gzip.decompress(path.read_bytes()).decode("utf-8")
    return sum(1 for line in raw.split("\n") if line)


def load_replay(key: str, replay_dir: str = DEFAULT_REPLAY_DIR) -> dict[str, Any] | None:
    """Load a replay from disk by replay key. Returns parsed JSON or None.

    Tries the streaming .ndjson.gz format first, then falls back to the
    legacy single-JSON .json.gz and .json formats.
    """
    d = Path(replay_dir)

    ndjson_path = d / f"{key}.ndjson.gz"
    if ndjson_path.exists():
        try:
            raw = gzip.decompress(ndjson_path.read_bytes()).decode("utf-8")
            lines = [line for line in raw.split("\n") if line]
            if not lines:
                return None
            header: dict[str, Any] = json.loads(lines[0])
            header["events"] = [json.loads(line) for line in lines[1:]]
            return header
        except Exception:
            log.exception("Failed to load replay %s", ndjson_path)
            return None

    gz_path = d / f"{key}.json.gz"
    if gz_path.exists():
        try:
            result: dict[str, Any] = json.loads(gzip.decompress(gz_path.read_bytes()).decode("utf-8"))
            return result
        except Exception:
            log.exception("Failed to load replay %s", gz_path)
            return None
    json_path = d / f"{key}.json"
    if json_path.exists():
        try:
            result_json: dict[str, Any] = json.loads(json_path.read_text(encoding="utf-8"))
            return result_json
        except Exception:
            log.exception("Failed to load replay %s", json_path)
            return None
    return None


def get_replay_path(key: str, replay_dir: str = DEFAULT_REPLAY_DIR) -> Path | None:
    """Return the path to a replay file (streaming ndjson preferred), or None if not found.

    key may be a datetime-based replay key (e.g. '20260101_120000_42')
    or a legacy numeric string (e.g. '42').
    """
    d = Path(replay_dir)
    ndjson = d / f"{key}.ndjson.gz"
    if ndjson.exists():
        return ndjson
    gz = d / f"{key}.json.gz"
    if gz.exists():
        return gz
    legacy = d / f"{key}.json"
    if legacy.exists():
        return legacy
    return None


def list_replays(replay_dir: str = DEFAULT_REPLAY_DIR) -> list[dict[str, Any]]:
    """List available replays (metadata only, no events)."""
    d = Path(replay_dir)
    if not d.is_dir():
        return []
    result = []
    # Collect all replay files, preferring the newest format per replay key
    # (.ndjson.gz > .json.gz > legacy .json).
    seen_keys: set[str] = set()
    files: list[tuple[Path, str]] = []  # (path, format)
    for f in d.glob("*.ndjson.gz"):
        key = f.name.removesuffix(".ndjson.gz")
        seen_keys.add(key)
        files.append((f, "ndjson"))
    for f in d.glob("*.json.gz"):
        key = f.stem.removesuffix(".json")
        if key not in seen_keys:
            seen_keys.add(key)
            files.append((f, "json"))
    for f in d.glob("*.json"):
        key = f.stem
        if key not in seen_keys:
            files.append((f, "json"))
    files.sort(key=lambda x: x[0].stat().st_mtime, reverse=True)

    for path, fmt in files:
        try:
            if fmt == "ndjson":
                raw = gzip.decompress(path.read_bytes()).decode("utf-8")
                lines = [line for line in raw.split("\n") if line]
                if not lines:
                    continue
                header = json.loads(lines[0])
                event_count = len(lines) - 1
                stem = path.name.removesuffix(".ndjson.gz")
            else:
                is_gz = path.suffix == ".gz"
                raw_bytes = gzip.decompress(path.read_bytes()) if is_gz else path.read_bytes()
                header = json.loads(raw_bytes.decode("utf-8"))
                event_count = len(header.get("events", []))
                stem = path.stem.removesuffix(".json") if is_gz else path.stem
            replay_key = header.get("replay_key") or stem
            result.append({
                "bid": header.get("bid"),
                "replay_key": replay_key,
                "defender_uid": header.get("defender_uid"),
                "attacker_uid": header.get("attacker_uid"),
                "created_at": header.get("created_at"),
                "event_count": event_count,
            })
        except Exception:
            # Skip corrupt/unreadable replay files — one bad file shouldn't block the listing
            log.warning("list_replays: skipping unreadable file %s", path, exc_info=True)
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
    for pattern in ("*.ndjson.gz", "*.json.gz", "*.json"):
        for f in d.glob(pattern):
            try:
                if f.stat().st_mtime < cutoff:
                    f.unlink()
                    deleted += 1
            except Exception:
                # Race condition: file may be deleted between glob and unlink — skip it
                log.debug("cleanup_old_replays: could not remove %s", f, exc_info=True)
                continue
    if deleted:
        log.info("Replay cleanup: deleted %d files older than %d days", deleted, max_age_days)
    return deleted
