"""Tests for persistence/message_store.py."""

import pytest
from gameserver.persistence.message_store import MessageStore, _encode, _decode


class TestEncoding:
    def test_roundtrip(self):
        assert _decode(_encode("Hello World")) == "Hello World"

    def test_unicode(self):
        text = "Ünïcödé 🏰"
        assert _decode(_encode(text)) == text

    def test_decode_invalid_returns_empty(self):
        assert _decode("!!!not-base64!!!") == ""


class TestMessageStore:
    @pytest.fixture
    def store(self, tmp_path):
        return MessageStore(path=str(tmp_path / "msgs.yaml"))

    def test_send_and_inbox(self, store):
        msg = store.send(from_uid=1, to_uid=2, body="Hi")
        assert msg["from_uid"] == 1
        assert msg["to_uid"] == 2
        assert msg["body"] == "Hi"
        assert msg["id"] == 1
        inbox = store.get_inbox(2)
        assert len(inbox) == 1
        assert inbox[0]["body"] == "Hi"

    def test_inbox_empty_for_other_user(self, store):
        store.send(from_uid=1, to_uid=2, body="Secret")
        assert store.get_inbox(3) == []

    def test_sent_messages(self, store):
        store.send(from_uid=1, to_uid=2, body="A")
        store.send(from_uid=1, to_uid=3, body="B")
        sent = store.get_sent(1)
        assert len(sent) == 2

    def test_global_chat(self, store):
        store.send(from_uid=1, to_uid=0, body="Hello all")
        store.send(from_uid=0, to_uid=0, body="System")  # excluded (from system)
        msgs = store.get_global()
        assert len(msgs) == 1
        assert msgs[0]["body"] == "Hello all"

    def test_private_messages(self, store):
        store.send(from_uid=1, to_uid=2, body="DM")
        store.send(from_uid=1, to_uid=0, body="Global")  # excluded
        store.send(from_uid=0, to_uid=1, body="System")  # excluded
        private = store.get_private_for(1)
        assert len(private) == 1
        assert private[0]["body"] == "DM"

    def test_battle_reports(self, store):
        store.send(from_uid=0, to_uid=1, body="You lost!")
        store.send(from_uid=2, to_uid=1, body="Not a report")
        reports = store.get_battle_reports_for(1)
        assert len(reports) == 1
        assert reports[0]["body"] == "You lost!"

    def test_unread_count(self, store):
        store.send(from_uid=1, to_uid=2, body="A")
        store.send(from_uid=1, to_uid=2, body="B")
        assert store.unread_count(2) == 2

    def test_mark_read(self, store):
        msg = store.send(from_uid=1, to_uid=2, body="Read me")
        assert store.unread_count(2) == 1
        found = store.mark_read(uid=2, msg_id=msg["id"])
        assert found is True
        assert store.unread_count(2) == 0

    def test_mark_read_wrong_user(self, store):
        msg = store.send(from_uid=1, to_uid=2, body="Secret")
        found = store.mark_read(uid=3, msg_id=msg["id"])
        assert found is False
        assert store.unread_count(2) == 1

    def test_unread_count_private_vs_battle(self, store):
        store.send(from_uid=1, to_uid=2, body="Private")
        store.send(from_uid=0, to_uid=2, body="Battle report")
        assert store.unread_count_private(2) == 1
        # System messages (from_uid=0) are pre-read
        assert store.unread_count_battle(2) == 0

    def test_system_messages_are_pre_read(self, store):
        msg = store.send(from_uid=0, to_uid=2, body="System")
        assert msg["read"] is True
        assert store.unread_count_battle(2) == 0

    def test_persistence_roundtrip(self, tmp_path):
        path = str(tmp_path / "msgs.yaml")
        store1 = MessageStore(path=path)
        store1.send(from_uid=1, to_uid=2, body="Persist me")

        store2 = MessageStore(path=path)
        store2.load()
        inbox = store2.get_inbox(2)
        assert len(inbox) == 1
        assert inbox[0]["body"] == "Persist me"

    def test_load_nonexistent_file(self, tmp_path):
        store = MessageStore(path=str(tmp_path / "nope.yaml"))
        store.load()  # should not raise
        assert store.get_inbox(1) == []

    def test_auto_incrementing_ids(self, store):
        m1 = store.send(from_uid=1, to_uid=2, body="A")
        m2 = store.send(from_uid=1, to_uid=2, body="B")
        assert m2["id"] == m1["id"] + 1

    def test_get_all_for(self, store):
        store.send(from_uid=1, to_uid=2, body="Sent")
        store.send(from_uid=3, to_uid=1, body="Received")
        store.send(from_uid=4, to_uid=5, body="Other")
        all_msgs = store.get_all_for(1)
        assert len(all_msgs) == 2
