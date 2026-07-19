#!/usr/bin/env python3
"""Reconstruct season_winners rows from historical state.yaml snapshots.

Run this ONLY while the gameserver is stopped (writes to gameserver.db).
Usage: .venv/bin/python scripts/populate_season_winners.py [--db PATH]
"""
import argparse
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent

SEASON_SNAPSHOTS = [
    REPO_ROOT / "data/prod/results/season1/state.yaml",
    REPO_ROOT / "data/prod/results/season2/state.yaml",
]


def reconstruct_winners(state_path: Path) -> tuple[int, str, list[dict]]:
    with open(state_path) as f:
        data = yaml.safe_load(f)
    g = data["global"]
    season_number = g["season_number"]
    season_title = g["season_title"]
    empires = data["empires"]
    ranked = sorted(
        (e for e in empires if e.get("uid") != 0),
        key=lambda e: e.get("resources", {}).get("culture", 0.0),
        reverse=True,
    )
    winners = [
        {
            "place": i + 1,
            "empire_uid": e["uid"],
            "empire_name": e["name"],
            "culture": e.get("resources", {}).get("culture", 0.0),
        }
        for i, e in enumerate(ranked[:3])
    ]
    return season_number, season_title, winners


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default=str(REPO_ROOT / "data/prod/gameserver.db"))
    args = parser.parse_args()

    con = sqlite3.connect(args.db)
    now = datetime.now(timezone.utc).isoformat()

    for snapshot in SEASON_SNAPSHOTS:
        season_number, season_title, winners = reconstruct_winners(snapshot)
        existing = con.execute(
            "SELECT COUNT(*) FROM season_winners WHERE season_number = ?", (season_number,)
        ).fetchone()[0]
        if existing > 0:
            print(f"Season {season_number} already has {existing} row(s) — skipping")
            continue
        for w in winners:
            con.execute(
                "INSERT INTO season_winners "
                "(season_number, season_title, place, empire_uid, empire_name, culture, recorded_at)"
                " VALUES (?, ?, ?, ?, ?, ?, ?)",
                (season_number, season_title, w["place"], w["empire_uid"], w["empire_name"], w["culture"], now),
            )
        con.commit()
        print(f"Season {season_number} ({season_title}): inserted {len(winners)} winner rows")
        for w in winners:
            print(f"  #{w['place']} {w['empire_name']} (uid={w['empire_uid']}) culture={w['culture']:.0f}")

    con.close()


if __name__ == "__main__":
    main()
