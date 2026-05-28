# web/scripts/ — Agent Instructions

This directory holds Node scripts that run as part of the frontend build pipeline.

## Files

- `optimize-assets.mjs` — converts JPG/PNG sprites to WebP siblings. Runs before `vite build`.
- `build-api-page.mjs` — generates `web/api.html` from `docs/API.md`. Public API documentation page targeting external AI developers.

## Public API Documentation Page

**`docs/API.md` is the single source of truth.** Never hand-edit `web/api.html` — it is regenerated on every build.

### Regenerating after editing the markdown

```bash
cd web
npm run build:api        # regenerate api.html only
# OR
npm run build            # regenerate api.html + optimize assets + vite build
```

The full `npm run build` chain runs `build-api-page.mjs` before `vite build`, so any change to `docs/API.md` automatically flows into the bundled output.

### Where to change things

- **The Python quick-start code, the dev pitch, the endpoint reference:** edit `docs/API.md`.
- **SEO meta tags (title, description, keywords, OG tags, JSON-LD):** edit the constants at the top of `build-api-page.mjs` (`TITLE`, `DESCRIPTION`, `KEYWORDS`, `ldJson`).
- **Page layout / CSS / hero copy:** edit the template literal in `build-api-page.mjs`.

### Critical: don't break the `/api/` namespace

The JSON game API lives under `/api/auth/...`, `/api/empire/...`, etc. nginx whitelists these paths and forwards them to the gameserver.

- The public **documentation page** lives at `/api.html` — note the dot, not a slash. This is intentional. `/api/` (with trailing slash) would collide with the JSON namespace.
- The friendly alias `/api-docs` (defined in `web/fastapi_server.py`) 301-redirects to `/api.html`.
- `web/robots.txt` MUST keep `Disallow: /api/` — that blocks crawlers from hammering the JSON endpoints. It does NOT block `/api.html` because robots.txt uses prefix matching and `/api.` is not a prefix of `/api/`.

If you add new routes that start with `/api`, make sure they don't accidentally land under the disallowed prefix or shadow a gameserver endpoint.

### Vite multi-page setup

`web/api.html` is registered as a Vite entry point in `web/vite.config.js`. If you add additional standalone HTML pages (e.g. a press page, a guide page), follow the same pattern:

1. Generate or hand-write the HTML in `web/`.
2. Add it to `rollupOptions.input` in `vite.config.js`.
3. Add an entry to `web/sitemap.xml`.
