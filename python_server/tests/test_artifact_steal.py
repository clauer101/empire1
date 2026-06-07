"""Unit tests for _apply_artifact_steal and army steal multiplier."""

from unittest.mock import MagicMock

from gameserver.models.empire import Empire
from gameserver.models.battle import BattleState
from gameserver.models.army import Army, CritterWave
from gameserver.network.handlers import _apply_artifact_steal
from gameserver.network.handlers.battle_task import _army_power, _army_steal_multiplier

ATTACKER_UID = 2
DEFENDER_UID = 1


def _make_battle(attacker_uid: int = ATTACKER_UID, defender_uid: int = DEFENDER_UID) -> tuple[BattleState, Empire, Empire]:
    attacker = Empire(uid=attacker_uid, name="Attacker")
    defender = Empire(uid=defender_uid, name="Defender")
    battle = BattleState(
        bid=1,
        defender=defender,
        attacker_uids=[attacker_uid],
        attacker_gains={attacker_uid: {}},
    )
    return battle, attacker, defender


def _make_svc(attacker: Empire, victory_chance: float = 0.5, defeat_chance: float = 0.05,
              steal_power_thresholds=None, steal_min_multiplier=0.10):
    cfg = MagicMock()
    cfg.base_artifact_steal_victory = victory_chance
    cfg.base_artifact_steal_defeat = defeat_chance
    cfg.steal_power_thresholds = steal_power_thresholds or [200.0]
    cfg.steal_min_multiplier = steal_min_multiplier

    empire_svc = MagicMock()
    empire_svc.get = MagicMock(return_value=attacker)
    empire_svc.recalculate_effects = MagicMock()
    empire_svc.get_current_era = MagicMock(return_value="stone")

    svc = MagicMock()
    svc.game_config = cfg
    svc.empire_service = empire_svc
    svc.upgrade_provider = MagicMock()
    svc.upgrade_provider.items = {}
    return svc


def _item(health=1.0, armour=0.0, speed=0.0, slots=1, spawn_on_death=None):
    m = MagicMock()
    m.health = health
    m.armour = armour
    m.speed = speed
    m.slots = slots
    m.spawn_on_death = spawn_on_death or {}
    return m


# ── _army_power ────────────────────────────────────────────────────────────────

