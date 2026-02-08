"""Item loader — parses item YAML files into ItemDetails models.

Replaces the Java ItemInterpreter SAX parser.

Supports two modes:
  1. Single file with all sections (legacy items.yaml)
  2. Directory with per-category files: buildings.yaml, knowledge.yaml,
     structures.yaml, critters.yaml, artefacts.yaml
"""

from __future__ import annotations

from pathlib import Path

import yaml

from gameserver.models.items import ItemDetails, ItemType

# Category keys and the file stems they map to.
_CATEGORIES = ("buildings", "knowledge", "structures", "critters", "artefacts", "wonders")


def _type_for_category(cat: str) -> ItemType:
    """Map a plural category key to its ItemType enum value."""
    singular = cat.rstrip("s")  # buildings → building
    return ItemType(singular)


def _parse_section(type_key: str, section: dict) -> list[ItemDetails]:
    """Parse a single category section dict into ItemDetails."""
    item_type = _type_for_category(type_key)
    items: list[ItemDetails] = []
    for iid, attrs in (section or {}).items():
        if not isinstance(attrs, dict):
            continue
        items.append(ItemDetails(
            iid=iid,
            name=attrs.get("name", iid),
            description=attrs.get("description", ""),
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


def load_items(path: str | Path = "config") -> list[ItemDetails]:
    """Load all item definitions from YAML file(s).

    Args:
        path: Either a directory containing per-category YAML files
              (buildings.yaml, knowledge.yaml, …) or a single YAML file
              with all sections (legacy mode).

    Returns:
        List of ItemDetails objects.
    """
    path = Path(path)
    items: list[ItemDetails] = []

    if path.is_dir():
        # ── Per-category files mode ────────────────────────
        for cat in _CATEGORIES:
            cat_file = path / f"{cat}.yaml"
            if not cat_file.exists():
                continue
            with cat_file.open() as f:
                data = yaml.safe_load(f) or {}
            items.extend(_parse_section(cat, data))
    else:
        # ── Single-file legacy mode ────────────────────────
        with path.open() as f:
            data = yaml.safe_load(f) or {}
        for cat in _CATEGORIES:
            section = data.get(cat, {}) or {}
            items.extend(_parse_section(cat, section))

    return items
