"""Comprehensive tests for _calculate_siege_duration in AttackService.

Formula:
    result = max(1.0,
        (base + defender.siege_offset)
        * (1 - defender.siege_time_modifier)
        * (1 - attacker.enemy_siege_time_modifier)
    )

where:
  base               = base_override if given, else 0.0  (AI waves supply this)
  siege_offset       = flat seconds added by defender buildings/knowledge/rally
  siege_time_modifier = % reduction applied by defender (rally gives this to all)
  enemy_siege_time_modifier = % reduction applied by attacker (siege corruption)
"""

import pytest
from gameserver.engine.attack_service import AttackService
from gameserver.models.army import Army
from gameserver.models.attack import Attack, AttackPhase
from gameserver.engine.empire_service import EmpireService
from gameserver.engine.upgrade_provider import UpgradeProvider
from gameserver.loaders.game_config_loader import GameConfig
from gameserver.models.empire import Empire
from gameserver.util.events import EventBus
from gameserver.util import effects as fx


ATTACKER_UID = 1
DEFENDER_UID = 100


@pytest.fixture
def svc():
    event_bus = EventBus()
    upgrade_provider = UpgradeProvider()
    gc = GameConfig()
    empire_service = EmpireService(upgrade_provider, event_bus, gc)
    attack_service = AttackService(event_bus, gc, empire_service)
    attacker = Empire(uid=ATTACKER_UID, name="Attacker")
    defender = Empire(uid=DEFENDER_UID, name="Defender")
    empire_service.register(attacker)
    empire_service.register(defender)
    return attack_service, empire_service


def _calc(svc, base_override=None):
    attack_service, _ = svc
    return attack_service._calculate_siege_duration(ATTACKER_UID, DEFENDER_UID, base_override=base_override)


def _atk(svc) -> Empire:
    _, empire_service = svc
    return empire_service.get(ATTACKER_UID)


def _def(svc) -> Empire:
    _, empire_service = svc
    return empire_service.get(DEFENDER_UID)


# ── baseline ──────────────────────────────────────────────────────────────────

class TestBaseline:
    def test_no_effects_no_base_returns_minimum(self, svc):
        """With no base and no effects, result is clamped to 1.0."""
        assert _calc(svc) == 1.0

    def test_base_only_no_effects(self, svc):
        """base_override is used verbatim when no effects are set."""
        assert _calc(svc, base_override=300.0) == pytest.approx(300.0)

    def test_no_base_offset_only(self, svc):
        """siege_offset alone (no base_override) sets the siege time."""
        _def(svc).effects[fx.SIEGE_TIME_OFFSET] = 3600.0
        assert _calc(svc) == pytest.approx(3600.0)

    def test_base_plus_offset(self, svc):
        """base_override and siege_offset are summed before multipliers."""
        _def(svc).effects[fx.SIEGE_TIME_OFFSET] = 1000.0
        assert _calc(svc, base_override=500.0) == pytest.approx(1500.0)

    def test_missing_defender_falls_back_to_base(self, svc):
        attack_service, _ = svc
        result = attack_service._calculate_siege_duration(ATTACKER_UID, 9999, base_override=60.0)
        assert result == pytest.approx(60.0)

    def test_missing_attacker_skips_corruption(self, svc):
        """If attacker is not found, corruption defaults to 0 (no reduction)."""
        attack_service, empire_service = svc
        _def(svc).effects[fx.SIEGE_TIME_OFFSET] = 1000.0
        result = attack_service._calculate_siege_duration(9999, DEFENDER_UID)
        assert result == pytest.approx(1000.0)


# ── siege_offset (defender flat bonus) ───────────────────────────────────────

class TestSiegeOffset:
    def test_zero_offset(self, svc):
        _def(svc).effects[fx.SIEGE_TIME_OFFSET] = 0.0
        assert _calc(svc) == 1.0

    def test_large_offset(self, svc):
        _def(svc).effects[fx.SIEGE_TIME_OFFSET] = 23520.0
        assert _calc(svc) == pytest.approx(23520.0)

    def test_negative_offset_reduces_base(self, svc):
        """Negative offset shortens siege time (base 300 - 200 = 100)."""
        _def(svc).effects[fx.SIEGE_TIME_OFFSET] = -200.0
        assert _calc(svc, base_override=300.0) == pytest.approx(100.0)

    def test_negative_offset_clamped_to_minimum(self, svc):
        """Offset so negative that result < 1.0 is clamped to 1.0."""
        _def(svc).effects[fx.SIEGE_TIME_OFFSET] = -500.0
        assert _calc(svc, base_override=100.0) == 1.0


