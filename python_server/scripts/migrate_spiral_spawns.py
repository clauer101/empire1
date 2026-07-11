#!/usr/bin/env python3
"""One-off migration: recompute every empire's spawn position as a clean,
deterministic hex spiral (see gameserver.models.hex.spiral_slot), and rigidly
shift each empire's entire owned map (hex_map tiles, structures, and — if
applicable — any persisted battle where this empire is the defender) so all
relative positions (e.g. already-purchased tiles) are preserved exactly,
just moved to the new origin.

Why: the previous spawn algorithm used a square-grid + distance-check search
that didn't produce a clean spiral and left some castles closer together
than the configured spacing. The new algorithm (spiral_slot) is a
closed-form index formula (the Nth empire always gets the Nth spiral slot),
so this script assigns every EXISTING empire, in original-signup order (by
uid ascending), a fresh slot 0, 1, 2, ... and shifts everything it owns by
the resulting delta.

Run against a STOPPED server only (state.yaml is edited on disk directly).
Back up state.yaml yourself before running for real:

    ./deploy.sh prod stop
    cp data/prod/state.yaml data/prod/state.yaml.backup_$(date +%Y%m%d_%H%M%S)
    .venv/bin/python python_server/scripts/migrate_spiral_spawns.py --state data/prod/state.yaml --dry-run
    .venv/bin/python python_server/scripts/migrate_spiral_spawns.py --state data/prod/state.yaml
    ./deploy.sh -f prod
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import yaml  # noqa: E402

from gameserver.models.hex import spiral_slot  # noqa: E402

SPECIAL_UIDS = {0, 100}
DEFAULT_SPACING = 10


def _castle_of(hex_map: list[dict[str, Any]]) -> tuple[int, int] | None:
    for tile in hex_map:
        if tile.get("type") == "castle":
            return tile["q"], tile["r"]
    return None


def _shift_points(points: list[dict[str, Any]], dq: int, dr: int) -> None:
    for p in points:
        p["q"] += dq
        p["r"] += dr


def _shift_structures(structures: dict[str, Any], dq: int, dr: int) -> None:
    for s in structures.values():
        pos = s.get("position")
        if pos:
            pos["q"] += dq
            pos["r"] += dr


def _shift_battles_for_defender(
    battles: list[dict[str, Any]], defender_uid: int, dq: int, dr: int
) -> None:
    for battle in battles:
        if battle.get("defender_uid") != defender_uid:
            continue
        _shift_structures(battle.get("structures", {}), dq, dr)
        _shift_points(battle.get("critter_path", []), dq, dr)
        for critter in battle.get("critters", {}).values():
            _shift_points(critter.get("path", []), dq, dr)
        for shot in battle.get("pending_shots", []):
            origin = shot.get("origin")
            if origin:
                origin["q"] += dq
                origin["r"] += dr


def migrate(state: dict[str, Any], spacing: int) -> list[tuple[int, str, tuple[int, int], tuple[int, int]]]:
    """Mutates `state` in place. Returns [(uid, name, old_castle, new_castle), ...]."""
    empires = [e for e in state.get("empires", []) if e.get("uid") not in SPECIAL_UIDS]
    empires.sort(key=lambda e: e["uid"])
    battles = state.get("battles", [])

    summary = []
    for index, empire in enumerate(empires):
        hex_map = empire.get("hex_map", [])
        old_castle = _castle_of(hex_map)
        if old_castle is None:
            continue  # no castle tile — nothing to anchor a shift to, skip
        slot = spiral_slot(index)
        new_castle = (slot.q * spacing, slot.r * spacing)
        dq, dr = new_castle[0] - old_castle[0], new_castle[1] - old_castle[1]

        if dq or dr:
            _shift_points(hex_map, dq, dr)
            _shift_structures(empire.get("structures", {}), dq, dr)
            _shift_battles_for_defender(battles, empire["uid"], dq, dr)

        summary.append((empire["uid"], empire.get("name", ""), old_castle, new_castle))
    return summary


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--state", required=True, help="Path to state.yaml to migrate")
    ap.add_argument("--spacing", type=int, default=DEFAULT_SPACING,
                    help=f"Hex spacing between spiral slots (default {DEFAULT_SPACING})")
    ap.add_argument("--dry-run", action="store_true", help="Print the plan without writing anything")
    args = ap.parse_args()

    path = Path(args.state)
    state = yaml.safe_load(path.read_text())

    summary = migrate(state, args.spacing)

    print(f"{'uid':<6}{'name':<32}{'old':<14}{'new':<14}delta")
    for uid, name, old, new in summary:
        dq, dr = new[0] - old[0], new[1] - old[1]
        print(f"{uid:<6}{name[:30]:<32}{str(old):<14}{str(new):<14}({dq:+d},{dr:+d})")
    print(f"\n{len(summary)} empires processed.")

    if args.dry_run:
        print("--dry-run: nothing written.")
        return 0

    tmp = path.with_suffix(".yaml.tmp")
    tmp.write_text(yaml.dump(state, default_flow_style=False, allow_unicode=True, sort_keys=False), encoding="utf-8")
    tmp.replace(path)
    print(f"Written: {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
