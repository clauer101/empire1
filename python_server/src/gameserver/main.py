"""Game server entry point.

Initializes all components and starts the asyncio event loop:
1. Load configuration (items, maps, AI templates)
2. Initialize persistence layer (database, state restore)
3. Create engine services (upgrade_provider, empire, battle, attack, army, ai, statistics)
4. Create event bus and wire up services
5. Start network server (WebSocket)
6. Start game loop (1s tick)

Usage:
    python -m gameserver.main
    # or via entry point:
    gameserver
"""

from __future__ import annotations

import asyncio
import logging
import logging.handlers
import structlog
import signal
import sys
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from gameserver.engine.ai_service import AIService
from gameserver.engine.army_service import ArmyService
from gameserver.engine.attack_service import AttackService
from gameserver.engine.battle_service import BattleService
from gameserver.engine.empire_service import EmpireService
from gameserver.engine.game_loop import GameLoop
from gameserver.engine.statistics import StatisticsService
from gameserver.engine.upgrade_provider import UpgradeProvider
from gameserver.loaders.ai_loader import load_ai_waves
from gameserver.loaders.item_loader import load_items
from gameserver.loaders.map_loader import load_map
from gameserver.models.map import HexMap
from gameserver.network.auth import AuthService
from gameserver.network.router import Router
from gameserver.network.server import Server
from gameserver.persistence.database import Database
from gameserver.persistence.state_load import load_state
from gameserver.persistence.state_save import save_state
from gameserver.util.events import EventBus, BattleFinished, AttackArrived, ItemCompleted
from gameserver.models.empire import Empire
from gameserver.network.handlers import register_all_handlers
from gameserver.network.handlers._core import _active_battles
from gameserver.loaders.game_config_loader import GameConfig, load_game_config

log = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# Default paths — relative to the working directory
# ---------------------------------------------------------------------------
DEFAULT_ITEMS_PATH = "config"
DEFAULT_MAP_PATH = "config/maps/default.yaml"
DEFAULT_DB_PATH = "gameserver.db"
DEFAULT_MESSAGES_PATH = "messages.yaml"
# ---------------------------------------------------------------------------
# Container for all loaded configuration
# ---------------------------------------------------------------------------


@dataclass
class Configuration:
    """Holds all data loaded from config files."""

    items: list[Any] = field(default_factory=list)
    hex_map: Optional[HexMap] = None
    ai_waves: list[Any] = field(default_factory=list)
    game: GameConfig = field(default_factory=GameConfig)
    knowledge_era_groups: dict[str, list[str]] = field(default_factory=dict)
    building_era_groups: dict[str, list[str]] = field(default_factory=dict)
    item_era_index: dict[str, int] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Container for all services (makes passing around easier)
# ---------------------------------------------------------------------------


@dataclass
class Services:
    """Holds references to all engine services."""

    game_config: Optional[GameConfig] = None
    event_bus: Optional[EventBus] = None
    upgrade_provider: Optional[UpgradeProvider] = None
    empire_service: Optional[EmpireService] = None
    battle_service: Optional[BattleService] = None
    attack_service: Optional[AttackService] = None
    army_service: Optional[ArmyService] = None
    ai_service: Optional[AIService] = None
    statistics: Optional[StatisticsService] = None
    game_loop: Optional[GameLoop] = None
    auth_service: Optional[AuthService] = None
    router: Optional[Router] = None
    server: Optional[Server] = None
    database: Optional[Database] = None
    # Set during start_network — present after startup
    _rest_server: Optional[object] = None
    _rest_task: Optional[asyncio.Task[None]] = None
    _cleanup_task: Optional[asyncio.Task[None]] = None
    _backup_task: Optional[asyncio.Task[None]] = None


# ===================================================================
# 1. Load configuration
# ===================================================================


def _load_era_groups_from_yaml(yaml_path: Path) -> dict[str, list[str]]:
    """Build era → [iid] mapping from explicit era: fields in a YAML file."""
    import yaml as _yaml
    result: dict[str, list[str]] = {}
    try:
        data = _yaml.safe_load(yaml_path.read_text(encoding="utf-8")) or {}
    except OSError:
        log.warning("Could not read %s for era groups", yaml_path)
        return result
    for iid, item in data.items():
        if not isinstance(item, dict):
            continue
        era = item.get("era", "")
        if era:
            result.setdefault(era, []).append(iid)
    return result


