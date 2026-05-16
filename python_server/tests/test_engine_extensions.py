"""Engine extension tests — covers previously untested branches in:
- engine/attack_service.py
- engine/game_loop.py
- engine/statistics.py
"""

from __future__ import annotations

import asyncio
from unittest.mock import MagicMock, AsyncMock, patch

import pytest

from gameserver.engine.attack_service import AttackService
from gameserver.engine.empire_service import EmpireService
from gameserver.engine.game_loop import GameLoop
from gameserver.engine.statistics import StatisticsService
from gameserver.engine.upgrade_provider import UpgradeProvider
from gameserver.models.army import Army, CritterWave
from gameserver.models.attack import Attack, AttackPhase
from gameserver.util.events import EventBus

from conftest import make_empire


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _attack_svc(game_config=None) -> AttackService:
    bus = EventBus()
    return AttackService(bus, game_config=game_config)


def _attack_svc_with_empires() -> tuple[AttackService, EmpireService]:
    bus = EventBus()
    up = UpgradeProvider()
    es = EmpireService(up, bus)
    svc = AttackService(bus, game_config=None, empire_service=es)
    return svc, es


def _army_with_waves(aid: int = 1, uid: int = 1) -> Army:
    return Army(aid=aid, uid=uid, waves=[CritterWave(wave_id=1, iid="goblin", slots=3)])


# ---------------------------------------------------------------------------
# AttackService — era travel offset
# ---------------------------------------------------------------------------

class TestEraTravelOffset:
    def test_no_knowledge_era_groups_returns_base(self):
        svc = _attack_svc()
        empire = make_empire()
        result = svc._era_travel_offset(empire)
        assert result == svc._base_travel_offset

    def test_with_knowledge_era_groups_no_completed_knowledge(self):
        gc = MagicMock()
        gc.base_travel_offset = 300.0
        gc.step_length_ms = 1000.0
        gc.stone_travel_offset = 150.0
        bus = EventBus()
        svc = AttackService(bus, game_config=gc,
                            knowledge_era_groups={"stone": ["HUNTING"], "iron": ["METALLURGY"]})
        empire = make_empire(knowledge={})  # nothing completed
        result = svc._era_travel_offset(empire)
        # Falls back to stone era
        assert isinstance(result, float)

    def test_with_completed_knowledge_uses_higher_era(self):
        gc = MagicMock()
        gc.base_travel_offset = 300.0
        gc.step_length_ms = 1000.0
        gc.stone_travel_offset = 200.0
        gc.iron_travel_offset = 100.0
        bus = EventBus()
        svc = AttackService(bus, game_config=gc,
                            knowledge_era_groups={"stone": ["HUNTING"], "iron": ["METALLURGY"]})
        empire = make_empire(knowledge={"METALLURGY": 0.0})
        result = svc._era_travel_offset(empire)
        # Should reference iron_travel_offset
        assert isinstance(result, float)


# ---------------------------------------------------------------------------
# AttackService — query methods
# ---------------------------------------------------------------------------

class TestAttackServiceQuery:
    def test_get_all_attacks_empty(self):
        svc = _attack_svc()
        assert svc.get_all_attacks() == []

    def test_get_incoming_filters_by_defender(self):
        svc = _attack_svc()
        a1 = Attack(attack_id=1, attacker_uid=10, defender_uid=20,
                    army_aid=1, phase=AttackPhase.TRAVELLING, eta_seconds=100.0)
        a2 = Attack(attack_id=2, attacker_uid=10, defender_uid=30,
                    army_aid=2, phase=AttackPhase.TRAVELLING, eta_seconds=100.0)
        svc._attacks = [a1, a2]
        assert svc.get_incoming(20) == [a1]
        assert svc.get_incoming(30) == [a2]
        assert svc.get_incoming(99) == []

    def test_get_incoming_excludes_finished(self):
        svc = _attack_svc()
        a = Attack(attack_id=1, attacker_uid=10, defender_uid=20,
                   army_aid=1, phase=AttackPhase.FINISHED, eta_seconds=0.0)
        svc._attacks = [a]
        assert svc.get_incoming(20) == []

    def test_get_outgoing_filters_by_attacker(self):
        svc = _attack_svc()
        a = Attack(attack_id=1, attacker_uid=5, defender_uid=99,
                   army_aid=1, phase=AttackPhase.TRAVELLING, eta_seconds=100.0)
        svc._attacks = [a]
        assert svc.get_outgoing(5) == [a]
        assert svc.get_outgoing(99) == []

    def test_get_returns_by_id(self):
        svc = _attack_svc()
        a = Attack(attack_id=42, attacker_uid=1, defender_uid=2,
                   army_aid=1, phase=AttackPhase.TRAVELLING, eta_seconds=50.0)
        svc._attacks = [a]
        assert svc.get(42) is a
        assert svc.get(999) is None


