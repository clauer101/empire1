"""Tests for culture life-steal on attack (_apply_culture_life_steal).

Culture is stolen from a defender based on the life lost in THIS battle
(battle.defender_losses["life"]), scaled by the defender's era. Missing life
carried over from earlier battles is never re-billed. Only *human* attackers
receive culture — pure AI attacks steal nothing. Attackers in a later era
than the defender suffer a penalty.
"""

from types import SimpleNamespace

from gameserver.engine.ai_service import AI_UID
from gameserver.network.handlers.battle_task import _apply_culture_life_steal


def _empire(uid: int, era: str = "stone", culture: float = 0.0,
            life: float = 10.0, max_life: float = 10.0):
    return SimpleNamespace(
        uid=uid,
        resources={"culture": culture, "life": life},
        max_life=max_life,
    )


def _svc(empires: dict, era_by_uid: dict, *,
         rate: float = 2000.0, era_ratio: float = 0.5):
    cfg = SimpleNamespace(
        culture_steal_per_life_and_era=rate,
        culture_era_advantage_ratio=era_ratio,
    )
    empire_service = SimpleNamespace(
        get=lambda uid: empires.get(uid),
        get_current_era=lambda emp: era_by_uid[emp.uid],
    )
    return SimpleNamespace(game_config=cfg, empire_service=empire_service)


def _battle(defender, attacker_uids, life_lost: float = 4.0):
    return SimpleNamespace(
        defender=defender,
        attacker_uids=attacker_uids,
        attacker_gains={},
        defender_losses={"life": life_lost} if life_lost else {},
    )


def test_steals_correct_amount_single_human_same_era():
    # defender: stone (idx 0), missing 4 life, rate 2000 -> 4 * 1 * 2000 = 8000
    defender = _empire(99, era="stone", culture=100_000, life=6.0, max_life=10.0)
    attacker = _empire(1, era="stone", culture=0.0)
    svc = _svc({99: defender, 1: attacker}, {99: "stone", 1: "stone"})
    battle = _battle(defender, [1])
    loot: dict = {}

    _apply_culture_life_steal(battle, svc, loot)

    assert attacker.resources["culture"] == 8000.0
    assert defender.resources["culture"] == 92_000.0
    assert loot["culture"] == 8000.0
    assert battle.defender_losses["culture"] == 8000.0


def test_capped_by_defender_culture_pool():
    # Would steal 8000 but defender only has 500.
    defender = _empire(99, era="stone", culture=500.0, life=6.0, max_life=10.0)
    attacker = _empire(1, era="stone", culture=0.0)
    svc = _svc({99: defender, 1: attacker}, {99: "stone", 1: "stone"})
    battle = _battle(defender, [1])
    loot: dict = {}

    _apply_culture_life_steal(battle, svc, loot)

    assert attacker.resources["culture"] == 500.0
    assert defender.resources["culture"] == 0.0


def test_scales_with_defender_era():
    # defender: iron (idx 3) -> 4 * (3+1) * 2000 = 32000
    defender = _empire(99, era="iron", culture=100_000, life=6.0, max_life=10.0)
    attacker = _empire(1, era="iron", culture=0.0)
    svc = _svc({99: defender, 1: attacker}, {99: "iron", 1: "iron"})
    battle = _battle(defender, [1])
    loot: dict = {}

    _apply_culture_life_steal(battle, svc, loot)

    assert attacker.resources["culture"] == 32_000.0


def test_era_penalty_for_more_advanced_attacker():
    # defender stone (idx 0), attacker industrial (idx 6 > 0) -> 0.5 penalty.
    defender = _empire(99, era="stone", culture=100_000, life=6.0, max_life=10.0)
    attacker = _empire(1, era="industrial", culture=0.0)
    svc = _svc({99: defender, 1: attacker}, {99: "stone", 1: "industrial"})
    battle = _battle(defender, [1])
    loot: dict = {}

    _apply_culture_life_steal(battle, svc, loot)

    # base 8000 * 0.5 = 4000
    assert attacker.resources["culture"] == 4000.0
    assert loot["per_attacker"][1]["culture_era_penalty"] is True
    assert loot["per_attacker"][1]["culture_era_penalty_lost"] == 4000.0
    assert battle.attacker_gains[1]["culture_era_penalty"] is True