# ── siege_time_modifier (defender % reduction) ───────────────────────────────

class TestSiegeTimeModifier:
    def test_no_modifier(self, svc):
        _def(svc).effects[fx.SIEGE_TIME_OFFSET] = 1000.0
        assert _calc(svc) == pytest.approx(1000.0)

    def test_50_pct_modifier_halves(self, svc):
        _def(svc).effects[fx.SIEGE_TIME_OFFSET] = 1000.0
        _def(svc).effects[fx.SIEGE_TIME_MODIFIER] = 0.5
        assert _calc(svc) == pytest.approx(500.0)

    def test_25_pct_modifier(self, svc):
        _def(svc).effects[fx.SIEGE_TIME_OFFSET] = 2000.0
        _def(svc).effects[fx.SIEGE_TIME_MODIFIER] = 0.25
        assert _calc(svc) == pytest.approx(1500.0)

    def test_100_pct_modifier_clamps_to_minimum(self, svc):
        """Full modifier (1.0) reduces result to 0, clamped at 1.0."""
        _def(svc).effects[fx.SIEGE_TIME_OFFSET] = 23520.0
        _def(svc).effects[fx.SIEGE_TIME_MODIFIER] = 1.0
        assert _calc(svc) == 1.0

    def test_modifier_applies_to_base_plus_offset(self, svc):
        """Modifier applies after base and offset are summed."""
        _def(svc).effects[fx.SIEGE_TIME_OFFSET] = 500.0
        _def(svc).effects[fx.SIEGE_TIME_MODIFIER] = 0.5
        # (300 + 500) * 0.5 = 400
        assert _calc(svc, base_override=300.0) == pytest.approx(400.0)

    def test_rally_modifier_50_pct(self, svc):
        """Simulate rally effect: siege_time_modifier=0.5 added to defender."""
        _def(svc).effects[fx.SIEGE_TIME_OFFSET] = 23520.0
        _def(svc).effects[fx.SIEGE_TIME_MODIFIER] = 0.5
        # 23520 * 0.5 = 11760
        assert _calc(svc) == pytest.approx(11760.0)


# ── enemy_siege_time_modifier (attacker siege corruption) ────────────────────

class TestAttackerCorruption:
    def test_no_corruption(self, svc):
        _def(svc).effects[fx.SIEGE_TIME_OFFSET] = 1000.0
        assert _calc(svc) == pytest.approx(1000.0)

    def test_28_pct_corruption(self, svc):
        _def(svc).effects[fx.SIEGE_TIME_OFFSET] = 1000.0
        _atk(svc).effects[fx.ENEMY_SIEGE_TIME_MODIFIER] = 0.28
        assert _calc(svc) == pytest.approx(720.0)

    def test_38_pct_corruption(self, svc):
        _def(svc).effects[fx.SIEGE_TIME_OFFSET] = 1000.0
        _atk(svc).effects[fx.ENEMY_SIEGE_TIME_MODIFIER] = 0.38
        assert _calc(svc) == pytest.approx(620.0)

    def test_100_pct_corruption_clamps(self, svc):
        _def(svc).effects[fx.SIEGE_TIME_OFFSET] = 23520.0
        _atk(svc).effects[fx.ENEMY_SIEGE_TIME_MODIFIER] = 1.0
        assert _calc(svc) == 1.0

    def test_corruption_only_affects_attacker_not_defender(self, svc):
        """Attacker A's corruption does not influence the value when A is the defender."""
        # Defender has no corruption set
        _def(svc).effects[fx.SIEGE_TIME_OFFSET] = 1000.0
        _atk(svc).effects[fx.ENEMY_SIEGE_TIME_MODIFIER] = 0.5
        # Defender is NOT the one with corruption — corruption is attacker-side
        assert _calc(svc) == pytest.approx(500.0)


