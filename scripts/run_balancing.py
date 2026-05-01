#!/usr/bin/env python3
"""Balancing test script.

Loads maps from config/saved_maps.yaml, determines each map's dominant era
(the era with the most towers), runs all AI armies from that era against it,
and prints a table like test_early_maps.py.

--age ERA  Only maps whose dominant era matches (comma-separated substrings,
           case-insensitive). e.g. "bronze", "industrial".
"""

import asyncio
import argparse
import copy
import re
import sys
import time
from collections import Counter
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent / "python_server" / "src"))

from gameserver.main import load_configuration
from gameserver.engine.battle_service import BattleService
from gameserver.engine.hex_pathfinding import find_path_from_spawn_to_castle
from gameserver.models.battle import BattleState
from gameserver.models.structure import Structure
from gameserver.models.hex import HexCoord
from gameserver.models.empire import Empire
from gameserver.models.army import Army, CritterWave

# ── Constants ────────────────────────────────────────────────

CONFIG_DIR = str(Path(__file__).resolve().parent / "python_server" / "config")
SAVED_MAPS_PATH = Path(__file__).resolve().parent / "python_server" / "config" / "saved_maps.yaml"
AI_WAVES_PATH = Path(__file__).resolve().parent / "python_server" / "config" / "ai_waves.yaml"

NON_STRUCTURE_TYPES = {"empty", "path", "spawnpoint", "castle", "blocked", "void", ""}

TOWER_ERA: dict[str, str] = {
    "BASIC_TOWER": "Stone Age", "SLING_TOWER": "Stone Age",
    "DOUBLE_SLING_TOWER": "Neolithic", "SPIKE_TRAP": "Neolithic",
    "ARROW_TOWER": "Bronze Age", "BALLISTA_TOWER": "Bronze Age", "FIRE_TOWER": "Bronze Age",
    "CATAPULTS": "Iron Age", "ARBELESTE_TOWER": "Iron Age",
    "TAR_TOWER": "Middle Ages", "HEAVY_TOWER": "Middle Ages", "BOILING_OIL": "Middle Ages",
    "CANNON_TOWER": "Renaissance", "RIFLE_TOWER": "Renaissance",
    "COLD_TOWER": "Renaissance", "ICE_TOWER": "Renaissance",
    "FLAME_THROWER": "Industrial", "SHOCK_TOWER": "Industrial",
    "PARALYZNG_TOWER": "Industrial", "NAPALM_THROWER": "Industrial",
    "MG_TOWER": "Modern", "RAPID_FIRE_MG_BUNKER": "Modern",
    "RADAR_TOWER": "Modern", "ANTI_AIR_TOWER": "Modern", "LASER_TOWER": "Modern",
    "SNIPER_TOWER": "Future", "ROCKET_TOWER": "Future",
}

# Section keywords in ai_waves.yaml → era label
ERA_KEYWORDS = [
    ("ZUKUNFT", "Future"),
    ("MODERN", "Modern"),
    ("INDUSTR", "Industrial"),
    ("RENAIS", "Renaissance"),
    ("MITTEL", "Middle Ages"),
    ("EISEN", "Iron Age"),
    ("BRONZE", "Bronze Age"),
    ("NEOLITH", "Neolithic"),
    ("STEIN", "Stone Age"),
]


# ── Helpers ──────────────────────────────────────────────────

def _tile_type(v) -> str:
    return v if isinstance(v, str) else v.get("type", "empty")


def _tile_select(v, default="first") -> str:
    return v.get("select", default) if isinstance(v, dict) else default


# ── Map loading ──────────────────────────────────────────────

def load_saved_maps() -> list[dict]:
    data = yaml.safe_load(SAVED_MAPS_PATH.read_text())
    result = []
    for m in (data.get("maps") or []):
        tiles_list = m.get("hex_map") or []
        hex_map = {f"{t['q']},{t['r']}": t.get("type", "") for t in tiles_list}
        result.append({
            "name": m.get("name", m.get("id", "?")),
            "hex_map": hex_map,
            "life": m.get("life"),
        })
    return result


def dominant_era(hex_map: dict) -> str | None:
    """Return the era with the most towers in this map, or None."""
    era_counts: Counter[str] = Counter()
    for tile_val in hex_map.values():
        tt = _tile_type(tile_val)
        era = TOWER_ERA.get(tt)
        if era:
            era_counts[era] += 1
    if not era_counts:
        return None
    return era_counts.most_common(1)[0][0]


# ── Army loading by era ─────────────────────────────────────

def load_armies_by_era(game_config) -> dict[str, list[tuple[str, Army]]]:
    """Parse ai_waves.yaml, group armies by era section header.

    Returns {era_label: [(name, Army), ...]}.
    """
    raw = yaml.safe_load(AI_WAVES_PATH.read_text())
    raw_text = AI_WAVES_PATH.read_text()
    initial_delay_ms = getattr(game_config, "initial_wave_delay_ms", 15000.0)

    # Build ordered list of (name → era) from section headers
    name_to_era: dict[str, str] = {}
    current_era = "Stone Age"
    for line in raw_text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            upper = stripped.lstrip("#").strip().upper()
            for kw, label in ERA_KEYWORDS:
                if kw in upper:
                    current_era = label
                    break
        elif stripped.startswith("- name:"):
            name = stripped[len("- name:"):].strip().strip('"').strip("'")
            name_to_era[name] = current_era

    # Build Army objects
    result: dict[str, list[tuple[str, Army]]] = {}
    aid = 1
    for entry in (raw.get("armies") or []):
        waves_def = entry.get("waves") or []
        if not waves_def:
            continue
        name = entry.get("name", f"Army #{aid}")
        era = name_to_era.get(name, "Stone Age")

        waves = []
        for i, wd in enumerate(waves_def):
            iid = (wd.get("critter") or "").upper()
            slots = int(wd.get("slots", 1))
            waves.append(CritterWave(
                wave_id=i + 1,
                iid=iid,
                slots=slots,
                num_critters_spawned=0,
                next_critter_ms=int(i * initial_delay_ms),
            ))

        army = Army(aid=aid, uid=0, name=name, waves=waves)
        result.setdefault(era, []).append((name, army))
        aid += 1

    return result


