"""Economy & research strategy planner."""

from __future__ import annotations

import logging
import time

from bot.api_client import ApiError

from ..army_building import next_skill
from .base import BotContext, Option, Planner, cheapest_affordable

log = logging.getLogger("bot.planner.economy")

# Seconds to wait before retrying a ruler skill-up the server rejected (e.g. the
# next skill needs a higher ruler level than reached). Without this the planner
# would re-propose the same failing skill-up every cycle. Shared with the attack
# planner via memory["ruler_skill_blocked_until"].
SKILL_RETRY_S = 3600.0

ECON_EFFECTS = ("gold_modifier", "gold_offset", "culture_modifier", "culture_offset",
                "research_speed_modifier", "research_speed_offset",
                "build_speed_modifier", "citizen_effect_modifier")

# gain weights: econ-effect items beat plain filler at equal price; free
# strategy-defining actions (ruler skill-up) outrank both.
GAIN_ECON_ITEM = 2.0
GAIN_PLAIN_ITEM = 1.0
GAIN_CITIZEN = 3.0
GAIN_RULER_SKILL = 50.0


def _has_econ_effect(item: dict) -> bool:
    effects = item.get("effects") or {}
    return any(k in effects for k in ECON_EFFECTS)


class EconomyPlanner(Planner):
    def propose_options(self, ctx: BotContext, *,
                        advance_phase: bool = True) -> list[Option]:
        summary = ctx.summary
        options: list[Option] = []

        # 1. Keep research queue busy (prefer econ-effect knowledge)
        if not summary.get("research_queue"):
            knowledge = ctx.items.get("knowledge", {})
            econ = cheapest_affordable(knowledge, ctx, _has_econ_effect)
            iid = econ or cheapest_affordable(knowledge, ctx)
            if iid:
                price = float((knowledge.get(iid, {}).get("costs") or {}).get("gold", 0.0))
                options.append(Option(
                    category="economy", price=price,
                    gain=GAIN_ECON_ITEM if iid == econ else GAIN_PLAIN_ITEM,
                    filler=(iid != econ),
                    description=f"research {iid}",
                    run=lambda api, iid=iid: api.build(iid)))

        # 2. Keep build queue busy (prefer econ-effect buildings)
        if not summary.get("build_queue"):
            buildings = ctx.items.get("buildings", {})
            econ = cheapest_affordable(buildings, ctx, _has_econ_effect)
            iid = econ or cheapest_affordable(buildings, ctx)
            if iid:
                price = float((buildings.get(iid, {}).get("costs") or {}).get("gold", 0.0))
                options.append(Option(
                    category="economy", price=price,
                    gain=GAIN_ECON_ITEM if iid == econ else GAIN_PLAIN_ITEM,
                    filler=(iid != econ),
                    description=f"build {iid}",
                    run=lambda api, iid=iid: api.build(iid)))

        # 3. Buy a citizen when comfortably affordable, then rebalance.
        #    Citizen upgrades cost culture, not gold — emit only when culture
        #    affordable; price stays 0.0 because the gain/price scale is gold-only.
        citizen_price = float(summary.get("citizen_price", 0.0) or 0.0)
        if citizen_price > 0 and ctx.culture >= citizen_price * 1.2:
            citizens = dict(summary.get("citizens", {}))
            total = sum(citizens.values()) + 1
            dist = {
                "merchant": round(total * 0.4),
                "scientist": round(total * 0.4),
            }
            dist["artist"] = max(0, total - dist["merchant"] - dist["scientist"])

            def run(api, dist=dist):
                res = api.citizen_upgrade()
                if isinstance(res, dict) and res.get("success") is False:
                    return res
                return api.set_citizens(dist)

            options.append(Option(
                category="economy", price=0.0, gain=GAIN_CITIZEN,
                description=f"buy citizen + rebalance {dist}", run=run))

        # 4. Spend ruler skill points (claiming is handled by baseline).
        ruler = summary.get("ruler")
        if ruler:
            level = int(ruler.get("level", 0))
            spent = sum(int(ruler.get(s, 0)) for s in "qwer")
            blocked_until = float(ctx.memory.get("ruler_skill_blocked_until", 0.0) or 0.0)
            if level > spent and time.time() >= blocked_until:
                skill = next_skill(ruler)
                if skill:
                    def run_skill_up(api, skill=skill):
                        try:
                            result = api.ruler_skill_up(skill)
                        except ApiError as e:
                            if not 400 <= e.status < 500:
                                raise
                            result = {"success": False, "error": e.body}
                        if isinstance(result, dict) and result.get("success") is False:
                            ctx.memory["ruler_skill_blocked_until"] = (
                                time.time() + SKILL_RETRY_S)
                            log.info("skill-up %s rejected, retry in 1h", skill)
                        return result
                    options.append(Option(
                        category="economy", price=0.0, gain=GAIN_RULER_SKILL,
                        description=f"ruler skill-up {skill}", run=run_skill_up))

        return options
