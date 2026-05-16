"""Persist AI battle statistics to the database for balance analysis."""

from __future__ import annotations

import json
import logging
import math
from typing import TYPE_CHECKING

from gameserver.util.eras import ERA_ORDER, ERA_LABELS_EN

if TYPE_CHECKING:
    from gameserver.engine.empire_service import EmpireService
    from gameserver.models.battle import BattleState
    from gameserver.persistence.database import Database

log = logging.getLogger(__name__)


async def log_ai_battle(
    battle: "BattleState",
    empire_service: "EmpireService",
    db: "Database",
    army_name: str,
) -> None:
    """Write one AI battle row to ai_battle_log. Errors are logged, never raised."""
    try:
        defender = battle.defender
        if defender is None:
            return

        # -- Defender era --
        era_key = empire_service.get_current_era(defender) or "stone"
        defender_era = ERA_LABELS_EN.get(era_key, era_key)

        # -- Tower distribution by era --
        towers_by_era: dict[str, int] = {}
        tower_gold = 0.0
        for s in battle.structures.values():
            item = empire_service._upgrades.get(s.iid)
            if item:
                idx = empire_service._item_era_index.get(s.iid, 0)
                label = ERA_LABELS_EN.get(ERA_ORDER[idx] if idx < len(ERA_ORDER) else "stone", "?")
                towers_by_era[label] = towers_by_era.get(label, 0) + 1
                tower_gold += item.costs.get("gold", 0.0)

        # -- Critter distribution by era --
        critters_by_era: dict[str, int] = {}
        for army in battle.armies.values():
            for wave in army.waves:
                item = empire_service._upgrades.get(wave.iid)
                slot_cost = (item.slots if item and item.slots > 0 else 1.0)
                count = math.floor(wave.slots / slot_cost)
                idx = empire_service._item_era_index.get(wave.iid, 0)
                label = ERA_LABELS_EN.get(ERA_ORDER[idx] if idx < len(ERA_ORDER) else "stone", "?")
                critters_by_era[label] = critters_by_era.get(label, 0) + count

        life_end = defender.resources.get("life", 0.0)

        await db.insert_ai_battle_log(
            bid=battle.bid,
            defender_name=defender.name,
            defender_era=defender_era,
            army_name=army_name,
            result="AI_WIN" if not battle.defender_won else "DEFENDER_WIN",
            path_length=max(0, len(battle.critter_path) - 1),
            life_start=defender.max_life,
            life_end=life_end,
            tower_count=len(battle.structures),
            tower_gold=round(tower_gold, 2),
            towers_by_era=json.dumps(towers_by_era, ensure_ascii=False),
            critters_total=battle.critters_spawned,
            critters_reached=battle.critters_reached,
            critters_killed=battle.critters_killed,
            critters_by_era=json.dumps(critters_by_era, ensure_ascii=False),
            battle_duration_s=round(battle.elapsed_ms / 1000, 1),
        )
    except Exception:
        log.exception("[AI_BATTLE_LOG] Failed to persist battle bid=%s", getattr(battle, "bid", "?"))