def load_configuration(
    config_dir: str = "config",
    items_path: str = "",
    map_path: str = "",
) -> Configuration:
    """Load items, hex map, and AI waves from YAML files.

    All loaders are synchronous (pure file I/O + parsing).

    Args:
        config_dir: Base configuration directory (default: "config").
        items_path: Path to the items YAML (default: config_dir).
        map_path: Path to the hex-map YAML (default: config_dir/maps/default.yaml).

    Returns:
        Populated :class:`Configuration` containing items, map, and AI data.
    """
    log.info("Loading configuration …")

    # Use provided paths or defaults based on config_dir
    if not items_path:
        items_path = config_dir
    if not map_path:
        map_path = os.path.join(config_dir, "maps/default.yaml")

    items = load_items(items_path)
    log.info("  items:        %d loaded from %s", len(items), items_path)

    hex_map = load_map(map_path)
    path_count = len(hex_map.critter_path) if hex_map.critter_path else 0
    tile_count = len(hex_map.build_tiles)
    log.info("  map:          %d path tiles, %d build tiles from %s", path_count, tile_count, map_path)

    ai_waves_path = os.path.join(config_dir, "ai_waves.yaml")
    ai_waves = load_ai_waves(ai_waves_path)
    log.info("  ai_waves:     %d hardcoded entries from %s", len(ai_waves), ai_waves_path)

    game_cfg = load_game_config(os.path.join(config_dir, "game.yaml"))
    log.info("  game_config:  loaded")

    knowledge_era_groups = _load_era_groups_from_yaml(Path(config_dir) / "knowledge.yaml")
    log.info("  knowledge_era_groups: %d eras", len(knowledge_era_groups))

    building_era_groups = _load_era_groups_from_yaml(Path(config_dir) / "buildings.yaml")
    log.info("  building_era_groups: %d eras", len(building_era_groups))

    from gameserver.util.eras import ERA_ORDER as _ERA_ORDER_LIST
    item_era_index: dict[str, int] = {}
    for _cat_yaml in ("structures.yaml", "critters.yaml"):
        for _era, _iids in _load_era_groups_from_yaml(Path(config_dir) / _cat_yaml).items():
            _idx = _ERA_ORDER_LIST.index(_era) if _era in _ERA_ORDER_LIST else 0
            for _iid in _iids:
                item_era_index[_iid] = _idx
    log.info("  item_era_index: %d items indexed", len(item_era_index))

    return Configuration(items=items, hex_map=hex_map,
                         ai_waves=ai_waves, game=game_cfg,
                         knowledge_era_groups=knowledge_era_groups,
                         building_era_groups=building_era_groups,
                         item_era_index=item_era_index)


# ===================================================================
# 2. Initialize persistence layer
# ===================================================================


async def init_persistence(db_path: str = DEFAULT_DB_PATH, state_file: str = "state.yaml") -> tuple[Any, ...]:
    """Open the database and try to restore previous game state.

    Args:
        db_path: Path to the SQLite file.
        state_file: Path to the state YAML file (default: state.yaml).

    Returns:
        Tuple of (Database, restored_state_or_None).
    """
    log.info("Initializing persistence …")

    database = Database(db_path)
    await database.connect()
    log.info("  database:     connected (%s)", db_path)

    restored = await load_state(path=state_file)
    if restored is not None:
        log.info("  state:        restored from disk (%d empires, %d attacks)",
                 len(restored.empires), len(restored.attacks))
    else:
        log.info("  state:        no previous state found — fresh start")

    return database, restored


# ===================================================================
# 3. Create engine services
# ===================================================================


