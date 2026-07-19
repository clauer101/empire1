---
name: verify-backend
description: Validate backend changes in the required order - ruff lint, test suite, pre-commit (ruff + mypy + detect-secrets). Run after every backend change.
---

# Verify backend changes

Run in this order; stop and fix at the first failure:

```bash
# 1. Lint
.venv/bin/ruff check python_server/src/

# 2. Tests (full suite; narrow with --match=NAME or a path while iterating)
rtk run_tests.sh

# 3. Pre-commit: ruff + mypy + detect-secrets
.venv/bin/pre-commit run --all-files
```

Test runner options: `--match=<pattern>`, `<path>`, `--all`, `--quick`, `--cov`, `--failfast`.
mypy standalone: `.venv/bin/mypy --config-file=python_server/pyproject.toml python_server/src`
(the `--config-file` is required from the repo root — otherwise mypy silently
skips `strict = true` and misses errors CI would catch).
Never bypass pre-commit with `--no-verify`.
