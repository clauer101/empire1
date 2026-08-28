# empire1 — Relics & Rockets

[![CI](https://github.com/clauer101/empire1/actions/workflows/ci.yml/badge.svg)](https://github.com/clauer101/empire1/actions/workflows/ci.yml)

A multiplayer tower-defense / empire-building game, live at
[relicsnrockets.io](https://relicsnrockets.io). Solo full-stack project: an
asyncio game server driving real-time base building, army composition, and
tower-defense combat across nine historical eras, with a Vite-bundled SPA
frontend and a Docker-based dual-environment deployment pipeline.

This project was also built with Claude Code as a primary development
collaborator. The rules, skills, and permissions that make that collaboration
safe on a live production service — not just "I used an AI" — are documented
in [docs/AI_WORKFLOW.md](docs/AI_WORKFLOW.md).

## Architecture

```
                        ┌────────────────────┐
   Internet ──HTTPS──>  │       nginx        │
                        │(prod: 443, dev:80) │
                        └─────────┬──────────┘
                    ┌─────────────┼─────────────┐
              /api, /ws                    everything else
                    ▼                             ▼
          ┌───────────────────┐        ┌──────────────────────┐
          │     gameserver    │        │       webserver      │
          │ asyncio + FastAPI │        │  FastAPI static host │
          │ WebSocket + REST  │        │  serves Vite SPA     │
          │ 1000ms game tick  │        │  (web/dist/)         │
          └────────┬──────────┘        └──────────────────────┘
                   │
          ┌────────┴───────────┐
          │ SQLite (aiosqlite) │
          │ + YAML state       │
          │ + Alembic          │
          └────────────────────┘
```

Prod and dev are two independent stacks (separate Docker Compose projects,
ports, `.env` files, and data directories), sharing the same images built from
one Dockerfile. `ai_players/` runs autonomous bots against the dev stack's
public REST API for load and gameplay testing.

## Tech stack

- **Backend**: Python 3.12, `asyncio`, FastAPI (WebSocket + REST), Pydantic,
  aiosqlite, Alembic migrations, `structlog`
- **Frontend**: vanilla JS SPA, Vite 6 build
- **Infra**: Docker Compose, nginx, deployed behind Let's Encrypt TLS
- **Quality**: pytest + pytest-asyncio, ruff, mypy (strict), pre-commit,
  Playwright, GitHub Actions

## Engineering highlights

- **Slot-based wave spawning** — waves have a slot capacity rather than a flat
  unit count, so multi-slot critters properly consume capacity instead of
  being counted 1:1. See `battle_service._step_wave()`.
- **Effects as data, not code branches** — tower effects (burn, slow, splash,
  …) live in a uniform `effects.*` dict in both config and models, so new
  effect types don't require new combat-loop branches.
- **Deterministic 1000ms game tick** — all combat, wave progression, and AI
  behavior is driven by a single async tick in `game_loop.py`, keeping game
  state reproducible and testable.
- **Battle-aware deployment** — `deploy.sh` checks for in-progress battles via
  the admin API before stopping a server, so a routine deploy can't cut off a
  live fight (with explicit `-f`/`-w` overrides for when that's intentional).

## Testing & quality

```bash
.venv/bin/ruff check python_server/src/     # lint
rtk run_tests.sh                            # pytest + pytest-asyncio, 93 test files
.venv/bin/pre-commit run --all-files        # ruff + mypy --strict + detect-secrets
```

- Coverage gate enforced in CI: `pytest --cov=gameserver --cov-fail-under=66`.
- mypy runs in `strict` mode across `python_server/src`.
- Playwright end-to-end smoke tests run against an isolated dev environment
  only, with automatic test-account teardown after each run.
- GitHub Actions runs lint + mypy + the full test suite with coverage on every
  push/PR to `main` (see `.github/workflows/ci.yml`).

## Deployment

Two independent Docker Compose stacks (prod/dev) sit behind one nginx config
that whitelists REST API path prefixes and forwards everything else to the
static frontend host. `deploy.sh` handles both environments:

```bash
./deploy.sh dev             # build frontend + deploy dev stack
./deploy.sh prod            # build frontend + deploy prod stack (requires confirmation)
./deploy.sh dev stop        # save state and stop dev
./attach.sh dev             # follow dev gameserver logs
```

Every deploy saves in-memory game state before stopping a container; every
prod deploy additionally backs up the production database and commits the
backup to git before touching the running stack.

## AI-assisted development

`CLAUDE.md` plus scoped rules in `.claude/rules/`, three codified workflows in
`.claude/skills/`, and a layered tool-permission model form the actual
guardrails this project runs on when an AI agent is driving changes against a
service with real users and real data — including a purpose-built, publicly
available CLI ([RTK — Rust Token Killer](https://github.com/rtk-ai/rtk)) that
cuts the token cost of routine shell/git operations. Full writeup:
[docs/AI_WORKFLOW.md](docs/AI_WORKFLOW.md).

## Getting started

```bash
./deploy.sh dev             # build + deploy the dev stack (Docker)
./attach.sh dev             # follow dev gameserver logs
rtk run_tests.sh            # backend test suite
```

Frontend build (required before deploy after any JS/CSS change — both
environments serve the built `web/dist/`, never raw source):

```bash
export NVM_DIR="$HOME/.nvm" && . "$NVM_DIR/nvm.sh"
cd web && npm run build && cd .. && ./deploy.sh dev
```

## Repository layout

- `python_server/` — game server (engine, persistence, network, YAML configs)
- `web/` — SPA frontend, developer tools (`web/tools/`), Playwright e2e
- `ai_players/` — autonomous bot players (dev only)
- `docs/` — project documentation, indexed in [docs/README.md](docs/README.md)
- `scripts/` — balance/analysis utilities
- `data/{prod,dev}/` — persisted state and SQLite DB per environment

## Documentation

- Full doc index: [docs/README.md](docs/README.md)
- AI-assisted workflow: [docs/AI_WORKFLOW.md](docs/AI_WORKFLOW.md)
- Claude Code guidance: [CLAUDE.md](CLAUDE.md)

## License

Proprietary. This repository is shared publicly for portfolio and code-review
purposes only — no license is granted for reuse, modification, or
redistribution.
