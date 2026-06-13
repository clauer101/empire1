import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bot.army_building import (  # noqa: E402
    ADD_WAVE_MIN_SLOTS,
    BUILD_BASE_POWER,
    army_power,
    build_up_target,
    critter_power,
    next_skill,
    pick_ruler,
    ruler_wave_target,
    strengthen_plan,
)
from bot.planners.attack import AttackPlanner  # noqa: E402
from bot.planners.base import BotContext  # noqa: E402

RULERS = {"MAJA": {}, "BORIN": {}}
RULER_IIDS = set(RULERS)


def _critter(iid, era=0, slots=1, health=10, armour=0.0, speed=1.0):
    return {"iid": iid, "era_index": era, "slots": slots,
            "health": health, "armour": armour, "speed": speed}


def _military(waves, available=None, next_wave_price=500.0):
    return {"armies": [{"aid": 1, "waves": waves,
                        "next_wave_price": next_wave_price}],
            "available_critters": available or []}


# ── ruler helpers ─────────────────────────────────────────────────────────

def test_pick_ruler_random_from_catalog():
    # Always a catalog member; single option is deterministic; empty → None
    picks = {pick_ruler(RULERS) for _ in range(50)}
    assert picks <= set(RULERS)
    assert len(picks) > 1  # spreads over the catalog, not always the same
    assert pick_ruler({"BORIN": {}}) == "BORIN"
    assert pick_ruler({}) is None


def test_next_skill_order_and_caps():
    assert next_skill({"q": 0, "w": 0, "e": 0, "r": 0}) == "r"
    assert next_skill({"q": 0, "w": 0, "e": 0, "r": 3}) == "q"
    assert next_skill({"q": 5, "w": 5, "e": 4, "r": 3}) == "e"
    assert next_skill({"q": 5, "w": 5, "e": 5, "r": 3}) is None


def test_ruler_wave_target_picks_strongest_army_wave_zero():
    armies = [
        {"aid": 1, "waves": [{"iid": "SLAVE"}]},
        {"aid": 2, "waves": [{"iid": "SLAVE"}, {"iid": "SLAVE"}]},
    ]
    assert ruler_wave_target(armies, RULER_IIDS) == (2, 0)


def test_ruler_wave_target_none_when_already_placed():
    armies = [{"aid": 1, "waves": [{"iid": "MAJA"}]}]
    assert ruler_wave_target(armies, RULER_IIDS) is None
    assert ruler_wave_target([], RULER_IIDS) is None


# ── strengthen plan ───────────────────────────────────────────────────────

def test_free_critter_switch_ranks_first():
    weak, strong = _critter("WEAK", health=5), _critter("STRONG", health=50)
    mil = _military([{"iid": "WEAK", "slots": 2, "max_era": 0,
                      "next_slot_price": 100.0, "next_era_price": 200.0}],
                    [weak, strong])
    options = strengthen_plan(mil, {}, RULER_IIDS)
    assert options[0].kind == "switch_critter"
    assert options[0].critter_iid == "STRONG" and options[0].price == 0.0


def test_wave_era_proposed_when_stronger_critter_above():
    cur, above = _critter("CUR", era=0, health=10), _critter("NEXT", era=1, health=100)
    mil = _military([{"iid": "CUR", "slots": 1, "max_era": 0,
                      "next_slot_price": 1000.0, "next_era_price": 50.0}],
                    [cur, above])
    # era "bronze" (rank 2) > wave max_era 0 → climbing to current era is tier 0
    options = strengthen_plan(mil, {"era": "bronze"}, RULER_IIDS)
    paid = [o for o in options if o.price > 0]
    assert paid[0].kind == "buy_wave_era"  # tier 0 beats the slot


