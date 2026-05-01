# REFACTORING.md — Prototype-to-Production Hardening Guide for Coding Agents

> **This file is written for AI coding agents** (Claude Code, Cursor, Aider, etc.).
> Humans can read it, but every section is optimized for agent consumption: explicit
> file paths, exact verification commands, atomic tasks with clear pre/post conditions.

---

## 1. Purpose & Audience

This document instructs an AI coding agent on how to take **Empire1** — a working
prototype of a multiplayer tower-defense / empire-building game — from "demo-grade"
to **production-ready** in incremental, verifiable steps.

The codebase is healthy for a prototype:

- ~14,635 LOC Python, 50+ pytest test files (~500 KB of tests)
- Pydantic v2 models for REST validation
- mypy `strict = true` and ruff configured (but not enforced)
- async throughout (asyncio + aiosqlite + websockets)

But it has critical gaps for production: secrets in code, no CI/CD, no Docker, no
log rotation, no migrations, god modules, no frontend build, no rate limits.

**Read this file first** before touching any code. It contains the order, the
conventions, and the anti-goals.

---

## 2. How To Use This Document

1. **Pick one task** from a phase whose dependencies are already done.
2. **Read the entire task entry** — Why, Files, Steps, Verification, Done When.
3. **Execute the Steps** in order. Each step ends in a runnable state.
4. **Run the Verification** commands exactly as listed. Do not skip.
5. **Commit** with the conventional message (see §3.3).
6. **Move to the next task** — never bundle multiple tasks into one commit.

If a verification fails, **do not push forward**. Diagnose, fix, re-verify.
Use `git revert <sha>` if a task is unsalvageable; tasks are atomic by design.

This guide uses the **Strangler Fig pattern**: new code grows alongside the old,
the old is deleted only when the new is proven. Combined with the **Boy Scout
rule**: leave the codebase a little better with every commit.

---

## 3. Conventions

### 3.1 Anatomy of an Atomic Task

Every task in this document follows this exact schema:

```
### T<phase>.<n> <Title>
- Why: 1–2 lines linking the gap to user-visible/operational risk.
- Files: exact absolute paths; new files marked NEW.
- Depends-on: [T-ids that must land first].
- Steps: numbered, atomic edits; each step ends in a runnable state.
- Verification: shell commands an agent can run unattended.
- Done When: bulleted observable post-conditions.
- Risks & Rollback: known footguns; `git revert <sha>` is always safe.
- Out of Scope: explicit non-goals.
```

If you need to do something that does not fit a single task entry, **stop and
ask the user** before fragmenting the work — do not invent a new task on the fly.

### 3.2 Verification Commands (canonical set)

Every task verification draws from this canonical command set. Memorize them:

```bash
# Lint
rtk ruff check python_server/

# Type check
rtk mypy python_server/src

# Run all tests (full suite, ~1-2 min)
./run_tests.sh

# Run a scoped test file
./run_tests.sh tests/test_<area>.py

# Run a single test by name match
./run_tests.sh --match=<pattern>

# Coverage
./run_tests.sh --cov

# Restart servers
./restart.sh gameserver
./restart.sh webserver
./restart.sh gameserver stop

# Probe REST
rtk curl -fsS http://localhost:8000/api/admin/status

# Probe WebSocket (requires wscat: npm i -g wscat)
wscat -c ws://localhost:8765
```

Task-specific verifications (e.g. `grep -R "change-in-prod" python_server/`) are
listed inside each task and **must be run in addition to** the canonical set
relevant to that task's surface area.

### 3.3 Commit & Branch Conventions

- **Branch name**: `refactor/T<id>-<slug>` — e.g. `refactor/T1.1-jwt-fail-fast`
- **Commit message**: `refactor(T<id>): <imperative summary>` — e.g.
  `refactor(T1.1): remove JWT_SECRET fallback, fail fast on missing env`
- **One task = one commit** (or one PR). Never bundle.
- **Co-author trailer**: append the standard `Co-Authored-By:` trailer for the
  agent that did the work, if the project requires attribution.
- **Never** use `--no-verify`. If pre-commit fails, fix the cause, do not bypass.

### 3.4 Merge-Conflict Strategy for God-Module Splits

Splitting a 3000-line file (Phase 3) is conflict-prone. Procedure:

1. **Freeze the source file** — announce in the PR title and ask reviewers not
   to merge other edits to that file until the split lands.
2. **Single PR** — do the entire split in one PR. Do not split the split.
3. **Branches in flight** that touch the source file rebase via
   `git rerere` (enable with `git config rerere.enabled true`); conflicts are
   import-only and resolve mechanically.
4. **Functional behavior unchanged** — split tasks must not refactor logic;
   they only move code. Behavioral changes belong in a follow-up commit.

---

## 4. Anti-Goals — DO NOT DO THESE

These are explicit non-goals. Doing any of them counts as task failure.

- **Do NOT rewrite modules from scratch.** Split-in-place using Strangler Fig.
- **Do NOT delete or rewrite existing tests.** Only add. A failing test on the
  current branch is a signal, not a target.
