"""Era definitions — single source of truth for all era-related constants.

Every module that needs era keys, labels, or mappings should import from here
rather than defining its own copies.
"""

from __future__ import annotations

# Ordered list of era keys (German uppercase identifiers used throughout codebase).
ERA_ORDER: list[str] = [
    "STEINZEIT", "NEOLITHIKUM", "BRONZEZEIT", "EISENZEIT",
    "MITTELALTER", "RENAISSANCE", "INDUSTRIALISIERUNG", "MODERNE", "ZUKUNFT",
]

# Maps era key → GameConfig field name for travel offset.
ERA_TRAVEL_FIELD: dict[str, str] = {
    "STEINZEIT":          "stone_travel_offset",
    "NEOLITHIKUM":        "neolithicum_travel_offset",
    "BRONZEZEIT":         "bronze_travel_offset",
    "EISENZEIT":          "iron_travel_offset",
    "MITTELALTER":        "middle_ages_travel_offset",
    "RENAISSANCE":        "rennaissance_travel_offset",
    "INDUSTRIALISIERUNG": "industrial_travel_offset",
    "MODERNE":            "modern_travel_offset",
    "ZUKUNFT":            "diamond_travel_offset",
}

# Maps lowercase YAML key (used in game.yaml era_effects) → uppercase era key.
ERA_YAML_TO_KEY: dict[str, str] = {
    "stone": "STEINZEIT", "neolithicum": "NEOLITHIKUM", "bronze": "BRONZEZEIT",
    "iron": "EISENZEIT", "middle_ages": "MITTELALTER", "rennaissance": "RENAISSANCE",
    "industrial": "INDUSTRIALISIERUNG", "modern": "MODERNE", "future": "ZUKUNFT",
}

# Maps lowercase YAML key → GameConfig field prefix for travel/siege.
ERA_YAML_TO_FIELD: dict[str, str] = {
    "stone": "stone", "neolithicum": "neolithicum", "bronze": "bronze",
    "iron": "iron", "middle_ages": "middle_ages", "rennaissance": "rennaissance",
    "industrial": "industrial", "modern": "modern", "future": "diamond",
}

# Display labels (German).
ERA_LABELS_DE: dict[str, str] = {
    "STEINZEIT": "Steinzeit", "NEOLITHIKUM": "Neolithikum",
    "BRONZEZEIT": "Bronzezeit", "EISENZEIT": "Eisenzeit",
    "MITTELALTER": "Mittelalter", "RENAISSANCE": "Renaissance",
    "INDUSTRIALISIERUNG": "Industrialisierung", "MODERNE": "Moderne",
    "ZUKUNFT": "Zukunft",
}

# Display labels (English).
ERA_LABELS_EN: dict[str, str] = {
    "STEINZEIT": "Stone Age", "NEOLITHIKUM": "Neolithic",
    "BRONZEZEIT": "Bronze Age", "EISENZEIT": "Iron Age",
    "MITTELALTER": "Middle Ages", "RENAISSANCE": "Renaissance",
    "INDUSTRIALISIERUNG": "Industrial", "MODERNE": "Modern",
    "ZUKUNFT": "Future",
}
