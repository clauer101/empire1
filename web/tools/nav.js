/**
 * Dev Tools Navigation Bar
 * Include this script in any tool page to get a shared navigation bar.
 */
(function () {
  // ── Auth Guard ──────────────────────────────────────────────────────────────
  const GAMESERVER = window.location.origin;

  function decodeJwtPayload(token) {
    try {
      const part = token.split('.')[1];
      return JSON.parse(atob(part.replace(/-/g, '+').replace(/_/g, '/')));
    } catch { return null; }
  }

  function isAuthorized() {
    const token = localStorage.getItem('e3_jwt_token');
    if (!token) return false;
    const payload = decodeJwtPayload(token);
    if (!payload) return false;
    if (payload.exp && payload.exp < Date.now() / 1000) return false;
    return true;
  }

  if (!isAuthorized()) {
    window.location.replace('/#login');
    return;
  }

  // Check admin access by verifying username via gameserver
  (async function checkAdmin() {
    try {
      const token = localStorage.getItem('e3_jwt_token');
      const r = await fetch('/api/admin/whoami', {
        headers: { Authorization: 'Bearer ' + token }
      });
      if (!r.ok) {
        window.location.replace('/');
        return;
      }
      const data = await r.json();
      if ((data.username || '').toLowerCase() !== 'eem') {
        window.location.replace('/');
      }
    } catch {
      window.location.replace('/');
    }
  })();
  // ────────────────────────────────────────────────────────────────────────────

  const TOOLS = [
    { name: '🏠 Index',    href: 'index.html' },
    { name: '📊 Status',   href: 'status.html' },
    { name: '🔁 Restart',  href: 'restart.html' },
    { name: '🗄️ Database', href: 'database.html' },
    // { name: '⚔ Sprite',   href: 'sprite.html' },
    { name: '🌊 AI Waves', href: 'ai-waves.html' },
    // { name: '⏱ Effort',   href: 'effort-tuner.html' },
    
    { name: '🎛️ Sigmoid', href: 'sigmoid_tuner.html' },
    // { name: '⚡ Effects',  href: 'effects.html' },
    { name: '⚖ Balance',  href: 'balance.html' },
    { name: '⏱ Era FX',   href: 'era-effects.html' },
    // { name: '📊 Scatter',  href: 'critter-scatter.html' },
    { name: '⚔ AI Army',  href: 'send-ai-army.html' },
    { name: '🗺 Maps',     href: 'map-overview.html' },
    { name: '🐾 Critters', href: 'critters.html' },
    { name: '✨ Artefacts', href: 'artifacts.html' },
    { name: '⚔ Sim Map',  href: 'sim-map.html' },
    // { name: '🌳 Tree',    href: 'tech-tree.html' },
    { name: '🤖 Claude',  href: 'claude.html' },
  ];

  const current = window.location.pathname.split('/').pop() || 'index.html';

  const style = document.createElement('style');
  style.textContent = `
    #dev-nav {
      position: fixed; top: 0; left: 0; right: 0; z-index: 9999;
      background: #0d1117; border-bottom: 1px solid #30363d;
      display: flex; align-items: center; gap: 0;
      padding: 0 12px; height: 38px;
      font-family: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace;
      font-size: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.5);
      overflow-x: auto; overflow-y: hidden;
      -webkit-overflow-scrolling: touch;
    }
    #dev-nav .nav-brand {
      color: #58a6ff; font-weight: bold; margin-right: 8px;
      white-space: nowrap; padding-right: 12px;
      border-right: 1px solid #30363d;
    }
    #dev-nav a {
      color: #8b949e; text-decoration: none;
      padding: 0 10px; height: 38px; display: flex; align-items: center;
      border-bottom: 2px solid transparent;
      transition: color 0.15s, border-color 0.15s;
      white-space: nowrap;
    }
    #dev-nav a:hover { color: #c9d1d9; }
    #dev-nav a.active { color: #58a6ff; border-bottom-color: #58a6ff; }
    body { padding-top: 38px !important; }
  `;
  document.head.appendChild(style);

  const nav = document.createElement('nav');
  nav.id = 'dev-nav';

  const brand = document.createElement('span');
  brand.className = 'nav-brand';
  brand.textContent = '🔧 Dev Tools';
  nav.appendChild(brand);

  TOOLS.forEach(function (tool) {
    const a = document.createElement('a');
    a.href = tool.href;
    a.textContent = tool.name;
    if (tool.href === current) a.classList.add('active');
    nav.appendChild(a);
  });

  function mount() { document.body.prepend(nav); }
  if (document.body) { mount(); }
  else { document.addEventListener('DOMContentLoaded', mount); }
})();
