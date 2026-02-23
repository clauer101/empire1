"""Game configuration — loads tunable constants from config/game.yaml.

Provides a single ``GameConfig`` dataclass that is loaded once at startup
and then passed (or injected) wherever constants are needed.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict

import yaml

log = logging.getLogger(__name__)

DEFAULT_GAME_CONFIG_PATH = "config/game.yaml"


@dataclass
class SpyCosts:
    """Gold costs for spy operations."""
    defense: int = 500
    build_queue: int = 1000
    research_queue: int = 2000
    attacks: int = 5000
    artefacts: int = 10000


@dataclass
class GameConfig:
    """All tunable gameplay constants.

    Loaded from ``config/game.yaml``.  Every field has a sensible default
    so the server can start even without the file.
    """

    # -- Timing ------------------------------------------------------
    step_length_ms: float = 1000.0
    battle_tick_ms: float = 15.0
    broadcast_interval_ms: float = 250.0
    min_keep_alive_ms: float = 10_000.0
    initial_wave_delay_ms: float = 0.0
    splash_flight_ms: float = 500.0

    # -- Economy -----------------------------------------------------
    base_gold_per_sec: float = 1.0
    base_culture_per_sec: float = 0.5
    citizen_effect: float = 0.03
    base_build_speed: float = 1.0
    base_research_speed: float = 1.0

    # -- New empire defaults -----------------------------------------
    starting_resources: Dict[str, float] = field(default_factory=lambda: {
        "gold": 0.0, "culture": 0.0, "life": 10.0,
    })
    starting_max_life: float = 10.0
    restore_life_after_loss_offset: float = 1.0

    # -- Travel & Siege ----------------------------------------------
    base_travel_offset: float = 300.0
    base_siege_offset: float = 900.0

    # -- Army & Waves ------------------------------------------------
    waves_per_level: float = 1.0
    slot_adder_per_ai_level: float = 2.0
    default_spawn_interval_ms: float = 2000.0

    # -- AI attack schedule ------------------------------------------
    ai_travel_seconds: float = 30.0

    # -- Battle strategy / loot --------------------------------------
    min_lose_knowledge: float = 0.03
    max_lose_knowledge: float = 0.15
    min_lose_culture: float = 0.01
    max_lose_culture: float = 0.05
    artefact_steal_chance: float = 0.33

    # -- Spy costs ---------------------------------------------------
    spy_costs: SpyCosts = field(default_factory=SpyCosts)

    # -- Auth validation ---------------------------------------------
    min_username_length: int = 2
    max_username_length: int = 20
    min_password_length: int = 4

    # -- Network -----------------------------------------------------
    ws_port: int = 8765
    rest_port: int = 8080
    ws_ping_interval: int = 30
    ws_ping_timeout: int = 10
    ws_max_message_size: int = 1_048_576
    debug_port: int = 9000

    # -- Server UIDs -------------------------------------------------
    uid_game_server: int = 0
    uid_game_engine: int = 1
    uid_ai: int = 2
    uid_min_player: int = 1000


def load_game_config(path: str = DEFAULT_GAME_CONFIG_PATH) -> GameConfig:
    """Load game configuration from a YAML file.

    Missing keys fall back to dataclass defaults.  If the file does not
    exist, a warning is logged and pure defaults are returned.
    """
    p = Path(path)
    if not p.exists():
        log.warning("Game config not found at %s — using defaults", p)
        return GameConfig()

    with p.open() as f:
        raw = yaml.safe_load(f) or {}

    log.info("Loaded game config from %s (%d keys)", p, len(raw))

    # Handle nested spy_costs
    spy_raw = raw.pop("spy_costs", None)
    spy = SpyCosts(**spy_raw) if isinstance(spy_raw, dict) else SpyCosts()

    # Build config from flat keys + nested spy_costs
    cfg = GameConfig(spy_costs=spy, **{
        k: v for k, v in raw.items()
        if k in GameConfig.__dataclass_fields__
    })
    return cfg
