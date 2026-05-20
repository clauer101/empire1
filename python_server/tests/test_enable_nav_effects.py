"""Unit tests for enable_* binary effects that unlock nav views."""

from gameserver.models.empire import Empire


ENABLE_EFFECTS = ["enable_army", "enable_techtree", "enable_workshop", "enable_messages"]


class TestEnableNavEffectsModel:
    def test_effects_not_set_by_default(self):
        empire = Empire(uid=1, name="Test")
        for key in ENABLE_EFFECTS:
            assert empire.effects.get(key, 0) == 0

    def test_set_effect_positive(self):
        empire = Empire(uid=1, name="Test")
        for key in ENABLE_EFFECTS:
            empire.effects[key] = 1.0
            assert empire.effects[key] > 0

    def test_zero_value_not_unlocked(self):
        empire = Empire(uid=1, name="Test")
        for key in ENABLE_EFFECTS:
            empire.effects[key] = 0.0
            assert not (empire.effects.get(key, 0) > 0)

    def test_get_effect_helper(self):
        empire = Empire(uid=1, name="Test")
        for key in ENABLE_EFFECTS:
            assert empire.get_effect(key) == 0.0
            empire.effects[key] = 1.0
            assert empire.get_effect(key) == 1.0

    def test_all_four_effects_independent(self):
        empire = Empire(uid=1, name="Test")
        empire.effects["enable_army"] = 1.0
        assert empire.get_effect("enable_army") > 0
        assert empire.get_effect("enable_techtree") == 0.0
        assert empire.get_effect("enable_workshop") == 0.0
        assert empire.get_effect("enable_messages") == 0.0
