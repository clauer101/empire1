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
    ruler_xp: PriceParams = field(default_factory=lambda: PriceParams(u=0, y=10, z=1, v=2.0))


@dataclass
class SpyCosts:
    """Gold costs for spy operations."""
    defense: int = 500
    build_queue: int = 1000
    research_queue: int = 2000
    attacks: int = 5000
    artifacts: int = 10000


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
    culture_era_advantage_ratio: float = 0.5
    artifact_steal_chance: float = 0.33
    base_artifact_steal_victory: float = 0.5
    base_artifact_steal_defeat: float = 0.05

    # -- Ruler XP rewards --------------------------------------------
    ruler_xp_per_kill: float = 1.0
    ruler_xp_per_reached_per_era: float = 10.0
    ruler_xp_victory_per_era: float = 50.0

    # -- Prices ------------------------------------------------------
    prices: Prices = field(default_factory=Prices)

    # -- Spy costs ---------------------------------------------------
    spy_costs: SpyCosts = field(default_factory=SpyCosts)

    # -- Unit upgrades -----------------------------------------------
    structure_upgrades: StructureUpgradeDef = field(default_factory=StructureUpgradeDef)
    critter_upgrades: CritterUpgradeDef = field(default_factory=CritterUpgradeDef)
    item_upgrade_base_costs: list[int] = field(default_factory=lambda: [1, 15, 100, 300, 600, 1200, 2500, 5000, 10000])

    # -- End-game rally ----------------------------------------------
    # iid of the item whose completion triggers the end rally
    end_criterion: str = ""
    # Effects applied to ALL empires while the rally is active
    end_rally_effects: Dict[str, float] = field(default_factory=dict)
    # Duration of the rally in seconds (after activation, game ends)
    end_rally_duration: float = 604800.0  # 1 week default

    # -- Structures --------------------------------------------------
    tower_sell_refund: float = 0.3  # fraction of build cost refunded when selling a tower
    max_spy_armies: int = 1

    # -- Artifact lottery --------------------------------------------
    accounts_per_artifact: int = 12

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


def _require(d: dict, key: str, context: str = "game.yaml") -> object:
    """Raise ValueError if key is missing from dict."""
    if key not in d:
        raise ValueError(f"Missing required config key '{key}' in {context}")
    return d[key]


def _require_price_params(prices_raw: dict, key: str) -> PriceParams:
    if key not in prices_raw:
        raise ValueError(f"Missing required prices.{key} in game.yaml")
    return PriceParams(**prices_raw[key])


