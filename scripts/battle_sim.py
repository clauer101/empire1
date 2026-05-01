"""battle_sim.py — Reusable headless battle simulation library.

Provides helpers to construct and run BattleState simulations without a
running server.  Import this from any script that needs to simulate battles.

Usage::

    from battle_sim import build_structures, make_battle, run_battle, BattleResult, compute_total_critters

    config   = load_configuration(config_dir=CONFIG_DIR)
    items    = {item.iid: item for item in config.items}
    svc      = BattleService(items=items)

    path       = find_path_from_spawn_to_castle(hex_map)
    structures = build_structures(hex_map, items)
    battle     = make_battle(army, structures, path, defender_life=10.0)
    result     = run_battle(svc, battle)

    print(result.defender_won, result.killed, result.reached, result.life_left)
"""

from __future__ import annotations

import copy
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parent / "python_server" / "src"))

from gameserver.engine.battle_service import BattleService
from gameserver.models.battle import BattleState
from gameserver.models.structure import Structure
from gameserver.models.hex import HexCoord
from gameserver.models.empire import Empire
from gameserver.models.army import Army

NON_STRUCTURE_TYPES = {"empty", "path", "spawnpoint", "castle", "blocked", "void", ""}


# ── Tile helpers ──────────────────────────────────────────────────────────────

def tile_type(v) -> str:
    """Return the type string from a tile value (str or dict)."""
    return v if isinstance(v, str) else v.get("type", "empty")


def tile_select(v, default: str = "first") -> str:
    """Return the select mode from a tile value (str or dict)."""
    return v.get("select", default) if isinstance(v, dict) else default


# ── Structure builder ─────────────────────────────────────────────────────────

def build_structures(hex_map: dict, items_dict: dict) -> dict[int, Structure]:
    """Build a sid→Structure dict from a hex_map and item catalog.

    Args:
        hex_map:    {\"q,r\": type_str_or_dict} — tile map as stored in saved_maps.yaml.
        items_dict: {iid: ItemDetails} — full item catalog from config.

    Returns:
        Dict mapping sid (1-based int) → Structure.
    """
    structures: dict[int, Structure] = {}
    sid = 1
    for tile_key, tile_val in hex_map.items():
        tt = tile_type(tile_val)
        if tt in NON_STRUCTURE_TYPES:
            continue
        item = items_dict.get(tt)
        if not item:
            continue
        q, r = map(int, tile_key.split(","))
        structures[sid] = Structure(
            sid=sid,
            iid=tt,
            position=HexCoord(q, r),
            damage=getattr(item, "damage", 1.0),
            range=getattr(item, "range", 1),
            reload_time_ms=getattr(item, "reload_time_ms", 2000.0),
            shot_speed=getattr(item, "shot_speed", 1.0),
            shot_type=getattr(item, "shot_type", "normal"),
            shot_sprite=getattr(item, "shot_sprite", ""),
            select=tile_select(tile_val, getattr(item, "select", "first")),
            effects=getattr(item, "effects", {}),
        )
        sid += 1
    return structures


# ── Battle factory ────────────────────────────────────────────────────────────

def make_battle(
    army: Army,
    structures: dict[int, Structure],
    critter_path: list,
    defender_life: float = 10.0,
    defender_name: str = "Defender",
    attacker_name: str = "AI",
    deep_copy: bool = True,
) -> BattleState:
    """Create a BattleState ready for simulation.

    Args:
        army:           Army to attack with.
        structures:     Tower layout (sid→Structure).
        critter_path:   List of HexCoord from spawn to castle.
        defender_life:  Starting life points for the defender.
        defender_name:  Display name for the defender empire.
        attacker_name:  Display name for the attacker empire.
        deep_copy:      If True, deep-copy army and structures so the originals
                        are not mutated (useful when running the same army
                        against multiple maps).

    Returns:
        A fresh BattleState.
    """
    defender = Empire(uid=0, name=defender_name)
    defender.resources["life"] = defender_life
    defender.max_life = defender_life

    return BattleState(
        bid=0,
        defender=defender,
        attacker=Empire(uid=1, name=attacker_name),
        army=copy.deepcopy(army) if deep_copy else army,
        structures=copy.deepcopy(structures) if deep_copy else structures,
        critter_path=critter_path,
    )


# ── Result dataclass ──────────────────────────────────────────────────────────

@dataclass
class BattleResult:
    defender_won: bool
    life_left: float
    max_life: float
    killed: int
    reached: int
    ticks: int


# ── Simulation runner ─────────────────────────────────────────────────────────

def run_battle(
    svc: BattleService,
    battle: BattleState,
    dt_ms: float = 15.0,
    max_ticks: int = 500_000,
) -> BattleResult:
    """Run a battle to completion and return a BattleResult.

    Ticks the BattleService at `dt_ms` intervals until the battle is finished
    or `max_ticks` is reached (timeout → defender wins).

    Args:
        svc:       BattleService instance (shared across calls).
        battle:    BattleState to simulate (mutated in place).
        dt_ms:     Simulated milliseconds per tick (default 15 ms).
        max_ticks: Safety cap; if reached the defender is declared winner.

    Returns:
        BattleResult with outcome statistics.
    """
    ticks = 0
    for ticks in range(max_ticks):
        svc.tick(battle, dt_ms)
        if battle.is_finished:
            break
    else:
        battle.is_finished = True
        battle.defender_won = True

    life_left = battle.defender.resources.get("life", 0.0)
    max_life  = battle.defender.max_life
    killed    = sum(1 for rc in battle.removed_critters if rc.get("reason") == "died")
    reached   = sum(1 for rc in battle.removed_critters if rc.get("reason") == "reached")

    return BattleResult(
        defender_won=bool(battle.defender_won),
        life_left=life_left,
        max_life=max_life,
        killed=killed,
        reached=reached,
        ticks=ticks + 1,
    )


# ── Utility ───────────────────────────────────────────────────────────────────

def compute_total_critters(waves, items_dict: dict) -> int:
    """Estimate the total number of critters an army will spawn.

    Args:
        waves:      List of CritterWave objects.
        items_dict: Item catalog for slot-cost lookups.

    Returns:
        Estimated critter count.
    """
    total = 0
    for w in waves:
        item = items_dict.get(w.iid)
        cost = max(1, int(getattr(item, "slots", 1) or 1)) if item else 1
        total += w.slots // cost
    return total
