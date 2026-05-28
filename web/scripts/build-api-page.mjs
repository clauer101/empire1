/**
 * Build the public API documentation HTML page.
 *
 * Reads docs/API.md and emits web/api.html — a fully standalone, SEO-optimized
 * landing page aimed at external developers who might build an AI bot against
 * the public REST API.
 *
 * Usage:
 *   node scripts/build-api-page.mjs
 *
 * This script is also run as part of `npm run build` so the generated file
 * stays in sync with the markdown source.
 */

import { readFile, writeFile } from 'fs/promises';
import { dirname, join } from 'path';
import { fileURLToPath } from 'url';
import { marked } from 'marked';

const __dirname = dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = join(__dirname, '..', '..');
const MD_PATH = join(REPO_ROOT, 'docs', 'API.md');
const OUT_PATH = join(REPO_ROOT, 'web', 'api.html');

const SITE_URL = 'https://relicsnrockets.io';
const PAGE_URL = `${SITE_URL}/api.html`;
const OG_IMAGE = `${SITE_URL}/assets/sprites/banner.webp`;

const TITLE = 'Game API for AI Developers — Build Your Own Bot | Relics\'n\'Rockets';
const DESCRIPTION =
  'Build your own AI bot for Relics\'n\'Rockets — a multiplayer tower-defense game with a public REST API. Python, JS, Rust, any language. JWT auth, JSON, real opponents.';
const KEYWORDS =
  'game ai api, build ai bot, multiplayer game api, tower defense api, game bot tutorial, rest api game, ai agent game, autonomous game bot, jwt game api, python game bot';

function slugify(text) {
  return String(text)
    .toLowerCase()
    .replace(/[^\w\s-]/g, '')
    .trim()
    .replace(/\s+/g, '-');
}

marked.setOptions({ gfm: true, breaks: false });

// marked v14 dropped built-in header IDs — inject them via a walkTokens pass so
// the TOC and CTA anchors actually resolve. The default renderer reads
// token.text as raw HTML when rendering, so we prepend the id attribute via a
// custom heading renderer that delegates to parseInline.
marked.use({
  renderer: {
    heading({ tokens, depth, text }) {
      const slug = slugify((text ?? '').replace(/\s*🔐\s*$/, ''));
      const inner = this.parser.parseInline(tokens);
      return `<h${depth} id="${slug}">${inner}</h${depth}>\n`;
    },
  },
});

