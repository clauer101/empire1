#!/usr/bin/env python3
"""One-off migration: reposition every empire's owned map so its center of
gravity (the centroid of its hex_map tiles) sits on a clean, deterministic
hex spiral (see gameserver.models.hex.spiral_slot), spaced `--spacing` hexes
apart from its neighbors. All relative positions (owned tiles, structures,
already-purchased upgrades) are preserved exactly — only shifted.

Unlike migrate_spiral_spawns.py (which anchors on the castle tile), this
anchors on each empire's centroid, so empires that have expanded lopsidedly
away from their castle still end up a plausible distance from their
neighbors' actual footprint, not just from their castle.

Run against a STOPPED server only (state.yaml is edited on disk directly).
Back up state.yaml yourself before running for real:

    ./deploy.sh dev stop
    cp data/dev/state.yaml data/dev/state.yaml.backup_$(date +%Y%m%d_%H%M%S)
    .venv/bin/python python_server/scripts/reposition_empires_centroid.py --state data/dev/state.yaml --dry-run
    .venv/bin/python python_server/scripts/reposition_empires_centroid.py --state data/dev/state.yaml
    ./deploy.sh -f dev
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import yaml  # noqa: E402

from gameserver.models.hex import HexCoord, spiral_slot  # noqa: E402

SPECIAL_UIDS = {0, 100}
DEFAULT_SPACING = 9


def _centroid_of(hex_map: list[dict[str, Any]]) -> tuple[int, int] | None:
    """Cube-rounded centroid of an empire's owned tiles, or None if empty."""
    if not hex_map:
        return None
    fq = sum(t["q"] for t in hex_map) / len(hex_map)
    fr = sum(t["r"] for t in hex_map) / len(hex_map)
    return _cube_round(fq, fr)


def _cube_round(fq: float, fr: float) -> tuple[int, int]:
    fs = -fq - fr
    q, r, s = round(fq), round(fr), round(fs)
    q_diff, r_diff, s_diff = abs(q - fq), abs(r - fr), abs(s - fs)
    if q_diff > r_diff and q_diff > s_diff:
        q = -r - s
    elif r_diff > s_diff:
        r = -q - s
    return q, r


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
    """Mutates `state` in place. Returns [(uid, name, old_centroid, new_centroid), ...]."""
    empires = [e for e in state.get("empires", []) if e.get("uid") not in SPECIAL_UIDS]
    empires.sort(key=lambda e: e["uid"])
    battles = state.get("battles", [])

    summary = []
    for index, empire in enumerate(empires):
        hex_map = empire.get("hex_map", [])
        old_centroid = _centroid_of(hex_map)
        if old_centroid is None:
            continue  # no owned tiles — nothing to anchor a shift to, skip
        slot = spiral_slot(index)
        new_centroid = (slot.q * spacing, slot.r * spacing)
        dq, dr = new_centroid[0] - old_centroid[0], new_centroid[1] - old_centroid[1]

        if dq or dr:
            _shift_points(hex_map, dq, dr)
            _shift_structures(empire.get("structures", {}), dq, dr)
            _shift_battles_for_defender(battles, empire["uid"], dq, dr)

        summary.append((empire["uid"], empire.get("name", ""), old_centroid, new_centroid))
    return summary


def _min_pairwise_distance(centroids: list[tuple[int, int]]) -> int | None:
    if len(centroids) < 2:
        return None
    best = None
    for i, (aq, ar) in enumerate(centroids):
        for bq, br in centroids[i + 1:]:
            d = HexCoord(aq, ar).distance_to(HexCoord(bq, br))
            best = d if best is None else min(best, d)
    return best


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

    print(f"{'uid':<6}{'name':<32}{'old centroid':<16}{'new centroid':<16}delta")
    for uid, name, old, new in summary:
        dq, dr = new[0] - old[0], new[1] - old[1]
        print(f"{uid:<6}{name[:30]:<32}{str(old):<16}{str(new):<16}({dq:+d},{dr:+d})")
    print(f"\n{len(summary)} empires processed.")

    min_dist = _min_pairwise_distance([new for _, _, _, new in summary])
    if min_dist is not None:
        print(f"Minimum pairwise centroid distance: {min_dist} hex (spacing={args.spacing})")

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
