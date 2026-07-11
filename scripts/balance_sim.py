#!/usr/bin/env python3
"""balance_sim.py — Systematic critter/tower balancing simulation.

Attacks curated player mazes (`python_server/config/saved_maps.yaml`) with
era-appropriate armies — both the hardcoded `ai_waves.yaml` armies and random
armies from the AI army generator — and reports win rates, per-critter reach
rates, and per-tower damage/kill shares. Flags critters/towers that look
overpowered (OP) or underpowered (UP) relative to their era's mean.

All simulations use base item stats (no per-empire item_upgrades applied) —
this measures config balance, not player investment.

Usage:
    python3 scripts/balance_sim.py --list-maps
    python3 scripts/balance_sim.py --era bronze --n 20
    python3 scripts/balance_sim.py --era all --n 20 --seed 42
    python3 scripts/balance_sim.py --quick
"""

from __future__ import annotations

import argparse
import csv
import statistics
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "python_server" / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from gameserver.engine.battle_service import BattleService
from gameserver.main import load_configuration
from gameserver.util.eras import ERA_ORDER, ERA_LABELS_EN
from gameserver.util.maze_loader import Maze, build_era_maze_pool, coverage_report

from scripts.army_pool import AttackingArmy, build_hardcoded_pool, generate_random_army
from scripts.battle_sim import build_structures, compute_total_critters, make_battle, run_battle

REPO_ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = REPO_ROOT / "python_server" / "config"

# OP/UP thresholds — see report for the exact numbers that trigger a flag.
MIN_CRITTER_SAMPLE = 30       # spawned count floor before judging a critter's reach rate
CRITTER_OP_SIGMA = 2.0        # reach_rate > era_mean + this many std-devs
MIN_TOWER_PLACEMENTS = 5      # placement count floor before judging a tower's damage share
TOWER_OP_RATIO = 2.0          # damage_share / placement_share >= this → OP
TOWER_UP_RATIO = 0.5          # damage_share / placement_share <= this → UP


@dataclass
class BattleRecord:
    era: str
    maze_name: str
    maze_source: str
    army_name: str
    army_kind: str
    army_seed: int | None
    defender_won: bool
    life_left: float
    max_life: float
    killed: int
    reached: int
    total_critters: int
    duration_ms: float
    reached_iids: list[str]  # critter iids that reached the castle, one entry per critter
    army_waves_str: str  # "IID×slots, IID×slots, ..." — this army's full wave composition
    army_era_slots: dict[str, float]  # era -> slot count, i.e. this army's own critter-era composition


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--era", default="all", help="Single era key (e.g. 'bronze') or 'all' (default).")
    p.add_argument("--n", type=int, default=20, help="Random armies per maze (default: 20).")
    p.add_argument("--seed", type=int, default=None, help="Master seed for reproducible random armies.")
    p.add_argument("--out", type=Path, default=None, help="Output directory (default: data/balancing/<timestamp>/).")
    p.add_argument("--list-maps", action="store_true", help="Print per-era maze coverage and exit.")
    p.add_argument("--quick", action="store_true", help="Fast smoke run: n=5, max 2 mazes per era.")
    return p.parse_args()


def _army_era_slots(waves, items_dict: dict[str, Any]) -> dict[str, float]:
    """Slot-weighted era composition of an army: {era: slot_count}."""
    slots_by_era: dict[str, float] = defaultdict(float)
    for w in waves:
        item = items_dict.get(w.iid)
        era = getattr(item, "era", None) if item else None
        slots_by_era[era or "?"] += float(w.slots)
    return dict(slots_by_era)


def _format_army_waves(waves) -> str:
    """'LEGIONARY×14, PIKENEER×12, ...' — full wave composition, one entry per wave."""
    return ", ".join(f"{w.iid}×{w.slots:.0f}" for w in waves)


