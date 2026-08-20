"""Bot detection — per-user AI agent confidence score.

Signals combined into ``bot_probability`` (0.0 = human, 1.0 = bot):

1. **Header fingerprint** (weight 55 % with 2 signals, 45 % with 3)
   Browsers send ``Sec-Ch-Ua``, ``Sec-Fetch-*``, ``Accept-Language``.
   Python/curl bots typically omit all of them.

2. **Reaction latency** (weight 45 % with 2 signals, 35 % with 3)
   Time (ms) between the server sending ``summary_response`` and the client
   taking a game action.  Bots react in < 300 ms; humans in > 2 s.

3. **Timing regularity** (weight 20 %, only once enough samples exist)
   Coefficient of variation of the intervals between a uid's tracked API
   actions. A human clicking buttons never reproduces the same interval
   exactly; a script firing on a fixed schedule does.

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

# 2-signal weights (header + reaction only) — used whenever the timing
# signal isn't available yet (the common case for casual players); kept
# bit-identical to this codebase's original weights so existing behavior
# for low-frequency users never drifts.
_W_HEADER_2WAY = 0.55
_W_REACTION_2WAY = 0.45

# 3-signal weights — used once a uid has accumulated enough api_call
# samples for the timing-regularity signal to be meaningful.
_W_HEADER_3WAY = 0.45
_W_REACTION_3WAY = 0.35
_W_TIMING_3WAY = 0.20

_EWMA_ALPHA = 0.15            # header score update rate (lower = more stable)

_TIMING_WINDOW_S = 600        # trailing window for the timing-regularity signal (10 min)
_TIMING_MIN_SAMPLES = 5       # minimum api_call events before timing signal is meaningful
_TIMING_KIND = "api_call"     # event_window_log 'kind' bucket for this signal

# Show 🤖 badge when probability exceeds this threshold
BOT_THRESHOLD = 0.70

# WS message types that count as "taking an action"
WS_ACTION_TYPES: frozenset[str] = frozenset({
    "new_item", "new_structure", "delete_structure", "upgrade_structure",
    "citizen_upgrade", "change_citizen", "increase_life",
    "new_army", "new_attack_request", "change_army",
})

# REST paths that count as "taking an action" (must be POST/PUT). This is
# the single source of truth — network/rest_api.py's bot_signal_middleware
# imports this rather than maintaining its own copy.
#
# NOTE: "/api/attack" also covers "/api/attack/{id}/skip-siege" (str.startswith
# matches without a trailing slash) — no separate entry needed for skip-siege.
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


def _timing_bot_score(stddev_s: float, mean_s: float) -> float:
    """Return 0.0 (irregular/human) … 1.0 (suspiciously regular/scripted)
    from the coefficient of variation (stddev/mean) of inter-action
    intervals. CV is scale-invariant, so it works whether a uid's action
    cadence is 2s or 200s apart, unlike an absolute stddev threshold.

    CV ≤ 0.05 is near-machine-precision regularity; CV ≥ 0.5 is normal
    human variance. Guards mean_s <= 0 (degenerate/no interval data).
    """
    if mean_s <= 0:
        return 0.5
    cv = stddev_s / mean_s
    if cv <= 0.05:
        return 1.0
    if cv >= 0.5:
        return 0.0
    return 1.0 - (cv - 0.05) / 0.45


# ── BotDetector ──────────────────────────────────────────────────────────────

class BotDetector:
    """Tracks per-user signals and exposes a combined ``bot_probability``."""

    def __init__(self, database: Optional["Database"] = None) -> None:
        self._db = database
        self._pending: dict[int, float] = {}           # uid → monotonic time when summary was sent
        self._reaction_times: dict[int, list[float]] = {}
        self._header_score: dict[int, float] = {}      # -1.0 = never seen
        self._timing_score: dict[int, float] = {}       # uid → timing-regularity score, absent = never refreshed
        self._user_agent: dict[int, str] = {}
        self._bot_probability: dict[int, float] = {}
        self._is_bot: dict[int, bool] = {}
        self._declared: set[int] = set()               # uids that self-declared as bot at signup
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

    def declare_bot(self, uid: int) -> None:
        """Mark uid as a self-declared bot (set at signup; bypasses detection heuristics)."""
        self._declared.add(uid)
        self._is_bot[uid] = True
        self._bot_probability[uid] = 1.0
        try:
            asyncio.get_running_loop().create_task(self._persist_uid(uid))
        except RuntimeError:
            pass

    # ── Signal recording ──────────────────────────────────────────────────────

    def record_reaction_event(self, uid: int) -> None:
        """Mark that the server just sent a summary to uid (starts the reaction timer)."""
        self._pending[uid] = time.monotonic()

    def record_action(self, uid: int) -> None:
        """Record that uid took a game action; compute reaction time if timer is running.

        Also records the action for the timing-regularity signal (one shared
        "api_call" bucket per uid across all tracked endpoints) and schedules
        a refresh of that signal — both fire-and-forget, same pattern as the
        existing persistence task below.
        """
        if self._db is not None:
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(
                    self._db.record_window_event(kind=_TIMING_KIND, key_uid=uid, ts=int(time.time()))
                )
                loop.create_task(self.refresh_timing_signal(uid))
            except RuntimeError:
                pass

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

    async def refresh_timing_signal(self, uid: int) -> None:
        """Query recent api_call event intervals for uid and update the
        timing-regularity score, then recompute the combined probability."""
        if self._db is None:
            return
        since_ts = int(time.time()) - _TIMING_WINDOW_S
        try:
            stats = await self._db.get_window_event_stats_for_key(_TIMING_KIND, uid, since_ts)
        except Exception as exc:
            log.warning("refresh_timing_signal failed uid=%d: %s", uid, exc)
            return
        if stats is None or stats["event_count"] < _TIMING_MIN_SAMPLES:
            return  # not enough data yet — leave _timing_score unset, same as header/reaction fallback
        self._timing_score[uid] = _timing_bot_score(stats["stddev_interval_s"], stats["mean_interval_s"])
        self._recompute(uid)

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
        if uid in self._declared:
            self._bot_probability[uid] = 1.0
            self._is_bot[uid] = True
            return
        h = self._header_score.get(uid, -1.0)
        r_times = self._reaction_times.get(uid, [])
        r = _reaction_bot_score(r_times)
        t = self._timing_score.get(uid)  # None = never refreshed / not enough samples yet

        header_available = h >= 0
        reaction_available = len(r_times) >= _MIN_SAMPLES
        timing_available = t is not None

        if header_available and reaction_available and t is not None:
            # All three signals available — the only case using the new
            # 3-way weights, only reached once a uid has accumulated enough
            # api_call samples.
            self._bot_probability[uid] = (
                _W_HEADER_3WAY * h + _W_REACTION_3WAY * r + _W_TIMING_3WAY * t
            )
        elif header_available and reaction_available:
            # Unchanged 2-signal case — bit-identical to this codebase's
            # original behavior whenever the timing signal isn't available
            # yet (the common case for casual, low-frequency players).
            self._bot_probability[uid] = _W_HEADER_2WAY * h + _W_REACTION_2WAY * r
        elif not header_available and not reaction_available and not timing_available:
            self._bot_probability[uid] = 0.5
        else:
            # Exactly one signal available (any of the three), or timing
            # plus exactly one of header/reaction — renormalize weights over
            # whichever signals are present so no signal is silently dropped.
            weighted: list[tuple[float, float]] = []
            if header_available:
                weighted.append((_W_HEADER_3WAY, h))
            if reaction_available:
                weighted.append((_W_REACTION_3WAY, r))
            if timing_available and t is not None:
                weighted.append((_W_TIMING_3WAY, t))
            total_w = sum(w for w, _ in weighted)
            self._bot_probability[uid] = sum(w * s for w, s in weighted) / total_w

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

    def get_signal_breakdown(self, uid: int) -> dict[str, Any]:
        """Return every raw factor that feeds into bot_probability/is_bot for
        uid — for admin-dashboard transparency into why a given score was
        computed, rather than just the final number.
        """
        header_score = self._header_score.get(uid, -1.0)
        r_times = self._reaction_times.get(uid, [])
        reaction_score = _reaction_bot_score(r_times)
        timing_score = self._timing_score.get(uid)
        return {
            "user_agent": self._user_agent.get(uid, ""),
            "header_score": round(header_score, 3) if header_score >= 0 else None,
            "reaction_sample_count": len(r_times),
            "reaction_score": round(reaction_score, 3) if len(r_times) >= _MIN_SAMPLES else None,
            "timing_score": round(timing_score, 3) if timing_score is not None else None,
            "declared_bot": uid in self._declared,
            "bot_probability": round(self.get_probability(uid), 3),
            "is_bot": self.get_is_bot(uid),
        }

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
