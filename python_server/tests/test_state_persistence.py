"""Tests for state_save and state_load round-trip persistence."""

from __future__ import annotations

import asyncio
import os
import tempfile
from pathlib import Path

import pytest

from gameserver.models.army import Army, CritterWave, SpyArmy
from gameserver.models.attack import Attack, AttackPhase
from gameserver.models.battle import BattleState
from gameserver.models.critter import Critter
from gameserver.models.empire import Empire
from gameserver.models.hex import HexCoord
from gameserver.models.map import Direction, HexMap
from gameserver.models.shot import Shot
from gameserver.models.structure import Structure
from gameserver.persistence.state_load import RestoredState, load_state
from gameserver.persistence.state_save import save_state


# -------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------

def _make_empire(uid: int = 1, name: str = "TestEmpire") -> Empire:
    """Create a fully populated test empire."""
    return Empire(
        uid=uid,
        name=name,
        resources={"gold": 123.45, "culture": 67.89, "life": 8.5},
        buildings={"farm": 15.0, "barracks": 0.0},
        knowledge={"archery": 30.0, "masonry": 0.0},
        citizens={"merchant": 3, "scientist": 2, "artist": 1},
        effects={"gold_bonus": 0.5, "research_bonus": 0.2},
        artefacts=["ruby_ring", "iron_shield"],
        max_life=12.0,
        structures={
            10: Structure(
                sid=10, iid="arrow_tower",
                position=HexCoord(3, -1),
                damage=5.0, range=3, reload_time_ms=1500.0,
                shot_speed=8.0, shot_type="arrow",
                effects={"slow": 0.3},
            ),
        },
        armies=[
            Army(
                aid=1, uid=uid, direction=Direction.NORTH, name="Alpha",
                waves=[
                    CritterWave(
                        critter_iid="goblin", slots=5,
                        critters=[
                            Critter(cid=100, iid="goblin", health=10.0,
                                    max_health=10.0, speed=1.5, armour=0.0,
                                    path=[HexCoord(0, 0), HexCoord(1, 0), HexCoord(2, 0)],
                                    path_progress=0.5,
                                    capture={"gold": 2.0}, bonus={"gold": 1.0}),
                        ],
                        spawn_interval_ms=600.0,
                        next_spawn_ms=200.0,
                        spawn_pointer=1,
                    ),
                ],
                wave_pointer=0,
                next_wave_ms=20000.0,
            ),
        ],
        spies=[
            SpyArmy(aid=5, uid=uid, options={"spy_defense": 500.0}),
        ],
        bosses={
            "dragon": Critter(
                cid=999, iid="dragon", health=100.0, max_health=100.0,
                speed=0.5, armour=5.0, level=3, xp=250.0, is_boss=True,
            ),
        },
        empire_map=HexMap(
            paths={
                Direction.NORTH: [HexCoord(0, 0), HexCoord(0, -1), HexCoord(0, -2)],
                Direction.SOUTH: [HexCoord(0, 0), HexCoord(0, 1)],
            },
            build_tiles={HexCoord(1, 0), HexCoord(2, 0), HexCoord(3, -1)},
            occupied={HexCoord(3, -1)},
        ),
    )


def _make_attack() -> Attack:
    return Attack(
        attack_id=42,
        attacker_uid=1,
        defender_uid=2,
        army_aid=1,
        phase=AttackPhase.IN_SIEGE,
        eta_seconds=0.0,
        siege_remaining_seconds=120.5,
    )


def _make_battle() -> BattleState:
    return BattleState(
        bid=7,
        defender_uid=2,
        attacker_uids=[1],
        critters={
            200: Critter(cid=200, iid="orc", health=20.0, max_health=20.0,
                         speed=1.0, armour=1.0,
                         path=[HexCoord(0, 0), HexCoord(1, 0)]),
        },
        structures={
            10: Structure(sid=10, iid="arrow_tower", position=HexCoord(2, 0),
                          damage=5.0, range=3, reload_time_ms=1500.0,
                          shot_speed=8.0),
        },
        pending_shots=[
            Shot(damage=5.0, target_cid=200, source_sid=10,
                 effects={"slow": 0.2}, flight_remaining_ms=300.0),
        ],
        elapsed_ms=5000.0,
        observer_uids={1, 2, 3},
        attacker_gains={1: {"gold": 10.0}},
        defender_losses={"life": 2.0},
    )


# -------------------------------------------------------------------
# Tests
# -------------------------------------------------------------------

