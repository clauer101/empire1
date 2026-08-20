# Devlog Pipeline

The public devlog page (`/devlog.html`) is generated from `CHANGELOG.md` — never
edit `web/devlog.html` directly, it is build output and gets overwritten.

## Flow

1. **Write the entry in `CHANGELOG.md`** (repo root), newest entry at the top
   under a `## YYYY-MM-DD` heading, with one or more `### Title` sections
   underneath. Match the tone/format of existing entries (see e.g. the
   2026-08-15 season wrap-up entry).
2. **Regenerate the page** — `web/scripts/build-devlog-page.mjs` reads
   `CHANGELOG.md`, converts it with `marked`, and writes `web/devlog.html`:
   ```bash
   export NVM_DIR="$HOME/.nvm" && . "$NVM_DIR/nvm.sh"
   cd web && node scripts/build-devlog-page.mjs
   ```
   This also runs automatically as part of `npm run build`.
3. **Deploy** if the update should go live — build + deploy dev (or prod, with
   explicit user confirmation) per `.claude/rules/deployment.md`.

## When to add an entry

Any player-facing change worth announcing: balance passes, new features,
season start/end summaries, policy changes. Skip purely internal/dev-facing
changes (those belong in commit messages, not the changelog).

This mirrors `docs/API.md` → `web/api.html` (see `build-api-page.mjs`) — same
pattern, markdown source of truth generating a static page.
