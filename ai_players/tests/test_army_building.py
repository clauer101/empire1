import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bot.analyzer import ERA_RANK  # noqa: E402
from bot.army_building import (  # noqa: E402
    critter_power,
    next_skill,
    pick_ruler,
    ruler_wave_target,
)
from bot.planners.attack import AttackPlanner, _target_waves  # noqa: E402
from bot.planners.base import BotContext  # noqa: E402

RULERS = {"MAJA": {}, "BORIN": {}}
RULER_IIDS = set(RULERS)

_ERA_NAME = {rank: name for name, rank in ERA_RANK.items()}


def _critter(iid, era=0, slots=1, health=10, armour=0.0, speed=1.0):
    # Real catalog (GET /api/empire/items → critters) keys era as the STRING
    # era name (e.g. "bronze"), not an int — matches bot/planners/attack.py's
    # _era_rank_of(). `era` here is the convenient int rank for tests.
    return {"era": _ERA_NAME[era], "slots": slots,
            "health": health, "armour": armour, "speed": speed}


def _military(waves, next_wave_price=500.0):
    return {"armies": [{"aid": 1, "waves": waves,
                        "next_wave_price": next_wave_price}]}


# ── ruler helpers ─────────────────────────────────────────────────────────

def test_pick_ruler_random_from_catalog():
    # Always a catalog member; single option is deterministic; empty → None
    picks = {pick_ruler(RULERS) for _ in range(50)}
    assert picks <= set(RULERS)
    assert len(picks) > 1  # spreads over the catalog, not always the same
    assert pick_ruler({"BORIN": {}}) == "BORIN"
    assert pick_ruler({}) is None


def test_next_skill_order_and_caps():
    assert next_skill({"q": 0, "w": 0, "e": 0, "r": 0}) == "q"
    assert next_skill({"q": 5, "w": 0, "e": 0, "r": 0}) == "w"
    assert next_skill({"q": 5, "w": 5, "e": 4, "r": 3}) == "e"
    assert next_skill({"q": 5, "w": 5, "e": 5, "r": 3}) is None


def test_ruler_wave_target_random_among_existing_waves():
    # Only one army is ever built, so ruler_wave_target picks among its waves
    # directly — must spread across ALL indices, not always wave 0.
    waves = [{"iid": "SLAVE"}, {"iid": "SLAVE"}, {"iid": "SLAVE"}]
    picks = {ruler_wave_target(waves, RULER_IIDS) for _ in range(300)}
    assert picks == {0, 1, 2}


def test_ruler_wave_target_none_when_placed_or_empty():
    assert ruler_wave_target([{"iid": "MAJA"}], RULER_IIDS) is None
    assert ruler_wave_target([], RULER_IIDS) is None


def test_critter_power_per_slot():
    assert critter_power(_critter("A", slots=2, health=20, armour=1.0, speed=1.0)) == \
        20 * 2.0 * 2.0 / 2


# ── target wave count ────────────────────────────────────────────────────

def test_target_waves_formula():
    # max(2, ceil(era_rank * 1.5))
    assert _target_waves(0) == 2   # stone
    assert _target_waves(1) == 2   # neolithic
    assert _target_waves(2) == 3   # bronze
    assert _target_waves(3) == 5   # iron
    assert _target_waves(4) == 6   # medieval
    assert _target_waves(5) == 8   # renaissance
    assert _target_waves(8) == 12  # future


# ── planner integration ───────────────────────────────────────────────────

class FakeApi:
    def __init__(self, military):
        self._military = military
        self.calls = []

    def military(self):
        return self._military

    def __getattr__(self, name):
        def record(*args, **kwargs):
            self.calls.append((name, args))
            return {"success": True}
        return record


def _ctx(military, summary=None, memory=None, critters=None):
    summary = summary or {"resources": {"gold": 1000, "culture": 0},
                          "attacks_outgoing": [], "effects": {},
                          "ruler": {"type": ""}}
    strategy = {"type": "attack", "valid_until": "2099-01-01T00:00:00Z",
                "params": {"target_uid": 9, "target_name": "victim"}}
    items = {"critters": critters or {}, "rulers": RULERS}
    return BotContext(summary, items, memory if memory is not None else {},
                      strategy, FakeApi(military))


