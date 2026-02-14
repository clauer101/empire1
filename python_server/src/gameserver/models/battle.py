"""Battle state model — data container for an active battle.

The BattleState holds all mutable state for a running battle.
Business logic is in engine/battle_service.py.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from gameserver.models.army import Army
from gameserver.models.critter import Critter
from gameserver.models.shot import Shot
from gameserver.models.structure import Structure

if TYPE_CHECKING:
    from gameserver.models.empire import Empire


@dataclass
class BattleState:
    """Mutable state container for an active tower-defense battle.

    Attributes:
        bid: Unique battle ID.
        defender_uid: UID of the defending player.
        attacker_uids: UIDs of all attacking players.

        armies: Active armies 
        critters: All live critters on the field, keyed by CID.
        structures: Defender's towers, keyed by SID.
        pending_shots: Shots in flight.

        elapsed_ms: Total elapsed battle time.
        broadcast_timer_ms: Countdown to next broadcast window.
        keep_alive: Whether the battle loop should continue.
        is_finished: Whether the battle has concluded.
        defender_won: Whether the defender won (set on finish).

        # Delta tracking for broadcasts
        new_critters: Critters added since last broadcast.
        new_shots: Shots fired since last broadcast.
        dead_critter_ids: CIDs of critters killed since last broadcast.
        finished_critter_ids: CIDs of critters that reached the end.
        new_structure_ids: SIDs of structures added since last broadcast.

        # Observers
        observer_uids: UIDs of players watching this battle.

        # Summary
        attacker_gains: Resources gained per attacker UID.
        defender_losses: Resources lost by defender.
    """

    bid: int
    defender_uid: int
    attacker_uids: list[int] = field(default_factory=list)
    attack_id: int | None = None  # Reference to Attack (if battle is part of an attack)

    attacker: Army | None = None  # The attacking army
    defender: Empire | None = None  # The defending empire
    critters: dict[int, Critter] = field(default_factory=dict)
    structures: dict[int, Structure] = field(default_factory=dict)
    pending_shots: list[Shot] = field(default_factory=list)



    elapsed_ms: float = 0.0
    broadcast_timer_ms: float = 0.0
    keep_alive: bool = True
    is_finished: bool = False
    defender_won: bool | None = None

    # Observers
    observer_uids: set[int] = field(default_factory=set)

    # Summary
    attacker_gains: dict[int, dict[str, float]] = field(default_factory=dict)
    defender_losses: dict[str, float] = field(default_factory=dict)

    # Configuration (set at battle creation time)
    broadcast_interval_ms: float = 250.0  # Configurable from game.yaml

    # -- Constants -------------------------------------------------------

    MIN_KEEP_ALIVE_MS: float = 10_000.0

    def should_broadcast(self) -> bool:
        """Check if enough time has passed for a network update."""
        return self.broadcast_timer_ms <= 0

    def reset_broadcast(self) -> None:
        """Reset broadcast timer and clear delta lists."""
        pass