def _battles_for_era(
    era: str,
    mazes: list[Maze],
    hardcoded_armies: list[AttackingArmy],
    n_random: int,
    max_mazes: int | None,
    master_seed: int | None,
    svc: BattleService,
    items_dict: dict[str, Any],
    ai_generator_cfg: dict[str, Any],
) -> list[BattleRecord]:
    records: list[BattleRecord] = []
    mazes_to_run = mazes[:max_mazes] if max_mazes else mazes
    total_battles = len(mazes_to_run) * (len(hardcoded_armies) + n_random)

    with tqdm(total=total_battles, desc=f"{era:<11}", unit="battle", leave=False) as bar:
        for maze in mazes_to_run:
            structures = build_structures(maze.hex_map, items_dict)

            attacking_armies: list[AttackingArmy] = list(hardcoded_armies)
            for i in range(n_random):
                seed = (master_seed * 10_000 + i) if master_seed is not None else None
                attacking_armies.append(
                    generate_random_army(era, ai_generator_cfg, seed=seed if seed is not None else i, aid=i + 1)
                )

            for attacker in attacking_armies:
                battle = make_battle(attacker.army, structures, maze.path, defender_life=maze.life)
                result = run_battle(svc, battle)
                reached_iids = [
                    iid for iid, s in result.critter_stats.items() for _ in range(int(s["reached"]))
                ]
                records.append(BattleRecord(
                    era=era,
                    maze_name=maze.name,
                    maze_source=maze.source,
                    army_name=attacker.name,
                    army_kind=attacker.kind,
                    army_seed=attacker.seed,
                    defender_won=result.defender_won,
                    life_left=result.life_left,
                    max_life=result.max_life,
                    killed=result.killed,
                    reached=result.reached,
                    total_critters=compute_total_critters(attacker.army.waves, items_dict),
                    duration_ms=result.duration_ms,
                    reached_iids=reached_iids,
                    army_waves_str=_format_army_waves(attacker.army.waves),
                    army_era_slots=_army_era_slots(attacker.army.waves, items_dict),
                ))
                _accumulate_stats(era, maze, attacker, result, items_dict)
                bar.update(1)

    return records


# ── Aggregation (module-level accumulators reset per run) ────────────────────

_critter_stats: dict[str, dict[str, dict[str, float]]] = {}  # era -> iid -> {spawned, killed, reached, castle_damage}
_tower_stats: dict[str, dict[str, dict[str, float]]] = {}    # era -> iid -> {damage, kills, placements}


def _reset_stats() -> None:
    _critter_stats.clear()
    _tower_stats.clear()


def _accumulate_stats(era: str, maze: Maze, attacker: AttackingArmy, result, items_dict: dict[str, Any]) -> None:
    critter_bucket = _critter_stats.setdefault(era, {})
    for iid, s in result.critter_stats.items():
        agg = critter_bucket.setdefault(iid, {"spawned": 0, "killed": 0, "reached": 0, "castle_damage": 0.0})
        agg["spawned"] += s["spawned"]
        agg["killed"] += s["killed"]
        agg["reached"] += s["reached"]
        agg["castle_damage"] += s["castle_damage"]

    tower_bucket = _tower_stats.setdefault(era, {})
    for iid in _maze_tower_counts(maze):
        agg = tower_bucket.setdefault(iid, {"damage": 0.0, "kills": 0, "placements": 0})
        agg["placements"] += 1  # counted once per battle the tower participated in
    for iid, dmg in result.tower_damage_by_iid.items():
        agg = tower_bucket.setdefault(iid, {"damage": 0.0, "kills": 0, "placements": 0})
        agg["damage"] += dmg
    for iid, kills in result.tower_kills_by_iid.items():
        agg = tower_bucket.setdefault(iid, {"damage": 0.0, "kills": 0, "placements": 0})
        agg["kills"] += kills


def _maze_tower_counts(maze: Maze) -> Counter[str]:
    """Count placed towers by iid on this maze (already-normalized hex_map)."""
    from scripts.battle_sim import NON_STRUCTURE_TYPES, tile_type
    return Counter(
        tt for tv in maze.hex_map.values()
        if (tt := tile_type(tv)) not in NON_STRUCTURE_TYPES
    )


def _format_tower_list(tower_counts: Counter[str]) -> str:
    """'HEAVY_TOWER×5, ARROW_TOWER×3, ...' summary of a maze's placed towers."""
    if not tower_counts:
        return ""
    return ", ".join(f"{iid}×{n}" for iid, n in sorted(tower_counts.items(), key=lambda kv: -kv[1]))


# ── OP/UP detection ──────────────────────────────────────────────────────────

