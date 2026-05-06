"""Battle state model — data container for an active battle.

The BattleState holds all mutable state for a running battle.
Business logic is in engine/battle_service.py.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, TYPE_CHECKING

from gameserver.models.critter import Critter
from gameserver.models.shot import Shot
from gameserver.models.structure import Structure
from gameserver.models.hex import HexCoord

if TYPE_CHECKING:
    from gameserver.models.army import Army
    from gameserver.models.empire import Empire
    from gameserver.persistence.replay import ReplayRecorder


@dataclass
class BattleState:
    """Mutable state container for an active tower-defense battle.

    Supports multiple simultaneous attackers against the same defender.
    All attackers share a single critter pool; towers fire at the combined
    pool at their normal reload rate.

    Attributes:
        bid: Unique battle ID.
        defender: The defending empire.
        attacker_uids: UIDs of all attacking players (join order).
        attack_ids: Attack IDs of all participating attacks.
        armies: Active armies keyed by attacker UID.

        critters: All live critters on the field, keyed by CID.
        structures: Defender's towers, keyed by SID.
        pending_shots: Shots in flight.
        critter_path: Precomputed path for critters to follow.

        observer_uids: UIDs of players watching this battle.
        attacker_gains: Resources gained per attacker UID.
        defender_losses: Resources lost by defender.
    """

    bid: int
    defender: Empire | None

    attacker_uids: list[int] = field(default_factory=list)
    attack_ids: list[int] = field(default_factory=list)
    armies: dict[int, Army] = field(default_factory=dict)  # attack_id -> Army

    critters: dict[int, Critter] = field(default_factory=dict)
    structures: dict[int, Structure] = field(default_factory=dict)
    pending_shots: list[Shot] = field(default_factory=list)

    critter_path: list[HexCoord] = field(default_factory=list)

    elapsed_ms: float = 0.0
    broadcast_timer_ms: float = 0.0
    keep_alive: bool = True
    is_finished: bool = False
    defender_won: bool | None = None

    observer_uids: set[int] = field(default_factory=set)

    attacker_gains: dict[int, dict[str, float]] = field(default_factory=dict)
    defender_losses: dict[str, float] = field(default_factory=dict)
    defender_gold_earned: float = 0.0

    critters_spawned: int = 0
    critters_killed: int = 0
    critters_reached: int = 0

    # reason: "died" | "reached"
    removed_critters: list[dict[str, Any]] = field(default_factory=list)

    broadcast_interval_ms: float = 250.0
    recorder: ReplayRecorder | None = None

    MIN_KEEP_ALIVE_MS: float = 10_000.0

    # -- Backward-compat properties (single-attacker callers) ------------

    @property
    def attacker(self) -> Empire | None:
        """Primary attacker empire (first in join order)."""
        from gameserver.network.handlers._core import _svc
        svc = _svc()
        uid = self.attacker_uids[0] if self.attacker_uids else None
        if uid is None or svc.empire_service is None:
            return None
        return svc.empire_service.get(uid)

    @property
    def attack_id(self) -> int | None:
        """Primary attack ID (first in list)."""
        return self.attack_ids[0] if self.attack_ids else None

    @property
    def army(self) -> Army | None:
        """Primary army (first attack's army, keyed by attack_id)."""
        aid = self.attack_ids[0] if self.attack_ids else None
        return self.armies.get(aid) if aid is not None else None  # type: ignore[arg-type]

    def should_broadcast(self) -> bool:
        return self.broadcast_timer_ms <= 0

    def reset_broadcast(self) -> None:
        pass
