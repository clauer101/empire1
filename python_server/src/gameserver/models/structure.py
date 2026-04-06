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
    range: float
    reload_time_ms: float
    shot_speed: float
    shot_type: str = "normal"
    shot_sprite: str = ""  # Sprite URL for the projectile visual
    select: str = "first"  # Targeting strategy: first | last | random
    effects: dict[str, float] = field(default_factory=dict)

    # Transient battle state
    focus_cid: int | None = field(default=None, repr=False)
    reload_remaining_ms: float = field(default=0.0, repr=False)


def structure_from_item(
    sid: int,
    iid: str,
    position: HexCoord,
    item: object,
    select_override: str | None = None,
) -> Structure:
    """Create a Structure from an ItemDetails-like config object.

    Args:
        sid: Unique structure instance ID.
        iid: Item type identifier.
        position: Hex coordinate.
        item: ItemDetails (or similar) with optional damage/range/reload_time_ms/etc.
        select_override: If set and not 'first', overrides the item's select strategy.
    """
    item_select = getattr(item, "select", "first")
    select = select_override if select_override and select_override != "first" else item_select
    return Structure(
        sid=sid,
        iid=iid,
        position=position,
        damage=getattr(item, "damage", 1.0),
        range=getattr(item, "range", 1),
        reload_time_ms=getattr(item, "reload_time_ms", 2000.0),
        shot_speed=getattr(item, "shot_speed", 1.0),
        shot_type=getattr(item, "shot_type", "normal"),
        shot_sprite=getattr(item, "shot_sprite", ""),
        select=select,
        effects=getattr(item, "effects", {}),
    )
