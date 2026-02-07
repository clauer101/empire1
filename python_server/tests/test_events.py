"""Tests for the event bus."""

from gameserver.util.events import EventBus, CritterDied, CritterFinished


class TestEventBus:
    def test_emit_triggers_handler(self):
        bus = EventBus()
        received = []
        bus.on(CritterDied, lambda e: received.append(e.critter_id))
        bus.emit(CritterDied(critter_id=42))
        assert received == [42]

    def test_no_cross_event(self):
        bus = EventBus()
        received = []
        bus.on(CritterDied, lambda e: received.append("died"))
        bus.emit(CritterFinished(critter_id=1, with_transfer=True))
        assert received == []

    def test_multiple_handlers(self):
        bus = EventBus()
        a, b = [], []
        bus.on(CritterDied, lambda e: a.append(1))
        bus.on(CritterDied, lambda e: b.append(2))
        bus.emit(CritterDied(critter_id=1))
        assert a == [1] and b == [2]

    def test_off_removes_handler(self):
        bus = EventBus()
        received = []
        handler = lambda e: received.append(1)
        bus.on(CritterDied, handler)
        bus.off(CritterDied, handler)
        bus.emit(CritterDied(critter_id=1))
        assert received == []

    def test_clear(self):
        bus = EventBus()
        bus.on(CritterDied, lambda e: None)
        bus.clear()
        # Should not raise
        bus.emit(CritterDied(critter_id=1))
