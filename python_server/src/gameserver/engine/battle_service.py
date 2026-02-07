"""Battle service — real-time tower-defense battle simulation.

Runs each battle as an independent asyncio task with ~15ms tick rate.

Tick order (must be preserved):
1. step_shots     — decrement flight time, apply damage on arrival
2. step_critters  — movement + burn tick
3. step_towers    — acquire targets + fire
4. step_armies    — wave timers + critter spawning
5. broadcast      — send delta to observers (throttled to 250ms)

Provides deterministic tick function for testing (explicit dt_ms).
"""

from __future__ import annotations

import asyncio
import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from gameserver.engine.upgrade_provider import UpgradeProvider
    from gameserver.models.battle import BattleState
    from gameserver.models.empire import Empire
    from gameserver.util.events import EventBus


class BattleService:
    """Service that runs and manages tower-defense battles.

    Args:
        event_bus: Event bus for critter/structure lifecycle events.
        upgrade_provider: Item database for spawn-on-death lookups.
    """

    def __init__(self, event_bus: EventBus, upgrade_provider: UpgradeProvider) -> None:
        self._events = event_bus
        self._upgrades = upgrade_provider

    async def run_battle(self, battle: BattleState) -> None:
        """Run a battle to completion as an asyncio task."""
        last = time.monotonic()
        while battle.keep_alive:
            now = time.monotonic()
            dt_ms = (now - last) * 1000
            last = now

            self.tick(battle, dt_ms)

            if battle.should_broadcast():
                await self._broadcast(battle)

            await asyncio.sleep(0.015)

    def tick(self, battle: BattleState, dt_ms: float) -> None:
        """Execute one deterministic battle tick. Used by tests."""
        self._step_shots(battle, dt_ms)
        self._step_critters(battle, dt_ms)
        self._step_towers(battle, dt_ms)
        self._step_armies(battle, dt_ms)
        battle.elapsed_ms += dt_ms
        battle.broadcast_timer_ms -= dt_ms
        self._check_finished(battle)

    # -- Shot resolution -------------------------------------------------

    def _step_shots(self, battle: BattleState, dt_ms: float) -> None:
        """Decrement flight time, apply damage/effects when shots arrive."""
        # TODO: implement
        pass

    # -- Critter movement ------------------------------------------------

    def _step_critters(self, battle: BattleState, dt_ms: float) -> None:
        """Move critters along paths, apply burn damage."""
        # TODO: implement
        pass

    # -- Tower targeting & firing ----------------------------------------

    def _step_towers(self, battle: BattleState, dt_ms: float) -> None:
        """Towers acquire targets and fire shots."""
        # TODO: implement
        pass

    # -- Army wave dispatch ----------------------------------------------

    def _step_armies(self, battle: BattleState, dt_ms: float) -> None:
        """Advance wave timers, spawn critters from waves."""
        # TODO: implement
        pass

    # -- Finish conditions -----------------------------------------------

    def _check_finished(self, battle: BattleState) -> None:
        """Check win/loss conditions."""
        # TODO: implement
        pass

    # -- Broadcasting ----------------------------------------------------

    async def _broadcast(self, battle: BattleState) -> None:
        """Send battle update to all observers."""
        # TODO: implement
        battle.reset_broadcast()

    # -- Loot ------------------------------------------------------------

    def loot_defender(
        self, battle: BattleState, defender: Empire, attackers: dict[int, Empire]
    ) -> None:
        """Apply end-of-battle loot on defender loss."""
        # TODO: implement
        pass
