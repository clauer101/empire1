"""Tests for battle subscription exclusivity.

A UID must be subscribed to at most one battle/attack at a time.
New subscriptions must silently evict the UID from all previous ones.
"""

from __future__ import annotations



from gameserver.network.handlers import _evict_observer_from_all
from gameserver.models.battle import BattleState
from gameserver.models.attack import Attack, AttackPhase


# ── Helpers ──────────────────────────────────────────────────────────────────

def _make_attack(attack_id: int, defender_uid: int, attacker_uid: int = 99) -> Attack:
    a = Attack(
        attack_id=attack_id,
        attacker_uid=attacker_uid,
        defender_uid=defender_uid,
        army_aid=1,
        phase=AttackPhase.IN_SIEGE,
    )
    a._observers: set[int] = set()
    return a


def _make_battle(bid: int, defender_uid: int, attack_id: int, observers: set[int]) -> BattleState:
    return BattleState(
        bid=bid,
        defender=None,
        attacker=None,
        attack_id=attack_id,
        observer_uids=set(observers),
    )


# ── Tests ─────────────────────────────────────────────────────────────────────

class TestEvictObserverFromAll:
    """Unit tests for _evict_observer_from_all."""

    def test_evicts_uid_from_other_attack_observers(self):
        """UID is removed from a different attack's _observers."""
        old_attack = _make_attack(attack_id=1, defender_uid=10)
        new_attack = _make_attack(attack_id=2, defender_uid=20)

        uid = 42
        old_attack._observers.add(uid)

        _evict_observer_from_all(
            uid,
            all_attacks=[old_attack, new_attack],
            active_battles={},
            exclude_attack_id=new_attack.attack_id,
        )

        assert uid not in old_attack._observers
        assert uid not in new_attack._observers  # never added to new_attack here

    def test_does_not_evict_from_excluded_attack(self):
        """UID already in the target attack's observers must not be removed."""
        attack = _make_attack(attack_id=5, defender_uid=10)
        uid = 7
        attack._observers.add(uid)

        _evict_observer_from_all(
            uid,
            all_attacks=[attack],
            active_battles={},
            exclude_attack_id=5,
        )

        assert uid in attack._observers  # untouched

    def test_evicts_uid_from_other_active_battle(self):
        """UID is removed from a different BattleState's observer_uids."""
        uid = 55
        old_battle = _make_battle(bid=1, defender_uid=10, attack_id=1, observers={uid, 99})
        new_attack = _make_attack(attack_id=2, defender_uid=20)
        new_battle = _make_battle(bid=2, defender_uid=20, attack_id=2, observers=set())

        active_battles = {10: old_battle, 20: new_battle}

        _evict_observer_from_all(
            uid,
            all_attacks=[],
            active_battles=active_battles,
            exclude_attack_id=new_attack.attack_id,
        )

        assert uid not in old_battle.observer_uids
        assert 99 in old_battle.observer_uids           # other observer untouched
        assert uid not in new_battle.observer_uids      # new battle untouched

    def test_does_not_evict_from_excluded_battle(self):
        """UID must not be evicted from the battle that matches exclude_attack_id."""
        uid = 42
        battle = _make_battle(bid=3, defender_uid=30, attack_id=10, observers={uid})
        active_battles = {30: battle}

        _evict_observer_from_all(
            uid,
            all_attacks=[],
            active_battles=active_battles,
            exclude_attack_id=10,
        )

        assert uid in battle.observer_uids  # untouched

    def test_evicts_from_multiple_old_attacks(self):
        """UID registered in several old attacks is removed from all of them."""
        uid = 1
        attacks = [_make_attack(attack_id=i, defender_uid=i * 10) for i in range(1, 5)]
        for a in attacks:
            a._observers.add(uid)

        new_attack = _make_attack(attack_id=99, defender_uid=990)

        _evict_observer_from_all(
            uid,
            all_attacks=attacks + [new_attack],
            active_battles={},
            exclude_attack_id=99,
        )

        for a in attacks:
            assert uid not in a._observers

    def test_tolerates_attack_without_observers_attr(self):
        """Attacks that never had _observers set must not raise."""
        a = Attack(
            attack_id=1,
            attacker_uid=10,
            defender_uid=20,
            army_aid=1,
            phase=AttackPhase.TRAVELLING,
        )
        # No _observers attribute set

        # Must not raise
        _evict_observer_from_all(42, all_attacks=[a], active_battles={}, exclude_attack_id=99)

    def test_no_others_when_no_previous_subscriptions(self):
        """If uid was not subscribed anywhere, nothing changes."""
        uid = 77
        attack = _make_attack(attack_id=1, defender_uid=10)
        battle = _make_battle(bid=1, defender_uid=10, attack_id=1, observers={5, 6})
        active_battles = {10: battle}

        _evict_observer_from_all(uid, all_attacks=[attack], active_battles=active_battles, exclude_attack_id=99)

        assert battle.observer_uids == {5, 6}
        assert uid not in attack._observers