def _full_summary(ruler_type="MAJA", gold=1000, era="stone"):
    return {"resources": {"gold": gold, "culture": 0}, "attacks_outgoing": [],
            "effects": {"ruler_unlock": 1}, "era": era,
            "ruler": {"type": ruler_type, "q": 5, "w": 5, "e": 5, "r": 3}}


def test_fills_empty_wave_with_best_era_random_tie():
    # Two critters tied at era 1 (the wave's max_era), one at era 0 — the
    # weaker era-0 critter must never be picked while era-1 ones exist.
    critters = {"WEAK0": _critter("WEAK0", era=0, health=999),  # strong but old era
                "TOP_A": _critter("TOP_A", era=1, health=10),
                "TOP_B": _critter("TOP_B", era=1, health=20)}
    mil = _military([{"iid": "", "slots": 2, "max_era": 1, "next_slot_price": 0.0}])
    picks = set()
    for _ in range(100):
        ctx = _ctx(mil, critters=critters)
        action = AttackPlanner().propose(ctx)
        assert action is not None
        api = FakeApi(mil)
        action.run(api)
        assert api.calls[0][0] == "set_wave"
        picks.add(api.calls[0][1][2])  # iid arg
    assert picks == {"TOP_A", "TOP_B"}  # both ties chosen across runs, never WEAK0


def test_all_empty_waves_proposed_in_same_tick_not_just_one():
    critters = {"CUR": _critter("CUR", era=0, health=10)}
    mil = _military([{"iid": "", "slots": 1, "max_era": 0, "next_slot_price": 0.0},
                     {"iid": "", "slots": 1, "max_era": 0, "next_slot_price": 0.0},
                     {"iid": "", "slots": 1, "max_era": 0, "next_slot_price": 0.0}])
    ctx = _ctx(mil, critters=critters)
    opts = AttackPlanner().propose_options(ctx)
    fill_waves = {int(o.description.split("wave ")[1].split(" ")[0])
                  for o in opts if o.description.startswith("set wave")}
    assert fill_waves == {0, 1, 2}


def test_swaps_outdated_wave_to_current_top_era():
    critters = {"OLD": _critter("OLD", era=0, health=10),
                "NEW": _critter("NEW", era=1, health=50)}
    # Wave already filled with the era-0 critter, but its max_era was raised
    # to 1 and a stronger era-1 critter is now unlocked — must be swapped.
    mil = _military([{"iid": "OLD", "slots": 2, "max_era": 1,
                      "next_slot_price": 0.0}])
    ctx = _ctx(mil, critters=critters)
    action = AttackPlanner().propose(ctx)
    assert action is not None
    assert "switch wave 0 to NEW" in action.description
    api = FakeApi(mil)
    action.run(api)
    assert api.calls == [("set_wave", (1, 0, "NEW", 2))]


def test_all_outdated_waves_proposed_in_same_tick_not_just_one():
    # Free action, so every outdated wave is a candidate the same cycle —
    # not just the first one found (which used to be the case).
    critters = {"OLD": _critter("OLD", era=0, health=10),
                "NEW": _critter("NEW", era=1, health=50)}
    mil = _military([{"iid": "OLD", "slots": 1, "max_era": 1,
                      "next_slot_price": 0.0},
                     {"iid": "OLD", "slots": 1, "max_era": 1,
                      "next_slot_price": 0.0},
                     {"iid": "OLD", "slots": 1, "max_era": 1,
                      "next_slot_price": 0.0}])
    ctx = _ctx(mil, critters=critters)
    opts = AttackPlanner().propose_options(ctx)
    swap_waves = {int(o.description.split("wave ")[1].split(" ")[0])
                  for o in opts if o.description.startswith("switch wave")}
    assert swap_waves == {0, 1, 2}


def test_does_not_swap_wave_already_at_top_era():
    critters = {"CUR": _critter("CUR", era=1, health=10)}
    mil = _military([{"iid": "CUR", "slots": 1, "max_era": 1,
                      "next_slot_price": 0.0}])
    ctx = _ctx(mil, critters=critters)
    # No ruler, no fill/swap candidate → nothing to propose (era already at
    # target waves=2 requires an add_wave, which needs strengthen phase).
    ctx.strategy["params"]["phase"] = "strengthen"
    opts = AttackPlanner().propose_options(ctx)
    assert not any("switch wave" in o.description for o in opts)


