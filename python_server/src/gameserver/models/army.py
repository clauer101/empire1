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
    
    Note: Runtime state (spawn_pointer, next_spawn_ms) is managed by BattleService
          during battle execution and stored in BattleState, not persisted.
    """

    wave_id: int
    iid: str = ""
    slots: int = 0


@dataclass
class Army:
    """An attacking army consisting of multiple critter waves.

    Attributes:
        aid: Unique army ID.
        uid: Owner player UID.
        name: Display name.
        waves: Ordered list of critter waves.
        wave_pointer: Index of next wave to dispatch.
        next_wave_ms: Countdown to next wave dispatch.
    """

    aid: int
    uid: int
    name: str = ""
    waves: list[CritterWave] = field(default_factory=list)
    wave_pointer: int = 0
    next_wave_ms: float = 25_000.0  # INITIAL_WAVE_DELAY

    @property
    def is_finished(self) -> bool:
        """True when the last wave has finished deployment.
        
        Note: This checks wave_pointer against wave count, but the actual
        dispatch state (spawn_pointer) is tracked in BattleState during battle.
        """
        if not self.waves:
            return True
        # All waves have been started
        return self.wave_pointer >= len(self.waves)


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
