"""Unit tests for knowledge theft logic in _compute_and_apply_loot."""

from unittest.mock import MagicMock
import pytest

from gameserver.models.empire import Empire
from gameserver.models.battle import BattleState
from gameserver.network.handlers import _compute_and_apply_loot


AI_UID = 0


def _make_item(iid, effort=100.0):
    item = MagicMock()
    item.effort = effort
    item.name = iid
    return item


def _make_svc(items: dict = None):
    cfg = MagicMock()
    cfg.min_lose_knowledge = 0.5
    cfg.max_lose_knowledge = 0.5   # fixed 50% for deterministic tests
    cfg.min_lose_culture = 0.0
    cfg.max_lose_culture = 0.0
    cfg.restore_life_after_loss_offset = 0.0

    up = MagicMock()
    up.items = items or {}

    svc = MagicMock()
    svc.game_config = cfg
    svc.upgrade_provider = up
    svc.empire_service.recalculate_effects = MagicMock()
    return svc


def _make_battle(attacker_uid: int, defender_uid: int) -> BattleState:
    defender = Empire(uid=defender_uid, name="Defender")
    battle = BattleState(
        bid=1,
        defender=defender,
        attacker_uids=[attacker_uid],
        attacker_gains={attacker_uid: {}},
    )
    battle.defender_won = False
    return battle


# ── AI wins — steals item with most progress ──────────────────────────────────

class TestAiWinsKnowledgeSteal:
    def test_ai_steals_item_with_most_progress(self):
        """Should pick item with highest (effort - remaining), i.e. most work done."""
        items = {
            "TECH_A": _make_item("TECH_A", effort=100.0),
            "TECH_B": _make_item("TECH_B", effort=100.0),
        }
        svc = _make_svc(items)
        battle = _make_battle(attacker_uid=AI_UID, defender_uid=1)
        battle.defender.knowledge = {
            "TECH_A": 80.0,   # progress = 20
            "TECH_B": 20.0,   # progress = 80 ← most
        }

        loot = _compute_and_apply_loot(battle, svc)

        assert loot["knowledge"]["iid"] == "TECH_B"

    def test_steals_correct_item_with_varying_effort(self):
        """When effort differs, progress = effort - remaining, not just remaining."""
        items = {
            "TECH_A": _make_item("TECH_A", effort=200.0),  # remaining=180 → progress=20
            "TECH_B": _make_item("TECH_B", effort=100.0),  # remaining=50  → progress=50 ← most
        }
        svc = _make_svc(items)
        battle = _make_battle(attacker_uid=AI_UID, defender_uid=1)
        battle.defender.knowledge = {
            "TECH_A": 180.0,
            "TECH_B": 50.0,
        }

        loot = _compute_and_apply_loot(battle, svc)

        assert loot["knowledge"]["iid"] == "TECH_B"

    def test_ai_win_increases_defender_remaining(self):
        """Stolen progress is added back to defender's remaining effort."""
        items = {"TECH": _make_item("TECH", effort=100.0)}
        svc = _make_svc(items)
        battle = _make_battle(attacker_uid=AI_UID, defender_uid=1)
        battle.defender.knowledge = {"TECH": 20.0}   # 80% done → gain = 80 * 0.5 = 40

        _compute_and_apply_loot(battle, svc)

        assert battle.defender.knowledge["TECH"] == pytest.approx(60.0)

    def test_ai_win_defender_cannot_exceed_full_effort(self):
        """Stolen amount is capped so remaining never exceeds full effort."""
        items = {"TECH": _make_item("TECH", effort=100.0)}
        svc = _make_svc(items)
        battle = _make_battle(attacker_uid=AI_UID, defender_uid=1)
        battle.defender.knowledge = {"TECH": 5.0}  # 95% done → gain = 95 * 0.5 = 47.5

        _compute_and_apply_loot(battle, svc)

        assert battle.defender.knowledge["TECH"] <= 100.0

    def test_ai_win_no_steal_when_no_active_research(self):
        """No knowledge in progress → nothing to steal."""
        items = {"DONE": _make_item("DONE", effort=100.0)}
        svc = _make_svc(items)
        battle = _make_battle(attacker_uid=AI_UID, defender_uid=1)
        battle.defender.knowledge = {"DONE": 0.0}   # completed, not active

        loot = _compute_and_apply_loot(battle, svc)

        assert loot.get("knowledge") is None

    def test_ai_win_does_not_credit_ai_knowledge_dict(self):
        """AI attacker must not accumulate knowledge entries."""
        items = {"TECH": _make_item("TECH", effort=100.0)}
        svc = _make_svc(items)
        battle = _make_battle(attacker_uid=AI_UID, defender_uid=1)
        battle.defender.knowledge = {"TECH": 30.0}

        _compute_and_apply_loot(battle, svc)

        # AI never receives knowledge credits — attacker_gains has no knowledge entry
        assert "TECH" not in battle.attacker_gains.get(AI_UID, {})


