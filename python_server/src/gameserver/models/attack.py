"""Attack model — state machine for army travel and siege.

An Attack tracks an army travelling to a target, entering siege,
and eventually triggering a battle.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class AttackPhase(Enum):
    """Phases of an attack."""

    TRAVELLING = "travelling"
    IN_SIEGE = "in_siege"
    IN_BATTLE = "in_battle"
    FINISHED = "finished"


@dataclass
class Attack:
    """State of an in-progress attack.

    Attributes:
        attack_id: Unique attack ID.
        attacker_uid: UID of the attacking player.
        defender_uid: UID of the defending player.
        army_aid: AID of the army being sent.
        phase: Current phase of the attack.
        eta_seconds: Remaining travel time in seconds.
        siege_remaining_seconds: Remaining siege countdown.
        total_eta_seconds: Initial travel time for progress calculation.
        total_siege_seconds: Initial siege duration for progress calculation.
        wave_pointer: Index of current wave being spawned.
        critter_pointer: Number of critters spawned in current wave.
        next_wave_ms: Countdown to next wave dispatch.
    """

    attack_id: int
    attacker_uid: int
    defender_uid: int
    army_aid: int
    phase: AttackPhase = AttackPhase.TRAVELLING
    eta_seconds: float = 5400.0  # BASE_TRAVEL_OFFSET
    total_eta_seconds: float = 5400.0  # initial ETA for progress calculation
    siege_remaining_seconds: float = 0.0
    total_siege_seconds: float = 30.0  # initial siege duration for progress calculation
    wave_pointer: int = 0  # Current wave index
    critter_pointer: int = 0  # Critters spawned in current wave
    next_wave_ms: float = 25_000.0  # Countdown to next wave
