"""Unit tests for _apply_artefact_steal in handlers.py."""

from unittest.mock import MagicMock, patch

from gameserver.models.empire import Empire
from gameserver.models.battle import BattleState
from gameserver.network.handlers import _apply_artefact_steal

ATTACKER_UID = 2
DEFENDER_UID = 1


def _make_battle(attacker_uid: int = ATTACKER_UID, defender_uid: int = DEFENDER_UID) -> tuple[BattleState, Empire, Empire]:
    attacker = Empire(uid=attacker_uid, name="Attacker")
    defender = Empire(uid=defender_uid, name="Defender")
    battle = BattleState(
        bid=1,
        defender=defender,
        attacker_uids=[attacker_uid],
        attacker_gains={attacker_uid: {}},
    )
    return battle, attacker, defender


def _make_svc(attacker: Empire, victory_chance: float = 0.5, defeat_chance: float = 0.05):
    cfg = MagicMock()
    cfg.base_artifact_steal_victory = victory_chance
    cfg.base_artifact_steal_defeat = defeat_chance

    empire_svc = MagicMock()
    empire_svc.get = MagicMock(return_value=attacker)
    empire_svc.recalculate_effects = MagicMock()

    svc = MagicMock()
    svc.game_config = cfg
    svc.empire_service = empire_svc
    return svc


# ── Attacker-win (victory) ────────────────────────────────────────────────────

class TestAttackerWin:
    def test_steals_artefact_when_roll_succeeds(self):
        battle, attacker, defender = _make_battle()
        defender.artefacts = ["SWORD_OF_POWER"]
        svc = _make_svc(attacker, victory_chance=1.0)

        iid, winner_uid = _apply_artefact_steal(battle, svc, attacker_won=True)

        assert iid == "SWORD_OF_POWER"
        assert winner_uid == ATTACKER_UID
        assert "SWORD_OF_POWER" not in defender.artefacts
        assert "SWORD_OF_POWER" in attacker.artefacts

    def test_no_steal_when_roll_fails(self):
        battle, attacker, defender = _make_battle()
        defender.artefacts = ["SWORD_OF_POWER"]
        svc = _make_svc(attacker, victory_chance=0.0)

        iid, winner_uid = _apply_artefact_steal(battle, svc, attacker_won=True)

        assert iid is None
        assert winner_uid is None
        assert defender.artefacts == ["SWORD_OF_POWER"]
        assert attacker.artefacts == []

    def test_no_steal_when_defender_has_no_artefacts(self):
        battle, attacker, defender = _make_battle()
        svc = _make_svc(attacker, victory_chance=1.0)

        iid, winner_uid = _apply_artefact_steal(battle, svc, attacker_won=True)

        assert iid is None
        assert winner_uid is None

    def test_only_one_artefact_stolen_even_if_multiple_exist(self):
        battle, attacker, defender = _make_battle()
        defender.artefacts = ["ART_A", "ART_B", "ART_C"]
        svc = _make_svc(attacker, victory_chance=1.0)

        iid, winner_uid = _apply_artefact_steal(battle, svc, attacker_won=True)

        assert iid is not None
        assert len(attacker.artefacts) == 1
        assert len(defender.artefacts) == 2

    def test_recalculate_effects_called_on_both_empires(self):
        battle, attacker, defender = _make_battle()
        defender.artefacts = ["SWORD_OF_POWER"]
        svc = _make_svc(attacker, victory_chance=1.0)

        _apply_artefact_steal(battle, svc, attacker_won=True)

        calls = [c.args[0] for c in svc.empire_service.recalculate_effects.call_args_list]
        assert defender in calls
        assert attacker in calls

    def test_uses_victory_chance_not_defeat_chance(self):
        battle, attacker, defender = _make_battle()
        defender.artefacts = ["ART"]
        svc = _make_svc(attacker, victory_chance=0.0, defeat_chance=1.0)

        iid, _ = _apply_artefact_steal(battle, svc, attacker_won=True)

        assert iid is None  # victory_chance=0 → no steal despite defeat_chance=1


# ── Defender-win (attacker defeated) ─────────────────────────────────────────
# Artefacts are always stolen FROM the defender — the attacker never loses artefacts.

class TestDefenderWin:
    def test_attacker_can_still_steal_from_defender_on_loss(self):
        battle, attacker, defender = _make_battle()
        defender.artefacts = ["CROWN"]
        svc = _make_svc(attacker, defeat_chance=1.0)

        iid, winner_uid = _apply_artefact_steal(battle, svc, attacker_won=False)

        assert iid == "CROWN"
        assert winner_uid == ATTACKER_UID
        assert "CROWN" not in defender.artefacts
        assert "CROWN" in attacker.artefacts

    def test_attacker_does_not_lose_own_artefacts_on_loss(self):
        battle, attacker, defender = _make_battle()
        attacker.artefacts = ["SWORD"]
        defender.artefacts = []
        svc = _make_svc(attacker, defeat_chance=1.0)

        _apply_artefact_steal(battle, svc, attacker_won=False)

        assert attacker.artefacts == ["SWORD"]

    def test_no_steal_when_roll_fails(self):
        battle, attacker, defender = _make_battle()
        defender.artefacts = ["CROWN"]
        svc = _make_svc(attacker, defeat_chance=0.0)

        iid, winner_uid = _apply_artefact_steal(battle, svc, attacker_won=False)

        assert iid is None
        assert winner_uid is None
        assert defender.artefacts == ["CROWN"]
