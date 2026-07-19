#!/usr/bin/env python3
"""
Diff tower (structures.yaml) and critter (critters.yaml) balance changes
between the current working tree and a git revision from N days ago.

Compares each item (by IID) field-by-field and reports additions, removals,
and value changes. Output is machine-readable JSON.

Usage:
    python3 scripts/tower_critter_changes.py                       # last 14 days, prints to stdout
    python3 scripts/tower_critter_changes.py --days 7
    python3 scripts/tower_critter_changes.py --since 2026-06-01
    python3 scripts/tower_critter_changes.py --out data/balancing/changes.json
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = REPO_ROOT / "python_server" / "config"

FILES = {
    "structures": CONFIG_DIR / "structures.yaml",
    "critters": CONFIG_DIR / "critters.yaml",
}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = p.add_mutually_exclusive_group()
    g.add_argument("--days", type=int, default=14, help="Compare against the revision this many days ago (default: 14).")
    g.add_argument("--since", help="Compare against the revision at this date (e.g. 2026-06-01) instead of --days.")
    p.add_argument("--out", type=Path, default=None, help="Write JSON to this path instead of stdout.")
    return p.parse_args()


def git_rev_before(rel_path: Path, since_expr: str) -> str | None:
    """Latest commit hash touching rel_path at or before since_expr, or None if none exists."""
    result = subprocess.run(
        ["git", "log", "-1", "--format=%H", f"--before={since_expr}", "--", str(rel_path)],
        cwd=REPO_ROOT, capture_output=True, text=True, check=True,
    )
    rev = result.stdout.strip()
    return rev or None


def git_show(rev: str, rel_path: Path) -> str | None:
    """File content at a given revision, or None if the file didn't exist yet."""
    result = subprocess.run(
        ["git", "show", f"{rev}:{rel_path.as_posix()}"],
        cwd=REPO_ROOT, capture_output=True, text=True,
    )
    if result.returncode != 0:
        return None
    return result.stdout


def load_yaml_text(text: str) -> dict[str, Any]:
    data = yaml.safe_load(text) or {}
    return {k: v for k, v in data.items() if isinstance(v, dict)}


def diff_items(old: dict[str, Any], new: dict[str, Any]) -> dict[str, Any]:
    added = sorted(set(new) - set(old))
    removed = sorted(set(old) - set(new))
    changed: dict[str, Any] = {}

    for iid in sorted(set(old) & set(new)):
        old_fields = old[iid]
        new_fields = new[iid]
        field_diffs: dict[str, Any] = {}
        for key in sorted(set(old_fields) | set(new_fields)):
            old_val = old_fields.get(key, "__missing__")
            new_val = new_fields.get(key, "__missing__")
            if old_val != new_val:
                field_diffs[key] = {"old": old_fields.get(key), "new": new_fields.get(key)}
        if field_diffs:
            # era/name are carried alongside the diff (not inside it) so a
            # consumer can group/label a changed item even when era/name
            # themselves didn't change. `current` is the full current-state
            # dict so a consumer can show unchanged fields (e.g. damage on a
            # tower whose only change was reload_time) for full context.
            changed[iid] = {
                "era": new_fields.get("era", old_fields.get("era")),
                "name": new_fields.get("name", old_fields.get("name")),
                "fields": field_diffs,
                "current": new_fields,
            }

    return {
        "added": {iid: new[iid] for iid in added},
        "removed": {iid: old[iid] for iid in removed},
        "changed": changed,
    }


def main() -> None:
    args = parse_args()
    since_expr = args.since or f"{args.days} days ago"

    result: dict[str, Any] = {
        "since": since_expr,
        "generated_at": subprocess.run(
            ["git", "log", "-1", "--format=%cI"], cwd=REPO_ROOT, capture_output=True, text=True, check=True,
        ).stdout.strip(),
        "categories": {},
    }

    for category, path in FILES.items():
        rel_path = path.relative_to(REPO_ROOT)
        rev = git_rev_before(rel_path, since_expr)
        if rev is None:
            print(f"WARNING: no revision of {rel_path} found before '{since_expr}' — skipping {category}", file=sys.stderr)
            continue

        old_text = git_show(rev, rel_path)
        if old_text is None:
            print(f"WARNING: {rel_path} did not exist at {rev} — skipping {category}", file=sys.stderr)
            continue

        old_items = load_yaml_text(old_text)
        new_items = load_yaml_text(path.read_text())
        diff = diff_items(old_items, new_items)
        diff["base_revision"] = rev
        result["categories"][category] = diff

    out_json = json.dumps(result, indent=2, ensure_ascii=False, default=str)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(out_json + "\n")
        total_changed = sum(
            len(c["added"]) + len(c["removed"]) + len(c["changed"])
            for c in result["categories"].values()
        )
        print(f"Wrote {args.out} ({total_changed} changed items across {len(result['categories'])} categories)")
    else:
        print(out_json)


if __name__ == "__main__":
    main()
