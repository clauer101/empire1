# AI-Assisted Engineering: Architecture, Tests, and Guardrails

This document describes the agent-oriented configuration and verification
systems that are present in this repository. It distinguishes committed
project instructions from local tooling and human operating rules: a written
rule is not necessarily enforced by a script, and a local-only hook is not
reproducible from a checkout.

## Runtime architecture

Relics & Rockets is a multiplayer tower-defense and empire-building game. The
gameserver owns authoritative game state and rules; the browser is a display
and interaction client, while autonomous test bots use the public REST API.

```text
Browser / Playwright                 Autonomous bots (dev)
        |                                      |
        +------------------+-------------------+
                           v
                    nginx (deployed)
                     /api and /ws
                           |
                           v
       gameserver: asyncio tick, FastAPI REST/WebSocket
                           |
                           v
              SQLite + YAML state snapshots

Browser static requests -> webserver -> Vite-built SPA (web/dist/)
```

- `python_server/` contains the authoritative game engine, async services,
  models, persistence, API/network layer, YAML loaders, and game configuration.
  The game loop advances on a 1000 ms tick. Package-level `INTERFACES.md` files
  describe backend public surfaces.
- `web/` contains a vanilla-JavaScript SPA. `app.js` and `router.js` provide the
  shell, views live in `js/views/`, REST and WebSocket clients live in `js/`,
  and Vite builds the deployable bundle into `web/dist/`.
- Prod and dev are separate Docker Compose stacks with separate ports, state,
  and database paths. nginx sends API/WebSocket traffic to the gameserver and
  static traffic to the webserver.
- `ai_players/` contains standalone, strategy-driven Python clients. They
  poll and mutate game state through the REST API; they are not part of the
  gameserver process and do not use an LLM. Their planner behavior is specified
  in `ai_players/docs/strategies/` and implemented in `ai_players/bot/planners/`.

## Test and quality architecture

There are independent test suites; they do not all run in CI today.

### Gameserver

- Tests are under `python_server/tests/` and use pytest, pytest-asyncio, and
  shared fixtures/factories from `conftest.py`. Coverage spans game mechanics,
  combat and waves, services, REST/routers, persistence, configuration and
  serialization, including integration-style tests.
- `python_server/pyproject.toml` sets `asyncio_mode = "auto"`, adds `src` to
  the import path, and configures coverage to require at least 66% of
  `gameserver`. Several infrastructure or integration-oriented modules are
  excluded from the coverage denominator; see `[tool.coverage.run].omit`.
- The root `run_tests.sh` runs Ruff, mypy, then pytest by default. It supports
  `--quick`, `--all`, `--match=PATTERN` (pytest `-k` selection), `--cov`,
  `--cov-html`, `--failfast`, `--no-lint`, and a test path. It runs pytest from
  `python_server/`; use paths relative to that directory when selecting files.
- GitHub Actions (`.github/workflows/ci.yml`) runs on pushes and pull requests
  to `main`. It checks the uv lockfile, installs Python 3.12 dependencies,
  runs Ruff and mypy, then runs pytest with the 66% coverage gate. It uploads
  coverage output even on failure. It does not currently run the frontend,
  Playwright, or bot-player suites.

### Frontend

- `web/tests/` contains Node-executable JavaScript unit tests for shared
  formatting, HTML escaping, era logic, income calculation, and speed logic.
  They use small in-file test harnesses and run directly with Node, for example
  `cd web && node tests/test_html.test.js`. `package.json` currently has no
  aggregate `test` script, and CI does not execute these tests.
- Playwright tests live in `web/e2e/`. The smoke suite covers signup, login,
  building view, defense canvas, army composer, known empires, and logout.
  Tests run sequentially in one Firefox worker, with one retry and a 45-second
  timeout; screenshots, video, traces, and an HTML report are retained as
  configured in `playwright.config.js`.
