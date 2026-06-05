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


# ── _army_power ────────────────────────────────────────────────────────────────

class TestArmyPower:
    def _item(self, health=1.0, armour=0.0, speed=0.15, slots=1):
        m = MagicMock()
        m.health = health
        m.armour = armour
        m.speed = speed
        m.slots = slots
        return m

    def test_empty_army_returns_zero(self):
        army = Army(aid=1, uid=1, name="X", waves=[])
        assert _army_power(army, {}) == 0.0

    def test_single_wave_basic(self):
        item = self._item(health=2.0, armour=0.0, speed=0.0, slots=1)
        wave = CritterWave(wave_id=1, iid="SLAVE", slots=4)
        army = Army(aid=1, uid=1, name="X", waves=[wave])
        # count=4/1=4, score=4 * 2.0 * 1.0 * 1.0 = 8.0
        assert _army_power(army, {"SLAVE": item}) == 8.0

    def test_armour_and_speed_multiply(self):
        item = self._item(health=1.0, armour=1.0, speed=1.0, slots=1)
        wave = CritterWave(wave_id=1, iid="KNIGHT", slots=2)
        army = Army(aid=1, uid=1, name="X", waves=[wave])
        # count=2, score=2 * 1.0 * 2.0 * 2.0 = 8.0
        assert _army_power(army, {"KNIGHT": item}) == 8.0

    def test_multi_slot_critter_divides_count(self):
        item = self._item(health=10.0, armour=0.0, speed=0.0, slots=2)
        wave = CritterWave(wave_id=1, iid="CART", slots=4)
        army = Army(aid=1, uid=1, name="X", waves=[wave])
        # count=4/2=2, score=2 * 10 * 1.0 * 1.0 = 20.0
        assert _army_power(army, {"CART": item}) == 20.0

    def test_unknown_iid_skipped(self):
        wave = CritterWave(wave_id=1, iid="UNKNOWN", slots=10)
        army = Army(aid=1, uid=1, name="X", waves=[wave])
        assert _army_power(army, {}) == 0.0


# ── _army_steal_multiplier ─────────────────────────────────────────────────────

class TestArmyStealMultiplier:
    def _item(self, health=1.0, armour=0.0, speed=0.0, slots=1):
        m = MagicMock()
        m.health = health
        m.armour = armour
        m.speed = speed
        m.slots = slots
        return m

    def _gc(self, thresholds, min_mult=0.10):
        gc = MagicMock()
        gc.steal_power_thresholds = thresholds
        gc.steal_min_multiplier = min_mult
        return gc

    def test_full_army_gives_multiplier_one(self):
        item = self._item(health=1.0)
        wave = CritterWave(wave_id=1, iid="S", slots=200)
        army = Army(aid=1, uid=1, name="X", waves=[wave])
        gc = self._gc([200.0])
        assert _army_steal_multiplier(army, 0, {"S": item}, gc) == 1.0

    def test_empty_army_gives_min_multiplier(self):
        army = Army(aid=1, uid=1, name="X", waves=[])
        gc = self._gc([200.0], min_mult=0.10)
        assert _army_steal_multiplier(army, 0, {}, gc) == 0.10

    def test_half_power_gives_half_multiplier(self):
        item = self._item(health=1.0)
        wave = CritterWave(wave_id=1, iid="S", slots=100)
        army = Army(aid=1, uid=1, name="X", waves=[wave])
        gc = self._gc([200.0])
        result = _army_steal_multiplier(army, 0, {"S": item}, gc)
        assert abs(result - 0.5) < 1e-9

    def test_era_index_selects_correct_threshold(self):
        item = self._item(health=1.0)
        wave = CritterWave(wave_id=1, iid="S", slots=80)
        army = Army(aid=1, uid=1, name="X", waves=[wave])
        gc = self._gc([80.0, 180.0, 400.0])
        # era_idx=0: power=80 / threshold=80 → 1.0
        assert _army_steal_multiplier(army, 0, {"S": item}, gc) == 1.0
        # era_idx=1: power=80 / threshold=180 → ~0.44
        result = _army_steal_multiplier(army, 1, {"S": item}, gc)
        assert abs(result - 80/180) < 1e-9

    def test_never_below_min_multiplier(self):
        army = Army(aid=1, uid=1, name="X", waves=[])
        gc = self._gc([999999.0], min_mult=0.15)
        assert _army_steal_multiplier(army, 0, {}, gc) == 0.15


