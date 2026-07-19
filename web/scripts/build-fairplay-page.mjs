/**
 * Build the public Fair Play page.
 *
 * Reads docs/FAIRPLAY.md and emits web/fairplay.html — a standalone static
 * page explaining the game's balance/exploit policy to players. Mirrors
 * build-devlog-page.mjs's approach (markdown → styled HTML).
 *
 * Usage:
 *   node scripts/build-fairplay-page.mjs
 *
 * Also run as part of `npm run build` so the generated file stays in sync
 * with the markdown source.
 */

import { readFile, writeFile } from 'fs/promises';
import { dirname, join } from 'path';
import { fileURLToPath } from 'url';
import { marked } from 'marked';

const __dirname = dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = join(__dirname, '..', '..');
const MD_PATH = join(REPO_ROOT, 'docs', 'FAIRPLAY.md');
const OUT_PATH = join(REPO_ROOT, 'web', 'fairplay.html');

const SITE_URL = 'https://relicsnrockets.io';
const PAGE_URL = `${SITE_URL}/fairplay.html`;

const TITLE = "Fair Play | Relics'n'Rockets";
const DESCRIPTION = "Our policy on OP settings and exploits in Relics'n'Rockets — what gets nerfed, why, and what that means for your strategy.";
const KEYWORDS = "relics'n'rockets fair play, game balance policy, exploit policy, nerf policy";

function escapeHtml(s) {
  return String(s)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

marked.setOptions({ gfm: true, breaks: false });

const md = await readFile(MD_PATH, 'utf-8');
const bodyHtml = marked.parse(md);

const html = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">

  <title>${escapeHtml(TITLE)}</title>
  <meta name="description" content="${escapeHtml(DESCRIPTION)}">
  <meta name="keywords" content="${escapeHtml(KEYWORDS)}">
  <meta name="robots" content="index, follow">
  <link rel="canonical" href="${PAGE_URL}">

  <meta property="og:type" content="website">
  <meta property="og:url" content="${PAGE_URL}">
  <meta property="og:title" content="${escapeHtml(TITLE)}">
  <meta property="og:description" content="${escapeHtml(DESCRIPTION)}">
  <meta property="og:site_name" content="Relics'n'Rockets">

  <meta name="twitter:card" content="summary">
  <meta name="twitter:title" content="${escapeHtml(TITLE)}">
  <meta name="twitter:description" content="${escapeHtml(DESCRIPTION)}">

  <link rel="icon" href="/icon-192.png" type="image/png">
  <link rel="apple-touch-icon" href="/apple-touch-icon.png">

  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">

  <script type="application/ld+json">
${JSON.stringify({
  '@context': 'https://schema.org',
  '@type': 'TechArticle',
  headline: 'Fair Play',
  description: DESCRIPTION,
  url: PAGE_URL,
  inLanguage: 'en',
  dateModified: new Date().toISOString().slice(0, 10),
  publisher: { '@type': 'Organization', name: "Relics'n'Rockets", url: SITE_URL },
  about: { '@type': 'VideoGame', name: "Relics'n'Rockets", url: SITE_URL },
}, null, 2)}
  </script>

  <style>
    /* Matches web/css/_base.css — same palette as the game/login page */
    :root {
      --bg: #0d0d14;
      --bg-2: #14141f;
      --bg-3: #1a1a28;
      --fg: #e0e0e6;
      --fg-dim: #9999a8;
      --fg-faint: #888;
      --accent: #4fc3f7;
      --accent-2: #ffb74d;
      --border: #2a2a3a;
      --code-bg: #0a0a10;
    }
    * { box-sizing: border-box; }
    html, body {
      margin: 0;
      padding: 0;
      background: var(--bg);
      color: var(--fg);
      font-family: 'Inter', 'Segoe UI', system-ui, -apple-system, sans-serif;
      font-size: 15px;
      line-height: 1.6;
    }
    a { color: var(--accent); text-decoration: none; }
    a:hover { text-decoration: underline; }

    header.top {
      border-bottom: 1px solid var(--border);
      padding: 20px 24px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      flex-wrap: wrap;
    }
    header.top h1 { font-size: 20px; margin: 0; }
    header.top .back { color: var(--fg-dim); font-size: 14px; }

    .content {
      max-width: 780px;
      margin: 0 auto;
      padding: 32px 24px 64px;
    }
    .content h1 {
      font-size: 26px;
      margin: 0 0 24px;
      padding-bottom: 10px;
      border-bottom: 2px solid var(--border);
    }
    .content h2 {
      font-size: 20px;
      margin: 36px 0 14px;
      color: var(--accent-2);
    }
    .content p { margin: 0 0 12px; }
    .content ul, .content ol { margin: 0 0 12px; padding-left: 22px; }
    .content li { margin: 4px 0; }
    .content em { color: var(--fg-dim); }
    .content strong { color: var(--fg); }
    .content blockquote {
      margin: 0 0 24px;
      padding: 12px 18px;
      border-left: 3px solid var(--accent);
      background: var(--bg-2);
      border-radius: 0 6px 6px 0;
    }
    .content blockquote p { margin: 0; }

    footer {
      border-top: 1px solid var(--border);
      padding: 32px 24px;
      text-align: center;
      color: var(--fg-faint);
      font-size: 13px;
    }
    footer a { color: var(--fg-dim); margin: 0 10px; }
  </style>
</head>
<body>

<header class="top">
  <h1>⚖️ Fair Play</h1>
  <a href="/" class="back">← Back to the Game</a>
</header>

<main class="content">
${bodyHtml}
</main>

<footer>
  <a href="/">← Back to the Game</a>
  <a href="/devlog.html">Devlog</a>
  <a href="/api.html">API for AI devs</a>
  <a href="/dsgvo.html">Privacy / GDPR</a>
</footer>

</body>
</html>
`;

await writeFile(OUT_PATH, html, 'utf-8');
console.log(`wrote ${OUT_PATH} (${html.length.toLocaleString()} bytes)`);
