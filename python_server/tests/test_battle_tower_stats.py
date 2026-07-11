"""Tests for per-tower damage/kill instrumentation used by balancing analysis.

These counters (BattleState.tower_damage/tower_kills, Critter.burn_source_sid/
last_hit_sid, removed_critters[].iid) are read-only bookkeeping — they must not
change battle outcomes, only make them analyzable.
"""

from gameserver.engine.battle_service import BattleService
from gameserver.models.battle import BattleState
from gameserver.models.critter import Critter
from gameserver.models.structure import Structure
from gameserver.models.hex import HexCoord
from gameserver.models.empire import Empire
from gameserver.models.army import Army, CritterWave


class ItemMock:
    def __init__(self, iid, **kwargs):
        self.iid = iid
        for key, value in kwargs.items():
            setattr(self, key, value)


def _make_path():
    return [HexCoord(0, 5), HexCoord(1, 4), HexCoord(2, 3), HexCoord(3, 2)]


class TestTowerDamageAttribution:
    def test_direct_hit_damage_and_kill_attributed_to_source_tower(self):
        items = {
            "soldier": ItemMock("soldier", health=2.0, speed=0.5, armour=0.0, time_between=500),
            "tower": ItemMock(
                "tower", damage=5.0, range=10, reload_time_ms=100.0,
                shot_speed=80.0, shot_type=0, effects={},
            ),
        }
        service = BattleService(items=items)
        defender = Empire(uid=1, name="Defender")
        defender.resources["life"] = 10.0
        tower = Structure(
            sid=7, iid="tower", position=HexCoord(1, 4), damage=5.0, range=10,
            reload_time_ms=100.0, shot_speed=80.0, shot_type=0, effects={},
            reload_remaining_ms=0.0,
        )
        wave = CritterWave(wave_id=1, iid="soldier", slots=1, num_critters_spawned=0, next_critter_ms=0)
        army = Army(aid=1, uid=2, name="Test Army", waves=[wave])
        battle = BattleState(
            bid=1, defender=defender, attacker_uids=[2], attack_ids=[1],
            armies={1: army}, attacker_gains={2: {}},
            structures={7: tower}, critter_path=_make_path(),
        )

        for _ in range(2000):
            service.tick(battle, 15.0)
            if battle.is_finished:
                break

        assert battle.critters_killed == 1
        assert battle.tower_kills == {7: 1}
        # 2 HP critter, single-shot tower with 5 damage → exactly 2 effective damage
        assert battle.tower_damage[7] == 2.0
        assert battle.removed_critters[0]["iid"] == "soldier"
        assert battle.removed_critters[0]["reason"] == "died"

    def test_burn_damage_and_kill_attributed_to_burning_tower(self):
        items = {
            "soldier": ItemMock("soldier", health=3.0, speed=0.5, armour=0.0, time_between=500),
            "fire_tower": ItemMock(
                "fire_tower", damage=0.0, range=10, reload_time_ms=100.0,
                shot_speed=80.0, shot_type=1,
                effects={"burn_dps": 5.0, "burn_duration": 3000.0},
            ),
        }
        service = BattleService(items=items)
        defender = Empire(uid=1, name="Defender")
        defender.resources["life"] = 10.0
        tower = Structure(
            sid=3, iid="fire_tower", position=HexCoord(1, 4), damage=0.0, range=10,
            reload_time_ms=100.0, shot_speed=80.0, shot_type=1,
            effects={"burn_dps": 5.0, "burn_duration": 3000.0},
            reload_remaining_ms=0.0,
        )
        wave = CritterWave(wave_id=1, iid="soldier", slots=1, num_critters_spawned=0, next_critter_ms=0)
        army = Army(aid=1, uid=2, name="Test Army", waves=[wave])
        battle = BattleState(
            bid=1, defender=defender, attacker_uids=[2], attack_ids=[1],
            armies={1: army}, attacker_gains={2: {}},
            structures={3: tower}, critter_path=_make_path(),
        )

        for _ in range(2000):
            service.tick(battle, 15.0)
            if battle.is_finished:
                break

        assert battle.critters_killed == 1
        assert battle.tower_kills == {3: 1}
        # All damage on this critter came from burn (base shot damage is 0) → fully attributed to sid=3
        assert battle.tower_damage[3] == 3.0

    def test_reached_critter_records_iid(self):
        items = {
            "runner": ItemMock("runner", health=1.0, speed=5.0, armour=0.0, time_between=500, damage=1.0),
        }
        service = BattleService(items=items)
        defender = Empire(uid=1, name="Defender")
        defender.resources["life"] = 10.0
        wave = CritterWave(wave_id=1, iid="runner", slots=1, num_critters_spawned=0, next_critter_ms=0)
        army = Army(aid=1, uid=2, name="Test Army", waves=[wave])
        battle = BattleState(
            bid=1, defender=defender, attacker_uids=[2], attack_ids=[1],
            armies={1: army}, attacker_gains={2: {}},
            structures={}, critter_path=_make_path(),
        )

        for _ in range(2000):
            service.tick(battle, 15.0)
            if battle.is_finished:
                break

        assert battle.critters_reached == 1
        reached = [rc for rc in battle.removed_critters if rc["reason"] == "reached"]
        assert reached[0]["iid"] == "runner"

    def test_critter_model_defaults(self):
        c = Critter(cid=1, iid="x")
        assert c.burn_source_sid == 0
        assert c.last_hit_sid == 0

    def test_battle_state_new_fields_default_empty(self):
        battle = BattleState(bid=1, defender=None)
        assert battle.tower_damage == {}
        assert battle.tower_kills == {}
