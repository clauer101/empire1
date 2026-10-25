#!/usr/bin/env python3
"""sim_random_maze.py — Battle auto-generated random mazes against random armies.

Both sides of the battle are generated fresh per trial: the maze via
`gameserver.engine.maze_generator.MazeGenerator` (corridor length drawn from
game.yaml's per-era `maze_length` range — see `scripts/maze_pool.py`), and the
attacking army via the AI army generator behind the "Random Army" button in
`web/tools/send-ai-army.html` (`gameserver.util.army_generator`, wrapped by
`scripts/army_pool.py`). Combat itself runs on the same headless battle engine
as `scripts/sim_map.py` / `scripts/balance_sim.py` (`scripts/battle_sim.py`) —
no running server needed.

This is the auto-generation counterpart to `sim_map.py` (one curated map) and
`balance_sim.py` (a curated map pool): both the maze AND the army are random
here, so it measures how well auto-generated mazes hold up rather than how a
specific hand-built map performs. `--tower-type`/`--critter-type` narrow
either side to one class for counter-matchup testing; `--matrix` sweeps every
class pairing for an era in one shot. See the `balancing` skill
(`.claude/skills/balancing/SKILL.md`) for a guided walkthrough.

Usage:
    python3 scripts/sim_random_maze.py --era bronze --n 20
    python3 scripts/sim_random_maze.py --era all --n 10 --seed 42
    python3 scripts/sim_random_maze.py --list-classes --era bronze
    python3 scripts/sim_random_maze.py --era bronze --tower-type fast --critter-type tank --n 20
    python3 scripts/sim_random_maze.py --matrix --era bronze --n 10
    python3 scripts/sim_random_maze.py --era bronze --army-era iron --n 10
    python3 scripts/sim_random_maze.py --era bronze --length 12 --n 10
"""

from __future__ import annotations

import argparse
import statistics
import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "python_server" / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from gameserver.engine.battle_service import BattleService
from gameserver.engine.empire_service import EmpireService
from gameserver.engine.upgrade_provider import UpgradeProvider
from gameserver.main import load_configuration
from gameserver.models.items import ItemDetails, ItemType
from gameserver.util.eras import ERA_LABELS_EN, ERA_ORDER
from gameserver.util.events import EventBus

from scripts.army_pool import generate_random_army
from scripts.battle_sim import build_structures, make_battle, run_battle
from scripts.maze_pool import generate_random_maze

REPO_ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = REPO_ROOT / "python_server" / "config"
if not CONFIG_DIR.exists():
    CONFIG_DIR = REPO_ROOT / "config"

ARMY_COL = 32
MAZE_COL = 14
RESULT_COL = 26


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--era", default="all", help="Single era key (e.g. 'bronze') or 'all' (default).")
    p.add_argument("--n", type=int, default=10, help="Battles per era/pairing (default: 10).")
    p.add_argument("--seed", type=int, default=None, help="Master seed for reproducible mazes+armies.")
    p.add_argument("--top-n", type=int, default=2,
                   help="MazeGenerator weighted-pick pool size — higher varies maze shape more (default: 2).")
    p.add_argument("--tower-type", default=None,
                   help="Restrict the maze's towers to one tower_type (e.g. 'fast'). See --list-classes.")
    p.add_argument("--critter-type", default=None,
                   help="Restrict the army's critters to one critter_type (e.g. 'tank'). See --list-classes.")
    p.add_argument("--army-era", default=None,
                   help="Attacker era, if different from --era (the maze/defender era). Defaults to --era — "
                        "set this for cross-era stress tests.")
    p.add_argument("--length", type=int, default=None,
                   help="Force an exact maze corridor length instead of a random draw from game.yaml's "
                        "per-era maze_length range.")
    p.add_argument("--list-classes", action="store_true",
                   help="Print available tower_type/critter_type per era and exit — no battles run.")
    p.add_argument("--matrix", action="store_true",
                   help="Run every tower_type x critter_type pairing for --era (must be a single era, not "
                        "'all') and print a win-rate grid.")
    return p.parse_args()


@dataclass
class BattleStats:
    wins: int = 0
    losses: int = 0
    life_pcts: list[float] = field(default_factory=list)

    @property
    def total(self) -> int:
        return self.wins + self.losses

    @property
    def win_pct(self) -> float:
        return 100 * self.wins / self.total if self.total else 0.0

    @property
    def avg_life_pct(self) -> float:
        return statistics.mean(self.life_pcts) if self.life_pcts else 0.0


