"""Tests for siege construction speed penalty in EmpireService."""

from unittest.mock import MagicMock

import pytest

from gameserver.engine.empire_service import EmpireService
from gameserver.loaders.game_config_loader import GameConfig
from gameserver.models.attack import Attack, AttackPhase
from gameserver.models.empire import Empire


DEFENDER_UID = 1
ATTACKER_UID = 2


def _make_attack(phase: AttackPhase, defender_uid: int = DEFENDER_UID) -> Attack:
    a = MagicMock(spec=Attack)
    a.phase = phase
    a.defender_uid = defender_uid
    return a


def _make_service(per_army: float = 0.05) -> EmpireService:
    gc = GameConfig(base_build_speed=1.0, base_siege_construction_speed_per_army_modifier=per_army)
    svc = EmpireService(upgrade_provider=MagicMock(), event_bus=MagicMock(), game_config=gc)
    return svc


def _make_empire(max_penalty: float = 0.12) -> Empire:
    emp = Empire(uid=DEFENDER_UID, name="Defender")
    emp.effects["max_siege_construction_speed_modifier"] = max_penalty
    return emp


class TestSiegeConstructionPenalty:
    def test_no_attack_service_no_penalty(self):
        """Without attack_service the penalty is always 0."""
        svc = _make_service()
        emp = _make_empire()
        emp.buildings["hut"] = 5.0
        emp.build_queue = "hut"

        svc._progress_buildings(emp, dt=1.0)

        assert emp.buildings["hut"] == pytest.approx(4.0)  # full speed

    def test_no_siege_armies_no_penalty(self):
        svc = _make_service()
        emp = _make_empire()
        emp.buildings["hut"] = 5.0
        emp.build_queue = "hut"

        svc._attack_service = MagicMock()
        svc._attack_service.get_incoming.return_value = []

        svc._progress_buildings(emp, dt=1.0)

        assert emp.buildings["hut"] == pytest.approx(4.0)

    def test_one_siege_army_reduces_speed(self):
        """1 army × 0.05 = 5% reduction → speed = 1.0 * 0.95 = 0.95."""
        svc = _make_service(per_army=0.05)
        emp = _make_empire(max_penalty=0.12)
        emp.buildings["hut"] = 5.0
        emp.build_queue = "hut"

        svc._attack_service = MagicMock()
        svc._attack_service.get_incoming.return_value = [
            _make_attack(AttackPhase.IN_SIEGE),
        ]

        svc._progress_buildings(emp, dt=1.0)

        assert emp.buildings["hut"] == pytest.approx(5.0 - 0.95)

    def test_two_siege_armies_reduces_speed(self):
        """2 armies × 0.05 = 10% reduction → speed = 0.90."""
        svc = _make_service(per_army=0.05)
        emp = _make_empire(max_penalty=0.12)
        emp.buildings["hut"] = 5.0
        emp.build_queue = "hut"

        svc._attack_service = MagicMock()
        svc._attack_service.get_incoming.return_value = [
            _make_attack(AttackPhase.IN_SIEGE),
            _make_attack(AttackPhase.IN_SIEGE),
        ]

        svc._progress_buildings(emp, dt=1.0)

        assert emp.buildings["hut"] == pytest.approx(5.0 - 0.90)

    def test_penalty_capped_at_max(self):
        """3 armies × 0.05 = 0.15 > max 0.12 → capped at 0.12 → speed = 0.88."""
        svc = _make_service(per_army=0.05)
        emp = _make_empire(max_penalty=0.12)
        emp.buildings["hut"] = 5.0
        emp.build_queue = "hut"

        svc._attack_service = MagicMock()
        svc._attack_service.get_incoming.return_value = [
            _make_attack(AttackPhase.IN_SIEGE),
            _make_attack(AttackPhase.IN_SIEGE),
            _make_attack(AttackPhase.IN_SIEGE),
        ]

        svc._progress_buildings(emp, dt=1.0)

        assert emp.buildings["hut"] == pytest.approx(5.0 - 0.88)

    def test_travelling_armies_not_counted(self):
        """Armies still travelling do not reduce construction speed."""
        svc = _make_service(per_army=0.05)
        emp = _make_empire(max_penalty=0.12)
        emp.buildings["hut"] = 5.0
        emp.build_queue = "hut"

        svc._attack_service = MagicMock()
        svc._attack_service.get_incoming.return_value = [
            _make_attack(AttackPhase.TRAVELLING),
            _make_attack(AttackPhase.TRAVELLING),
        ]

        svc._progress_buildings(emp, dt=1.0)

        assert emp.buildings["hut"] == pytest.approx(4.0)  # no penalty

    def test_in_battle_armies_not_counted(self):
        """Armies in battle (past siege) do not reduce construction speed."""
        svc = _make_service(per_army=0.05)
        emp = _make_empire(max_penalty=0.12)
        emp.buildings["hut"] = 5.0
        emp.build_queue = "hut"

        svc._attack_service = MagicMock()
        svc._attack_service.get_incoming.return_value = [
            _make_attack(AttackPhase.IN_BATTLE),
        ]

        svc._progress_buildings(emp, dt=1.0)

        assert emp.buildings["hut"] == pytest.approx(4.0)

    def test_no_max_penalty_in_era_no_cap(self):
        """Empire has no max_siege_construction_speed_modifier effect → no cap applied."""
        svc = _make_service(per_army=0.05)
        emp = Empire(uid=DEFENDER_UID, name="Defender")  # no effects
        emp.buildings["hut"] = 5.0
        emp.build_queue = "hut"

        svc._attack_service = MagicMock()
        svc._attack_service.get_incoming.return_value = [
            _make_attack(AttackPhase.IN_SIEGE),
            _make_attack(AttackPhase.IN_SIEGE),
        ]

        svc._progress_buildings(emp, dt=1.0)

        # 2 × 0.05 = 0.10 penalty, no cap → speed = 0.90
        assert emp.buildings["hut"] == pytest.approx(5.0 - 0.90)


