#!/usr/bin/env python3
"""Test early-age AI armies against the four basic maps.

Runs all Stone Age and Neolithic armies from ai_waves.yaml against:
  - 1 Basic Tower
  - 1 Basic Tower (len: 3)
  - 1 Basic Tower (len: 4)
  - 2 Basic Tower (len: 4)
"""

import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent / "python_server" / "src"))

from gameserver.main import load_configuration
from gameserver.engine.battle_service import BattleService
from gameserver.engine.hex_pathfinding import find_path_from_spawn_to_castle
from gameserver.models.army import Army, CritterWave

from scripts.battle_sim import (
    build_structures,
    make_battle,
    run_battle,
    compute_total_critters,
    tile_type,
)

# ── Config ────────────────────────────────────────────────────

TARGET_MAP_NAMES = {
    "1 Basic Tower",
    "1 Basic Tower (len: 3)",
    "1 Basic Tower (len: 4)",
    "2 Basic Tower (len: 4)",
}

TARGET_SECTIONS = {"STEINZEIT", "NEOLITH"}  # substring match on section headers

CONFIG_DIR = str(Path(__file__).resolve().parent / "python_server" / "config")
SAVED_MAPS_PATH = Path(__file__).resolve().parent / "python_server" / "config" / "saved_maps.yaml"
AI_WAVES_PATH   = Path(__file__).resolve().parent / "python_server" / "config" / "ai_waves.yaml"


# ── Load target maps ──────────────────────────────────────────

def load_target_maps() -> list[dict]:
    data = yaml.safe_load(SAVED_MAPS_PATH.read_text())
    result = []
    for m in (data.get("maps") or []):
        name = m.get("name", m.get("id", "?"))
        if name not in TARGET_MAP_NAMES:
            continue
        tiles_list = m.get("hex_map") or []
        hex_map = {f"{t['q']},{t['r']}": t.get("type", "") for t in tiles_list}  # type: ignore[misc]
        result.append({
            "name": name,
            "hex_map": hex_map,
            "life": m.get("life"),
        })
    return result


# ── Load early armies ─────────────────────────────────────────

def load_early_armies(game_config) -> list[tuple[str, Army]]:
    """Return (name, Army) for all Stone Age + Neolithic entries."""
    raw = yaml.safe_load(AI_WAVES_PATH.read_text())
    initial_delay_ms = getattr(game_config, "initial_wave_delay_ms", 15000.0)

    in_target_section = False
    armies = []
    aid = 1

    for entry in (raw.get("armies") or []):
        # Army entries don't carry section info directly — we re-parse the file
        # to detect section boundaries. Instead we use the critter age from
        # the CRITTER_AGE map built in run_balancing.py logic:
        # Simpler: just collect ALL armies here and filter by critter IID era below.
        waves_def = entry.get("waves") or []
        if not waves_def:
            continue
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
        armies.append((entry.get("name", f"Army #{aid}"), Army(aid=aid, uid=0, name=entry.get("name", ""), waves=waves)))
        aid += 1

    # Filter: keep only armies whose index in ai_waves.yaml falls before BRONZEZEIT.
    # We do this by re-reading the file and collecting army names per section.
    early_names: set[str] = set()
    raw_text = AI_WAVES_PATH.read_text()
    current_early = False
    for line in raw_text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            upper = stripped.lstrip("#").strip().upper()
            # New section header
            if any(kw in upper for kw in ("STEINZEIT", "NEOLITH", "BRONZEZEIT", "EISEN",
                                           "MITTEL", "RENAIS", "INDUSTR", "MODERN", "ZUKUNFT")):
                current_early = any(kw in upper for kw in TARGET_SECTIONS)
        elif stripped.startswith("- name:") and current_early:
            name = stripped[len("- name:"):].strip().strip('"').strip("'")
            early_names.add(name)

    return [(name, army) for name, army in armies if name in early_names]


# ── Main ──────────────────────────────────────────────────────

def main():
    config = load_configuration(config_dir=CONFIG_DIR)
    items_dict = {item.iid: item for item in config.items}
    svc = BattleService(items=items_dict)
    default_life = getattr(config.game, "starting_max_life", 10.0)

    maps = load_target_maps()
    if not maps:
        print("ERROR: No target maps found.")
        sys.exit(1)

    armies = load_early_armies(config.game)
    if not armies:
        print("ERROR: No early armies found.")
        sys.exit(1)

    map_names = [m["name"] for m in maps]

    # Header
    col_w = 32
    map_col_w = 22
    header = f"{'Army':<{col_w}}" + "".join(f"{n:^{map_col_w}}" for n in map_names)
    sep    = "-" * len(header)
    print(sep)
    print(header)
    print(sep)

    # Pre-build structures + paths
    map_data = []
    for m in maps:
        normalized = {k: tile_type(v) for k, v in m["hex_map"].items()}
        path = find_path_from_spawn_to_castle(normalized)
        if not path:
            print(f"  SKIP '{m['name']}': no path")
            continue
        structures = build_structures(m["hex_map"], items_dict)
        life = float(m.get("life") or default_life)
        map_data.append({"name": m["name"], "path": path, "structures": structures, "life": life})

    for army_name, army in armies:
        row = f"{army_name:<{col_w}}"
        for md in map_data:
            battle = make_battle(army, md["structures"], md["path"], defender_life=md["life"],
                                 defender_name=md["name"])
            result = run_battle(svc, battle)

            cell_text = (
                f"🛡 {result.life_left:.0f}/{result.max_life:.0f} ({result.killed}k/{result.reached}r)"
                if result.defender_won else
                f"⚔ {result.life_left:.0f}/{result.max_life:.0f} ({result.killed}k/{result.reached}r)"
            )
            color = "\033[32m" if result.defender_won else "\033[31m"
            reset = "\033[0m"
            padded = f"{cell_text:^{map_col_w}}"
            row += f"{color}{padded}{reset}"

        print(row)

    print(sep)


if __name__ == "__main__":
    main()
