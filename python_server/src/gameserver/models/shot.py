"""Shot model — a projectile in flight from a structure to a critter.

Shots are pure data. Flight time is tracked directly in the shot.
Damage and effects are applied by battle_service when flight_remaining_ms reaches 0.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from gameserver.models.critter import DamageType
from gameserver.models.hex import HexCoord


@dataclass
class Shot:
    """A projectile fired by a structure.

    Attributes:
        damage: Damage dealt on arrival.
        target_cid: CID of the target critter.
        source_sid: SID of the firing structure (-1 for splash sub-shots).
        shot_type: One of DamageType constants.
        effects: Effect map from the source structure.
        flight_remaining_ms: Time until shot arrives at target.
        path_progress: For visual purposes, between 0 and 1, updated by battle_service during flight.
        origin: For visual purposes, set by battle_service on shot creation.
    """

    damage: float  # Damage dealt on arrival
    target_cid: int  # CID of the target critter
    source_sid: int  #Structure id of the firing tower, -1 for splash damage sub-shots
    shot_type: int = DamageType.NORMAL  # Type of damage (normal, burn, cold, splash)
    effects: dict[str, float] = field(default_factory=dict)
    flight_remaining_ms: float = 0.0  # Time until shot arrives (ms)
    origin: HexCoord | None = None  # For visual purposes, set by battle_service on shot creation 
    path_progress: float = 0.0  # For visual purposes between 0 and 1, updated by battle_service during flight
