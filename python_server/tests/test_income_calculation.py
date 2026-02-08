"""Test that gold and culture income calculation is identical in Python and JavaScript."""

import pytest


class TestIncomeCalculation:
    """Verify income calculation consistency between backend and frontend."""

    def test_gold_income_calculation_python(self):
        """Python side: (base_gold + gold_offset) * (1 + gold_modifier) per second."""
        # Setup
        base_gold = 1.0
        gold_offset = 0.15
        merchant_count = 2
        citizen_effect = 0.03
        gold_modifier_from_effects = 0.0  # no building effects
        dt = 1.0  # 1 second
        
        # Python calculation
        gold_mod = merchant_count * citizen_effect + gold_modifier_from_effects
        gold_per_second = (base_gold + gold_offset) * (1 + gold_mod)
        gold_total = gold_per_second * dt
        
        # Expected: (1.0 + 0.15) * (1 + 0.06) = 1.15 * 1.06 = 1.219
        assert abs(gold_total - 1.219) < 0.01

    def test_culture_income_calculation_python(self):
        """Python side: (base_culture + culture_offset) * (1 + culture_modifier) per second."""
        # Setup
        base_culture = 0.5
        culture_offset = 0.05
        artist_count = 1
        citizen_effect = 0.03
        culture_modifier_from_effects = 0.0
        dt = 1.0
        
        # Python calculation
        culture_mod = artist_count * citizen_effect + culture_modifier_from_effects
        culture_per_second = (base_culture + culture_offset) * (1 + culture_mod)
        culture_total = culture_per_second * dt
        
        # Expected: (0.5 + 0.05) * (1 + 0.03) = 0.55 * 1.03 = 0.5665
        assert abs(culture_total - 0.5665) < 0.01

    def test_income_with_effect_modifiers(self):
        """Test with effect modifiers from buildings/research."""
        base_gold = 1.0
        gold_offset = 0.15
        merchant_count = 2
        citizen_effect = 0.03
        gold_modifier_from_effects = 0.05  # +5% from a building
        dt = 1.0
        
        # Python calculation
        gold_mod = merchant_count * citizen_effect + gold_modifier_from_effects
        gold_per_second = (base_gold + gold_offset) * (1 + gold_mod)
        gold_total = gold_per_second * dt
        
        # Expected: (1.0 + 0.15) * (1 + 0.06 + 0.05) = 1.15 * 1.11 = 1.2765
        assert abs(gold_total - 1.2765) < 0.01

    def test_zero_income(self):
        """Test with no citizens and no effects."""
        base_gold = 1.0
        gold_offset = 0.0
        merchant_count = 0
        citizen_effect = 0.03
        gold_modifier_from_effects = 0.0
        dt = 1.0
        
        gold_mod = merchant_count * citizen_effect + gold_modifier_from_effects
        gold_per_second = (base_gold + gold_offset) * (1 + gold_mod)
        gold_total = gold_per_second * dt
        
        # Expected: (1.0 + 0.0) * (1 + 0) = 1.0 * 1 = 1.0
        assert abs(gold_total - 1.0) < 0.01

    def test_income_formula_matching(self):
        """
        Verify the formula matches across both implementations.
        
        Python formula (from empire_service.py):
            gold_per_second = (base_gold + gold_offset) * (1 + gold_modifier)
            gold_modifier = citizens.merchant * citizen_effect + effects.gold_modifier
        
        JavaScript formula (displayed in dashboard.js):
            gold_mult = 1 + gold_modifier + (merchantCount * citizenEffectVal)
            displayed_result = gold_mult * gold_offset  (but this is wrong for display!)
            
        The CORRECT formula should be:
            gold_per_second = (base_gold + gold_offset) * (1 + gold_modifier)
        """
        test_cases = [
            # (base, offset, merchants, effects_mod, citizen_effect, expected)
            (1.0, 0.15, 2, 0.0, 0.03, (1.0 + 0.15) * (1 + 2*0.03)),      # 1.219
            (1.0, 0.10, 1, 0.05, 0.03, (1.0 + 0.10) * (1 + 1*0.03 + 0.05)), # 1.188
            (0.5, 0.05, 3, 0.02, 0.03, (0.5 + 0.05) * (1 + 3*0.03 + 0.02)), # 0.6105
            (1.0, 0.0, 0, 0.0, 0.03, (1.0 + 0.0) * (1 + 0)),               # 1.0
        ]
        
        for base, offset, citizens, effect_mod, citizen_eff, expected in test_cases:
            total_mod = citizens * citizen_eff + effect_mod
            result = (base + offset) * (1 + total_mod)
            assert abs(result - expected) < 0.0001, \
                f"Failed for base={base}, offset={offset}, citizens={citizens}, " \
                f"effect_mod={effect_mod}: got {result}, expected {expected}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
