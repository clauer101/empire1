"""army_pool.py — Era-classified attacking armies for balancing simulations.

Two sources:

- **Hardcoded** armies from `python_server/config/ai_waves.yaml`, classified by
  the era with the most wave slots (majority era, catalog-driven — no comment
  parsing). Many hardcoded armies mix in one or two waves of an adjacent era's
  critter (e.g. "Bronze Warriors" has a lone Iron Age PIKENEER wave among
  mostly Bronze Age waves); classifying by the single highest-era critter
  would misfile such an army entirely under the outlier era instead of the
  era it's actually representative of.
- **Random** armies from `gameserver.util.army_generator.generate_army`, the
  same generator behind `/api/ai-generator/generate`
  (`web/tools/send-ai-army.html`'s "🎲 Random Army" button).
"""

from __future__ import annotations

import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "python_server" / "src"))

from gameserver.models.army import Army, CritterWave
from gameserver.util.army_generator import (
    ERA_ORDER_INTERNAL,
    generate_army,
    parse_boss_iids,
    parse_critter_era_groups,
    parse_slot_by_iid,
)

CRITTERS_PATH = Path(__file__).resolve().parent.parent / "python_server" / "config" / "critters.yaml"


@dataclass
class AttackingArmy:
    name: str
    army: Army
    era: str
    kind: str  # "hardcoded" | "random"
    seed: int | None = None


def _wave_era(iid: str, item_era_index: dict[str, int]) -> int | None:
    return item_era_index.get(iid)


def classify_hardcoded_era(waves: list[dict[str, Any]], item_era_index: dict[str, int]) -> str | None:
    """Slot-weighted majority era across an army's waves.

    A single outlier wave (e.g. one Iron Age PIKENEER wave among mostly Bronze
    Age waves) must not decide the whole army's era — the era with the most
    wave slots wins instead. Ties fall back to the highest era among the tied
    candidates (keeps behavior deterministic and slightly favors the more
    advanced era, matching the original intent of not under-classifying).
    """
    era_slots: Counter[int] = Counter()
    for w in waves:
        idx = _wave_era((w.get("critter") or "").upper(), item_era_index)
        if idx is not None:
            era_slots[idx] += float(w.get("slots", 1))
    if not era_slots:
        return None
    max_slots = max(era_slots.values())
    best_idx = max(idx for idx, slots in era_slots.items() if slots == max_slots)
    return ERA_ORDER_INTERNAL[best_idx]


def build_hardcoded_pool(
    ai_waves: list[dict[str, Any]],
    item_era_index: dict[str, int],
    initial_wave_delay_ms: float = 15000.0,
) -> dict[str, list[AttackingArmy]]:
    """Return {era: [AttackingArmy, ...]} for every non-empty ai_waves.yaml entry."""
    pool: dict[str, list[AttackingArmy]] = {}
    aid = 1
    for entry in ai_waves:
        waves_def = entry.get("waves") or []
        if not waves_def:
            continue  # e.g. "No Army" suppression entries
        era = classify_hardcoded_era(waves_def, item_era_index)
        if era is None:
            continue
        name = entry.get("name", f"Army #{aid}")
        waves = [
            CritterWave(
                wave_id=i + 1,
                iid=(wd.get("critter") or "").upper(),
                slots=float(wd.get("slots", 1)),
                num_critters_spawned=0,
                next_critter_ms=i * initial_wave_delay_ms,
            )
            for i, wd in enumerate(waves_def)
        ]
        army = Army(aid=aid, uid=0, name=name, waves=waves)
        pool.setdefault(era, []).append(AttackingArmy(name=name, army=army, era=era, kind="hardcoded"))
        aid += 1
    return pool


def generate_random_army(
    era: str,
    ai_generator_cfg: dict[str, Any],
    seed: int,
    initial_wave_delay_ms: float = 15000.0,
    aid: int = 1,
    critters_path: Path = CRITTERS_PATH,
) -> AttackingArmy:
    """Generate one seeded random army for `era` via the shared AI army generator."""
    critter_groups = parse_critter_era_groups(critters_path)
    slot_by_iid = parse_slot_by_iid(critters_path)
    boss_iids = parse_boss_iids(critters_path)

    result = generate_army(era, ai_generator_cfg, critter_groups, slot_by_iid, seed=seed, boss_iids=boss_iids)
    name = result["name"]
    waves = [
        CritterWave(
            wave_id=i + 1,
            iid=wd["critter"].upper(),
            slots=float(wd["slots"]),
            num_critters_spawned=0,
            next_critter_ms=i * initial_wave_delay_ms,
        )
        for i, wd in enumerate(result["waves"])
    ]
    army = Army(aid=aid, uid=0, name=name, waves=waves)
    return AttackingArmy(name=name, army=army, era=era, kind="random", seed=seed)