class TestArmyPower:
    def test_empty_army_returns_zero(self):
        army = Army(aid=1, uid=1, name="X", waves=[])
        assert _army_power(army, {}) == 0.0

    def test_single_wave_basic(self):
        item = _item(health=2.0, armour=0.0, speed=0.0, slots=1)
        wave = CritterWave(wave_id=1, iid="SLAVE", slots=4)
        army = Army(aid=1, uid=1, name="X", waves=[wave])
        # count=4/1=4, score=4 * 2.0 * 1.0 * 1.0 = 8.0
        assert _army_power(army, {"SLAVE": item}) == 8.0

    def test_armour_multiplies(self):
        item = _item(health=1.0, armour=1.0, speed=0.0, slots=1)
        wave = CritterWave(wave_id=1, iid="A", slots=2)
        army = Army(aid=1, uid=1, name="X", waves=[wave])
        # count=2, score=2 * 1.0 * (1+1.0) * 1.0 = 4.0
        assert _army_power(army, {"A": item}) == 4.0

    def test_speed_multiplies(self):
        item = _item(health=1.0, armour=0.0, speed=1.0, slots=1)
        wave = CritterWave(wave_id=1, iid="A", slots=3)
        army = Army(aid=1, uid=1, name="X", waves=[wave])
        # count=3, score=3 * 1.0 * 1.0 * (1+1.0) = 6.0
        assert _army_power(army, {"A": item}) == 6.0

    def test_armour_and_speed_both_multiply(self):
        item = _item(health=1.0, armour=1.0, speed=1.0, slots=1)
        wave = CritterWave(wave_id=1, iid="KNIGHT", slots=2)
        army = Army(aid=1, uid=1, name="X", waves=[wave])
        # count=2, score=2 * 1.0 * 2.0 * 2.0 = 8.0
        assert _army_power(army, {"KNIGHT": item}) == 8.0

    def test_multi_slot_critter_divides_count(self):
        item = _item(health=10.0, armour=0.0, speed=0.0, slots=2)
        wave = CritterWave(wave_id=1, iid="CART", slots=4)
        army = Army(aid=1, uid=1, name="X", waves=[wave])
        # count=4/2=2, score=2 * 10 * 1.0 * 1.0 = 20.0
        assert _army_power(army, {"CART": item}) == 20.0

    def test_multi_slot_minimum_one(self):
        # slots=0 on item should be treated as 1 (max(1, 0))
        item = _item(health=5.0, armour=0.0, speed=0.0, slots=0)
        wave = CritterWave(wave_id=1, iid="X", slots=3)
        army = Army(aid=1, uid=1, name="X", waves=[wave])
        # critter_slots=max(1,0)=1 → count=3, score=3*5*1*1=15
        assert _army_power(army, {"X": item}) == 15.0

    def test_spawn_on_death_children_included(self):
        # CART: slots=3, health=2, armour=1, speed=0.2, spawns 5 CLUBMAN on death
        # CLUBMAN: slots=1, health=2, armour=0, speed=0.2
        clubman = _item(health=2.0, armour=0.0, speed=0.2, slots=1)
        cart = _item(health=2.0, armour=1.0, speed=0.2, slots=3, spawn_on_death={"CLUBMAN": 5})
        wave = CritterWave(wave_id=1, iid="CART", slots=6)
        army = Army(aid=1, uid=1, name="X", waves=[wave])
        # count = 6/3 = 2 CARTs
        # cart power:    2 × 2.0 × (1+1.0) × (1+0.2) = 2 × 4.8 = 9.6
        # children:      2 × 5 × 2.0 × 1.0 × 1.2    = 24.0
        # total = 33.6
        result = _army_power(army, {"CART": cart, "CLUBMAN": clubman})
        assert abs(result - 33.6) < 1e-9

    def test_spawn_on_death_unknown_child_ignored(self):
        carrier = _item(health=1.0, armour=0.0, speed=0.0, slots=1, spawn_on_death={"UNKNOWN": 3})
        wave = CritterWave(wave_id=1, iid="C", slots=2)
        army = Army(aid=1, uid=1, name="X", waves=[wave])
        # unknown child not in items_by_iid → ignored, only carrier counts
        result = _army_power(army, {"C": carrier})
        assert result == 2.0

    def test_multiple_waves_summed(self):
        item_a = _item(health=2.0, slots=1)
        item_b = _item(health=3.0, slots=1)
        waves = [
            CritterWave(wave_id=1, iid="A", slots=4),
            CritterWave(wave_id=2, iid="B", slots=2),
        ]
        army = Army(aid=1, uid=1, name="X", waves=waves)
        # 4*2 + 2*3 = 8+6 = 14
        assert _army_power(army, {"A": item_a, "B": item_b}) == 14.0

    def test_unknown_iid_skipped(self):
        wave = CritterWave(wave_id=1, iid="UNKNOWN", slots=10)
        army = Army(aid=1, uid=1, name="X", waves=[wave])
        assert _army_power(army, {}) == 0.0

    def test_partial_unknown_iid_only_known_counted(self):
        item_a = _item(health=2.0, slots=1)
        waves = [
            CritterWave(wave_id=1, iid="A", slots=3),
            CritterWave(wave_id=2, iid="UNKNOWN", slots=5),
        ]
        army = Army(aid=1, uid=1, name="X", waves=waves)
        assert _army_power(army, {"A": item_a}) == 6.0


# ── _army_steal_multiplier ─────────────────────────────────────────────────────

