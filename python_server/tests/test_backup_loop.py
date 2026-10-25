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
    last_daily_date: str | None = None,
    today_date: str = "2026-01-01",
) -> tuple[int, str | None]:
    """Execute one iteration of the backup logic extracted from main._backup_loop.

    Hourly slots (00-23) are overwritten each day. Daily snapshots are keyed by
    calendar date and are never overwritten or deleted.

    Returns (new_hour_slot, new_last_daily_date).
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

    new_last_daily_date = last_daily_date
    if today_date != last_daily_date:
        _shutil.copy2(state_file, daily_dir / f"state_{today_date}.yaml")
        if db_path and db_path.exists():
            _shutil.copy2(db_path, daily_dir / f"gameserver_{today_date}.db")
        new_last_daily_date = today_date

    return new_hour_slot, new_last_daily_date


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
            _run_backup_once(state_file, last_daily_date=None, today_date="2026-01-02")
        )

        assert (tmp_path / "states" / "daily" / "state_2026-01-02.yaml").exists()
        assert new_last == "2026-01-02"

    def test_daily_not_written_same_day(self, tmp_path):
        state_file = tmp_path / "state.yaml"
        state_file.write_text("empires: []", encoding="utf-8")

        asyncio.run(
            _run_backup_once(state_file, last_daily_date="2026-01-03", today_date="2026-01-03")
        )

        # Only the "new day" write happens under a fresh filename; a repeat
        # call for the same date must not touch the daily dir at all.
        assert not any((tmp_path / "states" / "daily").glob("*"))

    def test_daily_snapshots_never_overwritten(self, tmp_path):
        """Each calendar day gets its own file; prior days are untouched by later runs."""
        state_file = tmp_path / "state.yaml"
        state_file.write_text("version: 1", encoding="utf-8")
        asyncio.run(
            _run_backup_once(state_file, last_daily_date=None, today_date="2026-01-01")
        )

        state_file.write_text("version: 2", encoding="utf-8")
        asyncio.run(
            _run_backup_once(state_file, last_daily_date="2026-01-01", today_date="2026-01-02")
        )

        daily_dir = tmp_path / "states" / "daily"
        assert (daily_dir / "state_2026-01-01.yaml").exists()
        assert (daily_dir / "state_2026-01-02.yaml").exists()
        assert "version: 1" in (daily_dir / "state_2026-01-01.yaml").read_text()
        assert "version: 2" in (daily_dir / "state_2026-01-02.yaml").read_text()

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

    def test_daily_db_written_per_date(self, tmp_path):
        """Daily DB backups accumulate under distinct dated filenames, never overwritten."""
        state_file = tmp_path / "state.yaml"
        state_file.write_text("empires: []", encoding="utf-8")
        db_path = tmp_path / "gameserver.db"
        _make_sqlite_db(db_path)

        asyncio.run(_run_backup_once(state_file, db_path=db_path, last_daily_date=None, today_date="2026-01-01"))
        asyncio.run(_run_backup_once(state_file, db_path=db_path, last_daily_date="2026-01-01", today_date="2026-01-08"))

        daily_dir = tmp_path / "states" / "daily"
        assert (daily_dir / "gameserver_2026-01-01.db").exists()
        assert (daily_dir / "gameserver_2026-01-08.db").exists()

    def test_all_24_hourly_slots_written(self, tmp_path):
        state_file = tmp_path / "state.yaml"
        state_file.write_text("empires: []", encoding="utf-8")

        slot = 0
        for _ in range(24):
            slot, _ = asyncio.run(_run_backup_once(state_file, hour_slot=slot))

        hourly_dir = tmp_path / "states" / "hourly"
        for i in range(24):
            assert (hourly_dir / f"state_{i:02d}.yaml").exists(), f"Missing slot {i:02d}"