# ── AI loses — no knowledge steal ────────────────────────────────────────────

class TestAiDefeatNoKnowledgeSteal:
    def test_ai_defeat_no_knowledge_stolen(self):
        """On defender victory, knowledge is never stolen — regardless of whether
        _compute_and_apply_loot ends up being called at all (it also runs on a lost
        attack if some critters reached, for the culture-steal-on-partial-siege
        feature, but knowledge steal is explicitly gated on attacker_won=True)."""
        battle = _make_battle(attacker_uid=AI_UID, defender_uid=1)
        battle.defender.knowledge = {"TECH": 30.0}
        original = dict(battle.defender.knowledge)
        svc = _make_svc({"TECH": _make_item("TECH", effort=100.0)})

        _compute_and_apply_loot(battle, svc, attacker_won=False)

        assert battle.defender.knowledge == original

    def test_ai_defeat_no_artifact_stolen(self):
        """When AI loses, no artifact is stolen in either direction."""
        from gameserver.network.handlers import _apply_artifact_steal

        battle = _make_battle(attacker_uid=AI_UID, defender_uid=1)
        battle.defender.artifacts = ["CROWN"]
        svc = _make_svc()
        svc.game_config.base_artifact_steal_victory = 1.0
        svc.game_config.base_artifact_steal_defeat = 1.0

        stolen, *_ = _apply_artifact_steal(battle, svc, attacker_won=False)

        assert stolen == []
        assert battle.defender.artifacts == ["CROWN"]

    def test_ai_win_no_artifact_stolen(self):
        """AI never steals artifacts even on win."""
        from gameserver.network.handlers import _apply_artifact_steal

        battle = _make_battle(attacker_uid=AI_UID, defender_uid=1)
        battle.defender.artifacts = ["CROWN"]
        svc = _make_svc()
        svc.game_config.base_artifact_steal_victory = 1.0

        stolen, *_ = _apply_artifact_steal(battle, svc, attacker_won=True)

        assert stolen == []
        assert battle.defender.artifacts == ["CROWN"]


# ── Human attacker loses (partial siege) — no knowledge steal, unlike culture ──

class TestHumanDefeatNoKnowledgeSteal:
    def test_human_defeat_with_critters_reached_still_no_knowledge_stolen(self):
        """A lost attack where some critters reached the castle steals culture
        (tested elsewhere) but must NOT steal research — attacker_won=False
        must fully suppress the knowledge-steal block."""
        items = {"TECH": _make_item("TECH", effort=100.0)}
        svc = _make_svc(items)
        battle = _make_battle(attacker_uid=5, defender_uid=1)
        battle.defender.knowledge = {"TECH": 20.0}
        original = dict(battle.defender.knowledge)

        loot = _compute_and_apply_loot(battle, svc, attacker_won=False)

        assert battle.defender.knowledge == original
        assert loot["knowledge"] is None

    def test_human_win_still_steals_knowledge(self):
        """Sanity check: the default (attacker_won=True) behavior is unchanged."""
        items = {"TECH": _make_item("TECH", effort=100.0)}
        svc = _make_svc(items)
        battle = _make_battle(attacker_uid=5, defender_uid=1)
        battle.defender.knowledge = {"TECH": 20.0}
        attacker = Empire(uid=5, name="Attacker")
        svc.empire_service.get = lambda uid: attacker if uid == 5 else None

        loot = _compute_and_apply_loot(battle, svc, attacker_won=True)

        assert loot["knowledge"]["iid"] == "TECH"
