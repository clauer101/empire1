"""Unit tests for artifact_steal_victory / artifact_steal_defeat empire effects."""

from unittest.mock import MagicMock

from gameserver.models.empire import Empire
from gameserver.models.battle import BattleState
from gameserver.network.handlers import _apply_artefact_steal

ATTACKER_UID = 2
DEFENDER_UID = 1


def _make_battle(attacker_uid: int = ATTACKER_UID) -> tuple[BattleState, Empire, Empire]:
    attacker = Empire(uid=attacker_uid, name="Attacker")
    defender = Empire(uid=DEFENDER_UID, name="Defender")
    battle = BattleState(
        bid=1,
        defender=defender,
        attacker_uids=[attacker_uid],
        attacker_gains={attacker_uid: {}},
    )
    return battle, attacker, defender


def _make_svc(attacker: Empire, base_victory: float = 0.5, base_defeat: float = 0.05):
    cfg = MagicMock()
    cfg.base_artifact_steal_victory = base_victory
    cfg.base_artifact_steal_defeat = base_defeat

    empire_svc = MagicMock()
    empire_svc.get = MagicMock(return_value=attacker)
    empire_svc.recalculate_effects = MagicMock()

    svc = MagicMock()
    svc.game_config = cfg
    svc.empire_service = empire_svc
    return svc


# ── artifact_steal_victory modifier ──────────────────────────────────────────

class TestArtifactStealVictoryEffect:
    def test_modifier_zero_leaves_base_chance_unchanged(self):
        """get_effect returns 0.0 by default → chance = base * 1.0."""
        battle, attacker, defender = _make_battle()
        defender.artefacts = ["ART"]
        # base=0.0 means no steal — modifier doesn't help
        svc = _make_svc(attacker, base_victory=0.0)

        iid, _ = _apply_artefact_steal(battle, svc, attacker_won=True)

        assert iid is None

    def test_modifier_adds_to_base_chance(self):
        """artifact_steal_victory=0.5 + modifier=0.5 → effective=1.0 → guaranteed steal."""
        battle, attacker, defender = _make_battle()
        defender.artefacts = ["ART"]
        attacker.effects["artifact_steal_victory_modifier"] = 0.5
        # base=0.5 + modifier=0.5 → effective=1.0 → guaranteed steal
        svc = _make_svc(attacker, base_victory=0.5)

        iid, winner_uid = _apply_artefact_steal(battle, svc, attacker_won=True)

        assert iid == "ART"
        assert winner_uid == ATTACKER_UID

    def test_modifier_raises_below_threshold_chance_to_guarantee(self):
        """base=0.4 + modifier=0.6 → effective=1.0 → guaranteed steal."""
        battle, attacker, defender = _make_battle()
        defender.artefacts = ["ART"]
        attacker.effects["artifact_steal_victory_modifier"] = 0.6
        svc = _make_svc(attacker, base_victory=0.4)

        iid, _ = _apply_artefact_steal(battle, svc, attacker_won=True)

        assert iid == "ART"

    def test_modifier_does_not_affect_defeat_chance(self):
        """artifact_steal_victory modifier must not bleed into defeat path."""
        battle, attacker, defender = _make_battle()
        defender.artefacts = ["ART"]
        attacker.effects["artifact_steal_victory_modifier"] = 100.0
        # defeat_chance=0.0 → no steal regardless of victory modifier
        svc = _make_svc(attacker, base_victory=0.5, base_defeat=0.0)

        iid, _ = _apply_artefact_steal(battle, svc, attacker_won=False)

        assert iid is None

    def test_multiple_artefacts_all_stolen_with_guaranteed_chance(self):
        """base=0.5 + modifier=0.5 → effective=1.0 → all artefacts stolen."""
        battle, attacker, defender = _make_battle()
        defender.artefacts = ["A", "B", "C"]
        attacker.effects["artifact_steal_victory_modifier"] = 0.5
        svc = _make_svc(attacker, base_victory=0.5)

        _apply_artefact_steal(battle, svc, attacker_won=True)

        assert len(attacker.artefacts) == 3
        assert len(defender.artefacts) == 0


# ── artifact_steal_defeat modifier ───────────────────────────────────────────

