"""Unit tests for _apply_artefact_steal in handlers.py."""

from unittest.mock import MagicMock, patch

from gameserver.models.empire import Empire
from gameserver.models.battle import BattleState
from gameserver.network.handlers import _apply_artefact_steal


def _make_battle(attacker_uid: int, defender_uid: int) -> BattleState:
    attacker = Empire(uid=attacker_uid, name="Attacker")
    defender = Empire(uid=defender_uid, name="Defender")
    return BattleState(bid=1, defender=defender, attacker=attacker)


def _make_svc(victory_chance: float = 0.5, defeat_chance: float = 0.05):
    cfg = MagicMock()
    cfg.base_artifact_steal_victory = victory_chance
    cfg.base_artifact_steal_defeat = defeat_chance

    empire_svc = MagicMock()
    empire_svc.recalculate_effects = MagicMock()

    svc = MagicMock()
    svc.game_config = cfg
    svc.empire_service = empire_svc
    return svc


# ── Attacker-win (victory) ────────────────────────────────────────────────────

class TestAttackerWin:
    def test_steals_artefact_when_roll_succeeds(self):
        battle = _make_battle(attacker_uid=2, defender_uid=1)
        battle.defender.artefacts = ["SWORD_OF_POWER"]
        svc = _make_svc(victory_chance=1.0)

        result = _apply_artefact_steal(battle, svc, attacker_won=True)

        assert result == "SWORD_OF_POWER"
        assert "SWORD_OF_POWER" not in battle.defender.artefacts
        assert "SWORD_OF_POWER" in battle.attacker.artefacts

    def test_no_steal_when_roll_fails(self):
        battle = _make_battle(attacker_uid=2, defender_uid=1)
        battle.defender.artefacts = ["SWORD_OF_POWER"]
        svc = _make_svc(victory_chance=0.0)

        result = _apply_artefact_steal(battle, svc, attacker_won=True)

        assert result is None
        assert battle.defender.artefacts == ["SWORD_OF_POWER"]
        assert battle.attacker.artefacts == []

    def test_no_steal_when_defender_has_no_artefacts(self):
        battle = _make_battle(attacker_uid=2, defender_uid=1)
        svc = _make_svc(victory_chance=1.0)

        result = _apply_artefact_steal(battle, svc, attacker_won=True)

        assert result is None

    def test_only_one_artefact_stolen_even_if_multiple_exist(self):
        battle = _make_battle(attacker_uid=2, defender_uid=1)
        battle.defender.artefacts = ["ART_A", "ART_B", "ART_C"]
        svc = _make_svc(victory_chance=1.0)

        result = _apply_artefact_steal(battle, svc, attacker_won=True)

        assert result is not None
        assert len(battle.attacker.artefacts) == 1
        assert len(battle.defender.artefacts) == 2

    def test_recalculate_effects_called_on_both_empires(self):
        battle = _make_battle(attacker_uid=2, defender_uid=1)
        battle.defender.artefacts = ["SWORD_OF_POWER"]
        svc = _make_svc(victory_chance=1.0)

        _apply_artefact_steal(battle, svc, attacker_won=True)

        calls = [c.args[0] for c in svc.empire_service.recalculate_effects.call_args_list]
        assert battle.defender in calls
        assert battle.attacker in calls

    def test_uses_victory_chance_not_defeat_chance(self):
        battle = _make_battle(attacker_uid=2, defender_uid=1)
        battle.defender.artefacts = ["ART"]
        svc = _make_svc(victory_chance=0.0, defeat_chance=1.0)

        result = _apply_artefact_steal(battle, svc, attacker_won=True)

        assert result is None  # victory_chance=0 → no steal despite defeat_chance=1


# ── Defender-win (attacker defeated) ─────────────────────────────────────────
# Artefacts are always stolen FROM the defender — the attacker never loses artefacts.

