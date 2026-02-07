"""Army service — army creation, cost calculation, wave management.

Handles:
- Army creation and validation
- Wave slot calculation (scales with wave index)
- Critter cost calculation
- Spy army options and costs
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from gameserver.engine.upgrade_provider import UpgradeProvider
    from gameserver.models.army import Army
    from gameserver.models.empire import Empire
    from gameserver.util.events import EventBus


class ArmyService:
    """Service for army management.

    Args:
        upgrade_provider: Item database for critter lookups.
        event_bus: Event bus for army lifecycle events.
    """

    def __init__(self, upgrade_provider: UpgradeProvider, event_bus: EventBus) -> None:
        self._upgrades = upgrade_provider
        self._events = event_bus

    def create_army(self, empire: Empire, direction: str, name: str) -> Army | str:
        """Create a new army. Returns Army or error string."""
        # TODO: implement
        pass  # type: ignore[return-value]

    def calculate_cost(self, army: Army) -> float:
        """Calculate the gold cost to deploy an army."""
        # TODO: implement
        return 0.0

    def calculate_slots(self, wave_index: int, empire: Empire) -> int:
        """Calculate available slots for a wave at the given index."""
        # TODO: implement
        return 0
