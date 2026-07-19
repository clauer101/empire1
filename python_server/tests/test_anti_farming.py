"""Tests for the anti-farming protection (repeated PvP wins vs. same defender).

Covers all four pieces:
1. persistence/database.py — count_recent_attacker_wins / record_attacker_win
2. handlers/battle_task.py — _compute_and_apply_loot culture reduction
3. handlers/battle_task.py — _award_ruler_xp skips penalized uids
4. engine/battle_service.py — live 3x defender gold on critter kill
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from gameserver.network.handlers.battle_task import _award_ruler_xp, _compute_and_apply_loot
from gameserver.persistence.database import Database


# ── 1. DB rolling-window win count ──────────────────────────────────────────


@pytest.fixture
async def db() -> Database:
    database = Database(":memory:")
    await database.connect()
    yield database
    await database.close()


class TestAttackerWinLog:
    async def test_counts_recent_wins(self, db: Database):
        now = 1_000_000
        for i in range(4):
            await db.record_attacker_win(1, 2, now + i)
        count = await db.count_recent_attacker_wins(1, 2, now - 100)
        assert count == 4

    async def test_wins_outside_window_not_counted(self, db: Database):
        now = 1_000_000
        await db.record_attacker_win(1, 2, now - 200)  # old, outside window
        await db.record_attacker_win(1, 2, now)  # recent
        count = await db.count_recent_attacker_wins(1, 2, since_ts=now - 100)
        assert count == 1

    async def test_different_defender_not_counted(self, db: Database):
        now = 1_000_000
        await db.record_attacker_win(1, 2, now)
        await db.record_attacker_win(1, 3, now)  # different defender
        count = await db.count_recent_attacker_wins(1, 2, since_ts=now - 100)
        assert count == 1

    async def test_record_prunes_old_rows_for_pair(self, db: Database):
        now = 1_000_000
        await db.record_attacker_win(1, 2, now - 200_000)  # older than 48h prune window
        await db.record_attacker_win(1, 2, now)
        assert db._conn is not None
        async with db._conn.execute(
            "SELECT COUNT(*) FROM attacker_win_log WHERE attacker_uid=1 AND defender_uid=2",
        ) as cur:
            row = await cur.fetchone()
        assert row[0] == 1  # the stale row was pruned by the second call


class TestGetActiveAntiFarmPairs:
    """Covers the DB read used by /api/admin/anti-farm/active."""

    async def test_pair_at_threshold_is_active(self, db: Database):
        now = 1_000_000
        for i in range(4):
            await db.record_attacker_win(1, 2, now + i)

        pairs = await db.get_active_anti_farm_pairs(since_ts=now - 100, threshold=4)

        assert len(pairs) == 1
        assert pairs[0] == {
            "attacker_uid": 1, "defender_uid": 2, "win_count": 4, "last_win_ts": now + 3,
        }

    async def test_pair_below_threshold_is_not_active(self, db: Database):
        now = 1_000_000
        for i in range(3):
            await db.record_attacker_win(1, 2, now + i)

        pairs = await db.get_active_anti_farm_pairs(since_ts=now - 100, threshold=4)

        assert pairs == []

    async def test_multiple_pairs_ordered_by_win_count_desc(self, db: Database):
        now = 1_000_000
        for i in range(4):
            await db.record_attacker_win(1, 2, now + i)
        for i in range(6):
            await db.record_attacker_win(3, 2, now + i)

        pairs = await db.get_active_anti_farm_pairs(since_ts=now - 100, threshold=4)

        assert [p["attacker_uid"] for p in pairs] == [3, 1]
        assert [p["win_count"] for p in pairs] == [6, 4]


class TestGetAttackerWinMessages:
    """Covers the DB read used by the /api/admin/anti-farm/backfill endpoint."""

    async def test_returns_only_you_won_system_messages(self, db: Database):
        await db.send_message(0, 5, "⚔ You Won!\n🛡 Defender:  Caelum et Terra\n")
        await db.send_message(0, 5, "⚔ You Lost!\n🛡 Defender:  Caelum et Terra\n")  # wrong outcome
        await db.send_message(7, 5, "⚔ You Won!\n🛡 Defender:  Caelum et Terra\n")  # not from system

        rows = await db.get_attacker_win_messages("2000-01-01 00:00:00")

        assert len(rows) == 1
        assert rows[0]["to_uid"] == 5
        assert "Caelum et Terra" in rows[0]["body"]

    async def test_since_ts_filters_out_older_messages(self, db: Database):
        assert db._conn is not None
        await db._conn.execute(
            "INSERT INTO messages (from_uid, to_uid, body, read, sent_at) VALUES (0, 5, ?, 0, '2020-01-01 00:00:00')",
            ("⚔ You Won!\n🛡 Defender:  Old Empire\n",),
        )
        await db._conn.commit()
        await db.send_message(0, 5, "⚔ You Won!\n🛡 Defender:  New Empire\n")

        rows = await db.get_attacker_win_messages("2025-01-01 00:00:00")

        assert len(rows) == 1
        assert "New Empire" in rows[0]["body"]


# ── 2. Culture payout reduction ─────────────────────────────────────────────


def _empire(uid: int, era: str = "stone", culture: float = 0.0,
            life: float = 6.0, max_life: float = 10.0):
    return SimpleNamespace(
        uid=uid,
        resources={"culture": culture, "life": life},
        max_life=max_life,
        knowledge={},
        buildings={},
        artifacts=set(),
        effects={},
        research_queue=None,
        build_queue=None,
    )


def _svc(empires: dict, era_by_uid: dict, *, antifarm_mult: float = 0.33):
    cfg = SimpleNamespace(
        min_lose_culture=0.04,
        max_lose_culture=0.04,
        ai_culture_steal_modifier=0.33,
        culture_era_advantage_ratio=0.51,
        restore_life_after_loss_offset=1.0,
        anti_farm_culture_multiplier=antifarm_mult,
    )
    empire_service = SimpleNamespace(
        get=lambda uid: empires.get(uid),
        get_current_era=lambda emp: era_by_uid[emp.uid],
    )
    return SimpleNamespace(
        game_config=cfg,
        empire_service=empire_service,
        upgrade_provider=SimpleNamespace(items={}, check_requirements=lambda *_: True),
    )


def _battle(defender, attacker_uids, life_lost: float = 10.0):
    return SimpleNamespace(
        defender=defender,
        attacker_uids=attacker_uids,
        attacker_gains={},
        defender_losses={"life": life_lost},
        defender_won=False,
        critters_reached=int(life_lost > 0),
    )


class TestAntiFarmCulturePenalty:
    def test_penalized_attacker_gets_reduced_culture(self):
        defender = _empire(99, era="stone", culture=10_000.0)
        attacker = _empire(1, era="stone", culture=0.0)
        svc = _svc({99: defender, 1: attacker}, {99: "stone", 1: "stone"})
        battle = _battle(defender, [1])

        loot = _compute_and_apply_loot(battle, svc, penalized_uids=set())
        unpenalized_payout = loot["per_attacker"][1]["culture"]

        # Same setup, but this time the attacker is penalized.
        defender2 = _empire(99, era="stone", culture=10_000.0)
        attacker2 = _empire(1, era="stone", culture=0.0)
        svc2 = _svc({99: defender2, 1: attacker2}, {99: "stone", 1: "stone"})
        battle2 = _battle(defender2, [1])
        loot2 = _compute_and_apply_loot(battle2, svc2, penalized_uids={1})
        penalized_payout = loot2["per_attacker"][1]["culture"]

        assert penalized_payout == pytest.approx(unpenalized_payout * 0.33, rel=1e-3)
        assert loot2["per_attacker"][1]["antifarm_penalty"] is True

    def test_unpenalized_attacker_has_no_flag(self):
        defender = _empire(99, era="stone", culture=10_000.0)
        attacker = _empire(1, era="stone", culture=0.0)
        svc = _svc({99: defender, 1: attacker}, {99: "stone", 1: "stone"})
        battle = _battle(defender, [1])

        loot = _compute_and_apply_loot(battle, svc, penalized_uids=set())
        assert "antifarm_penalty" not in loot["per_attacker"][1]


# ── 3. Ruler XP skipped for penalized uids ──────────────────────────────────


class TestAntiFarmRulerXp:
    def _make_empire(self):
        ruler = SimpleNamespace(type="MAJA", xp=0.0, name="Maja Soulstone")
        return SimpleNamespace(uid=1, ruler=ruler)

    def _make_battle(self):
        army = SimpleNamespace(uid=1, waves=[SimpleNamespace(iid="MAJA")])
        return SimpleNamespace(
            armies={1: army}, defender=SimpleNamespace(uid=99),
            kills_era_xp_sum=5.0, critters_reached_slots=0,
        )

    def _make_svc(self, empire):
        cfg = SimpleNamespace(
            ruler_xp_per_kill=1.0, ruler_xp_per_reached_per_era=10.0, ruler_xp_victory_per_era=50.0,
        )
        empire_service = SimpleNamespace(
            get=lambda uid: empire if uid == empire.uid else None,
            get_current_era=lambda _emp: "stone",
            _ERA_ORDER=["stone"],
            ruler_level_from_xp=lambda xp: 1,
            recalculate_effects=lambda _emp: None,
        )
        return SimpleNamespace(game_config=cfg, empire_service=empire_service)

    def test_penalized_uid_gets_no_xp(self):
        empire = self._make_empire()
        battle = self._make_battle()
        svc = self._make_svc(empire)

        gained, _ = _award_ruler_xp(battle, svc, attacker_won=True, penalized_uids={1})

        assert 1 not in gained
        assert empire.ruler.xp == 0.0

    def test_unpenalized_uid_still_gets_xp(self):
        empire = self._make_empire()
        battle = self._make_battle()
        svc = self._make_svc(empire)

        gained, _ = _award_ruler_xp(battle, svc, attacker_won=True, penalized_uids=set())

        assert 1 in gained
        assert empire.ruler.xp > 0.0


# ── 4. Live 3x defender gold on critter kill ────────────────────────────────


class TestAntiFarmDefenderGoldBonus:
    def test_gold_tripled_when_attacker_is_farming(self):
        from gameserver.engine.battle_service import BattleService
        from gameserver.models.battle import BattleState
        from gameserver.models.critter import Critter

        defender = SimpleNamespace(resources={"gold": 0.0})
        battle = BattleState(
            bid=1, defender=defender, attacker_uids=[7],
            farming_attacker_uids={7},
        )
        critter = Critter(cid=1, iid="WARRIOR", value=10.0, path=[], path_progress=0.0)
        battle.critters[critter.cid] = critter

        svc = BattleService(items={})
        svc._critter_died(battle, critter)

        assert defender.resources["gold"] == pytest.approx(30.0)
        assert battle.defender_gold_earned == pytest.approx(30.0)

    def test_gold_not_tripled_when_not_farming(self):
        from gameserver.engine.battle_service import BattleService
        from gameserver.models.battle import BattleState
        from gameserver.models.critter import Critter

        defender = SimpleNamespace(resources={"gold": 0.0})
        battle = BattleState(bid=1, defender=defender, attacker_uids=[7])
        critter = Critter(cid=1, iid="WARRIOR", value=10.0, path=[], path_progress=0.0)
        battle.critters[critter.cid] = critter

        svc = BattleService(items={})
        svc._critter_died(battle, critter)

        assert defender.resources["gold"] == pytest.approx(10.0)
        assert battle.defender_gold_earned == pytest.approx(10.0)
