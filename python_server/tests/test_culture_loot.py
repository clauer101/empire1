"""Tests for pool-% culture steal in _compute_and_apply_loot.

A pure AI attack steals a random fraction of the defender's culture pool,
scaled by ai_culture_steal_modifier. The culture is removed from the
defender but credited to nobody (the AI has no resource needs).
"""

from types import SimpleNamespace

from gameserver.engine.ai_service import AI_UID
from gameserver.network.handlers.battle_task import _compute_and_apply_loot


def _empire(uid: int, era: str = "stone", culture: float = 0.0,
            life: float = 6.0, max_life: float = 10.0):
    return SimpleNamespace(
        uid=uid,
        resources={"culture": culture, "life": life},
        max_life=max_life,
        knowledge={},
        buildings={},
        artifacts=set(),
        effects={},
        research_queue=None,
        build_queue=None,
    )


def _svc(empires: dict, era_by_uid: dict, *,
         min_c: float = 0.02, max_c: float = 0.04,
         ai_modifier: float = 0.33):
    cfg = SimpleNamespace(
        min_lose_culture=min_c,
        max_lose_culture=max_c,
        ai_culture_steal_modifier=ai_modifier,
        culture_era_advantage_ratio=0.51,
        restore_life_after_loss_offset=1.0,
    )
    empire_service = SimpleNamespace(
        get=lambda uid: empires.get(uid),
        get_current_era=lambda emp: era_by_uid[emp.uid],
    )
    return SimpleNamespace(
        game_config=cfg,
        empire_service=empire_service,
        upgrade_provider=SimpleNamespace(items={}, check_requirements=lambda *_: True),
    )


def _battle(defender, attacker_uids):
    return SimpleNamespace(
        defender=defender,
        attacker_uids=attacker_uids,
        attacker_gains={},
        defender_losses={},
        defender_won=False,
    )


def test_ai_only_steals_pool_pct_times_modifier():
    # Fixed pct range so the random draw is deterministic: 0.04 * 0.04 = same.
    defender = _empire(99, era="stone", culture=10_000.0)
    svc = _svc({99: defender}, {99: "stone"},
               min_c=0.04, max_c=0.04, ai_modifier=0.33)
    battle = _battle(defender, [AI_UID])

    loot = _compute_and_apply_loot(battle, svc)

    # 10000 * 0.04 * 0.33 = 132.0
    expected = round(10_000.0 * 0.04 * 0.33, 2)
    assert loot["culture"] == expected
    assert defender.resources["culture"] == 10_000.0 - expected
    assert battle.defender_losses["culture"] == expected
    # Credited to nobody.
    assert AI_UID not in loot["per_attacker"]


def test_ai_steal_modifier_reduces_amount():
    defender_a = _empire(99, era="stone", culture=10_000.0)
    defender_b = _empire(99, era="stone", culture=10_000.0)
    svc_full = _svc({99: defender_a}, {99: "stone"},
                    min_c=0.04, max_c=0.04, ai_modifier=1.0)
    svc_third = _svc({99: defender_b}, {99: "stone"},
                     min_c=0.04, max_c=0.04, ai_modifier=0.33)

    loot_full = _compute_and_apply_loot(_battle(defender_a, [AI_UID]), svc_full)
    loot_third = _compute_and_apply_loot(_battle(defender_b, [AI_UID]), svc_third)

    assert loot_third["culture"] < loot_full["culture"]
    assert round(loot_third["culture"] / loot_full["culture"], 2) == 0.33


def test_human_attack_ignores_ai_modifier():
    defender = _empire(99, era="stone", culture=10_000.0)
    attacker = _empire(1, era="stone", culture=0.0)
    svc = _svc({99: defender, 1: attacker}, {99: "stone", 1: "stone"},
               min_c=0.04, max_c=0.04, ai_modifier=0.33)
    battle = _battle(defender, [1])

    loot = _compute_and_apply_loot(battle, svc)

    # Full pct, no AI modifier: 10000 * 0.04 = 400, credited to the human.
    expected = round(10_000.0 * 0.04, 2)
    assert attacker.resources["culture"] == expected
    assert loot["per_attacker"][1]["culture"] == expected
