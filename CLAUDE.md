# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Language

**Project language is English.** This applies to:
- All UI text, labels, messages, button text, and placeholders
- All code identifiers, variable names, constants, and function names
- All comments, docstrings, and documentation
- All YAML config keys and section comments
- No German words anywhere in the codebase

## Frontend Data Principle

The backend owns all game data. The frontend is a display layer only — it must not recalculate or derive values that the backend already computes (e.g. combat stats, XP thresholds, era effects). Always have the backend include the computed value in its API response and display it directly in the frontend.

**Exception:** Optimistic updates (e.g. immediately reflecting a user action before the server responds) may compute new values locally, provided the next server response overwrites them.

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

## Playwright E2E Tests

**Prod is read-only.** Never run Playwright tests against the prod environment (`localhost:8000` / `localhost:8080`). Tests create user accounts and mutate state.

Use the dev environment and clean up after:
```bash
cd web && BASE_URL=http://localhost:8100 API_URL=http://localhost:8180 npx playwright test
```

After the test run, delete the smoke test user from dev:
```bash
curl -s -X DELETE http://localhost:8180/api/admin/user/smoke_test_user \
  -H "Authorization: Bearer $(cat data/dev/admin_token 2>/dev/null)"
```

Or use the cleanup script: `web/e2e/cleanup.sh`

## Frontend Build (Vite)

The SPA uses [Vite](https://vitejs.dev/) for bundling. Node ≥20 required (use NVM).

```bash
# One-time setup
export NVM_DIR="$HOME/.nvm" && . "$NVM_DIR/nvm.sh"   # load NVM
cd web && npm install

# Development — serves raw files from web/, no build step needed
npm run dev          # Vite dev server on :5173 (proxies /api + /ws to :8080)

# Production bundle — output to web/dist/
npm run build        # hashed assets in web/dist/
```

Set `BUILD_MODE=production` to make the web server (`web/fastapi_server.py`) serve
`web/dist/` instead of raw source. Default is `dev` (raw files, no build needed).

> **IMPORTANT — both dev and prod environments use `BUILD_MODE=production`** (set in
> `docker-compose.dev.yml` and `docker-compose.prod.yml`). This means the server always
> serves `web/dist/`, **not** raw source files. Any JS/CSS change that "doesn't appear"
> after deploy is almost certainly because the Vite build was not re-run first.
> **Always run build + deploy together:**
> ```bash
> export NVM_DIR="$HOME/.nvm" && . "$NVM_DIR/nvm.sh"
> cd web && npm run build && cd .. && ./deploy.sh dev
> ```
> Never assume raw file edits are visible in the browser without rebuilding.

After changing JS/CSS files: re-run `npm run build` before deploying.

**API documentation** lives in `docs/API.md`. The file `web/api.html` is auto-generated from it by `web/scripts/build-api-page.mjs`, which runs automatically as part of `npm run build`. Never edit `web/api.html` directly — all changes must go into `docs/API.md`.

When adding new image assets (JPG/PNG sprites): run `npm run assets:optimize` to
generate WebP siblings. The build step runs this automatically. Skip PWA icons
(`apple-touch-icon.png`, `icon-192.png`, `icon-512.png`) — those must stay PNG.

## Frontend Shared Utilities (`web/js/lib/format.js`)

All formatting logic lives in `web/js/lib/format.js`. Do not inline formatting elsewhere.

| Function | Purpose |
|---|---|
| `fmtEffort(n)` | Numbers with K/M suffix |
| `fmtSecs(s)` | Seconds → `1h 2m 3s` |
| `fmtEffectRow(key, value)` | Two-column HTML row: `<span>icon label:</span><span>+value</span>` — for overlays/detail panels |
| `fmtEffectsInline(effects)` | Compact comma string: `"💰 +3.6/h, 🎭 +5%"` — for card previews |
| `fmtTowerEffects(effects)` | Tower combat effects: burn / slow / splash |

## nginx API Routing

nginx uses a regex whitelist to proxy `/api/*` paths to the gameserver. When adding
a **new REST endpoint**, always add its prefix to the whitelist in `nginx.conf.example`
(both the dev and prod server blocks) and reload nginx:

```
location ~ ^/api/(auth|empire|...|YOUR_NEW_PREFIX)(/|$)
```

After editing `nginx.conf.example`:
```bash
sudo cp nginx.conf.example /etc/nginx/sites-available/empire1 && sudo nginx -t && sudo systemctl reload nginx
```

Symptom if forgotten: endpoint returns 404 from the webserver instead of the gameserver,
even though `curl localhost:8180/api/your-endpoint` works fine.

## Adding Python Packages

1. Add to `python_server/pyproject.toml` under `dependencies`
2. Run `uv lock` in the repo root to update `python_server/uv.lock`
3. Run `bash deploy.sh prod` (or `dev`) — Docker runs `uv sync --frozen` during build, so the lockfile must be committed before deploying

Never install with `pip install` alone — it won't update the lockfile and the package will be missing in Docker.

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
- `artifacts.yaml`, `knowledge.yaml` — Tech tree content
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

### Era Key Naming — 2 Systems

Two era key formats exist. Do not mix them:

| System | Example | Used in |
|--------|---------|---------|
| **Lowercase** | `stone`, `middle_ages`, `renaissance` | `ERA_ORDER`, `get_current_era()`, `era_effects` dict keys, `game.yaml`, `ERA_LABELS_EN` |
| **UPPERCASE** | `STONE_AGE`, `MIDDLE_AGES`, `INDUSTRIAL` | `era:` field in item YAMLs (`knowledge.yaml`, `buildings.yaml`, etc.), `ERA_ITEM_TO_INDEX` |

The lowercase form is the canonical runtime format. The UPPERCASE form only appears in item YAML `era:` fields and `ERA_ITEM_TO_INDEX`.  
Travel offsets are stored as legacy flat fields: `stone_travel_offset`, `middle_ages_travel_offset`, etc. in `GameConfig`.

### Upgrade System

- **Item upgrades** (`item_upgrades: dict[iid, dict[stat, level]]`) live on `Empire`.
- **Price formula**: `base_cost × (total_levels_on_iid + 1)²` — base cost from `game.yaml item_upgrade_base_costs[era_index]`.
- Era index for structures/critters is built at startup in `main.py` (`_item_era_index`) by parsing YAML section comments.
- Structure stats: `damage`, `range`, `reload`, `effect_duration`, `effect_value` (+2–3% per level).
- Critter stats: `health`, `speed`, `armour` (+2% per level).
- Applied in `battle_service._step_armies()` at spawn time (normal waves) and `_make_critter_from_item()` (spawn-on-death).


### Language in text

 All text in the front-end should be written in american english 