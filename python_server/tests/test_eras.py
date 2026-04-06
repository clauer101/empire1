"""Tests for util/eras.py — era constants integrity."""

from gameserver.util.eras import (
    ERA_ORDER, ERA_TRAVEL_FIELD, ERA_YAML_TO_KEY,
    ERA_YAML_TO_FIELD, ERA_LABELS_DE, ERA_LABELS_EN,
)


class TestEraOrder:
    def test_nine_eras(self):
        assert len(ERA_ORDER) == 9

    def test_starts_with_steinzeit(self):
        assert ERA_ORDER[0] == "STEINZEIT"

    def test_ends_with_zukunft(self):
        assert ERA_ORDER[-1] == "ZUKUNFT"

    def test_no_duplicates(self):
        assert len(ERA_ORDER) == len(set(ERA_ORDER))


class TestEraMaps:
    def test_travel_field_covers_all_eras(self):
        assert set(ERA_TRAVEL_FIELD.keys()) == set(ERA_ORDER)

    def test_yaml_to_key_maps_to_valid_eras(self):
        for yaml_key, era_key in ERA_YAML_TO_KEY.items():
            assert era_key in ERA_ORDER, f"{yaml_key} maps to unknown era {era_key}"

    def test_yaml_to_key_covers_all_eras(self):
        assert set(ERA_YAML_TO_KEY.values()) == set(ERA_ORDER)

    def test_yaml_to_field_same_keys_as_yaml_to_key(self):
        assert set(ERA_YAML_TO_FIELD.keys()) == set(ERA_YAML_TO_KEY.keys())


class TestEraLabels:
    def test_de_covers_all_eras(self):
        assert set(ERA_LABELS_DE.keys()) == set(ERA_ORDER)

    def test_en_covers_all_eras(self):
        assert set(ERA_LABELS_EN.keys()) == set(ERA_ORDER)

    def test_labels_are_nonempty_strings(self):
        for era in ERA_ORDER:
            assert ERA_LABELS_DE[era].strip(), f"Empty DE label for {era}"
            assert ERA_LABELS_EN[era].strip(), f"Empty EN label for {era}"
