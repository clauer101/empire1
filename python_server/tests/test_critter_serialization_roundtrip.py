"""Regression test: Critter serialization must roundtrip ruler/combat fields.

Bug: a battle resumed after a server restart reset every critter's `damage`,
`value`, `slots`, `owner_uid`, `is_ruler`, `aura_radius` and `aura_effects` to
their dataclass defaults, because `_serialize_critter`/`_deserialize_critter`
did not include them. A ruler critter already spawned with a level-scaled
`damage` (e.g. 7) would silently drop to the default `damage=1.0` on resume.
"""

from __future__ import annotations

from gameserver.models.critter import Critter
from gameserver.models.hex import HexCoord
from gameserver.persistence.state_load import _deserialize_critter
from gameserver.persistence.state_save import _serialize_critter


def test_ruler_critter_roundtrips_damage_and_ruler_fields():
    critter = Critter(
        cid=42,
        iid="ruler_maja",
        path=[HexCoord(q=0, r=0), HexCoord(q=0, r=1)],
        path_progress=0.5,
        health=676.82,
        max_health=676.82,
        value=12.5,
        damage=7.0,
        slots=1,
        owner_uid=26,
        is_ruler=True,
        aura_radius=2.0,
        aura_effects={"increase_armour_modifier": 0.2},
    )

    restored = _deserialize_critter(_serialize_critter(critter))

    assert restored.damage == 7.0
    assert restored.value == 12.5
    assert restored.slots == 1
    assert restored.owner_uid == 26
    assert restored.is_ruler is True
    assert restored.aura_radius == 2.0
    assert restored.aura_effects == {"increase_armour_modifier": 0.2}


def test_regular_critter_roundtrips_defaults():
    critter = Critter(cid=1, iid="WARRIOR", value=5.0, damage=2.0, slots=2, owner_uid=7)

    restored = _deserialize_critter(_serialize_critter(critter))

    assert restored.damage == 2.0
    assert restored.value == 5.0
    assert restored.slots == 2
    assert restored.owner_uid == 7
    assert restored.is_ruler is False
