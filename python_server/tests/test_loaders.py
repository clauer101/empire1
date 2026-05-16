"""Tests for loaders that had low/zero coverage:
- loaders/map_loader.py
- loaders/ai_loader.py
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from gameserver.loaders.ai_loader import load_ai_templates, load_ai_waves
from gameserver.loaders.map_loader import load_map, load_map_from_tiles
from gameserver.models.hex import HexCoord


# ---------------------------------------------------------------------------
# map_loader
# ---------------------------------------------------------------------------

_SIMPLE_TILES = {
    "0,0": "castle",
    "1,0": "path",
    "2,0": "path",
    "3,0": "spawnpoint",
    "0,1": "build",
    "0,2": "build",
}


class TestLoadMapFromTiles:
    def test_build_tiles_extracted(self):
        hm = load_map_from_tiles(_SIMPLE_TILES)
        assert HexCoord(0, 1) in hm.build_tiles
        assert HexCoord(0, 2) in hm.build_tiles

    def test_non_build_tiles_not_in_build_tiles(self):
        hm = load_map_from_tiles(_SIMPLE_TILES)
        assert HexCoord(0, 0) not in hm.build_tiles
        assert HexCoord(1, 0) not in hm.build_tiles

    def test_critter_path_computed(self):
        hm = load_map_from_tiles(_SIMPLE_TILES)
        assert len(hm.critter_path) > 0

    def test_empty_tiles_no_path(self):
        hm = load_map_from_tiles({})
        assert hm.critter_path == []
        assert len(hm.build_tiles) == 0


class TestLoadMapNewFormat:
    def test_loads_from_yaml_new_format(self, tmp_path: Path):
        data = {"tiles": _SIMPLE_TILES}
        f = tmp_path / "map.yaml"
        f.write_text(yaml.dump(data))
        hm = load_map(f)
        assert HexCoord(0, 1) in hm.build_tiles

    def test_loads_from_yaml_old_format(self, tmp_path: Path):
        data = {
            "build_tiles": [[0, 1], [0, 2]],
        }
        f = tmp_path / "map_old.yaml"
        f.write_text(yaml.dump(data))
        hm = load_map(f)
        assert HexCoord(0, 1) in hm.build_tiles
        assert HexCoord(0, 2) in hm.build_tiles

    def test_empty_yaml_returns_empty_map(self, tmp_path: Path):
        f = tmp_path / "empty.yaml"
        f.write_text("")
        hm = load_map(f)
        assert hm.build_tiles == set()

    def test_loads_real_default_map(self):
        """Smoke test: the actual default map loads without error."""
        real_map = Path(__file__).parent.parent / "config" / "maps" / "default.yaml"
        if not real_map.exists():
            pytest.skip("default.yaml not found")
        hm = load_map(real_map)
        # Should have some build tiles and a critter path
        assert len(hm.build_tiles) > 0 or len(hm.critter_path) > 0


# ---------------------------------------------------------------------------
# ai_loader
# ---------------------------------------------------------------------------

class TestLoadAiTemplates:
    def test_nonexistent_file_returns_empty(self, tmp_path: Path):
        result = load_ai_templates(tmp_path / "nonexistent.yaml")
        assert result == {}

    def test_loads_real_file_if_present(self):
        real = Path(__file__).parent.parent / "config" / "ai_templates.yaml"
        result = load_ai_templates(real)
        # Returns dict regardless of whether the file exists
        assert isinstance(result, dict)

    def test_custom_yaml(self, tmp_path: Path):
        f = tmp_path / "ai_tpl.yaml"
        f.write_text("difficulty_tiers:\n  easy: 1\ntemplates:\n  goblin: {}\n")
        result = load_ai_templates(f)
        assert result.get("difficulty_tiers") == {"easy": 1}
        assert "goblin" in result.get("templates", {})


class TestLoadAiWaves:
    def test_nonexistent_file_returns_empty_list(self, tmp_path: Path):
        result = load_ai_waves(tmp_path / "none.yaml")
        assert result == []

    def test_loads_real_ai_waves(self):
        real = Path(__file__).parent.parent / "config" / "ai_waves.yaml"
        if not real.exists():
            pytest.skip("ai_waves.yaml not found")
        result = load_ai_waves(real)
        assert isinstance(result, list)
        assert len(result) > 0

    def test_custom_waves_yaml(self, tmp_path: Path):
        data = {"armies": [{"name": "TestArmy", "waves": []}]}
        f = tmp_path / "waves.yaml"
        f.write_text(yaml.dump(data))
        result = load_ai_waves(f)
        assert len(result) == 1
        assert result[0]["name"] == "TestArmy"

    def test_yaml_without_armies_key_returns_empty(self, tmp_path: Path):
        f = tmp_path / "no_armies.yaml"
        f.write_text("something_else: []\n")
        result = load_ai_waves(f)
        assert result == []
