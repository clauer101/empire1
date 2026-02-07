"""Shot model — a projectile in flight from a structure to a critter.

Shots are pure data. Flight time is tracked directly in the shot.
Damage and effects are applied by battle_service when flight_remaining_ms reaches 0.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from gameserver.models.critter import DamageType


@dataclass
class Shot:
    """A projectile fired by a structure.

    Attributes:
        damage: Damage dealt on arrival.
        target_cid: CID of the target critter.
        source_sid: SID of the firing structure (-1 for splash sub-shots).
        shot_type: One of DamageType constants.
        effects: Effect map from the source structure.
        flight_remaining_ms: Time until the shot arrives.
    """

    damage: float
    target_cid: int
    source_sid: int
    shot_type: int = DamageType.NORMAL
    effects: dict[str, float] = field(default_factory=dict)
    flight_remaining_ms: float = 0.0
