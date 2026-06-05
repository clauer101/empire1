"""Bot detection — per-user AI agent confidence score.

Signals combined into ``bot_probability`` (0.0 = human, 1.0 = bot):

1. **Header fingerprint** (weight 55 %)
   Browsers send ``Sec-Ch-Ua``, ``Sec-Fetch-*``, ``Accept-Language``.
   Python/curl bots typically omit all of them.

2. **Reaction latency** (weight 45 %)
   Time (ms) between the server sending ``summary_response`` and the client
   taking a game action.  Bots react in < 300 ms; humans in > 2 s.

Scores are persisted to SQLite so they survive server restarts.
"""
from __future__ import annotations

import asyncio
import json
import time
from typing import Any, Optional, TYPE_CHECKING

import structlog

if TYPE_CHECKING:
    from gameserver.persistence.database import Database

log = structlog.get_logger(__name__)

# ── Tuning constants ─────────────────────────────────────────────────────────

_BOT_UA_SUBSTRINGS = (
    "python-requests", "python-httpx", "httpx", "aiohttp",
    "curl/", "wget/", "go-http-client", "libwww-perl",
    "java/", "okhttp", "node-fetch", "axios",
)

_REACTION_MIN_MS = 1.0        # ignore sub-ms (noise / same-tick)
_REACTION_MAX_MS = 120_000.0  # ignore if user was idle > 2 min
_MIN_SAMPLES = 3              # reaction signal inactive below this
_MAX_SAMPLES = 20             # sliding window size

_W_HEADER = 0.55              # weight of header signal
_W_REACTION = 0.45            # weight of reaction signal
_EWMA_ALPHA = 0.15            # header score update rate (lower = more stable)

# Show 🤖 badge when probability exceeds this threshold
BOT_THRESHOLD = 0.70

# WS message types that count as "taking an action"
WS_ACTION_TYPES: frozenset[str] = frozenset({
    "new_item", "new_structure", "delete_structure", "upgrade_structure",
    "citizen_upgrade", "change_citizen", "increase_life",
    "new_army", "new_attack_request", "change_army",
})

# REST paths that count as "taking an action" (must be POST/PUT)
REST_ACTION_PREFIXES: tuple[str, ...] = (
    "/api/empire/build",
    "/api/empire/citizen",
    "/api/map/buy-tile",
    "/api/empire/ruler/skill-up",
    "/api/empire/ruler/choose",
    "/api/army",
    "/api/attack",
    "/api/spy-attack",
    "/api/item/buy-upgrade",
)


# ── Signal functions ─────────────────────────────────────────────────────────

def _header_bot_score(headers: Any) -> float:
    """Return 0.0 (browser) … 1.0 (bot) from HTTP headers."""
    get = headers.get if hasattr(headers, "get") else lambda k, d="": d
    ua = get("user-agent", "").lower()

    if any(s in ua for s in _BOT_UA_SUBSTRINGS):
        return 0.92

    browser_signals = sum([
        bool(get("sec-ch-ua", "")),
        bool(get("sec-fetch-site", "")),
        bool(get("sec-fetch-mode", "")),
        bool(get("accept-language", "")),
    ])

    # Mozilla/5.0 UA but zero Sec-* headers → spoofed UA
    if "mozilla/5.0" in ua and browser_signals == 0:
        return 0.70

    return max(0.0, 1.0 - browser_signals / 4.0)


