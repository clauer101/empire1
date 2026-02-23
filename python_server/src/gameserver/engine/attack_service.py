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
    from gameserver.models.army import Army
    from gameserver.util.events import EventBus

from gameserver.models.attack import Attack, AttackPhase

log = logging.getLogger(__name__)


class AttackService:
    """Service managing attack travel and siege.

    Args:
        event_bus: Event bus for attack lifecycle events.
        game_config: Game configuration for travel/siege timings.
        empire_service: Empire service for defender lookups.
    """

    def __init__(self, event_bus: EventBus,
                 game_config: GameConfig | None = None,
                 empire_service: EmpireService | None = None) -> None:
        self._events = event_bus
        self._empire_service = empire_service
        self._attacks: list[Attack] = []
        self._base_travel_offset = (
            game_config.base_travel_offset if game_config else 300.0
        )
        self._base_siege_offset = (
            game_config.base_siege_offset if game_config else 900.0
        )
        self._next_attack_id: int = 1
        self._broadcast_timer: dict[int, float] = {}  # attack_id -> seconds since last broadcast
        self._battles_started: set[int] = set()  # attack_ids that have already emitted BattleStartRequested

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

    def get(self, attack_id: int) -> Attack | None:
        """Return the attack with the given ID, if it exists."""
        for attack in self._attacks:
            if attack.attack_id == attack_id:
                return attack
        return None

    def skip_siege(self, attack_id: int, requester_uid: int) -> Attack | str:
        """Immediately end the siege phase for attack_id.

        Only the defender may call this.
        Returns the Attack on success, or an error string.
        """
        attack = self.get(attack_id)
        if attack is None:
            return f"Attack {attack_id} not found"
        if attack.phase != AttackPhase.IN_SIEGE:
            return f"Attack {attack_id} is not in IN_SIEGE phase (current: {attack.phase.value})"
        if attack.defender_uid != requester_uid:
            return "Only the defender can use Fight now!"
        attack.siege_remaining_seconds = 0.0
        log.info(
            "Siege skipped: attack_id=%d defender=%d attacker=%d",
            attack_id, attack.defender_uid, attack.attacker_uid,
        )
        return attack

    def restore_attacks(self, attacks: list[Attack]) -> None:
        """Restore persisted attacks and advance the ID counter past all existing IDs."""
        self._attacks.extend(attacks)
        if attacks:
            self._next_attack_id = max(a.attack_id for a in attacks) + 1
            log.info(
                "Restored %d attacks; next_attack_id set to %d",
                len(attacks), self._next_attack_id,
            )

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

        # Calculate travel time: base + attacker.TRAVEL_TIME_OFFSET
        # Negative offset = faster travel; positive = slower.
        from gameserver.util import effects as fx
        travel_offset = att_empire.get_effect(fx.TRAVEL_TIME_OFFSET, 0.0)
        eta = max(1.0, self._base_travel_offset + travel_offset)

        attack = Attack(
            attack_id=self._next_attack_id,
            attacker_uid=attacker_uid,
            defender_uid=defender_uid,
            army_aid=army_aid,
            phase=AttackPhase.TRAVELLING,
            eta_seconds=eta,
            total_eta_seconds=eta,
        )
        self._next_attack_id += 1

        self._attacks.append(attack)

        log.info(
            "Attack started: id=%d  %d→%d  army=%d  ETA=%.0fs",
            attack.attack_id, attacker_uid, defender_uid, army_aid, eta,
        )
        return attack

    def start_ai_attack(
        self,
        defender_uid: int,
        army: Army,
        travel_seconds: float = 30.0,
    ) -> Attack | str:
        """Launch an AI attack against *defender_uid* using a pre-built army.

        Siege time is intentionally left at 0 — it will be computed at the
        TRAVELLING→IN_SIEGE transition using the defender's current effects.

        Args:
            defender_uid:   UID of the player to attack.
            army:           Pre-generated Army (already registered with AI
                            empire via empire_service).
            travel_seconds: Travel time before the attack arrives.

        Returns:
            The new Attack object, or an error string.
        """
        from gameserver.engine.ai_service import AI_UID

        attack = Attack(
            attack_id=self._next_attack_id,
            attacker_uid=AI_UID,
            defender_uid=defender_uid,
            army_aid=army.aid,
            phase=AttackPhase.TRAVELLING,
            eta_seconds=travel_seconds,
            total_eta_seconds=travel_seconds,
            # siege set to 0: computed at TRAVELLING→IN_SIEGE from defender effects
        )
        self._next_attack_id += 1
        self._attacks.append(attack)

        log.info(
            "[AI_ATTACK] Attack queued: id=%d  AI→%d  army=%d  ETA=%.0fs",
            attack.attack_id, defender_uid, army.aid, travel_seconds,
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

                # Always compute siege duration at transition using defender's
                # current effects (INCOMING_SIEGE_TIME_OFFSET, etc.)
                siege_duration = self._calculate_siege_duration(
                    attack.attacker_uid, attack.defender_uid
                )
                attack.siege_remaining_seconds = siege_duration
                attack.total_siege_seconds = siege_duration
                    
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
                # Mark battle as started and return attack object so caller can start battle
                self._battles_started.add(attack.attack_id)
                return attack
        
        # Handle case where attack was loaded from persistent state already IN_BATTLE
        if attack.phase == AttackPhase.IN_BATTLE and attack.attack_id not in self._battles_started:
            log.info(
                "[STATE] Attack %d: Recovered from saved state IN_BATTLE (attacker=%d, defender=%d, army=%d)",
                attack.attack_id, attack.attacker_uid,
                attack.defender_uid, attack.army_aid,
            )
            self._battles_started.add(attack.attack_id)
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
            
            # Broadcast battle status to observers during IN_SIEGE and IN_BATTLE
            if attack.phase in (AttackPhase.IN_SIEGE, AttackPhase.IN_BATTLE):
                # Throttle broadcasts to 1 per second
                if attack.attack_id not in self._broadcast_timer:
                    self._broadcast_timer[attack.attack_id] = 0.0
                
                self._broadcast_timer[attack.attack_id] += dt
                
                if self._broadcast_timer[attack.attack_id] >= 1.0:
                    self._broadcast_timer[attack.attack_id] = 0.0
                    # Emit event for observers to receive updates
                    from gameserver.util.events import BattleObserverBroadcast
                    self._events.emit(BattleObserverBroadcast(attack_id=attack.attack_id))
        
        # Prune finished attacks
        self._attacks = [
            a for a in self._attacks if a.phase != AttackPhase.FINISHED
        ]
        
        return battles_to_start

    # -- Helpers ---------------------------------------------------------

    def _calculate_siege_duration(self, attacker_uid: int, defender_uid: int) -> float:
        """Calculate siege duration at TRAVELLING→IN_SIEGE transition.

        Formula:
            result = max(1.0, base_siege_offset + defender.SIEGE_TIME_OFFSET)

        The same base applies for both AI and player attackers so that the
        defender's SIEGE_TIME_OFFSET effects are meaningful regardless of who
        is attacking.  Computed fresh each time so buildings completed during
        travel are reflected.
        """
        from gameserver.util import effects as fx

        base = self._base_siege_offset

        if not self._empire_service:
            return base

        defender = self._empire_service.get(defender_uid)
        if not defender:
            log.warning(
                "Defender %d not found for siege calculation, using base %.1fs",
                defender_uid, base,
            )
            return base

        offset = defender.get_effect(fx.SIEGE_TIME_OFFSET, 0.0)
        result = max(1.0, base + offset)
        log.debug(
            "Siege duration %d→%d: %.1fs (base_siege=%.1f, defender_offset=%.3f)",
            attacker_uid, defender_uid, result, base, offset,
        )
        return result
