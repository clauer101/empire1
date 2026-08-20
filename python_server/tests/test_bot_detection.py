"""Tests for engine/bot_detection.py — BotDetector and its pure signal functions.

No coverage existed for this module before this test file. Covers:
1. Pure functions: _header_bot_score, _reaction_bot_score, _timing_bot_score
2. _recompute weighting for all fallback branches (2-signal unchanged, new 3-signal)
3. Hysteresis on the is_bot flag
4. declare_bot bypass
5. refresh_timing_signal against a real in-memory Database
"""

from __future__ import annotations

import time

import pytest

from gameserver.engine.bot_detection import (
    BotDetector,
    _header_bot_score,
    _reaction_bot_score,
    _timing_bot_score,
)
from gameserver.persistence.database import Database


# ---------------------------------------------------------------------------
# Pure functions
# ---------------------------------------------------------------------------

class TestHeaderBotScore:
    def test_known_bot_user_agent(self):
        assert _header_bot_score({"user-agent": "python-requests/2.31"}) == 0.92

    def test_curl_user_agent(self):
        assert _header_bot_score({"user-agent": "curl/8.1.0"}) == 0.92

    def test_full_browser_headers_scores_zero(self):
        headers = {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0)",
            "sec-ch-ua": '"Chromium";v="120"',
            "sec-fetch-site": "same-origin",
            "sec-fetch-mode": "cors",
            "accept-language": "en-US",
        }
        assert _header_bot_score(headers) == 0.0

    def test_spoofed_mozilla_ua_with_no_browser_headers(self):
        headers = {"user-agent": "Mozilla/5.0"}
        assert _header_bot_score(headers) == 0.70

    def test_partial_browser_headers(self):
        headers = {
            "user-agent": "SomeClient/1.0",
            "sec-ch-ua": '"Chromium";v="120"',
            "sec-fetch-site": "same-origin",
        }
        assert _header_bot_score(headers) == 0.5

    def test_missing_get_method_defaults_safely(self):
        # headers object without .get (defensive path) — should not raise
        assert _header_bot_score({}) >= 0.0


class TestReactionBotScore:
    def test_below_min_samples_is_neutral(self):
        assert _reaction_bot_score([100.0, 200.0]) == 0.5

    def test_fast_median_is_bot(self):
        assert _reaction_bot_score([100.0, 150.0, 180.0]) == 1.0

    def test_slow_median_is_human(self):
        assert _reaction_bot_score([15_000.0, 20_000.0, 25_000.0]) == 0.0

    def test_interpolated_middle_value(self):
        # median = 5100ms -> 1.0 - (5100-200)/9800 = 1.0 - 0.5 = 0.5
        score = _reaction_bot_score([5100.0, 5100.0, 5100.0])
        assert abs(score - 0.5) < 1e-9


class TestTimingBotScore:
    def test_zero_variance_is_scripted(self):
        assert _timing_bot_score(stddev_s=0.0, mean_s=10.0) == 1.0

    def test_low_cv_is_scripted(self):
        assert _timing_bot_score(stddev_s=0.3, mean_s=10.0) == 1.0  # cv=0.03

    def test_high_cv_is_human(self):
        assert _timing_bot_score(stddev_s=8.0, mean_s=10.0) == 0.0  # cv=0.8

    def test_interpolated_middle_cv(self):
        # cv = 0.275 (midpoint of 0.05..0.5) -> score = 0.5
        score = _timing_bot_score(stddev_s=2.75, mean_s=10.0)
        assert abs(score - 0.5) < 1e-9

    def test_degenerate_mean_returns_neutral(self):
        assert _timing_bot_score(stddev_s=0.0, mean_s=0.0) == 0.5
        assert _timing_bot_score(stddev_s=1.0, mean_s=-5.0) == 0.5


# ---------------------------------------------------------------------------
# _recompute weighting
# ---------------------------------------------------------------------------

class TestRecomputeWeighting:
    def test_no_signals_is_neutral(self):
        bd = BotDetector(database=None)
        assert bd.get_probability(1) == 0.5

    def test_header_only(self):
        bd = BotDetector(database=None)
        bd._header_score[1] = 0.9
        bd._recompute(1)
        assert bd.get_probability(1) == 0.9

    def test_reaction_only(self):
        bd = BotDetector(database=None)
        bd._reaction_times[1] = [100.0, 150.0, 180.0]  # median -> score 1.0
        bd._recompute(1)
        assert bd.get_probability(1) == 1.0

    def test_header_and_reaction_uses_2way_weights_unchanged(self):
        bd = BotDetector(database=None)
        bd._header_score[1] = 0.8
        bd._reaction_times[1] = [100.0, 150.0, 180.0]  # score 1.0
        bd._recompute(1)
        expected = 0.55 * 0.8 + 0.45 * 1.0
        assert abs(bd.get_probability(1) - expected) < 1e-9

    def test_all_three_signals_uses_3way_weights(self):
        bd = BotDetector(database=None)
        bd._header_score[1] = 0.8
        bd._reaction_times[1] = [100.0, 150.0, 180.0]  # score 1.0
        bd._timing_score[1] = 0.6
        bd._recompute(1)
        expected = 0.45 * 0.8 + 0.35 * 1.0 + 0.20 * 0.6
        assert abs(bd.get_probability(1) - expected) < 1e-9

    def test_timing_absent_falls_back_to_2way_even_with_dict_entry_missing(self):
        bd = BotDetector(database=None)
        bd._header_score[1] = 0.8
        bd._reaction_times[1] = [100.0, 150.0, 180.0]
        # no bd._timing_score[1] set at all
        bd._recompute(1)
        expected = 0.55 * 0.8 + 0.45 * 1.0
        assert abs(bd.get_probability(1) - expected) < 1e-9