- E2E defaults target the dev webserver (`localhost:8100`) and gameserver
  (`localhost:8180`). The dev stack must be running. Tests create accounts and
  mutate server state; never target prod. `globalSetup.js` rejects an
  `API_URL` whose port is exactly `8080`; this is a narrow guard, not a general
  production-environment detector. Cleanup only deletes the fixed
  `smoke_test_user` and only when `ADMIN_PASS` is configured. If credentials
  are absent or teardown is interrupted, cleanup is not guaranteed. The
  signup smoke test also creates a timestamped account, which the teardown
  does not delete.

### Autonomous bot players

- `ai_players/tests/` is a separate pytest suite for planner selection,
  strategy state, army building, analysis, dispatch, and bot behavior. Run it
  from the bot project with `cd ai_players && python -m pytest tests/`.
- The bot suite is not part of `run_tests.sh` or the current GitHub Actions
  workflow. Do not use the gameserver runner with an `ai_players/tests/` path:
  it changes directory to `python_server/` before invoking pytest.
- Bots are configured for dev (`ai_players/config.yaml` defaults to
  `http://localhost:8180`) and their strategy docs are the behavior spec.
  `run_bot.py` refuses a non-localhost host by default, but this can be
  overridden with `--allow-remote` or by setting `SERVER_URL`; treat either as
  an explicit opt-out from the local-only guard. Bot state files contain
  persisted account credentials and should not be committed.

## Context and instruction layers

Instructions are layered so general constraints remain visible while domain
details are loaded only for matching paths.

- Root `CLAUDE.md` establishes American English, backend ownership of computed
  game values, RTK-prefixed shell commands, required backend verification,
  dev-only Playwright use, production deployment confirmation, and a compact
  architecture overview. It links to this document and to the scoped rules.
- `.claude/rules/backend.md` applies to `python_server/**`. It documents the
  two era-key naming systems and where each is valid; upgrade ownership,
  price formula, era indexing and application points; the `pyproject.toml` +
  `uv.lock` dependency workflow; and structlog configuration.
- `.claude/rules/frontend.md` applies to `web/**`. It requires Node 20+,
  explains the Vite dev/build distinction and that both deployed environments
  serve `web/dist/`, identifies generated API docs and asset optimization, and
  centralizes shared display-formatting utilities.
- `.claude/rules/deployment.md` applies repository-wide. It prohibits prod
  deployment without explicit user confirmation and direct writes to the live
  prod SQLite database; records deployment commands, state/database paths,
  frontend build requirements, live-log commands, and nginx's REST-prefix
  whitelist requirement.
- `web/CLAUDE.md` adds frontend layout and ownership pointers. `ai_players/CLAUDE.md`
  documents the bots' dev-only intent, strategy-spec synchronization, layout,
  and test command.
- There are no project-local custom agent definitions or hook scripts under
  `.claude/`; the project-specific agent behavior is supplied by these
  instruction files, the four skills, and the shared settings file.

Rules provide agent context and obligations; they do not, by themselves,
intercept shell commands or enforce operating-system access controls.

## Project skills

The four `SKILL.md` files in `.claude/skills/` encode repeatable workflows.
Each has a name and a description for discovery, followed by procedural
instructions; skills orchestrate existing commands rather than implement new
runtime capabilities.

### `verify-backend`

For every backend change, run the prescribed sequence and stop at the first
failure:

1. `.venv/bin/ruff check python_server/src/`
2. `rtk run_tests.sh` (which itself runs Ruff, mypy, and pytest unless lint is
   disabled)
3. `.venv/bin/pre-commit run --all-files` (Ruff, strict mypy with the project
   config, and detect-secrets)

The standalone mypy command requires
`--config-file=python_server/pyproject.toml` from the repository root or strict
configuration may not be applied. Do not bypass normal commit checks with
`--no-verify`. The deployment script has a narrow exception described below
for committing an automatically generated production backup archive.

### `deploy-dev`

