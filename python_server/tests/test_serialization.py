"""Tests for network/serialization.py — encode/decode with optional compression."""

from gameserver.network.serialization import encode, decode


class TestEncodeDecode:
    def test_roundtrip_plain(self):
        data = {"type": "ping", "value": 42}
        raw = encode(data)
        assert decode(raw) == data

    def test_roundtrip_compressed(self):
        data = {"items": list(range(100))}
        raw = encode(data, compress=True)
        assert decode(raw, compressed=True) == data

    def test_plain_is_json_utf8(self):
        raw = encode({"a": 1})
        assert raw == b'{"a":1}'

    def test_compressed_smaller_for_large_payload(self):
        data = {"big": "x" * 10_000}
        plain = encode(data, compress=False)
        compressed = encode(data, compress=True)
        assert len(compressed) < len(plain)

    def test_unicode_roundtrip(self):
        data = {"name": "Ünit Tëst 🏰"}
        assert decode(encode(data)) == data

    def test_empty_dict(self):
        assert decode(encode({})) == {}