def test_split_between_multiple_human_winners():
    # 8000 split between two same-era winners -> 4000 each.
    defender = _empire(99, era="stone", culture=100_000, life=6.0, max_life=10.0)
    a1 = _empire(1, era="stone", culture=0.0)
    a2 = _empire(2, era="stone", culture=0.0)
    svc = _svc({99: defender, 1: a1, 2: a2},
               {99: "stone", 1: "stone", 2: "stone"})
    battle = _battle(defender, [1, 2])
    loot: dict = {}

    _apply_culture_life_steal(battle, svc, loot)

    assert a1.resources["culture"] == 4000.0
    assert a2.resources["culture"] == 4000.0
    assert loot["culture"] == 8000.0


def test_ai_only_attack_no_life_steal():
    # Life-based steal is human-only; AI culture steal goes through the
    # pool-% path in _compute_and_apply_loot instead (see test_culture_loot.py).
    defender = _empire(99, era="stone", culture=100_000, life=6.0, max_life=10.0)
    svc = _svc({99: defender}, {99: "stone"})
    battle = _battle(defender, [AI_UID])
    loot: dict = {}

    _apply_culture_life_steal(battle, svc, loot)

    assert defender.resources["culture"] == 100_000.0
    assert "culture" not in loot


def test_ai_winner_excluded_human_gets_full_pool_share():
    # Mixed attack: AI_UID is filtered out, so the single human is the only
    # winner and receives the full stolen amount (not a split with the AI).
    defender = _empire(99, era="stone", culture=100_000, life=6.0, max_life=10.0)
    attacker = _empire(1, era="stone", culture=0.0)
    svc = _svc({99: defender, 1: attacker}, {99: "stone", 1: "stone"})
    battle = _battle(defender, [AI_UID, 1])
    loot: dict = {}

    _apply_culture_life_steal(battle, svc, loot)

    assert attacker.resources["culture"] == 8000.0


def test_no_life_lost_steals_nothing():
    defender = _empire(99, era="stone", culture=100_000, life=10.0, max_life=10.0)
    attacker = _empire(1, era="stone", culture=0.0)
    svc = _svc({99: defender, 1: attacker}, {99: "stone", 1: "stone"})
    battle = _battle(defender, [1], life_lost=0.0)
    loot: dict = {}

    _apply_culture_life_steal(battle, svc, loot)

    assert attacker.resources["culture"] == 0.0
    assert "culture" not in loot


def test_consecutive_battles_bill_each_leak_only_once():
    # Player report: repeated (even won) defenses kept losing huge culture
    # because the old formula re-billed ALL missing life every battle.
    # Two battles without life regen in between: battle 1 leaks 4 life,
    # battle 2 leaks 1 -> total stolen must be (4 + 1) * 2000, not
    # 4*2000 + (4+1)*2000.
    defender = _empire(99, era="stone", culture=100_000, life=10.0, max_life=10.0)
    attacker = _empire(1, era="stone", culture=0.0)
    svc = _svc({99: defender, 1: attacker}, {99: "stone", 1: "stone"})

    battle1 = _battle(defender, [1], life_lost=4.0)
    defender.resources["life"] -= 4.0  # damage applied by the battle loop
    _apply_culture_life_steal(battle1, svc, {})
    assert attacker.resources["culture"] == 8000.0

    battle2 = _battle(defender, [1], life_lost=1.0)
    defender.resources["life"] -= 1.0  # life from battle 1 not regenerated
    _apply_culture_life_steal(battle2, svc, {})

    assert attacker.resources["culture"] == 10_000.0  # +2000, not +10_000
    assert defender.resources["culture"] == 90_000.0


def test_preexisting_missing_life_is_not_rebilled():
    # Defender enters the battle already missing 8 life from earlier battles;
    # this battle leaks only 1 damage -> steal is 1 * 1 * 2000, not 9 * 2000.
    defender = _empire(99, era="stone", culture=100_000, life=1.0, max_life=10.0)
    attacker = _empire(1, era="stone", culture=0.0)
    svc = _svc({99: defender, 1: attacker}, {99: "stone", 1: "stone"})
    battle = _battle(defender, [1], life_lost=1.0)
    loot: dict = {}

    _apply_culture_life_steal(battle, svc, loot)

    assert attacker.resources["culture"] == 2000.0
    assert defender.resources["culture"] == 98_000.0
