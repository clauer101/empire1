"""Tests for item_loader — ensures config files load correctly."""

from pathlib import Path

import pytest

from gameserver.loaders.item_loader import load_items, _CATEGORIES
from gameserver.models.items import ItemDetails, ItemType

# Path to the real config directory
CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"


class TestLoadItemsFromConfigDir:
    """Verify that load_items() works with the split per-category YAML files."""

    def test_config_directory_exists(self):
        assert CONFIG_DIR.is_dir(), f"Config directory not found: {CONFIG_DIR}"

    @pytest.mark.parametrize("category", ["buildings", "knowledge", "structures", "critters", "artefacts"])
    def test_category_file_exists(self, category):
        f = CONFIG_DIR / f"{category}.yaml"
        assert f.exists(), f"Missing config file: {f}"

    def test_load_returns_items(self):
        items = load_items(CONFIG_DIR)
        assert len(items) > 0, "No items loaded from config directory"

    def test_all_items_are_item_details(self):
        items = load_items(CONFIG_DIR)
        for item in items:
            assert isinstance(item, ItemDetails)

    def test_expected_categories_present(self):
        items = load_items(CONFIG_DIR)
        types_found = {item.item_type for item in items}
        for expected in (ItemType.BUILDING, ItemType.KNOWLEDGE, ItemType.STRUCTURE, ItemType.CRITTER, ItemType.ARTEFACT):
            assert expected in types_found, f"No items of type {expected} loaded"

    def test_expected_item_counts(self):
        """Smoke test: each category should have a plausible number of items."""
        items = load_items(CONFIG_DIR)
        by_type = {}
        for item in items:
            by_type.setdefault(item.item_type, []).append(item)

        assert len(by_type[ItemType.BUILDING]) >= 80
        assert len(by_type[ItemType.KNOWLEDGE]) >= 50
        assert len(by_type[ItemType.STRUCTURE]) >= 15
        assert len(by_type[ItemType.CRITTER]) >= 20
        assert len(by_type[ItemType.ARTEFACT]) >= 10

    def test_items_have_iid_and_name(self):
        items = load_items(CONFIG_DIR)
        for item in items:
            assert item.iid, f"Item missing iid: {item}"
            assert item.name, f"Item missing name: {item}"

    def test_buildings_have_effort(self):
        items = load_items(CONFIG_DIR)
        buildings = [i for i in items if i.item_type == ItemType.BUILDING]
        # INIT is a special start marker with no effort
        for b in buildings:
            if b.iid == "INIT":
                continue
            assert b.effort > 0, f"Building {b.iid} has no effort value"

    def test_knowledge_have_effort(self):
        items = load_items(CONFIG_DIR)
        knowledge = [i for i in items if i.item_type == ItemType.KNOWLEDGE]
        for k in knowledge:
            assert k.effort > 0, f"Knowledge {k.iid} has no effort value"


class TestLoadItemsFromSingleFile:
    """Verify legacy single-file mode still works."""

    def test_load_from_single_file(self, tmp_path):
        f = tmp_path / "items.yaml"
        f.write_text(
            "buildings:\n"
            "  hut:\n"
            "    name: Hut\n"
            "    effort: 100\n"
            "knowledge:\n"
            "  fire:\n"
            "    name: Fire\n"
            "    effort: 50\n"
        )
        items = load_items(f)
        assert len(items) == 2
        types = {i.item_type for i in items}
        assert ItemType.BUILDING in types
        assert ItemType.KNOWLEDGE in types

    def test_missing_file_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_items(tmp_path / "nonexistent.yaml")

    def test_empty_file(self, tmp_path):
        f = tmp_path / "items.yaml"
        f.write_text("")
        items = load_items(f)
        assert items == []


class TestLoadItemsFromDirectory:
    """Verify directory mode with synthetic files."""

    def test_load_from_directory(self, tmp_path):
        (tmp_path / "buildings.yaml").write_text(
            "hut:\n  name: Hut\n  effort: 100\n"
            "farm:\n  name: Farm\n  effort: 200\n"
        )
        (tmp_path / "critters.yaml").write_text(
            "wolf:\n  name: Wolf\n  health: 50\n  speed: 1.5\n"
        )
        items = load_items(tmp_path)
        assert len(items) == 3
        types = {i.item_type for i in items}
        assert types == {ItemType.BUILDING, ItemType.CRITTER}

    def test_empty_directory(self, tmp_path):
        items = load_items(tmp_path)
        assert items == []

    def test_partial_categories(self, tmp_path):
        """Only some category files present — should not error."""
        (tmp_path / "artefacts.yaml").write_text(
            "ring:\n  name: Ring of Power\n"
        )
        items = load_items(tmp_path)
        assert len(items) == 1
        assert items[0].item_type == ItemType.ARTEFACT