def _flag_critters(era: str, item_era_index: dict[str, int]) -> tuple[list[str], list[str]]:
    bucket = _critter_stats.get(era, {})
    reach_rates = {}
    for iid, s in bucket.items():
        if item_era_index.get(iid) is None or ERA_ORDER[item_era_index[iid]] != era:
            continue  # only judge critters native to this era's pool
        if s["spawned"] < MIN_CRITTER_SAMPLE:
            continue
        reach_rates[iid] = s["reached"] / s["spawned"]
    if len(reach_rates) < 2:
        return [], []
    mean = statistics.mean(reach_rates.values())
    stdev = statistics.pstdev(reach_rates.values()) or 0.0001
    op, up = [], []
    for iid, rate in reach_rates.items():
        if rate > mean + CRITTER_OP_SIGMA * stdev:
            op.append(f"{iid} (reach_rate={rate:.1%}, era_mean={mean:.1%})")
        elif mean > 0.02 and rate < 0.005:
            up.append(f"{iid} (reach_rate={rate:.1%}, era_mean={mean:.1%})")
    return op, up


def _flag_towers(era: str) -> tuple[list[str], list[str]]:
    bucket = _tower_stats.get(era, {})
    eligible = {iid: s for iid, s in bucket.items() if s["placements"] >= MIN_TOWER_PLACEMENTS}
    total_damage = sum(s["damage"] for s in eligible.values())
    total_placements = sum(s["placements"] for s in eligible.values())
    if not eligible or total_damage <= 0 or total_placements <= 0:
        return [], []
    op, up = [], []
    for iid, s in eligible.items():
        damage_share = s["damage"] / total_damage
        placement_share = s["placements"] / total_placements
        ratio = damage_share / placement_share if placement_share > 0 else 0.0
        if ratio >= TOWER_OP_RATIO:
            op.append(f"{iid} (damage_share={damage_share:.1%} vs placement_share={placement_share:.1%}, ratio={ratio:.2f})")
        elif ratio <= TOWER_UP_RATIO:
            up.append(f"{iid} (damage_share={damage_share:.1%} vs placement_share={placement_share:.1%}, ratio={ratio:.2f})")
    return op, up


# ── Output ────────────────────────────────────────────────────────────────────

def _life_icon(life_left: float, max_life: float) -> str:
    """5-step color gradient for remaining defender life."""
    pct = life_left / max_life if max_life else 0.0
    if pct <= 0:
        return "⬛"
    if pct < 0.2:
        return "🔴"
    if pct < 0.5:
        return "🟠"
    if pct < 0.8:
        return "🟡"
    return "🟢"


def _format_reached(reached_iids: list[str]) -> str:
    """'CRUSADER×3, HANDGUNNER×1' style summary, empty string if nothing reached."""
    if not reached_iids:
        return ""
    counts = Counter(reached_iids)
    return ", ".join(f"{iid}×{n}" for iid, n in sorted(counts.items(), key=lambda kv: -kv[1]))


def _format_era_slots(era_slots: dict[str, float]) -> str:
    """'Iron 80%, Bronze 20%' style summary of an army's own critter-era mix."""
    total = sum(era_slots.values())
    if not total:
        return ""
    return ", ".join(
        f"{ERA_LABELS_EN.get(e, e)} {100 * s / total:.0f}%"
        for e, s in sorted(era_slots.items(), key=lambda kv: -kv[1])
    )


def write_battles_csv(path: Path, records: list[BattleRecord]) -> None:
    with path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "era", "maze_name", "maze_source", "army_name", "army_kind", "army_seed",
            "defender_won", "life_left", "max_life", "killed", "reached", "total_critters", "duration_ms",
            "reached_iids", "army_era_slots", "army_waves",
        ])
        for r in records:
            era_slots_str = "|".join(f"{e}:{s:.0f}" for e, s in sorted(r.army_era_slots.items(), key=lambda kv: -kv[1]))
            writer.writerow([
                r.era, r.maze_name, r.maze_source, r.army_name, r.army_kind, r.army_seed,
                r.defender_won, f"{r.life_left:.2f}", f"{r.max_life:.2f}", r.killed, r.reached,
                r.total_critters, f"{r.duration_ms:.0f}", "|".join(r.reached_iids), era_slots_str,
                r.army_waves_str,
            ])


