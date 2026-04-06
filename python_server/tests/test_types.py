"""Tests for util/types.py — formatting utilities."""

from gameserver.util.types import format_time, format_number, format_percent


class TestFormatTime:
    def test_seconds_only(self):
        assert format_time(45) == "45s"

    def test_minutes_and_seconds(self):
        assert format_time(125) == "2m 5s"

    def test_hours_and_minutes(self):
        assert format_time(3661) == "1h 1m"

    def test_zero(self):
        assert format_time(0) == "0s"

    def test_exact_minute(self):
        assert format_time(60) == "1m 0s"

    def test_exact_hour(self):
        assert format_time(3600) == "1h 0m"


class TestFormatNumber:
    def test_integer_value(self):
        assert format_number(42.0) == "42"

    def test_float_value(self):
        assert format_number(3.7) == "3.7"

    def test_zero(self):
        assert format_number(0.0) == "0"


class TestFormatPercent:
    def test_half(self):
        assert format_percent(0.5) == "50%"

    def test_full(self):
        assert format_percent(1.0) == "100%"

    def test_small(self):
        assert format_percent(0.03) == "3%"
