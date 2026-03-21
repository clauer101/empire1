#!/usr/bin/env python3
"""Balancing test script.

Loads each state fixture, finds all matching AI armies,
runs battles to completion using synchronous tick() calls,
and writes results to balancing.md.
"""

import asyncio
import argparse
import copy
import re
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

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
from gameserver.persistence.state_load import load_state


# ── Helpers ──────────────────────────────────────────────────

def _tile_type(v) -> str:
    return v if isinstance(v, str) else v.get("type", "empty")


def _tile_select(v, item_default: str = "first") -> str:
    if isinstance(v, dict):
        return v.get("select", item_default)
    return item_default


NON_STRUCTURE_TYPES = {"empty", "path", "spawnpoint", "castle", "blocked", "void"}

# Era ordering for items (buildings / knowledge)
_ITEM_ERA_KEYWORDS = [
    ("ZUKUNFT",         "Future"),
    ("MODERN",          "Modern Age"),
    ("INDUSTR",         "Industrial Age"),
    ("RENAIS",          "Renaissance"),
    ("MITTEL",          "Middle Ages"),
    ("EISEN",           "Iron Age"),
    ("BRONZE",          "Bronze Age"),
    ("NEOLITH",         "Neolithic"),
    ("STEIN",           "Stone Age"),
]
_ITEM_ERA_ORDER = [
    "Stone Age", "Neolithic", "Bronze Age", "Iron Age",
    "Middle Ages", "Renaissance", "Industrial Age", "Modern Age", "Future",
]


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
    """Return {army_name: 'ITEM1, ITEM2 · Era'} for each army."""
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


def build_structures(tiles: dict, items_dict: dict) -> dict[int, Structure]:
    """Build Structure objects from hex_map tiles, mirroring handlers.py logic."""
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


def get_completed_items(empire: Empire) -> set[str]:
    """Return set of IIDs with effort == 0.0 (completed)."""
    completed = set()
    for iid, effort in getattr(empire, "buildings", {}).items():
        if effort == 0.0:
            completed.add(iid.upper())
    for iid, effort in getattr(empire, "knowledge", {}).items():
        if effort == 0.0:
            completed.add(iid.upper())
    return completed


def build_all_armies(
    ai_waves: list[dict],
    game_config,
) -> list[tuple[str, "Army", float]]:
    """Build Army objects for ALL entries in ai_waves.yaml.

    Returns list of (army_name, Army, travel_time) tuples.
    """
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
    critters_spawned: int        # reached + killed (actually entered the field)
    army_total_critters: int     # theoretical max critters the army could send
    num_waves: int
    num_structures: int
    wall_time_ms: float
    army_waves: list = field(default_factory=list)  # CritterWave list for composition


def compute_army_total_critters(waves: list, items_dict: dict) -> int:
    """Compute theoretical max critters the army could spawn across all waves.

    Each wave's capacity = floor(wave.slots / critter_slot_cost).
    critter_slot_cost is taken from the critter item definition (item.slots).
    """
    total = 0
    for wave in waves:
        item = items_dict.get(wave.iid)
        slot_cost = getattr(item, "slots", 1) if item else 1
        if slot_cost <= 0:
            slot_cost = 1
        total += wave.slots // slot_cost
    return total


def compute_max_life(
    empire: Empire,
    items_dict: dict,
    starting_max_life: float = 10.0,
) -> float:
    """Compute max_life from completed buildings/knowledge effects."""
    total_modifier = 0.0
    for iid, remaining in {**empire.buildings, **empire.knowledge}.items():
        if remaining <= 0:
            item = items_dict.get(iid)
            if item:
                effects = getattr(item, "effects", {}) or {}
                total_modifier += effects.get("max_life_modifier", 0.0)
    return starting_max_life + total_modifier


def run_battle_sync(
    battle_service: BattleService,
    battle: BattleState,
    dt_ms: float = 15.0,
    max_ticks: int = 2_000_000,
    max_life: float | None = None,
) -> None:
    """Run battle ticks synchronously until finished or max_ticks exceeded.

    If *max_life* is given, the defender's life is reset to that value
    whenever a wave clears (all active critters gone), so each wave
    starts the defender at full health.
    """
    had_critters = False
    for _ in range(max_ticks):
        battle_service.tick(battle, dt_ms)
        if battle.is_finished:
            return
        if max_life is not None:
            now_has_critters = len(battle.critters) > 0
            # Critters just all cleared → reset life for the next wave
            if had_critters and not now_has_critters and battle.defender:
                battle.defender.resources["life"] = max_life
            had_critters = now_has_critters
    # Force-finish if we hit max ticks
    battle.is_finished = True
    battle.defender_won = True


# ── Main ─────────────────────────────────────────────────────

FIXTURE_DIR = Path(__file__).resolve().parent / "python_server" / "tests" / "fixtures" / "states"

