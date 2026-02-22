"""Message store — persists player messages to a YAML file.

Message bodies are stored base64-encoded so the content is not
immediately readable in plain text.

File format (messages.yaml):
    messages:
      - id: 1
        from_uid: 2
        to_uid: 3
        body_b64: "SGVsbG8gV29ybGQ="   # base64 of the raw text
        sent_at: "2026-02-22T14:00:00"
    next_id: 2
"""

from __future__ import annotations

import base64
import logging
import time
from pathlib import Path
from typing import Any

import yaml

log = logging.getLogger(__name__)

DEFAULT_PATH = "messages.yaml"


def _encode(text: str) -> str:
    return base64.b64encode(text.encode("utf-8")).decode("ascii")


def _decode(b64: str) -> str:
    try:
        return base64.b64decode(b64.encode("ascii")).decode("utf-8")
    except Exception:
        return ""


class MessageStore:
    """Thread-safe (asyncio) YAML-backed message store.

    All write operations immediately persist to disk (atomic write via
    a temporary file).  Reads are served from the in-memory list.

    Args:
        path: Path to the YAML file.  Created on first write.
    """

    def __init__(self, path: str = DEFAULT_PATH) -> None:
        self._path = Path(path)
        self._messages: list[dict[str, Any]] = []
        self._next_id: int = 1

    # ------------------------------------------------------------------
    # Load / Save
    # ------------------------------------------------------------------

    def load(self) -> None:
        """Load messages from disk.  Safe to call even if file does not exist."""
        if not self._path.exists():
            log.info("MessageStore: no file at %s — starting empty", self._path)
            return
        try:
            data = yaml.safe_load(self._path.read_text(encoding="utf-8")) or {}
            self._messages = data.get("messages", []) or []
            self._next_id = data.get("next_id", 1)
            log.info("MessageStore: loaded %d messages from %s", len(self._messages), self._path)
        except Exception:
            log.exception("MessageStore: failed to load %s — starting empty", self._path)
            self._messages = []
            self._next_id = 1

    def _save(self) -> None:
        """Persist current state atomically."""
        tmp = self._path.with_suffix(".tmp")
        try:
            payload = {
                "messages": self._messages,
                "next_id": self._next_id,
            }
            tmp.write_text(
                yaml.dump(payload, default_flow_style=False, allow_unicode=True, sort_keys=False),
                encoding="utf-8",
            )
            tmp.replace(self._path)
        except Exception:
            log.exception("MessageStore: failed to save to %s", self._path)
            if tmp.exists():
                tmp.unlink(missing_ok=True)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def send(self, from_uid: int, to_uid: int, body: str) -> dict[str, Any]:
        """Store a new message and return it as a dict (body decoded)."""
        msg: dict[str, Any] = {
            "id": self._next_id,
            "from_uid": from_uid,
            "to_uid": to_uid,
            "body_b64": _encode(body),
            "sent_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "read": False,
        }
        self._next_id += 1
        self._messages.append(msg)
        self._save()
        log.info("MessageStore: message %d from uid=%d to uid=%d", msg["id"], from_uid, to_uid)
        return self._to_dto(msg)

    def get_inbox(self, uid: int) -> list[dict[str, Any]]:
        """Return all messages received by `uid`, newest first."""
        return [
            self._to_dto(m)
            for m in reversed(self._messages)
            if m["to_uid"] == uid
        ]

    def get_sent(self, uid: int) -> list[dict[str, Any]]:
        """Return all messages sent by `uid`, newest first."""
        return [
            self._to_dto(m)
            for m in reversed(self._messages)
            if m["from_uid"] == uid
        ]

    def get_all_for(self, uid: int) -> list[dict[str, Any]]:
        """Return inbox + sent combined, newest first."""
        return [
            self._to_dto(m)
            for m in reversed(self._messages)
            if m["to_uid"] == uid or m["from_uid"] == uid
        ]

    def mark_read(self, uid: int, msg_id: int) -> bool:
        """Mark a message as read.  Returns True if found."""
        for m in self._messages:
            if m["id"] == msg_id and m["to_uid"] == uid:
                if not m.get("read"):
                    m["read"] = True
                    self._save()
                return True
        return False

    def unread_count(self, uid: int) -> int:
        """Number of unread inbox messages for `uid`."""
        return sum(
            1 for m in self._messages
            if m["to_uid"] == uid and not m.get("read", False)
        )

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _to_dto(self, m: dict[str, Any]) -> dict[str, Any]:
        """Convert a stored record to a client-facing dict (body decoded)."""
        return {
            "id": m["id"],
            "from_uid": m["from_uid"],
            "to_uid": m["to_uid"],
            "body": _decode(m["body_b64"]),
            "sent_at": m.get("sent_at", ""),
            "read": m.get("read", False),
        }
