"""handlers package — thin dispatcher, re-exports everything from _core.py.

During the Strangler Fig migration (T3.1), domain-specific functions are
moved from _core.py into domain submodules. This __init__.py always
re-exports the complete public surface so callers need no changes.

NOTE: mutable module-level variables (_services, _active_battles, etc.) are
forwarded via __getattr__ so that tests that do `handlers._services` always
see the live value from _core, not a stale import-time snapshot.
"""
import types
import sys
from typing import Any
from gameserver.network.handlers import _core  # noqa: F401

# mypy strict requires explicit __all__ for underscore-prefixed re-exports
__all__ = [
    "_evict_observer_from_all", "_apply_artifact_steal", "_compute_and_apply_loot",
    "_create_empire_for_new_user", "_build_empire_summary", "_build_session_state",
    "register_all_handlers",
    "handle_notification_request", "handle_user_message", "handle_timeline_request",
    "handle_userinfo_request", "handle_hall_of_fame",
    "handle_preferences_request", "handle_change_preferences",
]

# Re-export the full public surface of the legacy god module.
from gameserver.network.handlers._core import *  # noqa: F401, F403
from gameserver.network.handlers._core import (  # noqa: F401
    # private names needed by tests / internal callers
    _evict_observer_from_all,
    _apply_artifact_steal,
    _compute_and_apply_loot,
    _create_empire_for_new_user,
    _build_empire_summary,
    _build_session_state,
    register_all_handlers,
)

# Domain submodule re-exports (social already migrated)
from gameserver.network.handlers.social import (  # noqa: F401
    handle_notification_request,
    handle_user_message,
    handle_timeline_request,
    handle_userinfo_request,
    handle_hall_of_fame,
    handle_preferences_request,
    handle_change_preferences,
)

# Forward mutable module-level variables from _core so callers always see the
# live value (import-time copies would be stale after register_all_handlers()).
_FORWARDED = frozenset({"_services", "_active_battles", "_next_bid", "_next_cid", "_next_wid"})


def __getattr__(name: str) -> Any:
    if name in _FORWARDED:
        return getattr(_core, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


# Replace this package's module object with a subclass that also forwards __setattr__
# for the mutable _core variables, so tests that do `handlers._services = x` propagate.
class _ProxyModule(types.ModuleType):
    def __setattr__(self, name: str, value: object) -> None:
        if name in _FORWARDED:
            setattr(_core, name, value)
        else:
            super().__setattr__(name, value)


_this = _ProxyModule(__name__)
_this.__dict__.update(sys.modules[__name__].__dict__)
sys.modules[__name__] = _this