def _reaction_bot_score(times_ms: list[float]) -> float:
    """Return 0.0 (human) … 1.0 (bot) from reaction-time distribution."""
    if len(times_ms) < _MIN_SAMPLES:
        return 0.5  # not enough data
    median = sorted(times_ms)[len(times_ms) // 2]
    if median <= 200:
        return 1.0
    if median >= 10_000:
        return 0.0
    return 1.0 - (median - 200) / 9_800.0


# ── BotDetector ──────────────────────────────────────────────────────────────

class BotDetector:
    """Tracks per-user signals and exposes a combined ``bot_probability``."""

    def __init__(self, database: Optional["Database"] = None) -> None:
        self._db = database
        self._pending: dict[int, float] = {}           # uid → monotonic time when summary was sent
        self._reaction_times: dict[int, list[float]] = {}
        self._header_score: dict[int, float] = {}      # -1.0 = never seen
        self._user_agent: dict[int, str] = {}
        self._bot_probability: dict[int, float] = {}
        self._is_bot: dict[int, bool] = {}
        self._last_header_persist: dict[int, float] = {}  # uid → monotonic time

    # ── Startup ───────────────────────────────────────────────────────────────

    async def load_all(self) -> None:
        """Load persisted signals from DB (call once at startup)."""
        if self._db is None:
            return
        rows = await self._db.list_bot_signals()
        for row in rows:
            uid = row["uid"]
            try:
                self._reaction_times[uid] = json.loads(row.get("reaction_times_json") or "[]")
            except Exception:
                self._reaction_times[uid] = []
            self._header_score[uid] = float(row.get("header_bot_score") or -1.0)
            self._user_agent[uid] = row.get("user_agent") or ""
            self._bot_probability[uid] = float(row.get("bot_probability") or 0.5)
        log.info("BotDetector loaded %d records", len(self._bot_probability))

    def sync_from_empires(self, empires: Any) -> None:
        """Initialise _is_bot from persisted Empire.is_bot values (call once after startup load)."""
        values = empires.values() if hasattr(empires, "values") else empires
        for empire in values:
            self._is_bot[empire.uid] = bool(empire.is_bot)

    # ── Signal recording ──────────────────────────────────────────────────────

    def record_reaction_event(self, uid: int) -> None:
        """Mark that the server just sent a summary to uid (starts the reaction timer)."""
        self._pending[uid] = time.monotonic()

    def record_action(self, uid: int) -> None:
        """Record that uid took a game action; compute reaction time if timer is running."""
        pending = self._pending.pop(uid, None)
        if pending is None:
            return
        ms = (time.monotonic() - pending) * 1000.0
        if ms < _REACTION_MIN_MS or ms > _REACTION_MAX_MS:
            return
        times = self._reaction_times.setdefault(uid, [])
        times.append(ms)
        if len(times) > _MAX_SAMPLES:
            times.pop(0)
        self._recompute(uid)
        try:
            asyncio.get_running_loop().create_task(self._persist_uid(uid))
        except RuntimeError:
            pass

    def record_header_signal(self, uid: int, headers: Any) -> None:
        """Update header-based score (EWMA) for uid."""
        score = _header_bot_score(headers)
        ua = headers.get("user-agent", "") if hasattr(headers, "get") else ""
        prev = self._header_score.get(uid, -1.0)
        if prev < 0:
            self._header_score[uid] = score
            should_persist = True
        else:
            self._header_score[uid] = (1 - _EWMA_ALPHA) * prev + _EWMA_ALPHA * score
            # Persist at most once per 5 minutes or on significant change
            now = time.monotonic()
            last = self._last_header_persist.get(uid, 0.0)
            should_persist = abs(self._header_score[uid] - prev) > 0.1 or (now - last) > 300
        self._user_agent[uid] = ua
        self._recompute(uid)
        if should_persist:
            self._last_header_persist[uid] = time.monotonic()
            try:
                asyncio.get_running_loop().create_task(self._persist_uid(uid))
            except RuntimeError:
                pass

    # ── Probability ───────────────────────────────────────────────────────────

    def _recompute(self, uid: int) -> None:
        h = self._header_score.get(uid, -1.0)
        r_times = self._reaction_times.get(uid, [])
        r = _reaction_bot_score(r_times)

        if h < 0 and len(r_times) < _MIN_SAMPLES:
            self._bot_probability[uid] = 0.5
        elif h < 0:
            self._bot_probability[uid] = r
        elif len(r_times) < _MIN_SAMPLES:
            self._bot_probability[uid] = h
        else:
            self._bot_probability[uid] = _W_HEADER * h + _W_REACTION * r

        # Hysteresis: flag set at ≥ 0.95, cleared only when < 0.50
        prob = self._bot_probability[uid]
        current = self._is_bot.get(uid, False)
        if prob >= 0.95:
            self._is_bot[uid] = True
        elif prob < 0.50:
            self._is_bot[uid] = False
        else:
            self._is_bot[uid] = current  # stay in current state

    def get_probability(self, uid: int) -> float:
        """Return bot probability in [0.0, 1.0]. Returns 0.5 when unknown."""
        return self._bot_probability.get(uid, 0.5)

    def get_is_bot(self, uid: int) -> bool:
        """Return the stable is_bot flag (hysteresis: set ≥ 0.95, cleared < 0.50)."""
        return self._is_bot.get(uid, False)

    # ── Persistence ───────────────────────────────────────────────────────────

    async def _persist_uid(self, uid: int) -> None:
        if self._db is None:
            return
        try:
            await self._db.upsert_bot_signal(
                uid=uid,
                reaction_times_json=json.dumps(self._reaction_times.get(uid, [])),
                header_bot_score=self._header_score.get(uid, -1.0),
                bot_probability=self._bot_probability.get(uid, 0.5),
                user_agent=self._user_agent.get(uid, ""),
            )
        except Exception as exc:
            log.warning("BotDetector persist failed uid=%d: %s", uid, exc)
