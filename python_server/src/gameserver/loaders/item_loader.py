"""Item loader — parses items.yaml into ItemDetails models.

Replaces the Java ItemInterpreter SAX parser.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from gameserver.models.items import ItemDetails, ItemType


def load_items(path: str | Path = "config/items.yaml") -> list[ItemDetails]:
    """Load all item definitions from a YAML file.

    Args:
        path: Path to the items.yaml configuration file.

    Returns:
        List of ItemDetails objects.
    """
    path = Path(path)
    with path.open() as f:
        data = yaml.safe_load(f) or {}

    items: list[ItemDetails] = []

    for type_key in ("buildings", "knowledge", "structures", "critters", "artefacts", "wonders"):
        item_type = ItemType(type_key.rstrip("s"))  # buildings → building
        section = data.get(type_key, {}) or {}
        for iid, attrs in section.items():
            if not isinstance(attrs, dict):
                continue
            items.append(ItemDetails(
                iid=iid,
                name=attrs.get("name", iid),
                item_type=item_type,
                effort=float(attrs.get("effort", 0)),
                costs=attrs.get("costs", {}),
                requirements=attrs.get("requirements", []),
                effects=attrs.get("effects", {}),
                damage=float(attrs.get("damage", 0)),
                range=int(attrs.get("range", 0)),
                reload_time_ms=float(attrs.get("reload_time", 0)),
                shot_speed=float(attrs.get("shot_speed", 0)),
                shot_type=attrs.get("shot_type", "normal"),
                speed=float(attrs.get("speed", 0)),
                health=float(attrs.get("health", 0)),
                armour=float(attrs.get("armour", 0)),
                slots=int(attrs.get("slots", 1)),
                time_between_ms=float(attrs.get("time_between", 500)),
                is_boss=bool(attrs.get("is_boss", False)),
                capture=attrs.get("capture", {}),
                bonus=attrs.get("bonus", {}),
                spawn_on_death=attrs.get("spawn_on_death", {}),
            ))

    return items
