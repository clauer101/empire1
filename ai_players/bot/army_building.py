"""Pure decision logic for army building: ruler deployment and strengthening.

No API calls here — functions take plain dicts (military response, summary)
and return decisions, so everything is unit-testable.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from bot.analyzer import ERA_RANK

SKILL_CAPS = {"q": 5, "w": 5, "e": 5, "r": 3}
SKILL_ORDER = ["r", "q", "w", "e"]  # R first (strongest), then Q/W/E

# Strengthen-on-defeat tuning
MAX_STRENGTHEN_ROUNDS = 6       # defeats against one target before giving up
MIN_WAVES_FOR_SECOND_ARMY = 4   # first army needs this many waves first
ADD_WAVE_MIN_SLOTS = 4          # existing waves must be this well-stocked first

# Proactive build-up tuning (before the first attack)
MAX_BUILD_UP_ROUNDS = 12        # safety cap on proactive build-up purchases
BUILD_BASE_POWER = 40.0         # lean army-power floor (one filled current-era wave)
BUILD_STRENGTH_K = 1.0          # how hard est_strength scales the target on defeat


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


def ruler_wave_target(armies: list[dict], ruler_iids: set[str]) -> tuple[int, int] | None:
    """(aid, wave_number) where the ruler should go, or None if already placed.

    Targets wave 0 of the strongest army (by wave count, then aid).
    wave_number is the 0-indexed wave position (server semantics).
    """
    for army in armies:
        for wave in army.get("waves", []):
            if wave.get("iid") in ruler_iids:
                return None  # ruler already deployed
    if not armies:
        return None
    best = max(armies, key=lambda a: (len(a.get("waves", [])), -a.get("aid", 0)))
    if not best.get("waves"):
        return None
    return int(best["aid"]), 0


def critter_power(critter: dict) -> float:
    """Per-slot power heuristic mirroring the server's army power formula."""
    return (float(critter.get("health", 0.0))
            * (1.0 + float(critter.get("armour", 0.0)))
            * (1.0 + float(critter.get("speed", 0.0)))
            / max(1, int(critter.get("slots", 1) or 1)))


def army_power(military: dict, ruler_iids: set[str]) -> float:
    """Total per-slot power of all filled, non-ruler waves across all armies."""
    critters = {c["iid"]: c for c in military.get("available_critters", [])}
    total = 0.0
    for army in military.get("armies", []):
        for wave in army.get("waves", []):
            iid = wave.get("iid") or ""
            if not iid or iid in ruler_iids:
                continue
            cur = critters.get(iid)
            if cur is None:
                continue
            total += critter_power(cur) * int(wave.get("slots", 1) or 1)
    return total


def build_up_target(summary: dict, opp_memory: dict, cur_power: float) -> float:
    """Army power to reach before attacking (spy-relative, era-independent).

    Lean by default: field a basic current-era army and attack. Once a prior
    battle against this opponent was a defeat, scale the target above the army
    power that just lost by the estimated defensive strength (killed/spawned
    ratio, 0..1) so the next attempt fields a meaningfully stronger army.
    """
    if opp_memory.get("last_outcome") == "defeat":
        est_strength = float(opp_memory.get("est_strength", 0.0) or 0.0)
        return max(BUILD_BASE_POWER, cur_power * (1.0 + est_strength * BUILD_STRENGTH_K))
    return BUILD_BASE_POWER


@dataclass
class StrengthenOption:
    kind: str          # switch_critter | buy_slot | buy_wave_era | add_wave | create_army
    description: str
    price: float       # 0.0 = free
    aid: int = 0
    wave_number: int = 0
    critter_iid: str = ""
    slots: int = 1
    gain: float = 0.0  # power gain estimate (for ranking)
    tier: int = 2      # priority tier, lower wins (0=reach current era, 3=widen breadth)