- **Do NOT modify game-balance YAMLs** in `python_server/config/*.yaml`
  (game.yaml, buildings.yaml, structures.yaml, critters.yaml, ai_waves.yaml,
  artefacts.yaml, knowledge.yaml, maps/*.yaml). These are content, not code.
- **Do NOT introduce frameworks** beyond this allow-list:
  FastAPI, pydantic v2, structlog, slowapi, Alembic, argon2-cffi, Vite,
  Playwright, ESLint/Prettier, sharp/imagemin, uv, pytest plugins already in
  pyproject.toml.
- **Do NOT change the WebSocket wire format.** Pydantic models added in T2.8
  validate, they don't reshape. The frontend `js/api.js` must keep working
  unchanged.
- **Do NOT touch `restart.sh` semantics.** Verification depends on its current
  contract (start, stop, restart, PID files, log files at known paths).
- **Do NOT bypass CI** with `--no-verify` or by editing workflow files to skip
  steps.
- **Do NOT commit secrets**, even temporarily. Use `.env` (gitignored) and
  `.env.example` (committed).
- **Do NOT change game logic** while doing a refactor task. If you find a bug,
  open a separate ticket; do not fix it in the same commit.

---

## 5. Repo Map & Existing Tooling Inventory

### 5.1 Layout

```
empire1/
├── python_server/              # Game + REST backend
│   ├── pyproject.toml          # ruff, mypy strict, pytest configured
│   ├── config/                 # YAML game balance — DO NOT MODIFY in refactor tasks
│   │   ├── game.yaml
│   │   ├── buildings.yaml
│   │   ├── structures.yaml
│   │   ├── critters.yaml
│   │   ├── ai_waves.yaml
│   │   ├── knowledge.yaml
│   │   ├── artefacts.yaml
│   │   └── maps/
│   ├── src/gameserver/
│   │   ├── main.py
│   │   ├── engine/             # Core game loop, services
│   │   ├── network/            # handlers.py (god), rest_api.py (god), jwt_auth.py, auth.py, rest_models.py
│   │   ├── persistence/        # database.py, state_load.py, state_save.py
│   │   ├── loaders/            # YAML → typed models
│   │   ├── models/             # Pydantic / dataclasses
│   │   └── util/
│   ├── tests/                  # 50+ pytest files — DO NOT DELETE OR REWRITE
│   ├── state.yaml              # Live game state (auto-saved)
│   └── gameserver.db           # SQLite
├── web/                        # Frontend SPA, no build step
│   ├── index.html              # Has hardcoded relicsnrockets.io × 6
│   ├── manifest.json           # Has hardcoded domain
│   ├── fastapi_server.py       # Static-file server, port 8000
│   ├── css/style.css           # 3345 lines, monolithic
│   ├── js/
│   │   ├── app.js, router.js   # SPA shell
│   │   ├── api.js              # WebSocket client
│   │   ├── rest.js             # HTTP client
│   │   └── views/              # defense.js (2256 lines, god), army.js, status.js, ...
│   └── tools/                  # Dev tools (balance.html, status.html)
├── restart.sh                  # Process lifecycle — DO NOT MODIFY
├── run_tests.sh                # Test runner — already supports --match, --cov, --failfast
└── CLAUDE.md                   # Existing project instructions
```

### 5.2 Tooling Already Configured (Use, Do Not Replace)

- **ruff** — `pyproject.toml [tool.ruff]`, line-length 100, py39 target
- **mypy strict** — `pyproject.toml [tool.mypy]`, `strict = true`
- **pytest + pytest-asyncio** — `asyncio_mode = "auto"`, `testpaths = ["tests"]`
- **pytest-cov** — coverage available via `./run_tests.sh --cov`
- **PyJWT** — token signing/verification (do not swap for python-jose)
- **pydantic v2** — input validation (use for all new models)

### 5.3 Reference Patterns to Imitate

When you create a new file, copy the style from these existing patterns:

| Pattern | Reference file | Imitate when |
|---------|----------------|--------------|
| HTTP request/response models | [`rest_models.py`](../python_server/src/gameserver/network/rest_models.py) | Defining new pydantic schemas (T2.8 WS messages) |
| FastAPI route style | [`rest_api.py`](../python_server/src/gameserver/network/rest_api.py) | Splitting routes into `routers/` (T3.2) |
| Async SQLite usage | [`persistence/database.py`](../python_server/src/gameserver/persistence/database.py) | Any new DB code |
| Async test fixtures | [`tests/conftest.py`](../python_server/tests/conftest.py) | New test files |
| Service-style class | [`engine/battle_service.py`](../python_server/src/gameserver/engine/battle_service.py) | Adding new service classes |

---

## 6. Phase 1 — Foundation: Secrets, Env, CI

**Goal**: Stop the bleeding. Remove secrets from code, externalize config, gate
every future change with CI. Phase 1 must complete before Phase 2 begins; the
later phases assume CI is green.

### T1.1 Fail-fast JWT_SECRET

- **Why**: `python_server/src/gameserver/network/jwt_auth.py:33` has
  `JWT_SECRET = os.environ.get("JWT_SECRET", "e3-game-server-secret-key-change-in-prod")`.
  The fallback string is leaked publicly in source — a deployed instance with
  unset env var silently uses a known secret, defeating auth entirely.
- **Files**:
  - `/home/eem/empire1/python_server/src/gameserver/network/jwt_auth.py`
  - `/home/eem/empire1/.env.example` — **NEW**
- **Depends-on**: none
- **Steps**:
  1. In `jwt_auth.py`, replace the `os.environ.get(..., default)` call with:
     ```python
     JWT_SECRET = os.environ["JWT_SECRET"]  # raises KeyError on startup if missing
     ```
  2. Add a module-level docstring noting the env var is required.
  3. Create `.env.example` at repo root with `JWT_SECRET=replace-with-32-byte-random-hex`
     and a comment showing how to generate one (`python -c "import secrets; print(secrets.token_hex(32))"`).
  4. Confirm `.env` is in `.gitignore` (add if missing).
  5. Set `JWT_SECRET` in your local `.env` and source it before restarting.
- **Verification**:
  ```bash
  rtk grep -n "change-in-prod" python_server/src/gameserver/network/jwt_auth.py   # → no match
  unset JWT_SECRET && python -c "from gameserver.network import jwt_auth"          # → KeyError
  export JWT_SECRET=$(python -c "import secrets; print(secrets.token_hex(32))")
  ./run_tests.sh tests/  # all green
  ./restart.sh gameserver && rtk curl -fsS http://localhost:8000/  # 200
  ```
- **Done When**:
  - No fallback string in source.
  - Importing `jwt_auth` without `JWT_SECRET` set raises immediately.
  - `.env.example` exists; `.env` is gitignored.
  - Tests pass with `JWT_SECRET` set.
- **Risks & Rollback**: Tests that import jwt_auth without setting the env will
  break. Update `tests/conftest.py` to set a test secret. `git revert` if needed.
- **Out of Scope**: Rotating production secrets (operational, not code).

### T1.2 Purge Certs from Git History & Rotate

- **Why**: TLS certificates and VAPID keys were committed and remain in git
  history (`cert_relicsnrockets.io.crt`, `fullchain.pem`,
  `intermediate_relicsnrockets.io.crt`, `root_relicsnrockets.io.crt`,
  `server.csr`, `vapid_*.pem`). Anyone with repo read access can decrypt
  past traffic and impersonate VAPID push.
- **Files**:
  - All `*.crt`, `*.pem`, `*.csr`, `vapid_*.pem` in repo root and `certs/`.
  - `/home/eem/empire1/.gitignore`
- **Depends-on**: none
- **Steps**:
  1. **Confirm with the user before history rewrite** — this requires force-push
     and breaks all open PRs. Offer two paths: (a) `git filter-repo` with full
     history rewrite, or (b) accept the leak, rotate certs, add to .gitignore
     going forward (lower-risk for active teams).
  2. If path (a): run `git filter-repo --invert-paths --path-glob '*.pem' --path-glob '*.crt' --path-glob '*.csr'`. Force-push. Notify all collaborators.
  3. Either path: confirm `.gitignore` excludes `*.pem`, `*.crt`, `*.csr`,
     `certs/`, `fullchain.pem`.
  4. Generate new certs (Let's Encrypt) and new VAPID key pair. Store outside
     the repo (e.g. `/etc/letsencrypt/live/...`, `/etc/empire1/vapid/`).
  5. Add env vars `TLS_CERT_PATH`, `TLS_KEY_PATH`, `VAPID_PRIVATE_KEY_PATH`,
     `VAPID_PUBLIC_KEY_PATH` to `.env.example`.
- **Verification**:
  ```bash
  rtk git ls-files | rtk grep -E '\.(pem|crt|csr)$'       # → no matches
  rtk git log --all --full-history -- '*.pem' '*.crt'      # if path (a): no matches
  ```
- **Done When**:
  - No cert/key files tracked.
  - New certs deployed and old ones revoked at issuer.
  - .env.example references the new env vars.
- **Risks & Rollback**: History rewrite is irreversible. Coordinate with the
  team. Path (b) is acceptable if the leaked certs are already revoked.
- **Out of Scope**: Setting up cert auto-renewal (operational).

### T1.3 Externalize Domain & Site Config

- **Why**: `relicsnrockets.io` is hardcoded in 6+ places in
  `web/index.html` (canonical, og:url, og:image ×2, twitter:image, JSON-LD)
  and `web/manifest.json`. Staging/dev environments serve wrong canonical URLs;
  domain change is a 7-place edit.
- **Files**:
  - `/home/eem/empire1/web/index.html`
  - `/home/eem/empire1/web/manifest.json`
  - `/home/eem/empire1/web/fastapi_server.py`
  - `/home/eem/empire1/.env.example`
  - `/home/eem/empire1/python_server/src/gameserver/settings.py` — **NEW**
- **Depends-on**: T1.1 (env var pattern established)
- **Steps**:
  1. Create `settings.py` using `pydantic_settings.BaseSettings` (already in
     pydantic v2 ecosystem; if not installed, add `pydantic-settings>=2.0`):
     ```python
     class Settings(BaseSettings):
         site_url: str = "http://localhost:8000"
         site_name: str = "Relics & Rockets"
         model_config = SettingsConfigDict(env_file=".env")
     ```
  2. In `web/fastapi_server.py`, render `index.html` and `manifest.json`
     through Jinja2 (FastAPI ships with it) injecting `{{ site_url }}`.
  3. Replace all 6 occurrences of `relicsnrockets.io` in
     `web/index.html` with `{{ site_url }}` (without `https://` prefix where
     the URL needs templating, with prefix where it doesn't).
  4. Same for `web/manifest.json` if it contains the domain.
  5. Add `SITE_URL=http://localhost:8000` and `SITE_NAME="Relics & Rockets"` to `.env.example`.
- **Verification**:
  ```bash
  rtk grep -rn "relicsnrockets.io" web/   # → no matches in source HTML/JSON; OK in /assets binary refs
  SITE_URL=http://staging.example.com ./restart.sh webserver
  rtk curl -s http://localhost:8000/ | rtk grep "staging.example.com"   # → matches
  ./run_tests.sh
  ```
- **Done When**:
  - No occurrences of `relicsnrockets.io` in HTML/JSON/JS source.
  - `SITE_URL` env var changes the rendered canonical URL.
- **Risks & Rollback**: Caching might mask changes during testing — disable
  browser cache. `git revert` is safe.
- **Out of Scope**: i18n, multi-tenant deployments.

### T1.4 Replace SHA-256 Password Hash with argon2

- **Why**: `auth.py` hashes passwords with SHA-256 (no salt). Rainbow-table
  attacks recover any common password instantly. Argon2 is the OWASP-recommended
  default in 2025+.
- **Files**:
  - `/home/eem/empire1/python_server/src/gameserver/network/auth.py`
  - `/home/eem/empire1/python_server/pyproject.toml` (add `argon2-cffi>=23.0`)
  - `/home/eem/empire1/python_server/src/gameserver/persistence/database.py`
    (only if password column shape changes)
- **Depends-on**: T1.5 (CI must catch regressions)
- **Steps**:
  1. Add `argon2-cffi>=23.0` to `[project.dependencies]`.
  2. In `auth.py`, introduce `_hasher = argon2.PasswordHasher()`.
  3. `hash_password(plain) -> str` returns `_hasher.hash(plain)`.
  4. `verify_password(plain, stored) -> bool`:
     - If `stored.startswith("$argon2")`: `_hasher.verify(stored, plain)`.
     - Else (legacy SHA-256): verify legacy, then **re-hash and persist**
       under argon2 (lazy migration). Return True.
  5. Add a flag column or schema migration only if needed (probably not — the
     argon2 string is self-identifying).
  6. Add tests: legacy verification still works; new logins are stored as
     argon2; double-verification is a no-op.
- **Verification**:
  ```bash
  rtk ruff check python_server/
  rtk mypy python_server/src
  ./run_tests.sh --match=auth
  ./run_tests.sh tests/test_account.py
  ```
- **Done When**:
  - New passwords are stored as `$argon2id$...` strings.
  - Existing SHA-256 hashes still verify and are upgraded on next login.
  - All auth tests pass.
- **Risks & Rollback**: Failed migration of legacy hashes locks users out.
  Keep the legacy verification branch in place for at least one release.
- **Out of Scope**: Forcing all users to reset (an operational decision).

### T1.5 Add `.github/workflows/ci.yml`

- **Why**: There is no CI. Lint, type-check, and test failures only surface in
  local runs. Every merge risks regressions.
- **Files**:
  - `/home/eem/empire1/.github/workflows/ci.yml` — **NEW**
- **Depends-on**: T1.1 (CI needs `JWT_SECRET` as a GitHub secret to run tests)
- **Steps**:
  1. Workflow runs on `pull_request` and `push` to `main`.
  2. Matrix: python 3.12 (production target), ubuntu-latest.
  3. Steps: checkout → setup-python → `pip install -e python_server[dev]` →
     `ruff check python_server/` → `mypy python_server/src` → `./run_tests.sh`.
  4. Set `JWT_SECRET` from repo secret.
  5. Cache pip downloads.
  6. Upload coverage report as artifact (does not gate yet — that's T5.3).
- **Verification**:
  ```bash
  # Push a branch with the workflow:
  rtk git push -u origin refactor/T1.5-ci
  gh pr create
  gh pr checks   # → all green
  ```
- **Done When**:
  - CI runs on every PR.
  - A PR that introduces a ruff or mypy error fails the check.
  - A PR that breaks a test fails the check.
- **Risks & Rollback**: First run will likely surface latent issues. Fix them
  in follow-up commits — do not relax checks. `git revert` of the workflow
  itself if a fundamental config issue exists.
- **Out of Scope**: Frontend CI (Phase 4), coverage gating (T5.3), deploy.

### T1.6 Dockerfile + docker-compose.yml

- **Why**: The only deployment mechanism is `restart.sh`. There is no
  reproducible build, no isolation from host packages, no resource limits.
- **Files**:
  - `/home/eem/empire1/Dockerfile` — **NEW** (multi-stage)
  - `/home/eem/empire1/docker-compose.yml` — **NEW**
  - `/home/eem/empire1/.dockerignore` — **NEW**
- **Depends-on**: T1.3 (env config), T1.8 (lockfile)
- **Steps**:
  1. Multi-stage Dockerfile:
     - Stage 1 (`builder`): `python:3.12-slim`, install `uv`, copy lockfile,
       `uv sync --frozen --no-dev`.
     - Stage 2 (`runtime`): `python:3.12-slim`, copy site-packages from builder,
       copy source. Run as non-root user `app`. `EXPOSE 8000 8765`.
  2. `.dockerignore` excludes `.git`, `.venv`, `tests/`, `__pycache__`,
     `*.log`, `state.yaml`, `gameserver.db`, `certs/`, `*.pem`.
  3. `docker-compose.yml`: services `gameserver` (8765) and `webserver` (8000),
     volume mounts for `state.yaml` and `gameserver.db`, env_file `.env`.
- **Verification**:
  ```bash
  docker compose build
  docker compose up -d
  rtk curl -fsS http://localhost:8000/   # 200
  docker compose exec gameserver whoami  # → app (non-root)
  docker compose down
  ```
- **Done When**:
  - `docker compose up` brings up both services.
  - Image runs as non-root.
  - Image size is under 250 MB.
- **Risks & Rollback**: Volume mounts for state can cause permission issues —
  ensure `app` user owns the data dir. If broken, `docker compose down -v`.
- **Out of Scope**: Kubernetes manifests, image registry push, CDN.

### T1.7 `.pre-commit-config.yaml`

- **Why**: Local checks are inconsistent across contributors. Pre-commit
  enforces the same gates CI runs, before commits are made.
- **Files**:
  - `/home/eem/empire1/.pre-commit-config.yaml` — **NEW**
- **Depends-on**: T1.5 (CI defines the canonical gates pre-commit mirrors)
- **Steps**:
  1. Hooks: `ruff` (with `--fix`), `ruff-format`, `mypy` (project-scoped),
     `detect-secrets`, `check-added-large-files` (max 500 KB), `check-yaml`,
     `end-of-file-fixer`, `trailing-whitespace`.
  2. README snippet: `pip install pre-commit && pre-commit install`.
- **Verification**:
  ```bash
  pre-commit run --all-files
  echo "AKIAIOSFODNN7EXAMPLE" >> /tmp/leak.py && rtk git add /tmp/leak.py
  pre-commit run   # → detect-secrets blocks
  ```
- **Done When**:
  - `pre-commit install` succeeds.
  - All current files pass.
  - A staged file with a secret pattern is blocked.
- **Risks & Rollback**: Existing files may fail formatting — run
  `pre-commit run --all-files` once and commit fixes as a separate commit
  before merging the config.
- **Out of Scope**: Husky / JS-side hooks (Phase 4).

### T1.8 Lockfile via uv

- **Why**: `pyproject.toml` declares `>=` for every dep with no upper bounds and
  no lockfile. Two installs minutes apart can produce different dep graphs.
- **Files**:
  - `/home/eem/empire1/python_server/pyproject.toml`
  - `/home/eem/empire1/python_server/uv.lock` — **NEW** (committed)
  - `/home/eem/empire1/run_tests.sh` (update install line)
  - CI workflow from T1.5
- **Depends-on**: T1.5 (CI uses the lockfile)
- **Steps**:
  1. `pip install uv`.
  2. `cd python_server && uv lock`.
  3. Add upper bounds to dependencies in pyproject.toml that are known to be
     conservative (e.g. `fastapi>=0.100,<0.200`). Don't over-constrain.
  4. Update CI to `uv sync --frozen` instead of `pip install -e .[dev]`.
  5. Document `uv sync` and `uv lock --upgrade` in CLAUDE.md or README.
- **Verification**:
  ```bash
  cd python_server && uv sync --frozen
  uv pip list --frozen | rtk head
  ./run_tests.sh
  ```
- **Done When**:
  - `uv.lock` is committed.
  - CI uses `uv sync --frozen`.
  - Local `uv sync` reproduces an identical environment.
- **Risks & Rollback**: A frozen lock can pin a CVE-affected version. Schedule
  `uv lock --upgrade` monthly (recurring task — see CLAUDE.md).
- **Out of Scope**: Switching from pip to uv for runtime; uv is build-time only.

### Phase 1 — Definition of Done

- [ ] No secret literals or `change-in-prod` strings in source.
- [ ] `.env.example` lists every required env var.
- [ ] `.gitignore` excludes `.env`, certs, keys.
- [ ] `argon2id` is the default password hash; legacy SHA-256 still verifies.
- [ ] `.github/workflows/ci.yml` runs ruff + mypy + pytest on every PR.
- [ ] `docker compose up` brings up both services running as non-root.
- [ ] `pre-commit run --all-files` passes.
- [ ] `python_server/uv.lock` is committed and CI uses `uv sync --frozen`.

---

## 7. Phase 2 — Hardening: Errors, Logging, Migrations, Limits

**Goal**: The system survives in production. Logs don't fill disks, errors
don't disappear, schema changes are reversible, abusive clients are rate-limited.
Phase 2 requires Phase 1 (CI must be green to gate every change here).

### T2.1 Rotating Log Handlers

- **Why**: `gameserver.log` (1.9 MB) and `webserver.log` (20 MB) grow without
  bound. A long-running instance fills disk and crashes.
- **Files**:
  - `/home/eem/empire1/python_server/src/gameserver/main.py` (logging setup)
  - `/home/eem/empire1/web/fastapi_server.py`
- **Depends-on**: T1.5 (CI green)
- **Steps**:
  1. Replace `logging.basicConfig(filename=...)` with a
     `logging.handlers.TimedRotatingFileHandler(when="midnight", backupCount=14, utc=True)`.
  2. Add a parallel `StreamHandler` to stdout (Docker captures stdout; T1.6
     compose).
  3. Same for the webserver log.
- **Verification**:
  ```bash
  ./restart.sh gameserver
  rtk ls -la gameserver.log*   # only one file initially
  # After midnight (or trigger via test): gameserver.log.<date> appears
  ```
- **Done When**:
  - Log handler is rotating.
  - stdout also receives logs (visible via `docker compose logs`).
- **Risks & Rollback**: Old `gameserver.log` keeps growing if rotation isn't
  installed. Rotate manually once after deploy.
- **Out of Scope**: Shipping logs to a remote sink (Loki/Datadog).

### T2.2 Structured Logging + Request-ID Middleware

- **Why**: Plain-text logs are unsearchable. Tracing a single user's request
  across game server + web server is impossible.
- **Files**:
  - `/home/eem/empire1/python_server/pyproject.toml` (add `structlog>=24.0`)
  - `/home/eem/empire1/python_server/src/gameserver/util/logging.py` — **NEW**
  - `/home/eem/empire1/python_server/src/gameserver/main.py`
  - `/home/eem/empire1/python_server/src/gameserver/network/rest_api.py`
- **Depends-on**: T2.1
- **Steps**:
  1. Configure structlog with `JSONRenderer` in production, `ConsoleRenderer`
     in dev (decided by env var `LOG_FORMAT=json|console`).
  2. Add a FastAPI middleware that:
     - Reads `X-Request-ID` header or generates `uuid4()`.
     - Binds it to `structlog.contextvars`.
     - Echoes it back in response headers.
  3. Same for WebSocket: generate a `connection_id`, bind for the lifetime of
     the connection.
  4. Replace existing `logger.info(...)` calls' string interpolation with
     keyword fields where it adds clarity (don't flood; targeted edits only).
- **Verification**:
  ```bash
  LOG_FORMAT=json ./restart.sh gameserver
  rtk curl -fsS -H "X-Request-ID: test-123" http://localhost:8000/api/admin/status
  rtk grep "test-123" gameserver.log   # → JSON line with request_id field
  ```
- **Done When**:
  - JSON logs in prod, console logs in dev.
  - Every REST request has a `request_id` field.
  - Every WS connection has a `connection_id` field.
- **Risks & Rollback**: structlog setup at the wrong import time can swallow
  early logs. Initialize before any other logger usage in `main.py`.
- **Out of Scope**: OpenTelemetry tracing.

### T2.3 `/health` and `/health/ready`

- **Why**: Load balancers and orchestrators need cheap liveness/readiness
  endpoints. `/api/admin/status` requires auth and is too heavy.
- **Files**:
  - `/home/eem/empire1/python_server/src/gameserver/network/rest_api.py`
- **Depends-on**: T1.5
- **Steps**:
  1. `GET /health` → `{"status": "ok"}` always 200 (liveness — process alive).
  2. `GET /health/ready` → 200 only if SQLite is reachable
     (`SELECT 1` succeeds) and the game loop has ticked in the last 5 seconds.
  3. Both endpoints are unauthenticated; document that they leak only liveness.
- **Verification**:
  ```bash
  rtk curl -fsS http://localhost:8000/health        # 200 {"status":"ok"}
  rtk curl -fsS http://localhost:8000/health/ready  # 200 with checks
  # Stop the game loop and confirm /health/ready returns 503.
  ```
- **Done When**: Both endpoints respond as specified, unauthenticated.
- **Risks & Rollback**: `/health/ready` checks must be cheap (<50 ms). If
  they're slow, simplify.
- **Out of Scope**: Startup probes.

### T2.4 `/metrics` Prometheus Endpoint

- **Why**: No visibility into request rate, latency, error rate, game tick
  duration, active connections.
- **Files**:
  - `/home/eem/empire1/python_server/pyproject.toml` (add `prometheus-client>=0.20`)
  - `/home/eem/empire1/python_server/src/gameserver/util/metrics.py` — **NEW**
  - `/home/eem/empire1/python_server/src/gameserver/network/rest_api.py`
- **Depends-on**: T2.3
- **Steps**:
  1. Define metrics: `requests_total{path,method,status}`,
     `request_duration_seconds`, `ws_connections_active`,
     `game_tick_duration_seconds`, `db_query_duration_seconds`.
  2. Mount `/metrics` (use `prometheus_client.make_asgi_app()`).
  3. Add a tiny middleware that records request duration and status by route.
- **Verification**:
  ```bash
  rtk curl -fsS http://localhost:8000/metrics | head -30
  # Hit some endpoints, then re-query — counters increase.
  ```
- **Done When**:
  - `/metrics` exposes a Prometheus-format text response.
  - Counters increment under load.
- **Risks & Rollback**: High-cardinality labels (per-user) blow up memory.
  Stick to path/method/status.
- **Out of Scope**: Grafana dashboards, alerting rules.

### T2.5 Alembic Migrations (Baseline)

- **Why**: Schema changes happen via ad-hoc `ALTER TABLE` in `database.py`.
  No way to reproduce a schema in a fresh env, no rollback.
- **Files**:
  - `/home/eem/empire1/python_server/pyproject.toml` (add `alembic>=1.13`,
    `sqlalchemy>=2.0` if not already there for Alembic only — do NOT migrate
    queries to SQLAlchemy in this task)
  - `/home/eem/empire1/python_server/alembic.ini` — **NEW**
  - `/home/eem/empire1/python_server/alembic/env.py` — **NEW**
  - `/home/eem/empire1/python_server/alembic/versions/0001_baseline.py` — **NEW**
- **Depends-on**: T1.5
- **Steps**:
  1. `alembic init alembic`. Configure for SQLite + async.
  2. Generate baseline by inspecting the existing `gameserver.db` schema and
     hand-writing a `0001_baseline.py` that creates the same tables.
  3. Stamp existing prod DB: `alembic stamp head` (no-op DDL, just records the
     baseline as already applied).
  4. Document migration commands in CLAUDE.md.
- **Verification**:
  ```bash
  cd python_server && alembic upgrade head    # no-op on existing db
  rtk rm -f /tmp/test.db && DATABASE_URL=sqlite:////tmp/test.db alembic upgrade head
  rtk sqlite3 /tmp/test.db ".schema" | diff - <(rtk sqlite3 gameserver.db ".schema")  # → empty diff
  ```
- **Done When**:
  - Baseline migration creates the current schema in a fresh DB.
  - Prod DB is stamped at baseline.
  - CLAUDE.md documents `alembic revision --autogenerate -m "..."` workflow.
- **Risks & Rollback**: A wrong baseline corrupts fresh installs. Verify with
  the diff command above. Never run `alembic downgrade` on prod without backup.
- **Out of Scope**: Migrating existing queries to SQLAlchemy ORM.

### T2.6 Backup Automation for DB + state.yaml

- **Why**: A corrupted `gameserver.db` or `state.yaml` is an unrecoverable loss.
  No backups exist today.
- **Files**:
  - `/home/eem/empire1/scripts/backup.sh` — **NEW**
  - Crontab snippet in CLAUDE.md
- **Depends-on**: T1.6 (runs in-container)
- **Steps**:
  1. `backup.sh`: `sqlite3 gameserver.db ".backup /backups/gameserver-$(date +%F-%H%M).db"`,
     plus `cp state.yaml /backups/state-$(date +%F-%H%M).yaml`.
  2. Retention: keep last 7 daily, 4 weekly, 6 monthly. Use `find -mtime +N -delete`.
  3. Document cron entry: `0 * * * * /app/scripts/backup.sh`.
- **Verification**:
  ```bash
  ./scripts/backup.sh && rtk ls /backups/
  # Restore test:
  rtk sqlite3 /tmp/restored.db ".restore /backups/gameserver-<latest>.db"
  ```
- **Done When**:
  - Hourly backup script is executable.
  - Retention policy applied.
  - Restore from backup is documented and tested.
- **Risks & Rollback**: SQLite `.backup` is safe under writes; do NOT use `cp`
  on the live DB.
- **Out of Scope**: Off-host backup destination (S3/GCS) — operational.

### T2.7 Tighten Bare-Except Blocks

- **Why**: 10+ `except Exception:` clauses swallow errors silently in
  `state_load.py`, `message_store.py`, `database.py`, `ai_service.py`,
  `game_loop.py`. Real bugs hide as "logged-and-continued."
- **Files**: catalogue with `grep -rn "except Exception:" python_server/src/`.
- **Depends-on**: T2.2 (structured logging makes the new exception fields useful)
- **Steps**:
  1. For each occurrence: identify the *expected* exception type. Narrow to
     it. Re-raise unexpected.
  2. If the exception is genuinely "log-and-continue" (e.g. one player's bad
     state shouldn't crash the loop), keep `Exception` but **always** log
     `exc_info=True` and add a metric counter
     (`errors_swallowed_total{location}`).
  3. Add tests that exercise each branch where reasonable.
- **Verification**:
  ```bash
  rtk ruff check python_server/   # ruff has BLE rules — enable if not already
  rtk grep -rn "except Exception:" python_server/src/   # → only the audited ones, with comments
  ./run_tests.sh
  ```
- **Done When**:
  - Each remaining `except Exception:` has a comment explaining why and a
    metric increment.
  - Specific exceptions are caught where the type is known.
- **Risks & Rollback**: Narrowing too aggressively causes new crashes in prod.
  Stage in a pre-prod environment first.
- **Out of Scope**: Replacing exceptions with Result types.

### T2.8 Pydantic Models for WebSocket Messages

- **Why**: WS handlers parse dicts via runtime `.get(...)` calls. Schema
  changes silently break clients; no IDE autocomplete; no static guarantees.
- **Files**:
  - `/home/eem/empire1/python_server/src/gameserver/network/ws_models.py` — **NEW**
  - `/home/eem/empire1/python_server/src/gameserver/network/handlers.py`
- **Depends-on**: T1.5
- **Steps**:
  1. Pattern after `rest_models.py`. Define one base model `WSMessage` with
     `type: Literal[...]` and a discriminated-union dispatch.
  2. Define one model per existing message type in `handlers.py`.
  3. Wrap the inbound parser at the top of `handlers.dispatch(...)`:
     `WSMessage.model_validate_json(raw)`.
  4. Add tests for: valid messages, invalid types, missing required fields.
- **Verification**:
  ```bash
  mypy python_server/src   # strict — catches type errors
  ./run_tests.sh tests/test_message_exchange.py
  # Manual: send a malformed WS frame; server should reply with a typed error.
  ```
- **Done When**:
  - Every WS inbound message type has a pydantic model.
  - `handlers.dispatch` validates before doing anything else.
  - Wire format is unchanged (test against existing `js/api.js`).
- **Risks & Rollback**: Strict validation rejects messages that the prototype
  silently accepted. Run a soak test with the actual frontend before merging.
- **Out of Scope**: Splitting handlers into modules (T3.1).

### T2.9 Rate Limiting

- **Why**: No rate limit on REST or WS. A single malicious client can DoS
  signup, login, or the message queue.
- **Files**:
  - `/home/eem/empire1/python_server/pyproject.toml` (add `slowapi>=0.1.9`)
  - `/home/eem/empire1/python_server/src/gameserver/network/rest_api.py`
  - `/home/eem/empire1/python_server/src/gameserver/network/handlers.py`
    (custom token-bucket per `connection_id`)
- **Depends-on**: T2.2 (request_id / connection_id available)
- **Steps**:
  1. REST: add `Limiter(key_func=get_remote_address)`. Apply
     `@limiter.limit("5/minute")` to `/auth/login`, `/auth/signup`,
     `@limiter.limit("60/minute")` to general REST.
  2. WS: implement a token-bucket keyed on `connection_id` (e.g. 30 msg/sec
     burst, 10 msg/sec sustained). Reject and log when exceeded.
  3. Return `429 Too Many Requests` with Retry-After.
- **Verification**:
  ```bash
  for i in {1..10}; do rtk curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8000/auth/login -X POST -d '{"username":"x","password":"x"}'; done
  # → first 5 = 401, next 5 = 429
  ```
- **Done When**:
  - Login/signup return 429 after threshold.
  - WS dropping floods is logged and a metric increments.
- **Risks & Rollback**: Aggressive limits hurt legitimate bursts at game start.
  Tune per environment via env vars.
- **Out of Scope**: Distributed rate limiting (single-instance is fine for now).

### T2.10 CSP & Security Headers Middleware

- **Why**: No Content-Security-Policy. XSS payloads (e.g. injected via
  username) can exfiltrate auth tokens.
- **Files**:
  - `/home/eem/empire1/web/fastapi_server.py`
  - `/home/eem/empire1/python_server/src/gameserver/network/rest_api.py`
- **Depends-on**: T1.3 (templated SITE_URL needed for CSP `connect-src`)
- **Steps**:
  1. Add a middleware that sets:
     - `Content-Security-Policy`: default-src 'self'; img-src 'self' data:;
       script-src 'self'; style-src 'self' 'unsafe-inline' fonts.googleapis.com;
       connect-src 'self' wss://{ws_host} https://{site_host};
       font-src fonts.gstatic.com; frame-ancestors 'none'.
     - `X-Content-Type-Options: nosniff`
     - `Referrer-Policy: strict-origin-when-cross-origin`
     - `Permissions-Policy: geolocation=(), microphone=(), camera=()`
     - `Strict-Transport-Security: max-age=31536000; includeSubDomains` (TLS only)
  2. Test in browser DevTools: no console violations on the main flows
     (login, build, defend, attack).
- **Verification**:
  ```bash
  rtk curl -sI http://localhost:8000/ | rtk grep -E "Content-Security|X-Content|Referrer|Strict-Transport"
  ```
- **Done When**:
  - Headers present on every HTML response.
  - No console CSP violations during a full play loop.
- **Risks & Rollback**: CSP can break `style="..."` inline attributes used
  throughout the codebase. Audit all `innerHTML` template literals before
  enforcing — may need `'unsafe-inline'` for `style-src` initially, scheduled
  for tightening in Phase 4.
- **Out of Scope**: Subresource Integrity (SRI) for CDN fonts (Phase 4).

### Phase 2 — Definition of Done

- [ ] Logs rotate; no file exceeds 14 days of retention.
- [ ] All logs are JSON in prod, with `request_id` / `connection_id`.
- [ ] `/health`, `/health/ready`, `/metrics` are live and unauthenticated.
- [ ] Alembic baseline applied; new migrations workflow documented.
- [ ] `backup.sh` runs hourly; restore tested.
- [ ] No bare `except Exception:` without a comment + metric.
- [ ] Every WS message type validated by a pydantic model.
- [ ] Rate limiting enforced on auth endpoints and WS.
- [ ] Security headers present; no CSP violations on golden-path flows.

---

## 8. Phase 3 — Decomposition: Split God-Modules

**Goal**: No single file over 1000 LOC. Each module has one responsibility.
Phase 3 requires Phase 2 (typed WS messages and CI gates make the splits
mechanical).

### Strangler-Fig Procedure (apply to T3.1 – T3.4)

1. **Create the new package structure** alongside the god file. The god file
   keeps working.
2. **Move one cohesive group at a time** (e.g. all `auth_*` handlers).
3. **Re-export from the god file** so external imports still work:
   ```python
   from .handlers.auth import handle_login, handle_signup  # noqa: F401
   ```
4. **Run the full test suite after every move.**
5. **Once everything is moved**: replace the god file with a thin re-export
   shim, or delete it entirely if no external import path depends on its
   presence.
6. **Behavioral changes are forbidden** during the split — only relocation.

### T3.1 Split `handlers.py`

- **Why**: 3521 lines, dispatching every WS message. Reading or modifying
  any single handler requires loading the entire file.
- **Files**:
  - `/home/eem/empire1/python_server/src/gameserver/network/handlers.py`
    (becomes a thin dispatcher)
  - `/home/eem/empire1/python_server/src/gameserver/network/handlers/`
    — **NEW** package
  - `/home/eem/empire1/python_server/src/gameserver/network/handlers/auth.py` — **NEW**
  - `/home/eem/empire1/python_server/src/gameserver/network/handlers/military.py` — **NEW**
  - `/home/eem/empire1/python_server/src/gameserver/network/handlers/economy.py` — **NEW**
  - `/home/eem/empire1/python_server/src/gameserver/network/handlers/social.py` — **NEW**
  - `/home/eem/empire1/python_server/src/gameserver/network/handlers/admin.py` — **NEW**
- **Depends-on**: T2.8 (typed WS messages), T1.5 (CI green)
- **Steps**: follow the Strangler-Fig procedure above. Group by domain:
  - **auth**: login, signup, logout, password reset, account
  - **military**: army, attack, defense, battle, military_request
  - **economy**: build, research, upgrade, item_upgrade, knowledge_steal,
    artefact_steal
  - **social**: messages, threads, alliances
  - **admin**: status, debug, time travel
  Each new file has a `register(dispatcher)` function. The thin dispatcher
  imports all and calls them.
- **Verification**:
  ```bash
  rtk wc -l python_server/src/gameserver/network/handlers.py   # < 200 lines
  rtk wc -l python_server/src/gameserver/network/handlers/*.py # each < 1000
  ./run_tests.sh   # full suite green
  ./restart.sh gameserver
  # Smoke test the frontend: login, build, attack — all work.
  ```
- **Done When**:
  - `handlers.py` is a thin dispatcher (< 200 LOC).
  - Each domain file is self-contained.
  - All tests green; manual smoke green.
- **Risks & Rollback**: Circular imports between domains. Resolve by injecting
  the service object rather than importing other handlers. `git revert` if it
  spirals.
- **Out of Scope**: Refactoring within a domain file.

### T3.2 Split `rest_api.py`

- **Why**: 1595 lines of mixed routes.
- **Files**:
  - `/home/eem/empire1/python_server/src/gameserver/network/rest_api.py`
  - `/home/eem/empire1/python_server/src/gameserver/network/routers/__init__.py` — **NEW**
  - `/home/eem/empire1/python_server/src/gameserver/network/routers/auth.py` — **NEW**
  - `/home/eem/empire1/python_server/src/gameserver/network/routers/empire.py` — **NEW**
  - `/home/eem/empire1/python_server/src/gameserver/network/routers/admin.py` — **NEW**
- **Depends-on**: T3.1
- **Steps**: follow Strangler-Fig. Each router file exposes
  `router = APIRouter(prefix="/...")`. `rest_api.py` becomes a thin app factory
  that mounts each router with `app.include_router(...)`.
- **Verification**:
  ```bash
  rtk wc -l python_server/src/gameserver/network/rest_api.py   # < 300
  rtk curl -fsS http://localhost:8000/health
  rtk curl -fsS http://localhost:8000/openapi.json | jq '.paths | keys | length'
  # Path count unchanged from before split.
  ```
- **Done When**:
  - `rest_api.py` is < 300 LOC.
  - OpenAPI path list is unchanged.
  - All tests green.
- **Risks & Rollback**: Forgotten `include_router` drops endpoints silently.
  Diff the OpenAPI path list before and after.
- **Out of Scope**: Changing route URLs.

### T3.3 Split `web/js/views/defense.js`

- **Why**: 2256 lines mixing tile placement, rendering, animation, sound,
  network, and UI events.
- **Files**:
  - `/home/eem/empire1/web/js/views/defense.js` (thin entrypoint)
  - `/home/eem/empire1/web/js/views/defense/` — **NEW** directory
  - `/home/eem/empire1/web/js/views/defense/render.js` — **NEW**
  - `/home/eem/empire1/web/js/views/defense/placement.js` — **NEW**
  - `/home/eem/empire1/web/js/views/defense/animation.js` — **NEW**
  - `/home/eem/empire1/web/js/views/defense/events.js` — **NEW**
- **Depends-on**: T1.5
- **Steps**: Strangler-Fig in JS — each new file uses ES modules
  (`export function ...`); the thin entrypoint imports them.
- **Verification**:
  ```bash
  rtk wc -l web/js/views/defense.js   # < 200
  ./restart.sh webserver
  # Manual: open the defense view, place a tower, fight a wave — no regressions.
  ```
- **Done When**:
  - `defense.js` is a thin entrypoint.
  - All sub-modules under 600 LOC.
  - Manual smoke green.
- **Risks & Rollback**: Without a build step, every new file is one more HTTP
  request. After T4.1 (Vite), this is a non-issue. Until then, keep the count
  reasonable (4–6 files).
- **Out of Scope**: Other view files (status.js, army.js) — can follow the
  same pattern in follow-up tasks if useful.

### T3.4 Split `web/css/style.css`

- **Why**: 3345 lines. Hard to find rules; cascade conflicts.
- **Files**:
  - `/home/eem/empire1/web/css/style.css` (becomes the entry that `@import`s
    or is built from partials)
  - `/home/eem/empire1/web/css/_base.css` — **NEW** (resets, typography, vars)
  - `/home/eem/empire1/web/css/_layout.css` — **NEW** (shell, nav, grids)
  - `/home/eem/empire1/web/css/_components.css` — **NEW** (buttons, cards)
  - `/home/eem/empire1/web/css/views/_login.css` — **NEW**
  - `/home/eem/empire1/web/css/views/_defense.css` — **NEW** (and others)
- **Depends-on**: T3.3 (gives a clearer mapping of components → views)
- **Steps**:
  1. Group rules into the partials above.
  2. Until Vite arrives, use plain `@import` in `style.css` (extra HTTP
     requests are tolerable for a few partials; build will inline in T4.1).
  3. Run a visual diff on every page (Playwright snapshots if T4.3 done).
- **Verification**:
  ```bash
  rtk wc -l web/css/_*.css web/css/views/_*.css
  # Manual: every view looks identical to before the split.
  ```
- **Done When**:
  - No partial > 800 LOC.
  - All views render identically.
- **Risks & Rollback**: Cascade order matters — the `@import` order in
  `style.css` must match the original rule order for cascade ties.
- **Out of Scope**: CSS variables consolidation, dark mode, etc.

### Phase 3 — Definition of Done

- [ ] No Python file > 1000 LOC.
- [ ] No JS view file > 600 LOC.
- [ ] No CSS partial > 800 LOC.
- [ ] All tests green; manual smoke of all views green.
- [ ] OpenAPI path list unchanged.
- [ ] WebSocket message types unchanged.

---

## 9. Phase 4 — Frontend Build & Quality

**Goal**: The frontend has a build step, optimized assets, smoke tests, and
linting. Phase 4 requires T1.3 (templated domain) and T3.3 (split defense.js
makes bundling cleaner).

### T4.1 Add Vite (Vanilla Mode)

- **Why**: No bundling, no minification, no source maps, no tree-shaking.
  10+ JS modules load sequentially; total payload is unoptimized.
- **Files**:
  - `/home/eem/empire1/web/package.json` — **NEW**
  - `/home/eem/empire1/web/vite.config.js` — **NEW**
  - `/home/eem/empire1/web/.gitignore` (add `node_modules/`, `dist/`)
  - `/home/eem/empire1/restart.sh` (NO CHANGE — keep semantics)
  - `/home/eem/empire1/web/fastapi_server.py` (serve from `web/dist/` when
    `BUILD_MODE=production`)
- **Depends-on**: T3.3
- **Steps**:
  1. `npm create vite@latest` in a scratch dir, copy minimal vanilla template.
  2. Configure Vite multi-page (input: `index.html` + `tools/*.html`).
  3. Add npm scripts: `dev`, `build`, `preview`.
  4. Adjust `fastapi_server.py` to serve `web/dist/` in production mode and
     `web/` (raw) in dev. Default to dev for local.
  5. Document in CLAUDE.md: `cd web && npm install && npm run build`.
- **Verification**:
  ```bash
  cd web && npm install && npm run build
  rtk ls dist/   # bundled output
  BUILD_MODE=production ./restart.sh webserver
  rtk curl -fsS http://localhost:8000/   # 200, references hashed asset names
  ```
- **Done When**:
  - `npm run build` produces a hashed `dist/` bundle.
  - Production server serves the bundle.
  - Dev mode (raw files) still works for fast iteration.
- **Risks & Rollback**: HTML templating from T1.3 (Jinja2) must compose with
  Vite's HTML transform. Test the rendered HTML carefully.
- **Out of Scope**: TypeScript migration, framework adoption.

### T4.2 Asset Pipeline (sharp / imagemin)

- **Why**: `banner.jpg` 113 KB, `icon-512.png` 551 KB, `RnR.jpg` 292 KB.
  WebP versions would be 30–60% smaller. No compression today.
- **Files**:
  - `/home/eem/empire1/web/scripts/optimize-assets.mjs` — **NEW** (uses
    sharp via npm)
  - `/home/eem/empire1/web/package.json` (script `assets:optimize`)
  - `/home/eem/empire1/web/index.html` (use `<picture>` for WebP fallback)
- **Depends-on**: T4.1
- **Steps**:
  1. `npm i -D sharp`.
  2. Script generates `.webp` siblings for every `.jpg` / `.png` in
     `assets/`.
  3. Update `<img>` tags to `<picture>` with `<source type="image/webp">` +
     fallback `<img>`.
  4. Wire into Vite build hook.
- **Verification**:
  ```bash
  npm run assets:optimize
  rtk ls -la web/assets/*.webp   # exists
  npm run build
  # Lighthouse score on dist/index.html: image weight reduced
  ```
- **Done When**:
  - WebP siblings exist for all critical images.
  - HTML uses `<picture>` + fallback.
  - Lighthouse "image formats" passes.
- **Risks & Rollback**: Old browsers don't support WebP; the `<picture>`
  fallback handles it. Verify in Safari ≥14.
- **Out of Scope**: AVIF (marginal additional savings, more complexity).

### T4.3 Playwright Smoke Tests

- **Why**: Zero frontend tests. Every UI regression ships.
- **Files**:
  - `/home/eem/empire1/web/playwright.config.ts` — **NEW**
  - `/home/eem/empire1/web/tests/smoke.spec.ts` — **NEW**
  - `/home/eem/empire1/.github/workflows/ci.yml` (add e2e job)
- **Depends-on**: T4.1 (build output to test against)
- **Steps**:
  1. `npm i -D @playwright/test && npx playwright install --with-deps chromium`.
  2. Write smoke tests for: signup, login, build a structure, place a tower,
     compose an army, send an attack. One test per flow.
  3. Each test starts both servers via the existing `restart.sh` (or a
     Playwright `webServer` config).
  4. Add a `frontend-e2e` job in CI that runs after the build.
- **Verification**:
  ```bash
  cd web && npx playwright test
  # All flows green.
  ```
- **Done When**:
  - 5+ smoke tests cover golden-path flows.
  - CI runs them on every PR.
  - A regression in one of these flows fails CI.
- **Risks & Rollback**: Flaky network/timing makes tests fragile. Use
  `page.waitForResponse(...)` over `waitForTimeout`. Mark flakes with
  `test.fixme()` and open a follow-up — never disable silently.
- **Out of Scope**: Visual regression snapshots, mobile emulation.

### T4.4 ESLint + Prettier

- **Why**: No JS lint or format config. Style drifts.
- **Files**:
  - `/home/eem/empire1/web/.eslintrc.json` — **NEW**
  - `/home/eem/empire1/web/.prettierrc` — **NEW**
  - `/home/eem/empire1/web/package.json` (scripts `lint`, `format`)
  - `/home/eem/empire1/.pre-commit-config.yaml` (add eslint hook)
- **Depends-on**: T1.7
- **Steps**:
  1. `npm i -D eslint @eslint/js prettier eslint-config-prettier`.
  2. Use `eslint:recommended`. Don't be exotic.
  3. `npm run format` runs prettier across web/.
  4. Commit a one-time format pass as a separate commit.
  5. Add `npm run lint` to CI.
- **Verification**:
  ```bash
  cd web && npm run lint && npm run format -- --check
  ```
- **Done When**:
  - `npm run lint` passes on the whole tree.
  - Prettier formatting is uniform.
  - CI gates on lint.
- **Risks & Rollback**: Aggressive lint rules block the team. Stay close to
  defaults.
- **Out of Scope**: TypeScript, type-aware lint rules.

### Phase 4 — Definition of Done

- [ ] `npm run build` produces a hashed bundle in `web/dist/`.
- [ ] WebP variants exist for all critical images.
- [ ] Playwright smoke tests cover signup, login, build, attack.
- [ ] CI runs frontend lint + e2e on every PR.

---

## 10. Phase 5 — Polish

**Goal**: Tighten the gates that Phase 1–4 set as warnings.

### T5.1 Enforce mypy strict in CI

- **Why**: mypy is configured strict but errors are not currently a CI gate
  (T1.5 may report-only).
- **Files**: `/home/eem/empire1/.github/workflows/ci.yml`
- **Depends-on**: All previous phases (codebase clean enough)
- **Steps**:
  1. Run `mypy python_server/src` locally; address remaining errors.
  2. In CI, change mypy step from `continue-on-error: true` to default
     (failing on error).
- **Verification**: PR that introduces a type error fails CI.
- **Done When**: mypy step gates merges.
- **Out of Scope**: Strict mypy on the frontend.

### T5.2 Pin Upper Bounds + Lockfile Drift Check

- **Why**: T1.8 added a lockfile but pyproject ranges are still wide.
- **Files**: `python_server/pyproject.toml`, `.github/workflows/ci.yml`
- **Depends-on**: T1.8
- **Steps**:
  1. Add reasonable upper bounds (`fastapi>=0.100,<0.200`,
     `pydantic>=2.0,<3.0`, etc.).
  2. CI step: `uv lock --check` (fails if lockfile is out of date vs
     pyproject).
  3. Schedule a monthly recurring task (e.g. via `/schedule`) to run
     `uv lock --upgrade` and open a PR.
- **Verification**:
  ```bash
  cd python_server && uv lock --check   # → green
  ```
- **Done When**: PRs that change deps without updating the lock file fail CI.
- **Out of Scope**: Renovate / Dependabot setup (operational).

### T5.3 Coverage Gate

- **Why**: Coverage is collected but not enforced. Untested PRs slip through.
- **Files**: `.github/workflows/ci.yml`, `python_server/pyproject.toml`
- **Depends-on**: All previous (test coverage is meaningful)
- **Steps**:
  1. Compute current coverage: `./run_tests.sh --cov`.
  2. Set the gate to current floor (e.g. `--cov-fail-under=78`).
  3. Configure per-file thresholds for new code (use `coverage.xml` + `diff-cover`
     for delta coverage).
- **Verification**: A PR that drops coverage below the floor fails CI.
- **Done When**: Coverage gate is in CI.
- **Out of Scope**: 100% coverage targets.

### Phase 5 — Definition of Done

- [ ] mypy strict gates merges.
- [ ] Lockfile drift gates merges.
- [ ] Coverage floor gates merges.

---

## 11. Cross-Cutting Playbooks

### 11.1 Working with `state.yaml` During a Migration

`state.yaml` is the live game state — auto-saved, hot. Never edit live.

```bash
# 1. Snapshot
./restart.sh gameserver stop
rtk cp state.yaml state.yaml.bak

# 2. Modify on a copy
rtk cp state.yaml state.new.yaml
# ... transform state.new.yaml ...

# 3. Verify
rtk yq eval '.empires | length' state.yaml
rtk yq eval '.empires | length' state.new.yaml   # diff sanity-checked

# 4. Atomic swap
rtk mv state.new.yaml state.yaml
./restart.sh gameserver
# 5. Watch logs
rtk tail -f gameserver.log
```

### 11.2 Adding an Env Var (one source of truth)

Every new env var touches **all five** of these in one PR:

1. `.env.example` — documented with comment + example value
2. `python_server/src/gameserver/settings.py` — added to `Settings` model
3. `docker-compose.yml` — passed through `env_file` (no change usually) or
   explicit
4. `.github/workflows/ci.yml` — if needed for tests, added as `env:` from
   secrets
5. `CLAUDE.md` or `README.md` — env var table updated

### 11.3 Introducing a New Dependency

Checklist before `pip install` / `npm install`:

- [ ] License is OSI-approved and compatible.
- [ ] Last release within 12 months (or active main branch).
- [ ] No known CVEs (run `pip-audit` / `npm audit`).
- [ ] On the allow-list in §4 (or get explicit user approval).
- [ ] Lockfile is updated (`uv lock` / `npm install`).
- [ ] Dockerfile rebuild succeeds.
- [ ] CI is green.

### 11.4 Rolling Back a Task

Every task is one commit. Rollback is:

```bash
rtk git log --oneline | rtk head     # find the SHA
rtk git revert <sha>                 # creates an inverse commit
./run_tests.sh                       # confirm baseline
rtk git push
```

If the revert itself fails (rare — split tasks shouldn't), open an issue and
ask the user before continuing.

---

## 12. Glossary & References

### 12.1 File-Path Index

Critical files referenced by tasks above:

- [`python_server/src/gameserver/network/jwt_auth.py`](../python_server/src/gameserver/network/jwt_auth.py) — T1.1
- [`python_server/src/gameserver/network/auth.py`](../python_server/src/gameserver/network/auth.py) — T1.4
- [`python_server/src/gameserver/network/handlers.py`](../python_server/src/gameserver/network/handlers.py) — T2.8, T3.1
- [`python_server/src/gameserver/network/rest_api.py`](../python_server/src/gameserver/network/rest_api.py) — T3.2
- [`python_server/src/gameserver/network/rest_models.py`](../python_server/src/gameserver/network/rest_models.py) — REFERENCE PATTERN, do not modify
- [`python_server/src/gameserver/main.py`](../python_server/src/gameserver/main.py) — T2.1, T2.2
- [`python_server/pyproject.toml`](../python_server/pyproject.toml) — T1.4, T1.8, T2.2, T2.4, T2.5, T2.9
- [`web/index.html`](../web/index.html) — T1.3
- [`web/manifest.json`](../web/manifest.json) — T1.3
- [`web/js/views/defense.js`](../web/js/views/defense.js) — T3.3
- [`web/css/style.css`](../web/css/style.css) — T3.4
- [`web/fastapi_server.py`](../web/fastapi_server.py) — T1.3, T2.1, T2.10, T4.1
- [`restart.sh`](../restart.sh) — DO NOT MODIFY
- [`run_tests.sh`](../run_tests.sh) — verification entrypoint

### 12.2 Verification Command Cheat-Sheet

```bash
# Lint
rtk ruff check python_server/

# Type check
rtk mypy python_server/src

# Tests (full suite)
./run_tests.sh

# Tests (scoped)
./run_tests.sh tests/test_<area>.py
./run_tests.sh --match=<pattern>

# Coverage
./run_tests.sh --cov

# Servers
./restart.sh gameserver
./restart.sh webserver
./restart.sh gameserver stop

# Pre-commit
pre-commit run --all-files

# Frontend (post-T4.1)
cd web && npm run lint
cd web && npm run build
cd web && npx playwright test

# Docker (post-T1.6)
docker compose build && docker compose up -d
```

### 12.3 Existing Scripts (DO NOT MODIFY semantics)

- `./run_tests.sh` — supports `--match=<pat>`, `--all`, `--quick`, `--cov`,
  `--cov-html`, `--failfast`, file paths.
- `./restart.sh <gameserver|webserver> [stop|restart]` — manages PIDs in
  `.gameserver.pid` / `.webserver.pid`, logs to `gameserver.log` /
  `webserver.log`. Tasks add to these logs but never change the entrypoint.

---

## Sources

This document was assembled from current best-practices research:

- [AGENTS.md specification](https://agents.md) — atomic-task structure, "README for agents".
- [Strangler Fig Pattern (Martin Fowler)](https://martinfowler.com/bliki/StranglerFigApplication.html) — incremental refactor over rewrite.
- [FastAPI Best Practices (zhanymkanov)](https://github.com/zhanymkanov/fastapi-best-practices) — domain-grouped routers, async pitfalls, error handling.
- [Production-Ready FastAPI Project Structure 2026](https://dev.to/thesius_code_7a136ae718b7/production-ready-fastapi-project-structure-2026-guide-b1g) — multi-stage Docker, non-root, layered architecture.
- [Claude Prompt Engineering Best Practices 2026](https://promptbuilder.cc/blog/claude-prompt-engineering-best-practices-2026) — explicit constraints, structured headings, golden test sets.

---

**End of guide.** When you complete a task, append a `[x]` to its phase's
Definition of Done checklist in this file as part of the same commit.
