"""Integration tests for the battle system.

These tests use the deterministic tick() method to simulate
complete battle scenarios without timing dependencies.
"""

# TODO: Phase 2 — implement after battle_service is complete

# Planned tests:
#
# test_full_battle_critters_vs_towers
#   - Spawn critters, let towers shoot, verify kills
#
# test_battle_defender_wins
#   - All critters die before reaching end → defender_won = True
#
# test_battle_defender_loses
#   - Life reaches 0 → immediate end, defender_won = False
#
# test_battle_min_keepalive
#   - Battle doesn't end before MIN_KEEP_ALIVE_MS even if empty
#
# test_battle_loot_on_critter_finish
#   - Critter reaches end → resources transferred
#
# test_kill_bonus
#   - Critter killed → defender gets bonus resources
#
# test_spawn_on_death
#   - Parent critter dies → children spawn at parent location
#
# test_splash_hits_neighbors
#   - Splash shot damages critters on adjacent hexes
#
# test_splash_excludes_primary
#   - Primary target not hit by secondary splash
#
# test_slow_shot_reduces_speed
#   - COLD shot applies slow effect
#
# test_burn_shot_applies_dot
#   - BURN shot applies continuous damage
#
# test_four_direction_simultaneous
#   - Armies from all 4 directions in same battle
#
# test_broadcast_throttled
#   - Max 1 broadcast per 250ms
#
# test_wave_delay_scaling
#   - Defender effect increases wave delay
