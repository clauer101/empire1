/**
 * App bootstrap — wires together Router, views, status sidebar.
 *
 * Economy communication goes through REST (rest.js).
 * WebSocket is only used on the battle page (managed by battle.js).
 */

import { rest } from './rest.js';
import { state } from './state.js';
import { eventBus } from './events.js';
import { Router } from './router.js';
import { debug } from './debug.js';

import loginView   from './views/login.js';
import dashView    from './views/dashboard.js';
import buildView   from './views/buildings.js';
import resView     from './views/research.js';
import compView    from './views/composer.js';
import armyView    from './views/army.js';
import battleView  from './views/battle.js';
import socialView  from './views/social.js';
import signupView  from './views/signup.js';

// ── Determine REST URL ─────────────────────────────────────
const params = new URLSearchParams(window.location.search);
const restUrl = params.get('rest') || `http://${window.location.hostname}:8080`;

// ── Instantiate core objects ───────────────────────────────
rest.init(restUrl);
const appEl  = document.getElementById('app');
const router = new Router(appEl, null, state);

// On REST unauthorized, redirect to login
eventBus.on('rest:unauthorized', () => {
  rest.logout();
  router.navigate('login');
});

// ── Register views ─────────────────────────────────────────
[loginView, signupView, dashView, buildView, resView, compView, armyView, battleView, socialView]
  .forEach(v => router.register(v));

// ── Toast notifications for push messages ──────────────────
eventBus.on('quick_message', (data) => showToast(data.message || data.text || JSON.stringify(data)));
eventBus.on('notification',  (data) => showToast(data.message || data.text || JSON.stringify(data)));

function showToast(text, type = 'message') {
  const container = document.getElementById('toast-container');
  if (!container) return;
  const el = document.createElement('div');
  el.className = `toast${type ? ` toast-${type}` : ''}`;
  el.textContent = text;
  container.appendChild(el);
  setTimeout(() => el.remove(), 5000);
}

// ── Register debug toast callback ──────────────────────────
debug.setToastCallback((text, type) => showToast(text, type));

// ── Incoming attack alarm on nav-brand ──────────────────────
const navBrand = document.getElementById('nav-brand');
const navMsgBadge = document.getElementById('nav-msg-badge');
eventBus.on('state:summary', (data) => {
  const hasIncoming = data && Array.isArray(data.attacks_incoming) && data.attacks_incoming.length > 0;
  navBrand.classList.toggle('alarm', hasIncoming);
  navBrand.title = hasIncoming
    ? `⚠ ${data.attacks_incoming.length} incoming attack(s)!`
    : 'E3';

  // Unread messages badge
  const unread = data?.unread_messages || 0;
  if (navMsgBadge) {
    navMsgBadge.textContent = unread > 9 ? '9+' : String(unread);
    navMsgBadge.style.display = unread > 0 ? '' : 'none';
  }
});

// ── Summary polling (every 5s while authenticated) ─────────
let _pollTimer = null;

function startPolling() {
  if (_pollTimer) return;
  _pollTimer = setInterval(async () => {
    if (!state.auth.authenticated) return;
    try { await rest.getSummary(); } catch (_) { /* ignore */ }
  }, 5000);
}

function stopPolling() {
  if (_pollTimer) { clearInterval(_pollTimer); _pollTimer = null; }
}

eventBus.on('state:auth', (auth) => {
  if (auth.authenticated) startPolling();
  else stopPolling();
});

// ── Auth state → update nav + redirect ─────────────────────
const navAuth = document.getElementById('nav-auth');
const navAuthLabel = document.getElementById('nav-auth-label');

navAuth.addEventListener('click', (e) => {
  if (state.auth.authenticated) {
    e.preventDefault();
    rest.logout();
    window.location.hash = '#login';
  }
});

eventBus.on('state:auth', (auth) => {
  if (auth.authenticated) {
    navAuthLabel.textContent = 'Logout';
    navAuth.href = '#';
  } else {
    navAuthLabel.textContent = 'Login';
    navAuth.href = '#login';
  }
  if (auth.authenticated && router.currentRoute() === 'login') {
    const target = router.pendingRoute || 'dashboard';
    router.pendingRoute = null;
    router.navigate(target);
  }
});

// ── Start ──────────────────────────────────────────────────
// Connect + auto-login first, then activate router so the
// login screen never flashes when credentials are stored.

// ── Debug Toggle (bottom-right) ────────────────────────────
const debugToggle = document.createElement('div');
debugToggle.id = 'debug-toggle';
debugToggle.className = 'debug-toggle' + (debug.enabled ? ' active' : '');
debugToggle.title = 'Toggle debug mode (shows API responses)';
debugToggle.innerHTML = '🐛';
debugToggle.addEventListener('click', () => {
  debug.toggle(!debug.enabled);
  debugToggle.classList.toggle('active', debug.enabled);
  showToast(`Debug mode ${debug.enabled ? 'enabled' : 'disabled'}`);
});
// document.body.appendChild(debugToggle);

(async () => {
  // 1. Try REST auto-login (validates stored JWT or credentials)
  try {
    await rest.tryAutoLogin();
  } catch (err) {
    console.warn('[app] REST auto-login failed:', err.message);
  }

  // 2. Activate router (no WS needed — battle view manages its own)
  router.start();
})();
