"""Shared army generation logic used by both ai_service and the FastAPI web server.

Generates era-appropriate random AI armies using game.yaml ai_generator config
and critters.yaml era groupings.
"""

from __future__ import annotations

import random
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

BARBARIAN_NAMES: list[str] = [
    "Rude Barbarians", "Lazy Raiders", "Angry Mob", "Wandering Pillagers",
    "Grumpy Marauders", "Desperate Looters", "Hungry Invaders", "Rowdy Plunderers",
    "Clumsy Attackers", "Ragged Warband", "Restless Horde", "Drunken Raiders",
    "Bored Mercenaries", "Petty Bandits", "Disorganized Mob", "Frenzied Pillagers",
    "Crude Invaders", "Savage Rabble", "Muddy Marauders", "Stubborn Raiders",
    "Shrieking Horde", "Reckless Looters", "Forgotten Warband", "Blundering Invaders",
    "Howling Savages", "Rampaging Rabble", "Weary Plunderers", "Unlucky Raiders",
    "Noisy Barbarians", "Relentless Mob",
]

# ── Era definitions ───────────────────────────────────────────────────────────

# Era order — lowercase English, canonical format (matches ERA_ORDER in eras.py)
ERA_ORDER_INTERNAL: list[str] = [
    "stone", "neolithic", "bronze", "iron",
    "middle_ages", "renaissance", "industrial", "modern", "future",
]

# Alias kept for backward compatibility; identical to ERA_ORDER_INTERNAL
ERA_BACKEND_TO_INTERNAL: dict[str, str] = {k: k for k in ERA_ORDER_INTERNAL}

# ── Critter YAML parsing ──────────────────────────────────────────────────────

def parse_critter_era_groups(critters_yaml: Path) -> dict[str, list[str]]:
    """Return {era_key: [iid, ...]} from critters.yaml era: fields."""
    import yaml as _yaml
    result: dict[str, list[str]] = {k: [] for k in ERA_ORDER_INTERNAL}
    try:
        data = _yaml.safe_load(critters_yaml.read_text(encoding="utf-8")) or {}
    except OSError:
        return result
    for iid, item in data.items():
        if not isinstance(item, dict):
            continue
        era = item.get("era", ERA_ORDER_INTERNAL[0])
        if era in result:
            result[era].append(iid)
    return result


def parse_slot_by_iid(critters_yaml: Path) -> dict[str, int]:
    """Return {iid: slot_cost} from critters.yaml."""
    import yaml
    data = yaml.safe_load(critters_yaml.read_text(encoding="utf-8")) or {}
    return {iid: max(1, int(v.get("slots", 1))) for iid, v in data.items() if isinstance(v, dict)}


# ── Army generation ───────────────────────────────────────────────────────────

def generate_army(
    era_internal: str,
    ai_generator_cfg: dict,
    critter_era_groups: dict[str, list[str]],
    slot_by_iid: dict[str, int],
    seed: int | None = None,
    name: str | None = None,
) -> dict:
    """Generate a random army for the given internal era key.

    Args:
        era_internal: Internal era key, e.g. "renaissance".
        ai_generator_cfg: The ai_generator section from game.yaml (dict of era → params).
        critter_era_groups: {internal_era_key: [iid, ...]} from critters.yaml.
        slot_by_iid: {iid: slot_cost} lookup.
        seed: Optional RNG seed. Uses random.randint if None.
        name: Optional army name override.

    Returns:
        dict with keys: name, waves (list of {critter, slots}), era_internal, seed.
    """
    if seed is None:
        seed = random.randint(0, 99999)

    cfg = ai_generator_cfg.get(era_internal, {})
    min_waves    = cfg.get("min_waves",        2)
    max_waves    = cfg.get("max_waves",        4)
    min_slots    = cfg.get("min_slots",        10)
    max_slots    = cfg.get("max_slots",        20)
    min_prev     = max(0, cfg.get("min_previous_era", 0))
    max_prev     = max(0, cfg.get("max_previous_era", 0))
    min_next     = max(0, cfg.get("min_next_era",     0))
    max_next_era = max(0, cfg.get("max_next_era",     0))

    era_idx = ERA_ORDER_INTERNAL.index(era_internal) if era_internal in ERA_ORDER_INTERNAL else -1
    if era_idx < 0:
        raise ValueError(f"Unknown era: {era_internal!r}")

    main_pool = critter_era_groups.get(era_internal, [])
    if not main_pool:
        raise ValueError(f"No critters defined for era: {era_internal!r}")
    prev_pool = critter_era_groups.get(ERA_ORDER_INTERNAL[era_idx - 1], []) if era_idx > 0 else []
    next_pool = critter_era_groups.get(ERA_ORDER_INTERNAL[era_idx + 1], []) if era_idx < len(ERA_ORDER_INTERNAL) - 1 else []

    rng = _mulberry32(seed)

    def rand_int(lo: int, hi: int) -> int:
        lo = max(0, lo)
        hi = max(lo, hi)
        return lo + int(rng() * (hi - lo + 1))

    def make_wave(pool: list[str]) -> dict:
        iid = pool[int(rng() * len(pool))]
        slot_unit = slot_by_iid.get(iid, 1)
        raw_s = min_slots + rng() * (max_slots - min_slots)
        slots = max(slot_unit, round(raw_s / slot_unit) * slot_unit)
        return {"critter": iid, "slots": slots}

    num_waves = rand_int(min_waves, max_waves)
    num_prev  = min(rand_int(min_prev, max_prev), num_waves)
    num_next  = min(rand_int(min_next, max_next_era), num_waves - num_prev)
    num_main  = num_waves - num_prev - num_next

    waves: list[dict] = []
    for _ in range(num_main):
        waves.append(make_wave(main_pool))
    for _ in range(num_prev):
        waves.append(make_wave(prev_pool or main_pool))
    for _ in range(num_next):
        waves.append(make_wave(next_pool or main_pool))

    # Fisher-Yates shuffle
    for i in range(len(waves) - 1, 0, -1):
        j = int(rng() * (i + 1))
        waves[i], waves[j] = waves[j], waves[i]

    if name is None:
        name = BARBARIAN_NAMES[int(rng() * len(BARBARIAN_NAMES)) % len(BARBARIAN_NAMES)]

    return {"name": name, "waves": waves, "era_internal": era_internal, "seed": seed}


# ── Seeded RNG (matches JS Mulberry32 in ai_generator.html) ──────────────────

def _mulberry32(seed: int):
    s = [int(seed) & 0xFFFFFFFF or 1]

    def u32(x: int) -> int:
        return int(x) & 0xFFFFFFFF

    def rng() -> float:
        s[0] += 0x6D2B79F5
        sv = u32(s[0])
        t = u32(u32(sv ^ (sv >> 15)) * u32(1 | sv))
        t = u32(t ^ u32(t + u32(u32(t ^ (t >> 7)) * u32(61 | t))))
        return u32(t ^ (t >> 14)) / 4294967296

    return rng
