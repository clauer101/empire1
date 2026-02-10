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
from gameserver.loaders.ai_loader import load_ai_templates
from gameserver.loaders.item_loader import load_items
from gameserver.loaders.map_loader import load_map
from gameserver.models.items import ItemDetails
from gameserver.models.map import HexMap
from gameserver.network.auth import AuthService
from gameserver.network.router import Router
from gameserver.network.server import Server
from gameserver.persistence.database import Database
from gameserver.persistence.state_load import RestoredState, load_state
from gameserver.persistence.state_save import save_state
from gameserver.util.events import EventBus
from gameserver.models.empire import Empire
from gameserver.debug.dashboard import DebugDashboard
from gameserver.network.handlers import register_all_handlers
from gameserver.loaders.game_config_loader import GameConfig, load_game_config

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Default paths — relative to the working directory
# ---------------------------------------------------------------------------
DEFAULT_ITEMS_PATH = "config"
DEFAULT_MAP_PATH = "config/maps/default.yaml"
DEFAULT_AI_PATH = "config/ai_templates.yaml"
DEFAULT_DB_PATH = "gameserver.db"
DEFAULT_DEBUG_PORT = 9000

# ---------------------------------------------------------------------------
# Container for all loaded configuration
# ---------------------------------------------------------------------------


@dataclass
class Configuration:
    """Holds all data loaded from config files."""

    items: list = field(default_factory=list)
    hex_map: Optional[HexMap] = None
    ai_templates: dict = field(default_factory=dict)
    game: GameConfig = field(default_factory=GameConfig)


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
    debug_dashboard: Optional[DebugDashboard] = None


# ===================================================================
# 1. Load configuration
# ===================================================================


def load_configuration(
    config_dir: str = "config",
    items_path: str = "",
    map_path: str = "",
    ai_path: str = "",
) -> Configuration:
    """Load items, hex map, and AI templates from YAML files.

    All loaders are synchronous (pure file I/O + parsing).

    Args:
        config_dir: Base configuration directory (default: "config").
        items_path: Path to the items YAML (default: config_dir).
        map_path: Path to the hex-map YAML (default: config_dir/maps/default.yaml).
        ai_path: Path to the AI templates YAML (default: config_dir/ai_templates.yaml).

    Returns:
        Populated :class:`Configuration` containing items, map, and AI data.
    """
    log.info("Loading configuration …")

    # Use provided paths or defaults based on config_dir
    if not items_path:
        items_path = config_dir
    if not map_path:
        map_path = os.path.join(config_dir, "maps/default.yaml")
    if not ai_path:
        ai_path = os.path.join(config_dir, "ai_templates.yaml")

    items = load_items(items_path)
    log.info("  items:        %d loaded from %s", len(items), items_path)

    hex_map = load_map(map_path)
    path_count = sum(1 for p in hex_map.paths.values() if p)
    tile_count = len(hex_map.build_tiles)
    log.info("  map:          %d paths, %d build tiles from %s", path_count, tile_count, map_path)

    ai_templates = load_ai_templates(ai_path)
    log.info("  ai_templates: %d entries from %s", len(ai_templates), ai_path)

    game_cfg = load_game_config()
    log.info("  game_config:  loaded")

    return Configuration(items=items, hex_map=hex_map, ai_templates=ai_templates, game=game_cfg)


# ===================================================================
# 2. Initialize persistence layer
# ===================================================================


async def init_persistence(db_path: str = DEFAULT_DB_PATH, state_file: str = "state.yaml") -> tuple:
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


def create_services(config: Configuration, database: Database) -> Services:
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

    empire_service = EmpireService(upgrade_provider, event_bus, gc)
    battle_service = BattleService()
    attack_service = AttackService(event_bus, gc)
    army_service = ArmyService(upgrade_provider, event_bus)
    ai_service = AIService(upgrade_provider, config.ai_templates)
    statistics = StatisticsService()

    game_loop = GameLoop(event_bus, empire_service, attack_service, statistics, gc)

    auth_service = AuthService(database, gc)
    router = Router()
    server = Server(router, port=gc.ws_port)

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

    # Debug dashboard (references services, so created last)
    svc.debug_dashboard = DebugDashboard(svc, port=gc.debug_port)

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
    bus = services.event_bus

    # Battle outcomes → empire
    bus.on("BattleFinished", lambda evt: services.empire_service.on_battle_finished(evt)
           if hasattr(services.empire_service, "on_battle_finished") else None)

    # Attack arrival → battle
    bus.on("AttackArrived", lambda evt: services.battle_service.on_attack_arrived(evt)
           if hasattr(services.battle_service, "on_attack_arrived") else None)

    # Item completed → statistics
    bus.on("ItemCompleted", lambda evt: services.statistics.on_item_completed(evt)
           if hasattr(services.statistics, "on_item_completed") else None)

    log.info("  event handlers registered")


