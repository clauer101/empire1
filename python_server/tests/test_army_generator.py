"""Tests for the shared AI army generator (gameserver.util.army_generator)."""

from gameserver.util.army_generator import generate_army

ERA_GROUPS = {
    "stone": ["SLAVE", "WOLF", "MAMMOTH"],
    "neolithic": ["WARRIOR"],
}
SLOTS = {"SLAVE": 1, "WOLF": 1, "MAMMOTH": 5, "WARRIOR": 1}
BOSSES = {"MAMMOTH"}
CFG = {"stone": {"min_waves": 6, "max_waves": 8, "min_slots": 10, "max_slots": 20}}


def _boss_critter_count(waves):
    return sum(int(w["slots"] / SLOTS[w["critter"]])
               for w in waves if w["critter"] in BOSSES)


def test_at_most_one_boss_critter_per_army():
    for seed in range(200):
        result = generate_army(
            era_internal="stone", ai_generator_cfg=CFG,
            critter_era_groups=ERA_GROUPS, slot_by_iid=SLOTS,
            seed=seed, boss_iids=BOSSES)
        assert _boss_critter_count(result["waves"]) <= 1, f"seed={seed}"


def test_boss_wave_has_exactly_one_spawn():
    for seed in range(200):
        result = generate_army(
            era_internal="stone", ai_generator_cfg=CFG,
            critter_era_groups=ERA_GROUPS, slot_by_iid=SLOTS,
            seed=seed, boss_iids=BOSSES)
        for w in result["waves"]:
            if w["critter"] in BOSSES:
                assert w["slots"] == SLOTS[w["critter"]]


def test_no_boss_limit_without_boss_iids():
    # Backwards compatible: without boss_iids the generator is unchanged.
    result = generate_army(
        era_internal="stone", ai_generator_cfg=CFG,
        critter_era_groups=ERA_GROUPS, slot_by_iid=SLOTS, seed=7)
    assert result["waves"]
