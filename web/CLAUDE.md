# CLAUDE.md — web frontend

Single-page app bundled with Vite. **Any JS/CSS change requires `npm run build`
before deploy** — dev and prod both serve `web/dist/`, not raw source. Full build
and asset rules: `.claude/rules/frontend.md`.

## Layout

- `js/app.js` + `js/router.js` — SPA shell
- `js/views/` — one module per view: `defense.js` (tower placement + battle),
  `army.js` (wave composer), `techtree.js` (knowledge tree), `workshop.js` (item upgrades)
- `js/api.js` (WebSocket) + `js/rest.js` (HTTP) — all server communication
- `js/lib/` — shared utilities; all formatting goes through `js/lib/format.js`
- `tools/` — developer tools (`status.html`, `database.html`, balance tuner, replay viewer)
- `scripts/` — Node build scripts, documented in `scripts/AGENTS.md`
- `e2e/` — Playwright smoke tests (dev environment only; teardown via `globalTeardown.js`)

The backend computes all game values — never derive them in the frontend
(see root `CLAUDE.md`, Frontend Data Principle).