# ── combined modifier + corruption ───────────────────────────────────────────

class TestCombined:
    def test_modifier_and_corruption_multiply(self, svc):
        """Modifier and corruption apply multiplicatively."""
        _def(svc).effects[fx.SIEGE_TIME_OFFSET] = 23520.0
        _def(svc).effects[fx.SIEGE_TIME_MODIFIER] = 0.5
        _atk(svc).effects[fx.ENEMY_SIEGE_TIME_MODIFIER] = 0.28
        # 23520 * 0.5 * 0.72 = 8467.2
        assert _calc(svc) == pytest.approx(8467.2)

    def test_dravithar_eem_28pct_scenario(self, svc):
        """Reproduce the actual prod scenario: Dravithar 23520 offset, rally 0.5, eem 28%."""
        _def(svc).effects[fx.SIEGE_TIME_OFFSET] = 23520.0
        _def(svc).effects[fx.SIEGE_TIME_MODIFIER] = 0.5
        _atk(svc).effects[fx.ENEMY_SIEGE_TIME_MODIFIER] = 0.28
        assert _calc(svc) == pytest.approx(8467.2)

    def test_dravithar_eem_38pct_scenario(self, svc):
        """Prod scenario after ASSASSINS_DAGGER artifact: eem 38% corruption."""
        _def(svc).effects[fx.SIEGE_TIME_OFFSET] = 23520.0
        _def(svc).effects[fx.SIEGE_TIME_MODIFIER] = 0.5
        _atk(svc).effects[fx.ENEMY_SIEGE_TIME_MODIFIER] = 0.38
        # 23520 * 0.5 * 0.62 = 7291.2
        assert _calc(svc) == pytest.approx(7291.2)

    def test_modifier_100pct_overrides_corruption(self, svc):
        """When modifier=1.0, result is 0 regardless of corruption → clamped to 1.0."""
        _def(svc).effects[fx.SIEGE_TIME_OFFSET] = 23520.0
        _def(svc).effects[fx.SIEGE_TIME_MODIFIER] = 1.0
        _atk(svc).effects[fx.ENEMY_SIEGE_TIME_MODIFIER] = 0.5
        assert _calc(svc) == 1.0

    def test_high_offset_high_modifier_high_corruption(self, svc):
        _def(svc).effects[fx.SIEGE_TIME_OFFSET] = 50000.0
        _def(svc).effects[fx.SIEGE_TIME_MODIFIER] = 0.6
        _atk(svc).effects[fx.ENEMY_SIEGE_TIME_MODIFIER] = 0.4
        # 50000 * 0.4 * 0.6 = 12000
        assert _calc(svc) == pytest.approx(12000.0)

    def test_base_override_with_modifier_and_corruption(self, svc):
        """AI-style: base_override + offset both reduced by modifier and corruption."""
        _def(svc).effects[fx.SIEGE_TIME_OFFSET] = 200.0
        _def(svc).effects[fx.SIEGE_TIME_MODIFIER] = 0.5
        _atk(svc).effects[fx.ENEMY_SIEGE_TIME_MODIFIER] = 0.2
        # (100 + 200) * 0.5 * 0.8 = 120
        assert _calc(svc, base_override=100.0) == pytest.approx(120.0)


# ── siege_time_modifier is read from DEFENDER (design note) ──────────────────

class TestModifierSourceIsDefender:
    def test_attacker_siege_time_modifier_is_ignored(self, svc):
        """siege_time_modifier on the ATTACKER has no effect — only defender's is used.

        Per current implementation (attack_service.py line 435), modifier is
        read from the defender. If this test fails, the read source has changed.
        """
        _def(svc).effects[fx.SIEGE_TIME_OFFSET] = 1000.0
        _atk(svc).effects[fx.SIEGE_TIME_MODIFIER] = 0.9  # attacker has it — should be ignored
        # Only defender's modifier (unset = 0) applies → 1000.0
        assert _calc(svc) == pytest.approx(1000.0)

    def test_defender_siege_time_modifier_is_applied(self, svc):
        """siege_time_modifier on the DEFENDER is what reduces siege time."""
        _def(svc).effects[fx.SIEGE_TIME_OFFSET] = 1000.0
        _def(svc).effects[fx.SIEGE_TIME_MODIFIER] = 0.9
        # 1000 * 0.1 = 100
        assert _calc(svc) == pytest.approx(100.0)

    def test_both_have_modifier_only_defender_counts(self, svc):
        """When both have siege_time_modifier, only defender's is applied."""
        _def(svc).effects[fx.SIEGE_TIME_OFFSET] = 1000.0
        _def(svc).effects[fx.SIEGE_TIME_MODIFIER] = 0.5   # → halved
        _atk(svc).effects[fx.SIEGE_TIME_MODIFIER] = 0.9   # → ignored
        assert _calc(svc) == pytest.approx(500.0)


