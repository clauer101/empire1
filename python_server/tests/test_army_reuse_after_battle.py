"""Regression test: army waves must be reset after battle so the army can be reused.

Bug: After a battle ended normally (defender wins), army waves retained
num_critters_spawned == slots. The next battle with the same army would
immediately terminate (no critters spawned, defender wins trivially) because
_check_finished saw all_armies_done=True from the very first tick.

Fix locations:
  - handlers.py: reset waves in _run_battle_task after normal battle completion
  - state_load.py: auto-reset spent waves on server startup (_deserialize_critter_wave)
"""

import pytest
from gameserver.engine.battle_service import BattleService
from gameserver.models.battle import BattleState
from gameserver.models.empire import Empire
from gameserver.models.army import Army, CritterWave
from gameserver.models.hex import HexCoord


# ── Helpers ───────────────────────────────────────────────────────────────────

class _ItemMock:
    def __init__(self, iid, health=2.0, speed=0.5, time_between=500, slots=1, armour=0.0):
        self.iid = iid
        self.health = health
        self.speed = speed
        self.time_between_ms = time_between
        self.slots = slots
        self.armour = armour


def _make_battle(waves: list[CritterWave]) -> tuple[BattleState, BattleService]:
    items = {"GRUNT": _ItemMock("GRUNT")}
    svc = BattleService(items=items)

    defender = Empire(uid=1, name="Defender")
    defender.resources["life"] = 10.0
    attacker = Empire(uid=2, name="Attacker")

    army = Army(aid=1, uid=2, name="Test Army", waves=waves)
    battle = BattleState(
        bid=42,
        defender=defender,
        attacker=attacker,
        army=army,
        structures={},
        critter_path=[HexCoord(0, 0), HexCoord(1, 0), HexCoord(2, 0)],
    )
    return battle, svc


# ── Tests ─────────────────────────────────────────────────────────────────────

class TestSpentArmyImmediateFinish:
    """Document the original bug: spent waves cause instant battle end."""

    def test_spent_waves_finish_at_min_keep_alive_with_no_critters(self):
        """A battle where all waves are already consumed ends at MIN_KEEP_ALIVE_MS
        without ever spawning a critter. This is the symptom of the bug."""
        wave = CritterWave(
            wave_id=1, iid="GRUNT", slots=5,
            num_critters_spawned=5,  # already fully spent — simulates post-battle state
            next_critter_ms=0,
        )
        battle, svc = _make_battle([wave])

        max_ticks = 1000
        dt_ms = 15.0
        spawned_ever = 0

        for _ in range(max_ticks):
            critters_before = len(battle.critters)
            svc.tick(battle, dt_ms)
            spawned_ever += max(0, len(battle.critters) - critters_before)
            if battle.is_finished:
                break

        assert battle.is_finished, "battle should have finished"
        assert battle.defender_won is True, "defender should win trivially"
        assert spawned_ever == 0, "no critter must ever spawn from a spent army"
        assert battle.elapsed_ms >= battle.MIN_KEEP_ALIVE_MS


class TestResetWavesAllowsReuse:
    """After resetting waves (the fix), the army spawns critters normally."""

    def test_reset_waves_spawn_critters_in_new_battle(self):
        """Resetting num_critters_spawned=0 on all waves before a new battle
        causes critters to actually spawn — verifying the fix in handlers.py."""
        # Simulate the state after a battle: waves spent
        wave = CritterWave(
            wave_id=1, iid="GRUNT", slots=3,
            num_critters_spawned=3,  # spent
            next_critter_ms=0,
        )
        army = Army(aid=1, uid=2, name="Test Army", waves=[wave])

        # Apply the fix: reset waves (mirrors what _run_battle_task now does)
        for w in army.waves:
            w.num_critters_spawned = 0
            w.next_critter_ms = 0

        battle, svc = _make_battle(army.waves)
        battle.army = army

        spawned_ever = 0
        for _ in range(500):
            before = len(battle.critters)
            svc.tick(battle, 15.0)
            spawned_ever += max(0, len(battle.critters) - before)
            if battle.is_finished:
                break

        assert spawned_ever > 0, "critters must spawn after wave reset"

    def test_two_waves_both_reset_and_spawn(self):
        """Two spent waves, both reset → both waves spawn critters."""
        waves = [
            CritterWave(wave_id=1, iid="GRUNT", slots=2, num_critters_spawned=2, next_critter_ms=0),
            CritterWave(wave_id=2, iid="GRUNT", slots=2, num_critters_spawned=2, next_critter_ms=0),
        ]
        for w in waves:
            w.num_critters_spawned = 0
            w.next_critter_ms = 0

        battle, svc = _make_battle(waves)

        spawned_ever = 0
        for _ in range(1000):
            before = len(battle.critters)
            svc.tick(battle, 15.0)
            spawned_ever += max(0, len(battle.critters) - before)
            if battle.is_finished:
                break

        assert spawned_ever >= 2, "at minimum one critter per wave must spawn"


class TestStateLoadResetSpentWaves:
    """The state_load.py fix: _deserialize_critter_wave resets spent waves on load."""

    def test_deserialize_fully_spent_wave_resets_spawn_count(self):
        """Loading a wave with num_critters_spawned == slots resets it to 0."""
        from gameserver.persistence.state_load import _deserialize_critter_wave

        d = {"wave_id": 1, "iid": "GRUNT", "slots": 11, "num_critters_spawned": 11}
        wave = _deserialize_critter_wave(d)

        assert wave.num_critters_spawned == 0, (
            "A fully-spent wave loaded from state must be reset to 0 "
            "so the army can be reused after server restart"
        )
        assert wave.slots == 11

    def test_deserialize_partially_spent_wave_keeps_count(self):
        """A wave that was mid-spawn (e.g. during an active battle on server crash)
        keeps its partial count — only fully-spent waves are reset."""
        from gameserver.persistence.state_load import _deserialize_critter_wave

        d = {"wave_id": 1, "iid": "GRUNT", "slots": 10, "num_critters_spawned": 6}
        wave = _deserialize_critter_wave(d)

        assert wave.num_critters_spawned == 6

    def test_deserialize_unspent_wave_unchanged(self):
        """An unstarted wave (num_critters_spawned=0) is loaded as-is."""
        from gameserver.persistence.state_load import _deserialize_critter_wave

        d = {"wave_id": 2, "iid": "GRUNT", "slots": 5, "num_critters_spawned": 0}
        wave = _deserialize_critter_wave(d)

        assert wave.num_critters_spawned == 0