def test_never_swaps_or_refills_the_ruler_wave():
    critters = {"NEW": _critter("NEW", era=1, health=50)}
    mil = _military([{"iid": "MAJA", "slots": 1, "max_era": 1,
                      "next_slot_price": 0.0}])
    ctx = _ctx(mil, critters=critters)
    opts = AttackPlanner().propose_options(ctx)
    assert not any("wave 0" in o.description and "MAJA" not in o.description
                   and o.description.startswith(("set wave", "switch wave"))
                   for o in opts)


def test_ruler_placed_at_random_wave_index():
    mil = _military([{"iid": "SLAVE", "slots": 1, "max_era": 0},
                     {"iid": "SLAVE", "slots": 1, "max_era": 0},
                     {"iid": "SLAVE", "slots": 1, "max_era": 0}])
    picks = set()
    for _ in range(200):
        ctx = _ctx(mil, summary=_full_summary())
        action = AttackPlanner().propose(ctx)
        assert action and "place ruler MAJA" in action.description
        picks.add(int(action.description.split("wave ")[1].split(" ")[0]))
    assert picks == {0, 1, 2}


def test_places_ruler_in_only_wave():
    mil = _military([{"iid": "SLAVE", "slots": 1, "max_era": 0}])
    action = AttackPlanner().propose(_ctx(mil, summary=_full_summary()))
    assert action and "place ruler MAJA in wave 0" in action.description
    api = FakeApi(mil)
    action.run(api)
    assert api.calls == [("set_ruler_wave", (1, 0, "MAJA"))]


def test_era_upgrade_capped_at_own_era_rank():
    mil = _military([{"iid": "MAJA", "slots": 1, "max_era": 0},
                     {"iid": "CUR", "slots": 1, "max_era": 0,
                      "next_era_price": 100.0, "next_slot_price": 0.0}])
    ctx = _ctx(mil, summary=_full_summary(era="bronze"))  # era_rank 2
    ctx.strategy["params"]["phase"] = "strengthen"
    opts = AttackPlanner().propose_options(ctx)
    era_opt = next(o for o in opts if "era-upgrade" in o.description)
    assert "era 2" in era_opt.description  # bronze rank, never higher


def test_add_wave_and_era_upgrade_both_proposed_no_hard_gate():
    # Waves below target count AND below era_rank at the same time — both
    # options must be offered (no gate blocking add_wave until era catches up).
    mil = _military([{"iid": "MAJA", "slots": 1, "max_era": 0},
                     {"iid": "CUR", "slots": 1, "max_era": 0,
                      "next_era_price": 100.0, "next_slot_price": 0.0}],
                    next_wave_price=50.0)
    ctx = _ctx(mil, summary=_full_summary(era="bronze"))  # target_waves=3
    ctx.strategy["params"]["phase"] = "strengthen"
    opts = AttackPlanner().propose_options(ctx)
    kinds = [o.description for o in opts]
    assert any("era-upgrade" in d for d in kinds)
    assert any(d.startswith("add wave") for d in kinds)


def test_strengthen_advances_to_spy_with_minimal_army_not_fully_grown():
    # Regression: attacking is free, so the bot must start spying/attacking
    # as soon as it has ANY non-ruler wave with a critter — it must NOT wait
    # for every wave to reach era_rank or for the wave-count target to be
    # met (that used to block attacking indefinitely, since both are
    # gold-gated and the era target keeps moving as the empire advances).
    critters = {"CUR": _critter("CUR", era=0)}
    mil = _military([{"iid": "MAJA", "slots": 1, "max_era": 0},
                     {"iid": "CUR", "slots": 1, "max_era": 0,  # below era_rank
                      "next_era_price": 999999.0, "next_slot_price": 0.0}],
                    next_wave_price=999999.0)  # far from target_waves too
    ctx = _ctx(mil, summary=_full_summary(era="bronze"), critters=critters)
    ctx.strategy["params"]["phase"] = "strengthen"
    AttackPlanner().propose_options(ctx)
    assert ctx.strategy["params"]["phase"] == "spy"


def test_strengthen_does_not_advance_with_only_ruler_wave():
    mil = _military([{"iid": "MAJA", "slots": 1, "max_era": 0}])
    ctx = _ctx(mil, summary=_full_summary())
    ctx.strategy["params"]["phase"] = "strengthen"
    AttackPlanner().propose_options(ctx)
    assert ctx.strategy["params"]["phase"] == "strengthen"