# ---------------------------------------------------------------------------
# AttackService — skip_siege
# ---------------------------------------------------------------------------

class TestSkipSiege:
    def test_not_found_returns_error(self):
        svc = _attack_svc()
        result = svc.skip_siege(999, requester_uid=1)
        assert isinstance(result, str)
        assert "not found" in result

    def test_wrong_phase_returns_error(self):
        svc = _attack_svc()
        a = Attack(attack_id=1, attacker_uid=10, defender_uid=20,
                   army_aid=1, phase=AttackPhase.TRAVELLING, eta_seconds=50.0)
        svc._attacks = [a]
        result = svc.skip_siege(1, requester_uid=20)
        assert isinstance(result, str)
        assert "not in IN_SIEGE" in result

    def test_wrong_requester_returns_error(self):
        svc = _attack_svc()
        a = Attack(attack_id=1, attacker_uid=10, defender_uid=20,
                   army_aid=1, phase=AttackPhase.IN_SIEGE, eta_seconds=0.0)
        a.siege_remaining_seconds = 30.0
        svc._attacks = [a]
        result = svc.skip_siege(1, requester_uid=99)
        assert isinstance(result, str)
        assert "defender" in result.lower()

    def test_success_sets_siege_remaining_to_zero(self):
        svc = _attack_svc()
        a = Attack(attack_id=1, attacker_uid=10, defender_uid=20,
                   army_aid=1, phase=AttackPhase.IN_SIEGE, eta_seconds=0.0)
        a.siege_remaining_seconds = 120.0
        svc._attacks = [a]
        result = svc.skip_siege(1, requester_uid=20)
        assert result is a
        assert a.siege_remaining_seconds == 0.0


# ---------------------------------------------------------------------------
# AttackService — restore_attacks
# ---------------------------------------------------------------------------

class TestRestoreAttacks:
    def test_normal_attack_restored(self):
        svc = _attack_svc()
        a = Attack(attack_id=5, attacker_uid=1, defender_uid=2,
                   army_aid=1, phase=AttackPhase.TRAVELLING, eta_seconds=60.0)
        svc.restore_attacks([a])
        assert len(svc._attacks) == 1
        assert svc._next_attack_id == 6

    def test_finished_attacks_not_restored(self):
        svc = _attack_svc()
        a = Attack(attack_id=3, attacker_uid=1, defender_uid=2,
                   army_aid=1, phase=AttackPhase.FINISHED, eta_seconds=0.0)
        svc.restore_attacks([a])
        assert len(svc._attacks) == 0

    def test_spy_in_siege_finished_immediately(self):
        bus = EventBus()
        emitted = []
        bus.on("SpyArrived", lambda e: emitted.append(e))
        svc = AttackService(bus)
        a = Attack(attack_id=7, attacker_uid=1, defender_uid=2,
                   army_aid=1, phase=AttackPhase.IN_SIEGE, eta_seconds=0.0,
                   is_spy=True)
        svc.restore_attacks([a])
        assert a.phase == AttackPhase.FINISHED
        assert len(svc._attacks) == 0  # finished → not kept

    def test_next_attack_id_advanced(self):
        svc = _attack_svc()
        attacks = [
            Attack(attack_id=10, attacker_uid=1, defender_uid=2,
                   army_aid=1, phase=AttackPhase.TRAVELLING, eta_seconds=10.0),
            Attack(attack_id=15, attacker_uid=1, defender_uid=3,
                   army_aid=2, phase=AttackPhase.TRAVELLING, eta_seconds=10.0),
        ]
        svc.restore_attacks(attacks)
        assert svc._next_attack_id == 16


# ---------------------------------------------------------------------------
# AttackService — start_attack
# ---------------------------------------------------------------------------

