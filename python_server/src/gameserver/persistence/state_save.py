"""State save — serializes full game state to YAML.

On server shutdown the complete game state is written to a YAML file
so it can be restored on startup.  Models whose logic is not yet
implemented are marked with TODO comments in the serializer.
"""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any, Optional

import yaml

from gameserver.models.army import Army, CritterWave, SpyArmy
from gameserver.models.attack import Attack, AttackPhase
from gameserver.models.battle import BattleState
from gameserver.models.critter import Critter
from gameserver.models.empire import Empire
from gameserver.models.hex import HexCoord
from gameserver.models.map import Direction, HexMap
from gameserver.models.shot import Shot
from gameserver.models.structure import Structure

log = logging.getLogger(__name__)

# Default path for the state file (relative to working directory)
DEFAULT_STATE_PATH = "state.yaml"


# ===================================================================
# Public API
# ===================================================================


async def save_state(
    empires: dict[int, Empire],
    attacks: Optional[list[Attack]] = None,
    battles: Optional[list[BattleState]] = None,
    path: str = DEFAULT_STATE_PATH,
) -> None:
    """Serialize the entire game state to a YAML file.

    Args:
        empires: All registered empires keyed by uid.
        attacks: Active attacks (may be empty if AttackService not yet implemented).
        battles: Running battles (may be empty if BattleService not yet implemented).
        path: Output file path.
    """
    state: dict[str, Any] = {
        "meta": _serialize_meta(),
        "empires": [_serialize_empire(e) for e in empires.values()],
        "attacks": [_serialize_attack(a) for a in (attacks or [])],
        "battles": [_serialize_battle(b) for b in (battles or [])],
    }

    out = Path(path)
    tmp = out.with_suffix(".yaml.tmp")
    try:
        tmp.write_text(
            yaml.dump(state, default_flow_style=False, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )
        tmp.replace(out)
        log.info("Game state saved to %s (%d empires, %d attacks, %d battles)",
                 path, len(empires), len(attacks or []), len(battles or []))
    except Exception:
        log.exception("Failed to save game state to %s", path)
        if tmp.exists():
            tmp.unlink(missing_ok=True)
        raise


# ===================================================================
# Meta
# ===================================================================

def _serialize_meta() -> dict[str, Any]:
    return {
        "version": 1,
        "saved_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "saved_at_unix": time.time(),
    }


# ===================================================================
# HexCoord helpers
# ===================================================================

def _hex(c: HexCoord) -> dict[str, int]:
    return {"q": c.q, "r": c.r}


def _hex_list(coords: list[HexCoord]) -> list[dict[str, int]]:
    return [_hex(c) for c in coords]


def _hex_set(coords: set[HexCoord]) -> list[dict[str, int]]:
    return sorted([_hex(c) for c in coords], key=lambda h: (h["q"], h["r"]))


# ===================================================================
# Empire & sub-models
# ===================================================================

def _serialize_empire(empire: Empire) -> dict[str, Any]:
    return {
        "uid": empire.uid,
        "name": empire.name,
        "resources": dict(empire.resources),
        "buildings": dict(empire.buildings),
        "build_queue": empire.build_queue,
        "knowledge": dict(empire.knowledge),
        "research_queue": empire.research_queue,
        "citizens": dict(empire.citizens),
        "effects": dict(empire.effects),
        "artefacts": list(empire.artefacts),
        "max_life": empire.max_life,
        "structures": {
            sid: _serialize_structure(s)
            for sid, s in empire.structures.items()
        },
        "armies": [_serialize_army(a) for a in empire.armies],
        "spies": [_serialize_spy_army(s) for s in empire.spies],
        "bosses": {
            iid: _serialize_critter(c)
            for iid, c in empire.bosses.items()
        },
        "empire_map": _serialize_hex_map(empire.empire_map),
    }


def _serialize_structure(s: Structure) -> dict[str, Any]:
    return {
        "sid": s.sid,
        "iid": s.iid,
        "position": _hex(s.position),
        "damage": s.damage,
        "range": s.range,
        "reload_time_ms": s.reload_time_ms,
        "shot_speed": s.shot_speed,
        "shot_type": s.shot_type,
        "effects": dict(s.effects),
        # Transient battle state — not persisted in empire context:
        # focus_cid, reload_remaining_ms are battle-only
    }


def _serialize_critter(c: Critter) -> dict[str, Any]:
    return {
        "cid": c.cid,
        "iid": c.iid,
        "health": c.health,
        "max_health": c.max_health,
        "speed": c.speed,
        "armour": c.armour,
        "path": _hex_list(c.path),
        "path_progress": c.path_progress,
        "capture": dict(c.capture),
        "bonus": dict(c.bonus),
        "spawn_on_death": dict(c.spawn_on_death),
        "slow_remaining_ms": c.slow_remaining_ms,
        "slow_speed": c.slow_speed,
        "burn_remaining_ms": c.burn_remaining_ms,
        "burn_dps": c.burn_dps,
        "level": c.level,
        "xp": c.xp,
        "is_boss": c.is_boss,
    }


def _serialize_critter_wave(wave: CritterWave) -> dict[str, Any]:
    return {
        "critter_iid": wave.critter_iid,
        "slots": wave.slots,
        "critters": [_serialize_critter(c) for c in wave.critters],
        "spawn_interval_ms": wave.spawn_interval_ms,
        "next_spawn_ms": wave.next_spawn_ms,
        "spawn_pointer": wave.spawn_pointer,
    }


def _serialize_army(army: Army) -> dict[str, Any]:
    return {
        "aid": army.aid,
        "uid": army.uid,
        "direction": army.direction.value,
        "name": army.name,
        "waves": [_serialize_critter_wave(w) for w in army.waves],
        "wave_pointer": army.wave_pointer,
        "next_wave_ms": army.next_wave_ms,
    }


def _serialize_spy_army(spy: SpyArmy) -> dict[str, Any]:
    return {
        "aid": spy.aid,
        "uid": spy.uid,
        "options": dict(spy.options),
    }


def _serialize_hex_map(m: HexMap) -> dict[str, Any]:
    return {
        "paths": {
            d.value: _hex_list(coords)
            for d, coords in m.paths.items()
        },
        "build_tiles": _hex_set(m.build_tiles),
        "occupied": _hex_set(m.occupied),
    }


# ===================================================================
# Attack
# ===================================================================

def _serialize_attack(attack: Attack) -> dict[str, Any]:
    """Serialize an attack.

    TODO: AttackService has no active attack list yet — attacks
          are serialized structurally but no attacks will be present
          until AttackService.start_attack() is implemented.
    """
    return {
        "attack_id": attack.attack_id,
        "attacker_uid": attack.attacker_uid,
        "defender_uid": attack.defender_uid,
        "army_aid": attack.army_aid,
        "phase": attack.phase.value,
        "eta_seconds": attack.eta_seconds,
        "siege_remaining_seconds": attack.siege_remaining_seconds,
    }


# ===================================================================
# Battle
# ===================================================================

def _serialize_shot(shot: Shot) -> dict[str, Any]:
    return {
        "damage": shot.damage,
        "target_cid": shot.target_cid,
        "source_sid": shot.source_sid,
        "shot_type": shot.shot_type,
        "effects": dict(shot.effects),
        "flight_remaining_ms": shot.flight_remaining_ms,
    }


def _serialize_battle(battle: BattleState) -> dict[str, Any]:
    """Serialize a running battle.

    TODO: BattleService.run_battle() is not yet fully implemented.
          Active battles are lost on shutdown for now.
          Once implemented, battles should either be saved and resumed
          or gracefully ended before shutdown.
    """
    return {
        "bid": battle.bid,
        "defender_uid": battle.defender_uid,
        "attacker_uids": list(battle.attacker_uids),
        "armies": {
            key: _serialize_army(a) for key, a in battle.armies.items()
        },
        "critters": {
            str(cid): _serialize_critter(c) for cid, c in battle.critters.items()
        },
        "structures": {
            str(sid): _serialize_structure(s) for sid, s in battle.structures.items()
        },
        "pending_shots": [_serialize_shot(s) for s in battle.pending_shots],
        "elapsed_ms": battle.elapsed_ms,
        "is_finished": battle.is_finished,
        "defender_won": battle.defender_won,
        "observer_uids": sorted(battle.observer_uids),
        "attacker_gains": {
            str(uid): dict(gains) for uid, gains in battle.attacker_gains.items()
        },
        "defender_losses": dict(battle.defender_losses),
    }
