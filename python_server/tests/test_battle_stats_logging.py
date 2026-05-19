"""Tests for post-battle stats logging in battle_task._run_battle_task.

Extracts the stats-logging block into a helper and verifies that the correct
database methods are called with the correct arguments for each battle outcome.

Regression: battle.defender_uid does not exist on BattleState — the correct
attribute is battle.defender.uid. These tests would have caught that crash.
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

from gameserver.engine.ai_service import AI_UID
from gameserver.models.battle import BattleState
from gameserver.models.empire import Empire


# ── Helpers ──────────────────────────────────────────────────────────────────

def _empire(uid: int, name: str = "") -> Empire:
    e = Empire(uid=uid, name=name or f"Empire{uid}")
    return e


def _battle(
    defender: Empire,
    attacker_uids: list[int],
    defender_won: bool,
    elapsed_ms: float = 10_000.0,
    critters_killed: int = 0,
    defender_gold_earned: float = 0.0,
) -> BattleState:
    return BattleState(
        bid=1,
        defender=defender,
        attacker_uids=attacker_uids,
        defender_won=defender_won,
        elapsed_ms=elapsed_ms,
        critters_killed=critters_killed,
        defender_gold_earned=defender_gold_earned,
    )


def _mock_db() -> MagicMock:
    db = MagicMock()
    db.record_empire_stat = AsyncMock()
    db.record_empire_stat_max = AsyncMock()
    db.record_empire_stat_float = AsyncMock()
    db.record_artifact_acquired = AsyncMock()
    db.record_artifact_lost = AsyncMock()
    return db


async def _run_stats(battle: BattleState, db: MagicMock, loot: dict | None = None,
                     stolen_artifacts: list[tuple[str, int]] | None = None) -> None:
    from gameserver.network.handlers.battle_task import _log_battle_stats
    await _log_battle_stats(battle, db, loot or {}, stolen_artifacts or [])


# ── Tests ─────────────────────────────────────────────────────────────────────

class TestBattleStatsLogging:
    """Verify stats are logged correctly for every battle outcome."""

    async def test_defender_wins_vs_human(self):
        defender = _empire(uid=10)
        attacker_uid = 20
        battle = _battle(defender, [attacker_uid], defender_won=True)
        db = _mock_db()

        await _run_stats(battle, db)

        db.record_empire_stat.assert_any_call(10, defense_won_human=1)
        db.record_empire_stat.assert_any_call(20, attacks_lost_human=1)
        # Must NOT log defense_won_ai or attacks_won_human
        calls_kwargs = [c.kwargs for c in db.record_empire_stat.call_args_list]
        assert not any("defense_won_ai" in kw for kw in calls_kwargs)
        assert not any("attacks_won_human" in kw for kw in calls_kwargs)

    async def test_defender_loses_vs_human(self):
        defender = _empire(uid=10)
        attacker_uid = 20
        battle = _battle(defender, [attacker_uid], defender_won=False)
        db = _mock_db()

        await _run_stats(battle, db)

        db.record_empire_stat.assert_any_call(10, defense_lost_human=1)
        db.record_empire_stat.assert_any_call(20, attacks_won_human=1)

    async def test_defender_wins_vs_ai(self):
        defender = _empire(uid=10)
        battle = _battle(defender, [AI_UID], defender_won=True)
        db = _mock_db()

        await _run_stats(battle, db)

        db.record_empire_stat.assert_any_call(10, defense_won_ai=1)
        # No attacker stats for AI
        uids_credited = [c.args[0] for c in db.record_empire_stat.call_args_list]
        assert AI_UID not in uids_credited

    async def test_defender_loses_vs_ai(self):
        defender = _empire(uid=10)
        battle = _battle(defender, [AI_UID], defender_won=False)
        db = _mock_db()

        await _run_stats(battle, db)

        db.record_empire_stat.assert_any_call(10, defense_lost_ai=1)
        uids_credited = [c.args[0] for c in db.record_empire_stat.call_args_list]
        assert AI_UID not in uids_credited

    async def test_longest_battle_recorded(self):
        defender = _empire(uid=5)
        battle = _battle(defender, [AI_UID], defender_won=True, elapsed_ms=42_000.0)
        db = _mock_db()

        await _run_stats(battle, db)

        db.record_empire_stat_max.assert_called_once_with(5, "longest_battle_ms", 42_000)

    async def test_critters_killed_logged(self):
        defender = _empire(uid=5)
        battle = _battle(defender, [AI_UID], defender_won=True, critters_killed=37)
        db = _mock_db()

        await _run_stats(battle, db)

        db.record_empire_stat.assert_any_call(5, critters_killed=37)

    async def test_critters_killed_zero_not_logged(self):
        defender = _empire(uid=5)
        battle = _battle(defender, [AI_UID], defender_won=True, critters_killed=0)
        db = _mock_db()

        await _run_stats(battle, db)

        kwarg_sets = [c.kwargs for c in db.record_empire_stat.call_args_list]
        assert not any("critters_killed" in kw for kw in kwarg_sets)

    async def test_defense_gold_earned_logged(self):
        defender = _empire(uid=5)
        battle = _battle(defender, [AI_UID], defender_won=True, defender_gold_earned=1234.5)
        db = _mock_db()

        await _run_stats(battle, db)

        db.record_empire_stat_float.assert_any_call(5, "defense_gold_earned", 1234.5)

    async def test_defense_gold_zero_not_logged(self):
        defender = _empire(uid=5)
        battle = _battle(defender, [AI_UID], defender_won=True, defender_gold_earned=0.0)
        db = _mock_db()

        await _run_stats(battle, db)

        field_names = [c.args[1] for c in db.record_empire_stat_float.call_args_list]
        assert "defense_gold_earned" not in field_names

    async def test_culture_stolen_logged_on_defender_loss(self):
        defender = _empire(uid=10)
        attacker_uid = 20
        battle = _battle(defender, [attacker_uid], defender_won=False)
        db = _mock_db()
        loot = {"culture": 500.0, "per_attacker": {20: {"culture": 400.0}}}

        await _run_stats(battle, db, loot=loot)

        db.record_empire_stat_float.assert_any_call(10, "culture_stolen", 500.0)
        db.record_empire_stat_float.assert_any_call(20, "culture_won", 400.0)

    async def test_culture_not_logged_when_defender_wins(self):
        defender = _empire(uid=10)
        battle = _battle(defender, [20], defender_won=True)
        db = _mock_db()
        loot = {"culture": 500.0}

        await _run_stats(battle, db, loot=loot)

        field_names = [c.args[1] for c in db.record_empire_stat_float.call_args_list]
        assert "culture_stolen" not in field_names

    async def test_research_stolen_logged(self):
        defender = _empire(uid=10)
        attacker_uid = 20
        battle = _battle(defender, [attacker_uid], defender_won=False)
        db = _mock_db()
        loot = {
            "culture": 0.0,
            "knowledge": {"iid": "iron", "amount": 250.0, "per_winner": 250.0},
            "per_attacker": {20: {}},
        }

        await _run_stats(battle, db, loot=loot)

        db.record_empire_stat_float.assert_any_call(10, "research_stolen", 250.0)
        db.record_empire_stat_float.assert_any_call(20, "research_won", 250.0)

    async def test_artifact_stolen_logged(self):
        defender = _empire(uid=10)
        winner_uid = 20
        battle = _battle(defender, [winner_uid], defender_won=False)
        db = _mock_db()

        with patch("time.time", return_value=1_000_000.0):
            await _run_stats(battle, db, stolen_artifacts=[("goblet", winner_uid)])

        db.record_empire_stat.assert_any_call(20, artifacts_stolen=1)
        db.record_artifact_acquired.assert_called_once_with(20, "goblet", 1_000_000.0)
        db.record_artifact_lost.assert_called_once_with(10, "goblet", 1_000_000.0)

    async def test_multiple_artifacts_stolen_all_logged(self):
        defender = _empire(uid=10)
        winner_uid = 20
        battle = _battle(defender, [winner_uid], defender_won=False)
        db = _mock_db()

        with patch("time.time", return_value=1_000_000.0):
            await _run_stats(battle, db, stolen_artifacts=[("goblet", winner_uid), ("crown", winner_uid)])

        # artifacts_stolen incremented once per transfer
        stolen_calls = [c for c in db.record_empire_stat.call_args_list if "artifacts_stolen" in c.kwargs]
        assert len(stolen_calls) == 2
        # acquired and lost called for each artifact
        assert db.record_artifact_acquired.call_count == 2
        assert db.record_artifact_lost.call_count == 2
        db.record_artifact_acquired.assert_any_call(20, "goblet", 1_000_000.0)
        db.record_artifact_acquired.assert_any_call(20, "crown", 1_000_000.0)
        db.record_artifact_lost.assert_any_call(10, "goblet", 1_000_000.0)
        db.record_artifact_lost.assert_any_call(10, "crown", 1_000_000.0)

    async def test_artifacts_stolen_by_different_attackers_all_logged(self):
        defender = _empire(uid=10)
        battle = _battle(defender, [20, 21], defender_won=False)
        db = _mock_db()

        with patch("time.time", return_value=1_000_000.0):
            await _run_stats(battle, db, stolen_artifacts=[("goblet", 20), ("crown", 21)])

        db.record_empire_stat.assert_any_call(20, artifacts_stolen=1)
        db.record_empire_stat.assert_any_call(21, artifacts_stolen=1)
        db.record_artifact_acquired.assert_any_call(20, "goblet", 1_000_000.0)
        db.record_artifact_acquired.assert_any_call(21, "crown", 1_000_000.0)

    async def test_no_stolen_artifacts_nothing_logged(self):
        defender = _empire(uid=10)
        battle = _battle(defender, [20], defender_won=False)
        db = _mock_db()

        await _run_stats(battle, db, stolen_artifacts=[])

        db.record_artifact_acquired.assert_not_called()
        db.record_artifact_lost.assert_not_called()
        kwarg_sets = [c.kwargs for c in db.record_empire_stat.call_args_list]
        assert not any("artifacts_stolen" in kw for kw in kwarg_sets)

    async def test_uses_defender_dot_uid_not_nonexistent_defender_uid(self):
        """Regression: BattleState has no .defender_uid — must use .defender.uid."""
        defender = _empire(uid=99)
        battle = _battle(defender, [AI_UID], defender_won=True)
        db = _mock_db()

        # Must not raise AttributeError
        await _run_stats(battle, db)

        uids = [c.args[0] for c in db.record_empire_stat.call_args_list]
        assert 99 in uids

    async def test_no_crash_when_defender_is_none(self):
        """Stats logging must not crash if defender is None."""
        battle = BattleState(bid=1, defender=None, attacker_uids=[AI_UID], defender_won=True)
        db = _mock_db()

        await _run_stats(battle, db)  # must not raise

    async def test_multiple_human_attackers(self):
        defender = _empire(uid=10)
        battle = _battle(defender, [20, 21], defender_won=False)
        db = _mock_db()

        await _run_stats(battle, db)

        db.record_empire_stat.assert_any_call(20, attacks_won_human=1)
        db.record_empire_stat.assert_any_call(21, attacks_won_human=1)
