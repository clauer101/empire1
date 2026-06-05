"""AI service — periodic AI attacks every 8–14 hours (era-dependent).

The AI generates an army tailored to the player's current state using a
small set of tunable parameters.  After each battle the outcome is logged
with the ``[AI_ATTACK]`` tag and the parameters are adapted so the AI
converges on a 50 % win-rate against the player.

=== Heuristic overview =====================================================

1.  **Player-power score** – a single number derived from:
      • Σ effort of completed buildings  (× building_weight)
      • Σ effort of completed knowledge   (× research_weight)
      • Player's culture resource          (× culture_weight)
      • Number of structures on the map   (× tile_weight × 1 000)

2.  **Critter budget** – ``player_power × power_multiplier``

3.  **Critter selection** – available critters are split into pools:
      • *fast*    (speed ≥ 0.25)
      • *armored* (armour  > 0)
      • *normal*  (everything else)
    Pools are weighted by ``speed_bias`` / ``armor_bias`` / (1 - both).
    Within each pool the critter with the highest health is preferred
    (so the AI naturally uses era-appropriate units).

4.  **Waves** – ``wave_count`` waves are created; each wave contains
    ``ceil(budget / critter.health / wave_count)`` critters
    (clamped to [min_slots_per_wave, max_slots_per_wave]).

=== Parameter adaptation ===================================================

After every battle the AI's rolling win-rate (over the last
``history_window`` battles) is compared to ``win_rate_target`` (0.5).
If the AI wins too often ``power_multiplier`` is nudged **down** by
``adaptation_rate``; if it wins too rarely it is nudged **up**.
The multiplier is clamped to [min_power_multiplier, max_power_multiplier].

=== Logging =================================================================

Every attack is logged as::

    [AI_ATTACK] SEND  defender=<uid> power=<score> params={...} army={...}

Every outcome is logged as::

    [AI_ATTACK] RESULT defender=<uid> result=<AI_WIN|DEFENDER_WIN>
                       waves=<n> critters=<total>
                       win_rate=<rolling> power_multiplier=<old>→<new>
"""

from __future__ import annotations

import logging
import random
from collections import deque
from dataclasses import dataclass
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from gameserver.engine.attack_service import AttackService
    from gameserver.engine.empire_service import EmpireService
    from gameserver.models.army import Army
    from gameserver.models.battle import BattleState
    from gameserver.models.empire import Empire
    from gameserver.engine.upgrade_provider import UpgradeProvider

log = logging.getLogger(__name__)

# ── Constants ────────────────────────────────────────────────────────────────

AI_UID: int = 0   # Special UID reserved for the AI attacker

from gameserver.util.army_generator import BARBARIAN_NAMES  # noqa: E402


# ── Parameter dataclass ──────────────────────────────────────────────────────

@dataclass
class AIParams:
    """Tunable parameters for the AI attack heuristic.

    Attributes:
        power_multiplier:      Overall army-strength factor (adapted at runtime).
        armor_bias:            Share (0–1) of waves that use armored critters.
        speed_bias:            Share (0–1) of waves that use fast critters.
        wave_count:            Number of discrete critter waves per army.
        max_slots_per_wave:    Hard cap on critters spawned per wave.
        min_slots_per_wave:    Minimum critters per wave.

        building_weight:       Weight applied to building effort in score.
        research_weight:       Weight applied to research effort in score.
        culture_weight:        Weight applied to culture resource in score.
        tile_weight:           Weight applied to structure tile count in score.

        win_rate_target:       Target AI win-rate (0.5 = 50 %).
        adaptation_rate:       Power-multiplier adjustment per battle.
        min_power_multiplier:  Lower clamp for power_multiplier.
        max_power_multiplier:  Upper clamp for power_multiplier.
        history_window:        Rolling-window size for win-rate calculation.
    """

    # Army strength — adapted automatically
    power_multiplier: float = 1.0

    # Critter selection biases (0–1, should sum ≤ 1.0)
    armor_bias: float = 0.30
    speed_bias: float = 0.20

    # Wave layout
    wave_count: int = 3
    max_slots_per_wave: int = 20
    min_slots_per_wave: int = 2

    # Player assessment weights
    building_weight: float = 1.0
    research_weight: float = 0.8
    culture_weight: float = 0.015
    tile_weight: float = 0.8

    # Adaptation
    win_rate_target: float = 0.50
    adaptation_rate: float = 0.08
    min_power_multiplier: float = 0.2
    max_power_multiplier: float = 5.0
    history_window: int = 10


