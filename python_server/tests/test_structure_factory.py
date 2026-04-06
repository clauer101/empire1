"""Tests for structure_from_item factory in models/structure.py."""

from types import SimpleNamespace

from gameserver.models.hex import HexCoord
from gameserver.models.structure import Structure, structure_from_item


class TestStructureFromItem:
    def _item(self, **kw):
        defaults = dict(
            damage=5.0, range=3, reload_time_ms=1500.0,
            shot_speed=2.0, shot_type="fire", shot_sprite="/fire.png",
            select="last", effects={"burn_duration": 500},
        )
        defaults.update(kw)
        return SimpleNamespace(**defaults)

    def test_basic_creation(self):
        item = self._item()
        s = structure_from_item(sid=1, iid="TOWER_A", position=HexCoord(2, 3), item=item)
        assert isinstance(s, Structure)
        assert s.sid == 1
        assert s.iid == "TOWER_A"
        assert s.position == HexCoord(2, 3)
        assert s.damage == 5.0
        assert s.range == 3
        assert s.reload_time_ms == 1500.0
        assert s.shot_speed == 2.0
        assert s.shot_type == "fire"
        assert s.effects == {"burn_duration": 500}

    def test_defaults_for_missing_attrs(self):
        item = SimpleNamespace()  # no attrs at all
        s = structure_from_item(sid=10, iid="X", position=HexCoord(0, 0), item=item)
        assert s.damage == 1.0
        assert s.range == 1
        assert s.reload_time_ms == 2000.0
        assert s.shot_speed == 1.0
        assert s.shot_type == "normal"
        assert s.select == "first"
        assert s.effects == {}

    def test_select_override(self):
        item = self._item(select="first")
        s = structure_from_item(sid=1, iid="T", position=HexCoord(0, 0), item=item, select_override="last")
        assert s.select == "last"

    def test_select_override_first_uses_item(self):
        item = self._item(select="last")
        s = structure_from_item(sid=1, iid="T", position=HexCoord(0, 0), item=item, select_override="first")
        assert s.select == "last"

    def test_select_override_none_uses_item(self):
        item = self._item(select="random")
        s = structure_from_item(sid=1, iid="T", position=HexCoord(0, 0), item=item, select_override=None)
        assert s.select == "random"

    def test_transient_state_defaults(self):
        item = self._item()
        s = structure_from_item(sid=1, iid="T", position=HexCoord(0, 0), item=item)
        assert s.focus_cid is None
        assert s.reload_remaining_ms == 0.0
