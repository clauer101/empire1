"""Tests for engine/ai_service.py — AI attack heuristics and adaptation."""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from gameserver.engine.ai_service import AIService, AIParams, AI_UID, _params_summary
from gameserver.engine.upgrade_provider import UpgradeProvider
from gameserver.loaders.game_config_loader import GameConfig
from gameserver.models.empire import Empire


# ── Helpers ──────────────────────────────────────────────────────────────────


def _make_upgrade_provider():
    """Load real items so critter pools are populated."""
    from pathlib import Path
    from gameserver.loaders.item_loader import load_items

    config = Path(__file__).resolve().parent.parent / "config"
    items = load_items(config)
    up = UpgradeProvider()
    up.load(items)
    return up


def _make_empire(**kw) -> Empire:
    defaults = dict(uid=1, name="Test")
    defaults.update(kw)
    e = Empire(**defaults)
    e.resources = {"gold": 5000.0, "culture": 1000.0}
    return e


# ── AIParams ─────────────────────────────────────────────────────────────────


class TestAIParams:
    def test_defaults(self):
        p = AIParams()
        assert p.power_multiplier == 1.0
        assert p.wave_count == 3
        assert p.win_rate_target == 0.50

    def test_custom_values(self):
        p = AIParams(power_multiplier=2.0, wave_count=5)
        assert p.power_multiplier == 2.0
        assert p.wave_count == 5


# ── _assess_player ───────────────────────────────────────────────────────────


class TestAssessPlayer:
    @pytest.fixture
    def ai(self):
        return AIService(_make_upgrade_provider(), game_config=GameConfig())

    def test_empty_empire_returns_min_score(self, ai):
        empire = _make_empire()
        empire.resources = {"gold": 0, "culture": 0}
        score = ai._assess_player(empire)
        assert score == ai._game_config.ai_min_player_score

    def test_completed_buildings_increase_score(self, ai):
        empire = _make_empire()
        empire.resources = {"gold": 0, "culture": 0}
        # Mark some buildings as complete (remaining = 0.0)
        empire.buildings["BASE_CAMP"] = 0.0
        empire.buildings["FIRE_PLACE"] = 0.0
        score = ai._assess_player(empire)
        assert score >= ai._game_config.ai_min_player_score

    def test_culture_increases_score(self, ai):
        e1 = _make_empire()
        e1.resources = {"culture": 0}
        e2 = _make_empire()
        e2.resources = {"culture": 100_000}
        assert ai._assess_player(e2) > ai._assess_player(e1)

    def test_structure_tiles_increase_score(self, ai):
        e1 = _make_empire()
        e1.resources = {"culture": 0}
        e2 = _make_empire()
        e2.resources = {"culture": 0}
        e2.hex_map = {"0,0": "ARROW_TOWER", "1,0": "ARROW_TOWER", "2,0": "ARROW_TOWER"}
        assert ai._assess_player(e2) > ai._assess_player(e1)

    def test_incomplete_buildings_not_counted(self, ai):
        e1 = _make_empire()
        e1.resources = {"culture": 0}
        e2 = _make_empire()
        e2.resources = {"culture": 0}
        e2.buildings["BASE_CAMP"] = 50.0  # incomplete
        assert ai._assess_player(e1) == ai._assess_player(e2)


# ── on_battle_result / adaptation ────────────────────────────────────────────


class TestAdaptation:
    def test_ai_weakens_after_many_wins(self):
        ai = AIService(_make_upgrade_provider(), game_config=GameConfig())
        initial = ai._params.power_multiplier

        # Simulate 10 AI wins
        for i in range(10):
            attack_id = i + 1
            ai._pending[attack_id] = {"defender_uid": 1, "army_summary": {}}
            battle = MagicMock()
            battle.defender_won = False  # AI won
            battle.army = MagicMock()
            battle.army.waves = []
            ai.on_battle_result(attack_id, battle)

        assert ai._params.power_multiplier < initial

    def test_ai_strengthens_after_many_losses(self):
        ai = AIService(_make_upgrade_provider(), game_config=GameConfig())
        initial = ai._params.power_multiplier

        # Simulate 10 AI losses
        for i in range(10):
            attack_id = i + 1
            ai._pending[attack_id] = {"defender_uid": 1, "army_summary": {}}
            battle = MagicMock()
            battle.defender_won = True  # defender won
            battle.army = MagicMock()
            battle.army.waves = []
            ai.on_battle_result(attack_id, battle)

        assert ai._params.power_multiplier > initial

    def test_unknown_attack_id_ignored(self):
        ai = AIService(_make_upgrade_provider(), game_config=GameConfig())
        battle = MagicMock()
        battle.defender_won = True
        # No pending entry → should not crash
        ai.on_battle_result(999, battle)
        assert len(ai._history) == 0