class TestArtifactStealDefeatEffect:
    def test_modifier_zero_leaves_base_chance_unchanged(self):
        battle, attacker, defender = _make_battle()
        defender.artefacts = ["ART"]
        svc = _make_svc(attacker, base_defeat=0.0)

        iid, _ = _apply_artefact_steal(battle, svc, attacker_won=False)

        assert iid is None

    def test_modifier_adds_to_defeat_chance(self):
        """base=0.5 + modifier=0.5 → effective=1.0 → guaranteed steal."""
        battle, attacker, defender = _make_battle()
        defender.artefacts = ["ART"]
        attacker.effects["artifact_steal_defeat_modifier"] = 0.5
        # base=0.5 + modifier=0.5 → effective=1.0 → guaranteed steal
        svc = _make_svc(attacker, base_defeat=0.5)

        iid, winner_uid = _apply_artefact_steal(battle, svc, attacker_won=False)

        assert iid == "ART"
        assert winner_uid == ATTACKER_UID

    def test_modifier_does_not_affect_victory_chance(self):
        """artifact_steal_defeat modifier must not bleed into victory path."""
        battle, attacker, defender = _make_battle()
        defender.artefacts = ["ART"]
        attacker.effects["artifact_steal_defeat_modifier"] = 100.0
        svc = _make_svc(attacker, base_victory=0.0, base_defeat=0.5)

        iid, _ = _apply_artefact_steal(battle, svc, attacker_won=True)

        assert iid is None

    def test_multiple_artefacts_all_stolen_on_defeat_with_guaranteed_chance(self):
        battle, attacker, defender = _make_battle()
        defender.artefacts = ["X", "Y"]
        attacker.effects["artifact_steal_defeat_modifier"] = 0.5
        svc = _make_svc(attacker, base_defeat=0.5)

        _apply_artefact_steal(battle, svc, attacker_won=False)

        assert len(attacker.artefacts) == 2
        assert len(defender.artefacts) == 0


# ── Multi-attacker per-empire chance ─────────────────────────────────────────

class TestMultiAttackerEffects:
    def _make_multi_battle(self) -> tuple[BattleState, Empire, Empire, Empire]:
        att1 = Empire(uid=10, name="Att1")
        att2 = Empire(uid=11, name="Att2")
        defender = Empire(uid=1, name="Defender")
        battle = BattleState(
            bid=1,
            defender=defender,
            attacker_uids=[10, 11],
            attacker_gains={10: {}, 11: {}},
        )
        return battle, att1, att2, defender

    def test_each_attacker_uses_own_modifier(self):
        """att1 has modifier=-0.5 (base=0.5-0.5=0 → miss), att2 has modifier=0.5 → effective=1.0 → guaranteed."""
        battle, att1, att2, defender = self._make_multi_battle()
        defender.artefacts = ["ART"]

        att1.effects["artifact_steal_victory_modifier"] = -0.5   # effective = 0.5 - 0.5 = 0.0
        att2.effects["artifact_steal_victory_modifier"] = 0.5    # effective = 0.5 + 0.5 = 1.0

        cfg = MagicMock()
        cfg.base_artifact_steal_victory = 0.5
        cfg.base_artifact_steal_defeat = 0.0

        empire_store = {10: att1, 11: att2}
        empire_svc = MagicMock()
        empire_svc.get = MagicMock(side_effect=lambda uid: empire_store.get(uid))
        empire_svc.recalculate_effects = MagicMock()

        svc = MagicMock()
        svc.game_config = cfg
        svc.empire_service = empire_svc

        iid, winner_uid = _apply_artefact_steal(battle, svc, attacker_won=True)

        # att1 misses (effective=0), att2 steals (effective=1.0)
        assert iid == "ART"
        assert winner_uid == 11
        assert "ART" in att2.artefacts
        assert "ART" not in att1.artefacts

    def test_first_attacker_steals_second_gets_nothing(self):
        """When both have guaranteed chance, first in list takes the artefact."""
        battle, att1, att2, defender = self._make_multi_battle()
        defender.artefacts = ["ART"]

        cfg = MagicMock()
        cfg.base_artifact_steal_victory = 1.0
        cfg.base_artifact_steal_defeat = 0.0

        empire_store = {10: att1, 11: att2}
        empire_svc = MagicMock()
        empire_svc.get = MagicMock(side_effect=lambda uid: empire_store.get(uid))
        empire_svc.recalculate_effects = MagicMock()

        svc = MagicMock()
        svc.game_config = cfg
        svc.empire_service = empire_svc

        iid, winner_uid = _apply_artefact_steal(battle, svc, attacker_won=True)

        assert iid == "ART"
        assert winner_uid == 10
        assert "ART" in att1.artefacts
        assert att2.artefacts == []