def test_add_wave_only_when_waves_maxed_and_stocked():
    cur = _critter("CUR", health=10)
    # under-stocked (slots 1 < ADD_WAVE_MIN_SLOTS) → no add_wave yet
    under = _military([{"iid": "CUR", "slots": 1, "max_era": 0,
                        "next_slot_price": 100.0, "next_era_price": 0.0}],
                      [cur])
    assert "add_wave" not in {o.kind for o in strengthen_plan(under, {}, RULER_IIDS)}
    # at current era (stone rank 0) and well-stocked → add_wave allowed
    stocked = _military([{"iid": "CUR", "slots": ADD_WAVE_MIN_SLOTS, "max_era": 0,
                          "next_slot_price": 100.0, "next_era_price": 0.0}],
                        [cur])
    assert "add_wave" in {o.kind for o in strengthen_plan(stocked, {}, RULER_IIDS)}


def test_ruler_wave_never_touched():
    cur = _critter("CUR", health=10)
    mil = _military([{"iid": "MAJA", "slots": 1, "max_era": 0,
                      "next_slot_price": 100.0, "next_era_price": 100.0}],
                    [cur])
    options = strengthen_plan(mil, {}, RULER_IIDS)
    assert all(o.kind in ("add_wave", "create_army") for o in options)


def test_second_army_after_four_waves():
    cur = _critter("CUR", health=10)
    wave = {"iid": "CUR", "slots": 1, "max_era": 0,
            "next_slot_price": 100.0, "next_era_price": 0.0}
    # 3 waves → still no second army
    mil3 = _military([dict(wave)] * 3, [cur])
    assert "create_army" not in {
        o.kind for o in strengthen_plan(mil3, {"army_price": 800.0}, RULER_IIDS)}
    # 4 waves (MIN_WAVES_FOR_SECOND_ARMY) → second army allowed
    mil4 = _military([dict(wave)] * 4, [cur])
    assert "create_army" in {
        o.kind for o in strengthen_plan(mil4, {"army_price": 800.0}, RULER_IIDS)}


def test_buy_wave_era_beats_slot_when_below_current_era():
    # Cheap slot (great gain/gold) vs expensive era-up; wave below current era.
    # The era-up is tier 0 and must rank first despite worse gain/gold.
    cur, above = _critter("CUR", era=0, health=10), _critter("NEXT", era=1, health=100)
    mil = _military([{"iid": "CUR", "slots": 1, "max_era": 0,
                      "next_slot_price": 5.0, "next_era_price": 5000.0}],
                    [cur, above])
    options = strengthen_plan(mil, {"era": "bronze"}, RULER_IIDS)
    paid = [o for o in options if o.price > 0]
    assert paid[0].kind == "buy_wave_era"
    slot = next(o for o in paid if o.kind == "buy_slot")
    era = next(o for o in paid if o.kind == "buy_wave_era")
    assert era.tier < slot.tier


def test_slot_deprioritized_when_wave_below_current_era():
    cur = _critter("CUR", era=0, health=10)
    mil = _military([{"iid": "CUR", "slots": 1, "max_era": 0,
                      "next_slot_price": 100.0, "next_era_price": 0.0}],
                    [cur])
    options = strengthen_plan(mil, {"era": "bronze"}, RULER_IIDS)
    slot = next(o for o in options if o.kind == "buy_slot")
    assert slot.tier == 2


# ── build-up helpers ──────────────────────────────────────────────────────

def test_army_power_sums_filled_non_ruler_waves():
    cur = _critter("CUR", health=10, slots=2)  # power 10*1*2/2 = 10 per slot
    mil = {"armies": [{"aid": 1, "waves": [
        {"iid": "CUR", "slots": 2},   # 10 * 2 = 20
        {"iid": "MAJA", "slots": 1},  # ruler — skipped
        {"iid": "", "slots": 1},      # empty — skipped
    ]}], "available_critters": [cur]}
    assert army_power(mil, RULER_IIDS) == 20.0


def test_build_up_target_lean_when_no_history():
    # Lean, era-independent floor: high era still returns the base target.
    assert build_up_target({"era": "stone"}, {}, 0.0) == BUILD_BASE_POWER
    assert build_up_target({"era": "renaissance"}, {}, 0.0) == BUILD_BASE_POWER


