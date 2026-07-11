"""Growth strategy: invest in neither attack nor defense — save gold for
buildings/research/citizens (handled unconditionally by baseline.py) instead.

Reached only via the defense-win-streak choice in run_bot.py (alongside
attack) once a bot has proven its maze by winning defense
DEFENSE_WIN_STREAK_TARGET times in a row. Deliberately emits no options at
all: no army spend, not even attack's normally-always-on free actions (spy/
attack calls, wave-fill — see dispatch.py::gather_options, which excludes
attack specifically while growth is active), no maze upkeep (era-swap, tower
upgrades, tower floor — see baseline.py's growth gate).
"""

from __future__ import annotations

from .base import BotContext, Option, Planner


class GrowthPlanner(Planner):
    def propose_options(self, ctx: BotContext, *,
                        advance_phase: bool = True) -> list[Option]:
        return []