class TestHysteresis:
    def test_sets_is_bot_at_high_probability(self):
        bd = BotDetector(database=None)
        bd._header_score[1] = 0.99
        bd._reaction_times[1] = [100.0, 100.0, 100.0]
        bd._recompute(1)
        assert bd.get_probability(1) >= 0.95
        assert bd.get_is_bot(1) is True

    def test_holds_state_in_dead_zone(self):
        bd = BotDetector(database=None)
        bd._is_bot[1] = True
        bd._header_score[1] = 0.7  # mid-range, dead zone with reaction below
        bd._reaction_times[1] = [5000.0, 5000.0, 5000.0]
        bd._recompute(1)
        prob = bd.get_probability(1)
        assert 0.50 <= prob < 0.95
        assert bd.get_is_bot(1) is True  # held from prior state

    def test_clears_only_below_050(self):
        bd = BotDetector(database=None)
        bd._is_bot[1] = True
        bd._header_score[1] = 0.1
        bd._reaction_times[1] = [20_000.0, 20_000.0, 20_000.0]  # score 0.0
        bd._recompute(1)
        assert bd.get_probability(1) < 0.50
        assert bd.get_is_bot(1) is False


class TestDeclareBot:
    def test_pins_probability_and_flag(self):
        bd = BotDetector(database=None)
        bd.declare_bot(42)
        assert bd.get_probability(42) == 1.0
        assert bd.get_is_bot(42) is True

    def test_overrides_other_signals_on_recompute(self):
        bd = BotDetector(database=None)
        bd.declare_bot(42)
        bd._header_score[42] = 0.0  # would otherwise say "definitely human"
        bd._recompute(42)
        assert bd.get_probability(42) == 1.0
        assert bd.get_is_bot(42) is True


# ---------------------------------------------------------------------------
# refresh_timing_signal — real in-memory DB
# ---------------------------------------------------------------------------

@pytest.fixture
async def db() -> Database:
    database = Database(":memory:")
    await database.connect()
    yield database
    await database.close()


class TestRefreshTimingSignal:
    async def test_not_enough_samples_leaves_timing_score_unset(self, db: Database):
        bd = BotDetector(database=db)
        now = int(time.time())
        for i in range(2):  # below _TIMING_MIN_SAMPLES
            await db.record_window_event("api_call", 7, now + i * 10)
        await bd.refresh_timing_signal(7)
        assert 7 not in bd._timing_score

    async def test_regular_intervals_yield_high_score(self, db: Database):
        bd = BotDetector(database=db)
        now = int(time.time())
        for i in range(5):
            await db.record_window_event("api_call", 7, now + i * 10)
        await bd.refresh_timing_signal(7)
        assert bd._timing_score[7] == 1.0
        assert bd.get_probability(7) == 1.0  # timing is the only signal available

    async def test_no_events_leaves_timing_score_unset(self, db: Database):
        bd = BotDetector(database=db)
        await bd.refresh_timing_signal(999)
        assert 999 not in bd._timing_score


# ---------------------------------------------------------------------------
# get_signal_breakdown
# ---------------------------------------------------------------------------

class TestSignalBreakdown:
    def test_unknown_uid_returns_neutral_breakdown(self):
        bd = BotDetector(database=None)
        b = bd.get_signal_breakdown(999)
        assert b["user_agent"] == ""
        assert b["header_score"] is None
        assert b["reaction_sample_count"] == 0
        assert b["reaction_score"] is None
        assert b["timing_score"] is None
        assert b["declared_bot"] is False
        assert b["bot_probability"] == 0.5
        assert b["is_bot"] is False

    def test_header_only_populates_header_fields(self):
        bd = BotDetector(database=None)
        bd.record_header_signal(1, {"user-agent": "curl/8.1.0"})
        b = bd.get_signal_breakdown(1)
        assert b["user_agent"] == "curl/8.1.0"
        assert b["header_score"] == 0.92
        assert b["reaction_score"] is None
        assert b["reaction_sample_count"] == 0

    def test_reaction_score_only_populated_at_min_samples(self):
        bd = BotDetector(database=None)
        bd._reaction_times[1] = [100.0, 100.0]  # below _MIN_SAMPLES
        b = bd.get_signal_breakdown(1)
        assert b["reaction_sample_count"] == 2
        assert b["reaction_score"] is None

        bd._reaction_times[1] = [100.0, 100.0, 100.0]  # at _MIN_SAMPLES
        b = bd.get_signal_breakdown(1)
        assert b["reaction_sample_count"] == 3
        assert b["reaction_score"] == 1.0

    def test_timing_score_reflects_internal_state(self):
        bd = BotDetector(database=None)
        bd._timing_score[1] = 0.42
        b = bd.get_signal_breakdown(1)
        assert b["timing_score"] == 0.42

    def test_declared_bot_reported(self):
        bd = BotDetector(database=None)
        bd.declare_bot(1)
        b = bd.get_signal_breakdown(1)
        assert b["declared_bot"] is True
        assert b["bot_probability"] == 1.0
        assert b["is_bot"] is True

    def test_bot_probability_and_is_bot_match_getters(self):
        bd = BotDetector(database=None)
        bd._header_score[1] = 0.99
        bd._reaction_times[1] = [100.0, 100.0, 100.0]
        bd._recompute(1)
        b = bd.get_signal_breakdown(1)
        assert b["bot_probability"] == round(bd.get_probability(1), 3)
        assert b["is_bot"] == bd.get_is_bot(1)