def available_tower_types(items_dict: dict[str, ItemDetails], era: str) -> list[str]:
    """Tower types usable in a maze for `era` — cumulative through the era
    (mirrors `maze_generator.era_filtered_structures`: a maze can place any
    unlocked-by-era tower, not just ones introduced exactly at `era`)."""
    era_index = ERA_ORDER.index(era)
    return sorted({
        it.tower_type for it in items_dict.values()
        if it.item_type == ItemType.STRUCTURE and it.tower_type
        and it.era in ERA_ORDER and ERA_ORDER.index(it.era) <= era_index
    })


def available_critter_types(items_dict: dict[str, ItemDetails], era: str) -> list[str]:
    """Critter types native to `era`'s own pool (NOT cumulative — an army's
    main critter pool is exactly its own era; only a configured, small
    prev/next-era slice mixes in — see `generate_army`)."""
    return sorted({
        it.critter_type for it in items_dict.values()
        if it.item_type == ItemType.CRITTER and it.critter_type and it.era == era
    })


def run_battles(
    era: str, n: int, top_n: int, seed_base: int | None,
    config, items_dict: dict[str, ItemDetails], empire_service: EmpireService, svc: BattleService, *,
    army_era: str | None = None, tower_type: str | None = None,
    critter_type: str | None = None, length: int | None = None,
    print_rows: bool = False,
) -> BattleStats:
    """Run `n` fresh-maze-vs-fresh-army battles and return aggregate stats.

    Raises ValueError (from `generate_random_maze`/`generate_random_army`) if
    `tower_type`/`critter_type` has no matching item for the requested era —
    callers decide whether that means "skip this era" or "abort".
    """
    stats = BattleStats()
    attacker_era = army_era or era
    for i in range(n):
        maze_seed = (seed_base * 10_000 + i) if seed_base is not None \
            else (hash((era, tower_type, "maze", i)) & 0xFFFFFFFF)
        army_seed = (seed_base * 10_000 + i) if seed_base is not None \
            else (hash((attacker_era, critter_type, "army", i)) & 0xFFFFFFFF)

        maze = generate_random_maze(era, empire_service, items_dict, config.game, seed=maze_seed,
                                    top_n=top_n, tower_type=tower_type, target_length=length)
        structures = build_structures(maze.hex_map, items_dict)
        attacker = generate_random_army(attacker_era, config.game.ai_generator, seed=army_seed,
                                        aid=i + 1, critter_type=critter_type)

        battle = make_battle(attacker.army, structures, maze.path, defender_life=maze.life)
        result = run_battle(svc, battle)
        life_pct = 100 * result.life_left / result.max_life if result.max_life else 0.0
        stats.life_pcts.append(life_pct)

        if result.defender_won:
            stats.wins += 1
            icon, color = "🛡", "\033[32m"
        else:
            stats.losses += 1
            icon, color = "⚔", "\033[31m"

        if print_rows:
            maze_cell = f"{maze.tower_count}t/{len(maze.path)}len"
            result_cell = f"{icon} {result.life_left:.0f}/{result.max_life:.0f}  ({result.killed}k / {result.reached}r)"
            print(f"{i + 1:<4}{attacker.name:<{ARMY_COL}}{maze_cell:<{MAZE_COL}}{color}{result_cell}\033[0m")

    return stats


def run_era(
    era: str, n: int, top_n: int, seed: int | None,
    config, items_dict: dict[str, ItemDetails], empire_service: EmpireService, svc: BattleService, *,
    army_era: str | None = None, tower_type: str | None = None, critter_type: str | None = None,
    length: int | None = None,
) -> BattleStats:
    label_bits = [f"Era: {ERA_LABELS_EN.get(era, era)}"]
    if army_era and army_era != era:
        label_bits.append(f"Army era: {ERA_LABELS_EN.get(army_era, army_era)}")
    if tower_type:
        label_bits.append(f"Tower: {tower_type}")
    if critter_type:
        label_bits.append(f"Critter: {critter_type}")
    if length:
        label_bits.append(f"Length: {length}")
    label_bits.append(f"N={n}")
    title = "  |  ".join(label_bits)
    sep = "─" * (4 + ARMY_COL + MAZE_COL + RESULT_COL)
    print()
    print(title)
    print(sep)
    print(f"{'#':<4}{'Army':<{ARMY_COL}}{'Maze':<{MAZE_COL}}{'Result':<{RESULT_COL}}")
    print(sep)

    stats = run_battles(era, n, top_n, seed, config, items_dict, empire_service, svc,
                        army_era=army_era, tower_type=tower_type, critter_type=critter_type,
                        length=length, print_rows=True)

    print(sep)
    print(f"{'Defender wins:':<{4 + ARMY_COL + MAZE_COL}}{stats.wins}/{stats.total}  "
          f"({stats.win_pct:.0f}%)  avg life left: {stats.avg_life_pct:.0f}%")
    return stats