# Era keywords used to parse section comments in critters.yaml / buildings.yaml
_CRITTER_ERA_KEYWORDS = [
    ("ZUKUNFT",   "Future"),
    ("MODERN",    "Modern"),
    ("INDUSTR",   "Industrial"),
    ("RENAIS",    "Renaissance"),
    ("MITTEL",    "Middle Ages"),
    ("EISEN",     "Iron Age"),
    ("BRONZE",    "Bronze Age"),
    ("NEOLITH",   "Neolithic"),
    ("STEIN",     "Stone Age"),
]


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


AGE_ORDER = [
    "Stone Age", "Neolithic", "Bronze Age", "Iron Age",
    "Middle Ages", "Renaissance", "Industrial", "Modern", "Future",
]


def min_age_index(waves: list) -> int:
    """Return the index of the earliest (weakest) age present among the army's critters."""
    idx = len(AGE_ORDER) - 1
    for wave in waves:
        age = CRITTER_AGE.get(wave.iid, "Future")
        i = AGE_ORDER.index(age) if age in AGE_ORDER else len(AGE_ORDER) - 1
        if i < idx:
            idx = i
    return idx


def tower_gold_cost(tiles: dict, items_dict: dict) -> int:
    """Sum gold costs of all tower tiles in a hex_map."""
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


def critter_age_distribution(waves: list) -> str:
    """Return a compact age-distribution string, e.g. '70% Iron Age, 30% Bronze Age'."""
    counts: dict[str, int] = {}
    for wave in waves:
        age = CRITTER_AGE.get(wave.iid, "Unknown")
        counts[age] = counts.get(age, 0) + wave.slots
    total = sum(counts.values())
    if not total:
        return ""
    parts = sorted(counts.items(), key=lambda x: -x[1])
    return ", ".join(f"{round(s * 100 / total)}% {age}" for age, s in parts)

FIXTURE_META = {
    "state_all_bronze.yaml": "Bronze Age",
    "state_all_iron.yaml": "Iron Age",
    "state_all_middle_ages.yaml": "Middle Ages",
    "state_all_renaissance.yaml": "Renaissance",
    "state_all_industial.yaml": "Industrial",
    "state_all_moden.yaml": "Modern",
}


async def main():
    parser = argparse.ArgumentParser(description="Balancing simulation")
    parser.add_argument(
        "--age",
        metavar="ERA",
        help="Only simulate these eras (comma-separated, e.g. industrial,modern). Case-insensitive.",
    )
    args = parser.parse_args()

    config_dir = str(Path(__file__).resolve().parent / "python_server" / "config")
    config = load_configuration(config_dir=config_dir)
    items_dict = {item.iid: item for item in config.items}
    battle_service = BattleService(items=items_dict)

    # Build army list once (same for all state files)
    all_armies = build_all_armies(config.ai_waves, config.game)
    army_names = [name for name, _, _ in all_armies]
    # Store original waves (before battle mutates them) for composition analysis
    army_waves_map = {name: list(army.waves) for name, army, _ in all_armies}
    item_era_map = build_item_era_map()
    army_trigger_map = extract_army_trigger_map(config.ai_waves, item_era_map)

    # results[fixture_label][army_name] = BattleResult
    results_by_fixture: dict[str, dict[str, BattleResult]] = {}
    fixture_labels: list[str] = []
    fixture_gold: dict[str, int] = {}  # gold cost of towers per fixture

    # Filter fixtures by --age if provided
    active_fixtures = FIXTURE_META
    if args.age:
        age_filters = [a.strip().lower() for a in args.age.split(",") if a.strip()]
        active_fixtures = {
            k: v for k, v in FIXTURE_META.items()
            if any(f in v.lower() for f in age_filters)
        }
        if not active_fixtures:
            known = ", ".join(FIXTURE_META.values())
            print(f"Unknown age '{args.age}'. Known: {known}")
            return

    for fixture_name, era_label in active_fixtures.items():
        fixture_path = FIXTURE_DIR / fixture_name
        if not fixture_path.exists():
            print(f"  SKIP {fixture_name} (not found)")
            continue

        print(f"\n{'='*60}")
        print(f"  {era_label} — {fixture_name}")
        print(f"{'='*60}")

        restored = await load_state(str(fixture_path))
        if not restored or not restored.empires:
            print("  SKIP (no empires)")
            continue

        # Find the first player empire (lowest uid > 0, not AI)
        player_empires = sorted(
            ((uid, emp) for uid, emp in restored.empires.items() if uid not in (0, 100)),
            key=lambda x: x[0],
        )
        if not player_empires:
            print("  SKIP (no player empires)")
            continue

        uid, empire = player_empires[0]
        completed = get_completed_items(empire)
        print(f"\n  Empire uid={uid} '{empire.name}' — {len(completed)} completed items")

        tiles = empire.hex_map if isinstance(empire.hex_map, dict) else {}
        if not tiles:
            print(f"    SKIP (no hex_map)")
            continue

        normalized = {k: _tile_type(v) for k, v in tiles.items()}
        critter_path = find_path_from_spawn_to_castle(normalized)
        if not critter_path:
            print(f"    SKIP (no path from spawn to castle)")
            continue

        structures = build_structures(tiles, items_dict)
        gold = tower_gold_cost(tiles, items_dict)
        print(f"    Path length: {len(critter_path)}, Structures: {len(structures)}, Tower cost: {gold:,} gold")
        print(f"    Armies to simulate: {len(all_armies)}")

        fixture_results: dict[str, BattleResult] = {}

        def _army_has_era(waves: list, era: str) -> bool:
            """Return True if any wave in the army contains critters of *era*."""
            return any(CRITTER_AGE.get(w.iid) == era for w in waves)

        for army_name, army, travel_s in all_armies:
            # Only simulate armies that contain at least one wave from the fixture era
            if era_label in AGE_ORDER:
                waves = army_waves_map.get(army_name, army.waves)
                if not _army_has_era(waves, era_label):
                    continue

            total_slots = sum(w.slots for w in army.waves)
            army_copy = copy.deepcopy(army)

            defender_copy = copy.deepcopy(empire)
            max_life = compute_max_life(
                empire, items_dict, getattr(config.game, "starting_max_life", 10.0)
            )
            defender_copy.max_life = max_life
            defender_copy.resources["life"] = max_life

            attacker = Empire(uid=0, name="AI")

            battle = BattleState(
                bid=0,
                defender=defender_copy,
                attacker=attacker,
                army=army_copy,
                structures=copy.deepcopy(structures),
                critter_path=critter_path,
            )

            t0 = time.monotonic()
            run_battle_sync(battle_service, battle, max_life=max_life)
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
                defender_life_remaining=defender_copy.resources.get("life", 0),
                defender_life_max=max_life,
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

        fixture_labels.append(era_label)
        results_by_fixture[era_label] = fixture_results
        fixture_gold[era_label] = gold

    # ── Write balancing.md ────────────────────────────────────
    out_path = Path(__file__).resolve().parent / "balancing.md"
    write_balancing_report(out_path, army_names, fixture_labels, results_by_fixture, army_waves_map, fixture_gold, army_trigger_map)
    print(f"\n✓ Report written to {out_path}")