def test_buy_slot_targets_fewest_slots_wave_never_ruler():
    mil = _military([{"iid": "MAJA", "slots": 1, "max_era": 0,
                      "next_slot_price": 1.0},   # ruler wave — must be skipped
                     {"iid": "CUR", "slots": 3, "max_era": 0,
                      "next_slot_price": 200.0},
                     {"iid": "CUR2", "slots": 1, "max_era": 0,
                      "next_slot_price": 50.0}])
    critters = {"CUR": _critter("CUR", era=0), "CUR2": _critter("CUR2", era=0)}
    ctx = _ctx(mil, critters=critters)
    opts = AttackPlanner().propose_options(ctx)
    slot_opt = next(o for o in opts if "buy slot" in o.description)
    assert "wave 2" in slot_opt.description  # CUR2, fewest slots (1), not CUR (3)
    assert slot_opt.price == 50.0


def test_most_common_wave_critter_picks_majority():
    from bot.planners.attack import _most_common_wave_critter
    waves = [{"iid": "SWORDMAN"}, {"iid": "SWORDMAN"}, {"iid": "BOWMAN"},
            {"iid": "MAJA"}]  # ruler wave excluded
    assert _most_common_wave_critter(waves, RULER_IIDS) == "SWORDMAN"


def test_most_common_wave_critter_none_when_no_waves_filled():
    from bot.planners.attack import _most_common_wave_critter
    assert _most_common_wave_critter([{"iid": "MAJA"}, {"iid": ""}], RULER_IIDS) is None


def test_critter_upgrade_reads_flat_price_not_nested_dict():
    # Regression: the server sends item_upgrade_prices as {iid: float}, not
    # {iid: {stat: float}} — the old code read it as nested and always got 0.
    from bot.planners.attack import CRITTER_UPGRADE_STATS, _critter_upgrade_option
    summary = {"item_upgrade_prices": {"SWORDMAN": 150.0}, "item_upgrades": {}}
    ctx = _ctx(_military([]), summary=summary)
    opt = _critter_upgrade_option(ctx, "SWORDMAN")
    assert opt is not None
    assert opt.price == 150.0
    assert opt.description.startswith("upgrade critter SWORDMAN ")
    assert any(f" {stat} " in opt.description for stat in CRITTER_UPGRADE_STATS)


def test_critter_upgrade_targets_most_placed_not_just_any():
    critters = {"SWORDMAN": _critter("SWORDMAN", era=0),
               "BOWMAN": _critter("BOWMAN", era=0)}
    mil = _military([{"iid": "MAJA", "slots": 1, "max_era": 0},
                     {"iid": "SWORDMAN", "slots": 1, "max_era": 0},
                     {"iid": "SWORDMAN", "slots": 1, "max_era": 0},
                     {"iid": "BOWMAN", "slots": 1, "max_era": 0}])
    summary = _full_summary()
    summary["item_upgrade_prices"] = {"SWORDMAN": 100.0, "BOWMAN": 100.0}
    ctx = _ctx(mil, summary=summary, critters=critters)
    opts = AttackPlanner().propose_options(ctx)
    upg = next(o for o in opts if o.description.startswith("upgrade critter"))
    assert "SWORDMAN" in upg.description  # 2 waves vs BOWMAN's 1


def test_critter_upgrade_is_absolute_last_priority():
    from bot.planners.attack import PRIO_BUY_SLOT, PRIO_CRITTER_UPG
    assert PRIO_CRITTER_UPG < PRIO_BUY_SLOT


def test_max_upgrade_level_scales_with_era():
    from bot.planners.attack import _max_upgrade_level
    assert _max_upgrade_level(0) == 3    # stone
    assert _max_upgrade_level(1) == 6    # neolithic
    assert _max_upgrade_level(3) == 12   # iron


def test_focus_upgrade_stat_sticks_then_rotates_when_capped():
    from bot.planners.attack import _focus_upgrade_stat
    memory: dict = {}
    stats = ["health", "speed", "armour"]
    levels = {"health": 0, "speed": 0, "armour": 0}
    first = _focus_upgrade_stat(memory, "SWORDMAN", levels, stats, cap=1)
    assert first in stats
    # Same item, unchanged levels → sticks to the same stat every time.
    for _ in range(10):
        assert _focus_upgrade_stat(memory, "SWORDMAN", levels, stats, cap=1) == first
    # Once that stat hits the cap, a different (non-capped) one is chosen.
    levels[first] = 1
    second = _focus_upgrade_stat(memory, "SWORDMAN", levels, stats, cap=1)
    assert second != first
    assert second in stats


