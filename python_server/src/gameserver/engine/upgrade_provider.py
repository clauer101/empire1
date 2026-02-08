"""Upgrade provider — tech tree database.

Loads item definitions from config and provides lookup, filtering,
and requirement checking for all game items.
"""

from __future__ import annotations

from gameserver.models.items import ItemDetails, ItemType


class UpgradeProvider:
    """Tech tree database — read-only after initialization.

    Attributes:
        items: All item definitions keyed by IID.
    """

    def __init__(self) -> None:
        self.items: dict[str, ItemDetails] = {}

    def load(self, items: list[ItemDetails]) -> None:
        """Load item definitions into the provider."""
        self.items = {item.iid: item for item in items}

    def get(self, iid: str) -> ItemDetails | None:
        """Look up an item by IID."""
        return self.items.get(iid)

    def get_by_type(self, item_type: ItemType) -> list[ItemDetails]:
        """Return all items of a given type."""
        return [i for i in self.items.values() if i.item_type == item_type]

    def check_requirements(self, iid: str, completed: set[str]) -> bool:
        """Check if all prerequisites for an item are met."""
        item = self.items.get(iid)
        if item is None:
            return False
        return all(req in completed for req in item.requirements)

    def get_costs(self, iid: str) -> dict[str, float]:
        """Return the resource costs for an item."""
        item = self.items.get(iid)
        return dict(item.costs) if item else {}

    def get_effects(self, iid: str) -> dict[str, float]:
        """Return the passive effects granted by an item."""
        item = self.items.get(iid)
        return dict(item.effects) if item else {}

    def available_critters(self, completed: set[str]) -> list[ItemDetails]:
        """Return all critter types whose requirements are met."""
        return [
            i
            for i in self.items.values()
            if i.item_type == ItemType.CRITTER
            and all(req in completed for req in i.requirements)
        ]

    def available_items(self, item_type: ItemType, completed: set[str]) -> list[ItemDetails]:
        """Return all items of *item_type* whose requirements are met."""
        return [
            i
            for i in self.items.values()
            if i.item_type == item_type
            and all(req in completed for req in i.requirements)
        ]