def strengthen_plan(military: dict, summary: dict,
                    ruler_iids: set[str]) -> list[StrengthenOption]:
    """Ranked strengthening options (best first: gain per gold, free first).

    Uses the military response only: armies[].waves[] with iid/slots/max_era/
    next_slot_price/next_era_price, armies[].next_wave_price and
    available_critters (health/armour/speed/slots/era_index).
    """
    armies = military.get("armies", [])
    critters = {c["iid"]: c for c in military.get("available_critters", [])}
    if not armies:
        return []
    current_era_rank = ERA_RANK.get(summary.get("era", "stone"), 0)
    options: list[StrengthenOption] = []

    for army in armies:
        aid = int(army["aid"])
        for wn, wave in enumerate(army.get("waves", [])):
            iid = wave.get("iid") or ""
            if iid in ruler_iids:
                continue  # never touch the ruler wave
            slots = int(wave.get("slots", 1) or 1)
            max_era = int(wave.get("max_era", 0) or 0)
            below_current = max_era < current_era_rank
            cur = critters.get(iid)
            cur_power = critter_power(cur) * slots if cur else 0.0

            # a) free: switch to the strongest critter that fits this wave's era
            fitting = [c for c in critters.values()
                       if int(c.get("era_index", 0)) <= max_era]
            if fitting:
                best = max(fitting, key=critter_power)
                gain = critter_power(best) * slots - cur_power
                if best["iid"] != iid and gain > 0:
                    options.append(StrengthenOption(
                        kind="switch_critter", tier=0,
                        description=f"switch wave {wn} of army {aid} to {best['iid']}",
                        price=0.0, aid=aid, wave_number=wn,
                        critter_iid=best["iid"], slots=slots, gain=gain))

            # b) buy a slot: +1 slot of the current (or best fitting) critter.
            #    Deprioritized while the wave is below the current era — climb
            #    the era first instead of widening an outdated wave.
            slot_price = float(wave.get("next_slot_price", 0.0) or 0.0)
            per_slot = critter_power(cur) if cur else (
                max((critter_power(c) for c in fitting), default=0.0))
            if slot_price > 0 and per_slot > 0:
                options.append(StrengthenOption(
                    kind="buy_slot", tier=2 if below_current else 1,
                    description=f"buy slot on wave {wn} of army {aid}",
                    price=slot_price, aid=aid, wave_number=wn, gain=per_slot))

            # c) buy a wave era when a stronger critter sits above max_era. When
            #    the wave is below the current era, this is the top priority
            #    (tier 0): climb toward current-era critters before widening.
            era_price = float(wave.get("next_era_price", 0.0) or 0.0)
            reachable = [c for c in critters.values()
                         if max_era < int(c.get("era_index", 0)) <= current_era_rank]
            above = [c for c in critters.values()
                     if int(c.get("era_index", 0)) == max_era + 1]
            era_candidates = reachable if below_current else above
            if era_price > 0 and era_candidates:
                best_reach = max(era_candidates, key=critter_power)
                gain = critter_power(best_reach) * slots - max(
                    cur_power, max((critter_power(c) * slots for c in fitting), default=0.0))
                if gain > 0:
                    options.append(StrengthenOption(
                        kind="buy_wave_era", tier=0 if below_current else 1,
                        description=f"raise era of wave {wn} of army {aid}",
                        price=era_price, aid=aid, wave_number=wn, gain=gain))

    # d) add a wave only once every wave is at the current era and well-stocked
    #    with slots (prefer few strong waves over many weak ones)
    first = armies[0]
    waves = first.get("waves", [])
    if (waves and all(w.get("iid") for w in waves)
            and all(int(w.get("max_era", 0) or 0) >= current_era_rank for w in waves)
            and all(int(w.get("slots", 1) or 1) >= ADD_WAVE_MIN_SLOTS for w in waves)):
        wave_price = float(first.get("next_wave_price", 0.0) or 0.0)
        best_power = max((critter_power(c) for c in critters.values()), default=0.0)
        if wave_price > 0 and best_power > 0:
            options.append(StrengthenOption(
                kind="add_wave", tier=3,
                description=f"add wave to army {first['aid']}",
                price=wave_price, aid=int(first["aid"]), gain=best_power))

    # e) second army only once the first is substantial
    if len(armies) == 1 and len(waves) >= MIN_WAVES_FOR_SECOND_ARMY:
        army_price = float(summary.get("army_price", 0.0) or 0.0)
        if army_price > 0:
            options.append(StrengthenOption(
                kind="create_army", tier=3, description="create a second army",
                price=army_price,
                gain=max((critter_power(c) for c in critters.values()), default=1.0)))

    # Tier first (reach current era → widen → add breadth), then free-first,
    # then power gain per gold within the tier.
    options.sort(key=lambda o: (o.tier, o.price > 0,
                                -(o.gain / o.price if o.price > 0 else o.gain)))
    return options
