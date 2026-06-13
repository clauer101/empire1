"""Artifact theft strategy: same machine as attack, but success = artifact looted."""

from __future__ import annotations

from .attack import AttackPlanner


class ArtifactPlanner(AttackPlanner):
    def _goal_reached(self, history_entry: dict) -> bool:
        return bool(history_entry.get("artifacts"))
