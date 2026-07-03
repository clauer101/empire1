"""Tests for the unified culture steal mechanic.

Formula:
  base   = uniform(min_c, max_c) * culture_pool * life_ratio
  win    ×2 if attacker won
  era    ×0.5 per attacker if attacker era > defender era
  cap    at culture_pool
"""

from types import SimpleNamespace
from unittest.mock import patch
import pytest


PCT = 0.03  # fixed pct for deterministic tests


def _empire(uid: int, era: str = "stone", culture: float = 10_000.0, max_life: float = 10.0):
    return SimpleNamespace(
        uid=uid,
        resources={"culture": culture},
        max_life=max_life,
        artifacts=[],
        artifact_acquired_at={},
        effects={},
        get_effect=lambda k, d=0.0: d,
        knowledge={},
        buildings={},
        item_upgrades={},
    )


def _svc(empires: dict, era_by_uid: dict, min_c: float = PCT, max_c: float = PCT):
    cfg = SimpleNamespace(
        min_lose_culture=min_c,
        max_lose_culture=max_c,
        ai_culture_steal_modifier=1.0,
    )
    empire_service = SimpleNamespace(
        get=lambda uid: empires.get(uid),
        get_current_era=lambda emp: era_by_uid.get(emp.uid, "stone"),
    )
    return SimpleNamespace(game_config=cfg, empire_service=empire_service, upgrade_provider=SimpleNamespace(items={}))


def _battle(defender, attacker_uids, life_lost: float = 3.0, defender_won: bool = False):
    return SimpleNamespace(
        defender=defender,
        attacker_uids=attacker_uids,
        defender_won=defender_won,
        attacker_gains={},
        defender_losses={"life": life_lost},
        critters_reached=int(life_lost > 0),
    )


def _run_loot(battle, svc):
    from gameserver.network.handlers.battle_task import _compute_and_apply_loot
    with patch("random.uniform", return_value=PCT), \
         patch("random.choice", return_value=None), \
         patch("random.random", return_value=1.0):
        return _compute_and_apply_loot(battle, svc)


def test_attacker_loses_same_era():
    # base = 10000 × 0.03 × (3/10) × 1.0 = 90
    defender = _empire(99, culture=10_000.0, max_life=10.0)
    attacker = _empire(1, culture=0.0)
    svc = _svc({99: defender, 1: attacker}, {99: "stone", 1: "stone"})
    battle = _battle(defender, [1], life_lost=3.0, defender_won=True)
    loot = _run_loot(battle, svc)
    assert loot.get("culture", 0.0) == pytest.approx(90.0, abs=1.0)
    assert attacker.resources["culture"] == pytest.approx(90.0, abs=1.0)


def test_attacker_wins_same_era_doubles_loot():
    # base = 10000 × 0.03 × (3/10) × 2.0 = 180
    defender = _empire(99, culture=10_000.0, max_life=10.0)
    attacker = _empire(1, culture=0.0)
    svc = _svc({99: defender, 1: attacker}, {99: "stone", 1: "stone"})
    battle = _battle(defender, [1], life_lost=3.0, defender_won=False)
    loot = _run_loot(battle, svc)
    assert loot.get("culture", 0.0) == pytest.approx(180.0, abs=1.0)


def test_attacker_wins_higher_era_halved():
    # 10000 × 0.03 × 0.3 × 2.0 = 180 → ×0.5 = 90
    defender = _empire(99, era="stone", culture=10_000.0, max_life=10.0)
    attacker = _empire(1, era="iron", culture=0.0)
    svc = _svc({99: defender, 1: attacker}, {99: "stone", 1: "iron"})
    battle = _battle(defender, [1], life_lost=3.0, defender_won=False)
    loot = _run_loot(battle, svc)
    assert loot.get("culture", 0.0) == pytest.approx(90.0, abs=1.0)
    assert loot["per_attacker"][1].get("culture_era_penalty") is True


def test_no_life_lost_no_steal():
    defender = _empire(99, culture=10_000.0, max_life=10.0)
    attacker = _empire(1, culture=0.0)
    svc = _svc({99: defender, 1: attacker}, {99: "stone", 1: "stone"})
    battle = _battle(defender, [1], life_lost=0.0, defender_won=False)
    loot = _run_loot(battle, svc)
    assert loot.get("culture", 0.0) == 0.0


def test_full_life_loss_with_win():
    # 10000 × 0.03 × 1.0 × 2.0 = 600
    defender = _empire(99, culture=10_000.0, max_life=10.0)
    attacker = _empire(1, culture=0.0)
    svc = _svc({99: defender, 1: attacker}, {99: "stone", 1: "stone"})
    battle = _battle(defender, [1], life_lost=10.0, defender_won=False)
    loot = _run_loot(battle, svc)
    assert loot.get("culture", 0.0) == pytest.approx(600.0, abs=1.0)


def test_capped_at_culture_pool():
    # pct mocked to 5.0 (500%) → base = 100 * 5.0 * 1.0 * 2.0 = 1000, cap at 100
    defender = _empire(99, culture=100.0, max_life=10.0)
    attacker = _empire(1, culture=0.0)
    svc = _svc({99: defender, 1: attacker}, {99: "stone", 1: "stone"})
    battle = _battle(defender, [1], life_lost=10.0, defender_won=False)
    from gameserver.network.handlers.battle_task import _compute_and_apply_loot
    with patch("random.uniform", return_value=5.0), \
         patch("random.choice", return_value=None), \
         patch("random.random", return_value=1.0):
        loot = _compute_and_apply_loot(battle, svc)
    assert loot.get("culture", 0.0) == pytest.approx(100.0, abs=0.1)
    assert defender.resources["culture"] == pytest.approx(0.0, abs=0.1)
