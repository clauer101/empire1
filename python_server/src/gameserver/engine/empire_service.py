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
    from gameserver.loaders.game_config_loader import GameConfig
    from gameserver.util.events import EventBus

from gameserver.models.empire import Empire

log = logging.getLogger(__name__)


class EmpireService:
    """Service for all empire state management.

    Args:
        upgrade_provider: Tech tree database for item lookups.
        event_bus: Event bus for inter-service communication.
    """

    def __init__(self, upgrade_provider: UpgradeProvider, event_bus: EventBus,
                 game_config: GameConfig | None = None) -> None:
        self._upgrades = upgrade_provider
        self._events = event_bus
        self._empires: dict[int, Empire] = {}  # uid → Empire

        # Game balance constants (fall back to defaults if no config)
        if game_config is not None:
            self._base_gold = game_config.base_gold_per_sec
            self._base_culture = game_config.base_culture_per_sec
            self._citizen_effect = game_config.citizen_effect
            self._base_build_speed = game_config.base_build_speed
            self._base_research_speed = game_config.base_research_speed
        else:
            self._base_gold = 1.0
            self._base_culture = 0.5
            self._citizen_effect = 0.03
            self._base_build_speed = 1.0
            self._base_research_speed = 1.0

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

    def find_by_name(self, name: str) -> Optional[Empire]:
        """Look up an empire by name (case-insensitive)."""
        name_lower = name.lower()
        for empire in self._empires.values():
            if empire.name.lower() == name_lower:
                return empire
        return None

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
        # Gold: base * modifier + offset
        merchant_count = empire.citizens.get("merchant", 0)
        gold_modifier = merchant_count * self._citizen_effect
        gold_modifier += empire.get_effect("gold_modifier", 0.0)
        gold_offset = empire.get_effect("gold_offset", 0.0)
        empire.resources["gold"] += ((self._base_gold + gold_offset) * (1 + gold_modifier )) * dt

        # Culture: base * modifier + offset
        artist_count = empire.citizens.get("artist", 0)
        culture_modifier = artist_count * self._citizen_effect
        culture_modifier += empire.get_effect("culture_modifier", 0.0)
        culture_offset = empire.get_effect("culture_offset", 0.0)
        empire.resources["culture"] += ((self._base_culture + culture_offset) * (1 + culture_modifier)) * dt

        # Life: offset only (restore_life)
        life_offset = empire.get_effect("life_offset", 0.0)
        if life_offset > 0:
            empire.resources["life"] = min(
                empire.resources.get("life", 0.0) + life_offset * dt,
                empire.max_life,
            )

    # -- Build progress --------------------------------------------------

    def _progress_buildings(self, empire: Empire, dt: float) -> None:
        """Tick building construction for the single active build item."""
        if empire.build_queue is None:
            return

        iid = empire.build_queue
        remaining = empire.buildings.get(iid, 0.0)
        if remaining <= 0:
            empire.build_queue = None
            return

        # Build speed: (base + offset) * (1 + modifier)
        speed = (self._base_build_speed + empire.get_effect("build_speed_offset", 0.0)) * (1.0 + empire.get_effect("build_speed_modifier", 0.0))
        remaining -= dt * speed
        if remaining <= 0:
            remaining = 0.0
            empire.build_queue = None
            self._apply_effects(empire, iid)
            empire.buildings[iid] = remaining
            log.info("Empire %d: building %s completed", empire.uid, iid)
            from gameserver.util.events import ItemCompleted
            self._events.emit(ItemCompleted(empire_uid=empire.uid, iid=iid))
            return
        empire.buildings[iid] = remaining

    def _progress_knowledge(self, empire: Empire, dt: float) -> None:
        """Tick research progress for the single active research item."""
        if empire.research_queue is None:
            return

        iid = empire.research_queue
        remaining = empire.knowledge.get(iid, 0.0)
        if remaining <= 0:
            empire.research_queue = None
            return

        # Research speed: (base + offset) * (1 + modifier + n_scientists * citizen_effect)
        scientist_count = empire.citizens.get("scientist", 0)
        speed = (self._base_research_speed + empire.get_effect("research_speed_offset", 0.0)) * (1.0 + empire.get_effect("research_speed_modifier", 0.0) + scientist_count * self._citizen_effect)
        remaining -= dt * speed
        if remaining <= 0:
            remaining = 0.0
            empire.research_queue = None
            self._apply_effects(empire, iid)
            empire.knowledge[iid] = remaining
            log.info("Empire %d: knowledge %s completed", empire.uid, iid)
            from gameserver.util.events import ItemCompleted
            self._events.emit(ItemCompleted(empire_uid=empire.uid, iid=iid))
            return
        empire.knowledge[iid] = remaining

    # -- Effects ---------------------------------------------------------

    def _apply_effects(self, empire: Empire, iid: str) -> None:
        """Add the effects of a completed item to the empire."""
        effects = self._upgrades.get_effects(iid)
        for key, value in effects.items():
            empire.effects[key] = empire.effects.get(key, 0.0) + value
        if effects:
            log.info("Empire %d: applied effects for %s: %s", empire.uid, iid, effects)

    def recalculate_effects(self, empire: Empire) -> None:
        """Rebuild empire effects from all completed buildings and knowledge.

        Call this on server startup / state restore to ensure effects
        match the actually completed items.
        """
        empire.effects.clear()
        for iid, remaining in empire.buildings.items():
            if remaining <= 0:
                effects = self._upgrades.get_effects(iid)
                for key, value in effects.items():
                    empire.effects[key] = empire.effects.get(key, 0.0) + value
        for iid, remaining in empire.knowledge.items():
            if remaining <= 0:
                effects = self._upgrades.get_effects(iid)
                for key, value in effects.items():
                    empire.effects[key] = empire.effects.get(key, 0.0) + value
        log.info("Empire %d: recalculated effects → %s", empire.uid, empire.effects)

    # -- Actions ---------------------------------------------------------

    def build_item(self, empire: Empire, iid: str) -> Optional[str]:
        """Start building/researching an item. Returns error message or None.

        Validates requirements, deducts costs, and enqueues the item.
        If another item is already in the queue, it is paused (progress saved)
        and the new item takes over.
        Buildings go to ``build_queue``, knowledge to ``research_queue``.
        """
        item = self._upgrades.get(iid)
        if item is None:
            return f"Unknown item: {iid}"

        # Build completed set for requirement check
        completed: set[str] = set()
        for k, v in empire.buildings.items():
            if v <= 0:
                completed.add(k)
        for k, v in empire.knowledge.items():
            if v <= 0:
                completed.add(k)
        completed.update(empire.artefacts)

        if not self._upgrades.check_requirements(iid, completed):
            return f"Requirements not met for {iid}"

        from gameserver.models.items import ItemType

        if item.item_type == ItemType.BUILDING:
            if iid in empire.buildings and empire.buildings[iid] <= 0:
                return f"Building {iid} already completed"
            # Check if building is starting for the first time (costs only paid once)
            is_new_start = iid not in empire.buildings
            # Deduct costs only on first start
            if is_new_start:
                for res, cost in item.costs.items():
                    current = empire.resources.get(res, 0.0)
                    if current < cost:
                        return f"Not enough {res} (need {cost}, have {current:.1f})"
                for res, cost in item.costs.items():
                    empire.resources[res] -= cost
            # Enqueue (replace current build queue item)
            # Only set effort if not already started (not in dict or already completed)
            if is_new_start:
                empire.buildings[iid] = float(item.effort)
            if item.effort > 0:
                empire.build_queue = iid
            log.info("Empire %d: started building %s (effort=%s)", empire.uid, iid, item.effort)

        elif item.item_type == ItemType.KNOWLEDGE:
            if iid in empire.knowledge and empire.knowledge[iid] <= 0:
                return f"Knowledge {iid} already completed"
            # Check if research is starting for the first time (costs only paid once)
            is_new_start = iid not in empire.knowledge
            # Deduct costs only on first start
            if is_new_start:
                for res, cost in item.costs.items():
                    current = empire.resources.get(res, 0.0)
                    if current < cost:
                        return f"Not enough {res} (need {cost}, have {current:.1f})"
                for res, cost in item.costs.items():
                    empire.resources[res] -= cost
            # Enqueue (replace current research queue item)
            # Only set effort if not already started (not in dict or already completed)
            if is_new_start:
                empire.knowledge[iid] = float(item.effort)
            if item.effort > 0:
                empire.research_queue = iid
            log.info("Empire %d: started research %s (effort=%s)", empire.uid, iid, item.effort)

        else:
            return f"Cannot build item of type {item.item_type.value}"

        return None

    def place_structure(self, empire: Empire, iid: str, q: int, r: int) -> Optional[str]:
        """Place a structure on the map. Returns error message or None."""
        # TODO: implement
        pass

    def remove_structure(self, empire: Empire, sid: int) -> Optional[str]:
        """Remove a structure from the map. Returns error message or None."""
        # TODO: implement
        pass

    def upgrade_citizen(self, empire: Empire) -> Optional[str]:
        """Add one new citizen as an artist. Returns error message or None."""
        # Migrate any legacy free citizens to artist
        if empire.citizens.get("free", 0) > 0:
            empire.citizens["artist"] = empire.citizens.get("artist", 0) + empire.citizens.pop("free")
        n = sum(empire.citizens.values())
        price = self._citizen_price(n + 1)
        if empire.resources.get("culture", 0.0) < price:
            return f"Not enough culture (need {price:.1f}, have {empire.resources.get('culture', 0.0):.1f})"
        empire.citizens["artist"] = empire.citizens.get("artist", 0) + 1
        return None

    def _citizen_price(self, i: int) -> float:
        # sigmoid(i, MAX=60000, MIN=66, SPREAD=13, STEEP=8)
        import math
        maxv, minv, spread, steep = 50000, 100, 14, 7.5
        return minv + (maxv - minv) / (1 + math.exp((-7 * i) / spread + steep))
    
    def _tile_price(self, i: int) -> float:
        # sigmoid(i, MAX=30000, MIN=10, SPREAD=5, STEEP=5)
        import math
        maxv, minv, spread, steep = 47000, 100, 29, 8.5
        return minv + (maxv - minv) / (1 + math.exp((-7 * i) / spread + steep))

    def _wave_price(self, i: int) -> float:
        # Price for adding the i-th wave to an army
        # sigmoid(i, MAX=8000, MIN=50, SPREAD=12, STEEP=7)
        import math
        maxv, minv, spread, steep = 28000, 100, 12, 7
        return minv + (maxv - minv) / (1 + math.exp((-7 * i) / spread + steep))
    
    def _critter_slot_price(self, i: int) -> float:
        # Price for adding the i-th critter slot to a wave
        # sigmoid(i, MAX=3000, MIN=20, SPREAD=15, STEEP=6)
        import math
        maxv, minv, spread, steep = 13000, 25, 23, 7
        return minv + (maxv - minv) / (1 + math.exp((-7 * i) / spread + steep))

    def _army_price(self, i: int) -> float:
        # Price for creating the i-th army
        # sigmoid(i, MAX=15000, MIN=100, SPREAD=10, STEEP=6)
        import math
        maxv, minv, spread, steep = 75000, 1000, 7, 6
        return minv + (maxv - minv) / (1 + math.exp((-7 * i) / spread + steep))


    def change_citizens(self, empire: Empire, distribution: dict[str, int]) -> Optional[str]:
        """Redistribute citizens among roles. Returns error message or None.
        
        Args:
            empire: Target empire
            distribution: Dict like {'merchant': 2, 'scientist': 1, 'artist': 3}
                         Total must equal current total.
        
        Returns:
            Error message if validation fails, None on success.
        """
        # Valid citizen roles
        valid_roles = {"merchant", "scientist", "artist"}

        # Migrate any legacy free citizens to artist first
        if empire.citizens.get("free", 0) > 0:
            empire.citizens["artist"] = empire.citizens.get("artist", 0) + empire.citizens.pop("free")

        # Get current total (exclude free if still present from old state)
        current_total = sum(v for k, v in empire.citizens.items() if k != "free")
        
        # Validate all keys are valid roles
        for role in distribution.keys():
            if role not in valid_roles:
                return f"Invalid citizen role: {role}"
        
        # Validate all values are non-negative
        for role, count in distribution.items():
            if not isinstance(count, int) or count < 0:
                return f"Citizen count must be non-negative integer: {role}={count}"
        
        # Validate total matches exactly
        new_total = sum(distribution.values())
        if new_total != current_total:
            return f"Total must equal current citizens (expected {current_total}, got {new_total})"
        
        # Apply new distribution (no free citizens)
        empire.citizens = {k: v for k, v in distribution.items()}
        return None
