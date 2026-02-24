"""AI service — periodic AI attacks every 15 minutes.

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
import math
from collections import deque
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

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
        templates: AI army templates (kept for future use).
    """

    def __init__(
        self,
        upgrade_provider: UpgradeProvider,
        templates: dict,
        game_config=None,
        hardcoded_waves: list | None = None,
    ) -> None:
        self._upgrades = upgrade_provider
        self._templates = templates
        self._game_config = game_config
        self._hardcoded_waves: list[dict] = hardcoded_waves or []
        self._params = AIParams()
        self._next_army_aid: int = 10_000   # High range to avoid player AID clashes
        # deque of bool: True = AI won, False = defender won
        self._history: deque[bool] = deque(maxlen=self._params.history_window)
        # Pending battles: attack_id → {defender_uid, army_summary}
        self._pending: dict[int, dict] = {}

    # -- Public API --------------------------------------------------------

    def on_item_completed(
        self,
        empire_uid: int,
        iid: str,
        empire_service: "EmpireService",
        attack_service: "AttackService",
    ) -> None:
        """Called once when an empire completes a building or research item.

        Finds every hardcoded wave whose trigger list contains *iid* AND
        whose full trigger conditions are now satisfied, then dispatches them.
        """
        empire = empire_service.get(empire_uid)
        if empire is None:
            return

        matches = self._match_waves_for_item(empire, iid)
        for army in matches:
            self._send_army(empire_uid, empire, empire_service, attack_service, army)

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

    # -- Internals ---------------------------------------------------------

    def _send_army(
        self,
        defender_uid: int,
        empire: Empire,
        empire_service: EmpireService,
        attack_service: AttackService,
        army: Army,
    ) -> None:
        """Register *army* with the AI empire and dispatch the attack."""
        from gameserver.models.empire import Empire as EmpireModel

        ai_empire = empire_service.get(AI_UID)
        if ai_empire is None:
            ai_empire = EmpireModel(uid=AI_UID, name="AI")
            empire_service.register(ai_empire)

        ai_empire.armies = [a for a in ai_empire.armies if a.aid != army.aid]
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

        travel_s = self._game_config.ai_travel_seconds if self._game_config else 30.0

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
    ) -> None:
        """Generate an adaptive army and dispatch it (used by trigger_attacks)."""
        player_power = self._assess_player(empire)
        army = self._build_army(empire, player_power)
        if not army:
            log.warning(
                "[AI_ATTACK] No critters available for defender=%d — skipping",
                defender_uid,
            )
            return
        log.info(
            "[AI_ATTACK] adaptive army for defender=%d power=%.1f params=%s",
            defender_uid, player_power, _params_summary(self._params),
        )
        self._send_army(defender_uid=defender_uid, empire=empire,
                        empire_service=empire_service,
                        attack_service=attack_service, army=army)

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
                if tile_type not in {
                    "empty", "path", "spawnpoint", "castle", "blocked", "void"
                }:
                    structure_tiles += 1
        tile_score = structure_tiles * 1_000.0 * p.tile_weight

        total = building_score + research_score + culture_score + tile_score
        return max(total, 500.0)   # Floor so new players still get attacked

    def _match_waves_for_item(
        self,
        empire: "Empire",
        completed_iid: str,
    ) -> "list[Army]":
        """Return all Army entries whose trigger list contains *completed_iid*
        AND whose full trigger conditions are met.
        """
        if not self._hardcoded_waves:
            return []

        from gameserver.models.army import Army, CritterWave

        total_citizens = sum(empire.citizens.values())

        results = []
        for entry in self._hardcoded_waves:
            name = entry.get("name", "")

            trigger = entry.get("trigger") or {}
            req_items   = trigger.get("items") or []
            citizen_min = trigger.get("citizen", 999)

            # The completed item must appear in the trigger list
            iid_upper = completed_iid.upper()
            in_items = iid_upper in [x.upper() for x in req_items]
            citizen_trigger = total_citizens >= citizen_min

            if not (in_items or citizen_trigger):
                continue

            army_def = entry.get("army") or []
            if not army_def:
                continue

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

            initial_delay_ms = (
                self._game_config.initial_wave_delay_ms if self._game_config else 15000.0
            )
            for i, wave in enumerate(waves):
                wave.next_critter_ms = int(i * initial_delay_ms)

            aid = self._next_army_aid
            self._next_army_aid += 1
            log.info(
                "[AI_ATTACK] Wave '%s' triggered by iid=%s for empire=%s",
                name, completed_iid, empire.uid,
            )
            results.append(Army(aid=aid, uid=AI_UID, name=name, waves=waves))

        return results

    def _match_hardcoded_wave(self, empire: "Empire") -> "Army | None":
        """Return a hardcoded Army if any wave entry's trigger conditions are met.

        Iterates ``self._hardcoded_waves`` in order; the *last* entry whose
        trigger is fully satisfied wins (so more-specific entries should come
        later in the YAML).  Returns ``None`` when no entry matches or the
        list is empty.
        """
        if not self._hardcoded_waves:
            return None

        from gameserver.models.army import Army, CritterWave
        from gameserver.util import effects as fx

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

        army_def = last_match.get("army") or []
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

        aid = self._next_army_aid
        self._next_army_aid += 1
        name = last_match.get("name", "Hardcoded Attack")
        log.info("[AI_ATTACK] Using hardcoded wave '%s' for defender uid=%s", name, empire.uid)
        return Army(aid=aid, uid=AI_UID, name=name, waves=waves)

    def _build_army(self, empire: Empire, player_power: float) -> Army | None:
        """Construct an Army scaled to player_power using the heuristic."""
        from gameserver.models.army import Army, CritterWave
        from gameserver.models.items import ItemType

        # ── Check hardcoded waves first ───────────────────────────────────
        matched = self._match_hardcoded_wave(empire)
        if matched is not None:
            return matched

        p = self._params
        budget = player_power * p.power_multiplier

        # Available critters based on the defender's own completed tech tree
        # (so the army stays era-appropriate)
        completed: set[str] = set()
        for iid, remaining in empire.buildings.items():
            if remaining == 0.0:
                completed.add(iid)
        for iid, remaining in empire.knowledge.items():
            if remaining == 0.0:
                completed.add(iid)

        available = (
            self._upgrades.available_critters(completed)
            if self._upgrades else []
        )
        # Fallback: if the player hasn't unlocked anything yet, use all critters
        if not available and self._upgrades:
            available = [
                i for i in self._upgrades.items.values()
                if i.item_type == ItemType.CRITTER
            ]

        if not available:
            return None

        # ── Partition critters into role pools ────────────────────────────
        fast_pool    = [c for c in available if c.speed >= 0.25]
        armored_pool = [c for c in available if c.armour > 0]
        # Normal = everything not in the other two pools
        fast_set    = set(c.iid for c in fast_pool)
        armored_set = set(c.iid for c in armored_pool)
        normal_pool  = [c for c in available
                        if c.iid not in fast_set and c.iid not in armored_set]
        if not normal_pool:
            normal_pool = available   # ultimate fallback

        def _best(pool):
            return max(pool, key=lambda c: c.health) if pool else None

        best_fast    = _best(fast_pool)
        best_armored = _best(armored_pool)
        best_normal  = _best(normal_pool)

        # ── Share assignment ──────────────────────────────────────────────
        fast_share    = p.speed_bias if best_fast    else 0.0
        armored_share = p.armor_bias if best_armored else 0.0
        normal_share  = max(0.0, 1.0 - fast_share - armored_share)

        shares: list[tuple] = []
        if fast_share    > 0 and best_fast:
            shares.append((best_fast,    fast_share))
        if armored_share > 0 and best_armored:
            shares.append((best_armored, armored_share))
        if normal_share  > 0 and best_normal:
            shares.append((best_normal,  normal_share))
        if not shares:
            shares = [(best_normal, 1.0)]

        # ── Build waves (round-robin over roles) ──────────────────────────
        waves: list[CritterWave] = []
        for i in range(p.wave_count):
            critter_item, share = shares[i % len(shares)]
            # How many waves will this share cover?
            waves_for_share = max(1, round(p.wave_count * share))
            wave_budget = (budget * share) / waves_for_share
            slots = int(math.ceil(wave_budget / max(critter_item.health, 1.0)))
            slots = max(p.min_slots_per_wave, min(p.max_slots_per_wave, slots))

            waves.append(CritterWave(
                wave_id=i + 1,
                iid=critter_item.iid,
                slots=slots,
                num_critters_spawned=0,
                next_critter_ms=0.0,
            ))

        aid = self._next_army_aid
        self._next_army_aid += 1

        # ── Set initial wave timing (no player effects) ──────────────────
        initial_delay_ms = (
            self._game_config.initial_wave_delay_ms
            if self._game_config else 15000.0
        )
        for i, wave in enumerate(waves):
            wave.next_critter_ms = int(i * initial_delay_ms)  # first wave zero delay

        return Army(aid=aid, uid=AI_UID, name="AI Assault", waves=waves)

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
