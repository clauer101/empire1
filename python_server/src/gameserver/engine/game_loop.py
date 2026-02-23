"""Main game loop — asyncio-based 1-second tick.

Responsibilities:
- Process queued requests from clients
- Step all empires (resource generation, build progress, research)
- Step all active attacks (travel countdown, siege)
- Trigger AI attacks
- Periodic state save
- Update statistics

The game loop does NOT handle battles — those run as independent
asyncio tasks managed by battle_service.
"""

from __future__ import annotations

import asyncio
import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from gameserver.engine.ai_service import AIService
    from gameserver.engine.attack_service import AttackService
    from gameserver.engine.empire_service import EmpireService
    from gameserver.engine.statistics import StatisticsService
    from gameserver.loaders.game_config_loader import GameConfig
    from gameserver.util.events import EventBus



class GameLoop:
    """The central 1-second game tick loop.

    Args:
        event_bus: Global event bus for inter-service communication.
        empire_service: Service managing empire state.
        attack_service: Service managing attacks.
        statistics: Service for scoring and rankings.
    """

    def __init__(
        self,
        event_bus: EventBus,
        empire_service: EmpireService,
        attack_service: AttackService,
        statistics: StatisticsService,
        game_config: GameConfig | None = None,
        ai_service: AIService | None = None,
    ) -> None:
        self._events = event_bus
        self._empires = empire_service
        self._attacks = attack_service
        self._stats = statistics
        self._ai = ai_service
        self._running = False
        self._step_interval = (game_config.step_length_ms / 1000.0) if game_config else 1.0

        # --- Debug / monitoring counters ---
        self.tick_count: int = 0
        self.started_at: float = 0.0
        self.last_tick_dt: float = 0.0
        self.last_tick_duration_ms: float = 0.0
        self.avg_tick_duration_ms: float = 0.0
        self._tick_duration_sum: float = 0.0

    async def run(self) -> None:
        """Start the game loop. Runs until stop() is called."""
        self._running = True
        self.started_at = time.monotonic()
        last = self.started_at
        while self._running:
            now = time.monotonic()
            dt = now - last
            last = now

            t0 = time.monotonic()
            self._step(dt)
            elapsed_ms = (time.monotonic() - t0) * 1000

            self.tick_count += 1
            self.last_tick_dt = dt
            self.last_tick_duration_ms = elapsed_ms
            self._tick_duration_sum += elapsed_ms
            self.avg_tick_duration_ms = self._tick_duration_sum / self.tick_count

            await asyncio.sleep(self._step_interval)

    @property
    def uptime_seconds(self) -> float:
        """Seconds since the loop started."""
        if self.started_at == 0.0:
            return 0.0
        return time.monotonic() - self.started_at

    @property
    def is_running(self) -> bool:
        return self._running

    def stop(self) -> None:
        """Signal the game loop to stop."""
        self._running = False

    def _step(self, dt: float) -> None:
        """One tick of the game loop."""
        # 1. Advance all empires (resources, build progress, research)
        self._empires.step_all(dt)

        # 2. Advance all active attacks (travel countdown, siege)
        # Returns list of Attack objects for battles that should start
        battles_to_start = self._attacks.step_all(dt)
        
        # 3. Signal battle starts via event bus
        from gameserver.util.events import BattleStartRequested
        for attack in battles_to_start:
            event = BattleStartRequested(
                attack_id=attack.attack_id,
                attacker_uid=attack.attacker_uid,
                defender_uid=attack.defender_uid,
                army_aid=attack.army_aid,
            )
            self._events.emit(event)

        # 4. Update statistics
        # TODO: self._stats.update()

        # 5. Scripted AI attacks are triggered via ItemCompleted events, not polled.
