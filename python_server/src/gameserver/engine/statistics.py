"""Statistics service — TAI scoring, rankings, win conditions.

TAI (Total Achievement Index):
    sqrt(build_progress + research_progress + structure_costs * 3)
    * (1 + artefact_bonus + citizen_bonus)

Win conditions:
- World Wonder: Complete a wonder building.
- Treasure Hunter: Hold N different artefacts for M days.
- Defense God: Undefeated for 28 days.
- Prosperity: Highest TAI after the apocalypse phase.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from gameserver.models.empire import Empire


class StatisticsService:
    """Service for scoring and ranking.

    Manages TAI calculation, win condition evaluation, and
    leaderboard queries.
    """

    def calc_tai(self, empire: Empire) -> float:
        """Calculate the Total Achievement Index for an empire."""
        # TODO: implement
        return 0.0

    def check_win_conditions(self, empire: Empire) -> str | None:
        """Check if any win condition is met. Returns condition name or None."""
        # TODO: implement
        return None