def create_services(config: Configuration, database: Database, state_file: str = "state.yaml") -> Services:
    """Instantiate all engine/network services with proper dependency injection.

    Wiring order matters: services that are injected into others are created first.

    Args:
        config: Loaded configuration (items, map, ai templates).
        database: Connected database instance.

    Returns:
        Populated :class:`Services` container.
    """
    log.info("Creating services …")

    gc = config.game
    event_bus = EventBus()
    upgrade_provider = UpgradeProvider()
    upgrade_provider.load(config.items)
    log.info("  upgrade_provider: %d items registered", len(config.items))

    empire_service = EmpireService(upgrade_provider, event_bus, gc,
                                   knowledge_era_groups=config.knowledge_era_groups,
                                   building_era_groups=config.building_era_groups,
                                   item_era_index=config.item_era_index)
    battle_service = BattleService(items=upgrade_provider.items, gc=gc)
    attack_service = AttackService(event_bus, gc, empire_service,
                                   knowledge_era_groups=config.knowledge_era_groups)
    army_service = ArmyService(upgrade_provider, event_bus)
    ai_service = AIService(upgrade_provider,
                           game_config=gc, hardcoded_waves=config.ai_waves)
    statistics = StatisticsService()

    game_loop = GameLoop(event_bus, empire_service, attack_service, statistics, gc, ai_service=ai_service, state_file=state_file)

    auth_service = AuthService(database, gc)
    router = Router()
    server = Server(router, port=gc.ws_port)

    # Clean up old replay files
    from gameserver.persistence.replay import cleanup_old_replays
    cleanup_old_replays()

    log.info("  all services created")

    svc = Services(
        game_config=gc,
        event_bus=event_bus,
        upgrade_provider=upgrade_provider,
        empire_service=empire_service,
        battle_service=battle_service,
        attack_service=attack_service,
        army_service=army_service,
        ai_service=ai_service,
        statistics=statistics,
        game_loop=game_loop,
        auth_service=auth_service,
        router=router,
        server=server,
        database=database,
    )

    return svc


# ===================================================================
# 4. Wire up event handlers
# ===================================================================


def wire_events(services: Services) -> None:
    """Register event handlers to connect services via the EventBus.

    This is where cross-cutting concerns are wired — for example, when
    a battle finishes the empire service gets notified to apply loot.

    Args:
        services: All instantiated services.
    """
    log.info("Wiring event handlers …")
    assert services.event_bus is not None
    assert services.empire_service is not None
    assert services.battle_service is not None
    assert services.statistics is not None
    bus = services.event_bus
    _empire_svc = services.empire_service
    _battle_svc = services.battle_service
    _statistics = services.statistics

    # Battle outcomes → empire
    bus.on(BattleFinished, lambda evt: _empire_svc.on_battle_finished(evt)
           if hasattr(_empire_svc, "on_battle_finished") else None)

    # Attack arrival → battle
    bus.on(AttackArrived, lambda evt: _battle_svc.on_attack_arrived(evt)
           if hasattr(_battle_svc, "on_attack_arrived") else None)

    # Item completed → statistics
    bus.on(ItemCompleted, lambda evt: _statistics.on_item_completed(evt)
           if hasattr(_statistics, "on_item_completed") else None)

    # Item completed → AI scripted wave triggers
    if services.ai_service is not None:
        _ai = services.ai_service
        assert services.attack_service is not None
        _atk = services.attack_service
        bus.on(ItemCompleted, lambda evt: _ai.on_item_completed(
            evt.empire_uid, evt.iid, _empire_svc, _atk
        ))

    log.info("  event handlers registered")


# ===================================================================
# 5. Start network server
# ===================================================================