# ── _apply_artifact_steal ─────────────────────────────────────────────────────

class TestAttackerWin:
    def test_steals_artifact_when_roll_succeeds(self):
        battle, attacker, defender = _make_battle()
        defender.artifacts = ["SWORD_OF_POWER"]
        svc = _make_svc(attacker, victory_chance=1.0)

        stolen, chances = _apply_artifact_steal(battle, svc, attacker_won=True)

        assert len(stolen) == 1
        assert stolen[0] == ("SWORD_OF_POWER", ATTACKER_UID)
        assert "SWORD_OF_POWER" not in defender.artifacts
        assert "SWORD_OF_POWER" in attacker.artifacts

    def test_no_steal_when_roll_fails(self):
        battle, attacker, defender = _make_battle()
        defender.artifacts = ["SWORD_OF_POWER"]
        svc = _make_svc(attacker, victory_chance=0.0)

        stolen, chances = _apply_artifact_steal(battle, svc, attacker_won=True)

        assert stolen == []
        assert defender.artifacts == ["SWORD_OF_POWER"]
        assert attacker.artifacts == []

    def test_no_steal_when_defender_has_no_artifacts(self):
        battle, attacker, defender = _make_battle()
        svc = _make_svc(attacker, victory_chance=1.0)

        stolen, chances = _apply_artifact_steal(battle, svc, attacker_won=True)

        assert stolen == []

    def test_all_artifacts_stolen_when_chance_is_one(self):
        battle, attacker, defender = _make_battle()
        defender.artifacts = ["ART_A", "ART_B", "ART_C"]
        svc = _make_svc(attacker, victory_chance=1.0)

        stolen, chances = _apply_artifact_steal(battle, svc, attacker_won=True)

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

        stolen, chances = _apply_artifact_steal(battle, svc, attacker_won=True)

        assert stolen == []  # victory_chance=0 → no steal despite defeat_chance=1

    def test_steal_chances_returned_per_attacker(self):
        battle, attacker, defender = _make_battle()
        svc = _make_svc(attacker, victory_chance=0.3)

        _, chances = _apply_artifact_steal(battle, svc, attacker_won=True)

        assert ATTACKER_UID in chances
        # No army in battle.armies → multiplier=1.0 → chance = 0.3
        assert abs(chances[ATTACKER_UID] - 0.3) < 1e-4

    def test_army_power_multiplier_reduces_chance(self):
        battle, attacker, defender = _make_battle()
        # Attach an empty army — power=0 → multiplier=min_mult=0.1
        empty_army = Army(aid=1, uid=ATTACKER_UID, name="Tiny", waves=[])
        battle.armies[ATTACKER_UID] = empty_army
        svc = _make_svc(attacker, victory_chance=1.0,
                        steal_power_thresholds=[200.0], steal_min_multiplier=0.10)

        _, chances = _apply_artifact_steal(battle, svc, attacker_won=True)

        assert abs(chances[ATTACKER_UID] - 0.10) < 1e-4


# ── Defender-win (attacker defeated) ─────────────────────────────────────────

class TestDefenderWin:
    def test_attacker_can_still_steal_from_defender_on_loss(self):
        battle, attacker, defender = _make_battle()
        defender.artifacts = ["CROWN"]
        svc = _make_svc(attacker, defeat_chance=1.0)

        stolen, chances = _apply_artifact_steal(battle, svc, attacker_won=False)

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

        stolen, chances = _apply_artifact_steal(battle, svc, attacker_won=False)

        assert stolen == []
        assert defender.artifacts == ["CROWN"]
