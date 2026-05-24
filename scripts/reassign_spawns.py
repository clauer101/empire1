#!/usr/bin/env python3
"""
Reassign spawn positions for all empires in a state.yaml file.

Each empire gets a fresh 3-tile starter map (castle + spawnpoint + empty)
at a new position chosen by _next_spawn_point(), respecting empire_spawn_spacing
from game.yaml.

Usage:
    python3 reassign_spawns.py data/dev/state.yaml      # dry-run preview
    python3 reassign_spawns.py data/dev/state.yaml --apply  # write changes

The original file is backed up as <file>.bak before writing.
"""

import argparse
import math
import shutil
import sys
from pathlib import Path


def _hex_dist(aq: int, ar: int, bq: int, br: int) -> int:
    return (abs(aq - bq) + abs(aq + ar - bq - br) + abs(ar - br)) // 2


def _next_spawn_point(spacing: int, existing: list[tuple[int, int]]) -> tuple[int, int]:
    """Return the nearest grid point (multiples of spacing) >= spacing from all existing."""
    radius = 0
    while True:
        pts: list[tuple[int, float, int, int]] = []
        for gq in range(-radius, radius + 1):
            for gr in range(-radius, radius + 1):
                q, r = gq * spacing, gr * spacing
                d = _hex_dist(0, 0, q, r)
                angle = math.atan2(q, -r)
                pts.append((d, angle, q, r))
        pts.sort()
        for _, _, q, r in pts:
            if all(_hex_dist(q, r, eq, er) >= spacing for eq, er in existing):
                return (q, r)
        radius += 1


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("state_file", help="Path to state.yaml (e.g. data/dev/state.yaml)")
    parser.add_argument("--apply", action="store_true", help="Write changes (default: dry-run only)")
    parser.add_argument("--spacing", type=int, default=None, help="Override empire_spawn_spacing (default: read from game.yaml)")
    args = parser.parse_args()

    try:
        import yaml
    except ImportError:
        print("ERROR: PyYAML not installed. Run: pip install pyyaml", file=sys.stderr)
        sys.exit(1)

    state_path = Path(args.state_file)
    if not state_path.exists():
        print(f"ERROR: {state_path} not found", file=sys.stderr)
        sys.exit(1)

    # Load spacing from game.yaml unless overridden
    spacing = args.spacing
    if spacing is None:
        game_yaml = Path(__file__).parent / "python_server" / "config" / "game.yaml"
        if game_yaml.exists():
            with open(game_yaml) as f:
                cfg = yaml.safe_load(f)
            spacing = cfg.get("empire_spawn_spacing", 11)
            print(f"empire_spawn_spacing from game.yaml: {spacing}")
        else:
            spacing = 11
            print(f"game.yaml not found, using default spacing: {spacing}")

    with open(state_path) as f:
        state = yaml.safe_load(f)

    empires = state.get("empires", [])
    # Skip AI (uid=0) and empires without buildings (inactive/placeholder)
    real_empires = [e for e in empires if e.get("uid", 0) != 0]

    print(f"\nFound {len(real_empires)} empires (excluding AI)\n")

    placed: list[tuple[int, int]] = []
    changes: list[dict] = []

    for empire in real_empires:
        uid = empire["uid"]
        name = empire.get("name", f"uid={uid}")

        # Find current castle position (if any)
        old_castle = None
        for tile in empire.get("hex_map", []):
            if tile.get("type") == "castle":
                old_castle = (tile["q"], tile["r"])
                break

        # Assign new spawn
        q, r = _next_spawn_point(spacing, placed)
        placed.append((q, r))

        new_map = [
            {"q": q,     "r": r,     "type": "castle"},
            {"q": q,     "r": r + 1, "type": "spawnpoint"},
            {"q": q + 1, "r": r,     "type": "empty"},
        ]

        old_str = f"({old_castle[0]}, {old_castle[1]})" if old_castle else "none"
        print(f"  uid={uid:>3}  {name:<25}  {old_str:>12}  →  ({q}, {r})")

        changes.append({"empire": empire, "new_map": new_map})

    print()

    if not args.apply:
        print("Dry-run complete. Run with --apply to write changes.")
        return

    # Backup
    backup = state_path.with_suffix(".yaml.bak")
    shutil.copy2(state_path, backup)
    print(f"Backup written to {backup}")

    # Apply
    for change in changes:
        change["empire"]["hex_map"] = change["new_map"]

    with open(state_path, "w") as f:
        yaml.dump(state, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

    print(f"Written: {state_path}")
    print("\nNext step: restart the gameserver to pick up the new state.")


if __name__ == "__main__":
    main()
