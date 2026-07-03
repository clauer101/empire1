"""Central registry of all empire effect keys.

Each entry: (key, icon, label, description)
Keep in sync with EFFECT_META in web/js/lib/format.js.
"""
from __future__ import annotations

EMPIRE_EFFECT_KEYS: list[tuple[str, str, str, str]] = [
    # Resources
    ("gold_offset",                             "💰", "Gold income",                     "Increases gold production by a fixed amount"),
    ("gold_modifier",                           "💰", "Gold bonus",                      "Increases gold production by a multiplier"),
    ("culture_offset",                          "🎭", "Culture income",                  "Increases culture production by a fixed amount"),
    ("culture_modifier",                        "🎭", "Culture bonus",                   "Increases culture production by a multiplier"),
    ("life_regen_modifier",                     "❤️", "Life regen",                      "Increases life energy regeneration"),
    ("max_life_modifier",                       "❤️", "Max life",                        "Increases maximum life"),
    ("restore_life_after_loss_offset",          "❤️", "Life restore",                    "Restores life after a lost battle"),
    # Building & Research
    ("build_speed_modifier",                    "🏗",  "Build speed",                    "Accelerates building construction by a multiplier"),
    ("build_speed_offset",                      "🏗",  "Build speed",                    "Accelerates building construction by a fixed amount"),
    ("research_speed_modifier",                 "🔬", "Research speed",                  "Accelerates research by a multiplier"),
    ("research_speed_offset",                   "🔬", "Research speed",                  "Accelerates research by a fixed amount"),
    ("research_cost_modifier",                  "🔬", "Research cost",                   "Reduces the effort cost of each research"),
    ("scientist_citizen_bonus",                 "🔭", "Scientist bonus",                 "Increases the research speed bonus per scientist citizen"),
    ("gold_lump_sum_after_research",            "💰", "Research reward",                 "Grants a one-time gold bonus each time a research is completed"),
    # Workshop
    ("workshop_cost_modifier",                  "🔧", "Workshop discount",               "Reduces the gold cost of workshop item upgrades"),
    # Travel & Siege
    ("travel_time_modifier",                    "🚀", "Travel speed",                    "Reduces travel time of armies by a percentage"),
    ("travel_offset",                           "🚀", "Travel time",                     "Modifies travel time of armies"),
    ("siege_offset",                            "⚔️", "Siege time",                      "Modifies siege time of armies"),
    ("siege_time_modifier",                     "⚔️", "Siege speed",                     "Accelerates siege by a multiplier"),
    ("enemy_siege_time_modifier",               "⚔️", "Siege corruption",                "Reduces the siege duration of your own attacks"),
    ("max_siege_construction_speed_modifier",   "🏗",  "Max siege disruption",           "Maximum construction speed reduction during siege"),
    ("siege_construction_speed_per_army_modifier","🏗","Siege resilience",               "Reduces the construction speed penalty per besieging army"),
    # Army & Waves
    ("wave_delay_offset",                       "⏳", "Wave delay",                      "Increases delay between incoming waves"),
    ("wave_cost_modifier",                      "⚔️", "Wave discount",                   "Reduces the gold cost of adding new waves to armies"),
    ("wave_era_cost_modifier",                  "⚔️", "Wave era discount",               "Reduces the gold cost of upgrading wave era"),
    ("wave_slot_cost_modifier",                 "⚔️", "Wave slot discount",              "Reduces the gold cost of purchasing additional critter slots"),
    # Battle / Defense
    ("restore_life_during_battle_modifier",     "❤️", "Battle life regen",               "Adds to life regeneration while in battle"),
    ("damage_modifier",                         "💥", "Tower damage",                    "Increases damage of all towers by a multiplier"),
    ("range_modifier",                          "🎯", "Tower range",                     "Increases range of all towers by a multiplier"),
    ("reload_modifier",                         "⚡", "Tower reload speed",              "Increases reload speed of all towers by a multiplier"),
    # Critter buffs
    ("speed_modifier",                          "⚡", "Critter speed",                   "Boosts speed of all spawned critters"),
    ("health_modifier",                         "❤️", "Critter health",                  "Boosts health of all spawned critters"),
    ("armour_modifier",                         "🛡", "Critter armour",                  "Boosts armour of all spawned critters"),
    # Costs
    ("citizen_cost_modifier",                   "🫂", "Citizen discount",                "Reduces the culture cost of acquiring new citizens"),
    ("tile_cost_modifier",                      "🗺️", "Land discount",                   "Reduces the gold cost of acquiring new land tiles"),
    ("building_cost_modifier",                  "🏗",  "Building discount",              "Reduces the gold cost of constructing buildings"),
    ("tower_sell_refund_modifier",              "💰", "Tower refund",                    "Increases tower sell refund"),
    # Citizens
    ("citizen_effect_modifier",                 "🫂", "Citizen efficiency",              "Adds to the productivity bonus of each citizen"),
    ("other_citizen_gold_modifier",             "💰", "Artist/Scientist gold",           "Artists and scientists also contribute to gold income"),
    # Misc
    ("increase_start_gold",                     "💰", "Starting gold",                   "Grants extra gold when respawning after season restart"),
    # Artifacts & Spies
    ("artifact_steal_victory_modifier",         "⚜",  "Artifact steal (victory)",       "Increases artifact maximum steal chance on victory"),
    ("artifact_steal_defeat_modifier",          "⚜",  "Artifact steal (defeat)",        "Increases artifact maximum steal chance on defeat"),
    ("artifact_retention_time",                 "⚜",  "Artifact protection",            "Newly acquired artifacts cannot be stolen for this duration"),
    ("spy_workshop",                            "🕵️", "Workshop intel",                  "Unlocks workshop intelligence in spy reports"),
    # Unlocks
    ("ruler_unlock",                            "👑", "Ruler",                           "Assign a powerful ruler to your empire"),
    ("enable_army",                             "⚔",  "Army",                           "Unlocks the Army view to compose and send attack waves"),
    ("enable_techtree",                         "⬡",  "Tech Tree",                      "Unlocks the Tech Tree view for advanced research"),
    ("enable_workshop",                         "⚙",  "Workshop",                       "Unlocks the Workshop view for tower and critter upgrades"),
    ("enable_messages",                         "✉",  "Messages",                       "Unlocks the Messages view for battle reports"),
    # One-shot lump sums
    ("gold_lump_sum_on_skill_up",               "💰", "Skill-up gold reward",            "Grants a one-time gold bonus when this skill level is reached"),
    ("culture_lump_sum_on_skill_up",            "🎭", "Skill-up culture reward",         "Grants a one-time culture bonus when this skill level is reached"),
    # Ruler aura effects
    ("increase_armour_modifier",                "🛡", "Aura: Armour boost",              "Boosts armour of nearby friendly critters"),
    ("increase_critter_speed",                  "⚡", "Aura: Speed boost",               "Boosts speed of nearby friendly critters"),
    ("slow_tower_modifier",                     "❄",  "Aura: Tower slow",               "Slows reload speed of nearby enemy towers"),
    ("reduce_tower_damage",                     "💢", "Aura: Tower damage",              "Reduces damage of nearby enemy towers"),
]

# Flat list of keys only — for quick lookup
EMPIRE_EFFECT_KEY_SET: frozenset[str] = frozenset(k for k, *_ in EMPIRE_EFFECT_KEYS)
