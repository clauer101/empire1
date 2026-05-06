# CODINGGUIDELINE.md — Empire1 Coding Standards

> Derived from REFACTORING.md and practical experience hardening this codebase
> from prototype to production (T1.1–T5.3). Follow these rules when writing
> NEW code so that no subsequent refactoring pass is needed.

---

## 1. Python — Type Annotations

### 1.1 Always annotate everything

Every function, method, and module-level variable must be fully typed.
mypy `strict = true` is enforced in CI — a PR that introduces a mypy error will fail.

```python
# BAD
def process(items, config=None):
    result = {}
    ...

# GOOD
from typing import Any
def process(items: list[Any], config: Any = None) -> dict[str, Any]:
    result: dict[str, Any] = {}
    ...
```

### 1.2 Never use bare generics

Always parametrize `dict`, `list`, `tuple`, `set`. Use `dict[str, Any]` when the value type
is mixed or unknown.

```python
# BAD
data: dict = {}
items: list = []
coords: tuple = (0, 0)

# GOOD
from typing import Any
data: dict[str, Any] = {}
items: list[str] = []
coords: tuple[int, int] = (0, 0)
```

### 1.3 `from __future__ import annotations`

Add this as the first import in every Python file. It enables postponed evaluation of
annotations, allowing forward references and cleaner syntax.

```python
from __future__ import annotations
```

### 1.4 Python version must match runtime everywhere

`pyproject.toml` must declare the actual Python version in all three places:

```toml
[project]
requires-python = ">=3.12"

[tool.ruff]
target-version = "py312"

[tool.mypy]
python_version = "3.12"
strict = true
```

Never set `python_version = "3.9"` when the server runs Python 3.12 — this causes CI and
local mypy to diverge silently (0 errors locally, 271 errors in CI).

### 1.5 `# type: ignore` must name the error code

Never use a blanket `# type: ignore`. Always specify:

```python
# BAD
import bcrypt  # type: ignore

# GOOD
import bcrypt  # type: ignore[import-not-found]
import pywebpush  # type: ignore[import-not-found]
```

### 1.6 `json.loads()` and similar `Any`-returning calls

Assign to a typed local variable before returning:

```python
# BAD — triggers no-any-return
return json.loads(raw)

# GOOD
result: dict[str, Any] = json.loads(raw)
return result
```

### 1.7 Optional service fields — narrow before closures

When a dataclass has `Optional[Service]` fields that are always set after init, add an
`assert` AND assign to a local non-optional variable before any nested function or closure.
mypy cannot narrow through closure boundaries.

```python
def make_router(services: Services) -> APIRouter:
    assert services.empire_service is not None
    empire_service = services.empire_service  # local non-optional alias

    @router.get("/api/empires")
    async def list_empires() -> dict[str, Any]:
        # Use empire_service, not services.empire_service (mypy can't narrow through closures)
        for empire in empire_service.all_empires.values():
            ...
```

### 1.8 `__all__` for underscore-prefixed re-exports

mypy strict treats names starting with `_` as unexported. If a module re-exports private
names for use by other modules, declare them in `__all__`:

```python
# auth.py
__all__ = [
    "handle_auth_request",
    "_build_empire_summary",   # explicitly exported for handler re-exports
    "_build_session_state",
    "_create_empire_for_new_user",
]
```

**Place `__all__` AFTER all definitions**, not at the top of the file. mypy resolves types
at definition time — a forward-declared `__all__` can cause resolution failures.

### 1.9 `__getattr__` in proxy modules returns `Any`

Module-level `__getattr__` must return `Any`, not `object`:

```python
# BAD — all dynamic lookups typed as `object` (not callable)
def __getattr__(name: str) -> object: ...

# GOOD
from typing import Any
def __getattr__(name: str) -> Any: ...
```

### 1.10 Dynamic attributes use `setattr`/`getattr`

Never set dynamic attributes directly on typed dataclass instances:

```python
# BAD — triggers attr-defined
attack._observers = set()
attack._observers.add(uid)

# GOOD
setattr(attack, '_observers', set())
getattr(attack, '_observers').add(uid)
```

