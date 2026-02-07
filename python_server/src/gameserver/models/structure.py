"""Structure model — a defensive tower on the hex map.

Structures auto-target critters within range and fire shots at them.
Targeting strategy: most-advanced critter (lowest remainder_path).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from gameserver.models.hex import HexCoord


@dataclass
class Structure:
    """A defensive tower placed on the hex map.

    Attributes:
        sid: Unique structure instance ID.
        iid: Item type identifier (references ItemDetails).
        position: Hex coordinate where the structure is placed.
        damage: Damage per shot.
        range: Targeting range in hex fields.
        reload_time_ms: Time between shots in milliseconds.
        shot_speed: Projectile speed in hex fields per second.
        shot_type: Visual/mechanical shot type identifier.
        effects: Special effects applied by shots (slow, burn, splash).

        focus_cid: CID of the currently targeted critter (None if no target).
        reload_remaining_ms: Time until next shot is ready.
    """

    sid: int
    iid: str
    position: HexCoord
    damage: float
    range: int
    reload_time_ms: float
    shot_speed: float
    shot_type: str = "normal"
    effects: dict[str, float] = field(default_factory=dict)

    # Transient battle state
    focus_cid: int | None = field(default=None, repr=False)
    reload_remaining_ms: float = field(default=0.0, repr=False)