def write_critters_csv(path: Path) -> None:
    with path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["era", "iid", "spawned", "killed", "reached", "reach_rate", "castle_damage"])
        for era in ERA_ORDER:
            for iid, s in sorted(_critter_stats.get(era, {}).items()):
                rate = s["reached"] / s["spawned"] if s["spawned"] else 0.0
                writer.writerow([era, iid, int(s["spawned"]), int(s["killed"]), int(s["reached"]),
                                  f"{rate:.4f}", f"{s['castle_damage']:.1f}"])


def write_towers_csv(path: Path) -> None:
    with path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["era", "iid", "damage", "kills", "placements", "damage_per_placement"])
        for era in ERA_ORDER:
            for iid, s in sorted(_tower_stats.get(era, {}).items()):
                dpp = s["damage"] / s["placements"] if s["placements"] else 0.0
                writer.writerow([era, iid, f"{s['damage']:.1f}", int(s["kills"]), int(s["placements"]), f"{dpp:.2f}"])


def write_report(path: Path, pool: dict[str, list[Maze]], records: list[BattleRecord], item_era_index: dict[str, int]) -> None:
    lines: list[str] = ["# Balancing Report", "", f"Generated: {datetime.now(timezone.utc).isoformat()}", ""]

    lines.append("## Maze Coverage")
    lines.append("")
    lines.append("```")
    lines.append(coverage_report(pool))
    lines.append("```")
    lines.append("")

    lines.append("## Win Rates")
    lines.append("")
    lines.append("| Era | Battles | Defender Win % | Hardcoded Win % | Random Win % |")
    lines.append("|---|---:|---:|---:|---:|")
    by_era: dict[str, list[BattleRecord]] = defaultdict(list)
    for r in records:
        by_era[r.era].append(r)
    for era in ERA_ORDER:
        rs = by_era.get(era, [])
        if not rs:
            continue
        total = len(rs)
        win_pct = 100 * sum(1 for r in rs if r.defender_won) / total
        hard = [r for r in rs if r.army_kind == "hardcoded"]
        rand = [r for r in rs if r.army_kind == "random"]
        hard_pct = 100 * sum(1 for r in hard if r.defender_won) / len(hard) if hard else float("nan")
        rand_pct = 100 * sum(1 for r in rand if r.defender_won) / len(rand) if rand else float("nan")
        lines.append(f"| {ERA_LABELS_EN[era]} | {total} | {win_pct:.0f}% | {hard_pct:.0f}% | {rand_pct:.0f}% |")
    lines.append("")

    maze_by_name = {m.name: m for mazes in pool.values() for m in mazes}

    lines.append("## Battle-by-Battle Overview")
    lines.append("")
    lines.append("🟩 defender won · 🟥 defender lost. Life % uses a 5-step gradient")
    lines.append("(🟢 ≥80% · 🟡 ≥50% · 🟠 ≥20% · 🔴 >0% · ⬛ 0%). \"Reached\" lists the")
    lines.append("critter types that made it to the castle (× count), blank if none.")
    lines.append("One table per map, with that map's own tower-era distribution.")
    lines.append("")
    for era in ERA_ORDER:
        rs = by_era.get(era, [])
        if not rs:
            continue
        lines.append(f"### {ERA_LABELS_EN[era]}")
        lines.append("")

        by_maze: dict[str, list[BattleRecord]] = defaultdict(list)
        for r in rs:
            by_maze[r.maze_name].append(r)

        for maze_name, maze_rs in by_maze.items():
            maze = maze_by_name.get(maze_name)
            lines.append(f"#### {maze_name}")
            lines.append("")
            if maze is not None and maze.era_counts:
                total_towers = sum(maze.era_counts.values())
                dist = ", ".join(
                    f"{ERA_LABELS_EN.get(e, e)} {100 * c / total_towers:.0f}% ({c})"
                    for e, c in sorted(maze.era_counts.items(), key=lambda kv: -kv[1])
                )
                lines.append(f"| Tower Era Distribution ({total_towers} towers) | Towers |")
                lines.append("|---|---|")
                lines.append(f"| {dist} | {_format_tower_list(_maze_tower_counts(maze))} |")
            else:
                lines.append("Tower era distribution: unavailable")
            lines.append("")
            lines.append("| Result | Army | Kind | Army Critter Eras | Life Left | Reached | Killed (army waves) |")
            lines.append("|---|---|---|---|---|---|---|")
            for r in maze_rs:
                result_icon = "🟩" if r.defender_won else "🟥"
                life_icon = _life_icon(r.life_left, r.max_life)
                life_pct = 100 * r.life_left / r.max_life if r.max_life else 0.0
                reached_str = _format_reached(r.reached_iids)
                army_eras_str = _format_era_slots(r.army_era_slots)
                lines.append(
                    f"| {result_icon} | {r.army_name} | {r.army_kind} | {army_eras_str} | "
                    f"{life_icon} {r.life_left:.0f}/{r.max_life:.0f} ({life_pct:.0f}%) | {reached_str} | {r.army_waves_str} |"
                )
            lines.append("")

    lines.append("## Flagged Critters/Towers")
    lines.append("")
    any_flag = False
    for era in ERA_ORDER:
        if era not in by_era:
            continue
        c_op, c_up = _flag_critters(era, item_era_index)
        t_op, t_up = _flag_towers(era)
        if not (c_op or c_up or t_op or t_up):
            continue
        any_flag = True
        lines.append(f"### {ERA_LABELS_EN[era]}")
        if c_op:
            lines.append("- **Critters OP (reach rate far above era mean):** " + "; ".join(c_op))
        if c_up:
            lines.append("- **Critters UP (rarely reach the castle):** " + "; ".join(c_up))
        if t_op:
            lines.append("- **Towers OP (damage share far above placement share):** " + "; ".join(t_op))
        if t_up:
            lines.append("- **Towers UP (damage share far below placement share):** " + "; ".join(t_up))
        lines.append("")
    if not any_flag:
        lines.append("No critters or towers crossed the OP/UP thresholds in this run.")
        lines.append("")

    path.write_text("\n".join(lines))


