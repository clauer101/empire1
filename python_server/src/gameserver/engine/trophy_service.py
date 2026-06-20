"""Trophy service — award and query persistent player trophies."""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING, Any

from gameserver.models.items import ItemDetails, ItemType

if TYPE_CHECKING:
    from gameserver.persistence.database import Database
    from gameserver.engine.upgrade_provider import UpgradeProvider
    from gameserver.engine.empire_service import EmpireService
    from gameserver.models.empire import Empire

log = logging.getLogger(__name__)

# Condition types that map directly to an empire_stats column (value >= threshold)
_DIRECT_STAT_CONDITIONS: frozenset[str] = frozenset({
    "attacks_won_ai",
    "attacks_won_human",
    "defense_won_ai",
    "defense_won_human",
    "artifacts_stolen",
    "spies_sent",
    "culture_won",
    "culture_stolen",
    "research_won",
    "research_stolen",
    "longest_battle_ms",
    "coward_attacks",
    "max_lucky_punch_levels",
    "max_artifacts_stolen_one_battle",
    "max_artifacts_lost_one_battle",
})


class TrophyService:
    """Checks trophy conditions and awards trophies to players."""

    def __init__(
        self,
        database: "Database",
        upgrade_provider: "UpgradeProvider",
        empire_service: "EmpireService | None" = None,
    ) -> None:
        self._database = database
        self._upgrade_provider = upgrade_provider
        self._empire_service = empire_service

    def _trophies(self) -> list[ItemDetails]:
        return [
            item for item in self._upgrade_provider.items.values()
            if item.item_type == ItemType.TROPHY
        ]

    def _check_condition(
        self,
        condition: dict[str, Any],
        stats: dict[str, Any],
        empire: "Empire | None",
        era_firsts: dict[str, int] | None = None,
        all_trophy_iids: set[str] | None = None,
    ) -> bool:
        ctype = condition.get("type", "")
        threshold = condition.get("threshold", 1)

        # --- Legacy combined counters (still supported) ---
        if ctype == "defense_won":
            total = (stats.get("defense_won_human") or 0) + (stats.get("defense_won_ai") or 0)
            return total >= int(threshold)
        if ctype == "attacks_won":
            total = (stats.get("attacks_won_human") or 0) + (stats.get("attacks_won_ai") or 0)
            return total >= int(threshold)
        if ctype == "critters_killed":
            return (stats.get("critters_killed") or 0) >= int(threshold)
        if ctype == "hexes_owned":
            if empire is None:
                return False
            return len(empire.hex_map) >= int(threshold)

        # --- Direct per-season stat column ---
        if ctype in _DIRECT_STAT_CONDITIONS:
            val = stats.get(ctype) or 0
            return float(val) >= float(threshold)

        # --- Live / snapshot conditions ---
        if ctype == "ruler_level":
            if empire is None or self._empire_service is None:
                return False
            level = self._empire_service.ruler_level_from_xp(empire.ruler.xp if empire.ruler else 0.0)
            return level >= int(threshold)

        if ctype == "path_length":
            if empire is None:
                return False
            from gameserver.engine.hex_pathfinding import find_path_from_spawn_to_castle
            path = find_path_from_spawn_to_castle(empire.hex_map) or []
            return len(path) >= int(threshold)

        if ctype == "first_in_era":
            if empire is None or era_firsts is None:
                return False
            era_key = condition.get("era", "")
            return era_firsts.get(era_key) == empire.uid

        # --- Meta conditions ---
        if ctype == "all_era_firsts":
            if empire is None:
                return False
            era_first_trophies = [
                t for t in self._trophies()
                if t.condition.get("type") == "first_in_era"
            ]
            return all(t.iid in empire.trophies for t in era_first_trophies)

        if ctype == "all_trophies":
            if empire is None:
                return False
            meta_types = {"all_era_firsts", "all_trophies"}
            non_meta = [
                t for t in self._trophies()
                if t.condition.get("type") not in meta_types
            ]
            return all(t.iid in empire.trophies for t in non_meta)

        log.warning("Unknown trophy condition type: %s", ctype)
        return False

    async def check_and_award(
        self, uid: int, empire: "Empire | None" = None
    ) -> list[str]:
        """Check all trophies for uid and award newly met ones.

        Writes newly awarded trophies to both the DB and empire.trophies so
        recalculate_effects can pick them up synchronously.

        Returns list of newly awarded IIDs.
        """
        if empire is None:
            return []
        already_earned = set(empire.trophies.keys())
        unearned = [t for t in self._trophies() if t.iid not in already_earned]
        if not unearned:
            return []

        from gameserver.engine.global_state import get_season_number
        stats = await self._database.get_empire_stats(uid) or {}
        era_firsts_rows = await self._database.get_era_firsts()
        era_firsts: dict[str, int] = {r["era_key"]: r["uid"] for r in era_firsts_rows}
        now = int(time.time())
        season = get_season_number()
        newly_awarded: list[str] = []

        # Check non-meta trophies first so meta conditions see fresh state
        non_meta = [t for t in unearned if t.condition.get("type") not in ("all_era_firsts", "all_trophies")]
        meta = [t for t in unearned if t.condition.get("type") in ("all_era_firsts", "all_trophies")]

        for trophy in non_meta + meta:
            if trophy.iid in empire.trophies:
                continue  # may have been just awarded in this loop
            if self._check_condition(trophy.condition, stats, empire, era_firsts):
                await self._database.award_trophy(uid, trophy.iid, now, season)
                empire.trophies[trophy.iid] = {"earned_at": now, "season": season}
                newly_awarded.append(trophy.iid)
                log.info("Trophy awarded: uid=%d iid=%s season=%d", uid, trophy.iid, season)

        return newly_awarded

    async def load_trophies_into_empire(self, uid: int, empire: "Empire") -> None:
        """Populate empire.trophies from DB on server startup / state restore."""
        rows = await self._database.get_trophy_rows(uid)
        for row in rows:
            iid = row["iid"]
            if iid not in empire.trophies:
                empire.trophies[iid] = {
                    "earned_at": row.get("earned_at", 0),
                    "season": row.get("season", 1),
                }

    async def get_trophy_rows(self, uid: int, empire: "Empire | None" = None) -> list[dict[str, Any]]:
        """Return full trophy data for the REST endpoint."""
        rows = await self._database.get_trophy_rows(uid)
        empire_map = empire.trophies if empire is not None else {}
        result: list[dict[str, Any]] = []
        for row in rows:
            item = self._upgrade_provider.items.get(row["iid"])
            if item is None:
                continue
            empire_entry = empire_map.get(row["iid"], {})
            result.append({
                "iid": item.iid,
                "name": item.name,
                "image": item.image,
                "description": item.description,
                "earned_at": row["earned_at"],
                "season": empire_entry.get("season", row.get("season", 1)),
                "effects": item.effects,
            })
        return result