def run_matrix(
    era: str, n: int, top_n: int, seed: int | None,
    config, items_dict: dict[str, ItemDetails], empire_service: EmpireService, svc: BattleService,
) -> None:
    tower_types = available_tower_types(items_dict, era)
    critter_types = available_critter_types(items_dict, era)
    if not tower_types or not critter_types:
        print(f"ERROR: era {era!r} has nothing to matrix "
              f"(tower_types={tower_types}, critter_types={critter_types}) — try --list-classes.")
        sys.exit(1)

    col_w = 16
    row_label_w = 16
    print()
    print(f"Counter matrix — {ERA_LABELS_EN.get(era, era)}  |  N={n} trials per pairing  "
          f"(cell = defender win% (avg life% left))")
    header = f"{'Tower \\ Critter':<{row_label_w}}" + "".join(f"{c:<{col_w}}" for c in critter_types)
    print(header)
    print("-" * len(header))
    for tt in tower_types:
        row = f"{tt:<{row_label_w}}"
        for ct in critter_types:
            stats = run_battles(era, n, top_n, seed, config, items_dict, empire_service, svc,
                                tower_type=tt, critter_type=ct, print_rows=False)
            cell = f"{stats.win_pct:.0f}% ({stats.avg_life_pct:.0f}%)"
            row += f"{cell:<{col_w}}"
        print(row)
    print()


def list_classes(items_dict: dict[str, ItemDetails], eras: list[str]) -> None:
    print()
    print("tower_type is cumulative (a maze may use any tower unlocked up to its era);")
    print("critter_type is native-only (an army's main pool is exactly its own era).")
    print()
    for era in eras:
        towers = available_tower_types(items_dict, era)
        critters = available_critter_types(items_dict, era)
        print(f"{ERA_LABELS_EN.get(era, era):<12} tower_types:   {', '.join(towers) or '—'}")
        print(f"{'':<12} critter_types: {', '.join(critters) or '—'}")


def main() -> None:
    args = parse_args()

    eras = ERA_ORDER if args.era == "all" else [args.era]
    for era in eras:
        if era not in ERA_ORDER:
            print(f"ERROR: unknown era '{era}'. Choose from: {', '.join(ERA_ORDER)}")
            sys.exit(1)
    if args.army_era and args.army_era not in ERA_ORDER:
        print(f"ERROR: unknown --army-era '{args.army_era}'. Choose from: {', '.join(ERA_ORDER)}")
        sys.exit(1)
    if args.matrix and args.era == "all":
        print("ERROR: --matrix requires a single --era (not 'all') to bound runtime.")
        sys.exit(1)

    config = load_configuration(config_dir=str(CONFIG_DIR))
    items_dict = {item.iid: item for item in config.items}

    if args.list_classes:
        list_classes(items_dict, eras)
        return

    upgrade_provider = UpgradeProvider()
    upgrade_provider.load(config.items)
    empire_service = EmpireService(
        upgrade_provider, EventBus(),
        game_config=config.game, item_era_index=config.item_era_index,
    )
    svc = BattleService(items=items_dict)
    top_n = max(1, min(5, args.top_n))

    if args.matrix:
        run_matrix(eras[0], args.n, top_n, args.seed, config, items_dict, empire_service, svc)
        return

    overall_wins = overall_losses = 0
    for era in eras:
        try:
            stats = run_era(era, args.n, top_n, args.seed, config, items_dict, empire_service, svc,
                            army_era=args.army_era, tower_type=args.tower_type,
                            critter_type=args.critter_type, length=args.length)
        except ValueError as exc:
            if len(eras) > 1:
                print(f"[{era}] skipped: {exc}")
                continue
            print(f"ERROR: {exc}")
            sys.exit(1)
        overall_wins += stats.wins
        overall_losses += stats.losses

    if len(eras) > 1:
        total = overall_wins + overall_losses
        win_pct = 100 * overall_wins / total if total else 0
        print()
        print(f"Overall defender wins: {overall_wins}/{total}  ({win_pct:.0f}%)")
    print()


if __name__ == "__main__":
    main()