class TestArmyStealMultiplier:
    def _gc(self, thresholds, min_mult=0.10):
        gc = MagicMock()
        gc.steal_power_thresholds = thresholds
        gc.steal_min_multiplier = min_mult
        return gc

    def _army_with_power(self, power: float) -> tuple[Army, dict]:
        """Army with a single wave whose power equals `power` (health=power, slots=1, armour=speed=0)."""
        it = _item(health=power, armour=0.0, speed=0.0, slots=1)
        wave = CritterWave(wave_id=1, iid="S", slots=1)
        return Army(aid=1, uid=1, name="X", waves=[wave]), {"S": it}

    def test_power_at_threshold_gives_one(self):
        army, items = self._army_with_power(200.0)
        gc = self._gc([200.0])
        assert _army_steal_multiplier(army, 0, items, gc) == 1.0

    def test_power_above_threshold_clamped_to_one(self):
        army, items = self._army_with_power(400.0)
        gc = self._gc([200.0])
        assert _army_steal_multiplier(army, 0, items, gc) == 1.0

    def test_half_power_gives_half_multiplier(self):
        army, items = self._army_with_power(100.0)
        gc = self._gc([200.0])
        result = _army_steal_multiplier(army, 0, items, gc)
        assert abs(result - 0.5) < 1e-9

    def test_empty_army_gives_min_multiplier(self):
        army = Army(aid=1, uid=1, name="X", waves=[])
        gc = self._gc([200.0], min_mult=0.10)
        assert _army_steal_multiplier(army, 0, {}, gc) == 0.10

    def test_never_below_min_multiplier(self):
        army = Army(aid=1, uid=1, name="X", waves=[])
        gc = self._gc([999999.0], min_mult=0.15)
        assert _army_steal_multiplier(army, 0, {}, gc) == 0.15

    def test_era_index_selects_correct_threshold(self):
        army, items = self._army_with_power(80.0)
        gc = self._gc([80.0, 180.0, 400.0])
        # era_idx=0: 80/80 → 1.0
        assert _army_steal_multiplier(army, 0, items, gc) == 1.0
        # era_idx=1: 80/180 → ~0.444
        result = _army_steal_multiplier(army, 1, items, gc)
        assert abs(result - 80 / 180) < 1e-9
        # era_idx=2: 80/400 → 0.2 > min_mult
        result2 = _army_steal_multiplier(army, 2, items, gc)
        assert abs(result2 - 80 / 400) < 1e-9

    def test_era_index_out_of_bounds_clamped_to_last(self):
        army, items = self._army_with_power(50.0)
        gc = self._gc([100.0, 200.0])
        # era_idx=99 → clamped to idx=1 → 50/200=0.25
        result = _army_steal_multiplier(army, 99, items, gc)
        assert abs(result - 0.25) < 1e-9

    def test_zero_threshold_returns_one(self):
        army, items = self._army_with_power(0.0)
        gc = self._gc([0.0])
        assert _army_steal_multiplier(army, 0, items, gc) == 1.0

    def test_gc_none_uses_defaults(self):
        army, items = self._army_with_power(100.0)
        # gc=None → thresholds=[200.0], min_mult=0.10
        result = _army_steal_multiplier(army, 0, items, None)
        assert abs(result - 0.5) < 1e-9


# ── _apply_artifact_steal — steal_chances and army_multipliers return ─────────

class TestApplyArtifactStealReturnValues:
    def test_returns_three_tuple(self):
        battle, attacker, defender = _make_battle()
        svc = _make_svc(attacker, victory_chance=0.3)
        result = _apply_artifact_steal(battle, svc, attacker_won=True)
        assert len(result) == 3

    def test_steal_chances_keyed_by_uid(self):
        battle, attacker, defender = _make_battle()
        defender.artifacts = ["ART"]
        svc = _make_svc(attacker, victory_chance=0.3)
        _, chances, _ = _apply_artifact_steal(battle, svc, attacker_won=True)
        assert ATTACKER_UID in chances
        assert abs(chances[ATTACKER_UID] - 0.3) < 1e-4

    def test_army_multipliers_keyed_by_uid(self):
        battle, attacker, defender = _make_battle()
        defender.artifacts = ["ART"]
        svc = _make_svc(attacker, victory_chance=0.3)
        _, _, mults = _apply_artifact_steal(battle, svc, attacker_won=True)
        assert ATTACKER_UID in mults

    def test_army_multiplier_one_when_no_army(self):
        battle, attacker, defender = _make_battle()
        defender.artifacts = ["ART"]
        svc = _make_svc(attacker, victory_chance=0.5,
                        steal_power_thresholds=[200.0], steal_min_multiplier=0.10)
        _, _, mults = _apply_artifact_steal(battle, svc, attacker_won=True)
        assert abs(mults[ATTACKER_UID] - 1.0) < 1e-4

    def test_army_multiplier_reduced_for_weak_army(self):
        battle, attacker, defender = _make_battle()
        defender.artifacts = ["ART"]
        empty_army = Army(aid=1, uid=ATTACKER_UID, name="Tiny", waves=[])
        battle.armies[ATTACKER_UID] = empty_army
        svc = _make_svc(attacker, victory_chance=1.0,
                        steal_power_thresholds=[200.0], steal_min_multiplier=0.10)
        _, chances, mults = _apply_artifact_steal(battle, svc, attacker_won=True)
        assert abs(mults[ATTACKER_UID] - 0.10) < 1e-4
        assert abs(chances[ATTACKER_UID] - 0.10) < 1e-4

    def test_steal_chance_is_raw_times_multiplier(self):
        battle, attacker, defender = _make_battle()
        defender.artifacts = ["ART"]
        # Army with exactly half the threshold power → multiplier=0.5
        it = _item(health=100.0, armour=0.0, speed=0.0, slots=1)
        wave = CritterWave(wave_id=1, iid="S", slots=1)
        army = Army(aid=1, uid=ATTACKER_UID, name="Half", waves=[wave])
        battle.armies[ATTACKER_UID] = army
        svc = _make_svc(attacker, victory_chance=0.4,
                        steal_power_thresholds=[200.0], steal_min_multiplier=0.10)
        svc.upgrade_provider.items = {"S": it}
        _, chances, mults = _apply_artifact_steal(battle, svc, attacker_won=True)
        # power=100, threshold=200 → multiplier=0.5; chance=0.4*0.5=0.2
        assert abs(mults[ATTACKER_UID] - 0.5) < 1e-4
        assert abs(chances[ATTACKER_UID] - 0.2) < 1e-4


