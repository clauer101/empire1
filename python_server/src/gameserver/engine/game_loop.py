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
import logging
import time
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from gameserver.engine.ai_service import AIService
    from gameserver.engine.attack_service import AttackService
    from gameserver.engine.empire_service import EmpireService
    from gameserver.engine.statistics import StatisticsService
    from gameserver.loaders.game_config_loader import GameConfig
    from gameserver.util.events import EventBus

_log = logging.getLogger(__name__)



class GameLoop:
    """The central 1-second game tick loop.

    Args:
        event_bus: Global event bus for inter-service communication.
        empire_service: Service managing empire state.
        attack_service: Service managing attacks.
        statistics: Service for scoring and rankings.
    """

    STATE_SAVE_INTERVAL_S: float = 60.0

    def __init__(
        self,
        event_bus: EventBus,
        empire_service: EmpireService,
        attack_service: AttackService,
        statistics: StatisticsService,
        game_config: GameConfig | None = None,
        ai_service: AIService | None = None,
        state_file: str = "state.yaml",
    ) -> None:
        self._events = event_bus
        self._empires = empire_service
        self._attacks = attack_service
        self._stats = statistics
        self._ai = ai_service
        self._state_file = state_file
        self._running = False
        self._gc = game_config
        self._step_interval = (game_config.step_length_ms / 1000.0) if game_config else 1.0
        self._save_every_n_ticks = max(1, int(self.STATE_SAVE_INTERVAL_S / self._step_interval))

        self._database: Any | None = None
        self._season_snapshot_done: bool = False

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
            if self.tick_count % self._save_every_n_ticks == 0:
                asyncio.ensure_future(self._save_state())
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

    async def _take_season_snapshot(self) -> None:
        """Copy state.yaml + gameserver.db + runtime stats CSV to the season results folder.

        Target: <data_dir>/results/season1/
        Does nothing if the folder already contains files.
        """
        import csv
        import shutil

        results_dir = Path(self._state_file).parent / "results" / "season1"
        try:
            results_dir.mkdir(parents=True, exist_ok=True)
            if (results_dir / "gameserver.db").exists() and (results_dir / "state.yaml").exists():
                _log.info("Season snapshot: gameserver.db + state.yaml already present — skipping")
                return

            # 1. state.yaml
            state_src = Path(self._state_file)
            if state_src.exists():
                shutil.copy2(state_src, results_dir / "state.yaml")
                _log.info("Season snapshot: copied state.yaml")

            # 2. gameserver.db
            if self._database is not None:
                db_src = Path(self._database._db_path)
                if db_src.exists():
                    dest_db = results_dir / "gameserver.db"
                    await self._database._conn.execute(f"VACUUM INTO '{dest_db}'")
                    _log.info("Season snapshot: copied gameserver.db via VACUUM INTO")

            # 3. empire_stats CSV
            if self._database is not None:
                stats_rows = await self._database.get_all_empire_stats()
                _EMPIRE_STATS_COLS = [
                    "uid", "attacks_won_human", "attacks_lost_human", "attacks_won_ai",
                    "attacks_lost_ai", "defense_won_human", "defense_lost_human",
                    "defense_won_ai", "defense_lost_ai", "spies_sent", "towers_sold",
                    "towers_placed", "artifacts_stolen", "longest_battle_ms",
                    "critters_killed", "culture_stolen", "research_stolen",
                    "culture_won", "research_won", "defense_gold_earned", "first_era_reached",
                ]
                fieldnames = list(stats_rows[0].keys()) if stats_rows else _EMPIRE_STATS_COLS
                csv_path = results_dir / "empire_stats.csv"
                with csv_path.open("w", newline="", encoding="utf-8") as f:
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(stats_rows)
                _log.info("Season snapshot: wrote empire_stats.csv (%d rows)", len(stats_rows))

            # 4. artifact_holds CSV
            if self._database is not None:
                holds_rows = await self._database.get_artifact_hold_totals()
                _ARTIFACT_HOLDS_COLS = ["uid", "artifact_iid", "held_secs"]
                fieldnames = list(holds_rows[0].keys()) if holds_rows else _ARTIFACT_HOLDS_COLS
                csv_path = results_dir / "artifact_holds.csv"
                with csv_path.open("w", newline="", encoding="utf-8") as f:
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(holds_rows)
                _log.info("Season snapshot: wrote artifact_holds.csv (%d rows)", len(holds_rows))

            _log.info("Season snapshot complete → %s", results_dir)
        except Exception:
            _log.exception("Season snapshot failed — will not retry")

    async def _save_state(self) -> None:
        """Persist game state to YAML (called periodically from the loop)."""
        from gameserver.persistence.state_save import save_state
        import logging as _log
        try:
            await save_state(
                empires=self._empires.all_empires,
                attacks=self._attacks.get_all_attacks(),
                battles=[],
                path=self._state_file,
            )
        except Exception:
            # State save must never crash the game loop — log and continue ticking
            _log.getLogger(__name__).exception("Periodic state save failed")

    def _step(self, dt: float) -> None:
        """One tick of the game loop."""
        from gameserver.engine.global_state import get_end_criterion_activated, is_end_rally_active
        if get_end_criterion_activated() is not None and self._gc is not None and not is_end_rally_active(self._gc):
            if not self._season_snapshot_done:
                self._season_snapshot_done = True
                try:
                    asyncio.ensure_future(self._take_season_snapshot())
                except RuntimeError:
                    pass  # no running event loop in tests
            return

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

        # 5. Barbarian periodic attacks (Bernoulli trial every 60 s per player)
        if self._ai is not None:
            self._ai.tick_barbarians(dt, self._empires, self._attacks)

        # 6. Scripted AI attacks are triggered via ItemCompleted events, not polled.
