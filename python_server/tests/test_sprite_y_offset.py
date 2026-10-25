"""sprite_y_offset: optional vertical sprite shift for critters and rulers (default 0)."""

from __future__ import annotations

from gameserver.engine.empire_service import ruler_critter_stats
from gameserver.loaders.item_loader import _parse_section
from gameserver.persistence.state_load import _deserialize_critter

_CRITTER = {"name": "Test", "health": 1, "speed": 1, "animation": "assets/sprites/critters/test"}

_RULER_CFG = {
    "speed_min": 0.5, "speed_max": 1.0,
    "health_min": 10.0, "health_max": 100.0,
    "armour_min": 0.0, "armour_max": 5.0,
    "damage_min": 1.0, "damage_max": 10.0,
    "value_min": 10, "value_max": 100,
    "scale_base": 1.0, "animation": "assets/sprites/ruler/test",
}


def test_critter_offset_defaults_to_zero():
    (item,) = _parse_section("critters", {"TEST": dict(_CRITTER)})
    assert item.sprite_y_offset == 0.0


def test_critter_offset_is_loaded():
    (item,) = _parse_section("critters", {"TEST": {**_CRITTER, "sprite_y_offset": 0.15}})
    assert item.sprite_y_offset == 0.15


def test_ruler_offset_defaults_to_zero_and_is_passed_through():
    assert ruler_critter_stats(_RULER_CFG, level=1)["sprite_y_offset"] == 0.0
    cfg = {**_RULER_CFG, "sprite_y_offset": -0.1}
    assert ruler_critter_stats(cfg, level=5)["sprite_y_offset"] == -0.1


def test_offset_survives_state_reload():
    critter = _deserialize_critter({
        "cid": 1, "iid": "TEST", "health": 1.0, "max_health": 1.0,
        "speed": 1.0, "armour": 0.0, "sprite_y_offset": 0.2,
    })
    assert critter.sprite_y_offset == 0.2
    legacy = _deserialize_critter({
        "cid": 2, "iid": "TEST", "health": 1.0, "max_health": 1.0, "speed": 1.0, "armour": 0.0,
    })
    assert legacy.sprite_y_offset == 0.0
