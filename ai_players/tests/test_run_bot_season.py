import logging
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bot.state import BotState  # noqa: E402
from run_bot import _check_season_reset, _wipe_log_files  # noqa: E402


def _state() -> BotState:
    s = BotState(name="testbot")
    s.memory["attack_history"] = [{"outcome": "victory"}]
    s.memory["battle_log"] = [{"role": "attacker", "won": True}]
    return s


def test_first_ever_season_seen_does_not_reset():
    state = _state()
    changed = _check_season_reset({"season_number": 3}, state)
    assert changed is False
    assert state.memory["battle_log"] == [{"role": "attacker", "won": True}]
    assert state.memory["last_season"] == 3


def test_same_season_does_not_reset():
    state = _state()
    state.memory["last_season"] = 3
    changed = _check_season_reset({"season_number": 3}, state)
    assert changed is False
    assert state.memory["battle_log"] == [{"role": "attacker", "won": True}]


def test_season_change_resets_memory():
    # _check_season_reset also wipes log files (_wipe_log_files scans the ROOT
    # logger's handlers) — isolate root handlers so this doesn't touch pytest's
    # own log-capture handlers.
    root = logging.getLogger()
    saved_handlers = list(root.handlers)
    root.handlers = []
    try:
        state = _state()
        state.memory["last_season"] = 3
        changed = _check_season_reset({"season_number": 4}, state)
    finally:
        root.handlers = saved_handlers
    assert changed is True
    assert state.memory["battle_log"] == []
    assert state.memory["attack_history"] == []
    assert state.memory["last_season"] == 4
    # account/personality survive a reset
    assert state.name == "testbot"


def test_missing_season_number_is_noop():
    state = _state()
    assert _check_season_reset({}, state) is False
    assert state.memory["battle_log"] == [{"role": "attacker", "won": True}]


def test_wipe_log_files_truncates_open_file_handlers():
    # _wipe_log_files() only looks at the ROOT logger's handlers (that's where
    # run_bot.py's main() installs the per-bot FileHandler via basicConfig).
    # Swap out the root logger's handlers/level for the duration of the test —
    # pytest's own log-capture handlers must not be touched by _wipe_log_files().
    root = logging.getLogger()
    saved_handlers, saved_level = list(root.handlers), root.level
    with tempfile.TemporaryDirectory() as tmp:
        log_path = Path(tmp) / "bot.log"
        handler = logging.FileHandler(log_path)
        root.handlers = [handler]
        root.setLevel(logging.INFO)
        try:
            logging.info("hello")
            logging.info("world")
            handler.flush()
            assert log_path.stat().st_size > 0

            _wipe_log_files()

            assert log_path.stat().st_size == 0
            # handler must still be usable after the wipe (same fd, not reopened)
            logging.info("fresh start")
            handler.flush()
            content = log_path.read_text()
            assert "hello" not in content
            assert "fresh start" in content
        finally:
            handler.close()
            root.handlers = saved_handlers
            root.setLevel(saved_level)
