# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

**Run all tests:**
```bash
./run_tests.sh
```

**Run a single test or pattern:**
```bash
./run_tests.sh --match=test_battle_service
```

**Other test options:** `--all`, `--quick`, `--cov`, `--failfast`

**Start/stop/restart servers:**
```bash
./restart.sh gameserver   # Python WebSocket game server
./restart.sh webserver    # FastAPI static file server (port 8000)
./restart.sh gameserver stop
```

Logs: `gameserver.log`, `webserver.log`. PIDs: `.gameserver.pid`, `.webserver.pid`.

## Architecture

This is a multiplayer tower-defense / empire-building game. Two servers run independently:

- **Game server** (`python_server/`) — Python asyncio WebSocket server. Entry: `gameserver.main:main`
- **Web server** (`web/fastapi_server.py`) — FastAPI serving the SPA static files on port 8000

### Backend (`python_server/src/gameserver/`)

**engine/** — Core game logic, driven by a 1000ms tick in `game_loop.py`:
- `battle_service.py` — Wave spawning, slot-based critter capacity, combat resolution
- `army_service.py`, `attack_service.py` — Player armies and attacks
- `empire_service.py`, `power_service.py` — Player state and progression
- `ai_service.py` — AI wave generation
- `hex_pathfinding.py`, `upgrade_provider.py` — Map and upgrade mechanics

**persistence/** — SQLite (async) via `database.py`; state serialized to/from YAML (`state_load.py`, `state_save.py`); replays stored compressed.

**network/** — WebSocket routing (`router.py`, `handlers.py`) and REST models (`rest_api.py`).

**loaders/** — Parse YAML configs into typed models (`game_config_loader.py`, `item_loader.py`).

**models/** — Dataclasses/pydantic models for all game entities (`items.py`, etc.).

### Configuration (`python_server/config/`)

All game balance lives in YAML:
- `game.yaml` — Timings, resource rates, era effects
- `buildings.yaml`, `structures.yaml`, `critters.yaml` — Entity definitions
- `ai_waves.yaml` — AI wave definitions across 9 eras (Stone → Future)
- `artefacts.yaml`, `knowledge.yaml` — Tech tree content
- `maps/default.yaml` — Default map

Live game state: `state.yaml` (auto-saved). Restart state: `state_restart.yaml`.

### Frontend (`web/`)

Single-page app, no build step. `js/app.js` + `js/router.js` form the SPA shell. Views are in `js/views/`. API calls go through `js/api.js` (WebSocket) and `js/rest.js` (HTTP).

Developer tools are at `web/tools/` (balance tuner, effect tester, replay viewer, etc.).

### Key Design Patterns

- **Slot-based wave spawning**: waves have a slot capacity; critters consume 1+ slots. See `battle_service._step_wave()`.
- **Effects dict**: tower effects (burn, slow) are stored as `effects.burn_duration`, `effects.burn_dps`, etc. in config and models.
- **Async throughout**: backend uses `asyncio`; tests use `pytest-asyncio`.
