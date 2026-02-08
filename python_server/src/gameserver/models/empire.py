"""Empire model — a player's complete game state.

An Empire holds all resources, buildings, research, armies, structures,
citizens, effects, artefacts, and the player's hex map.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from gameserver.models.army import Army, SpyArmy
from gameserver.models.critter import Critter
from gameserver.models.structure import Structure


@dataclass
class Empire:
    """Complete state of a player's empire.

    Attributes:
        uid: Player user ID.
        name: Empire display name.
        resources: Current resource amounts {key: amount}.
        buildings: Building IIDs → remaining effort (0 = complete).
        build_queue: IID of the building currently under construction.
            Only this item is progressed each tick.
        knowledge: Knowledge IIDs → remaining effort (0 = complete).
        research_queue: IID of the knowledge currently being researched.
            Only this item is progressed each tick.
        structures: Structure instances by SID.
        armies: Player's attack armies.
        spies: Player's spy armies.
        citizens: Citizen distribution {type: count}.
        effects: Accumulated passive effects {key: value}.
        artefacts: Collected artefact IIDs.
        bosses: Boss critters {iid: Critter}.
        max_life: Maximum life points.
    """

    uid: int
    name: str = ""

    resources: dict[str, float] = field(default_factory=lambda: {
        "gold": 0.0,
        "culture": 0.0,
        "life": 10.0,
    })
    buildings: dict[str, float] = field(default_factory=dict)
    build_queue: Optional[str] = None
    knowledge: dict[str, float] = field(default_factory=dict)
    research_queue: Optional[str] = None
    structures: dict[int, Structure] = field(default_factory=dict)
    armies: list[Army] = field(default_factory=list)
    spies: list[SpyArmy] = field(default_factory=list)
    citizens: dict[str, int] = field(default_factory=lambda: {
        "merchant": 0,
        "scientist": 0,
        "artist": 0,
    })
    effects: dict[str, float] = field(default_factory=dict)
    artefacts: list[str] = field(default_factory=list)
    bosses: dict[str, Critter] = field(default_factory=dict)
    hex_map: dict = field(default_factory=dict)  # Composer hex tiles
    max_life: float = 10.0

    # -- Helpers ---------------------------------------------------------

    def get_effect(self, key: str, default: float = 0.0) -> float:
        """Look up an effect value with a default."""
        return self.effects.get(key, default)