Builds frontend assets and deploys dev as one operation: source NVM, run
`npm run build`, then `./deploy.sh dev`. The build also regenerates API/devlog/
fair-play pages, OpenAPI output, and optimized assets. It explicitly excludes
`prod` and `both`; it is intended for changes that should become visible on
dev. Logs can then be followed with `./attach.sh dev`.

### `e2e`

Runs `npx playwright test` from `web/` with explicit dev `BASE_URL` and
`API_URL`. The dev stack is a prerequisite. It warns against prod because the
tests create accounts and mutate state, and documents manual cleanup if
automatic teardown did not run. The technical port check and conditional
cleanup limitations are detailed above.

### `balancing`

Runs the headless real battle engine through `scripts/sim_random_maze.py` with
the project virtualenv; no server is needed. It documents class discovery,
random baseline trials, single-class counter matchups, fixed-side repetitions,
full per-era counter matrices, cross-era stress tests, and fixed maze lengths.
It also explains that tower filters are cumulative by era, critter filters are
native-era pools, and randomized results require multiple trials. Upgrade-level
sweeps and exporting auto-generated-maze results are explicitly marked as not
implemented by this workflow.

## Permission configuration and scope

`.claude/settings.json` is the shared project settings file. Its Bash
allowlist pre-authorizes `rtk git:*`, `rtk gain:*`, `rtk discover:*`, and two
specific catalog-integrity test invocations. It also adds
`/home/eem/.claude/hooks` and `/home/eem/.claude` as additional Claude Code
directories. These are Claude Code permission/context settings, not an OS
sandbox or a general security boundary; commands outside the allowlist may
still be run subject to the active permission mode and user approval.

`.claude/settings.local.json` is a machine/user-local file, not the shared
project contract. Its contents can vary by workstation and should not be
used to claim that all contributors have the same permissions.

## Deployment and data guardrails

The deploy script implements several operational protections, with important
failure modes that agents must understand:

- Before deploy or stop, `deploy.sh` queries the environment's admin status
  endpoint for active battles. It aborts by default if battles are found;
  `-w` waits, and `-f` proceeds intentionally. If the admin token is missing,
  the script warns and skips the check.
- Before stopping a running service, it attempts to POST
  `/api/admin/save-state`. If no token/server is available it skips this; if
  saving fails it warns but continues. This is a best-effort save, not a
  fail-closed guarantee.
- Before a production stop/deploy, it archives the production DB, state,
  bot states, admin token, and results under `data/backups/prod.tgz`, stages
  that file, and attempts a git commit before touching containers. The
  generated-archive commit uses `--no-verify` by design; this is narrower than
  bypassing hooks for source changes.
- Container shutdown sends a timed stop and can force-kill remaining
  containers. A `-f` deployment during a battle is therefore a destructive
  override.
- The live prod DB must never be edited directly while the server is running;
  doing so can break subsequent aiosqlite writes. Use the supported application
  or admin workflows.
- **Production confirmation is an agent/operator rule, not an interactive
  check in `deploy.sh`.** The script accepts prod/both without prompting. An
  agent must obtain explicit user confirmation before invoking either target.
- New REST prefixes must be added to the nginx regex whitelist in both server
  blocks of `nginx.conf.example`; otherwise a gameserver endpoint may work on
  its local port but return 404 through nginx.

## RTK and local integrations

The repository instructs agents to prefix bash commands with RTK and the
existing workflow documentation describes RTK as a Claude Code `PreToolUse`
optimization hook. The hook/configuration itself is referenced through the
external `/home/eem/.claude/` path, not defined by the committed project
files. RTK's presence and hook behavior therefore depend on workstation setup;
they are not reproducible from this repository alone.

## Operating principle

Automate routine, reversible checks and dev workflows; require a human for
production-impacting actions; and state whether each protection is a written
instruction, an application-level check, a best-effort script, or a local-only
integration. These safeguards supplement—not replace—review, testing, and
CI. The same quality gates apply regardless of whether code was written by a
person or an agent.
