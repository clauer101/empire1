"""Tests for util/effects.py — verify constants are importable and correctly typed."""

import gameserver.util.effects as eff


class TestEffectsConstants:
    def test_all_values_are_strings(self):
        for name in dir(eff):
            if name.startswith("_"):
                continue
            val = getattr(eff, name)
            assert isinstance(val, str), f"{name} should be str, got {type(val)}"

    def test_no_duplicates(self):
        values = [
            getattr(eff, name)
            for name in dir(eff)
            if not name.startswith("_") and isinstance(getattr(eff, name), str)
        ]
        assert len(values) == len(set(values)), "Duplicate effect key values found"

    def test_key_constants_exist(self):
        assert eff.GOLD_MODIFIER == "gold_modifier"
        assert eff.BUILD_SPEED_MODIFIER == "build_speed_modifier"
        assert eff.DAMAGE_MODIFIER == "damage_modifier"
        assert eff.TRAVEL_TIME_OFFSET == "travel_offset"
        assert eff.CAPTURE_GOLD == "capture_gold"