---

## 2. Python — Module Architecture

### 2.1 No file over 1000 lines

Split large modules using the Strangler Fig pattern (see REFACTORING.md §9).
One responsibility per file.

### 2.2 Wildcard re-exports and `__all__`

If a module does `from submodule import *` to re-export, do NOT add an `__all__` to the
source submodule unless you list every name you want re-exported. A partial `__all__`
silently blocks everything else.

```python
# _core.py — no __all__ here if `from _core import *` must re-export all public names
from gameserver.network.handlers.economy import *   # re-exports everything public
```

### 2.3 Services dataclass pattern

New services added to the `Services` dataclass must:

1. Be `Optional[ServiceType] = None`
2. Be asserted non-None in the router's `make_router()` before use
3. Have a local alias variable created for closure use (see §1.7)

### 2.4 No bare `except Exception:` without comment + logging

Every broad exception handler must explain why it's broad and log with `exc_info=True`:

```python
except Exception:
    # Game loop must not crash for one player's bad state
    log.error("battle tick crashed", exc_info=True)
```

---

## 3. Python — Dependencies

### 3.1 All dependencies need upper bounds

When adding a new dependency, always specify both lower and upper bounds:

```toml
"fastapi>=0.100,<1.0"
"pydantic>=2.0,<3.0"
"websockets>=12.0,<17.0"
```

Use the next major version as the upper bound.

### 3.2 Update lockfile after any dependency change

```bash
cd python_server && uv lock
```

CI runs `uv lock --check` and will fail if the lockfile is out of date.

### 3.3 New type stubs go in dev dependencies

```toml
[project.optional-dependencies]
dev = [
    "types-PyYAML>=6.0",  # stubs here, not in main deps
]
```

---

## 4. Python — Testing and CI

### 4.1 Run validation in this order after every backend change

```bash
# 1. Lint (auto-fix)
.venv/bin/ruff check python_server/src/

# 2. Type check (must be 0 errors)
cd python_server && uv run --active mypy src

# 3. Tests
bash run_tests.sh --quick

# 4. Pre-commit (before committing)
.venv/bin/pre-commit run --all-files
```

### 4.2 Coverage floor is 65%

The CI gate fails below 65% (measured with infra files omitted — see `[tool.coverage.run]`
omit list in `pyproject.toml`). New code must include tests. Do not reduce existing coverage.

### 4.3 Never use `--no-verify`

Never bypass pre-commit hooks. If a hook fails, fix the underlying issue.

### 4.4 Test files — only add, never rewrite

A failing test is a signal, not a cleanup target.

---

## 5. JavaScript — Code Style

### 5.1 ESLint and Prettier are mandatory

All JS must pass `npm run lint` (0 errors) and `npm run format:check`.

```bash
cd web && npm run lint          # must show 0 errors
cd web && npm run format:check  # must show "All matched files use Prettier code style"
```

### 5.2 ESLint config

`web/eslint.config.js` — flat config format (`@eslint/js` + `eslint-config-prettier`).
External libraries (`reconnecting-websocket.mjs`) are in the ignore list.

### 5.3 Prettier config

`web/.prettierrc`: single quotes, 100 char printWidth, ES5 trailing commas.
Run `npm run format` after editing JS/CSS files.

### 5.4 No unused variables

Prefix intentionally unused parameters/variables with `_`:

```javascript
// ESLint allows _-prefixed unused vars
function handler(_event, data) { ... }
```

---

## 6. JavaScript — Frontend Build

### 6.1 Rebuild after JS/CSS changes (production)

```bash
cd web && npm run build
```

The Vite build produces hashed assets in `web/dist/`. The production server serves from `dist/`.

### 6.2 Dev mode uses raw files

For development, `npm run dev` serves raw files from `web/` via Vite proxy.
No build step needed for local iteration.

### 6.3 New image assets need WebP siblings

```bash
cd web && npm run assets:optimize  # generates .webp siblings via sharp
```

---

## 7. Git and CI

### 7.1 One task = one commit

Never bundle multiple task completions into one commit.
Commit message format: `refactor(T<id>): <imperative summary>`