def _html_color(text: str, color: str) -> str:
    return f'<span style="color:{color};font-weight:bold">{text}</span>'


def _result_cell(r: BattleResult | None) -> str:
    """Format a single result cell with color-coded outcome."""
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
    fixture_labels: list[str],
    results_by_fixture: dict[str, dict[str, BattleResult]],
    army_waves_map: dict[str, list] | None = None,
    fixture_gold: dict[str, int] | None = None,
    army_trigger_map: dict[str, str] | None = None,
):
    lines = []
    lines.append("# Balancing Report\n")
    lines.append(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")

    total_battles = sum(len(v) for v in results_by_fixture.values())
    total_def_wins = sum(
        1 for v in results_by_fixture.values() for r in v.values() if r.defender_won
    )
    total_att_wins = total_battles - total_def_wins
    lines.append(
        f"**Total battles:** {total_battles} | "
        f"**Defender wins:** {_html_color(str(total_def_wins), '#2ea043')} | "
        f"**Attacker wins:** {_html_color(str(total_att_wins), '#f85149')}\n"
    )

    def _table_header() -> list[str]:
        gold_cells = " | ".join(
            f"💰 {(fixture_gold or {}).get(lbl, 0):,}" for lbl in fixture_labels
        )
        h = "| # | Army | Trigger | Waves | Slots | Composition |"
        s = "|---|------|---------|-------|-------|-------------|"
        for label in fixture_labels:
            h += f" {label} |"
            s += "---|"
        gold_row = f"| | **Tower gold cost** | | | | | {gold_cells} |"
        return [h, s, gold_row]

    current_section_idx = -1

    # One row per army
    seen = set()
    row_num = 0
    for army_name in army_names:
        if army_name in seen:
            continue
        seen.add(army_name)
        row_num += 1

        # Get wave/slot info from any fixture that has this army
        waves_str = ""
        slots_str = ""
        composition = ""
        source_waves = (army_waves_map or {}).get(army_name, [])
        for label in fixture_labels:
            r = results_by_fixture.get(label, {}).get(army_name)
            if r:
                waves_str = str(r.num_waves)
                slots_str = str(r.total_critter_slots)
                if not source_waves and r.army_waves:
                    source_waves = r.army_waves
                break
        composition = critter_age_distribution(source_waves) if source_waves else ""

        # Insert section break when the army's minimum critter age advances
        army_min_idx = min_age_index(source_waves) if source_waves else 0
        if army_min_idx > current_section_idx:
            current_section_idx = army_min_idx
            section_label = AGE_ORDER[current_section_idx]
            lines.append(f"\n## {section_label} Armies\n")
            hdr = _table_header()
            lines.extend(hdr)

        trigger_str = (army_trigger_map or {}).get(army_name, "—")
        row = f"| {row_num} | {army_name} | {trigger_str} | {waves_str} | {slots_str} | {composition} |"
        for label in fixture_labels:
            r = results_by_fixture.get(label, {}).get(army_name)
            row += f" {_result_cell(r)} |"
        lines.append(row)

    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    asyncio.run(main())
