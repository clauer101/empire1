"""Era definitions — single source of truth for all era-related constants."""

from __future__ import annotations

# Ordered list of era keys (lowercase English, canonical format).
ERA_ORDER: list[str] = [
    "stone", "neolithic", "bronze", "iron",
    "middle_ages", "renaissance", "industrial", "modern", "future",
]

# Maps era key → GameConfig field name for travel offset.
ERA_TRAVEL_FIELD: dict[str, str] = {
    "stone":        "stone_travel_offset",
    "neolithic":    "neolithic_travel_offset",
    "bronze":       "bronze_travel_offset",
    "iron":         "iron_travel_offset",
    "middle_ages":  "middle_ages_travel_offset",
    "renaissance":  "renaissance_travel_offset",
    "industrial":   "industrial_travel_offset",
    "modern":       "modern_travel_offset",
    "future":       "future_travel_offset",
}

# Identity map — era keys in game.yaml era_effects match ERA_ORDER directly.
ERA_YAML_TO_KEY: dict[str, str] = {k: k for k in ERA_ORDER}

# Identity map — era key matches the GameConfig field prefix.
ERA_YAML_TO_FIELD: dict[str, str] = {k: k for k in ERA_ORDER}

# Maps legacy item era field value → ERA_ORDER index.
ERA_ITEM_TO_INDEX: dict[str, int] = {
    "STONE_AGE": 0, "NEOLITHIC": 1, "BRONZE_AGE": 2, "IRON_AGE": 3,
    "MEDIEVAL": 4, "RENAISSANCE": 5, "INDUSTRIAL": 6, "MODERN": 7, "FUTURE": 8,
}

# Display labels (German).
ERA_LABELS_DE: dict[str, str] = {
    "stone":       "Steinzeit",
    "neolithic":   "Neolithikum",
    "bronze":      "Bronzezeit",
    "iron":        "Eisenzeit",
    "middle_ages": "Mittelalter",
    "renaissance": "Renaissance",
    "industrial":  "Industrialisierung",
    "modern":      "Moderne",
    "future":      "Zukunft",
}

# Display labels (English).
ERA_LABELS_EN: dict[str, str] = {
    "stone":       "Stone Age",
    "neolithic":   "Neolithic",
    "bronze":      "Bronze Age",
    "iron":        "Iron Age",
    "middle_ages": "Middle Ages",
    "renaissance": "Renaissance",
    "industrial":  "Industrial",
    "modern":      "Modern",
    "future":      "Future",
}