# ── Multi-army: strongest multiplier is used ──────────────────────────────────

class TestMultiArmyMaxMultiplier:
    def test_max_multiplier_chosen_across_armies(self):
        battle, attacker, defender = _make_battle()
        defender.artifacts = ["ART"]
        it_weak = _item(health=1.0, armour=0.0, speed=0.0, slots=1)   # power=1
        it_strong = _item(health=200.0, armour=0.0, speed=0.0, slots=1)  # power=200

        weak_army = Army(aid=1, uid=ATTACKER_UID, name="Weak",
                         waves=[CritterWave(wave_id=1, iid="WEAK", slots=1)])
        strong_army = Army(aid=2, uid=ATTACKER_UID, name="Strong",
                           waves=[CritterWave(wave_id=1, iid="STRONG", slots=1)])
        battle.armies[1] = weak_army
        battle.armies[2] = strong_army

        svc = _make_svc(attacker, victory_chance=0.5,
                        steal_power_thresholds=[200.0], steal_min_multiplier=0.10)
        svc.upgrade_provider.items = {"WEAK": it_weak, "STRONG": it_strong}

        _, chances, mults = _apply_artifact_steal(battle, svc, attacker_won=True)

        # strong_army: power=200/threshold=200 → mult=1.0 (should win over weak)
        assert abs(mults[ATTACKER_UID] - 1.0) < 1e-4
        assert abs(chances[ATTACKER_UID] - 0.5) < 1e-4

    def test_weak_army_alone_uses_min_multiplier(self):
        battle, attacker, defender = _make_battle()
        defender.artifacts = ["ART"]
        it_weak = _item(health=1.0, armour=0.0, speed=0.0, slots=1)
        weak_army = Army(aid=1, uid=ATTACKER_UID, name="Weak",
                         waves=[CritterWave(wave_id=1, iid="WEAK", slots=1)])
        battle.armies[ATTACKER_UID] = weak_army

        svc = _make_svc(attacker, victory_chance=1.0,
                        steal_power_thresholds=[200.0], steal_min_multiplier=0.10)
        svc.upgrade_provider.items = {"WEAK": it_weak}

        _, chances, mults = _apply_artifact_steal(battle, svc, attacker_won=True)

        # power=1/200=0.005 → clamped to min_mult=0.10
        assert abs(mults[ATTACKER_UID] - 0.10) < 1e-4

    def test_three_armies_max_wins(self):
        battle, attacker, defender = _make_battle()
        defender.artifacts = ["ART"]
        items = {}
        for name, power in [("A", 10.0), ("B", 150.0), ("C", 80.0)]:
            items[name] = _item(health=power, armour=0.0, speed=0.0, slots=1)
            army = Army(aid=ord(name), uid=ATTACKER_UID, name=name,
                        waves=[CritterWave(wave_id=1, iid=name, slots=1)])
            battle.armies[ord(name)] = army

        svc = _make_svc(attacker, victory_chance=1.0,
                        steal_power_thresholds=[200.0], steal_min_multiplier=0.10)
        svc.upgrade_provider.items = items

        _, _, mults = _apply_artifact_steal(battle, svc, attacker_won=True)

        # max power=150 → mult=150/200=0.75
        assert abs(mults[ATTACKER_UID] - 0.75) < 1e-4


# ── Existing behavior tests (updated for 3-tuple return) ─────────────────────