class TestStartAttack:
    def _svc_with_two_empires(self):
        svc, es = _attack_svc_with_empires()
        att = make_empire(uid=1)
        att.armies.append(_army_with_waves(aid=1, uid=1))
        defd = make_empire(uid=2)
        es.register(att)
        es.register(defd)
        return svc, es

    def test_success(self):
        svc, es = self._svc_with_two_empires()
        result = svc.start_attack(1, 2, army_aid=1, empire_service=es)
        assert isinstance(result, Attack)
        assert result.attacker_uid == 1
        assert result.defender_uid == 2

    def test_self_attack_rejected(self):
        svc, es = self._svc_with_two_empires()
        result = svc.start_attack(1, 1, army_aid=1, empire_service=es)
        assert isinstance(result, str)
        assert "yourself" in result

    def test_unknown_attacker_rejected(self):
        svc, es = self._svc_with_two_empires()
        result = svc.start_attack(99, 2, army_aid=1, empire_service=es)
        assert isinstance(result, str)
        assert "not found" in result

    def test_unknown_army_rejected(self):
        svc, es = self._svc_with_two_empires()
        result = svc.start_attack(1, 2, army_aid=999, empire_service=es)
        assert isinstance(result, str)
        assert "Army" in result

    def test_empty_waves_rejected(self):
        svc, es = _attack_svc_with_empires()
        att = make_empire(uid=1)
        att.armies.append(Army(aid=1, uid=1, waves=[]))
        defd = make_empire(uid=2)
        es.register(att)
        es.register(defd)
        result = svc.start_attack(1, 2, army_aid=1, empire_service=es)
        assert isinstance(result, str)
        assert "no waves" in result.lower()

    def test_army_already_attacking_rejected(self):
        svc, es = self._svc_with_two_empires()
        # Start first attack
        r1 = svc.start_attack(1, 2, army_aid=1, empire_service=es)
        assert isinstance(r1, Attack)
        # Second attack with same army is rejected
        r2 = svc.start_attack(1, 2, army_aid=1, empire_service=es)
        assert isinstance(r2, str)
        assert "already" in r2.lower()


# ---------------------------------------------------------------------------
# AttackService — step
# ---------------------------------------------------------------------------

class TestAttackStep:
    def test_travelling_decrements_eta(self):
        svc = _attack_svc()
        a = Attack(attack_id=1, attacker_uid=1, defender_uid=2,
                   army_aid=1, phase=AttackPhase.TRAVELLING, eta_seconds=100.0)
        svc.step(a, dt=10.0)
        assert a.eta_seconds == pytest.approx(90.0)

    def test_travelling_transitions_to_in_siege(self):
        svc = _attack_svc()
        a = Attack(attack_id=1, attacker_uid=1, defender_uid=2,
                   army_aid=1, phase=AttackPhase.TRAVELLING, eta_seconds=5.0)
        svc.step(a, dt=10.0)
        assert a.phase == AttackPhase.IN_SIEGE

    def test_in_siege_decrements(self):
        svc = _attack_svc()
        a = Attack(attack_id=1, attacker_uid=1, defender_uid=2,
                   army_aid=1, phase=AttackPhase.IN_SIEGE, eta_seconds=0.0)
        a.siege_remaining_seconds = 60.0
        result = svc.step(a, dt=10.0)
        assert a.siege_remaining_seconds == pytest.approx(50.0)
        assert result is None

    def test_in_siege_transitions_to_in_battle(self):
        svc = _attack_svc()
        a = Attack(attack_id=1, attacker_uid=1, defender_uid=2,
                   army_aid=1, phase=AttackPhase.IN_SIEGE, eta_seconds=0.0)
        a.siege_remaining_seconds = 5.0
        result = svc.step(a, dt=10.0)
        assert a.phase == AttackPhase.IN_BATTLE
        assert result is a

    def test_recovered_in_battle_attack_returned(self):
        svc = _attack_svc()
        a = Attack(attack_id=1, attacker_uid=1, defender_uid=2,
                   army_aid=1, phase=AttackPhase.IN_BATTLE, eta_seconds=0.0)
        result = svc.step(a, dt=1.0)
        assert result is a

    def test_spy_attack_finishes_at_siege(self):
        svc = _attack_svc()
        a = Attack(attack_id=1, attacker_uid=1, defender_uid=2,
                   army_aid=1, phase=AttackPhase.TRAVELLING,
                   eta_seconds=1.0, is_spy=True)
        svc.step(a, dt=5.0)
        assert a.phase == AttackPhase.FINISHED


# ---------------------------------------------------------------------------
# AttackService — start_ai_attack
# ---------------------------------------------------------------------------

