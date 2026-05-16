"""Effect key constants.

String keys used in effect maps on items, empires, and structures.
Replaces the ~80 string constants from the Java Effect class.
"""

# -- Resource modifiers --------------------------------------------------
GOLD_MODIFIER = "gold_modifier"
GOLD_OFFSET = "gold_offset"
CULTURE_MODIFIER = "culture_modifier"
CULTURE_OFFSET = "culture_offset"
LIFE_REGEN_MODIFIER = "life_regen_modifier"
MAX_LIFE_MODIFIER = "max_life_modifier"

# -- Building & Research -------------------------------------------------
BUILD_SPEED_MODIFIER = "build_speed_modifier"
BUILD_SPEED_OFFSET = "build_speed_offset"
RESEARCH_SPEED_MODIFIER = "research_speed_modifier"
RESEARCH_SPEED_OFFSET = "research_speed_offset"

# -- Structure / Tower ---------------------------------------------------
SPLASH_RADIUS = "splash_radius"

# -- Travel & Siege ------------------------------------------------------
TRAVEL_TIME_OFFSET = "travel_offset"      # only attacker: flat seconds added/removed
TRAVEL_TIME_MODIFIER = "travel_time_modifier"  # only attacker: percentage reduction (0.0–1.0)
SIEGE_TIME_OFFSET = "siege_offset"        # only defender can modify this
SIEGE_TIME_MODIFIER = "siege_time_modifier"  # attacker: percentage reduction (0.0–1.0)

RESTORE_LIFE_AFTER_LOSS_OFFSET = "restore_life_after_loss_offset"  # Immediately restore life after losing a battle

# -- Battle / Defense ----------------------------------------------------
WAVE_DELAY_OFFSET = "wave_delay_offset"

# -- Cost modifiers ------------------------------------------------------
CITIZEN_COST_MODIFIER = "citizen_cost_modifier"       # reduces citizen upgrade cost: price × (1 - v)
TILE_COST_MODIFIER = "tile_cost_modifier"             # reduces new tile cost: price × (1 - v)
LAND_COST_MODIFIER = "land_cost_modifier"             # reduces new tile cost (ruler variant): price × (1 - v), stacks with tile_cost_modifier
BUILDING_COST_MODIFIER = "building_cost_modifier"     # reduces gold cost of buildings: gold × (1 - v)
WAVE_COST_MODIFIER = "wave_cost_modifier"             # reduces new wave cost: price × (1 - v)
WAVE_ERA_COST_MODIFIER = "wave_era_cost_modifier"     # reduces wave era upgrade cost: price × (1 - v)
WAVE_SLOT_COST_MODIFIER = "wave_slot_cost_modifier"   # reduces critter slot purchase price: price × (1 - v)

# -- Citizen modifiers ---------------------------------------------------
CITIZEN_EFFECT_MODIFIER = "citizen_effect_modifier"       # scales citizen_effect: base × (1 + v)
OTHER_CITIZEN_GOLD_MODIFIER = "other_citizen_gold_modifier"  # artists+scientists each add v to gold_modifier

# -- One-time lump sums (fired on ruler skill-up, not stored in empire.effects) --
GOLD_LUMP_SUM_ON_SKILL_UP = "gold_lump_sum_on_skill_up"
CULTURE_LUMP_SUM_ON_SKILL_UP = "culture_lump_sum_on_skill_up"

# -- Combat --------------------------------------------------------------
RESTORE_LIFE_DURING_BATTLE_MODIFIER = "restore_life_during_battle_modifier"  # boosts life regen while under attack
ENEMY_SIEGE_TIME_MODIFIER = "enemy_siege_time_modifier"  # attacker: reduces own siege duration × (1 - v)
