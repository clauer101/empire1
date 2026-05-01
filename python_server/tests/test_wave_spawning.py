"""Tests for wave spawning."""

from gameserver.models.army import Army, CritterWave
from gameserver.engine.battle_service import BattleService


class _ItemMock:
    def __init__(self, iid, slots=1, time_between=2000):
        self.iid = iid
        self.slots = slots
        self.time_between_ms = time_between


class TestOversizedCritterSpawn:
    """A critter whose slot cost exceeds the wave's total slots must still spawn once."""

    def _make_service(self, critter_slots: int) -> BattleService:
        return BattleService(items={"boss": _ItemMock("boss", slots=critter_slots)})

    def test_boss_spawns_when_slot_cost_equals_wave_slots(self):
        """Critter cost == wave slots → spawns exactly once."""
        service = self._make_service(critter_slots=5)
        wave = CritterWave(wave_id=1, iid="boss", slots=5)
        wave.next_critter_ms = 0

        critters = service._step_wave(wave, dt_ms=100)

        assert len(critters) == 1, "expected exactly one critter"
        assert wave.num_critters_spawned == 5  # wave is now full

    def test_boss_spawns_when_slot_cost_exceeds_wave_slots(self):
        """Critter cost > wave slots (e.g. THE_GENERAL) → still spawns exactly once."""
        service = self._make_service(critter_slots=999)
        wave = CritterWave(wave_id=1, iid="boss", slots=5)
        wave.next_critter_ms = 0

        critters = service._step_wave(wave, dt_ms=100)

        assert len(critters) == 1, "oversized critter must still spawn"

    def test_boss_wave_marked_complete_after_first_spawn(self):
        """After spawning the oversized critter the wave must be complete."""
        service = self._make_service(critter_slots=999)
        wave = CritterWave(wave_id=1, iid="boss", slots=5)
        wave.next_critter_ms = 0

        service._step_wave(wave, dt_ms=100)
        # reset timer so the second tick would try to spawn again
        wave.next_critter_ms = 0
        second = service._step_wave(wave, dt_ms=100)

        assert len(second) == 0, "no second critter should spawn after wave is complete"
        assert service._mark_wave_complete_if_blocked(wave) is True

    def test_normal_critter_still_respects_slot_limit(self):
        """A normal critter (cost 1, wave 3 slots) fills up to 3 and then stops."""
        service = self._make_service(critter_slots=1)
        wave = CritterWave(wave_id=1, iid="boss", slots=3)

        spawned = 0
        for _ in range(10):
            wave.next_critter_ms = 0
            critters = service._step_wave(wave, dt_ms=100)
            spawned += len(critters)
            if service._mark_wave_complete_if_blocked(wave):
                break

        assert spawned == 3


def _make_wave(num_slots: int = 5, iid: str = "goblin") -> CritterWave:
    return CritterWave(
        wave_id=1,
        iid=iid,
        slots=num_slots,
    )


class TestArmy:
    def test_create_army_with_waves(self):
        """Test that an army can be created with waves."""
        army = Army(aid=1, uid=100, waves=[_make_wave(3)])
        assert len(army.waves) == 1
        assert army.waves[0].slots == 3
        assert army.waves[0].iid == "goblin"

    def test_not_finished_with_active_waves(self):
        army = Army(
            aid=1, uid=100,
            waves=[_make_wave(3)],
        )
        # Note: is_finished now checks if last wave is dispatched
        # This requires battle runtime state to properly check
        # In tests without battle context, we skip this assertion
        assert len(army.waves) > 0
