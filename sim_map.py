#!/usr/bin/env python3
"""sim_map.py — Simulate N random era armies against a saved map.

Usage:
    python3 sim_map.py <map_name> <era> <n>

Arguments:
    map_name   Name of the map from saved_maps.yaml (e.g. "2 Basic Tower (len: 4)")
    era        Era name, case-insensitive prefix match:
                 steinzeit | neolithikum | bronzezeit | eisenzeit |
                 mittelalter | renaissance | industrialisierung | moderne | zukunft
    n          Number of battles to simulate (armies drawn randomly with replacement)

Examples:
    python3 sim_map.py "2 Basic Tower (len: 4)" steinzeit 20
    python3 sim_map.py "default" mittelalter 10
"""

import json
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent / "python_server" / "src"))

from gameserver.main import load_configuration
from gameserver.engine.battle_service import BattleService
from gameserver.engine.hex_pathfinding import find_path_from_spawn_to_castle
from gameserver.models.army import Army, CritterWave
from gameserver.util.army_generator import (
    generate_army,
    parse_critter_era_groups,
    parse_slot_by_iid,
    ERA_BACKEND_TO_INTERNAL,
)

from battle_sim import build_structures, make_battle, run_battle, tile_type

# ── Paths ─────────────────────────────────────────────────────────────────────

CONFIG_DIR      = Path(__file__).resolve().parent / "python_server" / "config"
SAVED_MAPS_PATH = CONFIG_DIR / "saved_maps.yaml"
CRITTERS_PATH   = CONFIG_DIR / "critters.yaml"

# Maps era CLI arg → backend era key
ERA_KEYWORDS = {
    "steinzeit":          "STEINZEIT",
    "neolithikum":        "NEOLITHIKUM",
    "bronzezeit":         "BRONZEZEIT",
    "eisenzeit":          "EISENZEIT",
    "mittelalter":        "MITTELALTER",
    "renaissance":        "RENAISSANCE",
    "industrialisierung": "INDUSTRIALISIERUNG",
    "moderne":            "MODERNE",
    "zukunft":            "ZUKUNFT",
}


# ── Loaders ───────────────────────────────────────────────────────────────────

def load_map(name: str) -> dict:
    """Load a single map by name from saved_maps.yaml."""
    data = yaml.safe_load(SAVED_MAPS_PATH.read_text())
    for m in (data.get("maps") or []):
        mname = m.get("name", m.get("id", ""))
        if mname == name:
            tiles_list = m.get("hex_map") or []
            hex_map = {f"{t['q']},{t['r']}": t.get("type", "") for t in tiles_list}
            return {"name": mname, "hex_map": hex_map, "life": m.get("life")}
    available = [m.get("name", m.get("id", "?")) for m in (data.get("maps") or [])]
    print(f"ERROR: Map '{name}' not found.\nAvailable maps:")
    for n in available:
        print(f"  - {n}")
    sys.exit(1)


def make_army(era_internal: str, game_config, aid: int) -> tuple[str, Army]:
    """Generate one random army via the AI army generator."""
    ai_cfg           = getattr(game_config, "ai_generator", {}) or {}
    critter_groups   = parse_critter_era_groups(CRITTERS_PATH)
    slot_by_iid      = parse_slot_by_iid(CRITTERS_PATH)
    initial_delay_ms = getattr(game_config, "initial_wave_delay_ms", 15000.0)

    result = generate_army(era_internal, ai_cfg, critter_groups, slot_by_iid)
    aname  = result["name"]
    waves  = [
        CritterWave(
            wave_id=i + 1,
            iid=wd["critter"].upper(),
            slots=int(wd["slots"]),
            num_critters_spawned=0,
            next_critter_ms=int(i * initial_delay_ms),
        )
        for i, wd in enumerate(result["waves"])
    ]
    return aname, Army(aid=aid, uid=0, name=aname, waves=waves)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 4:
        print(__doc__)
        sys.exit(1)

    map_name = sys.argv[1]
    era_arg  = sys.argv[2].lower()
    try:
        n = int(sys.argv[3])
    except ValueError:
        print(f"ERROR: N must be an integer, got '{sys.argv[3]}'")
        sys.exit(1)

    # Optional output file for SSE streaming (argv[4])
    out_path = sys.argv[4] if len(sys.argv) > 4 else None
    out_fp   = open(out_path, "w", buffering=1) if out_path else None

    def emit(obj):
        """Write a JSON line to the output file (if any)."""
        if out_fp:
            out_fp.write(json.dumps(obj) + "\n")
            out_fp.flush()

    # Resolve era
    era_key = next((v for k, v in ERA_KEYWORDS.items() if k.startswith(era_arg)), None)
    if not era_key:
        print(f"ERROR: Unknown era '{sys.argv[2]}'.\nChoose from: {', '.join(ERA_KEYWORDS)}")
        sys.exit(1)
    era_internal = ERA_BACKEND_TO_INTERNAL.get(era_key)
    if not era_internal:
        print(f"ERROR: No internal era mapping for '{era_key}'.")
        sys.exit(1)

    # Load config
    config     = load_configuration(config_dir=str(CONFIG_DIR))
    items_dict = {item.iid: item for item in config.items}
    svc        = BattleService(items=items_dict)
    default_life = getattr(config.game, "starting_max_life", 10.0)

    # Load map
    m           = load_map(map_name)
    normalized  = {k: tile_type(v) for k, v in m["hex_map"].items()}
    path        = find_path_from_spawn_to_castle(normalized)
    if not path:
        print(f"ERROR: No valid path found in map '{map_name}'.")
        sys.exit(1)
    structures  = build_structures(m["hex_map"], items_dict)
    life        = float(m.get("life") or default_life)

    # Header
    army_col  = 36
    result_col = 28
    title = f"Map: {map_name}  |  Era: {era_key}  |  N={n}"
    sep   = "─" * (army_col + result_col)

    print()
    print(title)
    print(sep)
    print(f"{'#':<4}{'Army':<{army_col}}{'Result':<{result_col}}")
    print(sep)

    wins = losses = 0

    for i in range(n):
        army_name, army = make_army(era_internal, config.game, aid=i + 1)
        battle = make_battle(army, structures, path, defender_life=life)
        result = run_battle(svc, battle)

        if result.defender_won:
            wins += 1
            icon  = "🛡"
            color = "\033[32m"
        else:
            losses += 1
            icon  = "⚔"
            color = "\033[31m"

        cell = f"{icon} {result.life_left:.0f}/{result.max_life:.0f}  ({result.killed}k / {result.reached}r)"
        line = f"{i+1:<4}{army_name:<{army_col}}{cell}"
        print(f"{i+1:<4}{army_name:<{army_col}}{color}{cell}\033[0m")
        emit(line)

    print(sep)
    total = wins + losses
    win_pct = 100 * wins / total if total else 0
    print(f"{'Defender wins:':<{army_col + 4}}{wins}/{total}  ({win_pct:.0f}%)")
    print()
    emit("__DONE__")
    if out_fp:
        out_fp.close()


if __name__ == "__main__":
    main()