### 7.2 CI gates (all must be green before merge)

| Gate | Command | Threshold |
|------|---------|-----------|
| Lockfile | `uv lock --check` | exact match |
| Lint (Python) | `uv run ruff check .` | 0 errors |
| Type check | `uv run mypy src` | 0 errors |
| Tests + coverage | `uv run pytest --cov=gameserver --cov-fail-under=65` | ≥65% |
| JS lint | `cd web && npm run lint` | 0 errors |

### 7.3 Pre-commit hooks run automatically

Hooks: ruff (auto-fix), mypy, detect-secrets, check-large-files.
Run manually before committing:

```bash
.venv/bin/pre-commit run --all-files
```

---

## 8. Architecture Invariants

### 8.1 WebSocket wire format is frozen

Never change the WebSocket message types or field names without coordinating the frontend.
The frontend `js/api.js` depends on the exact wire format.

### 8.2 Game balance YAMLs are content, not code

Never modify `python_server/config/*.yaml` in a code/refactoring commit. These are content
files (game.yaml, buildings.yaml, structures.yaml, critters.yaml, ai_waves.yaml,
artefacts.yaml, knowledge.yaml, maps/*.yaml).

### 8.3 Three era key systems — never mix

| System | Example | Used in |
|--------|---------|---------|
| German | `STEINZEIT`, `MITTELALTER` | `ERA_ORDER`, `get_current_era()` |
| Internal | `stone`, `middle_ages` | `game.yaml`, `ai_generator` |
| YAML-item | `STONE_AGE`, `MEDIEVAL` | `era:` field in knowledge.yaml |

Import era constants from `gameserver.util.eras` — never hardcode era strings elsewhere.

### 8.4 All language must be English

UI text, labels, messages, button text, comments in code — all English.

### 8.5 File size limits

| Type | Limit |
|------|-------|
| Python | 1000 lines |
| JavaScript | 600 lines |
| CSS | 800 lines |

If a file approaches these limits, plan a Strangler Fig split before adding more code.

---

## 9. Quick Reference — Validation Commands

```bash
# Python type check (must be 0 errors)
cd /home/eem/empire1/python_server && uv run --active mypy src

# Python tests with coverage gate
cd /home/eem/empire1/python_server && uv run --active pytest --cov=gameserver --cov-fail-under=65 -q

# Python lint
.venv/bin/ruff check python_server/src/

# Lockfile check
cd /home/eem/empire1/python_server && uv lock --check

# Full test suite
cd /home/eem/empire1 && bash run_tests.sh --quick

# JS lint
cd /home/eem/empire1/web && npm run lint

# JS format check
cd /home/eem/empire1/web && npm run format:check

# Frontend build
cd /home/eem/empire1/web && npm run build

# Pre-commit all files
.venv/bin/pre-commit run --all-files
```

---

## 10. Common Pitfalls (learned from T5.1 hardening)

| Pitfall | Symptom | Fix |
|---------|---------|-----|
| `python_version` mismatch | 0 errors locally, 271 in CI | Set `python_version = "3.12"` in pyproject.toml |
| Bare `dict`/`list` | `type-arg` error | Always parametrize: `dict[str, Any]` |
| `__getattr__ -> object` | `"object" not callable` everywhere | Change return type to `-> Any` |
| `__all__` before definitions | Types unresolvable | Place `__all__` after all definitions |
| `__all__` on wildcard source | Blocks re-export | Remove `__all__` from source if `from x import *` must export everything |
| Unannotated functions | `no-untyped-def` | Add `-> Any` minimum; be specific where possible |
| Closures can't narrow `Optional` | `union-attr` in endpoint | Add local alias: `svc = services.my_service` after assert |
| Dynamic attrs on typed objects | `attr-defined` | Use `setattr(obj, 'attr', val)` / `getattr(obj, 'attr')` |
| `json.loads()` return value | `no-any-return` | `result: dict[str, Any] = json.loads(raw); return result` |
| Underscore re-exports missing | `attr-defined` on `_name` | Add `_name` to `__all__` in the source module |
