"""Tests for message routing."""

import pytest
from gameserver.models.messages import (
    AuthRequest, NewStructureRequest, parse_message, MESSAGE_TYPES,
)


class TestParseMessage:
    def test_parse_auth_request(self):
        raw = {"type": "auth_request", "username": "alice", "password": "secret"}
        msg = parse_message(raw)
        assert isinstance(msg, AuthRequest)
        assert msg.username == "alice"

    def test_parse_new_structure(self):
        raw = {"type": "new_structure", "iid": "tower_1", "hex_q": 5, "hex_r": 3}
        msg = parse_message(raw)
        assert isinstance(msg, NewStructureRequest)
        assert msg.hex_q == 5
        assert msg.hex_r == 3

    def test_parse_unknown_type(self):
        raw = {"type": "nonexistent", "sender": 1}
        msg = parse_message(raw)
        assert msg.type == "nonexistent"

    def test_all_types_registered(self):
        assert len(MESSAGE_TYPES) > 0
        for key, cls in MESSAGE_TYPES.items():
            # Pydantic models have 'type' as a model field, not a class attribute
            assert "type" in cls.model_fields
