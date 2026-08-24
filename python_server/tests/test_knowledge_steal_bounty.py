"""Regression test: stealing knowledge that completes a winner's research
must still pay Maja's Scholar's Bounty (gold_lump_sum_after_research).

Bug: knowledge-steal loot decremented the winner's `empire.knowledge[iid]`
directly, bypassing `_progress_knowledge`'s completion block entirely
whenever the stolen item wasn't the winner's actively-queued research
(`empire.research_queue`) — so the gold bounty, item effects, and
ItemCompleted event never fired for that item.
"""

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from gameserver.engine.empire_service import EmpireService
from gameserver.engine.upgrade_provider import UpgradeProvider
from gameserver.loaders.item_loader import load_items
from gameserver.main import _load_rulers
from gameserver.models.battle import BattleState
from gameserver.models.empire import Empire
from gameserver.network.handlers import _compute_and_apply_loot
from gameserver.util.events import EventBus

CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"

AI_UID = 0


@pytest.fixture
def upgrade_provider():
    items = load_items(CONFIG_DIR)
    provider = UpgradeProvider()
    provider.load(items)
    return provider


@pytest.fixture
def empire_service(upgrade_provider):
    rulers = _load_rulers(CONFIG_DIR / "rulers.yaml")
    return EmpireService(upgrade_provider, EventBus(), rulers=rulers)


def _give_scholars_bounty(empire: Empire) -> None:
    """Set the empire's ruler to Maja with Grand Architect's Decree (R skill) at
    level 1 — real rulers.yaml grants gold_lump_sum_after_research: 50000 at that
    level. (Season balance pass moved this payload from the W skill to R; W now
    grants workshop_cost_modifier instead.)"""
    empire.ruler.type = "MAJA"
    empire.ruler.r = 1


def _make_item(iid, effort=100.0):
    item = MagicMock()
    item.effort = effort
    item.name = iid
    return item


def _make_svc(empire_service, items: dict):
    cfg = MagicMock()
    cfg.min_lose_knowledge = 0.5
    cfg.max_lose_knowledge = 0.5  # fixed 50% for deterministic tests
    cfg.min_lose_culture = 0.0
    cfg.max_lose_culture = 0.0
    cfg.restore_life_after_loss_offset = 0.0

    up = MagicMock()
    up.items = items

    svc = MagicMock()
    svc.game_config = cfg
    svc.upgrade_provider = up
    svc.empire_service = empire_service
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


class TestKnowledgeStealPaysBounty:
    def test_completing_stolen_item_not_in_research_queue_pays_bounty(
        self, empire_service, upgrade_provider,
    ):
        """Winner has the stolen item in progress but NOT actively queued —
        completion (and the gold bounty) must still fire."""
        items = {"TECH": _make_item("TECH", effort=100.0)}
        svc = _make_svc(empire_service, items)

        battle = _make_battle(attacker_uid=1, defender_uid=2)
        battle.defender.knowledge = {"TECH": 20.0}  # 80% done → gain = 80 * 0.5 = 40

        winner = Empire(uid=1, name="Winner")
        winner.knowledge["TECH"] = 5.0  # nearly done, 5 remaining — will be finished off
        winner.research_queue = "OTHER_TECH"  # actively researching something else
        _give_scholars_bounty(winner)
        empire_service.register(winner)

        _compute_and_apply_loot(battle, svc)

        assert winner.knowledge["TECH"] == 0.0
        assert winner.resources["gold"] == pytest.approx(50000.0)
        # research_queue pointed at a different item — must be left untouched
        assert winner.research_queue == "OTHER_TECH"

    def test_completing_stolen_item_that_is_actively_queued_pays_bounty(
        self, empire_service, upgrade_provider,
    ):
        """Winner has the stolen item as their actively-queued research —
        completion must clear research_queue and pay the bounty."""
        items = {"TECH": _make_item("TECH", effort=100.0)}
        svc = _make_svc(empire_service, items)

        battle = _make_battle(attacker_uid=1, defender_uid=2)
        battle.defender.knowledge = {"TECH": 20.0}

        winner = Empire(uid=1, name="Winner")
        winner.knowledge["TECH"] = 5.0
        winner.research_queue = "TECH"
        _give_scholars_bounty(winner)
        empire_service.register(winner)

        _compute_and_apply_loot(battle, svc)

        assert winner.knowledge["TECH"] == 0.0
        assert winner.resources["gold"] == pytest.approx(50000.0)
        assert winner.research_queue is None

    def test_partial_progress_without_completion_pays_no_bounty(
        self, empire_service, upgrade_provider,
    ):
        """Stolen progress that doesn't finish the item must not pay a bounty."""
        items = {"TECH": _make_item("TECH", effort=100.0)}
        svc = _make_svc(empire_service, items)

        battle = _make_battle(attacker_uid=1, defender_uid=2)
        battle.defender.knowledge = {"TECH": 20.0}  # gain = 40, far from finishing

        winner = Empire(uid=1, name="Winner")
        winner.knowledge["TECH"] = 90.0  # 40 gain leaves 50 remaining — not complete
        _give_scholars_bounty(winner)
        empire_service.register(winner)

        _compute_and_apply_loot(battle, svc)

        assert winner.knowledge["TECH"] == pytest.approx(50.0)
        assert winner.resources.get("gold", 0.0) == 0.0

    def test_winner_without_prior_progress_does_not_falsely_complete(
        self, empire_service, upgrade_provider,
    ):
        """Winner who never started this item (no entry in .knowledge) must
        not be treated as 'completing' it just because the loot code's
        internal default (effort) makes the subtraction land <= 0 only when
        gain >= effort — guards the w_was_in_progress check itself."""
        items = {"TECH": _make_item("TECH", effort=10.0)}
        svc = _make_svc(empire_service, items)

        battle = _make_battle(attacker_uid=1, defender_uid=2)
        battle.defender.knowledge = {"TECH": 1.0}  # 9 progress → gain = 9 * 0.5 = 4.5

        winner = Empire(uid=1, name="Winner")
        # no "TECH" key at all — winner has never touched this research
        _give_scholars_bounty(winner)
        empire_service.register(winner)

        _compute_and_apply_loot(battle, svc)

        assert winner.resources.get("gold", 0.0) == 0.0