def main() -> None:
    args = parse_args()

    config = load_configuration(config_dir=str(CONFIG_DIR))
    items_dict = {item.iid: item for item in config.items}
    item_era_index = config.item_era_index

    pool = build_era_maze_pool(item_era_index)

    if args.list_maps:
        print(coverage_report(pool))
        return

    eras = ERA_ORDER if args.era == "all" else [args.era]
    for era in eras:
        if era not in ERA_ORDER:
            print(f"ERROR: unknown era '{era}'. Choose from: {', '.join(ERA_ORDER)}")
            sys.exit(1)

    n_random = 5 if args.quick else args.n
    max_mazes = 2 if args.quick else None

    svc = BattleService(items=items_dict)
    hardcoded_pool = build_hardcoded_pool(config.ai_waves, item_era_index, config.game.initial_wave_delay_ms)

    _reset_stats()
    all_records: list[BattleRecord] = []
    for era in tqdm(eras, desc="Overall", unit="era"):
        mazes = pool.get(era, [])
        if not mazes:
            tqdm.write(f"[{era}] no maze available — skipping")
            continue
        hardcoded = hardcoded_pool.get(era, [])
        tqdm.write(f"[{era}] {len(mazes[:max_mazes] if max_mazes else mazes)} mazes × "
                   f"({len(hardcoded)} hardcoded + {n_random} random) armies")
        records = _battles_for_era(
            era, mazes, hardcoded, n_random, max_mazes, args.seed, svc, items_dict, config.game.ai_generator,
        )
        all_records.extend(records)

    if not all_records:
        print("No battles were simulated (no maze coverage for the requested era(s)).")
        return

    out_dir = args.out or (REPO_ROOT / "data" / "balancing" / datetime.now().strftime("%Y%m%d_%H%M%S"))
    out_dir.mkdir(parents=True, exist_ok=True)

    write_battles_csv(out_dir / "battles.csv", all_records)
    write_critters_csv(out_dir / "critters.csv")
    write_towers_csv(out_dir / "towers.csv")
    write_report(out_dir / "report.md", pool, all_records, item_era_index)

    print(f"\n{len(all_records)} battles simulated. Results written to {out_dir}")


if __name__ == "__main__":
    main()
