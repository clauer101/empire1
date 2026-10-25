"""Tests for the gold_steal_ratio empire effect (docs/EFFECTSGUIDE.md).

On a won attack each human winner steals `defender_gold × ratio / n_winners`
gold on top of the culture loot. A lost attack never steals gold.
"""

from types import SimpleNamespace

from gameserver.engine.ai_service import AI_UID
from gameserver.network.handlers.battle_task import _compute_and_apply_loot


def _empire(uid: int, gold: float = 0.0, effects: dict | None = None):
    return SimpleNamespace(
        uid=uid,
        resources={"culture": 0.0, "gold": gold, "life": 6.0},
        max_life=10.0,
        knowledge={},
        buildings={},
        artifacts=set(),
        effects=effects or {},
        research_queue=None,
        build_queue=None,
    )


def _svc(empires: dict):
    cfg = SimpleNamespace(
        min_lose_culture=0.02,
        max_lose_culture=0.04,
        ai_culture_steal_modifier=0.33,
        restore_life_after_loss_offset=1.0,
    )
    empire_service = SimpleNamespace(
        get=lambda uid: empires.get(uid),
        get_current_era=lambda emp: "stone",
    )
    return SimpleNamespace(
        game_config=cfg,
        empire_service=empire_service,
        upgrade_provider=SimpleNamespace(items={}, check_requirements=lambda *_: True),
    )


def _battle(defender, attacker_uids, defender_won: bool = False):
    return SimpleNamespace(
        defender=defender,
        attacker_uids=attacker_uids,
        attacker_gains={},
        defender_losses={"life": 10.0},
        defender_won=defender_won,
        critters_reached=1,
    )


def test_won_attack_steals_ratio_of_defender_gold():
    defender = _empire(99, gold=10_000.0)
    attacker = _empire(1, gold=500.0, effects={"gold_steal_ratio": 0.1})
    battle = _battle(defender, [1])

    loot = _compute_and_apply_loot(battle, _svc({99: defender, 1: attacker}))

    assert loot["gold"] == 1_000.0
    assert loot["per_attacker"][1]["gold"] == 1_000.0
    assert attacker.resources["gold"] == 1_500.0
    assert defender.resources["gold"] == 9_000.0
    assert battle.defender_losses["gold"] == 1_000.0
    assert battle.attacker_gains[1]["gold"] == 1_000.0


def test_no_effect_no_gold_steal():
    defender = _empire(99, gold=10_000.0)
    attacker = _empire(1)
    loot = _compute_and_apply_loot(_battle(defender, [1]), _svc({99: defender, 1: attacker}))

    assert "gold" not in loot
    assert defender.resources["gold"] == 10_000.0


def test_lost_attack_steals_no_gold():
    defender = _empire(99, gold=10_000.0)
    attacker = _empire(1, effects={"gold_steal_ratio": 0.1})
    battle = _battle(defender, [1], defender_won=True)

    loot = _compute_and_apply_loot(battle, _svc({99: defender, 1: attacker}), attacker_won=False)

    assert "gold" not in loot
    assert attacker.resources["gold"] == 0.0
    assert defender.resources["gold"] == 10_000.0


def test_multiple_winners_split_by_own_ratio():
    defender = _empire(99, gold=10_000.0)
    a1 = _empire(1, effects={"gold_steal_ratio": 0.2})
    a2 = _empire(2)
    loot = _compute_and_apply_loot(_battle(defender, [1, 2]), _svc({99: defender, 1: a1, 2: a2}))

    # 10000 × 0.2 / 2 winners = 1000; a2 has no effect.
    assert a1.resources["gold"] == 1_000.0
    assert a2.resources["gold"] == 0.0
    assert loot["gold"] == 1_000.0
    assert defender.resources["gold"] == 9_000.0


def test_ai_attacker_never_steals_gold():
    defender = _empire(99, gold=10_000.0)
    loot = _compute_and_apply_loot(_battle(defender, [AI_UID]), _svc({99: defender}))

    assert "gold" not in loot
    assert defender.resources["gold"] == 10_000.0
