"""battle_sim.py — Reusable headless battle simulation library.

Provides helpers to construct and run BattleState simulations without a
running server.  Import this from any script that needs to simulate battles.

Usage::

    from scripts.battle_sim import build_structures, make_battle, run_battle, BattleResult

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
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "python_server" / "src"))

from gameserver.engine.battle_service import BattleService
from gameserver.models.battle import BattleState
from gameserver.models.structure import Structure, structure_from_item
from gameserver.models.hex import HexCoord
from gameserver.models.empire import Empire
from gameserver.models.army import Army

NON_STRUCTURE_TYPES = {"empty", "path", "spawnpoint", "castle", "blocked", "void", ""}

DEFENDER_UID = 0
ATTACKER_UID = 1
ATTACK_ID = 1


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
        hex_map:    {"q,r": type_str_or_dict} — tile map as stored in saved_maps.yaml
                    or a deserialized season state.yaml.
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
        structures[sid] = structure_from_item(
            sid=sid, iid=tt, position=HexCoord(q, r), item=item,
            select_override=tile_select(tile_val),
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
        A fresh BattleState (multi-attacker model, single attacker in slot ATTACK_ID).
    """
    defender = Empire(uid=DEFENDER_UID, name=defender_name)
    defender.resources["life"] = defender_life
    defender.max_life = defender_life

    used_army = copy.deepcopy(army) if deep_copy else army
    used_structures = copy.deepcopy(structures) if deep_copy else structures

    return BattleState(
        bid=0,
        defender=defender,
        attacker_uids=[ATTACKER_UID],
        attack_ids=[ATTACK_ID],
        armies={ATTACK_ID: used_army},
        attacker_gains={ATTACKER_UID: {}},
        structures=used_structures,
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
    duration_ms: float
    # sid -> damage/kills; aggregated to iid -> ... by run_battle via `structures`
    tower_damage_by_iid: dict[str, float] = field(default_factory=dict)
    tower_kills_by_iid: dict[str, int] = field(default_factory=dict)
    # iid -> {spawned, killed, reached, castle_damage}
    critter_stats: dict[str, dict[str, float]] = field(default_factory=dict)


# ── Simulation runner ─────────────────────────────────────────────────────────

def run_battle(
    svc: BattleService,
    battle: BattleState,
    dt_ms: float = 15.0,
    max_ticks: int = 500_000,
) -> BattleResult:
    """Run a battle to completion and return a BattleResult.

    Ticks the BattleService at `dt_ms` intervals until the battle is finished
    or `max_ticks` is reached (timeout → defender wins). `dt_ms=15.0` matches
    the live battle loop's real tick cadence
    (`BattleService.run_battle_loop`'s `asyncio.sleep(0.015)`), so results are
    representative of live play.

    Args:
        svc:       BattleService instance (shared across calls).
        battle:    BattleState to simulate (mutated in place).
        dt_ms:     Simulated milliseconds per tick (default 15 ms).
        max_ticks: Safety cap; if reached the defender is declared winner.

    Returns:
        BattleResult with outcome statistics, including per-tower and
        per-critter breakdowns (by iid).
    """
    ticks = 0
    for ticks in range(max_ticks):
        svc.tick(battle, dt_ms)
        if battle.is_finished:
            break
    else:
        battle.is_finished = True
        battle.defender_won = True

    life_left = battle.defender.resources.get("life", 0.0) if battle.defender else 0.0
    max_life  = battle.defender.max_life if battle.defender else 0.0

    tower_damage_by_iid: dict[str, float] = {}
    tower_kills_by_iid: dict[str, int] = {}
    for sid, dmg in battle.tower_damage.items():
        iid = battle.structures[sid].iid if sid in battle.structures else f"sid:{sid}"
        tower_damage_by_iid[iid] = tower_damage_by_iid.get(iid, 0.0) + dmg
    for sid, kills in battle.tower_kills.items():
        iid = battle.structures[sid].iid if sid in battle.structures else f"sid:{sid}"
        tower_kills_by_iid[iid] = tower_kills_by_iid.get(iid, 0) + kills

    # Per-iid spawn count = critters removed (died/reached) + any still alive at
    # battle end (e.g. a max_ticks timeout). BattleState only tracks a global
    # critters_spawned counter, not one per iid, so this is reconstructed here.
    critter_stats: dict[str, dict[str, float]] = {}

    def _bucket(iid: str) -> dict[str, float]:
        return critter_stats.setdefault(iid, {"spawned": 0, "killed": 0, "reached": 0, "castle_damage": 0.0})

    for rc in battle.removed_critters:
        stats = _bucket(rc.get("iid", "?"))
        stats["spawned"] += 1
        if rc["reason"] == "died":
            stats["killed"] += 1
        elif rc["reason"] == "reached":
            stats["reached"] += 1
            stats["castle_damage"] += rc.get("damage", 0.0)
    for critter in battle.critters.values():
        _bucket(critter.iid)["spawned"] += 1

    killed  = sum(1 for rc in battle.removed_critters if rc.get("reason") == "died")
    reached = sum(1 for rc in battle.removed_critters if rc.get("reason") == "reached")

    return BattleResult(
        defender_won=bool(battle.defender_won),
        life_left=life_left,
        max_life=max_life,
        killed=killed,
        reached=reached,
        ticks=ticks + 1,
        duration_ms=battle.elapsed_ms,
        tower_damage_by_iid=tower_damage_by_iid,
        tower_kills_by_iid=tower_kills_by_iid,
        critter_stats=critter_stats,
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
        total += int(w.slots // cost)
    return total
