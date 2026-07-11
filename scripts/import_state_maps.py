#!/usr/bin/env python3
"""
Import empire hex maps from a state.yaml file into python_server/config/saved_maps.yaml.

Lists all non-AI empires with a populated hex_map found in the given state.yaml
and appends the selected ones as curated saved maps (same format the balance
tuner and the map-overview admin tool read from).

Usage:
    python3 scripts/import_state_maps.py data/dev/state.yaml               # list only
    python3 scripts/import_state_maps.py data/dev/state.yaml --uid 34      # import one
    python3 scripts/import_state_maps.py data/dev/state.yaml --uid 34 --uid 12
    python3 scripts/import_state_maps.py data/dev/state.yaml --all         # import all
    python3 scripts/import_state_maps.py data/dev/state.yaml --all --name-prefix "dev season3"
"""

import argparse
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SAVED_MAPS_PATH = REPO_ROOT / "python_server" / "config" / "saved_maps.yaml"


def _load_saved_maps(path: Path) -> list[dict]:
    import yaml
    if not path.exists():
        return []
    data = yaml.safe_load(path.read_text()) or {}
    return data.get("maps") or []


def _write_saved_maps(path: Path, maps: list[dict]) -> None:
    import yaml
    path.write_text(yaml.dump({"maps": maps}, allow_unicode=True, default_flow_style=False, sort_keys=False))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("state_file", help="Path to state.yaml (e.g. data/dev/state.yaml)")
    parser.add_argument("--uid", type=int, action="append", default=[], help="Import only this empire uid (repeatable)")
    parser.add_argument("--all", action="store_true", help="Import every empire with a hex_map")
    parser.add_argument("--name-prefix", default="", help="Prefix added to each imported map's name")
    parser.add_argument("--env", default=None, help="Label used in the generated map id (default: inferred from state_file's parent dir name)")
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

    env = args.env or state_path.resolve().parent.name  # e.g. "dev" / "prod"

    with open(state_path) as f:
        state = yaml.safe_load(f)

    empires = state.get("empires", [])
    candidates = [e for e in empires if e.get("name") != "AI" and e.get("hex_map")]

    if not candidates:
        print("No empires with a populated hex_map found.")
        return

    if not args.uid and not args.all:
        print(f"Empires with a map in {state_path}:\n")
        for e in candidates:
            num_tiles = len(e["hex_map"])
            print(f"  uid={e['uid']:>4}  {e.get('name', '?'):<30}  {num_tiles} tiles  life={e.get('max_life', '?')}")
        print("\nPass --uid <uid> (repeatable) or --all to import.")
        return

    selected = candidates if args.all else [e for e in candidates if e["uid"] in args.uid]
    missing = set(args.uid) - {e["uid"] for e in selected}
    if missing:
        print(f"WARNING: uid(s) not found or have no map: {sorted(missing)}", file=sys.stderr)

    saved_maps = _load_saved_maps(SAVED_MAPS_PATH)
    imported = []
    for e in selected:
        uid = e["uid"]
        name = f"{args.name_prefix} {e.get('name', f'uid={uid}')}".strip()
        map_id = f"{env}_{uid}_{int(time.time())}"
        saved_maps.append({
            "id": map_id,
            "name": name,
            "life": e.get("max_life", 10.0),
            "hex_map": e["hex_map"],
        })
        imported.append((map_id, name))
        # ensure unique timestamps if importing multiple empires in the same second
        time.sleep(1.001)

    _write_saved_maps(SAVED_MAPS_PATH, saved_maps)

    print(f"Imported {len(imported)} map(s) into {SAVED_MAPS_PATH}:")
    for map_id, name in imported:
        print(f"  {map_id}  {name}")


if __name__ == "__main__":
    main()