class TestSaveLoad:
    """Round-trip serialization / deserialization tests."""

    def _run(self, coro):
        """Helper to run async tests on Python 3.9."""
        return asyncio.get_event_loop().run_until_complete(coro)

    def test_save_creates_file(self, tmp_path: Path) -> None:
        path = str(tmp_path / "state.yaml")
        empire = _make_empire()
        self._run(save_state({empire.uid: empire}, path=path))
        assert Path(path).exists()

    def test_load_nonexistent_returns_none(self, tmp_path: Path) -> None:
        result = self._run(load_state(str(tmp_path / "nope.yaml")))
        assert result is None

    def test_round_trip_meta(self, tmp_path: Path) -> None:
        path = str(tmp_path / "state.yaml")
        empire = _make_empire()
        self._run(save_state({empire.uid: empire}, path=path))
        restored = self._run(load_state(path))
        assert restored is not None
        assert restored.meta["version"] == 1
        assert "saved_at" in restored.meta

    def test_round_trip_empire_basics(self, tmp_path: Path) -> None:
        path = str(tmp_path / "state.yaml")
        src = _make_empire(uid=42, name="Roundtrip")
        self._run(save_state({src.uid: src}, path=path))
        restored = self._run(load_state(path))
        assert restored is not None
        e = restored.empires[42]
        assert e.uid == 42
        assert e.name == "Roundtrip"
        assert e.resources["gold"] == pytest.approx(123.45)
        assert e.resources["culture"] == pytest.approx(67.89)
        assert e.resources["life"] == pytest.approx(8.5)
        assert e.max_life == 12.0

    def test_round_trip_buildings_knowledge(self, tmp_path: Path) -> None:
        path = str(tmp_path / "state.yaml")
        src = _make_empire()
        self._run(save_state({src.uid: src}, path=path))
        e = self._run(load_state(path)).empires[src.uid]
        assert e.buildings == {"farm": 15.0, "barracks": 0.0}
        assert e.knowledge == {"archery": 30.0, "masonry": 0.0}

    def test_round_trip_citizens(self, tmp_path: Path) -> None:
        path = str(tmp_path / "state.yaml")
        src = _make_empire()
        self._run(save_state({src.uid: src}, path=path))
        e = self._run(load_state(path)).empires[src.uid]
        assert e.citizens == {"merchant": 3, "scientist": 2, "artist": 1}

    def test_round_trip_effects_artefacts(self, tmp_path: Path) -> None:
        path = str(tmp_path / "state.yaml")
        src = _make_empire()
        self._run(save_state({src.uid: src}, path=path))
        e = self._run(load_state(path)).empires[src.uid]
        assert e.effects["gold_bonus"] == pytest.approx(0.5)
        assert e.artefacts == ["ruby_ring", "iron_shield"]

    def test_round_trip_structures(self, tmp_path: Path) -> None:
        path = str(tmp_path / "state.yaml")
        src = _make_empire()
        self._run(save_state({src.uid: src}, path=path))
        e = self._run(load_state(path)).empires[src.uid]
        assert 10 in e.structures
        s = e.structures[10]
        assert s.iid == "arrow_tower"
        assert s.position == HexCoord(3, -1)
        assert s.damage == 5.0
        assert s.range == 3
        assert s.effects == {"slow": 0.3}

    def test_round_trip_armies(self, tmp_path: Path) -> None:
        path = str(tmp_path / "state.yaml")
        src = _make_empire()
        self._run(save_state({src.uid: src}, path=path))
        e = self._run(load_state(path)).empires[src.uid]
        assert len(e.armies) == 1
        army = e.armies[0]
        assert army.aid == 1
        assert army.direction == Direction.NORTH
        assert army.name == "Alpha"
        assert len(army.waves) == 1
        wave = army.waves[0]
        assert wave.critter_iid == "goblin"
        assert wave.slots == 5
        assert len(wave.critters) == 1
        c = wave.critters[0]
        assert c.cid == 100
        assert c.health == 10.0
        assert len(c.path) == 3
        assert c.path[1] == HexCoord(1, 0)
        assert c.path_progress == pytest.approx(0.5)

    def test_round_trip_spies(self, tmp_path: Path) -> None:
        path = str(tmp_path / "state.yaml")
        src = _make_empire()
        self._run(save_state({src.uid: src}, path=path))
        e = self._run(load_state(path)).empires[src.uid]
        assert len(e.spies) == 1
        assert e.spies[0].aid == 5
        assert e.spies[0].options["spy_defense"] == 500.0

    def test_round_trip_bosses(self, tmp_path: Path) -> None:
        path = str(tmp_path / "state.yaml")
        src = _make_empire()
        self._run(save_state({src.uid: src}, path=path))
        e = self._run(load_state(path)).empires[src.uid]
        assert "dragon" in e.bosses
        boss = e.bosses["dragon"]
        assert boss.is_boss is True
        assert boss.level == 3
        assert boss.xp == 250.0
        assert boss.armour == 5.0

    def test_round_trip_hex_map(self, tmp_path: Path) -> None:
        path = str(tmp_path / "state.yaml")
        src = _make_empire()
        self._run(save_state({src.uid: src}, path=path))
        e = self._run(load_state(path)).empires[src.uid]
        m = e.empire_map
        assert Direction.NORTH in m.paths
        assert len(m.paths[Direction.NORTH]) == 3
        assert m.paths[Direction.NORTH][2] == HexCoord(0, -2)
        assert HexCoord(1, 0) in m.build_tiles
        assert HexCoord(3, -1) in m.occupied

    def test_round_trip_attack(self, tmp_path: Path) -> None:
        path = str(tmp_path / "state.yaml")
        empire = _make_empire()
        attack = _make_attack()
        self._run(save_state({empire.uid: empire}, attacks=[attack], path=path))
        restored = self._run(load_state(path))
        assert len(restored.attacks) == 1
        a = restored.attacks[0]
        assert a.attack_id == 42
        assert a.attacker_uid == 1
        assert a.defender_uid == 2
        assert a.phase == AttackPhase.IN_SIEGE
        assert a.siege_remaining_seconds == pytest.approx(120.5)

    def test_round_trip_battle(self, tmp_path: Path) -> None:
        path = str(tmp_path / "state.yaml")
        empire = _make_empire()
        battle = _make_battle()
        self._run(save_state({empire.uid: empire}, battles=[battle], path=path))
        restored = self._run(load_state(path))
        assert len(restored.battles) == 1
        b = restored.battles[0]
        assert b.bid == 7
        assert b.defender_uid == 2
        assert b.attacker_uids == [1]
        assert 200 in b.critters
        assert b.critters[200].iid == "orc"
        assert 10 in b.structures
        assert len(b.pending_shots) == 1
        assert b.pending_shots[0].damage == 5.0
        assert b.elapsed_ms == 5000.0
        assert b.observer_uids == {1, 2, 3}
        assert b.attacker_gains[1]["gold"] == 10.0
        assert b.defender_losses["life"] == 2.0

    def test_multiple_empires(self, tmp_path: Path) -> None:
        path = str(tmp_path / "state.yaml")
        e1 = _make_empire(uid=1, name="First")
        e2 = _make_empire(uid=2, name="Second")
        e2.resources = {"gold": 999.0, "culture": 0.0, "life": 5.0}
        self._run(save_state({1: e1, 2: e2}, path=path))
        restored = self._run(load_state(path))
        assert len(restored.empires) == 2
        assert restored.empires[1].name == "First"
        assert restored.empires[2].name == "Second"
        assert restored.empires[2].resources["gold"] == 999.0

    def test_empty_empire(self, tmp_path: Path) -> None:
        """Minimal empire with all defaults."""
        path = str(tmp_path / "state.yaml")
        e = Empire(uid=99)
        self._run(save_state({99: e}, path=path))
        restored = self._run(load_state(path))
        assert 99 in restored.empires
        r = restored.empires[99]
        assert r.uid == 99
        assert r.name == ""
        assert r.armies == []
        assert r.structures == {}

    def test_no_empires(self, tmp_path: Path) -> None:
        """Save with zero empires."""
        path = str(tmp_path / "state.yaml")
        self._run(save_state({}, path=path))
        restored = self._run(load_state(path))
        assert restored is not None
        assert len(restored.empires) == 0

    def test_atomic_write(self, tmp_path: Path) -> None:
        """Verify no .tmp file remains after successful save."""
        path = str(tmp_path / "state.yaml")
        e = _make_empire()
        self._run(save_state({e.uid: e}, path=path))
        assert not Path(path + ".tmp").exists()
        assert not (tmp_path / "state.yaml.tmp").exists()
        assert Path(path).exists()

    def test_critter_status_effects(self, tmp_path: Path) -> None:
        """Verify slow/burn effects survive round trip."""
        path = str(tmp_path / "state.yaml")
        e = Empire(uid=50)
        e.bosses["slowed_boss"] = Critter(
            cid=500, iid="troll", health=50.0, max_health=50.0,
            speed=2.0, armour=3.0,
            slow_remaining_ms=1500.0, slow_speed=0.5,
            burn_remaining_ms=3000.0, burn_dps=2.5,
        )
        self._run(save_state({50: e}, path=path))
        r = self._run(load_state(path)).empires[50]
        boss = r.bosses["slowed_boss"]
        assert boss.slow_remaining_ms == 1500.0
        assert boss.slow_speed == 0.5
        assert boss.burn_remaining_ms == 3000.0
        assert boss.burn_dps == 2.5
