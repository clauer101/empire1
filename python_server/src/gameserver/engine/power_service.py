"""Empire power metrics.

Four orthogonal scores, each on a comparable scale:

  economy_power  — how fast the empire generates resources and completes items
  attack_power   — how strong armies it can field
  defense_power  — how well its tower network can repel attackers
  total_power    — weighted composite of all three

Design principles
-----------------
* Pure functions — no I/O, no side-effects, all inputs explicit.
* Each function returns a float ≥ 0.
* Empire-level effects (modifiers) are folded in where they apply.
* Boss critters are excluded from attack_power (they are not spawnable in normal waves).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from gameserver.engine.upgrade_provider import UpgradeProvider
    from gameserver.models.empire import Empire
    from gameserver.models.items import ItemDetails, ItemType


# ---------------------------------------------------------------------------
# Weights (tune here without touching logic)
# ---------------------------------------------------------------------------

# economy_power
_BUILDING_EFFORT_W  = 1.0    # per effort-point of completed buildings
_KNOWLEDGE_EFFORT_W = 0.8    # per effort-point of completed knowledge
_CULTURE_W          = 0.015  # per point of current culture resource
_GOLD_W             = 0.005  # per point of current gold resource
_GOLD_RATE_W        = 50.0   # per gold/s (gold_offset + modifier bonus)
_CULTURE_RATE_W     = 80.0   # per culture/s
_LIFE_RATE_W        = 200.0  # per life/s regen
_BUILD_SPEED_W      = 500.0  # per point of effective build_speed above 1
_RESEARCH_SPEED_W   = 500.0  # per point of effective research_speed above 1
_MERCHANT_W         = 20.0   # per merchant citizen
_ARTIST_W           = 15.0   # per artist citizen

# attack_power
_CRITTER_EHP_W      = 0.4    # effective HP (health + armour*5) per slot
_CRITTER_SPEED_W    = 30.0   # per hex/s above baseline (0.2)
_ARMY_SIZE_W        = 5.0    # per slot available across pending armies
_HEALTH_MOD_BONUS   = 2.0    # multiplier contribution of health_modifier
_SPEED_MOD_BONUS    = 1.5    # multiplier contribution of speed_modifier
_ARMOUR_MOD_BONUS   = 1.5    # multiplier contribution of armour_modifier

# defense_power
_TOWER_DPS_W        = 80.0   # per effective DPS of each tower
_TOWER_RANGE_W      = 15.0   # per range unit of each tower
_BURN_DPS_BONUS     = 0.6    # burn_dps added to effective DPS
_SLOW_BONUS         = 20.0   # per tower with slow effect
_SPLASH_BONUS       = 25.0   # per tower with splash
_DAMAGE_MOD_BONUS   = 1.5    # multiplier contribution of damage_modifier
_RANGE_MOD_BONUS    = 1.0    # multiplier contribution of range_modifier
_RELOAD_MOD_BONUS   = 1.0    # multiplier contribution of reload_modifier
_SCIENTIST_W        = 15.0   # per scientist (faster research → faster defense)

# total_power weights
_ECONOMY_W  = 0.3
_ATTACK_W   = 0.35
_DEFENSE_W  = 0.35


# ---------------------------------------------------------------------------
# Public result dataclass
# ---------------------------------------------------------------------------

@dataclass
class PowerReport:
    """All four power scores for one empire."""
    economy:  float
    attack:   float
    defense:  float
    total:    float

    def to_dict(self) -> dict:
        return {
            "economy": round(self.economy,  1),
            "attack":  round(self.attack,   1),
            "defense": round(self.defense,  1),
            "total":   round(self.total,    1),
        }


# ---------------------------------------------------------------------------
# Economy power
# ---------------------------------------------------------------------------

def economy_power(empire: "Empire", upgrades: "UpgradeProvider") -> float:
    """Score based on research/building progress, income rates, and citizens.

    Captures how quickly the empire can grow — fast economies fund both
    offense and defense over time.
    """
    score = 0.0
    fx = empire.effects

    # ── Completed tech tree ──────────────────────────────────────────
    for iid, remaining in empire.buildings.items():
        if remaining <= 0:
            item = upgrades.get(iid)
            if item:
                score += item.effort * _BUILDING_EFFORT_W

    for iid, remaining in empire.knowledge.items():
        if remaining <= 0:
            item = upgrades.get(iid)
            if item:
                score += item.effort * _KNOWLEDGE_EFFORT_W

    # ── Current resources ────────────────────────────────────────────
    score += empire.resources.get("culture", 0.0) * _CULTURE_W
    score += empire.resources.get("gold",    0.0) * _GOLD_W

    # ── Income rates (from effects) ──────────────────────────────────
    gold_rate    = fx.get("gold_offset",    0.0) * (1.0 + fx.get("gold_modifier",    0.0))
    culture_rate = fx.get("culture_offset", 0.0) * (1.0 + fx.get("culture_modifier", 0.0))
    life_rate    = fx.get("life_offset",    0.0) * (1.0 + fx.get("life_modifier",    0.0))
    score += gold_rate    * _GOLD_RATE_W
    score += culture_rate * _CULTURE_RATE_W
    score += life_rate    * _LIFE_RATE_W

    # ── Build / research speed bonus ─────────────────────────────────
    build_speed    = (1.0 + fx.get("build_speed_offset",    0.0)) * (1.0 + fx.get("build_speed_modifier",    0.0))
    research_speed = (1.0 + fx.get("research_speed_offset", 0.0)) * (1.0 + fx.get("research_speed_modifier", 0.0))
    score += max(0.0, build_speed    - 1.0) * _BUILD_SPEED_W
    score += max(0.0, research_speed - 1.0) * _RESEARCH_SPEED_W

    # ── Citizens ─────────────────────────────────────────────────────
    score += empire.citizens.get("merchant",  0) * _MERCHANT_W
    score += empire.citizens.get("artist",    0) * _ARTIST_W

    return max(0.0, score)


# ---------------------------------------------------------------------------
# Attack power
# ---------------------------------------------------------------------------

def attack_power(empire: "Empire", upgrades: "UpgradeProvider") -> float:
    """Score based on unlocked critter quality and standing army slots.

    Effective HP (eHP) per slot is the primary driver — armoured, high-health
    units that move quickly are the hardest to stop.
    """
    from gameserver.models.items import ItemType

    score = 0.0
    fx = empire.effects

    # ── Empire modifiers ─────────────────────────────────────────────
    health_mod = 1.0 + fx.get("health_modifier", 0.0) * _HEALTH_MOD_BONUS
    speed_mod  = 1.0 + fx.get("speed_modifier",  0.0) * _SPEED_MOD_BONUS
    armour_mod = 1.0 + fx.get("armour_modifier", 0.0) * _ARMOUR_MOD_BONUS

    # ── Unlocked critters ────────────────────────────────────────────
    completed: set[str] = {
        iid for iid, r in {**empire.buildings, **empire.knowledge}.items() if r <= 0
    }
    available = [
        item for item in upgrades.items.values()
        if item.item_type == ItemType.CRITTER
        and not item.is_boss
        and all(req in completed for req in item.requirements)
    ]

    if available:
        # Best critter quality: max eHP/slot across available pool
        # (reflects the strongest unit the empire CAN field)
        best_ehp_per_slot = 0.0
        for c in available:
            effective_health = c.health * health_mod
            effective_armour = c.armour * armour_mod
            effective_speed  = c.speed  * speed_mod
            ehp = effective_health + effective_armour * 5.0
            speed_bonus = max(0.0, effective_speed - 0.2) * _CRITTER_SPEED_W
            ehp_per_slot = (ehp * _CRITTER_EHP_W + speed_bonus) / max(1, c.slots)
            best_ehp_per_slot = max(best_ehp_per_slot, ehp_per_slot)

        # Average quality across all available critters (breadth matters too)
        avg_ehp_per_slot = sum(
            ((c.health * health_mod + c.armour * armour_mod * 5.0) * _CRITTER_EHP_W
             + max(0.0, c.speed * speed_mod - 0.2) * _CRITTER_SPEED_W)
            / max(1, c.slots)
            for c in available
        ) / len(available)

        score += best_ehp_per_slot * 300.0
        score += avg_ehp_per_slot  * 100.0

    # ── Standing army (slots already committed) ───────────────────────
    for army in empire.armies:
        total_slots = sum(w.slots for w in army.waves)
        score += total_slots * _ARMY_SIZE_W

    # ── Capture/loot effects amplify attack value ─────────────────────
    culture_steal = fx.get("culture_steal_modifier",   0.0)
    knowledge_steal = fx.get("knowledge_steal_modifier", 0.0)
    score += culture_steal   * 500.0
    score += knowledge_steal * 500.0

    return max(0.0, score)


# ---------------------------------------------------------------------------
# Defense power
# ---------------------------------------------------------------------------

def defense_power(empire: "Empire", upgrades: "UpgradeProvider") -> float:
    """Score based on placed tower DPS, range coverage, and special effects.

    Effective DPS = damage / (reload_ms / 1000), factoring in empire modifiers.
    Range extends the zone of control and stacks with DPS.
    """
    from gameserver.models.items import ItemType

    score = 0.0
    fx = empire.effects

    # ── Empire tower modifiers ───────────────────────────────────────
    damage_mult = 1.0 + fx.get("damage_modifier", 0.0) * _DAMAGE_MOD_BONUS
    range_mult  = 1.0 + fx.get("range_modifier",  0.0) * _RANGE_MOD_BONUS
    reload_mult = 1.0 + fx.get("reload_modifier", 0.0) * _RELOAD_MOD_BONUS

    # ── Placed structures on hex map ─────────────────────────────────
    NON_TOWER = {"castle", "spawnpoint", "path", "empty", "blocked", "void", ""}
    for tile_val in empire.hex_map.values():
        tile_type = tile_val.get("type", "") if isinstance(tile_val, dict) else str(tile_val)
        if tile_type in NON_TOWER:
            continue
        item = upgrades.get(tile_type)
        if item is None or item.item_type != ItemType.STRUCTURE:
            continue

        reload_s = (item.reload_time_ms / 1000.0) / max(0.01, reload_mult)
        if reload_s <= 0:
            continue

        base_dps = item.damage / reload_s * damage_mult
        burn_dps  = item.effects.get("burn_dps", 0.0) * _BURN_DPS_BONUS
        eff_dps   = base_dps + burn_dps

        eff_range = item.range * range_mult

        score += eff_dps   * _TOWER_DPS_W
        score += eff_range * _TOWER_RANGE_W

        # Crowd-control bonuses
        if item.effects.get("slow_duration", 0) > 0:
            score += _SLOW_BONUS
        if item.effects.get("splash_radius", 0) > 0:
            score += _SPLASH_BONUS

    # ── Life pool (absorbs critter damage before losing) ─────────────
    score += empire.max_life * 10.0

    # ── Scientists accelerate research → faster unlocks → better defense
    score += empire.citizens.get("scientist", 0) * _SCIENTIST_W

    # ── Artefacts (any artefact grants a bonus) ───────────────────────
    score += len(empire.artefacts) * 150.0

    return max(0.0, score)


# ---------------------------------------------------------------------------
# Total power
# ---------------------------------------------------------------------------

def total_power(economy: float, attack: float, defense: float) -> float:
    """Weighted combination of the three orthogonal scores."""
    return economy * _ECONOMY_W + attack * _ATTACK_W + defense * _DEFENSE_W


# ---------------------------------------------------------------------------
# Convenience: compute all four at once
# ---------------------------------------------------------------------------

def compute_power(empire: "Empire", upgrades: "UpgradeProvider") -> PowerReport:
    """Compute all four power scores for an empire."""
    eco = economy_power(empire, upgrades)
    atk = attack_power(empire,  upgrades)
    dfn = defense_power(empire, upgrades)
    tot = total_power(eco, atk, dfn)
    return PowerReport(economy=eco, attack=atk, defense=dfn, total=tot)