class TestSiegeResilienceEffect:
    def test_effect_reduces_per_army_penalty(self):
        """base=0.05, effect=0.03 → effective 0.02 per army → 2 armies = 4% reduction."""
        svc = _make_service(per_army=0.05)
        emp = _make_empire(max_penalty=0.12)
        emp.effects["siege_construction_speed_per_army_modifier"] = 0.03
        emp.buildings["hut"] = 5.0
        emp.build_queue = "hut"

        svc._attack_service = MagicMock()
        svc._attack_service.get_incoming.return_value = [
            _make_attack(AttackPhase.IN_SIEGE),
            _make_attack(AttackPhase.IN_SIEGE),
        ]

        svc._progress_buildings(emp, dt=1.0)

        # effective per_army = 0.05 - 0.03 = 0.02 → 2 × 0.02 = 0.04 → speed = 0.96
        assert emp.buildings["hut"] == pytest.approx(5.0 - 0.96)

    def test_effect_cannot_make_per_army_negative(self):
        """effect larger than base → per_army clamped to 0 → no penalty."""
        svc = _make_service(per_army=0.05)
        emp = _make_empire(max_penalty=0.12)
        emp.effects["siege_construction_speed_per_army_modifier"] = 0.10  # > base
        emp.buildings["hut"] = 5.0
        emp.build_queue = "hut"

        svc._attack_service = MagicMock()
        svc._attack_service.get_incoming.return_value = [
            _make_attack(AttackPhase.IN_SIEGE),
            _make_attack(AttackPhase.IN_SIEGE),
        ]

        svc._progress_buildings(emp, dt=1.0)

        assert emp.buildings["hut"] == pytest.approx(4.0)  # no penalty

    def test_effect_still_respects_max_cap(self):
        """Resilience reduces per-army but cap still applies to final value."""
        svc = _make_service(per_army=0.05)
        emp = _make_empire(max_penalty=0.06)
        emp.effects["siege_construction_speed_per_army_modifier"] = 0.02  # effective = 0.03
        emp.buildings["hut"] = 5.0
        emp.build_queue = "hut"

        svc._attack_service = MagicMock()
        svc._attack_service.get_incoming.return_value = [
            _make_attack(AttackPhase.IN_SIEGE),
            _make_attack(AttackPhase.IN_SIEGE),
            _make_attack(AttackPhase.IN_SIEGE),
        ]

        svc._progress_buildings(emp, dt=1.0)

        # 3 × 0.03 = 0.09 → capped at 0.06 → speed = 0.94
        assert emp.buildings["hut"] == pytest.approx(5.0 - 0.94)