class TestDefenderWin:
    def test_attacker_can_still_steal_from_defender_on_loss(self):
        battle = _make_battle(attacker_uid=2, defender_uid=1)
        battle.defender.artefacts = ["CROWN"]
        svc = _make_svc(defeat_chance=1.0)

        result = _apply_artefact_steal(battle, svc, attacker_won=False)

        assert result == "CROWN"
        assert "CROWN" not in battle.defender.artefacts
        assert "CROWN" in battle.attacker.artefacts

    def test_attacker_does_not_lose_own_artefacts_on_loss(self):
        battle = _make_battle(attacker_uid=2, defender_uid=1)
        battle.attacker.artefacts = ["SWORD"]
        battle.defender.artefacts = []
        svc = _make_svc(defeat_chance=1.0)

        _apply_artefact_steal(battle, svc, attacker_won=False)

        assert battle.attacker.artefacts == ["SWORD"]

    def test_no_steal_when_roll_fails(self):
        battle = _make_battle(attacker_uid=2, defender_uid=1)
        battle.defender.artefacts = ["CROWN"]
        svc = _make_svc(defeat_chance=0.0)

        result = _apply_artefact_steal(battle, svc, attacker_won=False)

        assert result is None
        assert battle.defender.artefacts == ["CROWN"]

    def test_uses_defeat_chance_not_victory_chance(self):
        battle = _make_battle(attacker_uid=2, defender_uid=1)
        battle.defender.artefacts = ["ART"]
        svc = _make_svc(victory_chance=1.0, defeat_chance=0.0)

        result = _apply_artefact_steal(battle, svc, attacker_won=False)

        assert result is None  # defeat_chance=0 → no steal despite victory_chance=1


# ── AI attacker ───────────────────────────────────────────────────────────────

class TestAiAttacker:
    AI_UID = 0

    def test_ai_never_steals_on_win(self):
        battle = _make_battle(attacker_uid=self.AI_UID, defender_uid=1)
        battle.defender.artefacts = ["CROWN"]
        svc = _make_svc(victory_chance=1.0)

        result = _apply_artefact_steal(battle, svc, attacker_won=True)

        assert result is None
        assert battle.defender.artefacts == ["CROWN"]

    def test_ai_never_steals_on_loss(self):
        battle = _make_battle(attacker_uid=self.AI_UID, defender_uid=1)
        battle.attacker.artefacts = ["CROWN"]
        svc = _make_svc(defeat_chance=1.0)

        result = _apply_artefact_steal(battle, svc, attacker_won=False)

        assert result is None
        assert battle.attacker.artefacts == ["CROWN"]

    def test_no_artefact_steal_at_all_when_ai_is_attacker(self):
        """When the battle was initiated by the AI, no artefact steal happens
        in either direction — not even the defender stealing from the AI."""
        battle = _make_battle(attacker_uid=self.AI_UID, defender_uid=1)
        battle.attacker.artefacts = ["ART"]
        svc = _make_svc(defeat_chance=1.0)

        result = _apply_artefact_steal(battle, svc, attacker_won=False)

        assert result is None
        assert battle.attacker.artefacts == ["ART"]


# ── Exact roll boundary ───────────────────────────────────────────────────────

class TestExactRoll:
    """Validate that the random roll is compared correctly against the chance."""

    CHANCE = 0.4

    def _battle_with_artefact(self) -> BattleState:
        battle = _make_battle(attacker_uid=2, defender_uid=1)
        battle.defender.artefacts = ["GOLDEN_SHIELD"]
        return battle

    @patch("random.random")
    def test_defender_loses_artefact_when_roll_is_below_chance(self, mock_random):
        mock_random.return_value = self.CHANCE - 0.01  # just below threshold
        battle = self._battle_with_artefact()
        svc = _make_svc(victory_chance=self.CHANCE)

        result = _apply_artefact_steal(battle, svc, attacker_won=True)

        assert result == "GOLDEN_SHIELD"
        assert "GOLDEN_SHIELD" not in battle.defender.artefacts
        assert "GOLDEN_SHIELD" in battle.attacker.artefacts

    @patch("random.random")
    def test_defender_keeps_artefact_when_roll_equals_chance(self, mock_random):
        mock_random.return_value = self.CHANCE  # equal → not strictly less than
        battle = self._battle_with_artefact()
        svc = _make_svc(victory_chance=self.CHANCE)

        result = _apply_artefact_steal(battle, svc, attacker_won=True)

        assert result is None
        assert battle.defender.artefacts == ["GOLDEN_SHIELD"]

    @patch("random.random")
    def test_defender_keeps_artefact_when_roll_is_above_chance(self, mock_random):
        mock_random.return_value = self.CHANCE + 0.01  # just above threshold
        battle = self._battle_with_artefact()
        svc = _make_svc(victory_chance=self.CHANCE)

        result = _apply_artefact_steal(battle, svc, attacker_won=True)

        assert result is None
        assert battle.defender.artefacts == ["GOLDEN_SHIELD"]