async def start_network(services: Services, state_file: str = "state.yaml") -> None:
    """Start the WebSocket server and REST API so clients can connect.

    Message handlers are registered on the router before the server
    begins accepting connections.  The FastAPI REST app is started on
    a separate port via uvicorn.

    Args:
        services: All instantiated services.
    """
    log.info("Starting network servers …")
    assert services.server is not None
    assert services.game_config is not None

    # Register all message handlers on the router
    register_all_handlers(services)

    await services.server.start()
    log.info("  WebSocket server listening on %s:%d", services.server._host, services.server._port)

    # Start REST API (FastAPI + uvicorn)
    from gameserver.network.rest_api import create_app
    import uvicorn

    rest_app = create_app(services)
    rest_port = services.game_config.rest_port
    config = uvicorn.Config(
        rest_app,
        host="0.0.0.0",
        port=rest_port,
        log_level="warning",
        access_log=False,
    )
    rest_server = uvicorn.Server(config)
    # Store reference for shutdown
    services._rest_server = rest_server
    # Start as background task (non-blocking); keep task ref for clean await on shutdown
    services._rest_task = asyncio.create_task(rest_server.serve())
    log.info("  REST API listening on http://0.0.0.0:%d", rest_port)

    async def _message_cleanup_loop() -> None:
        while True:
            await asyncio.sleep(24 * 3600)  # run once per day
            if services.database is not None:
                await services.database.delete_old_messages(max_age_days=7)

    services._cleanup_task = asyncio.create_task(_message_cleanup_loop())

    async def _backup_loop(_state_file: str = state_file) -> None:
        """Rolling backups: 24 hourly slots + 7 daily slots for state.yaml and gameserver.db."""
        import shutil
        from datetime import datetime, timezone

        data_dir = Path(_state_file).parent
        hourly_dir = data_dir / "states" / "hourly"
        daily_dir  = data_dir / "states" / "daily"
        hourly_dir.mkdir(parents=True, exist_ok=True)
        daily_dir.mkdir(parents=True, exist_ok=True)

        db_path = str(services.database._db_path) if services.database else None

        last_daily_day: int | None = None
        hour_slot: int = 0

        while True:
            await asyncio.sleep(3600)
            if services.empire_service is None:
                continue
            try:
                await save_state(
                    empires=services.empire_service.all_empires,
                    attacks=services.attack_service.get_all_attacks() if services.attack_service else [],
                    battles=[],
                    path=_state_file,
                )
                now = datetime.now(timezone.utc)

                # Hourly rolling backup (slots 00–23)
                slot = f"{hour_slot:02d}"
                shutil.copy2(_state_file, hourly_dir / f"state_{slot}.yaml")
                if db_path and Path(db_path).exists():
                    services.database._conn and await services.database._conn.execute(  # type: ignore[union-attr]
                        f"VACUUM INTO '{hourly_dir / f'gameserver_{slot}.db'}'"
                    )
                log.info("Hourly backup written: slot %s", slot)
                hour_slot = (hour_slot + 1) % 24

                # Daily rolling backup (slots 0–6, one per weekday)
                today = now.weekday()
                if today != last_daily_day:
                    day = f"day{today}"
                    shutil.copy2(_state_file, daily_dir / f"state_{day}.yaml")
                    if db_path and Path(db_path).exists():
                        services.database._conn and await services.database._conn.execute(  # type: ignore[union-attr]
                            f"VACUUM INTO '{daily_dir / f'gameserver_{day}.db'}'"
                        )
                    log.info("Daily backup written: slot %s", day)
                    last_daily_day = today

            except Exception:
                # Backup errors must never crash the game server — log and retry next hour
                log.exception("Backup loop error — continuing")

    services._backup_task = asyncio.create_task(_backup_loop())



# ===================================================================
# 6. Start game loop
# ===================================================================


async def start_game_loop(services: Services, state_file: str = "state.yaml") -> None:
    """Start the main 1-second game loop.

    This is the last startup step — it runs until a shutdown signal is
    received.  The loop is launched as an asyncio task so the caller
    can set up signal handlers first.

    Args:
        services: All instantiated services.
    """
    log.info("Starting game loop …")
    assert services.game_loop is not None
    _game_loop = services.game_loop
    loop = asyncio.get_running_loop()

    # Graceful shutdown on SIGINT / SIGTERM
    def _request_shutdown() -> None:
        log.info("Shutdown signal received — stopping …")
        if _active_battles:
            uids = ", ".join(str(uid) for uid in _active_battles)
            log.warning("Shutdown mid-battle! %d active battle(s) will be interrupted (defender UIDs: %s)", len(_active_battles), uids)
        _game_loop.stop()

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, _request_shutdown)

    log.info("  game loop running (1 s tick)")
    await _game_loop.run()

    # --- Cleanup after loop exits ---
    log.info("Shutting down …")

    # Persist complete game state to YAML
    if services.empire_service is not None and services.attack_service is not None:
        try:
            await save_state(
                empires=services.empire_service.all_empires,
                attacks=services.attack_service.get_all_attacks(),
                battles=[],
                path=state_file,
            )
            log.info("Game state saved")
        except Exception:
            # Save failure must not block shutdown — servers still need to stop cleanly
            log.exception("State save failed — continuing shutdown")

    if services.server is not None:
        await services.server.stop()
        log.info("  WebSocket server stopped")
    rest_server = getattr(services, "_rest_server", None)
    rest_task = getattr(services, "_rest_task", None)
    if rest_server is not None:
        rest_server.should_exit = True
        if rest_task is not None:
            try:
                await asyncio.wait_for(rest_task, timeout=5.0)
            except (asyncio.CancelledError, asyncio.TimeoutError):
                pass
        log.info("  REST API server stopped")
    cleanup_task = getattr(services, "_cleanup_task", None)
    if cleanup_task is not None:
        cleanup_task.cancel()
    if services.database is not None:
        await services.database.close()
        log.info("  database closed")
    log.info("  goodbye")


