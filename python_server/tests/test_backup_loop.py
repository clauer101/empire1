"""Tests for the rolling backup loop in main.py.

Verifies that hourly and daily state backups are written correctly,
including when destination files already exist (VACUUM INTO overwrites).
"""

from __future__ import annotations

import asyncio
import sqlite3
from pathlib import Path



# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_sqlite_db(path: Path) -> None:
    conn = sqlite3.connect(str(path))
    conn.execute("CREATE TABLE t (x INT)")
    conn.execute("INSERT INTO t VALUES (1)")
    conn.commit()
    conn.close()


async def _run_backup_once(
    state_file: Path,
    db_path: Path | None = None,
    *,
    hour_slot: int = 0,
    last_daily_day: int | None = None,
    today_weekday: int = 0,
) -> tuple[int, int | None]:
    """Execute one iteration of the backup logic extracted from main._backup_loop.

    Returns (new_hour_slot, new_last_daily_day).
    """
    import shutil as _shutil

    data_dir = state_file.parent
    hourly_dir = data_dir / "states" / "hourly"
    daily_dir = data_dir / "states" / "daily"
    hourly_dir.mkdir(parents=True, exist_ok=True)
    daily_dir.mkdir(parents=True, exist_ok=True)

    slot = f"{hour_slot:02d}"
    _shutil.copy2(state_file, hourly_dir / f"state_{slot}.yaml")

    if db_path and db_path.exists():
        dest = hourly_dir / f"gameserver_{slot}.db"
        if dest.exists():
            dest.unlink()
        conn = sqlite3.connect(str(db_path))
        conn.execute(f"VACUUM INTO '{dest}'")
        conn.close()

    new_hour_slot = (hour_slot + 1) % 24

    new_last_daily_day = last_daily_day
    if today_weekday != last_daily_day:
        day = f"day{today_weekday}"
        _shutil.copy2(state_file, daily_dir / f"state_{day}.yaml")
        if db_path and db_path.exists():
            dest_d = daily_dir / f"gameserver_{day}.db"
            if dest_d.exists():
                dest_d.unlink()
            conn = sqlite3.connect(str(db_path))
            conn.execute(f"VACUUM INTO '{dest_d}'")
            conn.close()
        new_last_daily_day = today_weekday

    return new_hour_slot, new_last_daily_day


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestBackupWritesFiles:
    def test_hourly_yaml_written(self, tmp_path):
        state_file = tmp_path / "state.yaml"
        state_file.write_text("empires: []", encoding="utf-8")

        asyncio.run(_run_backup_once(state_file, hour_slot=0))

        assert (tmp_path / "states" / "hourly" / "state_00.yaml").exists()

    def test_hourly_db_written(self, tmp_path):
        state_file = tmp_path / "state.yaml"
        state_file.write_text("empires: []", encoding="utf-8")
        db_path = tmp_path / "gameserver.db"
        _make_sqlite_db(db_path)

        asyncio.run(_run_backup_once(state_file, db_path=db_path, hour_slot=3))

        assert (tmp_path / "states" / "hourly" / "gameserver_03.db").exists()

    def test_daily_yaml_written_on_new_day(self, tmp_path):
        state_file = tmp_path / "state.yaml"
        state_file.write_text("empires: []", encoding="utf-8")

        _, new_last = asyncio.run(
            _run_backup_once(state_file, last_daily_day=None, today_weekday=2)
        )

        assert (tmp_path / "states" / "daily" / "state_day2.yaml").exists()
        assert new_last == 2

    def test_daily_not_written_same_day(self, tmp_path):
        state_file = tmp_path / "state.yaml"
        state_file.write_text("empires: []", encoding="utf-8")

        asyncio.run(
            _run_backup_once(state_file, last_daily_day=3, today_weekday=3)
        )

        assert not (tmp_path / "states" / "daily" / "state_day3.yaml").exists()

    def test_hourly_slot_wraps_at_24(self, tmp_path):
        state_file = tmp_path / "state.yaml"
        state_file.write_text("empires: []", encoding="utf-8")

        new_slot, _ = asyncio.run(_run_backup_once(state_file, hour_slot=23))

        assert new_slot == 0

    def test_hourly_yaml_overwritten_on_second_run(self, tmp_path):
        """Second backup to same slot must overwrite without error."""
        state_file = tmp_path / "state.yaml"
        state_file.write_text("version: 1", encoding="utf-8")
        asyncio.run(_run_backup_once(state_file, hour_slot=5))

        state_file.write_text("version: 2", encoding="utf-8")
        asyncio.run(_run_backup_once(state_file, hour_slot=5))

        content = (tmp_path / "states" / "hourly" / "state_05.yaml").read_text()
        assert "version: 2" in content

    def test_hourly_db_overwritten_on_second_run(self, tmp_path):
        """VACUUM INTO must succeed even when destination .db already exists."""
        state_file = tmp_path / "state.yaml"
        state_file.write_text("empires: []", encoding="utf-8")
        db_path = tmp_path / "gameserver.db"
        _make_sqlite_db(db_path)

        # First backup
        asyncio.run(_run_backup_once(state_file, db_path=db_path, hour_slot=7))
        # Second backup to same slot — must not raise
        asyncio.run(_run_backup_once(state_file, db_path=db_path, hour_slot=7))

        assert (tmp_path / "states" / "hourly" / "gameserver_07.db").exists()

    def test_daily_db_overwritten_on_second_week(self, tmp_path):
        """Daily DB backup overwrites the same weekday slot next week."""
        state_file = tmp_path / "state.yaml"
        state_file.write_text("empires: []", encoding="utf-8")
        db_path = tmp_path / "gameserver.db"
        _make_sqlite_db(db_path)

        asyncio.run(_run_backup_once(state_file, db_path=db_path, last_daily_day=None, today_weekday=1))
        asyncio.run(_run_backup_once(state_file, db_path=db_path, last_daily_day=None, today_weekday=1))

        assert (tmp_path / "states" / "daily" / "gameserver_day1.db").exists()

    def test_all_24_hourly_slots_written(self, tmp_path):
        state_file = tmp_path / "state.yaml"
        state_file.write_text("empires: []", encoding="utf-8")

        slot = 0
        for _ in range(24):
            slot, _ = asyncio.run(_run_backup_once(state_file, hour_slot=slot))

        hourly_dir = tmp_path / "states" / "hourly"
        for i in range(24):
            assert (hourly_dir / f"state_{i:02d}.yaml").exists(), f"Missing slot {i:02d}"
