"""Catalog integrity tests.

1. Every item in buildings, knowledge, structures, and critters is reachable
   from the starting items (those with no requirements) via the requirement graph.

2. Every building and knowledge item either grants at least one effect OR is
   referenced as a prerequisite by another item.
"""

from pathlib import Path

import pytest

from gameserver.loaders.item_loader import load_items
from gameserver.models.items import ItemType

CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"

_REACHABILITY_TYPES = {ItemType.BUILDING, ItemType.KNOWLEDGE, ItemType.STRUCTURE, ItemType.CRITTER}
_USEFUL_TYPES = {ItemType.BUILDING, ItemType.KNOWLEDGE}


def _build_catalog():
    return {item.iid: item for item in load_items(CONFIG_DIR)}


def _reachable_iids(catalog: dict) -> set[str]:
    """BFS over the requirement graph, returns the set of all reachable IIDs."""
    reachable = {iid for iid, item in catalog.items() if not item.requirements}
    changed = True
    while changed:
        changed = False
        for iid, item in catalog.items():
            if iid not in reachable and all(r in reachable for r in item.requirements):
                reachable.add(iid)
                changed = True
    return reachable


# Computed once at collection time so parametrize IDs are stable
CATALOG = _build_catalog()
REACHABLE = _reachable_iids(CATALOG)
ALL_PREREQUISITE_IDS: set[str] = {r for item in CATALOG.values() for r in item.requirements}

_REACHABILITY_IDS = [
    iid for iid, item in CATALOG.items() if item.item_type in _REACHABILITY_TYPES
]
_USEFUL_IDS = [
    iid for iid, item in CATALOG.items() if item.item_type in _USEFUL_TYPES
]


class TestReachability:
    """Every item must be reachable from items that have no requirements."""

    @pytest.mark.parametrize("iid", _REACHABILITY_IDS)
    def test_item_is_reachable(self, iid):
        missing = [r for r in CATALOG[iid].requirements if r not in CATALOG]
        unreachable = [r for r in CATALOG[iid].requirements if r in CATALOG and r not in REACHABLE]
        msg_parts = []
        if missing:
            msg_parts.append(f"unknown requirements: {missing}")
        if unreachable:
            msg_parts.append(f"unreachable requirements: {unreachable}")
        assert iid in REACHABLE, (
            f"{iid} ({CATALOG[iid].item_type.value}, name={CATALOG[iid].name!r}) "
            "is not reachable" + (": " + "; ".join(msg_parts) if msg_parts else "")
        )


class TestRequirementsExist:
    """Every requirement IID must reference an existing catalog entry."""

    @pytest.mark.parametrize("iid", _REACHABILITY_IDS)
    def test_requirements_exist(self, iid):
        missing = [r for r in CATALOG[iid].requirements if r not in CATALOG]
        assert not missing, (
            f"{iid} ({CATALOG[iid].name!r}) lists unknown requirements: {missing}"
        )


class TestUseful:
    """Every building and knowledge item must have effects or be a prerequisite."""

    @pytest.mark.parametrize("iid", _USEFUL_IDS)
    def test_item_has_effect_or_is_prerequisite(self, iid):
        item = CATALOG[iid]
        assert item.effects or iid in ALL_PREREQUISITE_IDS, (
            f"{iid} ({item.item_type.value}, name={item.name!r}) has no effects "
            "and is not a prerequisite for any other item"
        )
