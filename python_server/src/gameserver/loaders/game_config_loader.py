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
class CitizenPrice:
    """Parameters for citizen upgrade price formula: u + (i*y) * (i+z)^v"""
    u: float = 34.0
    y: float = 1.0
    z: float = 1.5
    v: float = 3.3


@dataclass
class SigmoidPrice:
    """Parameters for sigmoid price formula."""
    maxv: float = 10000.0
    minv: float = 100.0
    spread: float = 10.0
    steep: float = 7.0


@dataclass
class Prices:
    """Purchase price parameters for all buyable items."""
    citizen: CitizenPrice = field(default_factory=CitizenPrice)
    tile: SigmoidPrice = field(default_factory=lambda: SigmoidPrice(maxv=47000, minv=100, spread=29, steep=8.5))
    wave: SigmoidPrice = field(default_factory=lambda: SigmoidPrice(maxv=28000, minv=100, spread=12, steep=7))
    critter_slot: SigmoidPrice = field(default_factory=lambda: SigmoidPrice(maxv=13000, minv=25, spread=23, steep=7))
    army: SigmoidPrice = field(default_factory=lambda: SigmoidPrice(maxv=75000, minv=1000, spread=7, steep=6))


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
    # Era-specific travel offsets (attacker's era determines which one is used).
    # base_travel_offset is the fallback when no era-specific value is set.
    base_travel_offset: float = 300.0
    stone_travel_offset: float = 300.0
    neolithicum_travel_offset: float = 300.0
    bronze_travel_offset: float = 300.0
    iron_travel_offset: float = 300.0
    middle_ages_travel_offset: float = 300.0
    rennaissance_travel_offset: float = 300.0
    industrial_travel_offset: float = 300.0
    modern_travel_offset: float = 300.0
    diamond_travel_offset: float = 300.0
    base_siege_offset: float = 900.0

    # Generic per-era effects dict: { "STEINZEIT": {"gold_offset": 5.0, ...}, ... }
    # Applied to empire.effects when era is determined.
    era_effects: Dict[str, Dict[str, float]] = field(default_factory=dict)

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

    # -- Prices ------------------------------------------------------
    prices: Prices = field(default_factory=Prices)

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
        raise FileNotFoundError(f"Game config not found at {p} — this file is required")

    with p.open() as f:
        raw = yaml.safe_load(f) or {}

    log.info("Loaded game config from %s (%d keys)", p, len(raw))

    # Handle nested spy_costs
    spy_raw = raw.pop("spy_costs", None)
    spy = SpyCosts(**spy_raw) if isinstance(spy_raw, dict) else SpyCosts()

    # Handle nested prices
    prices_raw = raw.pop("prices", None)
    if isinstance(prices_raw, dict):
        citizen_raw = prices_raw.get("citizen", {})
        prices = Prices(
            citizen=CitizenPrice(**citizen_raw) if isinstance(citizen_raw, dict) else CitizenPrice(),
            tile=SigmoidPrice(**prices_raw["tile"]) if "tile" in prices_raw else SigmoidPrice(maxv=47000, minv=100, spread=29, steep=8.5),
            wave=SigmoidPrice(**prices_raw["wave"]) if "wave" in prices_raw else SigmoidPrice(maxv=28000, minv=100, spread=12, steep=7),
            critter_slot=SigmoidPrice(**prices_raw["critter_slot"]) if "critter_slot" in prices_raw else SigmoidPrice(maxv=13000, minv=25, spread=23, steep=7),
            army=SigmoidPrice(**prices_raw["army"]) if "army" in prices_raw else SigmoidPrice(maxv=75000, minv=1000, spread=7, steep=6),
        )
    else:
        prices = Prices()

    # Handle nested era_effects → flatten travel/siege to legacy fields
    # AND build generic era_effects dict for empire effect system
    _ERA_YAML_TO_FIELD = {
        "stone": "stone", "neolithicum": "neolithicum", "bronze": "bronze",
        "iron": "iron", "middle_ages": "middle_ages", "rennaissance": "rennaissance",
        "industrial": "industrial", "modern": "modern", "future": "diamond",
    }
    _ERA_YAML_TO_KEY = {
        "stone": "STEINZEIT", "neolithicum": "NEOLITHIKUM", "bronze": "BRONZEZEIT",
        "iron": "EISENZEIT", "middle_ages": "MITTELALTER", "rennaissance": "RENAISSANCE",
        "industrial": "INDUSTRIALISIERUNG", "modern": "MODERNE", "future": "ZUKUNFT",
    }
    era_raw = raw.pop("era_effects", None)
    era_effects_dict: Dict[str, Dict[str, float]] = {}
    if isinstance(era_raw, dict):
        for yaml_key, vals in era_raw.items():
            if not isinstance(vals, dict):
                continue
            field_prefix = _ERA_YAML_TO_FIELD.get(yaml_key, yaml_key)
            era_key = _ERA_YAML_TO_KEY.get(yaml_key)
            # Legacy flat fields for travel/siege
            if "travel_offset" in vals:
                raw[f"{field_prefix}_travel_offset"] = vals["travel_offset"]
            if "siege_offset" in vals:
                if "base_siege_offset" not in raw:
                    raw["base_siege_offset"] = vals["siege_offset"]
            # Generic era effects (everything except travel/siege)
            if era_key:
                generic = {k: v for k, v in vals.items()
                           if k not in ("travel_offset", "siege_offset")}
                if generic:
                    era_effects_dict[era_key] = generic

    # Build config from flat keys + nested spy_costs + era_effects
    cfg = GameConfig(spy_costs=spy, prices=prices, era_effects=era_effects_dict, **{
        k: v for k, v in raw.items()
        if k in GameConfig.__dataclass_fields__ and k != "era_effects"
    })
    return cfg