def test_focus_upgrade_stat_none_when_all_capped():
    from bot.planners.attack import _focus_upgrade_stat
    levels = {"health": 2, "speed": 2, "armour": 2}
    assert _focus_upgrade_stat({}, "X", levels, ["health", "speed", "armour"],
                               cap=2) is None


def test_savings_goal_when_wave_unaffordable():
    mil = _military([{"iid": "MAJA", "slots": 1, "max_era": 0}],
                    next_wave_price=9000.0)
    ctx = _ctx(mil, summary=_full_summary(gold=10))
    ctx.strategy["params"]["phase"] = "strengthen"
    opts = AttackPlanner().propose_options(ctx)
    add_wave = next(o for o in opts if o.description.startswith("add wave"))
    assert add_wave.saves_for == 9000.0


def test_defeat_returns_to_strengthen_victory_completes():
    mil = _military([{"iid": "MAJA", "slots": 1, "max_era": 0}])
    ctx = _ctx(mil, summary=_full_summary(),
               memory={"attack_history": [{"opponent": "victim",
                                           "outcome": "defeat"}]})
    ctx.strategy["params"]["phase"] = "wait_result"
    AttackPlanner().propose_options(ctx)
    assert ctx.strategy["params"]["phase"] == "strengthen"

    ctx2 = _ctx(mil, summary=_full_summary(),
                memory={"attack_history": [{"opponent": "victim",
                                            "outcome": "victory"}]})
    ctx2.strategy["params"]["phase"] = "wait_result"
    AttackPlanner().propose_options(ctx2)
    assert ctx2.strategy.get("completed") is True


# ── attacking while defense (or anything else) is the active strategy ─────
# Attacking is free, so the planner must keep progressing even when it is
# not the nominally active strategy — using memory["attack_state"] instead
# of strategy.params, and self-selecting a target via score_targets.

class _EmpireApi(FakeApi):
    def __init__(self, military, empires):
        super().__init__(military)
        self._empires = empires

    def empires(self):
        return {"empires": self._empires}


def _defense_ctx(military, empires, memory=None):
    summary = {"resources": {"gold": 1000, "culture": 0}, "attacks_outgoing": [],
              "effects": {}, "ruler": {"type": ""}, "uid": 1, "era": "stone"}
    strategy = {"type": "defense", "valid_until": "2099-01-01T00:00:00Z", "params": {}}
    items = {"critters": {}, "rulers": RULERS}
    ctx = BotContext(summary, items, memory if memory is not None else {},
                     strategy, _EmpireApi(military, empires))
    return ctx


def test_self_selects_target_when_not_active_strategy():
    mil = _military([])
    empires = [{"uid": 1, "name": "Me", "is_self": True, "culture": 500, "era": "stone"},
              {"uid": 2, "name": "Weak", "culture": 100, "era": "stone"}]
    ctx = _defense_ctx(mil, empires)
    opts = AttackPlanner().propose_options(ctx, advance_phase=False)
    assert ctx.memory["attack_state"]["target_uid"] == 2
    assert ctx.memory["attack_state"]["phase"] == "strengthen"
    # Army creation spends gold, so it's gated on attack being the ACTIVE
    # strategy — background self-selection must not fund an army from
    # another strategy's (here: defense) budget.
    assert not any(o.description.startswith("add first wave") for o in opts)
    assert not any(o.description == "create army" for o in opts)
    # strategy dict (belongs to defense) must be left untouched
    assert ctx.strategy["params"] == {}


def test_no_targets_while_not_active_does_nothing():
    ctx = _defense_ctx(_military([]), [])
    opts = AttackPlanner().propose_options(ctx, advance_phase=False)
    assert opts == []
    assert "attack_state" not in ctx.memory or not ctx.memory["attack_state"]


def test_victory_while_not_active_clears_memory_not_strategy():
    mil = _military([{"iid": "MAJA", "slots": 1, "max_era": 0}])
    memory = {"attack_state": {"target_uid": 2, "target_name": "victim",
                               "phase": "wait_result"},
              "attack_history": [{"opponent": "victim", "outcome": "victory"}]}
    ctx = _defense_ctx(mil, [], memory=memory)
    AttackPlanner().propose_options(ctx, advance_phase=False)
    assert ctx.memory["attack_state"] == {}
    assert "completed" not in ctx.strategy
