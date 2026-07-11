---
paths:
  - "python_server/**"
---

# Backend Rules

## Era Key Naming — 2 Systems, do not mix

| System | Example | Used in |
|--------|---------|---------|
| **Lowercase** | `stone`, `medieval`, `renaissance` | `ERA_ORDER`, `get_current_era()`, `era_effects` dict keys, `game.yaml`, `ERA_LABELS_EN` |
| **UPPERCASE** | `STONE_AGE`, `MEDIEVAL`, `INDUSTRIAL` | `era:` field in item YAMLs (`knowledge.yaml`, `buildings.yaml`, etc.), `ERA_ITEM_TO_INDEX` |

Lowercase is the canonical runtime format. UPPERCASE only appears in item YAML
`era:` fields and `ERA_ITEM_TO_INDEX`. Travel offsets are legacy flat fields:
`stone_travel_offset`, `medieval_travel_offset`, etc. in `GameConfig`.

## Upgrade System

- **Item upgrades** (`item_upgrades: dict[iid, dict[stat, level]]`) live on `Empire`.
- **Price formula**: `base_cost × (total_levels_on_iid + 1)²` — base cost from `game.yaml item_upgrade_base_costs[era_index]`.
- Era index for structures/critters is built at startup in `main.py` (`_item_era_index`) by parsing YAML section comments.
- Structure stats: `damage`, `range`, `reload`, `effect_duration`, `effect_value` (+2–3% per level).
- Critter stats: `health`, `speed`, `armour` (+2% per level).
- Applied in `battle_service._step_armies()` at spawn time (normal waves) and `_make_critter_from_item()` (spawn-on-death).

## Adding Python Packages

1. Add to `python_server/pyproject.toml` under `dependencies`
2. Run `uv lock` in the repo root to update `python_server/uv.lock`
3. Run `bash deploy.sh dev` (or `prod`, only with user confirmation) — Docker runs
   `uv sync --frozen` during build, so the lockfile must be committed before deploying

Never install with `pip install` alone — it won't update the lockfile and the
package will be missing in Docker.

## Logging

`util/logging.py` — structlog setup; `LOG_FORMAT=json|console` env var controls the renderer.
