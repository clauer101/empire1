"""Serialization — JSON encoding/decoding with optional compression.

Replaces the Java XStream XML + zlib ObjectOutputStream protocol.
"""

from __future__ import annotations

import json
import zlib
from typing import Any


def encode(data: dict[str, Any], compress: bool = False) -> bytes:
    """Encode a message dict to bytes (JSON, optionally compressed)."""
    payload = json.dumps(data, separators=(",", ":")).encode("utf-8")
    if compress:
        payload = zlib.compress(payload)
    return payload


def decode(raw: bytes, compressed: bool = False) -> dict[str, Any]:
    """Decode bytes to a message dict."""
    if compressed:
        raw = zlib.decompress(raw)
    return json.loads(raw.decode("utf-8"))
