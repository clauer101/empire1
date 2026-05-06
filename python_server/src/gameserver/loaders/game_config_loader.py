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
class PriceParams:
    """Parameters for price formula: u + (i*y) * (i+z)^v"""
    u: float = 34.0
    y: float = 1.0
    z: float = 1.5
    v: float = 3.3


CitizenPrice = PriceParams  # backwards compat alias


@dataclass
class SigmoidPrice:
    """Parameters for sigmoid price formula."""
    maxv: float = 10000.0
    minv: float = 100.0
    spread: float = 10.0
    steep: float = 7.0


@dataclass
class StructureUpgradeDef:
    """Per-level percentage bonus for each upgradeable tower stat."""
    damage: float = 5.0          # % per level
    range: float = 5.0           # % per level
    reload: float = 5.0          # % per level
    effect_duration: float = 5.0  # % per level
    effect_value: float = 5.0    # % per level


@dataclass
class CritterUpgradeDef:
    """Per-level percentage bonus for each upgradeable critter stat."""
    health: float = 5.0   # % per level
    speed: float = 5.0    # % per level
    armour: float = 5.0   # % per level


@dataclass
class Prices:
    """Purchase price parameters for all buyable items."""
    citizen: PriceParams = field(default_factory=PriceParams)
    tile: PriceParams = field(default_factory=lambda: PriceParams(u=0, y=1, z=2, v=2.0))
    wave: PriceParams = field(default_factory=lambda: PriceParams(u=0, y=1, z=2, v=2.0))
    critter_slot: PriceParams = field(default_factory=lambda: PriceParams(u=0, y=1, z=2, v=2.0))
    army: PriceParams = field(default_factory=lambda: PriceParams(u=0, y=1, z=2, v=2.0))
    wave_era_costs: list[int] = field(default_factory=lambda: [0, 200, 500, 1200, 2500, 5000, 9000, 15000, 25000])


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
    initial_wave_delay_ms: float = 15000.0
    splash_flight_ms: float = 500.0
    default_reload_time_ms: float = 2000.0

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
    neolithic_travel_offset: float = 300.0
    bronze_travel_offset: float = 300.0
    iron_travel_offset: float = 300.0
    middle_ages_travel_offset: float = 300.0
    renaissance_travel_offset: float = 300.0
    industrial_travel_offset: float = 300.0
    modern_travel_offset: float = 300.0
    future_travel_offset: float = 300.0
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
    ai_min_player_score: float = 500.0

    # -- Barbarian attacks -------------------------------------------
    # Probability per minute (Bernoulli trial) that barbarians attack.
    # Keys are lowercase English era names (same as era_effects keys).
    barbarians_aggressiveness: Dict[str, float] = field(default_factory=dict)

    # -- AI army generator per era -----------------------------------
    # Keys are lowercase YAML era names (e.g. "renaissance").
    # Each entry: {min_waves, max_waves, min_slots, max_slots,
    #              min_previous_era, max_previous_era, min_next_era, max_next_era}
    ai_generator: Dict[str, Dict[str, int]] = field(default_factory=dict)

    # -- Battle strategy / loot --------------------------------------
    min_lose_knowledge: float = 0.03
    max_lose_knowledge: float = 0.15
    min_lose_culture: float = 0.01
    max_lose_culture: float = 0.05
    artefact_steal_chance: float = 0.33
    base_artifact_steal_victory: float = 0.5
    base_artifact_steal_defeat: float = 0.05

    # -- Prices ------------------------------------------------------
    prices: Prices = field(default_factory=Prices)

    # -- Spy costs ---------------------------------------------------
    spy_costs: SpyCosts = field(default_factory=SpyCosts)

    # -- Unit upgrades -----------------------------------------------
    structure_upgrades: StructureUpgradeDef = field(default_factory=StructureUpgradeDef)
    critter_upgrades: CritterUpgradeDef = field(default_factory=CritterUpgradeDef)
    item_upgrade_base_costs: list[int] = field(default_factory=lambda: [1, 15, 100, 300, 600, 1200, 2500, 5000, 10000])

    # -- Structures --------------------------------------------------
    tower_sell_refund: float = 0.3  # fraction of build cost refunded when selling a tower
    max_spy_armies: int = 1

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
            citizen=PriceParams(**citizen_raw) if isinstance(citizen_raw, dict) else PriceParams(),
            tile=PriceParams(**prices_raw["tile"]) if "tile" in prices_raw else PriceParams(u=0, y=1, z=2, v=2.0),
            wave=PriceParams(**prices_raw["wave"]) if "wave" in prices_raw else PriceParams(u=0, y=1, z=2, v=2.0),
            critter_slot=PriceParams(**prices_raw["critter_slot"]) if "critter_slot" in prices_raw else PriceParams(u=0, y=1, z=2, v=2.0),
            army=PriceParams(**prices_raw["army"]) if "army" in prices_raw else PriceParams(u=0, y=1, z=2, v=2.0),
            wave_era_costs=list(prices_raw["wave_era_costs"]) if "wave_era_costs" in prices_raw else [0, 200, 500, 1200, 2500, 5000, 9000, 15000, 25000],
        )
    else:
        prices = Prices()

    # Handle nested era_effects → flatten travel/siege to legacy fields
    # AND build generic era_effects dict for empire effect system
    from gameserver.util.eras import ERA_YAML_TO_FIELD, ERA_YAML_TO_KEY
    _ERA_YAML_TO_FIELD = ERA_YAML_TO_FIELD
    _ERA_YAML_TO_KEY = ERA_YAML_TO_KEY
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
                era_effects_dict[era_key] = generic

    # Handle ai_generator: {era_yaml_key: {min_waves, max_waves, ...}}
    ai_generator_raw = raw.pop("ai_generator", None)
    ai_generator: Dict[str, Dict[str, int]] = (
        {k: {ik: int(iv) for ik, iv in v.items() if isinstance(iv, (int, float))}
         for k, v in ai_generator_raw.items() if isinstance(v, dict)}
        if isinstance(ai_generator_raw, dict) else {}
    )

    # Handle structure_upgrades / critter_upgrades
    su_raw = raw.pop("structure_upgrades", None)
    structure_upgrades = StructureUpgradeDef(**{k: float(v) for k, v in su_raw.items()}) \
        if isinstance(su_raw, dict) else StructureUpgradeDef()
    cu_raw = raw.pop("critter_upgrades", None)
    critter_upgrades = CritterUpgradeDef(**{k: float(v) for k, v in cu_raw.items()}) \
        if isinstance(cu_raw, dict) else CritterUpgradeDef()

    # Handle nested barbarians_aggressiveness (already a flat {era_key: float} dict)
    barbarians_raw = raw.pop("barbarians_aggressiveness", None)
    barbarians_aggressiveness: Dict[str, float] = (
        {k: float(v) for k, v in barbarians_raw.items() if isinstance(v, (int, float))}
        if isinstance(barbarians_raw, dict) else {}
    )

    # Build config from flat keys + nested spy_costs + era_effects
    cfg = GameConfig(
        spy_costs=spy,
        prices=prices,
        era_effects=era_effects_dict,
        barbarians_aggressiveness=barbarians_aggressiveness,
        ai_generator=ai_generator,
        structure_upgrades=structure_upgrades,
        critter_upgrades=critter_upgrades,
        **{
            k: v for k, v in raw.items()
            if k in GameConfig.__dataclass_fields__ and k not in ("era_effects", "barbarians_aggressiveness")
        },
    )
    return cfg
