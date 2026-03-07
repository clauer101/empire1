/**
 * Dev Tools Navigation Bar
 * Include this script in any tool page to get a shared navigation bar.
 */
(function () {
  // ── Auth Guard ──────────────────────────────────────────────────────────────
  const ADMIN_USER = 'eem';
  const GAMESERVER = 'http://localhost:8080';

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
    return localStorage.getItem('e3_dev_user') === ADMIN_USER;
  }

  function showLoginOverlay() {
    document.documentElement.style.background = '#0d0d14';
    document.body.innerHTML = `
      <style>
        body { background:#0d0d14; margin:0; display:flex; align-items:center; justify-content:center; min-height:100vh;
               font-family:'Inter','Segoe UI',system-ui,sans-serif; font-size:13px; color:#e0e0e6; }
        .login-box { background:#14141f; border:1px solid #2a2a3a; border-radius:8px; padding:32px 36px; width:320px; }
        .login-box h2 { color:#4fc3f7; font-size:1rem; letter-spacing:1px; margin-bottom:24px; text-align:center; }
        label { display:flex; flex-direction:column; gap:4px; font-size:11px; color:#9999a8; margin-bottom:12px; }
        input { background:#1a1a28; border:1px solid #2a2a3a; border-radius:6px; color:#e0e0e6;
                font-size:12px; padding:8px 10px; outline:none; width:100%; }
        input:focus { border-color:#4fc3f7; }
        button { width:100%; background:#4fc3f7; color:#0d0d14; font-weight:600; font-size:13px;
                 border:none; border-radius:6px; padding:9px; cursor:pointer; margin-top:6px; }
        button:hover { opacity:.85; }
        #err { color:#ef5350; font-size:12px; text-align:center; min-height:18px; margin-top:10px; }
      </style>
      <div class="login-box">
        <h2>DEV TOOLS LOGIN</h2>
        <label>Username<input id="g-user" type="text" autocomplete="username" /></label>
        <label>Password<input id="g-pw" type="password" autocomplete="current-password" /></label>
        <button id="g-btn">Login</button>
        <div id="err"></div>
      </div>
    `;

    const userInput = document.getElementById('g-user');
    const pwInput   = document.getElementById('g-pw');
    const btn       = document.getElementById('g-btn');
    const err       = document.getElementById('err');

    async function doLogin() {
      err.textContent = '';
      btn.disabled = true;
      btn.textContent = '…';
      try {
        const resp = await fetch(GAMESERVER + '/api/auth/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ username: userInput.value.trim(), password: pwInput.value }),
        });
        const data = await resp.json();
        if (!data.success) { err.textContent = data.reason || 'Login fehlgeschlagen'; return; }
        const enteredUser = userInput.value.trim().toLowerCase();
        if (enteredUser !== ADMIN_USER) { err.textContent = `Kein Zugriff (nur für ${ADMIN_USER}).`; return; }
        localStorage.setItem('e3_jwt_token', data.token);
        localStorage.setItem('e3_dev_user', enteredUser);
        location.reload();
      } catch (e) {
        err.textContent = 'Gameserver nicht erreichbar.';
      } finally {
        btn.disabled = false;
        btn.textContent = 'Login';
      }
    }

    btn.addEventListener('click', doLogin);
    pwInput.addEventListener('keydown', e => { if (e.key === 'Enter') doLogin(); });
    userInput.addEventListener('keydown', e => { if (e.key === 'Enter') pwInput.focus(); });
    userInput.focus();
  }

  if (!isAuthorized()) {
    if (document.body) { showLoginOverlay(); }
    else { document.addEventListener('DOMContentLoaded', showLoginOverlay); }
    return; // stop rest of nav.js
  }
  // ────────────────────────────────────────────────────────────────────────────

  const TOOLS = [
    { name: '🏠 Index',    href: 'index.html' },
    { name: '📊 Status',   href: 'status.html' },
    { name: '⚔ Sprite',   href: 'sprite.html' },
    { name: '🌊 AI Waves', href: 'ai-waves.html' },
    { name: '🗄️ Database', href: 'database.html' },
    { name: '🎛️ Sigmoid', href: 'sigmoid_tuner.html' },
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
