"""Tests for game.yaml completeness — guards against accidental config loss."""

from pathlib import Path

import pytest
import yaml

from gameserver.loaders.game_config_loader import load_game_config

CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"
GAME_YAML = str(CONFIG_DIR / "game.yaml")
NUM_ERAS = 9  # Stone → Future


class TestGameConfigLoads:
    @pytest.fixture(scope="class")
    def gc(self):
        return load_game_config(GAME_YAML)

    def test_loads_without_error(self, gc):
        assert gc is not None

    def test_wave_era_costs_all_eras_present(self, gc):
        costs = gc.prices.wave_era_costs
        assert len(costs) == NUM_ERAS, (
            f"wave_era_costs has {len(costs)} entries, expected {NUM_ERAS}. "
            "Likely a game.yaml edit dropped entries."
        )

    def test_wave_era_costs_increase_monotonically(self, gc):
        costs = gc.prices.wave_era_costs
        for i in range(1, len(costs)):
            assert costs[i] >= costs[i - 1], (
                f"wave_era_costs not monotonically increasing at index {i}: "
                f"{costs[i-1]} → {costs[i]}"
            )

    def test_wave_era_costs_first_is_free(self, gc):
        assert gc.prices.wave_era_costs[0] == 0, "First era should be free (cost 0)"

    def test_ruler_xp_prices_defined(self, gc):
        p = gc.prices.ruler_xp
        assert p.y > 0, "ruler_xp price params missing or zero"

    def test_item_upgrade_base_costs_all_eras(self, gc):
        costs = gc.item_upgrade_base_costs
        assert len(costs) == NUM_ERAS, (
            f"item_upgrade_base_costs has {len(costs)} entries, expected {NUM_ERAS}"
        )

    def test_starting_resources_defined(self, gc):
        assert "gold" in gc.starting_resources
        assert "life" in gc.starting_resources

    def test_ruler_xp_rewards_defined(self, gc):
        assert gc.ruler_xp_per_kill > 0
        assert gc.ruler_xp_per_reached_per_era > 0
        assert gc.ruler_xp_victory_per_era > 0


class TestGameConfigStrictValidation:
    """Missing required keys must crash the server at startup, not silently use defaults."""

    _REQUIRED_SCALAR_KEYS = [
        "base_gold_per_sec",
        "base_culture_per_sec",
        "citizen_effect",
        "base_build_speed",
        "base_research_speed",
        "starting_max_life",
        "restore_life_after_loss_offset",
        "min_lose_knowledge",
        "max_lose_knowledge",
        "min_lose_culture",
        "max_lose_culture",
        "culture_era_advantage_ratio",
        "base_artifact_steal_victory",
        "base_artifact_steal_defeat",
        "ruler_xp_per_kill",
        "ruler_xp_per_reached_per_era",
        "ruler_xp_victory_per_era",
        "item_upgrade_base_costs",
        "end_criterion",
    ]

    _REQUIRED_SECTIONS = [
        "spy_costs",
        "prices",
        "era_effects",
        "structure_upgrades",
        "critter_upgrades",
        "end_ralley_effects",
    ]

    @pytest.fixture(scope="class")
    def base_data(self):
        with open(CONFIG_DIR / "game.yaml") as f:
            return yaml.safe_load(f)

    def _write_and_load(self, tmp_path, data):
        p = tmp_path / "game.yaml"
        p.write_text(yaml.dump(data))
        return load_game_config(str(p))

    @pytest.mark.parametrize("key", _REQUIRED_SCALAR_KEYS)
    def test_missing_scalar_key_raises(self, tmp_path, base_data, key):
        data = dict(base_data)
        data.pop(key, None)
        with pytest.raises((ValueError, KeyError, TypeError)):
            self._write_and_load(tmp_path, data)

    @pytest.mark.parametrize("section", _REQUIRED_SECTIONS)
    def test_missing_section_raises(self, tmp_path, base_data, section):
        data = dict(base_data)
        data.pop(section, None)
        with pytest.raises((ValueError, KeyError, TypeError)):
            self._write_and_load(tmp_path, data)
