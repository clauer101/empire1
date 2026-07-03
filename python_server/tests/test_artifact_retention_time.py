"""Tests for the artifact_retention_time effect — protects newly acquired artifacts from theft."""

import time
from unittest.mock import MagicMock

from gameserver.models.empire import Empire
from gameserver.models.battle import BattleState
from gameserver.network.handlers import _apply_artifact_steal

ATTACKER_UID = 2
DEFENDER_UID = 1


def _make_battle() -> tuple[BattleState, Empire, Empire]:
    attacker = Empire(uid=ATTACKER_UID, name="Attacker")
    defender = Empire(uid=DEFENDER_UID, name="Defender")
    battle = BattleState(
        bid=1,
        defender=defender,
        attacker_uids=[ATTACKER_UID],
        attacker_gains={ATTACKER_UID: {}},
    )
    return battle, attacker, defender


def _make_svc(attacker: Empire, base_victory: float = 1.0):
    cfg = MagicMock()
    cfg.base_artifact_steal_victory = base_victory
    cfg.base_artifact_steal_defeat = 0.05
    cfg.steal_power_thresholds = [200.0]
    cfg.steal_min_multiplier = 0.10

    empire_svc = MagicMock()
    empire_svc.get = MagicMock(return_value=attacker)
    empire_svc.recalculate_effects = MagicMock()
    empire_svc.get_current_era = MagicMock(return_value="stone")

    svc = MagicMock()
    svc.game_config = cfg
    svc.empire_service = empire_svc
    svc.upgrade_provider = MagicMock()
    svc.upgrade_provider.items = {}
    return svc


class TestArtifactRetentionTime:
    def test_artifact_within_retention_window_cannot_be_stolen(self):
        """Artifact acquired recently is fully protected — steal chance effectively 0."""
        battle, attacker, defender = _make_battle()
        defender.artifacts = ["ART_A"]
        defender.artifact_acquired_at = {"ART_A": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat()}  # just acquired
        defender.effects["artifact_retention_time"] = 3600.0  # 1h protection

        svc = _make_svc(attacker, base_victory=1.0)  # 100% base chance — would always steal

        stolen, *_ = _apply_artifact_steal(battle, svc, attacker_won=True)

        assert stolen == [], "Artifact inside retention window must not be stolen"
        assert "ART_A" in defender.artifacts

    def test_artifact_outside_retention_window_can_be_stolen(self):
        """Artifact acquired longer ago than retention_time is stealable."""
        battle, attacker, defender = _make_battle()
        defender.artifacts = ["ART_B"]
        defender.artifact_acquired_at = {"ART_B": time.time() - 7200.0}  # 2h ago
        defender.effects["artifact_retention_time"] = 3600.0  # only 1h protection

        svc = _make_svc(attacker, base_victory=1.0)

        stolen, *_ = _apply_artifact_steal(battle, svc, attacker_won=True)

        assert len(stolen) == 1
        assert stolen[0][0] == "ART_B"

    def test_no_retention_effect_allows_steal(self):
        """Without the effect, steal proceeds normally."""
        battle, attacker, defender = _make_battle()
        defender.artifacts = ["ART_C"]
        defender.artifact_acquired_at = {"ART_C": time.time()}

        svc = _make_svc(attacker, base_victory=1.0)

        stolen, *_ = _apply_artifact_steal(battle, svc, attacker_won=True)

        assert len(stolen) == 1

    def test_artifact_without_acquired_at_is_not_protected(self):
        """Artifact with no acquisition timestamp is not protected (legacy state)."""
        battle, attacker, defender = _make_battle()
        defender.artifacts = ["ART_D"]
        defender.artifact_acquired_at = {}  # no timestamp
        defender.effects["artifact_retention_time"] = 3600.0

        svc = _make_svc(attacker, base_victory=1.0)

        stolen, *_ = _apply_artifact_steal(battle, svc, attacker_won=True)

        assert len(stolen) == 1, "Artifact without timestamp must not be protected"

    def test_multiple_artifacts_only_protected_one_blocked(self):
        """One artifact in window, one outside — only the expired one is stealable."""
        battle, attacker, defender = _make_battle()
        defender.artifacts = ["ART_NEW", "ART_OLD"]
        import datetime as _dt
        _now = _dt.datetime.now(_dt.timezone.utc)
        defender.artifact_acquired_at = {
            "ART_NEW": _now.isoformat(),                                      # just acquired — protected
            "ART_OLD": (_now - _dt.timedelta(hours=2)).isoformat(),           # 2h ago — stealable
        }
        defender.effects["artifact_retention_time"] = 3600.0

        svc = _make_svc(attacker, base_victory=1.0)

        stolen, *_ = _apply_artifact_steal(battle, svc, attacker_won=True)

        stolen_iids = [iid for iid, _ in stolen]
        assert "ART_NEW" not in stolen_iids
        assert "ART_OLD" in stolen_iids
