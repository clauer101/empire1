"""Attack service — manages travel and siege state machine.

Handles the lifecycle of attacks:
  TRAVELLING → IN_SIEGE → IN_BATTLE → FINISHED

Travel time decreases each tick. When ETA reaches 0, the army arrives.
The arrival logic (siege/battle) is not yet implemented.
"""

from __future__ import annotations

import logging
from typing import Any, TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from gameserver.engine.empire_service import EmpireService
    from gameserver.loaders.game_config_loader import GameConfig
    from gameserver.models.army import Army
    from gameserver.util.events import EventBus

from gameserver.models.attack import Attack, AttackPhase
from gameserver.util.eras import ERA_ORDER, ERA_TRAVEL_FIELD

log = logging.getLogger(__name__)


class AttackService:
    """Service managing attack travel and siege.

    Args:
        event_bus: Event bus for attack lifecycle events.
        game_config: Game configuration for travel/siege timings.
        empire_service: Empire service for defender lookups.
    """

    _ERA_TRAVEL_FIELD: dict[str, str] = ERA_TRAVEL_FIELD
    _ERA_ORDER: list[str] = ERA_ORDER

    def __init__(self, event_bus: EventBus,
                 game_config: GameConfig | None = None,
                 empire_service: EmpireService | None = None,
                 knowledge_era_groups: dict[str, list[str]] | None = None) -> None:
        self._events = event_bus
        self._empire_service = empire_service
        self._game_config = game_config
        self._attacks: list[Attack] = []
        self._base_travel_offset = (
            game_config.base_travel_offset if game_config else 300.0
        )
        self._base_siege_offset = (
            game_config.base_siege_offset if game_config else 900.0
        )
        # era key → set of knowledge IIDs that belong to that era
        self._knowledge_era_groups: dict[str, list[str]] = knowledge_era_groups or {}
        self._next_attack_id: int = 1
        self._broadcast_timer: dict[int, float] = {}  # attack_id -> seconds since last broadcast
        self._battles_started: set[int] = set()  # attack_ids that have already emitted BattleStartRequested

    # -- Era travel offset -----------------------------------------------

    def _era_travel_offset(self, empire: Any) -> float:
        """Return the travel offset for the attacker's current era.

        Iterates eras in order; the highest era where at least one knowledge
        item is completed is the attacker's era. Falls back to base_travel_offset.
        """
        if not self._knowledge_era_groups or self._game_config is None:
            return self._base_travel_offset
        done = {iid for iid, remaining in empire.knowledge.items() if remaining == 0.0}
        era_key = self._ERA_ORDER[0]
        for key in self._ERA_ORDER:
            items = self._knowledge_era_groups.get(key, [])
            if any(iid in done for iid in items):
                era_key = key
        field_name = self._ERA_TRAVEL_FIELD.get(era_key, "")
        return getattr(self._game_config, field_name, self._base_travel_offset)

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
        for a in attacks:
            # Spy attacks that survived past IN_SIEGE (e.g. saved mid-transition)
            # should be finished immediately — they never battle.
            if a.is_spy and a.phase == AttackPhase.IN_SIEGE:
                log.info(
                    "[restore] Spy attack %d was in IN_SIEGE on load — finishing immediately",
                    a.attack_id,
                )
                from gameserver.util.events import SpyArrived
                self._events.emit(SpyArrived(
                    attack_id=a.attack_id,
                    attacker_uid=a.attacker_uid,
                    defender_uid=a.defender_uid,
                    army_aid=a.army_aid,
                ))
                a.phase = AttackPhase.FINISHED
        self._attacks.extend(a for a in attacks if a.phase != AttackPhase.FINISHED)
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
        is_spy: bool = False,
        spy_army_name: str = "",
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

        # Check army not already on a trip (spy attacks bypass this — they are invisible)
        if not is_spy:
            for existing in self._attacks:
                if (existing.attacker_uid == attacker_uid
                        and existing.army_aid == army_aid
                        and existing.phase != AttackPhase.FINISHED
                        and not existing.is_spy):
                    return "Army is already attacking"

        # Calculate travel time: (era_base + offset) × (1 - modifier)
        # TRAVEL_TIME_OFFSET: flat seconds added/removed (negative = faster)
        # TRAVEL_TIME_MODIFIER: percentage reduction 0.0–1.0 (0.5 = 50% faster)
        from gameserver.util import effects as fx
        travel_offset = att_empire.get_effect(fx.TRAVEL_TIME_OFFSET, 0.0)
        travel_modifier = att_empire.get_effect(fx.TRAVEL_TIME_MODIFIER, 0.0)
        eta_base = self._era_travel_offset(att_empire) + travel_offset
        eta = max(1.0, eta_base * (1.0 - travel_modifier))
        if is_spy:
            eta = max(1.0, eta / 2.0)
            # Unique virtual army_aid that never collides with real armies
            army_aid = 10_000_000 + self._next_attack_id

        attack = Attack(
            attack_id=self._next_attack_id,
            attacker_uid=attacker_uid,
            defender_uid=defender_uid,
            army_aid=army_aid,
            phase=AttackPhase.TRAVELLING,
            eta_seconds=eta,
            total_eta_seconds=eta,
            is_spy=is_spy,
            army_name_override=spy_army_name,
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
        siege_seconds: float | None = None,
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
            override_siege_seconds=siege_seconds,
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
                log.info(
                    "[STATE] Attack %d: TRAVELLING → IN_SIEGE (attacker=%d, defender=%d, army=%d, spy=%s)",
                    attack.attack_id, attack.attacker_uid,
                    attack.defender_uid, attack.army_aid, attack.is_spy,
                )
                attack.phase = AttackPhase.IN_SIEGE

                if attack.is_spy:
                    # Spy attacks skip siege entirely — emit SpyArrived and finish immediately
                    from gameserver.util.events import AttackPhaseChanged, SpyArrived
                    # Briefly notify defender it arrived (looks real)
                    self._events.emit(AttackPhaseChanged(
                        attack_id=attack.attack_id,
                        attacker_uid=attack.attacker_uid,
                        defender_uid=attack.defender_uid,
                        army_aid=attack.army_aid,
                        new_phase="in_siege",
                    ))
                    self._events.emit(SpyArrived(
                        attack_id=attack.attack_id,
                        attacker_uid=attack.attacker_uid,
                        defender_uid=attack.defender_uid,
                        army_aid=attack.army_aid,
                    ))
                    attack.phase = AttackPhase.FINISHED
                else:
                    # Use explicit siege_seconds as base if set, otherwise use config base;
                    # always apply defender's SIEGE_TIME_OFFSET on top.
                    if attack.override_siege_seconds is not None:
                        siege_duration = self._calculate_siege_duration(
                            attack.attacker_uid, attack.defender_uid,
                            base_override=float(attack.override_siege_seconds),
                        )
                    else:
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

    def _calculate_siege_duration(
        self,
        attacker_uid: int,
        defender_uid: int,
        base_override: float | None = None,
    ) -> float:
        """Calculate siege duration at TRAVELLING→IN_SIEGE transition.

        Formula:
            result = max(1.0, base + defender.SIEGE_TIME_OFFSET)

        where base is base_override (from ai_waves siege_time) if provided,
        otherwise self._base_siege_offset from game config.
        Computed fresh each time so buildings completed during travel are reflected.
        """
        from gameserver.util import effects as fx

        base = base_override if base_override is not None else self._base_siege_offset

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
            "Siege duration %d→%d: %.1fs (base=%.1f%s, defender_offset=%.3f)",
            attacker_uid, defender_uid, result, base,
            " [override]" if base_override is not None else "", offset,
        )
        return result
