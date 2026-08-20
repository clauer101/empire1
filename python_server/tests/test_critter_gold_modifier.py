"""Tests for the critter_gold_modifier empire effect (docs/EFFECTSGUIDE.md)."""

from __future__ import annotations

from types import SimpleNamespace

from gameserver.network.handlers.battle_task import _apply_critter_gold_bonus


def _defender(gold: float = 0.0, effects: dict | None = None):
    return SimpleNamespace(uid=99, resources={"gold": gold}, effects=effects or {})


def _battle(defender, defender_gold_earned: float):
    return SimpleNamespace(bid=1, defender=defender, defender_gold_earned=defender_gold_earned)


class TestCritterGoldModifier:
    def test_bonus_granted_proportional_to_gold_earned(self):
        defender = _defender(gold=100.0, effects={"critter_gold_modifier": 0.1})
        battle = _battle(defender, defender_gold_earned=50.0)

        bonus = _apply_critter_gold_bonus(battle)

        assert bonus == 5.0
        assert defender.resources["gold"] == 105.0

    def test_no_bonus_without_effect(self):
        defender = _defender(gold=100.0, effects={})
        battle = _battle(defender, defender_gold_earned=50.0)

        bonus = _apply_critter_gold_bonus(battle)

        assert bonus == 0.0
        assert defender.resources["gold"] == 100.0

    def test_no_bonus_when_no_gold_earned(self):
        defender = _defender(gold=100.0, effects={"critter_gold_modifier": 0.1})
        battle = _battle(defender, defender_gold_earned=0.0)

        bonus = _apply_critter_gold_bonus(battle)

        assert bonus == 0.0
        assert defender.resources["gold"] == 100.0

    def test_no_bonus_without_defender(self):
        battle = _battle(defender=None, defender_gold_earned=50.0)

        bonus = _apply_critter_gold_bonus(battle)

        assert bonus == 0.0