def load_game_config(path: str = DEFAULT_GAME_CONFIG_PATH) -> GameConfig:
    """Load game configuration from a YAML file.

    All keys are required — missing keys raise ValueError so the server
    fails fast at startup rather than silently using wrong defaults.
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Game config not found at {p} — this file is required")

    with p.open() as f:
        raw = yaml.safe_load(f) or {}

    log.info("Loaded game config from %s (%d keys)", p, len(raw))

    # -- spy_costs (required section) ------------------------------------
    if "spy_costs" not in raw:
        raise ValueError("Missing required section 'spy_costs' in game.yaml")
    spy_raw = raw.pop("spy_costs")
    spy = SpyCosts(**spy_raw)

    # -- prices (required section) ---------------------------------------
    if "prices" not in raw:
        raise ValueError("Missing required section 'prices' in game.yaml")
    prices_raw = raw.pop("prices")
    wave_era_costs = list(_require(prices_raw, "wave_era_costs", "prices"))  # type: ignore[call-overload]
    if len(wave_era_costs) != 9:
        raise ValueError(
            f"prices.wave_era_costs must have exactly 9 entries (one per era), got {len(wave_era_costs)}"
        )
    item_upgrade_base_costs_raw = raw.get("item_upgrade_base_costs")
    if item_upgrade_base_costs_raw is not None and len(item_upgrade_base_costs_raw) != 9:
        raise ValueError(
            f"item_upgrade_base_costs must have exactly 9 entries, got {len(item_upgrade_base_costs_raw)}"
        )
    prices = Prices(
        citizen=_require_price_params(prices_raw, "citizen"),
        tile=_require_price_params(prices_raw, "tile"),
        wave=_require_price_params(prices_raw, "wave"),
        critter_slot=_require_price_params(prices_raw, "critter_slot"),
        army=_require_price_params(prices_raw, "army"),
        wave_era_costs=wave_era_costs,
        ruler_xp=_require_price_params(prices_raw, "ruler_xp"),
    )

    # -- era_effects (required section) ----------------------------------
    from gameserver.util.eras import ERA_YAML_TO_FIELD, ERA_YAML_TO_KEY
    if "era_effects" not in raw:
        raise ValueError("Missing required section 'era_effects' in game.yaml")
    era_raw = raw.pop("era_effects")
    era_effects_dict: Dict[str, Dict[str, float]] = {}
    for yaml_key, vals in era_raw.items():
        if not isinstance(vals, dict):
            continue
        field_prefix = ERA_YAML_TO_FIELD.get(yaml_key, yaml_key)
        era_key = ERA_YAML_TO_KEY.get(yaml_key)
        if "travel_offset" in vals:
            raw[f"{field_prefix}_travel_offset"] = vals["travel_offset"]

        if era_key:
            era_effects_dict[era_key] = {
                k: v for k, v in vals.items()
                if k not in ("travel_offset", "siege_offset")
            }

    # -- structure_upgrades / critter_upgrades (required) ----------------
    if "structure_upgrades" not in raw:
        raise ValueError("Missing required section 'structure_upgrades' in game.yaml")
    su_raw = raw.pop("structure_upgrades")
    structure_upgrades = StructureUpgradeDef(**{k: float(v) for k, v in su_raw.items()})

    if "critter_upgrades" not in raw:
        raise ValueError("Missing required section 'critter_upgrades' in game.yaml")
    cu_raw = raw.pop("critter_upgrades")
    critter_upgrades = CritterUpgradeDef(**{k: float(v) for k, v in cu_raw.items()})

    # -- ai_generator (optional, empty dict if absent) -------------------
    ai_generator_raw = raw.pop("ai_generator", None)
    ai_generator: Dict[str, Dict[str, int]] = (
        {k: {ik: int(iv) for ik, iv in v.items() if isinstance(iv, (int, float))}
         for k, v in ai_generator_raw.items() if isinstance(v, dict)}
        if isinstance(ai_generator_raw, dict) else {}
    )

    # -- barbarians_aggressiveness (optional) ----------------------------
    barbarians_raw = raw.pop("barbarians_aggressiveness", None)
    barbarians_aggressiveness: Dict[str, float] = (
        {k: float(v) for k, v in barbarians_raw.items() if isinstance(v, (int, float))}
        if isinstance(barbarians_raw, dict) else {}
    )

    # -- end_ralley_effects (required) -----------------------------------
    if "end_ralley_effects" not in raw:
        raise ValueError("Missing required key 'end_ralley_effects' in game.yaml")
    end_rally_effects_raw = raw.pop("end_ralley_effects")
    end_rally_effects: Dict[str, float] = {
        k: float(v) for k, v in end_rally_effects_raw.items() if isinstance(v, (int, float))
    }
    if "end_ralley_duration" in raw:
        raw["end_rally_duration"] = raw.pop("end_ralley_duration")

    # -- required flat scalar keys ---------------------------------------
    _REQUIRED_SCALAR_KEYS = [
        "base_gold_per_sec", "base_culture_per_sec", "citizen_effect",
        "base_build_speed", "base_research_speed",
        "starting_max_life", "restore_life_after_loss_offset",
        "min_lose_knowledge", "max_lose_knowledge",
        "min_lose_culture", "max_lose_culture",
        "culture_era_advantage_ratio",
        "base_artifact_steal_victory", "base_artifact_steal_defeat",
        "ruler_xp_per_kill", "ruler_xp_per_reached_per_era", "ruler_xp_victory_per_era",
        "item_upgrade_base_costs",
        "end_criterion",
    ]
    for key in _REQUIRED_SCALAR_KEYS:
        _require(raw, key)

    cfg = GameConfig(
        spy_costs=spy,
        prices=prices,
        era_effects=era_effects_dict,
        barbarians_aggressiveness=barbarians_aggressiveness,
        ai_generator=ai_generator,
        structure_upgrades=structure_upgrades,
        critter_upgrades=critter_upgrades,
        end_rally_effects=end_rally_effects,
        **{
            k: v for k, v in raw.items()
            if k in GameConfig.__dataclass_fields__
            and k not in ("era_effects", "barbarians_aggressiveness", "end_rally_effects")
        },
    )
    return cfg