# ===================================================================
# Entry points
# ===================================================================


async def _start(config_dir: str = "config", state_file: str = "state.yaml", db_file: str = DEFAULT_DB_PATH) -> None:
    """Initialize and run all server components.
    
    Args:
        config_dir: Base configuration directory path.
        state_file: Path to the state YAML file for restoration.
    """
    from gameserver.util.logging import configure_logging
    configure_logging(log_file="gameserver.log", level=logging.INFO)
    logging.getLogger("gameserver.network.handlers").setLevel(logging.INFO)
    logging.getLogger("gameserver.engine.battle_service").setLevel(logging.INFO)
    log.info("=== Game Server starting ===")

    # Point replay storage at the persisted data directory so replays survive redeploys
    import gameserver.persistence.replay as _replay_mod
    _replay_mod.DEFAULT_REPLAY_DIR = str(Path(state_file).parent / "replays")

    # 1. Load configuration
    config = load_configuration(config_dir=config_dir)

    # 2. Initialize persistence
    database, saved_state = await init_persistence(db_path=db_file, state_file=state_file)

    # 3. Create services
    services = create_services(config, database, state_file=state_file)

    # Migrate messages from old YAML file to DB (one-time, no-op if already done)
    await database.migrate_messages_from_yaml(DEFAULT_MESSAGES_PATH)

    # 4. Wire event handlers
    wire_events(services)

    # 5. Restore empires from saved state, or register a test empire
    assert services.empire_service is not None
    assert services.attack_service is not None
    if saved_state is not None and saved_state.empires:
        for empire in saved_state.empires.values():
            services.empire_service.register(empire)
            services.empire_service.recalculate_effects(empire)
        log.info("Restored %d empires from saved state", len(saved_state.empires))
        services.empire_service.sync_aid_counter()
        # Restore attacks (also advances the ID counter)
        if saved_state.attacks:
            services.attack_service.restore_attacks(saved_state.attacks)
        # Remove AI armies that have no active attack in the restored state
        if services.ai_service is not None:
            services.ai_service.cleanup_inactive_armies(
                services.empire_service, services.attack_service
            )
    else:
        _add_test_empire(services)

    # Pre-register AI empire so it's visible from the start
    from gameserver.engine.ai_service import AI_UID
    if services.empire_service.get(AI_UID) is None:
        ai_empire = Empire(uid=AI_UID, name="AI")
        services.empire_service.register(ai_empire)
        log.info("AI empire pre-registered (uid=%d)", AI_UID)

    # 6. Start network
    await start_network(services, state_file=state_file)

    # 7. Start game loop (blocks until shutdown)
    await start_game_loop(services, state_file=state_file)


def _add_test_empire(services: Services) -> None:
    """Register a test empire so the game loop has something to tick.

    Remove this once real player login is implemented.
    """
    assert services.empire_service is not None
    test_empire = Empire(
        uid=100,
        name="TestImperium",
        resources={"gold": 50.0, "culture": 10.0, "life": 10.0},
        citizens={"merchant": 2, "scientist": 1, "artist": 1},
        buildings={"farm": 30.0, "library": 60.0},  # 30s / 60s build time
        knowledge={"archery": 45.0},  # 45s research
    )
    services.empire_service.register(test_empire)
    log.info("Test empire registered: uid=%d name=%r", test_empire.uid, test_empire.name)


def main() -> None:
    """Entry point for the game server.
    
    Supports command-line arguments:
        --state_file <path>  Use custom state file for restoration (default: state.yaml)
    """
    config_dir = "config"
    state_file = "state.yaml"
    db_file = DEFAULT_DB_PATH

    def _get_arg(flag: str) -> str | None:
        if flag in sys.argv:
            idx = sys.argv.index(flag)
            if idx + 1 < len(sys.argv):
                return sys.argv[idx + 1]
            print(f"Error: {flag} requires an argument", file=sys.stderr)
            sys.exit(1)
        return None

    state_file = _get_arg("--state_file") or state_file
    db_file = _get_arg("--db_file") or db_file

    asyncio.run(_start(config_dir=config_dir, state_file=state_file, db_file=db_file))


if __name__ == "__main__":
    main()
