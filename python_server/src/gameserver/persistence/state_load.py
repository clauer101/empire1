"""State load — restores game state from a YAML dump.

Reconstructs all empires, armies, structures, attacks, and battles
from a previously saved YAML state file.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import yaml

from gameserver.models.army import Army, CritterWave, SpyArmy
from gameserver.models.attack import Attack, AttackPhase
from gameserver.models.battle import BattleState
from gameserver.models.critter import Critter
from gameserver.models.empire import Empire
from gameserver.models.hex import HexCoord
from gameserver.models.shot import Shot
from gameserver.models.structure import Structure
from gameserver.persistence.state_save import DEFAULT_STATE_PATH

log = logging.getLogger(__name__)


# ===================================================================
# Result container
# ===================================================================

@dataclass
class RestoredState:
    """Container for all data restored from a YAML state file.

    Attributes:
        empires: Restored empires keyed by uid.
        attacks: Restored active attacks.
        battles: Restored active battles.
        meta: Metadata from the save file (version, save timestamp).
    """

    empires: dict[int, Empire] = field(default_factory=dict)
    attacks: list[Attack] = field(default_factory=list)
    battles: list[BattleState] = field(default_factory=list)
    meta: dict[str, Any] = field(default_factory=dict)


# ===================================================================
# Public API
# ===================================================================


async def load_state(path: str = DEFAULT_STATE_PATH) -> Optional[RestoredState]:
    """Load game state from a YAML file.

    Returns None if the file does not exist.

    Args:
        path: Path to the YAML state file.

    Returns:
        A :class:`RestoredState` with all restored objects, or None.
    """
    state_file = Path(path)
    if not state_file.exists():
        log.info("No state file found at %s", path)
        return None

    try:
        raw = yaml.safe_load(state_file.read_text(encoding="utf-8"))
    except Exception:
        log.exception("Failed to parse state file %s", path)
        return None

    if not isinstance(raw, dict):
        log.warning("State file %s has unexpected format (not a dict)", path)
        return None

    result = RestoredState()
    result.meta = raw.get("meta", {})
    log.info("Restoring state from %s (saved at %s, version %s)",
             path, result.meta.get("saved_at", "?"), result.meta.get("version", "?"))

    # ---- Empires ----
    for empire_dict in raw.get("empires", []):
        try:
            empire = _deserialize_empire(empire_dict)
            result.empires[empire.uid] = empire
        except Exception:
            log.exception("Failed to restore empire: %s", empire_dict.get("uid", "?"))

    # ---- Attacks ----
    for attack_dict in raw.get("attacks", []):
        try:
            result.attacks.append(_deserialize_attack(attack_dict))
        except Exception:
            log.exception("Failed to restore attack: %s", attack_dict.get("attack_id", "?"))

    # ---- Battles ----
    # TODO: BattleService.run_battle() is not yet implemented.
    #       Restored BattleState objects cannot be resumed yet.
    #       They are loaded for completeness but will not be active.
    battle_dicts = []  # Keep dicts for linking
    for battle_dict in raw.get("battles", []):
        try:
            battle = _deserialize_battle(battle_dict)
            result.battles.append(battle)
            battle_dicts.append((battle, battle_dict))
        except Exception:
            log.exception("Failed to restore battle: %s", battle_dict.get("bid", "?"))

    # ---- Link defender empires to battles ----
    for battle, battle_dict in battle_dicts:
        defender_uid = battle_dict.get("defender_uid")
        if defender_uid and defender_uid in result.empires:
            battle.defender = result.empires[defender_uid]
        # Link attacker (first attacker_uid)
        attacker_uids = battle_dict.get("attacker_uids", [])
        if attacker_uids and attacker_uids[0] in result.empires:
            battle.attacker = result.empires[attacker_uids[0]]

    log.info("Restored %d empires, %d attacks, %d battles",
             len(result.empires), len(result.attacks), len(result.battles))
    return result


# ===================================================================
# HexCoord helpers
# ===================================================================

def _to_hex(d: dict[str, int]) -> HexCoord:
    return HexCoord(q=d["q"], r=d["r"])


def _to_hex_list(items: list[dict[str, int]]) -> list[HexCoord]:
    return [_to_hex(h) for h in items]


def _to_hex_set(items: list[dict[str, int]]) -> set[HexCoord]:
    return {_to_hex(h) for h in items}


# ===================================================================
# Empire & sub-models
# ===================================================================

def _deserialize_empire(d: dict[str, Any]) -> Empire:
    structures: dict[int, Structure] = {}
    for sid_str, s_dict in d.get("structures", {}).items():
        sid = int(sid_str)
        structures[sid] = _deserialize_structure(s_dict)

    armies = [_deserialize_army(a) for a in d.get("armies", [])]
    spies = [_deserialize_spy_army(s) for s in d.get("spies", [])]

    bosses: dict[str, Critter] = {}
    for iid, c_dict in d.get("bosses", {}).items():
        bosses[iid] = _deserialize_critter(c_dict)

    return Empire(
        uid=d["uid"],
        name=d.get("name", ""),
        resources=dict(d.get("resources", {"gold": 0.0, "culture": 0.0, "life": 10.0})),
        buildings=dict(d.get("buildings", {})),
        build_queue=d.get("build_queue"),
        knowledge=dict(d.get("knowledge", {})),
        research_queue=d.get("research_queue"),
        citizens=dict(d.get("citizens", {"merchant": 0, "scientist": 0, "artist": 0})),
        effects=dict(d.get("effects", {})),
        artefacts=list(d.get("artefacts", [])),
        max_life=d.get("max_life", 10.0),
        structures=structures,
        armies=armies,
        spies=spies,
        bosses=bosses,
        hex_map=_deserialize_editor_hex_map(d.get("hex_map", [])),
    )


def _deserialize_structure(d: dict[str, Any]) -> Structure:
    return Structure(
        sid=d["sid"],
        iid=d["iid"],
        position=_to_hex(d["position"]),
        damage=d["damage"],
        range=d["range"],
        reload_time_ms=d["reload_time_ms"],
        shot_speed=d["shot_speed"],
        shot_type=d.get("shot_type", "normal"),
        effects=dict(d.get("effects", {})),
    )


def _deserialize_critter(d: dict[str, Any]) -> Critter:
    return Critter(
        cid=d["cid"],
        iid=d["iid"],
        health=d["health"],
        max_health=d["max_health"],
        speed=d["speed"],
        armour=d["armour"],
        path=_to_hex_list(d.get("path", [])),
        path_progress=d.get("path_progress", 0.0),
        capture=dict(d.get("capture", {})),
        bonus=dict(d.get("bonus", {})),
        spawn_on_death=dict(d.get("spawn_on_death", {})),
        slow_remaining_ms=d.get("slow_remaining_ms", 0.0),
        slow_speed=d.get("slow_speed", 0.0),
        burn_remaining_ms=d.get("burn_remaining_ms", 0.0),
        burn_dps=d.get("burn_dps", 0.0),
        level=d.get("level", 1),
        xp=d.get("xp", 0.0),
        is_boss=d.get("is_boss", False),
        scale=float(d.get("scale", 1.0)),
    )


def _deserialize_critter_wave(d: dict[str, Any]) -> CritterWave:
    return CritterWave(
        wave_id=d["wave_id"],
        iid=d.get("iid", "SLAVE"),
        slots=d.get("slots", 0),
        num_critters_spawned=d.get("num_critters_spawned", 0),
        next_critter_ms=d.get("next_critter_ms", 0.0),
    )


def _deserialize_army(d: dict[str, Any]) -> Army:
    return Army(
        aid=d["aid"],
        uid=d["uid"],
        name=d.get("name", ""),
        waves=[_deserialize_critter_wave(w) for w in d.get("waves", [])],
    )


def _deserialize_spy_army(d: dict[str, Any]) -> SpyArmy:
    return SpyArmy(
        aid=d["aid"],
        uid=d["uid"],
        options=dict(d.get("options", {})),
    )


def _deserialize_editor_hex_map(tiles_list: Any) -> dict[str, str]:
    """Convert editor hex_map from list format to dict format {"q,r": "type"}.
    
    Converts the persistent YAML list format back to the internal
    representation used by composer.js. Handles both list and dict formats
    for backwards compatibility.
    """
    result: dict[str, str] = {}
    
    if isinstance(tiles_list, list):
        # New format: list of tile dicts
        for tile in tiles_list:
            if isinstance(tile, dict) and "q" in tile and "r" in tile:
                key = f"{tile['q']},{tile['r']}"
                tile_type = tile.get("type", "empty")
                result[key] = tile_type
    elif isinstance(tiles_list, dict):
        # Old format: already a dict, keep as-is
        result = tiles_list
    
    return result


# ===================================================================
# Attack
# ===================================================================

def _deserialize_attack(d: dict[str, Any]) -> Attack:
    """Deserialize an attack."""
    return Attack(
        attack_id=d["attack_id"],
        attacker_uid=d["attacker_uid"],
        defender_uid=d["defender_uid"],
        army_aid=d["army_aid"],
        phase=AttackPhase(d.get("phase", "travelling")),
        eta_seconds=d.get("eta_seconds", 0.0),
        total_eta_seconds=d.get("total_eta_seconds", 60.0),  # default to 60s if not in save
        siege_remaining_seconds=d.get("siege_remaining_seconds", 0.0),
        total_siege_seconds=d.get("total_siege_seconds", 30.0),  # default to 30s if not in save
    )


# ===================================================================
# Battle
# ===================================================================

def _deserialize_shot(d: dict[str, Any]) -> Shot:
    from gameserver.models.hex import HexCoord
    origin = None
    if d.get("origin"):
        origin = HexCoord(int(d["origin"].get("q", 0)), int(d["origin"].get("r", 0)))
    
    return Shot(
        damage=d["damage"],
        target_cid=d["target_cid"],
        source_sid=d["source_sid"],
        shot_type=d.get("shot_type", 0),
        effects=dict(d.get("effects", {})),
        flight_remaining_ms=d.get("flight_remaining_ms", 0.0),
        origin=origin,
        path_progress=d.get("path_progress", 0.0),
    )


def _deserialize_battle(d: dict[str, Any]) -> BattleState:
    """Deserialize a battle.

    TODO: BattleService.run_battle() is not yet fully implemented.
          Restored battles cannot be resumed as async tasks yet.
          Once BattleService supports resumption, add a
          ``resume_battle(state: BattleState)`` method.
    """
    attacker_dict = d.get("attacker")
    attacker = _deserialize_army(attacker_dict) if attacker_dict else None

    critters: dict[int, Critter] = {}
    for cid_str, c_dict in d.get("critters", {}).items():
        critters[int(cid_str)] = _deserialize_critter(c_dict)

    structures: dict[int, Structure] = {}
    for sid_str, s_dict in d.get("structures", {}).items():
        structures[int(sid_str)] = _deserialize_structure(s_dict)

    pending_shots = [_deserialize_shot(s) for s in d.get("pending_shots", [])]

    attacker_gains: dict[int, dict[str, float]] = {}
    for uid_str, gains in d.get("attacker_gains", {}).items():
        attacker_gains[int(uid_str)] = dict(gains)
    
    # Load critter path if present
    critter_path = []
    if "critter_path" in d:
        from gameserver.models.hex import HexCoord
        critter_path = [HexCoord(int(c.get("q", 0)), int(c.get("r", 0))) 
                        for c in d.get("critter_path", [])]

    return BattleState(
        bid=d["bid"],
        defender=None,  # Will be loaded separately
        attacker=None,  # Will be loaded separately
        attack_id=d.get("attack_id"),
        army=None,  # Will be loaded separately
        critters=critters,
        structures=structures,
        pending_shots=pending_shots,
        critter_path=critter_path,
        elapsed_ms=d.get("elapsed_ms", 0.0),
        is_finished=d.get("is_finished", False),
        defender_won=d.get("defender_won"),
        observer_uids=set(d.get("observer_uids", [])),
        attacker_gains=attacker_gains,
        defender_losses=dict(d.get("defender_losses", {})),
    )