# ── AIService ────────────────────────────────────────────────────────────────

class AIService:
    """Periodic AI attacker with adaptive army generation.

    Args:
        upgrade_provider: Item database for critter lookups.
    """

    def __init__(
        self,
        upgrade_provider: UpgradeProvider,
        game_config: Any = None,
        hardcoded_waves: list[dict[str, Any]] | None = None,
    ) -> None:
        self._upgrades = upgrade_provider
        from gameserver.loaders.game_config_loader import GameConfig as _GC
        self._game_config: _GC = game_config or _GC()
        self._hardcoded_waves: list[dict[str, Any]] = hardcoded_waves or []
        self._params = AIParams()
        # Army IDs are now allocated globally via empire_service.next_army_id()
        # deque of bool: True = AI won, False = defender won
        self._history: deque[bool] = deque(maxlen=self._params.history_window)
        # Pending battles: attack_id → {defender_uid, army_summary}
        self._pending: dict[int, dict[str, Any]] = {}
        # Barbarian attack ticker
        self._barbarian_elapsed_s: float = 0.0
        self._BARBARIAN_INTERVAL_S: float = 60.0
        self._log_barbarian_mean_times()

    # -- Public API --------------------------------------------------------

    def on_item_completed(
        self,
        empire_uid: int,
        iid: str,
        empire_service: "EmpireService",
        attack_service: "AttackService",
    ) -> None:
        """Called once when an empire completes a building or research item.

        If a hardcoded wave in ai_waves.yaml has this item in its trigger list,
        those armies are dispatched. Otherwise a random number of era-appropriate
        adaptive armies is sent based on the chance_triggered_* weights in game.yaml.
        """
        empire = empire_service.get(empire_uid)
        if empire is None:
            return

        if self._is_suppressed_item(iid):
            log.info("[AI_ATTACK] Item '%s' completed for defender=%d — suppressed (no-spawn entry)", iid, empire_uid)
            return

        matches = self._match_waves_for_item(empire, iid, empire_service=empire_service)
        if matches:
            for army, travel_s in matches:
                self._send_army(empire_uid, empire, empire_service, attack_service, army, travel_s)
        else:
            self._trigger_random_armies(empire_uid, empire, empire_service, attack_service, iid)

    def trigger_attacks(
        self,
        empire_service: EmpireService,
        attack_service: AttackService,
    ) -> None:
        """Launch one adaptive AI attack against every human player empire.

        Kept for external use; not called by the game loop anymore.
        """
        for uid, empire in list(empire_service.all_empires.items()):
            if uid == AI_UID:
                continue
            self._attack_player(uid, empire, empire_service, attack_service)

    def on_battle_result(
        self,
        attack_id: int,
        battle: BattleState,
    ) -> None:
        """Record the outcome of an AI-initiated battle and adapt parameters.

        Called from the battle-task cleanup in handlers.py after the battle ends.
        """
        info = self._pending.pop(attack_id, None)
        if info is None:
            return

        defender_uid = info["defender_uid"]
        # AI wins when the defender LOST (defender_won is False)
        ai_won = battle.defender_won is False
        self._history.append(ai_won)

        win_rate = sum(self._history) / len(self._history) if self._history else 0.5

        # Adapt power_multiplier toward win_rate_target
        old_mult = self._params.power_multiplier
        if win_rate > self._params.win_rate_target + 0.05:
            # AI wins too often → weaken it
            self._params.power_multiplier = max(
                self._params.min_power_multiplier,
                old_mult - self._params.adaptation_rate,
            )
        elif win_rate < self._params.win_rate_target - 0.05:
            # AI loses too often → strengthen it
            self._params.power_multiplier = min(
                self._params.max_power_multiplier,
                old_mult + self._params.adaptation_rate,
            )

        total_critters = sum(w.slots for w in (battle.army.waves if battle.army else []))

        log.info(
            "[AI_ATTACK] RESULT defender=%d result=%s waves=%d critters=%d "
            "win_rate=%.2f power_multiplier=%.3f→%.3f params=%s",
            defender_uid,
            "AI_WIN" if ai_won else "DEFENDER_WIN",
            len(battle.army.waves) if battle.army else 0,
            total_critters,
            win_rate,
            old_mult,
            self._params.power_multiplier,
            _params_summary(self._params),
        )

    def cleanup_inactive_armies(
        self,
        empire_service: "EmpireService",
        attack_service: "AttackService",
    ) -> None:
        """Remove AI armies that have no active (non-FINISHED) attack."""
        from gameserver.models.attack import AttackPhase

        ai_empire = empire_service.get(AI_UID)
        if not ai_empire:
            return

        active_aids = {
            a.army_aid
            for a in attack_service.get_all_attacks()
            if a.attacker_uid == AI_UID and a.phase != AttackPhase.FINISHED
        }
        before = len(ai_empire.armies)
        ai_empire.armies = [a for a in ai_empire.armies if a.aid in active_aids]
        removed = before - len(ai_empire.armies)
        if removed:
            log.info("[AI] Cleaned up %d inactive AI armies", removed)

    # -- Internals ---------------------------------------------------------

    def _send_army(
        self,
        defender_uid: int,
        empire: Empire,
        empire_service: EmpireService,
        attack_service: AttackService,
        army: Army,
        travel_seconds: float | None = None,
    ) -> None:
        """Register *army* with the AI empire and dispatch the attack."""
        from gameserver.models.empire import Empire as EmpireModel

        # Assign globally unique army ID
        army.aid = empire_service.next_army_id()

        ai_empire = empire_service.get(AI_UID)
        if ai_empire is None:
            ai_empire = EmpireModel(uid=AI_UID, name="AI")
            empire_service.register(ai_empire)

        self.cleanup_inactive_armies(empire_service, attack_service)
        ai_empire.armies.append(army)

        army_summary = {
            "waves": [{"iid": w.iid, "slots": w.slots} for w in army.waves],
            "total_critters": sum(w.slots for w in army.waves),
        }

        log.info(
            "[AI_ATTACK] SEND defender=%d army=%s",
            defender_uid,
            army_summary,
        )

        travel_s = (
            travel_seconds
            if travel_seconds is not None
            else (self._game_config.ai_travel_seconds if self._game_config else 30.0)
        )

        attack = attack_service.start_ai_attack(
            defender_uid=defender_uid,
            army=army,
            travel_seconds=travel_s,
        )
        if isinstance(attack, str):
            log.error("[AI_ATTACK] FAILED to start attack: %s", attack)
            return

        self._pending[attack.attack_id] = {
            "defender_uid": defender_uid,
            "army_summary": army_summary,
        }

    def _attack_player(
        self,
        defender_uid: int,
        empire: Empire,
        empire_service: EmpireService,
        attack_service: AttackService,
        army_name: str = "AI Assault",
    ) -> None:
        """Generate an adaptive army and dispatch it (used by trigger_attacks)."""
        player_power = self._assess_player(empire)
        result = self._build_army(empire, player_power, army_name=army_name,
                                  empire_service=empire_service)
        if not result:
            log.warning(
                "[AI_ATTACK] No critters available for defender=%d — skipping",
                defender_uid,
            )
            return
        army, travel_s = result
        log.info(
            "[AI_ATTACK] '%s' for defender=%d power=%.1f params=%s",
            army_name, defender_uid, player_power, _params_summary(self._params),
        )
        self._send_army(defender_uid=defender_uid, empire=empire,
                        empire_service=empire_service,
                        attack_service=attack_service, army=army,
                        travel_seconds=travel_s)

    def _trigger_random_armies(
        self,
        defender_uid: int,
        empire: "Empire",
        empire_service: "EmpireService",
        attack_service: "AttackService",
        triggered_by_iid: str,
    ) -> None:
        """Dispatch 1–4 random era-appropriate armies from ai_waves.yaml.

        The count is drawn from a weighted distribution defined by the
        chance_triggered_* fields in game.yaml. Armies are selected from
        hardcoded entries whose critters primarily belong to the player's
        current era. travel_time is read directly from each yaml entry.
        If all weights are zero the feature is disabled.
        """
        cfg = self._game_config
        if cfg is None:
            return

        weights = [
            getattr(cfg, "chance_triggered_one_army", 5),
            getattr(cfg, "chance_triggered_two_armies", 4),
            getattr(cfg, "chance_triggered_three_armies", 1),
            getattr(cfg, "chance_triggered_four_armies", 0),
        ]
        if sum(weights) == 0:
            return

        item_details = (self._upgrades.items if self._upgrades else {}).get(triggered_by_iid.upper())
        era_internal = item_details.era if item_details and item_details.era else empire_service.get_current_era(empire)
        candidates = self._hardcoded_armies_for_era(era_internal)
        if not candidates:
            return

        army_count: int = random.choices([1, 2, 3, 4], weights=weights)[0]
        log.info(
            "[AI_ATTACK] Item '%s' completed for defender=%d era=%s → %d triggered army attack(s) "
            "(%d candidates)",
            triggered_by_iid, defender_uid, era_internal, army_count, len(candidates),
        )

        from gameserver.models.army import Army, CritterWave
        initial_delay_ms = cfg.initial_wave_delay_ms

        for _ in range(army_count):
            entry = random.choice(candidates)
            army_def = entry.get("waves") or []
            if not army_def:
                continue

            waves: list[CritterWave] = []
            for i, wave_def in enumerate(army_def):
                critter_iid = wave_def.get("critter", "")
                slots = wave_def.get("slots", 1)
                waves.append(CritterWave(
                    wave_id=i + 1,
                    iid=critter_iid.upper() if critter_iid else critter_iid,
                    slots=float(slots),
                    num_critters_spawned=0,
                    next_critter_ms=int(i * initial_delay_ms),
                ))

            explicit_travel = float(entry.get("travel_time", 0) or 0)
            travel_s = explicit_travel if explicit_travel else self._era_travel_seconds(empire, empire_service)

            army = Army(aid=0, uid=AI_UID, name=entry.get("name", "AI Assault"), waves=waves)
            self._send_army(defender_uid, empire, empire_service, attack_service, army, travel_s)

    def _hardcoded_armies_for_era(self, era_internal: str) -> "list[dict[str, Any]]":
        """Return hardcoded army entries whose critters are primarily from *era_internal*.

        Uses the dominant era (most total slots) of each army to classify it.
        Falls back to a broader search (≤ player era) if no exact match exists.
        """
        import os
        from pathlib import Path
        from gameserver.util.army_generator import parse_critter_era_groups, ERA_ORDER_INTERNAL

        config_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..", "config")
        critters_yaml = Path(config_dir) / "critters.yaml"
        try:
            era_groups = parse_critter_era_groups(critters_yaml)
        except Exception:
            log.warning("[AI_ATTACK] Could not parse critters.yaml for era classification")
            return self._hardcoded_waves

        # Reverse map: UPPER_IID → era_internal
        critter_to_era: dict[str, str] = {
            iid.upper(): era
            for era, iids in era_groups.items()
            for iid in iids
        }

        era_idx = ERA_ORDER_INTERNAL.index(era_internal) if era_internal in ERA_ORDER_INTERNAL else 0

        def dominant_era_idx(entry: "dict[str, Any]") -> int:
            slots_by_era: dict[str, float] = {}
            for wave_def in entry.get("waves") or []:
                iid = (wave_def.get("critter") or "").upper()
                era = critter_to_era.get(iid, ERA_ORDER_INTERNAL[0])
                slots_by_era[era] = slots_by_era.get(era, 0.0) + float(wave_def.get("slots", 1))
            if not slots_by_era:
                return 0
            dominant = max(slots_by_era, key=lambda e: slots_by_era[e])
            return ERA_ORDER_INTERNAL.index(dominant) if dominant in ERA_ORDER_INTERNAL else 0

        exact = [e for e in self._hardcoded_waves if dominant_era_idx(e) == era_idx]
        if exact:
            return exact

        # No exact match → fall back to closest available era
        broader = [e for e in self._hardcoded_waves if dominant_era_idx(e) <= era_idx]
        return broader or self._hardcoded_waves

    def _era_travel_seconds(self, empire: "Empire", empire_service: "EmpireService") -> float:
        """Return the era-appropriate travel time for an AI attack targeting *empire*.

        Reads ``era_effects[era_key].travel_offset`` from game_config — the same
        value that human attackers in that era would use.  Falls back to
        ``base_travel_offset`` if the era has no travel_offset configured.
        """
        if not self._game_config:
            return 30.0
        era_key = empire_service.get_current_era(empire)  # lowercase English e.g. "middle_ages"
        travel = getattr(self._game_config, f"{era_key}_travel_offset", None)
        if travel is not None:
            return float(travel)
        return float(getattr(self._game_config, "base_travel_offset", 300.0))

    def _assess_player(self, empire: Empire) -> float:
        """Compute a scalar 'player power' score from the empire's current state.

        Combines building effort, research effort, culture resource, and
        the number of defensive structures on the map.
        """
        items = self._upgrades.items if self._upgrades else {}
        p = self._params

        # Completed buildings
        building_score = sum(
            items[iid].effort
            for iid, remaining in empire.buildings.items()
            if iid in items and remaining == 0.0
        ) * p.building_weight

        # Completed research
        research_score = sum(
            items[iid].effort
            for iid, remaining in empire.knowledge.items()
            if iid in items and remaining == 0.0
        ) * p.research_weight

        # Culture resource
        culture_score = empire.resources.get("culture", 0.0) * p.culture_weight

        # Structure tiles on the hex map (proxy for defensive strength)
        structure_tiles = 0
        if empire.hex_map:
            for tile_type in empire.hex_map.values():
                if isinstance(tile_type, dict):
                    tile_type = tile_type.get("type", "")
                if tile_type not in {
                    "empty", "path", "spawnpoint", "castle", "blocked", "void"
                }:
                    structure_tiles += 1
        tile_score = structure_tiles * 1_000.0 * p.tile_weight

        total = building_score + research_score + culture_score + tile_score
        return max(total, self._game_config.ai_min_player_score)

    def _is_suppressed_item(self, iid: str) -> bool:
        """Return True if a hardcoded entry with empty waves claims this iid as its trigger."""
        iid_upper = iid.upper()
        for entry in self._hardcoded_waves:
            trigger = entry.get("trigger") or {}
            req_items = trigger.get("items") or []
            if iid_upper in [x.upper() for x in req_items]:
                if not entry.get("waves"):
                    return True
        return False

    def _match_waves_for_item(
        self,
        empire: "Empire",
        completed_iid: str,
        empire_service: "EmpireService | None" = None,
    ) -> "list[tuple[Army, float]]":
        """Return all Army entries whose trigger list contains *completed_iid*
        AND whose full trigger conditions are met.
        """
        if not self._hardcoded_waves:
            return []

        from gameserver.models.army import Army, CritterWave

        results = []
        for entry in self._hardcoded_waves:
            name = entry.get("name", "")

            trigger = entry.get("trigger") or {}
            req_items = trigger.get("items") or []

            iid_upper = completed_iid.upper()
            if iid_upper not in [x.upper() for x in req_items]:
                continue

            army_def = entry.get("waves") or []
            if not army_def:
                continue

            waves: list[CritterWave] = []
            for i, wave_def in enumerate(army_def):
                critter_iid = wave_def.get("critter", "")
                slots = wave_def.get("slots", 1)
                waves.append(CritterWave(
                    wave_id=i + 1,
                    iid=critter_iid.upper() if critter_iid else critter_iid,
                    slots=float(slots),
                    num_critters_spawned=0,
                    next_critter_ms=0,
                ))

            initial_delay_ms = self._game_config.initial_wave_delay_ms
            for i, wave in enumerate(waves):
                wave.next_critter_ms = int(i * initial_delay_ms)

            aid = 0  # assigned in _send_army via empire_service.next_army_id()
            explicit_travel = float(entry.get("travel_time", 0) or 0)
            if explicit_travel:
                travel_s = explicit_travel
            elif empire_service is not None:
                travel_s = self._era_travel_seconds(empire, empire_service)
            else:
                travel_s = self._game_config.ai_travel_seconds if self._game_config else 30.0
            log.info(
                "[AI_ATTACK] Wave '%s' triggered by iid=%s for empire=%s travel=%.0fs",
                name, completed_iid, empire.uid, travel_s,
            )
            results.append((Army(aid=aid, uid=AI_UID, name=name, waves=waves), travel_s))

        return results

    def _match_hardcoded_wave(self, empire: "Empire",
                              empire_service: "EmpireService | None" = None) -> "tuple[Army, float] | None":
        """Return (Army, travel_seconds) for the last matching hardcoded wave entry,
        or None if no entry matches."""
        if not self._hardcoded_waves:
            return None

        from gameserver.models.army import Army, CritterWave

        completed_all: set[str] = {
            iid for iid, r in {**empire.buildings, **empire.knowledge}.items() if r == 0.0
        }
        last_match = None
        for entry in self._hardcoded_waves:
            trigger = entry.get("trigger") or {}
            req_items = trigger.get("items") or []

            if not all(x in completed_all for x in req_items):
                continue
            last_match = entry

        if last_match is None:
            return None

        army_def = last_match.get("waves") or []
        if not army_def:
            return None

        waves: list[CritterWave] = []
        for i, wave_def in enumerate(army_def):
            critter_iid = wave_def.get("critter", "")
            slots = wave_def.get("slots", 1)
            waves.append(CritterWave(
                wave_id=i + 1,
                iid=critter_iid.upper() if critter_iid else critter_iid,
                slots=int(slots),
                num_critters_spawned=0,
                next_critter_ms=0,
            ))

        # Apply wave timing using initial_wave_delay_ms (no player effects)
        initial_delay_ms = (
            self._game_config.initial_wave_delay_ms if self._game_config else 15000.0
        )
        for i, wave in enumerate(waves):
            wave.next_critter_ms = int(i  * initial_delay_ms)  # first wave zero delay

        aid = 0  # assigned in _send_army via empire_service.next_army_id()
        name = last_match.get("name", "Hardcoded Attack")
        explicit_travel = float(last_match.get("travel_time", 0) or 0)
        if explicit_travel:
            travel_s = explicit_travel
        else:
            # Use era-specific travel_time from ai_generator config (same as _build_army)
            era_internal = empire_service.get_current_era(empire) if empire_service else "stone"
            era_cfg = getattr(self._game_config, "ai_generator", {}).get(era_internal, {})
            travel_s = float(era_cfg.get("travel_time", 0) or 0)
            if not travel_s:
                if empire_service is not None:
                    travel_s = self._era_travel_seconds(empire, empire_service)
                else:
                    travel_s = self._game_config.ai_travel_seconds if self._game_config else 30.0
        log.info("[AI_ATTACK] Using hardcoded wave '%s' for defender uid=%s travel=%.0fs", name, empire.uid, travel_s)
        return Army(aid=aid, uid=AI_UID, name=name, waves=waves), travel_s

    def _build_army(self, empire: Empire, player_power: float, army_name: str = "AI Assault",
                    empire_service: "EmpireService | None" = None) -> "tuple[Army, float] | None":
        """Construct a random era-appropriate Army using the shared army_generator logic."""
        from gameserver.models.army import Army, CritterWave
        from gameserver.util.army_generator import (
            generate_army, parse_critter_era_groups, parse_slot_by_iid,
        )
        import os

        era_internal = empire_service.get_current_era(empire) if empire_service else "stone"

        # Load critter data from config
        config_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..", "config")
        from pathlib import Path
        critters_yaml = Path(config_dir) / "critters.yaml"
        try:
            critter_era_groups = parse_critter_era_groups(critters_yaml)
            slot_by_iid = parse_slot_by_iid(critters_yaml)
        except (OSError, KeyError, ValueError, TypeError):
            log.exception("Failed to parse critters.yaml for AI wave generation")
            return None

        ai_generator_cfg = getattr(self._game_config, "ai_generator", {})

        try:
            result = generate_army(
                era_internal=era_internal,
                ai_generator_cfg=ai_generator_cfg,
                critter_era_groups=critter_era_groups,
                slot_by_iid=slot_by_iid,
                name=army_name if army_name != "AI Assault" else None,
            )
        except ValueError as exc:
            log.warning("[AI_ATTACK] army generation failed: %s", exc)
            return None

        waves: list[CritterWave] = []
        initial_delay_ms = self._game_config.initial_wave_delay_ms
        for i, w in enumerate(result["waves"]):
            waves.append(CritterWave(
                wave_id=i + 1,
                iid=w["critter"].upper(),
                slots=w["slots"],
                num_critters_spawned=0,
                next_critter_ms=int(i * initial_delay_ms),
            ))

        # Travel time from ai_generator config for this era
        era_cfg = ai_generator_cfg.get(era_internal, {})
        travel_s = float(era_cfg.get("travel_time", 0) or 0)
        log.info("[AI_ATTACK] travel debug: era_internal=%s era_cfg=%s travel_s=%s", era_internal, era_cfg, travel_s)
        if not travel_s:
            if empire_service is not None:
                travel_s = self._era_travel_seconds(empire, empire_service)
            else:
                travel_s = self._game_config.ai_travel_seconds if self._game_config else 30.0

        return Army(aid=0, uid=AI_UID, name=result["name"], waves=waves), travel_s

    # -- Barbarian periodic attacks ----------------------------------------

    def _log_barbarian_mean_times(self) -> None:
        """Log the expected mean time between barbarian attacks per era at startup."""
        cfg = self._game_config
        aggr = getattr(cfg, "barbarians_aggressiveness", {}) if cfg else {}
        if not aggr:
            log.info("[BARBARIANS] No aggressiveness config — barbarian attacks disabled")
            return
        log.info("[BARBARIANS] Mean time between attacks per era (interval=%ds):", self._BARBARIAN_INTERVAL_S)
        for era_key, p in aggr.items():
            if p > 0:
                mean_s = self._BARBARIAN_INTERVAL_S / p
                log.info("  %-14s  p=%.2f  →  mean %.0f s  (%.1f min)", era_key, p, mean_s, mean_s / 60)
            else:
                log.info("  %-14s  p=0.00  →  disabled", era_key)

    def tick_barbarians(
        self,
        dt: float,
        empire_service: "EmpireService",
        attack_service: "AttackService",
    ) -> None:
        """Called every game tick. Every 60 s, rolls a Bernoulli trial per player (p from barbarians_aggressiveness). Mean attack interval: ~8–14 h depending on era."""
        self._barbarian_elapsed_s += dt
        if self._barbarian_elapsed_s < self._BARBARIAN_INTERVAL_S:
            return
        self._barbarian_elapsed_s -= self._BARBARIAN_INTERVAL_S

        cfg = self._game_config
        aggr: dict[str, float] = getattr(cfg, "barbarians_aggressiveness", {}) if cfg else {}
        if not aggr:
            return

        for uid, empire in list(empire_service.all_empires.items()):
            if uid == AI_UID:
                continue

            era_key = empire_service.get_current_era(empire)   # lowercase English e.g. "middle_ages"
            p = aggr.get(era_key, 0.0)

            if p <= 0.0:
                continue

            if random.random() < p:
                name = random.choice(BARBARIAN_NAMES)
                log.info(
                    "[BARBARIANS] '%s' triggered for player=%d era=%s p=%.4f",
                    name, uid, era_key, p,
                )
                self._attack_player(uid, empire, empire_service, attack_service,
                                    army_name=name)

    # -- Legacy stubs (kept for API compatibility) -------------------------

    def get_difficulty_tier(self, effort_level: float) -> str:
        """Return a difficulty tier label for the given effort score."""
        if effort_level < 500:
            return "easy"
        if effort_level < 5_000:
            return "medium"
        if effort_level < 30_000:
            return "hard"
        return "elite"

    def generate_army(self, effort_level: float) -> Army | None:
        """Legacy stub — use trigger_attacks instead."""
        return None


# ── Helpers ───────────────────────────────────────────────────────────────────

def _params_summary(p: AIParams) -> str:
    """Return a compact string representation of current AI parameters."""
    return (
        f"{{mult={p.power_multiplier:.3f} armor={p.armor_bias:.2f} "
        f"speed={p.speed_bias:.2f} waves={p.wave_count}}}"
    )
