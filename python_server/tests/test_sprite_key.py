"""sprite_key: battle critters name their sprite by the YAML animation folder."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from gameserver.engine.battle_service import BattleService
from gameserver.loaders.game_config_loader import CritterUpgradeDef, GameConfig
from gameserver.models.hex import HexCoord
from gameserver.models.items import ItemDetails, ItemType
from gameserver.persistence.state_load import _deserialize_critter
from gameserver.util.sprites import sprite_key


@pytest.mark.parametrize("animation,expected", [
    ("assets/sprites/critters/mech_warrior2", "mech_warrior2"),
    ("assets/sprites/critters/mech_warrior2/", "mech_warrior2"),
    ("/assets/sprites/ruler/maja", "ruler_maja"),
    ("", ""),
])
def test_sprite_key(animation, expected):
    assert sprite_key(animation) == expected


def _svc(item: ItemDetails) -> BattleService:
    gc = MagicMock(spec=GameConfig)
    gc.critter_upgrades = CritterUpgradeDef()
    return BattleService(items=[item], gc=gc)


def test_spawned_critter_uses_animation_folder_not_iid():
    item = ItemDetails(iid="MECH_WARRIOR", item_type=ItemType.CRITTER, health=10, speed=1,
                       animation="assets/sprites/critters/mech_warrior2")
    critter = _svc(item)._make_critter_from_item(
        "MECH_WARRIOR", path=[HexCoord(i, 0) for i in range(3)])
    assert critter.sprite_key == "mech_warrior2"


def test_critter_without_animation_has_empty_key():
    item = ItemDetails(iid="X", item_type=ItemType.CRITTER, health=10, speed=1)
    critter = _svc(item)._make_critter_from_item("X", path=[HexCoord(0, 0), HexCoord(1, 0)])
    assert critter.sprite_key == ""


def test_sprite_key_survives_state_reload():
    base = {"cid": 1, "iid": "X", "health": 1.0, "max_health": 1.0, "speed": 1.0, "armour": 0.0}
    assert _deserialize_critter({**base, "sprite_key": "mech_warrior2"}).sprite_key == "mech_warrior2"
    assert _deserialize_critter(base).sprite_key == ""