# ===================================================================
# 5. Start network server
# ===================================================================


async def start_network(services: Services) -> None:
    """Start the WebSocket server so clients can connect.

    Message handlers are registered on the router before the server
    begins accepting connections.

    Args:
        services: All instantiated services.
    """
    log.info("Starting network server …")

    # Register all message handlers on the router
    register_all_handlers(services)

    await services.server.start()
    log.info("  WebSocket server listening on %s:%d", services.server._host, services.server._port)

    # Start debug dashboard
    if services.debug_dashboard is not None:
        await services.debug_dashboard.start()


# ===================================================================
# 6. Start game loop
# ===================================================================


async def start_game_loop(services: Services) -> None:
    """Start the main 1-second game loop.

    This is the last startup step — it runs until a shutdown signal is
    received.  The loop is launched as an asyncio task so the caller
    can set up signal handlers first.

    Args:
        services: All instantiated services.
    """
    log.info("Starting game loop …")
    loop = asyncio.get_running_loop()

    # Graceful shutdown on SIGINT / SIGTERM
    def _request_shutdown() -> None:
        log.info("Shutdown signal received — stopping …")
        services.game_loop.stop()

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, _request_shutdown)

    log.info("  game loop running (1 s tick)")
    await services.game_loop.run()

    # --- Cleanup after loop exits ---
    log.info("Shutting down …")

    # Persist complete game state to YAML
    if services.empire_service is not None:
        try:
            await save_state(
                empires=services.empire_service.all_empires,
                attacks=services.attack_service.get_all_attacks(),
                battles=[],
            )
        except Exception:
            log.exception("State save failed — continuing shutdown")

    if services.server is not None:
        await services.server.stop()
        log.info("  WebSocket server stopped")
    if services.debug_dashboard is not None:
        await services.debug_dashboard.stop()
        log.info("  debug dashboard stopped")
    if services.database is not None:
        await services.database.close()
        log.info("  database closed")
    log.info("  goodbye")


# ===================================================================
# Entry points
# ===================================================================


async def _start(config_dir: str = "config", state_file: str = "state.yaml") -> None:
    """Initialize and run all server components.
    
    Args:
        config_dir: Base configuration directory path.
        state_file: Path to the state YAML file for restoration.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )
    log.info("=== Game Server starting ===")

    # 1. Load configuration
    config = load_configuration(config_dir=config_dir)

    # 2. Initialize persistence
    database, saved_state = await init_persistence(state_file=state_file)

    # 3. Create services
    services = create_services(config, database)

    # 4. Wire event handlers
    wire_events(services)

    # 5. Restore empires from saved state, or register a test empire
    if saved_state is not None and saved_state.empires:
        for empire in saved_state.empires.values():
            services.empire_service.register(empire)
            services.empire_service.recalculate_effects(empire)
        log.info("Restored %d empires from saved state", len(saved_state.empires))
        # Restore attacks
        for attack in saved_state.attacks:
            services.attack_service._attacks.append(attack)
        if saved_state.attacks:
            log.info("Restored %d attacks from saved state", len(saved_state.attacks))
    else:
        _add_test_empire(services)

    # 6. Start network
    await start_network(services)

    # 7. Start game loop (blocks until shutdown)
    await start_game_loop(services)


def _add_test_empire(services: Services) -> None:
    """Register a test empire so the game loop has something to tick.

    Remove this once real player login is implemented.
    """
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
    config_dir = "config"  # Default config directory
    state_file = "state.yaml"  # Default state file
    
    # Parse command-line arguments
    if "--state_file" in sys.argv:
        try:
            idx = sys.argv.index("--state_file")
            if idx + 1 < len(sys.argv):
                state_file = sys.argv[idx + 1]
        except (ValueError, IndexError):
            print("Error: --state_file requires an argument", file=sys.stderr)
            sys.exit(1)
    
    asyncio.run(_start(config_dir=config_dir, state_file=state_file))


if __name__ == "__main__":
    main()