function buildToc(md) {
  const lines = md.split('\n');
  const items = [];
  let inFence = false;
  for (const line of lines) {
    if (line.startsWith('```')) {
      inFence = !inFence;
      continue;
    }
    if (inFence) continue;
    const m = /^(#{2,3})\s+(.+?)\s*$/.exec(line);
    if (m) {
      const depth = m[1].length;
      const text = m[2].replace(/\s*🔐\s*$/, '').trim();
      if (text.startsWith('Relics')) continue;
      items.push({ depth, text, slug: slugify(text) });
    }
  }
  return items
    .map(
      (it) =>
        `<li class="toc-d${it.depth}"><a href="#${it.slug}">${escapeHtml(it.text)}</a></li>`,
    )
    .join('\n');
}

function escapeHtml(s) {
  return String(s)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

const md = await readFile(MD_PATH, 'utf-8');
const bodyHtml = marked.parse(md);
const tocHtml = buildToc(md);

const today = new Date().toISOString().slice(0, 10);

const ldJson = {
  '@context': 'https://schema.org',
  '@type': 'TechArticle',
  headline: 'Game API for AI Developers — Build Your Own Bot',
  description: DESCRIPTION,
  url: PAGE_URL,
  image: OG_IMAGE,
  inLanguage: 'en',
  dateModified: today,
  audience: {
    '@type': 'Audience',
    audienceType: 'Developer',
  },
  publisher: {
    '@type': 'Organization',
    name: "Relics'n'Rockets",
    url: SITE_URL,
  },
  about: {
    '@type': 'VideoGame',
    name: "Relics'n'Rockets",
    url: SITE_URL,
    genre: ['Tower Defense', 'Strategy', 'MMO'],
  },
  proficiencyLevel: 'Intermediate',
  programmingLanguage: ['Python', 'JavaScript', 'Rust', 'Go', 'Any'],
};

const html = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">

  <title>${escapeHtml(TITLE)}</title>
  <meta name="description" content="${escapeHtml(DESCRIPTION)}">
  <meta name="keywords" content="${escapeHtml(KEYWORDS)}">
  <meta name="robots" content="index, follow, max-image-preview:large">
  <meta name="author" content="Relics'n'Rockets">
  <link rel="canonical" href="${PAGE_URL}">

  <!-- Open Graph -->
  <meta property="og:type" content="article">
  <meta property="og:url" content="${PAGE_URL}">
  <meta property="og:title" content="${escapeHtml(TITLE)}">
  <meta property="og:description" content="${escapeHtml(DESCRIPTION)}">
  <meta property="og:image" content="${OG_IMAGE}">
  <meta property="og:site_name" content="Relics'n'Rockets">
  <meta property="og:locale" content="en_US">
  <meta property="article:section" content="Developer Documentation">
  <meta property="article:tag" content="game api">
  <meta property="article:tag" content="ai bot">
  <meta property="article:tag" content="multiplayer">

  <!-- Twitter -->
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="${escapeHtml(TITLE)}">
  <meta name="twitter:description" content="${escapeHtml(DESCRIPTION)}">
  <meta name="twitter:image" content="${OG_IMAGE}">

  <link rel="icon" href="/icon-192.png" type="image/png">
  <link rel="apple-touch-icon" href="/apple-touch-icon.png">

  <script type="application/ld+json">
${JSON.stringify(ldJson, null, 2)}
  </script>

  <style>
    :root {
      --bg: #0d1014;
      --bg-2: #161b22;
      --bg-3: #1f262d;
      --fg: #e6edf3;
      --fg-dim: #9da7b3;
      --fg-faint: #6e7681;
      --accent: #4fc3f7;
      --accent-2: #ffb74d;
      --border: #2d333b;
      --code-bg: #0a0d10;
    }
    * { box-sizing: border-box; }
    html, body {
      margin: 0;
      padding: 0;
      background: var(--bg);
      color: var(--fg);
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
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

    /* Hero */
    .hero {
      background: linear-gradient(135deg, #1a1f2c 0%, #0d1014 100%);
      padding: 64px 24px 56px;
      border-bottom: 1px solid var(--border);
      text-align: center;
    }
    .hero-inner { max-width: 880px; margin: 0 auto; }
    .hero h1 {
      font-size: clamp(28px, 5vw, 46px);
      line-height: 1.15;
      margin: 0 0 16px;
      background: linear-gradient(90deg, #4fc3f7, #ffb74d);
      -webkit-background-clip: text;
      background-clip: text;
      color: transparent;
    }
    .hero .tagline {
      font-size: 18px;
      color: var(--fg-dim);
      margin: 0 0 28px;
    }
    .hero .cta-row {
      display: flex;
      gap: 12px;
      justify-content: center;
      flex-wrap: wrap;
      margin: 0 0 32px;
    }
    .cta {
      display: inline-block;
      padding: 12px 22px;
      border-radius: 6px;
      font-weight: 600;
      font-size: 15px;
      transition: transform 0.1s, background 0.15s;
    }
    .cta:hover { text-decoration: none; transform: translateY(-1px); }
    .cta-primary {
      background: var(--accent);
      color: #0d1014;
    }
    .cta-primary:hover { background: #6fd0fa; }
    .cta-secondary {
      background: transparent;
      color: var(--fg);
      border: 1px solid var(--border);
    }
    .cta-secondary:hover { background: var(--bg-3); }

    .hero-quickstart {
      text-align: left;
      max-width: 720px;
      margin: 0 auto;
    }
    .hero-quickstart h2 {
      font-size: 16px;
      color: var(--fg-dim);
      margin: 0 0 8px;
      font-weight: 500;
    }

    /* Layout */
    .layout {
      max-width: 1280px;
      margin: 0 auto;
      padding: 32px 24px 64px;
      display: grid;
      grid-template-columns: 260px 1fr;
      gap: 40px;
    }
    @media (max-width: 900px) {
      .layout { grid-template-columns: 1fr; }
      .toc { position: static !important; max-height: none !important; }
    }

    /* TOC */
    .toc {
      position: sticky;
      top: 24px;
      max-height: calc(100vh - 48px);
      overflow-y: auto;
      font-size: 13px;
      border-right: 1px solid var(--border);
      padding-right: 16px;
    }
    .toc h3 {
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: var(--fg-faint);
      margin: 0 0 12px;
    }
    .toc ul { list-style: none; margin: 0; padding: 0; }
    .toc li { margin: 2px 0; }
    .toc a { color: var(--fg-dim); display: block; padding: 3px 8px; border-radius: 4px; }
    .toc a:hover { background: var(--bg-3); color: var(--fg); text-decoration: none; }
    .toc-d2 { font-weight: 600; margin-top: 8px !important; }
    .toc-d2 > a { color: var(--fg); }
    .toc-d3 { padding-left: 12px; }

    /* Content */
    .content { min-width: 0; }
    .content h1 {
      font-size: 28px;
      margin: 0 0 20px;
      padding-bottom: 10px;
      border-bottom: 2px solid var(--border);
    }
    .content h2 {
      font-size: 22px;
      margin: 40px 0 16px;
      padding-bottom: 6px;
      border-bottom: 1px solid var(--border);
    }
    .content h3 {
      font-size: 17px;
      margin: 28px 0 10px;
      color: var(--accent);
    }
    .content h3 code {
      background: var(--bg-3);
      color: var(--accent);
      font-size: 15px;
    }
    .content p { margin: 0 0 12px; }
    .content ul, .content ol { margin: 0 0 12px; padding-left: 22px; }
    .content li { margin: 4px 0; }
    .content blockquote {
      margin: 12px 0;
      padding: 10px 16px;
      border-left: 3px solid var(--accent);
      background: rgba(79, 195, 247, 0.06);
      color: var(--fg-dim);
      border-radius: 0 4px 4px 0;
    }
    .content blockquote p { margin: 4px 0; }
    .content hr {
      border: none;
      border-top: 1px solid var(--border);
      margin: 32px 0;
    }
    .content table {
      border-collapse: collapse;
      margin: 12px 0;
      width: 100%;
      font-size: 13.5px;
    }
    .content th, .content td {
      border: 1px solid var(--border);
      padding: 6px 10px;
      text-align: left;
    }
    .content th {
      background: var(--bg-3);
      font-weight: 600;
    }

    /* Footer */
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

<header class="hero">
  <div class="hero-inner">
    <h1>Build a Game AI in 20 Lines of Code</h1>
    <p class="tagline">
      Relics'n'Rockets is a multiplayer tower-defense game with a fully public REST API.
      Write a bot in any language and let it compete against humans and other AIs in a living world.
    </p>
    <div class="cta-row">
      <a href="/#signup" class="cta cta-primary">Create a Free Account</a>
      <a href="#quick-start-a-bot-in-20-lines-of-python" class="cta cta-secondary">Jump to Quick Start →</a>
      <a href="/" class="cta cta-secondary">Back to Game</a>
    </div>
    <div class="hero-quickstart">
      <h2>The whole loop:</h2>
      <pre><code>POST /api/auth/login        → token
GET  /api/empire/summary    → state (poll every 5 s)
POST /api/empire/build      → queue a building
POST /api/attack            → raid a rival
GET  /api/messages          → read battle reports</code></pre>
    </div>
  </div>
</header>

<div class="layout">
  <aside class="toc" aria-label="Table of contents">
    <h3>On this page</h3>
    <ul>
${tocHtml}
    </ul>
  </aside>

  <main class="content">
${bodyHtml}
  </main>
</div>

<footer>
  <a href="/">← Back to the Game</a>
  <a href="/dsgvo.html">Privacy / GDPR</a>
  <a href="https://github.com/" rel="nofollow">Found a bug? Open an issue</a>
  <div style="margin-top:8px;opacity:0.6">© Relics'n'Rockets — Public API for autonomous AI agents</div>
</footer>

</body>
</html>
`;

await writeFile(OUT_PATH, html, 'utf-8');
console.log(`wrote ${OUT_PATH} (${html.length.toLocaleString()} bytes)`);
