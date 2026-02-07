"""Empire service — manages empire state transitions.

Responsibilities:
- Resource generation (gold, culture, life) with citizen bonuses
- Building construction progress
- Research progress
- Citizen management
- Structure placement / removal
- Effect accumulation
- Life management

All methods operate on Empire model objects. No network I/O.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from gameserver.engine.upgrade_provider import UpgradeProvider
    from gameserver.util.events import EventBus

from gameserver.models.empire import Empire
from gameserver.util.constants import CITIZEN_EFFECT

log = logging.getLogger(__name__)

# Base generation rates per second
_BASE_GOLD_PER_SEC = 1.0
_BASE_CULTURE_PER_SEC = 0.5


class EmpireService:
    """Service for all empire state management.

    Args:
        upgrade_provider: Tech tree database for item lookups.
        event_bus: Event bus for inter-service communication.
    """

    def __init__(self, upgrade_provider: UpgradeProvider, event_bus: EventBus) -> None:
        self._upgrades = upgrade_provider
        self._events = event_bus
        self._empires: dict[int, Empire] = {}  # uid → Empire

    # -- Empire registry -------------------------------------------------

    def register(self, empire: Empire) -> None:
        """Add an empire to the managed set."""
        self._empires[empire.uid] = empire
        log.info("Empire registered: uid=%d name=%r", empire.uid, empire.name)

    def unregister(self, uid: int) -> Optional[Empire]:
        """Remove and return an empire from the managed set."""
        return self._empires.pop(uid, None)

    def get(self, uid: int) -> Optional[Empire]:
        """Look up an empire by UID."""
        return self._empires.get(uid)

    @property
    def all_empires(self) -> dict[int, Empire]:
        """Read-only access to all managed empires."""
        return self._empires

    # -- Tick ------------------------------------------------------------

    def step_all(self, dt: float) -> None:
        """Advance all registered empires by dt seconds."""
        for empire in self._empires.values():
            self.step(empire, dt)

    def step(self, empire: Empire, dt: float) -> None:
        """Advance a single empire by dt seconds: resources, building, research."""
        self._generate_resources(empire, dt)
        self._progress_buildings(empire, dt)
        self._progress_knowledge(empire, dt)

    # -- Resource generation ---------------------------------------------

    def _generate_resources(self, empire: Empire, dt: float) -> None:
        """Generate gold and culture based on citizens and effects."""
        # Gold: base + merchant bonus
        merchant_count = empire.citizens.get("merchant", 0)
        gold_modifier = 1.0 + merchant_count * CITIZEN_EFFECT
        gold_modifier += empire.get_effect("gold_bonus", 0.0)
        empire.resources["gold"] += _BASE_GOLD_PER_SEC * gold_modifier * dt

        # Culture: base + artist bonus
        artist_count = empire.citizens.get("artist", 0)
        culture_modifier = 1.0 + artist_count * CITIZEN_EFFECT
        culture_modifier += empire.get_effect("culture_bonus", 0.0)
        empire.resources["culture"] += _BASE_CULTURE_PER_SEC * culture_modifier * dt

    # -- Build progress --------------------------------------------------

    def _progress_buildings(self, empire: Empire, dt: float) -> None:
        """Tick building construction. Emits ItemCompleted when done."""
        completed = []
        for iid, remaining in empire.buildings.items():
            if remaining <= 0:
                continue  # already finished
            remaining -= dt
            if remaining <= 0:
                remaining = 0.0
                completed.append(iid)
            empire.buildings[iid] = remaining

        for iid in completed:
            log.info("Empire %d: building %s completed", empire.uid, iid)
            # TODO: emit ItemCompleted event, apply effects

    def _progress_knowledge(self, empire: Empire, dt: float) -> None:
        """Tick research progress. Emits ItemCompleted when done."""
        completed = []
        for iid, remaining in empire.knowledge.items():
            if remaining <= 0:
                continue
            # Scientist bonus
            scientist_count = empire.citizens.get("scientist", 0)
            speed = 1.0 + scientist_count * CITIZEN_EFFECT
            speed += empire.get_effect("research_bonus", 0.0)
            remaining -= dt * speed
            if remaining <= 0:
                remaining = 0.0
                completed.append(iid)
            empire.knowledge[iid] = remaining

        for iid in completed:
            log.info("Empire %d: knowledge %s completed", empire.uid, iid)
            # TODO: emit ItemCompleted event, apply effects

    # -- Actions ---------------------------------------------------------

    def build_item(self, empire: Empire, iid: str) -> Optional[str]:
        """Start building/researching an item. Returns error message or None."""
        # TODO: implement full requirement checks + cost deduction
        pass

    def place_structure(self, empire: Empire, iid: str, q: int, r: int) -> Optional[str]:
        """Place a structure on the map. Returns error message or None."""
        # TODO: implement
        pass

    def remove_structure(self, empire: Empire, sid: int) -> Optional[str]:
        """Remove a structure from the map. Returns error message or None."""
        # TODO: implement
        pass

    def upgrade_citizen(self, empire: Empire) -> Optional[str]:
        """Add one citizen. Returns error message or None."""
        # TODO: implement
        pass

    def change_citizens(self, empire: Empire, distribution: dict[str, int]) -> Optional[str]:
        """Redistribute citizens. Returns error message or None."""
        # TODO: implement
        pass