# ── _build_army ──────────────────────────────────────────────────────────────


class TestBuildArmy:
    def test_generates_army_with_waves(self):
        up = _make_upgrade_provider()
        ai = AIService(up, game_config=GameConfig())
        empire = _make_empire()
        # Unlock some critters by completing prerequisites
        empire.buildings["BASE_CAMP"] = 0.0
        empire.buildings["FIRE_PLACE"] = 0.0

        result = ai._build_army(empire, player_power=2000.0)
        assert result is not None
        army, travel_s, siege_s = result
        assert len(army.waves) == ai._params.wave_count
        assert all(w.slots >= ai._params.min_slots_per_wave for w in army.waves)
        assert all(w.slots <= ai._params.max_slots_per_wave for w in army.waves)
        assert travel_s > 0

    def test_returns_none_without_critters(self):
        up = UpgradeProvider()  # empty, no items loaded
        ai = AIService(up, game_config=GameConfig())
        empire = _make_empire()
        result = ai._build_army(empire, player_power=1000.0)
        assert result is None


# ── get_difficulty_tier ──────────────────────────────────────────────────────


class TestDifficultyTier:
    def test_tiers(self):
        ai = AIService(_make_upgrade_provider())
        assert ai.get_difficulty_tier(100) == "easy"
        assert ai.get_difficulty_tier(1000) == "medium"
        assert ai.get_difficulty_tier(10_000) == "hard"
        assert ai.get_difficulty_tier(50_000) == "elite"

    def test_boundaries(self):
        ai = AIService(_make_upgrade_provider())
        assert ai.get_difficulty_tier(499) == "easy"
        assert ai.get_difficulty_tier(500) == "medium"
        assert ai.get_difficulty_tier(4999) == "medium"
        assert ai.get_difficulty_tier(5000) == "hard"
        assert ai.get_difficulty_tier(29999) == "hard"
        assert ai.get_difficulty_tier(30000) == "elite"


# ── _params_summary ──────────────────────────────────────────────────────────


class TestParamsSummary:
    def test_contains_key_values(self):
        p = AIParams(power_multiplier=1.5, armor_bias=0.3, speed_bias=0.2, wave_count=4)
        s = _params_summary(p)
        assert "1.500" in s
        assert "0.30" in s
        assert "0.20" in s
        assert "4" in s


# ── _match_waves_for_item ────────────────────────────────────────────────────


class TestMatchWaves:
    def test_matching_trigger(self):
        waves_config = [{
            "name": "test_wave",
            "trigger": {"items": ["FIRE_PLACE"]},
            "waves": [{"critter": "wolf", "slots": 5}],
            "travel_time": 10,
        }]
        ai = AIService(_make_upgrade_provider(), game_config=GameConfig(),
                        hardcoded_waves=waves_config)
        empire = _make_empire()
        results = ai._match_waves_for_item(empire, "FIRE_PLACE")
        assert len(results) == 1
        army, travel_s, siege_s = results[0]
        assert army.name == "test_wave"
        assert len(army.waves) == 1
        assert army.waves[0].iid == "WOLF"
        assert travel_s == 10.0

    def test_no_match(self):
        waves_config = [{
            "name": "test_wave",
            "trigger": {"items": ["SHRINE"]},
            "waves": [{"critter": "wolf", "slots": 5}],
        }]
        ai = AIService(_make_upgrade_provider(), game_config=GameConfig(),
                        hardcoded_waves=waves_config)
        empire = _make_empire()
        results = ai._match_waves_for_item(empire, "FIRE_PLACE")
        assert results == []

    def test_empty_hardcoded_waves(self):
        ai = AIService(_make_upgrade_provider(), game_config=GameConfig())
        empire = _make_empire()
        assert ai._match_waves_for_item(empire, "ANYTHING") == []
