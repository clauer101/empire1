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
TRAVEL_TIME_OFFSET = "travel_offset"  # only attacker can modify this
SIEGE_TIME_OFFSET = "siege_offset"  # only defender can modify this

RESTORE_LIFE_AFTER_LOSS_OFFSET = "restore_life_after_loss_offset"  # Immediately restore life after losing a battle

# -- Battle / Defense ----------------------------------------------------
WAVE_DELAY_OFFSET = "wave_delay_offset"
