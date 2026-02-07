"""Army and CritterWave models.

An Army consists of ordered CritterWaves dispatched with timing delays.
Each wave spawns critters one at a time at a configured interval.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from gameserver.models.critter import Critter
from gameserver.models.map import Direction


@dataclass
class CritterWave:
    """A wave of identical critters within an army.

    Attributes:
        critter_iid: Item type of the critters in this wave.
        slots: Capacity of this wave (determines critter count).
        critters: Pre-instantiated critter list.
        spawn_interval_ms: Time between individual critter spawns.
        next_spawn_ms: Countdown to next critter spawn.
        spawn_pointer: Index of the next critter to spawn.
    """

    critter_iid: str
    slots: int
    critters: list[Critter] = field(default_factory=list)
    spawn_interval_ms: float = 500.0
    next_spawn_ms: float = 0.0
    spawn_pointer: int = 0

    @property
    def is_dispatched(self) -> bool:
        """True when all critters in this wave have been spawned."""
        return self.spawn_pointer >= len(self.critters)


@dataclass
class Army:
    """An attacking army consisting of multiple critter waves.

    Attributes:
        aid: Unique army ID.
        uid: Owner player UID.
        direction: Entry direction on the map (NORTH/SOUTH/EAST/WEST).
        name: Display name.
        waves: Ordered list of critter waves.
        wave_pointer: Index of next wave to dispatch.
        next_wave_ms: Countdown to next wave dispatch.
    """

    aid: int
    uid: int
    direction: Direction
    name: str = ""
    waves: list[CritterWave] = field(default_factory=list)
    wave_pointer: int = 0
    next_wave_ms: float = 25_000.0  # INITIAL_WAVE_DELAY

    @property
    def is_finished(self) -> bool:
        """True when the last wave has dispatched all its critters."""
        if not self.waves:
            return True
        return self.waves[-1].is_dispatched


@dataclass
class SpyArmy:
    """A spy army variant — gathers intelligence instead of attacking.

    Attributes:
        aid: Unique army ID.
        uid: Owner player UID.
        options: Selected spy options with their costs.
    """

    aid: int
    uid: int
    options: dict[str, float] = field(default_factory=dict)
    # Spy option keys and base costs:
    #   spy_defense: 500       — view enemy structures
    #   spy_build_queue: 1000  — view construction progress
    #   spy_research_queue: 2000 — view research progress
    #   spy_attacks: 5000      — view incoming/outgoing attacks
    #   spy_artefacts: 10000   — view artefact collection
