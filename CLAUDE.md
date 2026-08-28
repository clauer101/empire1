# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.
For the human-readable story behind this file and the `.claude/` setup, see
[docs/AI_WORKFLOW.md](docs/AI_WORKFLOW.md).

Detailed, area-specific rules live in `.claude/rules/` (loaded automatically):
- `.claude/rules/frontend.md` — Vite build/deploy, shared utilities, assets, API docs
- `.claude/rules/backend.md` — era keys, upgrade system, Python packages
- `.claude/rules/deployment.md` — deploy scripts, nginx routing, state/DB paths

## Language

**Project language is American English.** This applies to all UI text, code identifiers,
comments, docstrings, documentation, and YAML config keys/comments. No German words
anywhere in the codebase.

## Frontend Data Principle

The backend owns all game data. The frontend is a display layer only — it must not
recalculate or derive values that the backend already computes (e.g. combat stats,
XP thresholds, era effects). Always have the backend include the computed value in
its API response and display it directly.

**Exception:** Optimistic updates may compute new values locally, provided the next
server response overwrites them.

## Shell Commands

Always prefix bash commands with `rtk` for token savings (e.g. `rtk git status`).

## Validating Code Changes

Run after every backend change, in order:

```bash
.venv/bin/ruff check python_server/src/     # 1. lint
rtk run_tests.sh                            # 2. tests (--match=NAME, path, --all, --quick, --cov, --failfast)
.venv/bin/pre-commit run --all-files        # 3. ruff + mypy + detect-secrets
```

Pre-commit runs automatically on `git commit`. Never use `--no-verify` to bypass it.

## Playwright E2E Tests

**Prod is read-only.** Never run Playwright tests against prod (`localhost:8000` /
`localhost:8080`) — tests create accounts and mutate state. Use dev:

```bash
cd web && BASE_URL=http://localhost:8100 API_URL=http://localhost:8180 npx playwright test
```

Test-user cleanup runs automatically via `web/e2e/globalTeardown.js`. Manual fallback:

```bash
curl -s -X DELETE http://localhost:8180/api/admin/user/smoke_test_user \
  -H "Authorization: Bearer $(cat data/dev/admin_token 2>/dev/null)"
```

## Deployment

**Never deploy to prod without explicit user confirmation.** Always default to dev.
Frontend changes require a Vite build before deploy — see `.claude/rules/frontend.md`
and `.claude/rules/deployment.md`.

## Architecture

Multiplayer tower-defense / empire-building game. Two servers per environment (prod/dev):

- **Game server** (`python_server/`) — asyncio WebSocket server + REST API (FastAPI). Entry: `gameserver.main:main`
- **Web server** (`web/fastapi_server.py`) — FastAPI serving the SPA static files on port 8000

nginx routes: API/WS → gameserver, static → webserver.
Prod: HTTPS on 443. Dev: HTTP on 80 only (`http://dev.relicsnrockets.io`).

### Backend (`python_server/src/gameserver/`)

Core game logic in `engine/`, driven by a 1000ms tick in `game_loop.py`
(`battle_service.py` = wave spawning + combat, `empire_service.py` = player state,
`ai_service.py` = AI waves). Persistence: async SQLite + YAML state snapshots,
Alembic migrations. WebSocket/REST in `network/`, YAML config loaders in `loaders/`,
entity models in `models/`.

**Each backend package has an `INTERFACES.md`** documenting its public surface —
read it before working in that package.

### Configuration (`python_server/config/`)

All game balance lives in YAML: `game.yaml` (timings, rates, era effects),
`buildings.yaml` / `structures.yaml` / `critters.yaml` (entities), `ai_waves.yaml`
(AI waves across 9 eras), `artifacts.yaml` / `knowledge.yaml` (tech tree),
`maps/default.yaml`.

### Frontend (`web/`)

Single-page app bundled with Vite (build required before deploy — see
`.claude/rules/frontend.md`). `js/app.js` + `js/router.js` form the SPA shell;
views in `js/views/`; API via `js/api.js` (WebSocket) and `js/rest.js` (HTTP).
Developer tools at `web/tools/`. Build scripts documented in `web/scripts/AGENTS.md`.

### AI Bot Players (`ai_players/`)

Autonomous bots playing via the public REST API (dev only). The strategy docs in
`ai_players/docs/strategies/` are the **spec** for the planner classes in
`ai_players/bot/planners/` and must stay in sync. See `ai_players/README.md` and
`ai_players/CLAUDE.md`.

### Key Design Patterns

- **Slot-based wave spawning**: waves have a slot capacity; critters consume 1+ slots. See `battle_service._step_wave()`.
- **Effects dict**: tower effects are stored as `effects.burn_duration`, `effects.burn_dps`, etc. in config and models.
- **Async throughout**: backend uses `asyncio`; tests use `pytest-asyncio`.

### Further Documentation

`docs/README.md` indexes all project docs (`API.md`, `CODINGGUIDELINE.md`,
`EFFECTSGUIDE.md`, …). `tasks/` holds working/planning notes, each with a status
header (active/stale/done).
