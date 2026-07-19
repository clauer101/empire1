/**
 * Build the public devlog page.
 *
 * Reads CHANGELOG.md and emits web/devlog.html — a standalone static page
 * listing game updates for players. Mirrors build-api-page.mjs's approach
 * (markdown → styled HTML) with a leaner, non-SEO-landing-page layout since
 * this is a changelog, not a developer acquisition page.
 *
 * Usage:
 *   node scripts/build-devlog-page.mjs
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
const MD_PATH = join(REPO_ROOT, 'CHANGELOG.md');
const OUT_PATH = join(REPO_ROOT, 'web', 'devlog.html');

const SITE_URL = 'https://relicsnrockets.io';
const PAGE_URL = `${SITE_URL}/devlog.html`;

const TITLE = "Devlog — What's New | Relics'n'Rockets";
const DESCRIPTION = "Recent updates and balance changes to Relics'n'Rockets, a multiplayer tower-defense game.";
const KEYWORDS = "relics'n'rockets devlog, game changelog, tower defense updates, balance changes, patch notes";

function escapeHtml(s) {
  return String(s)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function slugify(text) {
  return String(text)
    .toLowerCase()
    .replace(/[^\w\s-]/g, '')
    .trim()
    .replace(/\s+/g, '-');
}

// Dates (h2) and entry titles (h3) each get a stable, unique #anchor and a
// small 🔗 permalink so individual devlog entries can be linked to directly.
const usedSlugs = new Map();
function uniqueSlug(base) {
  const count = usedSlugs.get(base) || 0;
  usedSlugs.set(base, count + 1);
  return count === 0 ? base : `${base}-${count}`;
}

marked.use({
  renderer: {
    heading({ tokens, depth, text }) {
      const inner = this.parser.parseInline(tokens);
      if (depth < 2) return `<h${depth}>${inner}</h${depth}>\n`;
      const slug = uniqueSlug(slugify(text ?? ''));
      return `<h${depth} id="${slug}">${inner} <a class="permalink" href="#${slug}" title="Permalink to this entry" aria-label="Permalink to this entry">🔗</a></h${depth}>\n`;
    },
  },
});

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
  headline: "Devlog — What's New",
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
    code, pre, kbd, samp {
      font-family: "SF Mono", Menlo, Consolas, "Liberation Mono", monospace;
      font-size: 13.5px;
    }
    code {
      background: var(--bg-3);
      padding: 1px 6px;
      border-radius: 4px;
      color: var(--accent-2);
    }
    pre {
      background: var(--code-bg);
      padding: 14px 16px;
      border-radius: 6px;
      border: 1px solid var(--border);
      overflow-x: auto;
      line-height: 1.5;
    }
    pre code { background: transparent; padding: 0; color: var(--fg); }

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
    .content h3 {
      font-size: 16px;
      margin: 24px 0 8px;
      color: var(--accent);
    }
    .content h2, .content h3 { scroll-margin-top: 16px; }
    .content .permalink {
      font-size: 0.7em;
      opacity: 0;
      margin-left: 6px;
      text-decoration: none;
      transition: opacity 0.1s;
    }
    .content h2:hover .permalink,
    .content h3:hover .permalink,
    .content .permalink:focus {
      opacity: 0.6;
    }
    .content .permalink:hover { opacity: 1; }
    .content p { margin: 0 0 12px; }
    .content ul, .content ol { margin: 0 0 12px; padding-left: 22px; }
    .content li { margin: 4px 0; }
    .content hr {
      border: none;
      border-top: 1px solid var(--border);
      margin: 28px 0;
    }
    .content strong { color: var(--fg); }

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
  <h1>📜 Devlog</h1>
  <a href="/" class="back">← Back to the Game</a>
</header>

<main class="content">
${bodyHtml}
</main>

<footer>
  <a href="/">← Back to the Game</a>
  <a href="/fairplay.html">Fair Play</a>
  <a href="/api.html">API for AI devs</a>
  <a href="/dsgvo.html">Privacy / GDPR</a>
</footer>

</body>
</html>
`;

await writeFile(OUT_PATH, html, 'utf-8');
console.log(`wrote ${OUT_PATH} (${html.length.toLocaleString()} bytes)`);
