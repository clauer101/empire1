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
        # speedup_factor: ticks run N× faster AND each tick advances N× as
        # much game time, so one tick still covers step_length_ms of game time.
        self._speedup = max(float(game_config.speedup_factor), 0.01) if game_config else 1.0
        self._step_interval = ((game_config.step_length_ms / 1000.0) if game_config else 1.0) / self._speedup
        self._save_every_n_ticks = max(1, int(self.STATE_SAVE_INTERVAL_S / self._step_interval))

        self._database: Any | None = None
        self._season_snapshot_done: bool = False
        self._wipe_done: bool = False

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
            self._step(dt * self._speedup)
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
    def speedup(self) -> float:
        """Current game-time multiplier (1.0 = real time)."""
        return self._speedup

    def set_speedup(self, factor: float) -> None:
        """Change the game-time multiplier at runtime.

        Not persisted — after a server restart the value from game.yaml
        applies again.
        """
        self._speedup = max(float(factor), 0.01)
        base = (self._gc.step_length_ms / 1000.0) if self._gc else 1.0
        self._step_interval = base / self._speedup
        self._save_every_n_ticks = max(1, int(self.STATE_SAVE_INTERVAL_S / self._step_interval))
        # Write back to the shared GameConfig so other services reading
        # gc.speedup_factor (e.g. BattleService) pick up runtime changes too.
        if self._gc is not None:
            self._gc.speedup_factor = self._speedup
        _log.info("speedup set to %.2fx (tick interval %.3fs)",
                  self._speedup, self._step_interval)

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
        from gameserver.engine.global_state import get_season_number

        results_dir = Path(self._state_file).parent / "results" / f"season{get_season_number()}"
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

            # 2. gameserver.db — use shutil.copy2 to avoid VACUUM conflicts
            if self._database is not None:
                db_src = Path(self._database._db_path)
                if db_src.exists():
                    dest_db = results_dir / "gameserver.db"
                    await asyncio.get_running_loop().run_in_executor(
                        None, shutil.copy2, db_src, dest_db
                    )
                    _log.info("Season snapshot: copied gameserver.db")

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


            # 5. Record top-3 winners in the live DB
            if self._database is not None:
                from gameserver.engine.global_state import get_season_title
                empires = list(self._empires.all_empires.values())
                ranked = sorted(
                    (e for e in empires if e.uid != 0),
                    key=lambda e: e.resources.get("culture", 0.0), reverse=True,
                )
                winners = [
                    {
                        "place": i + 1,
                        "empire_uid": e.uid,
                        "empire_name": e.name,
                        "culture": e.resources.get("culture", 0.0),
                    }
                    for i, e in enumerate(ranked[:3])
                ]
                await self._database.record_season_winners(
                    season_number=get_season_number(),
                    season_title=get_season_title(),
                    winners=winners,
                )

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
        from datetime import datetime, timezone, timedelta
        from gameserver.engine.global_state import (
            get_end_criterion_activated, is_end_rally_active,
            get_next_season_leadtime, get_next_season_start,
            get_next_season_title, get_season_number, get_season_title,
            is_season_reset_triggered, set_season_reset_triggered, set_season,
            clear_end_criterion, parse_iso_utc, set_this_season_start_date,
            is_season_snapshot_done, set_season_snapshot_done,
        )
        now = datetime.now(timezone.utc)
        season_start = parse_iso_utc(get_next_season_start())

        # Phase 1 → 2: Rally ended — freeze game and take snapshot once.
        if get_end_criterion_activated() is not None and self._gc is not None and not is_end_rally_active(self._gc):
            if not is_season_snapshot_done():
                set_season_snapshot_done(True)
                set_season_reset_triggered(True)
                # Auto-set next_season_start if not already configured.
                if not get_next_season_start() and self._gc is not None:
                    activated = get_end_criterion_activated()
                    if isinstance(activated, datetime):
                        next_start = (activated + timedelta(seconds=float(self._gc.next_season_start_after_end))).isoformat()
                        set_season(get_season_number(), get_season_title(), _next_start=next_start)
                        _log.info(
                            "Auto-set next_season_start: %s (activated + %.0fs)",
                            next_start, self._gc.next_season_start_after_end,
                        )
                try:
                    loop = asyncio.get_running_loop()
                    loop.create_task(self._take_season_snapshot())
                except RuntimeError:
                    pass  # no running event loop in tests

        # Phase 2 → 3: Wipe when leadtime is reached (next_season_start minus
        # season_leadtime). Fires once regardless of whether game_frozen is
        # already True (set by rally end above). Gated on _season_snapshot_done
        # so snapshot runs first, and on wipe not having happened yet.
        if season_start is not None and self._gc is not None and not self._wipe_done:
            leadtime = get_next_season_leadtime(self._gc.season_leadtime)
            reset_at = parse_iso_utc(leadtime)
            if reset_at is not None and now >= reset_at:
                self._wipe_done = True
                import time as _time
                from gameserver.engine.global_state import set_season_wipe_time
                set_season_wipe_time(_time.time())
                uids = self._empires.wipe_all_empires()
                attack_count = self._attacks.wipe_all_attacks()
                clear_end_criterion()
                if self._database is not None:
                    asyncio.ensure_future(self._database.wipe_season_stats())
                _log.info(
                    "Season wipe: wiped %d empires, %d attacks; "
                    "frozen until %s",
                    len(uids), attack_count, get_next_season_start(),
                )
                return  # empires wiped — skip step_all this tick

        # Phase 2/3: While frozen, stay frozen until next_season_start is
        # reached, then advance the season and unfreeze (Phase 4).
        if is_season_reset_triggered():
            if season_start is None:
                if get_next_season_start():
                    _log.warning(
                        "game_frozen but next_season_start is malformed: %r",
                        get_next_season_start(),
                    )
                return  # frozen — waiting for admin to set next_season_start
            if now >= season_start:
                new_title = get_next_season_title() or get_season_title()
                set_season(get_season_number() + 1, new_title)
                set_this_season_start_date(season_start.isoformat())
                set_season_reset_triggered(False)
                set_season_snapshot_done(False)
                self._wipe_done = False
                _log.info(
                    "New season started: season %d '%s'",
                    get_season_number(), get_season_title(),
                )
            else:
                return  # frozen — next_season_start not yet reached

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

        # 4. Update statistics: peak simultaneous incoming attacks per defender.
        # Counts distinct in-flight attackers (AI counts as at most one).
        if self._database is not None:
            from gameserver.engine.ai_service import AI_UID
            from gameserver.models.attack import AttackPhase
            incoming: dict[int, set[int]] = {}
            for atk in self._attacks.get_all_attacks():
                if atk.phase == AttackPhase.FINISHED:
                    continue
                attacker = AI_UID if atk.attacker_uid == AI_UID else atk.attacker_uid
                incoming.setdefault(atk.defender_uid, set()).add(attacker)
            for def_uid, attackers in incoming.items():
                asyncio.ensure_future(
                    self._database.record_empire_stat_max(
                        def_uid, "peak_incoming", len(attackers)
                    )
                )

        # 5. Barbarian periodic attacks (Bernoulli trial every 60 s per player)
        if self._ai is not None:
            self._ai.tick_barbarians(dt, self._empires, self._attacks)

        # 6. Scripted AI attacks are triggered via ItemCompleted events, not polled.
