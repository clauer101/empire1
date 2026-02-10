"""Typed event bus — decoupled inter-service communication.

Replaces the Java ICritterListener / IStructureListener interfaces
with a generic publish-subscribe event bus.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Callable, TypeVar, Type

T = TypeVar("T")


# -- Battle events -------------------------------------------------------

@dataclass(frozen=True)
class CritterStarted:
    """A critter was spawned onto the battlefield."""
    critter_id: int
    direction: str


@dataclass(frozen=True)
class CritterFinished:
    """A critter reached the end of its path."""
    critter_id: int
    with_transfer: bool


@dataclass(frozen=True)
class CritterDied:
    """A critter was killed."""
    critter_id: int


@dataclass(frozen=True)
class StructureShot:
    """A structure fired a shot."""
    structure_id: int
    shot_index: int  # index into battle.pending_shots


@dataclass(frozen=True)
class BattleFinished:
    """A battle has concluded."""
    battle_id: int
    defender_won: bool


# -- Attack events -------------------------------------------------------

@dataclass(frozen=True)
class AttackArrived:
    """An attack's travel time has expired."""
    attack_id: int
    defender_uid: int
    army_aid: int


@dataclass(frozen=True)
class BattleStartRequested:
    """Battle should start (siege phase complete)."""
    attack_id: int
    attacker_uid: int
    defender_uid: int
    army_aid: int


@dataclass(frozen=True)
class SiegeExpired:
    """A siege timer has expired, battle should start."""
    defender_uid: int


@dataclass(frozen=True)
class AttackPhaseChanged:
    """An attack's phase has changed (TRAVELLING → IN_SIEGE or IN_SIEGE → IN_BATTLE)."""
    attack_id: int
    attacker_uid: int
    defender_uid: int
    army_aid: int
    new_phase: str  # e.g. "in_siege" or "in_battle"


# -- Empire events -------------------------------------------------------

@dataclass(frozen=True)
class ItemCompleted:
    """A building or research item was completed."""
    empire_uid: int
    iid: str


# -- Event Bus -----------------------------------------------------------

class EventBus:
    """Simple synchronous event bus with typed events.

    Usage:
        bus = EventBus()
        bus.on(CritterDied, lambda e: print(e.critter_id))
        bus.emit(CritterDied(critter_id=42))
    """

    def __init__(self) -> None:
        self._handlers: dict[type, list[Callable[[Any], None]]] = defaultdict(list)

    def on(self, event_type: Type[T], handler: Callable[[T], None]) -> None:
        """Register a handler for an event type."""
        self._handlers[event_type].append(handler)

    def off(self, event_type: Type[T], handler: Callable[[T], None]) -> None:
        """Unregister a handler."""
        handlers = self._handlers.get(event_type, [])
        if handler in handlers:
            handlers.remove(handler)

    def emit(self, event: object) -> None:
        """Emit an event to all registered handlers."""
        for handler in self._handlers.get(type(event), []):
            handler(event)

    def clear(self) -> None:
        """Remove all handlers."""
        self._handlers.clear()
