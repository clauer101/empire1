"""Sprite manifest naming shared by the battle engine and the /api/critters endpoints."""

from __future__ import annotations


def sprite_key(animation: str) -> str:
    """Manifest name (/api/critters ``name``) for a YAML ``animation`` folder path.

    ``assets/sprites/critters/mech_warrior2`` → ``mech_warrior2``;
    ruler folders get a prefix: ``assets/sprites/ruler/maja`` → ``ruler_maja``.
    Returns "" when no animation is configured.
    """
    parts = [p for p in animation.strip().strip("/").split("/") if p]
    if not parts:
        return ""
    folder = parts[-1]
    return f"ruler_{folder}" if len(parts) >= 2 and parts[-2] == "ruler" else folder