def test_build_up_target_scales_above_current_after_defeat():
    summary = {"era": "stone"}
    opp = {"last_outcome": "defeat", "est_strength": 0.5}
    # cur_power high enough that opponent-relative beats baseline
    target = build_up_target(summary, opp, 200.0)
    assert target == 200.0 * 1.5  # cur * (1 + 0.5*K), K=1 ; > lean base
    # a victory / no defeat keeps the lean base target
    assert build_up_target(summary, {"last_outcome": "victory"}, 200.0) == BUILD_BASE_POWER


def test_critter_power_per_slot():
    assert critter_power(_critter("A", slots=2, health=20, armour=1.0, speed=1.0)) == \
        20 * 2.0 * 2.0 / 2


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


def _ctx(military, summary=None, memory=None):
    summary = summary or {"resources": {"gold": 1000, "culture": 0},
                          "attacks_outgoing": [], "effects": {},
                          "ruler": {"type": ""}}
    strategy = {"type": "attack", "valid_until": "2099-01-01T00:00:00Z",
                "params": {"target_uid": 9, "target_name": "victim"}}
    items = {"critters": {}, "rulers": RULERS}
    return BotContext(summary, items, memory if memory is not None else {},
                      strategy, FakeApi(military))


def _full_summary(ruler_type="MAJA", gold=1000):
    return {"resources": {"gold": gold, "culture": 0}, "attacks_outgoing": [],
            "effects": {"ruler_unlock": 1},
            "ruler": {"type": ruler_type, "q": 5, "w": 5, "e": 5, "r": 3}}


def test_defeat_switches_to_strengthen_then_attack():
    cur = _critter("CUR", health=10)
    mil = _military([{"iid": "MAJA", "slots": 1, "max_era": 0},  # ruler wave
                     {"iid": "CUR", "slots": 1, "max_era": 0,
                      "next_slot_price": 100.0, "next_era_price": 0.0}])
    mil["available_critters"] = [cur]
    ctx = _ctx(mil, summary=_full_summary(),
               memory={"attack_history": [{"opponent": "victim",
                                           "outcome": "defeat"}]})
    ctx.strategy["params"]["phase"] = "wait_result"
    assert AttackPlanner().propose(ctx) is None
    assert ctx.strategy["params"]["phase"] == "strengthen"
    assert ctx.strategy["params"]["defeats"] == 1
    action = AttackPlanner().propose(ctx)
    assert action is not None
    assert ctx.strategy["params"]["phase"] == "attack"


def test_gives_up_after_max_defeats():
    mil = _military([{"iid": "MAJA", "slots": 1, "max_era": 0}])
    ctx = _ctx(mil, summary=_full_summary(),
               memory={"attack_history": [{"opponent": "victim",
                                           "outcome": "defeat"}]})
    from bot.army_building import MAX_STRENGTHEN_ROUNDS
    ctx.strategy["params"].update({"phase": "wait_result",
                                   "defeats": MAX_STRENGTHEN_ROUNDS})
    assert AttackPlanner().propose(ctx) is None
    assert ctx.strategy.get("completed") is True


def test_strengthen_sets_savings_goal_when_unaffordable():
    cur = _critter("CUR", health=10)
    mil = _military([{"iid": "MAJA", "slots": 1, "max_era": 0},
                     {"iid": "CUR", "slots": 1, "max_era": 0,
                      "next_slot_price": 5000.0, "next_era_price": 0.0}],
                    [cur], next_wave_price=9000.0)
    ctx = _ctx(mil, summary=_full_summary(gold=10))
    ctx.strategy["params"]["phase"] = "strengthen"
    # The planner no longer sets the goal itself; it emits a mandatory option
    # that carries the savings target (the dispatcher declares the goal).
    opts = AttackPlanner().propose_options(ctx)
    assert opts and opts[0].saves_for == 5000.0
    assert opts[0].goal_meta and opts[0].goal_meta.get("sticky") is True



def test_places_ruler_in_wave():
    mil = _military([{"iid": "SLAVE", "slots": 1, "max_era": 0}])
    action = AttackPlanner().propose(_ctx(mil, summary=_full_summary()))
    assert action and "place ruler MAJA" in action.description
    api = FakeApi(mil)
    action.run(api)
    assert api.calls == [("set_ruler_wave", (1, 0, "MAJA"))]
