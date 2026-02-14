"""Army and CritterWave models.

An Army consists of ordered CritterWaves dispatched with timing delays.
Each wave spawns critters one at a time at a configured interval.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class CritterWave:
    """A wave of critters within an army.

    Attributes:
        wave_id: Unique wave ID within the army.
        iid: Critter type (item ID) for all critters in this wave.
        slots: Number of critter slots in this wave.
        num_critters_spawned: Runtime state - spawn count in current wave (0 to slots).
        next_critter_ms: Runtime state - time until next critter spawn in milliseconds.
    
    Note: Runtime state is managed by BattleService during battle execution.
    """

    wave_id: int
    iid: str = ""
    slots: int = 0
    num_critters_spawned: int = 0
    next_critter_ms: float = 0.0


@dataclass
class Army:
    """An attacking army consisting of multiple critter waves.

    Attributes:
        aid: Unique army ID.
        uid: Owner player UID.
        name: Display name.
        waves: Ordered list of critter waves.
    
    Note: Wave progression is managed by BattleService during battle execution.
    Each wave spawns critters based on its next_critter_ms and num_critters_spawned runtime state.
    """

    aid: int
    uid: int
    name: str = ""
    waves: list[CritterWave] = field(default_factory=list)



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
