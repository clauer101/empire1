"""Critter model — a single unit moving along a hex path.

Critters are spawned by CritterWaves, move along a predefined hex path,
and can be damaged/killed by Structures. If they reach the end of the path,
they capture resources from the defender.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from gameserver.models.hex import HexCoord


class DamageType:
    """Shot/damage type constants."""

    NORMAL = 0
    BURN = 1
    COLD = 2
    SPLASH = 3


@dataclass
class Critter:
    """A single critter on the battlefield.

    Attributes:
        cid: Unique critter instance ID.
        iid: Item type identifier (references ItemDetails).
        health: Current hit points.
        max_health: Maximum hit points (for display).
        speed: Base movement speed in hex fields per second.
        armour: Damage reduction for non-burn damage.
        path: Ordered list of hex coordinates to follow.
        path_progress: Fractional position along the path (0.0 = start).

        capture: Resources captured when reaching the end.
        bonus: Resources granted to defender on kill.
        spawn_on_death: Critters spawned when this critter dies.

        slow_remaining_ms: Remaining slow effect duration in ms.
        slow_speed: Movement speed while slowed (hex/s).
        burn_remaining_ms: Remaining burn effect duration in ms.
        burn_dps: Burn damage per second.

        level: Critter level (for bosses).
        xp: Experience points (for bosses).
        is_boss: Whether this is a persistent boss.
    """

    cid: int
    iid: str
    health: float
    max_health: float
    speed: float
    armour: float
    path: list[HexCoord] = field(default_factory=list)
    path_progress: float = 0.0

    capture: dict[str, float] = field(default_factory=dict)
    bonus: dict[str, float] = field(default_factory=dict)
    spawn_on_death: dict[str, int] = field(default_factory=dict)

    # Status effects
    slow_remaining_ms: float = 0.0
    slow_speed: float = 0.0
    burn_remaining_ms: float = 0.0
    burn_dps: float = 0.0

    # Boss fields
    level: int = 1
    xp: float = 0.0
    is_boss: bool = False

    # -- Derived properties ----------------------------------------------

    @property
    def is_alive(self) -> bool:
        return self.health > 0

    @property
    def is_finished(self) -> bool:
        return self.path_progress >= len(self.path) - 1

    @property
    def current_hex(self) -> HexCoord:
        """The hex field the critter is currently on."""
        idx = min(int(self.path_progress), len(self.path) - 1)
        return self.path[idx]

    @property
    def remainder_path(self) -> float:
        """Remaining hex fields to the end of the path."""
        return max(0.0, len(self.path) - 1 - self.path_progress)

    @property
    def effective_speed(self) -> float:
        """Current speed accounting for slow effects."""
        if self.slow_remaining_ms > 0:
            return self.slow_speed
        return self.speed