# ── Build structures ─────────────────────────────────────────

def build_structures(hex_map: dict, items_dict: dict) -> dict[int, Structure]:
    structures = {}
    sid = 1
    for tile_key, tile_val in hex_map.items():
        tt = _tile_type(tile_val)
        if tt in NON_STRUCTURE_TYPES:
            continue
        item = items_dict.get(tt)
        if not item:
            continue
        q, r = map(int, tile_key.split(","))
        structures[sid] = Structure(
            sid=sid, iid=tt,
            position=HexCoord(q, r),
            damage=getattr(item, "damage", 1.0),
            range=getattr(item, "range", 1),
            reload_time_ms=getattr(item, "reload_time_ms", 2000.0),
            shot_speed=getattr(item, "shot_speed", 1.0),
            shot_type=getattr(item, "shot_type", "normal"),
            shot_sprite=getattr(item, "shot_sprite", ""),
            select=_tile_select(tile_val, getattr(item, "select", "first")),
            effects=getattr(item, "effects", {}),
        )
        sid += 1
    return structures


# ── Battle runner ────────────────────────────────────────────

def run_battle(svc: BattleService, battle: BattleState,
               dt_ms=15.0, max_ticks=500_000) -> None:
    for _ in range(max_ticks):
        svc.tick(battle, dt_ms)
        if battle.is_finished:
            return
    battle.is_finished = True
    battle.defender_won = True


def compute_total_critters(waves, items_dict) -> int:
    total = 0
    for w in waves:
        item = items_dict.get(w.iid)
        cost = max(1, int(getattr(item, "slots", 1) or 1)) if item else 1
        total += w.slots // cost
    return total


# ── Main ─────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Balancing simulation")
    parser.add_argument(
        "--age", metavar="ERA",
        help="Filter maps by dominant era (comma-separated substrings, case-insensitive).",
    )
    args = parser.parse_args()

    age_filters: list[str] = []
    if args.age:
        age_filters = [a.strip().lower() for a in args.age.split(",") if a.strip()]

    config = load_configuration(config_dir=CONFIG_DIR)
    items_dict = {item.iid: item for item in config.items}
    svc = BattleService(items=items_dict)
    default_life = getattr(config.game, "starting_max_life", 10.0)

    saved_maps = load_saved_maps()
    if not saved_maps:
        print("No maps found in saved_maps.yaml")
        return

    armies_by_era = load_armies_by_era(config.game)

    # Process each map
    for map_entry in saved_maps:
        map_name = map_entry["name"]
        hex_map = map_entry["hex_map"]
        era = dominant_era(hex_map)

        if not era:
            continue

        # Apply age filter
        if age_filters:
            if not any(f in era.lower() for f in age_filters):
                continue

        era_armies = armies_by_era.get(era, [])
        if not era_armies:
            continue

        normalized = {k: _tile_type(v) for k, v in hex_map.items()}
        critter_path = find_path_from_spawn_to_castle(normalized)
        if not critter_path:
            print(f"  SKIP '{map_name}' (no path)")
            continue

        structures = build_structures(hex_map, items_dict)
        map_life = float(map_entry.get("life") or default_life)

        # Count towers
        tower_count = sum(1 for v in hex_map.values() if _tile_type(v) in TOWER_ERA)

        print()
        print(f"{'=' * 70}")
        print(f"  Map: {map_name}  (era: {era}, {tower_count} towers, path={len(critter_path)}, life={map_life})")
        print(f"{'=' * 70}")

        # Table header
        col_w = 36
        res_col_w = 30
        header = f"{'Army':<{col_w}}{'Result':^{res_col_w}}"
        sep = "-" * len(header)
        print(sep)
        print(header)
        print(sep)

        for army_name, army in era_armies:
            army_copy = copy.deepcopy(army)

            defender = Empire(uid=0, name=map_name)
            defender.resources["life"] = map_life
            defender.max_life = map_life

            battle = BattleState(
                bid=0,
                defender=defender,
                attacker=Empire(uid=1, name="AI"),
                army=army_copy,
                structures=copy.deepcopy(structures),
                critter_path=critter_path,
            )

            run_battle(svc, battle)

            life_left = defender.resources.get("life", 0)
            total = compute_total_critters(army_copy.waves, items_dict)
            reached = sum(1 for rc in battle.removed_critters if rc.get("reason") == "reached")
            killed = sum(1 for rc in battle.removed_critters if rc.get("reason") == "died")

            if battle.defender_won:
                icon = "\033[32m🛡\033[0m"
            else:
                icon = "\033[31m⚔\033[0m"

            cell = f"{life_left:.0f}/{map_life:.0f} ({killed}k/{reached}r)"
            color = "\033[32m" if battle.defender_won else "\033[31m"
            reset = "\033[0m"

            print(f"{army_name:<{col_w}}{color}{cell:^{res_col_w}}{reset}")

        print(sep)


if __name__ == "__main__":
    main()
