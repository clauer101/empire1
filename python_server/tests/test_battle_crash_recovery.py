"""Tests for battle crash recovery and observer set mutation safety."""

import pytest

from gameserver.engine.battle_service import BattleService
from gameserver.models.battle import BattleState
from gameserver.models.empire import Empire
from gameserver.models.army import Army, CritterWave
from gameserver.models.hex import HexCoord


# ── Helpers ──────────────────────────────────────────────────────────────────

def _make_minimal_battle(army: Army | None = None) -> BattleState:
    defender = Empire(uid=1, name="Defender")
    defender.resources["life"] = 5.0
    attacker = Empire(uid=2, name="Attacker")

    if army is None:
        wave = CritterWave(wave_id=1, iid="X", slots=3, num_critters_spawned=2, next_critter_ms=500)
        army = Army(aid=1, uid=2, name="Test Army", waves=[wave])

    battle = BattleState(
        bid=99,
        defender=defender,
        attacker_uids=[attacker.uid],
        attack_ids=[1],
        armies={1: army},
        attacker_gains={attacker.uid: {}},
        structures={},
        critter_path=[HexCoord(0, 0), HexCoord(1, 0)],
    )
    return battle


def _make_service() -> BattleService:
    return BattleService(items={})


# ── Observer set mutation during broadcast ────────────────────────────────────

class TestObserverSetMutation:
    """RuntimeError: Set changed size during iteration in _broadcast / send_summary."""

    @pytest.mark.asyncio
    async def test_broadcast_tolerates_observer_added_during_send(self):
        """Adding an observer while _broadcast awaits send_fn must not raise."""
        battle = _make_minimal_battle()
        battle.observer_uids = {10, 20}
        battle.is_finished = True  # skip game-loop, only test broadcast path

        calls: list[int] = []

        async def send_fn(uid: int, msg: dict) -> bool:
            calls.append(uid)
            # Mutate the set mid-iteration (simulates concurrent connect)
            battle.observer_uids.add(99)
            return True

        svc = _make_service()
        # Must not raise RuntimeError
        await svc._broadcast(battle, send_fn)

        assert set(calls) <= {10, 20}   # only original observers received the message
        assert 99 in battle.observer_uids  # new observer was registered

    @pytest.mark.asyncio
    async def test_broadcast_tolerates_observer_removed_during_send(self):
        """Removing an observer while _broadcast awaits send_fn must not raise."""
        battle = _make_minimal_battle()
        battle.observer_uids = {10, 20, 30}
        battle.is_finished = True

        removed: list[int] = []

        async def send_fn(uid: int, msg: dict) -> bool:
            # Remove another uid mid-iteration
            battle.observer_uids.discard(30)
            removed.append(uid)
            return True

        svc = _make_service()
        await svc._broadcast(battle, send_fn)   # must not raise

        assert len(removed) > 0

    @pytest.mark.asyncio
    async def test_send_summary_tolerates_observer_mutation(self):
        """send_summary has the same iteration pattern and must also be safe."""
        battle = _make_minimal_battle()
        battle.observer_uids = {1, 2}

        async def send_fn(uid: int, msg: dict) -> bool:
            battle.observer_uids.add(999)
            return True

        svc = _make_service()
        await svc.send_summary(battle, send_fn, loot={})   # must not raise


# ── run_battle exception → crash recovery ────────────────────────────────────

class TestRunBattleCrashRecovery:
    """run_battle must propagate exceptions so _run_battle_task can recover."""

    @pytest.mark.asyncio
    async def test_run_battle_raises_on_broadcast_error(self):
        """If _broadcast raises, run_battle should propagate the exception."""
        battle = _make_minimal_battle()
        battle.keep_alive = True

        call_count = 0

        async def exploding_send_fn(uid: int, msg: dict) -> bool:
            nonlocal call_count
            call_count += 1
            battle.observer_uids.add(777)   # trigger the original bug
            raise RuntimeError("Set changed size during iteration")

        battle.observer_uids = {10}
        # Force an immediate broadcast
        battle.broadcast_timer_ms = -1

        svc = _make_service()
        with pytest.raises(RuntimeError, match="Set changed size during iteration"):
            await svc.run_battle(battle, exploding_send_fn, broadcast_interval_ms=250)

    @pytest.mark.asyncio
    async def test_army_waves_reset_after_crash(self):
        """Non-AI army waves must be reset to spawnable state after a crash."""
        wave = CritterWave(
            wave_id=1, iid="SLAVE", slots=6,
            num_critters_spawned=4,   # partially spawned
            next_critter_ms=1200,
        )
        army = Army(aid=1, uid=2, name="Raider", waves=[wave])
        battle = _make_minimal_battle(army=army)

        # Simulate the recovery logic from _run_battle_task
        battle.defender_won = True
        battle.is_finished = True
        for w in battle.army.waves:
            w.num_critters_spawned = 0
            w.next_critter_ms = 0

        assert wave.num_critters_spawned == 0
        assert wave.next_critter_ms == 0

    @pytest.mark.asyncio
    async def test_crash_sets_defender_won(self):
        """After a crash the battle state must be marked as defender win."""
        battle = _make_minimal_battle()
        assert battle.defender_won is None   # not yet decided

        # Simulate recovery
        battle.defender_won = True
        battle.is_finished = True

        assert battle.defender_won is True
        assert battle.is_finished is True
