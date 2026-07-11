# empire1

Multiplayer tower-defense / empire-building game ([relicsnrockets.io](https://relicsnrockets.io)).
Python asyncio game server (WebSocket + REST, FastAPI) with a Vite-bundled SPA
frontend, deployed via Docker in two environments (prod/dev) behind nginx.

## Quick start

```bash
./deploy.sh dev            # build + deploy dev stack (Docker)
./attach.sh dev            # follow dev gameserver logs
rtk run_tests.sh           # backend test suite
```

Frontend build (required before deploy after JS/CSS changes):

```bash
export NVM_DIR="$HOME/.nvm" && . "$NVM_DIR/nvm.sh"
cd web && npm run build && cd .. && ./deploy.sh dev
```

## Where to steer

Which file controls what — the levers for humans (and Claude):

| Lever | Location |
|---|---|
| Claude behavior rules (global) | `CLAUDE.md` |
| Claude behavior rules (scoped: frontend/backend/deploy) | `.claude/rules/*.md` |
| Repeatable workflows (deploy, e2e, verify) | `.claude/skills/*/SKILL.md` |
| Claude tool permissions | `.claude/settings.json` (shared), `.claude/settings.local.json` (personal) |
| Game balance (all of it) | `python_server/config/*.yaml` |
| AI wave definitions | `python_server/config/ai_waves.yaml` |
| Bot player behavior (spec, synced with code) | `ai_players/docs/strategies/*.md` |
| API documentation (single source of truth) | `docs/API.md` (generates `web/api.html`) |
| Backend package interfaces | `python_server/src/gameserver/*/INTERFACES.md` |
| Coding standards | `docs/CODINGGUIDELINE.md` |
| Planning / working notes | `tasks/*.md` (each has a status header) |
| nginx API whitelist | `nginx.conf.example` |

## Repository layout

- `python_server/` — game server (engine, persistence, network, YAML configs)
- `web/` — SPA frontend, developer tools (`web/tools/`), Playwright e2e
- `ai_players/` — autonomous bot players (dev only)
- `docs/` — project documentation, indexed in `docs/README.md`
- `scripts/` — balance/analysis utilities
- `data/{prod,dev}/` — persisted state and SQLite DB per environment

## Documentation

Full doc index: [docs/README.md](docs/README.md).
Claude Code guidance: [CLAUDE.md](CLAUDE.md).