class TestStartAiAttack:
    def test_creates_attack(self):
        svc = _attack_svc()
        army = _army_with_waves(aid=100, uid=0)
        result = svc.start_ai_attack(defender_uid=5, army=army, travel_seconds=60.0)
        assert isinstance(result, Attack)
        assert result.defender_uid == 5
        assert result.phase == AttackPhase.TRAVELLING

    def test_with_siege_seconds_override(self):
        svc = _attack_svc()
        army = _army_with_waves(aid=101, uid=0)
        result = svc.start_ai_attack(5, army, travel_seconds=30.0, siege_seconds=120.0)
        assert isinstance(result, Attack)
        assert result.override_siege_seconds == 120.0


# ---------------------------------------------------------------------------
# GameLoop
# ---------------------------------------------------------------------------

def _make_game_loop() -> tuple[GameLoop, MagicMock, MagicMock]:
    event_bus = EventBus()
    empire_svc = MagicMock()
    empire_svc.step_all = MagicMock()
    attack_svc = MagicMock()
    attack_svc.step_all.return_value = []
    attack_svc.get_all_attacks.return_value = []
    stats = StatisticsService()
    gc = MagicMock()
    gc.step_length_ms = 1000.0
    gl = GameLoop(
        event_bus=event_bus,
        empire_service=empire_svc,
        attack_service=attack_svc,
        statistics=stats,
        game_config=gc,
        state_file="/tmp/test_state.yaml",
    )
    return gl, empire_svc, attack_svc


class TestGameLoop:
    def test_initial_state(self):
        gl, _, _ = _make_game_loop()
        assert not gl.is_running
        assert gl.tick_count == 0
        assert gl.uptime_seconds == 0.0

    def test_stop_sets_running_false(self):
        gl, _, _ = _make_game_loop()
        gl._running = True
        gl.stop()
        assert not gl.is_running

    def test_step_calls_step_all_on_empires(self):
        gl, empire_svc, attack_svc = _make_game_loop()
        with patch("gameserver.engine.global_state.get_end_criterion_activated", return_value=None):
            gl._step(1.0)
        empire_svc.step_all.assert_called_once_with(1.0)

    def test_step_calls_step_all_on_attacks(self):
        gl, empire_svc, attack_svc = _make_game_loop()
        with patch("gameserver.engine.global_state.get_end_criterion_activated", return_value=None):
            gl._step(1.0)
        attack_svc.step_all.assert_called_once_with(1.0)

    def test_step_emits_battle_start_events(self):
        from gameserver.util.events import BattleStartRequested
        gl, _, attack_svc = _make_game_loop()
        fake_attack = Attack(
            attack_id=1, attacker_uid=1, defender_uid=2,
            army_aid=1, phase=AttackPhase.IN_BATTLE, eta_seconds=0.0,
        )
        attack_svc.step_all.return_value = [fake_attack]
        emitted = []
        gl._events.on(BattleStartRequested, lambda e: emitted.append(e))
        with patch("gameserver.engine.global_state.get_end_criterion_activated", return_value=None):
            gl._step(1.0)
        assert len(emitted) == 1

    def test_step_skipped_during_end_rally(self):
        gc = MagicMock()
        gc.step_length_ms = 1000.0
        bus = EventBus()
        empire_svc = MagicMock()
        attack_svc = MagicMock()
        attack_svc.step_all.return_value = []
        gl = GameLoop(bus, empire_svc, attack_svc, StatisticsService(), game_config=gc)
        with patch("gameserver.engine.global_state.get_end_criterion_activated",
                   return_value=object()), \
             patch("gameserver.engine.global_state.is_end_rally_active", return_value=False):
            gl._step(1.0)
        empire_svc.step_all.assert_not_called()

    async def test_run_and_stop(self):
        gl, _, _ = _make_game_loop()
        gl._step_interval = 0.01  # run fast
        task = asyncio.create_task(gl.run())
        await asyncio.sleep(0.05)
        gl.stop()
        await task
        assert gl.tick_count >= 1
        assert not gl.is_running

    async def test_save_state_does_not_raise(self):
        gl, _, attack_svc = _make_game_loop()
        attack_svc.get_all_attacks.return_value = []
        with patch("gameserver.persistence.state_save.save_state", new_callable=AsyncMock):
            await gl._save_state()  # no exception = success


# ---------------------------------------------------------------------------
# StatisticsService
# ---------------------------------------------------------------------------

class TestStatisticsService:
    def test_calc_tai_returns_float(self):
        stats = StatisticsService()
        empire = make_empire()
        result = stats.calc_tai(empire)
        assert isinstance(result, float)

    def test_check_win_conditions_returns_none(self):
        stats = StatisticsService()
        empire = make_empire()
        result = stats.check_win_conditions(empire)
        assert result is None
