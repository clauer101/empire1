"""Era dependency integrity tests for structures and critters.

Reads the `era:` field directly from each item in the YAML files to determine
which era each item belongs to, then verifies two invariants:

1. Every structure and critter has at least one requirement from its own era
   (either a building or a knowledge item that also lives in the same era,
   OR another structure/critter in the same era).

2. No requirement of a structure or critter is a knowledge or building item
   from a *later* era than the item itself.
"""

from pathlib import Path

import pytest
import yaml

from gameserver.loaders.item_loader import load_items
from gameserver.models.items import ItemType
from gameserver.util.eras import ERA_ORDER

CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"


def _parse_era_map(yaml_path: Path) -> dict[str, str]:
    """Return {IID: era_key} by reading the `era:` field of each top-level item."""
    data = yaml.safe_load(yaml_path.read_text(encoding="utf-8")) or {}
    return {
        iid: item["era"]
        for iid, item in data.items()
        if isinstance(item, dict) and "era" in item
    }


# ── Build lookup tables ───────────────────────────────────────────────────────
CATALOG = {item.iid: item for item in load_items(CONFIG_DIR)}

# Era assignment for each item type
_STRUCTURE_ERAS = _parse_era_map(CONFIG_DIR / "structures.yaml")
_CRITTER_ERAS   = _parse_era_map(CONFIG_DIR / "critters.yaml")
_BUILDING_ERAS  = _parse_era_map(CONFIG_DIR / "buildings.yaml")
_KNOWLEDGE_ERAS = _parse_era_map(CONFIG_DIR / "knowledge.yaml")

# Combined map for all items that have an era
_ALL_ERAS: dict[str, str] = {
    **_BUILDING_ERAS, **_KNOWLEDGE_ERAS,
    **_STRUCTURE_ERAS, **_CRITTER_ERAS,
}

ERA_INDEX: dict[str, int] = {era: i for i, era in enumerate(ERA_ORDER)}


def _era_index(iid: str) -> int | None:
    era = _ALL_ERAS.get(iid)
    return ERA_INDEX[era] if era else None


# ── Parametrize IDs ───────────────────────────────────────────────────────────
_STRUCTURE_IDS = [iid for iid in CATALOG if CATALOG[iid].item_type == ItemType.STRUCTURE]
_CRITTER_IDS   = [iid for iid in CATALOG if CATALOG[iid].item_type == ItemType.CRITTER]
_SC_IDS        = _STRUCTURE_IDS + _CRITTER_IDS


# =============================================================================
# Test 1: at least one requirement from the item's own era
# =============================================================================

class TestAtLeastOneOwnEraRequirement:
    """Each structure and critter must have ≥1 requirement from its own era."""

    @pytest.mark.parametrize("iid", _SC_IDS)
    def test_has_own_era_requirement(self, iid):
        item = CATALOG[iid]
        own_era = _ALL_ERAS.get(iid)
        if own_era is None:
            pytest.skip(f"{iid} has no era annotation in YAML sections")

        reqs = item.requirements
        if not reqs:
            pytest.skip(f"{iid} has no requirements (starter item)")

        own_era_reqs = [r for r in reqs if _ALL_ERAS.get(r) == own_era]
        assert own_era_reqs, (
            f"{iid} (era={own_era}) has no requirement from its own era. "
            f"Requirements: {reqs} — their eras: "
            f"{[_ALL_ERAS.get(r, '?') for r in reqs]}"
        )


# =============================================================================
# Test 2: no requirement from a later era
# =============================================================================

class TestNoLaterEraRequirement:
    """No requirement of a structure/critter may come from a later era."""

    @pytest.mark.parametrize("iid", _SC_IDS)
    def test_no_future_era_requirement(self, iid):
        item = CATALOG[iid]
        own_era = _ALL_ERAS.get(iid)
        if own_era is None:
            pytest.skip(f"{iid} has no era annotation in YAML sections")

        own_idx = ERA_INDEX[own_era]

        # Only check knowledge and building requirements (not other structures/critters)
        kb_types = {ItemType.KNOWLEDGE, ItemType.BUILDING}
        later_reqs = [
            r for r in item.requirements
            if CATALOG.get(r) and CATALOG[r].item_type in kb_types
            and _era_index(r) is not None
            and _era_index(r) > own_idx
        ]
        assert not later_reqs, (
            f"{iid} (era={own_era}) requires knowledge/building from a later era: "
            + ", ".join(f"{r}({_ALL_ERAS.get(r)})" for r in later_reqs)
        )
