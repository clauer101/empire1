"""Pure decision logic for army building: ruler deployment.

No API calls here — functions take plain dicts (military response, summary)
and return decisions, so everything is unit-testable.
"""

from __future__ import annotations

import random

SKILL_CAPS = {"q": 5, "w": 5, "e": 5, "r": 3}
SKILL_ORDER = ["q", "w", "e", "r"]  # R requires higher ruler level, so last


def pick_ruler(rulers_catalog: dict) -> str | None:
    """Uniformly random ruler from the catalog (items response `rulers`).

    Random so the bot population spreads over all rulers instead of every
    bot deterministically claiming the same one. Chosen once per bot — the
    claim is permanent, so no seed/stability is needed.
    """
    if not rulers_catalog:
        return None
    return random.choice(sorted(rulers_catalog))


def next_skill(ruler: dict) -> str | None:
    """Next skill to level, in SKILL_ORDER, or None when all are capped."""
    for skill in SKILL_ORDER:
        if int(ruler.get(skill, 0) or 0) < SKILL_CAPS[skill]:
            return skill
    return None


def ruler_wave_target(waves: list[dict], ruler_iids: set[str]) -> int | None:
    """Uniformly random existing wave index for ruler placement, or None.

    Only one army is ever built, so this picks among that army's waves
    directly. Returns None once the ruler already occupies a wave, or when
    there are no waves yet. Randomizing (instead of always wave 0) spreads
    ruler placement across the bot population.
    """
    if not waves or any(w.get("iid") in ruler_iids for w in waves):
        return None
    return random.randint(0, len(waves) - 1)


def critter_power(critter: dict) -> float:
    """Per-slot power heuristic mirroring the server's army power formula."""
    return (float(critter.get("health", 0.0))
            * (1.0 + float(critter.get("armour", 0.0)))
            * (1.0 + float(critter.get("speed", 0.0)))
            / max(1, int(critter.get("slots", 1) or 1)))
