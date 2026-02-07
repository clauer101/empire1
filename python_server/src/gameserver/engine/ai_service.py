"""AI service — generates and scales AI armies.

AI armies are triggered by player progress (completing buildings/research).
Difficulty scales with the player's total effort level.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from gameserver.engine.upgrade_provider import UpgradeProvider
    from gameserver.models.army import Army


class AIService:
    """Service for AI opponent army generation.

    Args:
        upgrade_provider: Item database for critter lookups.
        templates: AI army templates loaded from config.
    """

    def __init__(
        self,
        upgrade_provider: UpgradeProvider,
        templates: dict,
    ) -> None:
        self._upgrades = upgrade_provider
        self._templates = templates

    def generate_army(self, effort_level: float) -> Army | None:
        """Generate an AI army scaled to the given effort level."""
        # TODO: implement
        return None

    def get_difficulty_tier(self, effort_level: float) -> str:
        """Determine difficulty tier name for the given effort."""
        # TODO: implement
        return "easy"
