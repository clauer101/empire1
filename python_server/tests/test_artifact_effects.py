"""Unit tests verifying that artifact effects are correctly applied
via EmpireService.recalculate_effects."""

from unittest.mock import MagicMock

import pytest

from gameserver.models.empire import Empire
from gameserver.models.items import ItemDetails, ItemType
from gameserver.engine.empire_service import EmpireService
from gameserver.engine.upgrade_provider import UpgradeProvider


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_item(iid: str, item_type: ItemType, effects: dict) -> ItemDetails:
    return ItemDetails(
        iid=iid,
        name=iid,
        item_type=item_type,
        effects=effects,
    )


def _make_service(items: list[ItemDetails]) -> EmpireService:
    up = UpgradeProvider()
    up.load(items)
    gc = MagicMock()
    gc.era_effects = {}
    gc.starting_max_life = 10.0
    gc.stone_travel_offset = 0.0
    svc = EmpireService.__new__(EmpireService)
    svc._upgrades = up
    svc._gc = gc
    svc._ERA_ORDER = ["STEINZEIT"]
    svc._base_gold = 0.0
    svc._base_culture = 0.0
    svc._base_build_speed = 1.0
    svc._base_research_speed = 1.0
    svc.get_current_era = MagicMock(return_value="STEINZEIT")
    return svc


# ── Tests ─────────────────────────────────────────────────────────────────────

class TestArtifactEffectsApplied:
    def test_single_artifact_gold_offset_applied(self):
        art = _make_item("MAGIC_COIN", ItemType.ARTIFACT, {"gold_offset": 5.0})
        svc = _make_service([art])
        empire = Empire(uid=1, artifacts=["MAGIC_COIN"])

        svc.recalculate_effects(empire)

        assert empire.effects.get("gold_offset") == pytest.approx(5.0)

    def test_single_artifact_culture_offset_applied(self):
        art = _make_item("GOLDEN_LYRE", ItemType.ARTIFACT, {"culture_offset": 3.5})
        svc = _make_service([art])
        empire = Empire(uid=1, artifacts=["GOLDEN_LYRE"])

        svc.recalculate_effects(empire)

        assert empire.effects.get("culture_offset") == pytest.approx(3.5)

    def test_all_effect_keys_applied(self):
        effects = {
            "gold_offset": 2.0,
            "culture_offset": 1.5,
            "research_speed_modifier": 0.1,
            "build_speed_modifier": 0.05,
        }
        art = _make_item("WONDER_ORB", ItemType.ARTIFACT, effects)
        svc = _make_service([art])
        empire = Empire(uid=1, artifacts=["WONDER_ORB"])

        svc.recalculate_effects(empire)

        for key, val in effects.items():
            assert empire.effects.get(key) == pytest.approx(val), f"effect {key} not applied"

    def test_multiple_artifacts_effects_stacked(self):
        art1 = _make_item("ART_A", ItemType.ARTIFACT, {"gold_offset": 3.0})
        art2 = _make_item("ART_B", ItemType.ARTIFACT, {"gold_offset": 2.0})
        svc = _make_service([art1, art2])
        empire = Empire(uid=1, artifacts=["ART_A", "ART_B"])

        svc.recalculate_effects(empire)

        assert empire.effects.get("gold_offset") == pytest.approx(5.0)

    def test_artifact_effects_stack_with_building_effects(self):
        building = _make_item("MARKET", ItemType.BUILDING, {"gold_offset": 10.0})
        art = _make_item("COIN_PURSE", ItemType.ARTIFACT, {"gold_offset": 4.0})
        svc = _make_service([building, art])
        empire = Empire(uid=1, buildings={"MARKET": 0.0}, artifacts=["COIN_PURSE"])

        svc.recalculate_effects(empire)

        assert empire.effects.get("gold_offset") == pytest.approx(14.0)

    def test_no_artifacts_no_artifact_effects(self):
        art = _make_item("LOST_GRAIL", ItemType.ARTIFACT, {"gold_offset": 99.0})
        svc = _make_service([art])
        empire = Empire(uid=1, artifacts=[])

        svc.recalculate_effects(empire)

        assert empire.effects.get("gold_offset", 0.0) == pytest.approx(0.0)

    def test_unknown_artifact_iid_does_not_crash(self):
        svc = _make_service([])
        empire = Empire(uid=1, artifacts=["NONEXISTENT_ART"])

        svc.recalculate_effects(empire)  # must not raise

    def test_effects_cleared_when_artifact_removed(self):
        art = _make_item("CROWN", ItemType.ARTIFACT, {"gold_offset": 7.0})
        svc = _make_service([art])
        empire = Empire(uid=1, artifacts=["CROWN"])
        svc.recalculate_effects(empire)
        assert empire.effects.get("gold_offset") == pytest.approx(7.0)

        empire.artifacts.remove("CROWN")
        svc.recalculate_effects(empire)

        assert empire.effects.get("gold_offset", 0.0) == pytest.approx(0.0)