# ── minimum clamp ─────────────────────────────────────────────────────────────

class TestMinimumClamp:
    def test_result_never_below_one(self, svc):
        """Result is always at least 1.0 regardless of effects."""
        _def(svc).effects[fx.SIEGE_TIME_OFFSET] = 0.0
        _def(svc).effects[fx.SIEGE_TIME_MODIFIER] = 1.0
        _atk(svc).effects[fx.ENEMY_SIEGE_TIME_MODIFIER] = 1.0
        assert _calc(svc) == 1.0

    def test_result_is_exactly_one_when_offset_zero(self, svc):
        assert _calc(svc) == 1.0

    def test_small_result_clamped(self, svc):
        """Offset=2 * (1-0.9) * (1-0.9) = 0.02 → clamped to 1.0."""
        _def(svc).effects[fx.SIEGE_TIME_OFFSET] = 2.0
        _def(svc).effects[fx.SIEGE_TIME_MODIFIER] = 0.9
        _atk(svc).effects[fx.ENEMY_SIEGE_TIME_MODIFIER] = 0.9
        assert _calc(svc) == 1.0


# ── AI base_override scenarios ────────────────────────────────────────────────

class TestAiBaseOverride:
    def test_ai_base_only_no_defender_effects(self, svc):
        assert _calc(svc, base_override=600.0) == pytest.approx(600.0)

    def test_ai_base_with_defender_offset(self, svc):
        _def(svc).effects[fx.SIEGE_TIME_OFFSET] = 300.0
        # (600 + 300) = 900
        assert _calc(svc, base_override=600.0) == pytest.approx(900.0)

    def test_ai_base_with_all_effects(self, svc):
        _def(svc).effects[fx.SIEGE_TIME_OFFSET] = 300.0
        _def(svc).effects[fx.SIEGE_TIME_MODIFIER] = 0.5
        _atk(svc).effects[fx.ENEMY_SIEGE_TIME_MODIFIER] = 0.1
        # (600 + 300) * 0.5 * 0.9 = 405
        assert _calc(svc, base_override=600.0) == pytest.approx(405.0)

    def test_ai_base_zero_with_offset(self, svc):
        """Explicit base_override=0.0 still uses offset."""
        _def(svc).effects[fx.SIEGE_TIME_OFFSET] = 500.0
        assert _calc(svc, base_override=0.0) == pytest.approx(500.0)

    def test_no_base_override_uses_zero(self, svc):
        """Without base_override, base defaults to 0 (human attack)."""
        _def(svc).effects[fx.SIEGE_TIME_OFFSET] = 500.0
        assert _calc(svc) == pytest.approx(500.0)


# ── per-army siege corruption toggle ──────────────────────────────────────────

