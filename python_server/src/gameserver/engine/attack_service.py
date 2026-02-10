"""Attack service — manages travel and siege state machine.

Handles the lifecycle of attacks:
  TRAVELLING → IN_SIEGE → IN_BATTLE → FINISHED

Travel time decreases each tick. When ETA reaches 0, the army arrives.
The arrival logic (siege/battle) is not yet implemented.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from gameserver.engine.empire_service import EmpireService
    from gameserver.loaders.game_config_loader import GameConfig
    from gameserver.util.events import EventBus

from gameserver.models.attack import Attack, AttackPhase

log = logging.getLogger(__name__)

_next_attack_id: int = 1


class AttackService:
    """Service managing attack travel and siege.

    Args:
        event_bus: Event bus for attack lifecycle events.
    """

    def __init__(self, event_bus: EventBus,
                 game_config: GameConfig | None = None) -> None:
        self._events = event_bus
        self._attacks: list[Attack] = []
        self._base_travel_offset = (
            game_config.base_travel_offset if game_config else 5400.0
        )

    # -- Query -----------------------------------------------------------

    def get_incoming(self, uid: int) -> list[Attack]:
        """Return all ongoing attacks targeting the given defender UID."""
        return [a for a in self._attacks if a.defender_uid == uid
                and a.phase != AttackPhase.FINISHED]

    def get_outgoing(self, uid: int) -> list[Attack]:
        """Return all ongoing attacks launched by the given attacker UID."""
        return [a for a in self._attacks if a.attacker_uid == uid
                and a.phase != AttackPhase.FINISHED]

    def get_all_attacks(self) -> list[Attack]:
        """Return all attacks (for persistence/debugging)."""
        return list(self._attacks)

    # -- Lifecycle -------------------------------------------------------

    def start_attack(
        self,
        attacker_uid: int,
        defender_uid: int,
        army_aid: int,
        empire_service: EmpireService,
    ) -> Attack | str:
        """Initiate a new attack. Returns Attack or error string.

        Validation mirrors the Java HandleAttackRequest:
        - attacker / defender exist
        - not self-attack
        - army exists, has waves, not already travelling
        """
        att_empire = empire_service.get(attacker_uid)
        def_empire = empire_service.get(defender_uid)

        if att_empire is None or def_empire is None:
            return "Attacker or defender empire not found"

        if attacker_uid == defender_uid:
            return "Cannot attack yourself"

        # Resolve army
        army = None
        for a in att_empire.armies:
            if a.aid == army_aid:
                army = a
                break

        if army is None:
            return f"Army {army_aid} not found"

        if not army.waves:
            return "Army has no waves"

        # Check army not already on a trip
        for existing in self._attacks:
            if (existing.attacker_uid == attacker_uid
                    and existing.army_aid == army_aid
                    and existing.phase != AttackPhase.FINISHED):
                return "Army is already attacking"

        # Calculate ETA
        # TODO: use base_travel_offset * travel_modifier from config/effects
        eta = 60.0  # hardcoded 60 seconds for testing

        global _next_attack_id
        attack = Attack(
            attack_id=_next_attack_id,
            attacker_uid=attacker_uid,
            defender_uid=defender_uid,
            army_aid=army_aid,
            phase=AttackPhase.TRAVELLING,
            eta_seconds=eta,
            total_eta_seconds=eta,
        )
        _next_attack_id += 1

        self._attacks.append(attack)

        log.info(
            "Attack started: id=%d  %d→%d  army=%d  ETA=%.0fs",
            attack.attack_id, attacker_uid, defender_uid, army_aid, eta,
        )
        return attack

    # -- Tick ------------------------------------------------------------

    def step(self, attack: Attack, dt: float) -> Optional[Attack]:
        """Advance a single attack by dt seconds.
        
        Returns the Attack object when it transitions to IN_BATTLE,
        None otherwise.
        """
        if attack.phase == AttackPhase.TRAVELLING:
            attack.eta_seconds = max(attack.eta_seconds - dt, 0.0)
            if attack.eta_seconds <= 0.0:
                # Army has arrived — enter siege phase
                log.info(
                    "[STATE] Attack %d: TRAVELLING → IN_SIEGE (attacker=%d, defender=%d, army=%d)",
                    attack.attack_id, attack.attacker_uid,
                    attack.defender_uid, attack.army_aid,
                )
                attack.phase = AttackPhase.IN_SIEGE
                # Siege duration: 30 seconds (TODO: config)
                attack.siege_remaining_seconds = 30.0
                # Store total siege duration for progress calculation
                if attack.total_siege_seconds == 0.0:
                    attack.total_siege_seconds = 30.0
                # Emit event for push notification to clients
                from gameserver.util.events import AttackPhaseChanged
                self._events.emit(AttackPhaseChanged(
                    attack_id=attack.attack_id,
                    attacker_uid=attack.attacker_uid,
                    defender_uid=attack.defender_uid,
                    army_aid=attack.army_aid,
                    new_phase="in_siege",
                ))
                
        elif attack.phase == AttackPhase.IN_SIEGE:
            attack.siege_remaining_seconds = max(attack.siege_remaining_seconds - dt, 0.0)
            if attack.siege_remaining_seconds <= 0.0:
                # Siege complete — start battle
                log.info(
                    "[STATE] Attack %d: IN_SIEGE → IN_BATTLE (attacker=%d, defender=%d, army=%d)",
                    attack.attack_id, attack.attacker_uid,
                    attack.defender_uid, attack.army_aid,
                )
                attack.phase = AttackPhase.IN_BATTLE
                # Emit event for push notification to clients
                from gameserver.util.events import AttackPhaseChanged
                self._events.emit(AttackPhaseChanged(
                    attack_id=attack.attack_id,
                    attacker_uid=attack.attacker_uid,
                    defender_uid=attack.defender_uid,
                    army_aid=attack.army_aid,
                    new_phase="in_battle",
                ))
                # Return attack object so caller can start battle
                return attack
        
        return None

    def step_all(self, dt: float) -> list[Attack]:
        """Advance all ongoing attacks by dt seconds.
        
        Returns list of Attack objects for battles that should start.
        """
        battles_to_start = []
        
        for attack in self._attacks:
            result = self.step(attack, dt)
            if result:
                battles_to_start.append(result)
        
        # Prune finished attacks
        self._attacks = [
            a for a in self._attacks if a.phase != AttackPhase.FINISHED
        ]
        
        return battles_to_start