class TestAttackerWin:
    def test_steals_artifact_when_roll_succeeds(self):
        battle, attacker, defender = _make_battle()
        defender.artifacts = ["SWORD_OF_POWER"]
        svc = _make_svc(attacker, victory_chance=1.0)

        stolen, chances, _ = _apply_artifact_steal(battle, svc, attacker_won=True)

        assert len(stolen) == 1
        assert stolen[0] == ("SWORD_OF_POWER", ATTACKER_UID)
        assert "SWORD_OF_POWER" not in defender.artifacts
        assert "SWORD_OF_POWER" in attacker.artifacts

    def test_no_steal_when_roll_fails(self):
        battle, attacker, defender = _make_battle()
        defender.artifacts = ["SWORD_OF_POWER"]
        svc = _make_svc(attacker, victory_chance=0.0)

        stolen, chances, _ = _apply_artifact_steal(battle, svc, attacker_won=True)

        assert stolen == []
        assert defender.artifacts == ["SWORD_OF_POWER"]
        assert attacker.artifacts == []

    def test_no_steal_when_defender_has_no_artifacts(self):
        battle, attacker, defender = _make_battle()
        svc = _make_svc(attacker, victory_chance=1.0)

        stolen, chances, _ = _apply_artifact_steal(battle, svc, attacker_won=True)

        assert stolen == []

    def test_all_artifacts_stolen_when_chance_is_one(self):
        battle, attacker, defender = _make_battle()
        defender.artifacts = ["ART_A", "ART_B", "ART_C"]
        svc = _make_svc(attacker, victory_chance=1.0)

        stolen, chances, _ = _apply_artifact_steal(battle, svc, attacker_won=True)

        assert len(stolen) == 3
        assert len(attacker.artifacts) == 3
        assert len(defender.artifacts) == 0

    def test_recalculate_effects_called_on_both_empires(self):
        battle, attacker, defender = _make_battle()
        defender.artifacts = ["SWORD_OF_POWER"]
        svc = _make_svc(attacker, victory_chance=1.0)

        _apply_artifact_steal(battle, svc, attacker_won=True)

        calls = [c.args[0] for c in svc.empire_service.recalculate_effects.call_args_list]
        assert defender in calls
        assert attacker in calls

    def test_uses_victory_chance_not_defeat_chance(self):
        battle, attacker, defender = _make_battle()
        defender.artifacts = ["ART"]
        svc = _make_svc(attacker, victory_chance=0.0, defeat_chance=1.0)

        stolen, chances, _ = _apply_artifact_steal(battle, svc, attacker_won=True)

        assert stolen == []

    def test_army_power_multiplier_reduces_chance(self):
        battle, attacker, defender = _make_battle()
        defender.artifacts = ["ART"]
        empty_army = Army(aid=1, uid=ATTACKER_UID, name="Tiny", waves=[])
        battle.armies[ATTACKER_UID] = empty_army
        svc = _make_svc(attacker, victory_chance=1.0,
                        steal_power_thresholds=[200.0], steal_min_multiplier=0.10)

        _, chances, _ = _apply_artifact_steal(battle, svc, attacker_won=True)

        assert abs(chances[ATTACKER_UID] - 0.10) < 1e-4


class TestDefenderWin:
    def test_attacker_can_still_steal_from_defender_on_loss(self):
        battle, attacker, defender = _make_battle()
        defender.artifacts = ["CROWN"]
        svc = _make_svc(attacker, defeat_chance=1.0)

        stolen, chances, _ = _apply_artifact_steal(battle, svc, attacker_won=False)

        assert stolen == [("CROWN", ATTACKER_UID)]
        assert "CROWN" not in defender.artifacts
        assert "CROWN" in attacker.artifacts

    def test_attacker_does_not_lose_own_artifacts_on_loss(self):
        battle, attacker, defender = _make_battle()
        attacker.artifacts = ["SWORD"]
        defender.artifacts = []
        svc = _make_svc(attacker, defeat_chance=1.0)

        _apply_artifact_steal(battle, svc, attacker_won=False)

        assert attacker.artifacts == ["SWORD"]

    def test_no_steal_when_roll_fails(self):
        battle, attacker, defender = _make_battle()
        defender.artifacts = ["CROWN"]
        svc = _make_svc(attacker, defeat_chance=0.0)

        stolen, chances, _ = _apply_artifact_steal(battle, svc, attacker_won=False)

        assert stolen == []
        assert defender.artifacts == ["CROWN"]
