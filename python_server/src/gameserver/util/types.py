"""Formatting and conversion utilities.

Number formatting, time formatting, effect descriptions.
"""

from __future__ import annotations


def format_time(seconds: float) -> str:
    """Format seconds into a human-readable time string."""
    if seconds < 60:
        return f"{int(seconds)}s"
    if seconds < 3600:
        return f"{int(seconds // 60)}m {int(seconds % 60)}s"
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    return f"{hours}h {minutes}m"


def format_number(value: float) -> str:
    """Format a number with appropriate precision."""
    if value == int(value):
        return str(int(value))
    return f"{value:.1f}"


def format_percent(value: float) -> str:
    """Format a float as percentage."""
    return f"{value * 100:.0f}%"
