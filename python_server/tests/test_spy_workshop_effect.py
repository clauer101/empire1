"""Unit tests for spy_workshop empire effect in _build_spy_report."""

from unittest.mock import MagicMock

from gameserver.models.empire import Empire
from gameserver.network.handlers.military import _build_spy_report


def _make_defender() -> Empire:
    defender = Empire(uid=1, name="Target")
    defender.hex_map = {
        "0,0": "BASIC_TOWER",
        "1,0": "ARROW_TOWER",
        "2,0": "path",
        "3,0": "castle",
    }
    defender.item_upgrades = {
        "BASIC_TOWER": {"damage": 2, "range": 1},
    }
    return defender


def _make_svc(defender: Empire) -> MagicMock:
    from gameserver.util.eras import ERA_ORDER

    empire_svc = MagicMock()
    empire_svc.get_current_era = MagicMock(return_value=ERA_ORDER[0])  # STEINZEIT

    items: dict = {}
    empire_svc._item_era_index = {}

    upgrade_provider = MagicMock()
    upgrade_provider.items = items

    svc = MagicMock()
    svc.empire_service = empire_svc
    svc.upgrade_provider = upgrade_provider
    return svc


# ── Without spy_workshop effect ───────────────────────────────────────────────

class TestSpyReportWithoutWorkshop:
    def test_no_workshop_section_in_text(self):
        defender = _make_defender()
        svc = _make_svc(defender)
        attacker = Empire(uid=2, name="Spy")
        # no spy_workshop effect set

        text, data = _build_spy_report(defender, svc, attacker=attacker)

        assert "Workshop Intelligence" not in text

    def test_no_structures_in_data(self):
        defender = _make_defender()
        svc = _make_svc(defender)
        attacker = Empire(uid=2, name="Spy")

        _, data = _build_spy_report(defender, svc, attacker=attacker)

        assert "structures" not in data
        assert "critters" not in data

    def test_tower_placement_always_present(self):
        defender = _make_defender()
        svc = _make_svc(defender)
        attacker = Empire(uid=2, name="Spy")

        text, data = _build_spy_report(defender, svc, attacker=attacker)

        assert "Towers placed" in text
        assert "placed_towers" in data

    def test_attacker_none_also_hides_workshop(self):
        """Backward-compat: attacker=None (old call sites) → no workshop section."""
        defender = _make_defender()
        svc = _make_svc(defender)

        text, data = _build_spy_report(defender, svc, attacker=None)

        assert "Workshop Intelligence" not in text
        assert "structures" not in data


# ── With spy_workshop effect ──────────────────────────────────────────────────

class TestSpyReportWithWorkshop:
    def _attacker_with_workshop(self, value: float = 1.0) -> Empire:
        attacker = Empire(uid=2, name="Spy")
        attacker.effects["spy_workshop"] = value
        return attacker

    def test_workshop_section_present_in_text(self):
        defender = _make_defender()
        svc = _make_svc(defender)
        attacker = self._attacker_with_workshop()

        text, _ = _build_spy_report(defender, svc, attacker=attacker)

        assert "Workshop Intelligence" in text

    def test_structures_and_critters_in_data(self):
        defender = _make_defender()
        svc = _make_svc(defender)
        attacker = self._attacker_with_workshop()

        _, data = _build_spy_report(defender, svc, attacker=attacker)

        assert "structures" in data
        assert "critters" in data

    def test_tower_placement_still_present(self):
        defender = _make_defender()
        svc = _make_svc(defender)
        attacker = self._attacker_with_workshop()

        text, data = _build_spy_report(defender, svc, attacker=attacker)

        assert "Towers placed" in text
        assert "placed_towers" in data

    def test_spy_workshop_zero_hides_workshop(self):
        """Exactly 0.0 is below threshold → no workshop section."""
        defender = _make_defender()
        svc = _make_svc(defender)
        attacker = Empire(uid=2, name="Spy")
        attacker.effects["spy_workshop"] = 0.0

        text, data = _build_spy_report(defender, svc, attacker=attacker)

        assert "Workshop Intelligence" not in text
        assert "structures" not in data

    def test_spy_workshop_small_positive_enables_section(self):
        """Any value > 0 (e.g. 0.1) enables workshop intelligence."""
        defender = _make_defender()
        svc = _make_svc(defender)
        attacker = self._attacker_with_workshop(value=0.1)

        text, data = _build_spy_report(defender, svc, attacker=attacker)

        assert "Workshop Intelligence" in text
        assert "structures" in data
