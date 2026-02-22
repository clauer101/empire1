"""Item definition models.

Defines all game items: buildings, knowledge, structures, critters, artefacts, wonders.
Loaded from config/items.yaml via the item_loader.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class ItemType(Enum):
    """The category of a game item."""

    BUILDING = "building"
    KNOWLEDGE = "knowledge"
    STRUCTURE = "structure"
    CRITTER = "critter"
    ARTEFACT = "artefact"
    WONDER = "wonder"


@dataclass(frozen=True)
class ItemDetails:
    """Complete definition of a game item.

    Not all fields apply to all item types. Type-irrelevant fields keep their
    defaults and are ignored by the consuming code.

    Attributes:
        iid: Unique item identifier string.
        name: Human-readable display name.
        description: Extended description of the item.
        item_type: Category of the item.
        effort: Build / research effort (buildings, knowledge, wonders).
        costs: Resource costs to build / research. {resource_key: amount}
        requirements: List of IIDs that must be completed first.
        effects: Passive effects granted. {effect_key: value}

        # Structure-specific
        damage: Damage per shot.
        range: Targeting range in hex fields.
        reload_time_ms: Milliseconds between shots.
        shot_speed: Projectile speed in hex fields per second.
        shot_type: Visual shot type identifier.

        # Critter-specific
        speed: Movement speed in hex fields per second.
        health: Hit points.
        armour: Damage reduction.
        slots: Slot cost per critter in a wave.
        time_between_ms: Milliseconds between critter spawns in a wave.
        is_boss: Whether this is a persistent boss critter.
        capture: Resources captured when critter reaches the end. {key: amount}
        bonus: Resources granted to defender on kill. {key: amount}
        spawn_on_death: Critters spawned when this critter dies. {iid: count}
    """

    iid: str = ""
    name: str = ""
    item_type: ItemType = ItemType.BUILDING

    # Common
    effort: float = 0.0
    costs: dict[str, float] = field(default_factory=dict)
    requirements: list[str] = field(default_factory=list)
    effects: dict[str, float] = field(default_factory=dict)
    description: str = ""

    # Structure
    damage: float = 0.0
    range: int = 0
    reload_time_ms: float = 0.0
    shot_speed: float = 0.0
    shot_type: str = "normal"
    sprite: str | None = None

    # Critter
    speed: float = 0.0
    health: float = 0.0
    armour: float = 0.0
    slots: int = 1
    time_between_ms: float = 500.0
    is_boss: bool = False
    capture: dict[str, float] = field(default_factory=dict)
    bonus: dict[str, float] = field(default_factory=dict)
    spawn_on_death: dict[str, int] = field(default_factory=dict)
    scale: float = 1.0
