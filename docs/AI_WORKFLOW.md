# AI-Assisted Development Workflow

This project is developed with [Claude Code](https://claude.com/claude-code) as
a primary collaborator, running against a live service with real users and
real data. "Used an AI" is not, on its own, an interesting engineering claim —
what matters is the concrete mechanisms that make that collaboration safe and
efficient. This document describes those mechanisms as they actually exist in
this repository, with references to the real files behind each claim.

## Layered context instead of one giant prompt

- **`CLAUDE.md`** (repo root) — always-loaded global rules: project language,
  the frontend/backend data-ownership boundary, the required validation
  sequence for backend changes, deployment safety rules, and a compact
  architecture overview.
- **`.claude/rules/{frontend,backend,deployment}.md`** — path-scoped rules,
  loaded automatically only when work touches the matching area. `backend.md`
  covers gotchas like the two parallel era-key naming systems and the
  dependency-lockfile workflow; `frontend.md` covers the Vite build trap
  (both prod and dev serve the *built* bundle, never raw source) and shared
  formatting utilities; `deployment.md` covers the nginx API-prefix whitelist
  that silently 404s new endpoints if forgotten.

Splitting rules this way keeps the context an agent always carries small,
while still surfacing domain-specific traps exactly when they're relevant —
the same reasoning behind scoped ownership docs (`INTERFACES.md` per backend
package) rather than one monolithic spec.

## Skills: codified, repeatable workflows

Ad hoc prompting for multi-step, order-sensitive procedures is a repeated
source of mistakes (skip a step, run it in the wrong order). This repo
encodes the three procedures that matter most as project skills in
`.claude/skills/`:

- **`verify-backend`** — runs `ruff check` → `run_tests.sh` → `pre-commit run
  --all-files` (ruff + mypy strict + detect-secrets), in that fixed order,
  stopping at the first failure. `--no-verify` is explicitly disallowed.
- **`deploy-dev`** — builds the Vite frontend and deploys the dev stack in one
  step, and is scoped to never touch prod.
- **`e2e`** — runs the Playwright suite against the dev environment only, with
  automatic test-account teardown and a documented manual-cleanup fallback.

Each skill is a thin wrapper around real shell commands (`run_tests.sh`,
`deploy.sh`, `npx playwright test`) — the value is in fixing the order and the
scope, not in adding new capability.

## Guardrails around irreversible actions

The rules above are backed by mechanisms that don't rely on the agent
remembering them correctly every time:

- **`deploy.sh` is battle-aware** — it queries the admin API for in-progress
  battles before stopping a server and refuses to deploy over a live fight
  unless explicitly forced (`-f`) or told to wait (`-w`).
- **State is saved before every stop** — a deploy or stop always POSTs to
  `/api/admin/save-state` first, so in-memory game state survives a container
  restart.
- **Production backups are automatic** — every prod stop tars the database,
  state file, and bot state, and commits the backup to git before the running
  containers are touched.
- **The production database is never written directly** — writing to
  `data/prod/gameserver.db` while the server is running corrupts the
  `aiosqlite` connection for all subsequent writes; this is called out
  explicitly in `CLAUDE.md` and `.claude/rules/deployment.md`.
- **Prod deploys require explicit human confirmation** — `deploy.sh prod` and
  `deploy.sh both` are never run without the user confirming first; this is a
  standing rule, not a per-session judgment call.

The pattern throughout: automate the routine (lint, test, dev deploys, log
tailing), but keep a human in the loop for anything destructive or
hard-to-reverse (prod deploys, direct DB access, force-stopping mid-battle).

## Scoped tool permissions

`.claude/settings.json` (committed, shared) pre-authorizes a small allowlist
of genuinely safe, read-only commands (`git status`, test-analytics commands,
two specific test invocations) so the agent isn't stopped for permission on
things that can't cause harm. `.claude/settings.local.json` (personal,
gitignored) accumulates a broader allowlist from real working sessions —
kept separate so the *shared* baseline stays conservative while individual
contributors can widen their own.

## Efficient by construction: RTK

Every one of the mechanisms above still runs through an agent that calls
shell tools constantly — status checks, git operations, log reads. **[RTK — Rust Token Killer](https://github.com/rtk-ai/rtk)** is a
token-optimization CLI proxy that intercepts those calls via a Claude Code
`PreToolUse` hook and rewrites the routine ones (`git status`, `git log`, file
reads, …) into a compressed form that returns the same information for a
fraction of the tokens, transparently and without changing the command's
behavior. It's a publicly available tool, built specifically because "safe
AI-assisted development on a live service" is only practical day-to-day if
the routine parts of it are also cheap — guardrails that cost too much to run
get skipped under pressure, which defeats the point.

## Verification discipline

None of the above replaces testing. Every backend change goes through lint →
tests → pre-commit before it's considered done (see **Testing & quality** in
the root [README](../README.md)), and the same coverage/type-strictness gates
that apply to human-written code apply here — CI doesn't know or care who
wrote a given commit.