class TestArmySiegeCorruptionToggle:
    """Army.siege_corruption_enabled=False leaves the attacker's corruption out.

    The toggle is passed down from the TRAVELING→IN_SIEGE transition, which
    reads it off the attacking army.
    """

    def test_toggle_off_drops_the_attacker_corruption(self, svc):
        attack_service, _ = svc
        _def(svc).effects[fx.SIEGE_TIME_OFFSET] = 1000.0
        _atk(svc).effects[fx.ENEMY_SIEGE_TIME_MODIFIER] = 0.4

        with_corruption = attack_service._calculate_siege_duration(
            ATTACKER_UID, DEFENDER_UID,
        )
        without_corruption = attack_service._calculate_siege_duration(
            ATTACKER_UID, DEFENDER_UID, apply_attacker_corruption=False,
        )
        assert with_corruption == pytest.approx(600.0)   # 1000 * 0.6
        assert without_corruption == pytest.approx(1000.0)  # full siege

    def test_toggle_off_matches_having_no_corruption_at_all(self, svc):
        attack_service, _ = svc
        _def(svc).effects[fx.SIEGE_TIME_OFFSET] = 900.0
        _def(svc).effects[fx.SIEGE_TIME_MODIFIER] = 0.25
        _atk(svc).effects[fx.ENEMY_SIEGE_TIME_MODIFIER] = 0.3
        toggled_off = attack_service._calculate_siege_duration(
            ATTACKER_UID, DEFENDER_UID, apply_attacker_corruption=False,
        )

        _atk(svc).effects[fx.ENEMY_SIEGE_TIME_MODIFIER] = 0.0
        no_effect = attack_service._calculate_siege_duration(ATTACKER_UID, DEFENDER_UID)
        assert toggled_off == pytest.approx(no_effect)

    def test_toggle_on_is_the_default(self, svc):
        attack_service, _ = svc
        _def(svc).effects[fx.SIEGE_TIME_OFFSET] = 1000.0
        _atk(svc).effects[fx.ENEMY_SIEGE_TIME_MODIFIER] = 0.4
        assert attack_service._calculate_siege_duration(
            ATTACKER_UID, DEFENDER_UID,
        ) == attack_service._calculate_siege_duration(
            ATTACKER_UID, DEFENDER_UID, apply_attacker_corruption=True,
        )

    def test_toggle_off_still_respects_the_one_second_floor(self, svc):
        attack_service, _ = svc
        _atk(svc).effects[fx.ENEMY_SIEGE_TIME_MODIFIER] = 0.9
        assert attack_service._calculate_siege_duration(
            ATTACKER_UID, DEFENDER_UID, apply_attacker_corruption=False,
        ) == 1.0


# ── the toggle reaching the real TRAVELING→IN_SIEGE transition ────────────────

class TestSiegeTransitionReadsTheArmy:
    """AttackService.step() must pick the flag off the attacking army.

    Unit-testing _calculate_siege_duration alone would miss the army lookup at
    the call site, which is where the toggle is actually read.
    """

    @staticmethod
    def _arrive(svc, army: Army | None, aid: int = 1) -> float:
        attack_service, empire_service = svc
        # step() recomputes both empires' effects from their buildings before
        # the siege is sized; this test sets effects directly, so keep them.
        empire_service.recalculate_effects = lambda _empire: None
        attacker = empire_service.get(ATTACKER_UID)
        attacker.armies = [army] if army is not None else []
        attack = Attack(
            attack_id=1, attacker_uid=ATTACKER_UID, defender_uid=DEFENDER_UID,
            army_aid=aid, phase=AttackPhase.TRAVELING, eta_seconds=0.0,
        )
        attack_service.step(attack, 1.0)
        assert attack.phase is AttackPhase.IN_SIEGE
        return attack.total_siege_seconds

    def test_army_with_toggle_on_gets_the_shortened_siege(self, svc):
        _def(svc).effects[fx.SIEGE_TIME_OFFSET] = 1000.0
        _atk(svc).effects[fx.ENEMY_SIEGE_TIME_MODIFIER] = 0.4
        army = Army(aid=1, uid=ATTACKER_UID, name="Alpha")
        assert self._arrive(svc, army) == pytest.approx(600.0)

    def test_army_with_toggle_off_serves_the_full_siege(self, svc):
        _def(svc).effects[fx.SIEGE_TIME_OFFSET] = 1000.0
        _atk(svc).effects[fx.ENEMY_SIEGE_TIME_MODIFIER] = 0.4
        army = Army(aid=1, uid=ATTACKER_UID, name="Alpha", siege_corruption_enabled=False)
        assert self._arrive(svc, army) == pytest.approx(1000.0)

    def test_vanished_army_falls_back_to_applying_corruption(self, svc):
        # Army deleted while the attack was in the air — keep the old behaviour.
        _def(svc).effects[fx.SIEGE_TIME_OFFSET] = 1000.0
        _atk(svc).effects[fx.ENEMY_SIEGE_TIME_MODIFIER] = 0.4
        assert self._arrive(svc, None) == pytest.approx(600.0)
