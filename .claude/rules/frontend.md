---
paths:
  - "web/**"
---

# Frontend Rules

## Vite Build (mandatory before deploy)

Node ≥20 required (use NVM).

```bash
# One-time setup
export NVM_DIR="$HOME/.nvm" && . "$NVM_DIR/nvm.sh"
cd web && npm install

# Development server (raw files, no build)
npm run dev          # :5173, proxies /api + /ws to :8080

# Production bundle
npm run build        # hashed assets in web/dist/
```

> **IMPORTANT — both dev and prod environments use `BUILD_MODE=production`** (set in
> `docker-compose.dev.yml` and `docker-compose.yml`). The server always serves
> `web/dist/`, **not** raw source files. Any JS/CSS change that "doesn't appear"
> after deploy means the Vite build was not re-run. **Always run build + deploy together:**
> ```bash
> export NVM_DIR="$HOME/.nvm" && . "$NVM_DIR/nvm.sh"
> cd web && npm run build && cd .. && ./deploy.sh dev
> ```

## API Documentation

API docs live in `docs/API.md`. `web/api.html` is auto-generated from it by
`web/scripts/build-api-page.mjs` (runs during `npm run build`). Never edit
`web/api.html` directly.

## Image Assets

New JPG/PNG sprites: run `npm run assets:optimize` to generate WebP siblings
(the build runs this automatically). Skip PWA icons (`apple-touch-icon.png`,
`icon-192.png`, `icon-512.png`) — those must stay PNG.

## Shared Utilities (`web/js/lib/format.js`)

All formatting logic lives in `web/js/lib/format.js`. Do not inline formatting elsewhere.

| Function | Purpose |
|---|---|
| `fmtEffort(n)` | Numbers with K/M suffix |
| `fmtSecs(s)` | Seconds → `1h 2m 3s` |
| `fmtEffectRow(key, value)` | Two-column HTML row — for overlays/detail panels |
| `fmtEffectsInline(effects)` | Compact comma string — for card previews |
| `fmtTowerEffects(effects)` | Tower combat effects: burn / slow / splash |

Shared UI lib: `js/lib/item_overlay.js` (item detail overlay), `js/lib/eras.js`
(era constants).
