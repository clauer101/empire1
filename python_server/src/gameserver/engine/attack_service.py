"""Attack service — manages travel and siege state machine.

Handles the lifecycle of attacks:
  TRAVELLING → IN_SIEGE → IN_BATTLE → FINISHED

Travel time decreases each tick. When ETA reaches 0, the army enters
the defender's siege queue. After the siege timer expires, a battle starts.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from gameserver.models.attack import Attack
    from gameserver.util.events import EventBus


class AttackService:
    """Service managing attack travel and siege.

    Args:
        event_bus: Event bus for attack lifecycle events.
    """

    def __init__(self, event_bus: EventBus) -> None:
        self._events = event_bus

    def step(self, attack: Attack, dt: float) -> None:
        """Advance attack by dt seconds."""
        # TODO: implement
        pass

    def start_attack(
        self, attacker_uid: int, defender_uid: int, army_aid: int
    ) -> Attack | str:
        """Initiate a new attack. Returns Attack or error string."""
        # TODO: implement
        pass  # type: ignore[return-value]
