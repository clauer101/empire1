#!/usr/bin/env python3
"""Balancing test script.

Loads maps from config/saved_maps.yaml, finds matching AI armies,
runs battles to completion using synchronous tick() calls,
and writes results to balancing.md.

--age ERA  Only armies with ≥1 critter of that age vs maps with ≥1 tower of that age.
           ERA is case-insensitive substring match, e.g. "bronze", "industrial".
           Multiple eras: comma-separated, e.g. "bronze,iron".
"""

import asyncio
import argparse
import copy
import re
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

import yaml

# Add python_server/src to path
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

SAVED_MAPS_PATH = Path(__file__).resolve().parent / "python_server" / "config" / "saved_maps.yaml"

NON_STRUCTURE_TYPES = {"empty", "path", "spawnpoint", "castle", "blocked", "void", ""}

# Tower → age mapping based on sections in config/structures.yaml
TOWER_AGE: dict[str, str] = {
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

AGE_ORDER = [
    "Stone Age", "Neolithic", "Bronze Age", "Iron Age",
    "Middle Ages", "Renaissance", "Industrial", "Modern", "Future",
]

# Era keywords for parsing comment sections in critters.yaml / buildings.yaml
_CRITTER_ERA_KEYWORDS = [
    ("ZUKUNFT", "Future"),
    ("MODERN",  "Modern"),
    ("INDUSTR",  "Industrial"),
    ("RENAIS",   "Renaissance"),
    ("MITTEL",   "Middle Ages"),
    ("EISEN",    "Iron Age"),
    ("BRONZE",   "Bronze Age"),
    ("NEOLITH",  "Neolithic"),
    ("STEIN",    "Stone Age"),
]

_ITEM_ERA_KEYWORDS = [
    ("ZUKUNFT", "Future"),
    ("MODERN",  "Modern Age"),
    ("INDUSTR",  "Industrial Age"),
    ("RENAIS",   "Renaissance"),
    ("MITTEL",   "Middle Ages"),
    ("EISEN",    "Iron Age"),
    ("BRONZE",   "Bronze Age"),
    ("NEOLITH",  "Neolithic"),
    ("STEIN",    "Stone Age"),
]
_ITEM_ERA_ORDER = [
    "Stone Age", "Neolithic", "Bronze Age", "Iron Age",
    "Middle Ages", "Renaissance", "Industrial Age", "Modern Age", "Future",
]


# ── Helpers ──────────────────────────────────────────────────

def _tile_type(v) -> str:
    return v if isinstance(v, str) else v.get("type", "empty")


def _tile_select(v, item_default: str = "first") -> str:
    if isinstance(v, dict):
        return v.get("select", item_default)
    return item_default


def build_critter_age_map() -> dict[str, str]:
    """Parse critters.yaml section headers → {CRITTER_IID: era_label}."""
    cfg = Path(__file__).resolve().parent / "python_server" / "config" / "critters.yaml"
    result: dict[str, str] = {}
    current_era = "Stone Age"
    for line in cfg.read_text().splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            comment = stripped.lstrip("#").strip().upper()
            for kw, label in _CRITTER_ERA_KEYWORDS:
                if kw in comment:
                    current_era = label
                    break
        else:
            m = re.match(r"^([A-Z][A-Z_0-9]+):\s*$", line)
            if m:
                result[m.group(1)] = current_era
    return result


CRITTER_AGE: dict[str, str] = build_critter_age_map()


def build_item_era_map() -> dict[str, str]:
    """Parse buildings.yaml + knowledge.yaml → {IID: era_label}."""
    cfg = Path(__file__).resolve().parent / "python_server" / "config"
    result: dict[str, str] = {}
    for fname in ("buildings.yaml", "knowledge.yaml"):
        current_era = "Stone Age"
        for line in (cfg / fname).read_text().splitlines():
            stripped = line.strip()
            if stripped.startswith("#"):
                comment = stripped.lstrip("#").strip().upper()
                for kw, label in _ITEM_ERA_KEYWORDS:
                    if kw in comment:
                        current_era = label
                        break
            else:
                m = re.match(r"^([A-Z][A-Z_0-9]+):\s*$", line)
                if m:
                    result[m.group(1)] = current_era
    return result


def extract_army_trigger_map(
    ai_waves: list[dict],
    item_era_map: dict[str, str],
) -> dict[str, str]:
    trigger_map: dict[str, str] = {}
    for entry in ai_waves:
        name = entry.get("name", "")
        trigger = entry.get("trigger") or {}
        items = [str(i).upper() for i in (trigger.get("items") or [])]
        citizen = trigger.get("citizen")
        parts: list[str] = []
        if items:
            eras = [item_era_map.get(i, "?") for i in items]
            highest = max(eras, key=lambda e: _ITEM_ERA_ORDER.index(e) if e in _ITEM_ERA_ORDER else -1)
            parts.append(", ".join(items))
            parts.append(f" · {highest}")
        if citizen:
            parts.append(f" / citizen≥{citizen}")
        trigger_map[name] = "".join(parts) if parts else "—"
    return trigger_map


# ── Map loading ───────────────────────────────────────────────

def load_saved_maps() -> list[dict]:
    """Load maps from saved_maps.yaml.

    Returns list of dicts with keys: id, name, hex_map (dict "q,r" → type), life (optional float).
    """
    data = yaml.safe_load(SAVED_MAPS_PATH.read_text())
    result = []
    for m in (data.get("maps") or []):
        tiles_list = m.get("hex_map") or []
        hex_map = {f"{t['q']},{t['r']}": t.get("type", "") for t in tiles_list}
        result.append({
            "id": m.get("id", ""),
            "name": m.get("name", m.get("id", "?")),
            "hex_map": hex_map,
            "life": m.get("life"),
        })
    return result


def map_tower_ages(hex_map: dict) -> set[str]:
    """Return set of ages of towers present in a map."""
    ages = set()
    for tile_t in hex_map.values():
        age = TOWER_AGE.get(tile_t)
        if age:
            ages.add(age)
    return ages


def army_critter_ages(waves: list) -> set[str]:
    """Return set of critter ages present in an army."""
    return {CRITTER_AGE[w.iid] for w in waves if w.iid in CRITTER_AGE}


# ── Structure building ────────────────────────────────────────

def build_structures(tiles: dict, items_dict: dict) -> dict[int, Structure]:
    structures: dict[int, Structure] = {}
    sid = 1
    for tile_key, tile_val in tiles.items():
        tile_t = _tile_type(tile_val)
        if tile_t in NON_STRUCTURE_TYPES:
            continue
        item = items_dict.get(tile_t)
        if not item:
            continue
        q, r = map(int, tile_key.split(","))
        structures[sid] = Structure(
            sid=sid,
            iid=tile_t,
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


def tower_gold_cost(tiles: dict, items_dict: dict) -> int:
    total = 0
    for tile_val in tiles.values():
        tile_t = _tile_type(tile_val)
        if tile_t in NON_STRUCTURE_TYPES:
            continue
        item = items_dict.get(tile_t)
        if item:
            costs = getattr(item, "costs", {}) or {}
            total += int(costs.get("gold", 0))
    return total


# ── Army building ─────────────────────────────────────────────

def build_all_armies(
    ai_waves: list[dict],
    game_config,
) -> list[tuple[str, "Army", float]]:
    results = []
    aid = 1
    initial_delay_ms = getattr(game_config, "initial_wave_delay_ms", 15000.0)

    for entry in ai_waves:
        army_def = entry.get("waves") or []
        if not army_def:
            continue

        waves: list[CritterWave] = []
        for i, wave_def in enumerate(army_def):
            critter_iid = wave_def.get("critter", "")
            slots = wave_def.get("slots", 1)
            waves.append(CritterWave(
                wave_id=i + 1,
                iid=critter_iid.upper() if critter_iid else critter_iid,
                slots=int(slots),
                num_critters_spawned=0,
                next_critter_ms=int(i * initial_delay_ms),
            ))

        name = entry.get("name", f"Army #{aid}")
        travel_s = float(entry.get("travel_time", 0) or 0) or getattr(
            game_config, "ai_travel_seconds", 30.0
        )
        army = Army(aid=aid, uid=0, name=name, waves=waves)
        results.append((name, army, travel_s))
        aid += 1

    return results


# ── Battle ────────────────────────────────────────────────────

@dataclass
class BattleResult:
    army_name: str
    defender_won: bool
    elapsed_s: float
    defender_life_remaining: float
    defender_life_max: float
    total_critter_slots: int
    critters_reached: int
    critters_killed: int
    critters_spawned: int
    army_total_critters: int
    num_waves: int
    num_structures: int
    wall_time_ms: float
    army_waves: list = field(default_factory=list)


def compute_army_total_critters(waves: list, items_dict: dict) -> int:
    total = 0
    for wave in waves:
        item = items_dict.get(wave.iid)
        slot_cost = getattr(item, "slots", 1) if item else 1
        if slot_cost <= 0:
            slot_cost = 1
        total += wave.slots // slot_cost
    return total


def run_battle_sync(
    battle_service: BattleService,
    battle: BattleState,
    dt_ms: float = 15.0,
    max_ticks: int = 2_000_000,
    max_life: float | None = None,
) -> None:
    had_critters = False
    for _ in range(max_ticks):
        battle_service.tick(battle, dt_ms)
        if battle.is_finished:
            return
        if max_life is not None:
            now_has_critters = len(battle.critters) > 0
            if had_critters and not now_has_critters and battle.defender:
                battle.defender.resources["life"] = max_life
            had_critters = now_has_critters
    battle.is_finished = True
    battle.defender_won = True


# ── Reporting helpers ─────────────────────────────────────────

def min_age_index(waves: list) -> int:
    idx = len(AGE_ORDER) - 1
    for wave in waves:
        age = CRITTER_AGE.get(wave.iid, "Future")
        i = AGE_ORDER.index(age) if age in AGE_ORDER else len(AGE_ORDER) - 1
        if i < idx:
            idx = i
    return idx


def critter_age_distribution(waves: list, items_dict: dict) -> str:
    counts: dict[str, int] = {}
    for wave in waves:
        age = CRITTER_AGE.get(wave.iid, "Unknown")
        item = items_dict.get(wave.iid)
        slot_cost = getattr(item, "slots", 1) if item else 1
        if slot_cost <= 0:
            slot_cost = 1
        counts[age] = counts.get(age, 0) + (wave.slots // slot_cost)
    total = sum(counts.values())
    if not total:
        return ""
    parts = sorted(counts.items(), key=lambda x: -x[1])
    return ", ".join(f"{round(s * 100 / total)}% {age}" for age, s in parts)


def _html_color(text: str, color: str) -> str:
    return f'<span style="color:{color};font-weight:bold">{text}</span>'


def _result_cell(r: "BattleResult | None") -> str:
    if r is None:
        return "—"
    life_str = f"{r.defender_life_remaining:.0f}/{r.defender_life_max:.0f}"
    spawn_str = f"{r.critters_spawned}/{r.army_total_critters}"
    if r.defender_won:
        icon = "🛡"
        color = "#2ea043"
    else:
        icon = "⚔"
        color = "#f85149"
    return _html_color(f"{life_str} {icon} {spawn_str}", color)


def write_balancing_report(
    path: Path,
    army_names: list[str],
    map_labels: list[str],
    results: dict[str, dict[str, BattleResult]],  # results[map_name][army_name]
    army_waves_map: dict[str, list] | None = None,
    map_gold: dict[str, int] | None = None,
    army_trigger_map: dict[str, str] | None = None,
    items_dict: dict | None = None,
):
    lines = []
    lines.append("# Balancing Report\n")
    lines.append(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")

    total_battles = sum(len(v) for v in results.values())
    total_def_wins = sum(1 for v in results.values() for r in v.values() if r.defender_won)
    total_att_wins = total_battles - total_def_wins
    lines.append(
        f"**Total battles:** {total_battles} | "
        f"**Defender wins:** {_html_color(str(total_def_wins), '#2ea043')} | "
        f"**Attacker wins:** {_html_color(str(total_att_wins), '#f85149')}\n"
    )

    def _table_header() -> list[str]:
        h = "| # | Army | Trigger | Waves | Slots | Composition |"
        s = "|---|------|---------|-------|-------|-------------|"
        gold_row = "| | **Tower gold cost** | | | | |"
        for label in map_labels:
            h += f" {label} |"
            s += "---|"
            gold_row += f" 💰 {(map_gold or {}).get(label, 0):,} |"
        return [h, s, gold_row]

    current_section_idx = -1
    seen = set()
    row_num = 0
    for army_name in army_names:
        if army_name in seen:
            continue
        seen.add(army_name)

        # Check if this army has any results at all
        has_results = any(results.get(ml, {}).get(army_name) for ml in map_labels)
        if not has_results:
            continue

        row_num += 1
        source_waves = (army_waves_map or {}).get(army_name, [])
        waves_str = str(len(source_waves)) if source_waves else "—"
        slots_str = str(sum(w.slots for w in source_waves)) if source_waves else "—"
        composition = critter_age_distribution(source_waves, items_dict or {}) if source_waves else ""

        army_min_idx = min_age_index(source_waves) if source_waves else 0
        if army_min_idx > current_section_idx:
            current_section_idx = army_min_idx
            section_label = AGE_ORDER[current_section_idx]
            lines.append(f"\n## {section_label} Armies\n")
            lines.extend(_table_header())

        trigger_str = (army_trigger_map or {}).get(army_name, "—")
        row = f"| {row_num} | {army_name} | {trigger_str} | {waves_str} | {slots_str} | {composition} |"
        for label in map_labels:
            r = results.get(label, {}).get(army_name)
            row += f" {_result_cell(r)} |"
        lines.append(row)

    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


# ── Main ──────────────────────────────────────────────────────

async def main():
    parser = argparse.ArgumentParser(description="Balancing simulation")
    parser.add_argument(
        "--age",
        metavar="ERA",
        help=(
            "Filter armies AND maps by age (comma-separated substrings, case-insensitive). "
            "e.g. 'bronze' → armies with ≥1 Bronze Age critter vs maps with ≥1 Bronze Age tower."
        ),
    )
    args = parser.parse_args()

    age_filters: list[str] = []
    if args.age:
        age_filters = [a.strip().lower() for a in args.age.split(",") if a.strip()]

    config_dir = str(Path(__file__).resolve().parent / "python_server" / "config")
    config = load_configuration(config_dir=config_dir)
    items_dict = {item.iid: item for item in config.items}
    battle_service = BattleService(items=items_dict)
    max_life = getattr(config.game, "starting_max_life", 10.0)

    all_armies = build_all_armies(config.ai_waves, config.game)
    army_waves_map = {name: list(army.waves) for name, army, _ in all_armies}
    item_era_map = build_item_era_map()
    army_trigger_map = extract_army_trigger_map(config.ai_waves, item_era_map)

    # Load maps
    saved_maps = load_saved_maps()
    if not saved_maps:
        print("No maps found in saved_maps.yaml")
        return

    # Filter maps by age
    if age_filters:
        def map_matches(m: dict) -> bool:
            ages = map_tower_ages(m["hex_map"])
            return any(
                any(f in age.lower() for f in age_filters)
                for age in ages
            )
        active_maps = [m for m in saved_maps if map_matches(m)]
    else:
        active_maps = saved_maps

    if not active_maps:
        print(f"No maps matched age filter '{args.age}'.")
        return

    # Filter armies by age
    if age_filters:
        def army_matches(waves: list) -> bool:
            ages = army_critter_ages(waves)
            return any(
                any(f in age.lower() for f in age_filters)
                for age in ages
            )
        active_armies = [(name, army, t) for name, army, t in all_armies
                         if army_matches(army_waves_map.get(name, army.waves))]
    else:
        active_armies = all_armies

    if not active_armies:
        print(f"No armies matched age filter '{args.age}'.")
        return

    print(f"Maps: {[m['name'] for m in active_maps]}")
    print(f"Armies: {len(active_armies)}")

    # results[map_name][army_name] = BattleResult
    results_by_map: dict[str, dict[str, BattleResult]] = {}
    map_gold: dict[str, int] = {}
    map_labels: list[str] = []

    for map_entry in active_maps:
        map_name = map_entry["name"]
        hex_map = map_entry["hex_map"]

        normalized = {k: _tile_type(v) for k, v in hex_map.items()}
        critter_path = find_path_from_spawn_to_castle(normalized)
        if not critter_path:
            print(f"  SKIP '{map_name}' (no path from spawn to castle)")
            continue

        structures = build_structures(hex_map, items_dict)
        gold = tower_gold_cost(hex_map, items_dict)
        map_life = float(map_entry.get("life") or max_life)
        print(f"\n{'='*60}")
        print(f"  Map: {map_name}  ({len(structures)} towers, {gold:,} gold, path={len(critter_path)}, life={map_life})")
        print(f"{'='*60}")

        map_labels.append(map_name)
        map_gold[map_name] = gold
        fixture_results: dict[str, BattleResult] = {}

        for army_name, army, _travel_s in active_armies:
            total_slots = sum(w.slots for w in army.waves)
            army_copy = copy.deepcopy(army)

            defender = Empire(uid=0, name=map_name)
            defender.resources["life"] = map_life
            defender.max_life = map_life

            attacker = Empire(uid=0, name="AI")

            battle = BattleState(
                bid=0,
                defender=defender,
                attacker=attacker,
                army=army_copy,
                structures=copy.deepcopy(structures),
                critter_path=critter_path,
            )

            t0 = time.monotonic()
            run_battle_sync(battle_service, battle, max_life=map_life)
            wall_ms = (time.monotonic() - t0) * 1000

            critters_reached = sum(
                1 for rc in battle.removed_critters if rc.get("reason") == "reached"
            )
            critters_killed = sum(
                1 for rc in battle.removed_critters if rc.get("reason") == "died"
            )
            critters_spawned = critters_reached + critters_killed
            army_total_critters = compute_army_total_critters(army_copy.waves, items_dict)

            result = BattleResult(
                army_name=army_name,
                defender_won=battle.defender_won or False,
                elapsed_s=battle.elapsed_ms / 1000.0,
                defender_life_remaining=defender.resources.get("life", 0),
                defender_life_max=map_life,
                total_critter_slots=total_slots,
                critters_reached=critters_reached,
                critters_killed=critters_killed,
                critters_spawned=critters_spawned,
                army_total_critters=army_total_critters,
                num_waves=len(army_copy.waves),
                num_structures=len(structures),
                wall_time_ms=wall_ms,
                army_waves=army_copy.waves,
            )
            fixture_results[army_name] = result

            outcome = "DEFENDER ✓" if result.defender_won else "ATTACKER ✓"
            print(f"    → {army_name}: {outcome}  life={result.defender_life_remaining:.1f}/{max_life:.1f}  spawned={critters_spawned}/{army_total_critters}")

        results_by_map[map_name] = fixture_results

    out_path = Path(__file__).resolve().parent / "balancing.md"
    army_names = [name for name, _, _ in all_armies]
    write_balancing_report(
        out_path, army_names, map_labels, results_by_map,
        army_waves_map, map_gold, army_trigger_map, items_dict,
    )
    print(f"\n✓ Report written to {out_path}")


if __name__ == "__main__":
    asyncio.run(main())
