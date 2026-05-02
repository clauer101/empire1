# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Language

All UI text, labels, messages, button text, and placeholders in the codebase must be written in English.

## Shell Commands

Always prefix bash commands with `rtk` for token savings (e.g. `rtk git status`, `rtk cat file`).

## Validating Code Changes

Run these after every backend change, in order:

**1. Lint (ruff):**
```bash
.venv/bin/ruff check python_server/src/
```

**2. Tests:**
```bash
rtk run_tests.sh
```

**3. Single test or pattern:**
```bash
rtk run_tests.sh --match=test_battle_service
rtk run_tests.sh tests/test_item_upgrades.py
```

Other test options: `--all`, `--quick`, `--cov`, `--failfast`

**4. Pre-commit (runs ruff + mypy + detect-secrets):**
```bash
.venv/bin/pre-commit run --all-files
```

Pre-commit runs automatically on `git commit`. Never use `--no-verify` to bypass it.

## Deployment

```bash
./deploy.sh prod       # build + deploy prod
./deploy.sh dev        # build + deploy dev
./deploy.sh both       # build + deploy both
./deploy.sh prod stop  # save state + stop prod
./deploy.sh dev stop   # save state + stop dev
```

Live logs:
```bash
./attach.sh            # prod gameserver logs
./attach.sh dev        # dev gameserver logs
```

State and DB are persisted in:
- Prod: `data/prod/state.yaml`, `data/prod/gameserver.db`
- Dev:  `data/dev/state.yaml`,  `data/dev/gameserver.db`

## Architecture

This is a multiplayer tower-defense / empire-building game. Two servers run per environment (prod/dev):

- **Game server** (`python_server/`) — Python asyncio WebSocket server + REST API (FastAPI). Entry: `gameserver.main:main`
- **Web server** (`web/fastapi_server.py`) — FastAPI serving the SPA static files on port 8000

nginx routes: API/WS → gameserver, static → webserver.  
Prod: HTTPS on 443. Dev: HTTP on 80 only (`http://dev.relicsnrockets.io`).

### Backend (`python_server/src/gameserver/`)

**engine/** — Core game logic, driven by a 1000ms tick in `game_loop.py`:
- `battle_service.py` — Wave spawning, slot-based critter capacity, combat resolution
- `army_service.py`, `attack_service.py` — Player armies and attacks
- `empire_service.py`, `power_service.py` — Player state and progression
- `ai_service.py` — AI wave generation
- `hex_pathfinding.py`, `upgrade_provider.py` — Map and upgrade mechanics

**persistence/** — SQLite (async) via `database.py`; state serialized to/from YAML (`state_load.py`, `state_save.py`); replays stored compressed. Schema migrations via Alembic (`migrations/`).

**network/** — WebSocket routing (`router.py`, `handlers.py`) and REST API (`rest_api.py`).

**loaders/** — Parse YAML configs into typed models (`game_config_loader.py`, `item_loader.py`).

**models/** — Dataclasses/pydantic models for all game entities (`items.py`, etc.).

**util/logging.py** — structlog setup; `LOG_FORMAT=json|console` env var controls renderer.

### Configuration (`python_server/config/`)

All game balance lives in YAML:
- `game.yaml` — Timings, resource rates, era effects
- `buildings.yaml`, `structures.yaml`, `critters.yaml` — Entity definitions
- `ai_waves.yaml` — AI wave definitions across 9 eras (Stone → Future)
- `artefacts.yaml`, `knowledge.yaml` — Tech tree content
- `maps/default.yaml` — Default map

### Frontend (`web/`)

Single-page app, no build step. `js/app.js` + `js/router.js` form the SPA shell. Views are in `js/views/`. API calls go through `js/api.js` (WebSocket) and `js/rest.js` (HTTP).

Key views: `defense.js` (tower placement + battle), `army.js` (critter wave composer), `techtree.js` (knowledge tree), `workshop.js` (item upgrades).  
Shared UI lib: `js/lib/item_overlay.js` (item detail overlay), `js/lib/eras.js` (era constants).

Developer tools at `web/tools/` — `status.html` (live server status), `database.html` (user admin), balance tuner, replay viewer.

### Key Design Patterns

- **Slot-based wave spawning**: waves have a slot capacity; critters consume 1+ slots. See `battle_service._step_wave()`.
- **Effects dict**: tower effects (burn, slow) are stored as `effects.burn_duration`, `effects.burn_dps`, etc. in config and models.
- **Async throughout**: backend uses `asyncio`; tests use `pytest-asyncio`.

### Era Key Naming — 3 Systems (Gotcha)

Three different era key systems exist and must not be mixed:

| System | Example | Used in |
|--------|---------|---------|
| **German** | `STEINZEIT`, `MITTELALTER` | `ERA_ORDER`, `get_current_era()`, `era_effects` dict keys |
| **Internal** | `stone`, `middle_ages`, `renaissance` | `game.yaml` keys, `ai_generator`, `ERA_BACKEND_TO_INTERNAL` |
| **YAML-item** | `STONE_AGE`, `MEDIEVAL`, `INDUSTRIAL` | `era:` field in `knowledge.yaml`, `ERA_ITEM_TO_INDEX` |

Mappings: `ERA_BACKEND_TO_INTERNAL` in `util/army_generator.py`, `ERA_YAML_TO_KEY` in `util/eras.py`.  
Travel offsets are stored as legacy flat fields: `stone_travel_offset`, `middle_ages_travel_offset`, etc. in `GameConfig`.

### Upgrade System

- **Item upgrades** (`item_upgrades: dict[iid, dict[stat, level]]`) live on `Empire`.
- **Price formula**: `base_cost × (total_levels_on_iid + 1)²` — base cost from `game.yaml item_upgrade_base_costs[era_index]`.
- Era index for structures/critters is built at startup in `main.py` (`_item_era_index`) by parsing YAML section comments.
- Structure stats: `damage`, `range`, `reload`, `effect_duration`, `effect_value` (+2–3% per level).
- Critter stats: `health`, `speed`, `armour` (+2% per level).
- Applied in `battle_service._step_armies()` at spawn time (normal waves) and `_make_critter_from_item()` (spawn-on-death).
