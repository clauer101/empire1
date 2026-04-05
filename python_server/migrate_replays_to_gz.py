#!/usr/bin/env python3
"""One-time migration: compress existing .json replay files to .json.gz."""

import gzip
import json
import sys
from pathlib import Path

REPLAY_DIR = Path(__file__).parent / "replays"


def main() -> None:
    if not REPLAY_DIR.is_dir():
        print(f"Replay dir not found: {REPLAY_DIR}")
        sys.exit(1)

    json_files = sorted(REPLAY_DIR.glob("*.json"))
    if not json_files:
        print("No .json replay files found.")
        return

    ok = skip = fail = 0
    for src in json_files:
        dst = src.with_suffix(".gz")  # foo.json → foo.json.gz
        # full name: bid.json → bid.json.gz
        dst = src.parent / (src.name + ".gz")

        if dst.exists():
            print(f"  SKIP {src.name} (gz already exists)")
            skip += 1
            continue
        try:
            data = src.read_bytes()
            # Validate JSON
            json.loads(data)
            with gzip.open(dst, "wb", compresslevel=6) as f:
                f.write(data)
            ratio = len(data) / dst.stat().st_size
            print(f"  OK   {src.name} → {dst.name}  ({len(data):,} → {dst.stat().st_size:,} bytes, {ratio:.1f}x)")
            src.unlink()
            ok += 1
        except Exception as e:
            print(f"  FAIL {src.name}: {e}")
            fail += 1

    print(f"\nDone: {ok} compressed, {skip} skipped, {fail} failed.")


if __name__ == "__main__":
    main()
