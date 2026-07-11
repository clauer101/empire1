import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bot.strategy import NO_EXPIRY, is_expired  # noqa: E402
from run_bot import _empire_list  # noqa: E402


class _ApiListShape:
    """GET /api/empires as a bare list (not the real server shape, but must
    still work — some callers historically assumed this)."""
    def empires(self):
        return [{"uid": 1, "name": "A"}, {"uid": 2, "name": "B"}]


class _ApiDictShape:
    """The REAL server shape (empire.py::list_empires): {"empires": [...]}.

    _empire_list() must unwrap this — the bare-list assumption in run_bot.py's
    successful-defense and lost-attack-revenge code caused
    `e.get("uid")` to run over dict *keys* (strings) instead of empire dicts,
    crashing the whole cycle with an AttributeError and silently preventing
    the defense-won → attack switch from ever taking effect.
    """
    def empires(self):
        return {"empires": [{"uid": 1, "name": "A"}, {"uid": 2, "name": "B"}]}


class _ApiNoneShape:
    """Defensive: some ApiClient methods return None on empty responses."""
    def empires(self):
        return None


def test_empire_list_unwraps_dict_shape():
    result = _empire_list(_ApiDictShape())
    assert result == [{"uid": 1, "name": "A"}, {"uid": 2, "name": "B"}]
    # every entry must be a dict (the bug manifested as .get() on a str)
    assert all(isinstance(e, dict) for e in result)


def test_empire_list_accepts_bare_list():
    assert _empire_list(_ApiListShape()) == [{"uid": 1, "name": "A"}, {"uid": 2, "name": "B"}]


def test_empire_list_handles_none():
    assert _empire_list(_ApiNoneShape()) == []


def test_no_expiry_sentinel_never_expires():
    strategy = {"type": "attack", "valid_until": NO_EXPIRY, "source": "defense_won"}
    assert is_expired(strategy) is False
