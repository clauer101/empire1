/**
 * App bootstrap — wires together ApiClient, Router, views, status sidebar.
 */

import { ApiClient } from './api.js';
import { state } from './state.js';
import { eventBus } from './events.js';
import { Router } from './router.js';
import { initStatusBar } from './views/statusbar.js';
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

// ── Determine WebSocket URL ────────────────────────────────
// In production the client is served from the same host.
// Allow override via ?ws=<url> query param.
const params = new URLSearchParams(window.location.search);
const wsUrl = params.get('ws') || `ws://${window.location.hostname}:8765`;

// ── Instantiate core objects ───────────────────────────────
const api    = new ApiClient(wsUrl);
const appEl  = document.getElementById('app');
const router = new Router(appEl, api, state);

// ── Register views ─────────────────────────────────────────
[loginView, signupView, dashView, buildView, resView, compView, armyView, battleView, socialView]
  .forEach(v => router.register(v));

// ── Initialize status sidebar ──────────────────────────────
initStatusBar(document.getElementById('status-bar'));

// ── Toast notifications for push messages ──────────────────
eventBus.on('quick_message', (data) => showToast(data.message || data.text || JSON.stringify(data)));
eventBus.on('notification',  (data) => showToast(data.message || data.text || JSON.stringify(data)));

// ── Auto-navigate to battle view on battle_setup ───────────
eventBus.on('server:battle_setup', (data) => {
  console.log('[app] Battle setup received, navigating to battle view...');
  router.navigate('battle');
  showToast('⚔ Battle started!', 'warning');
});

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

// ── Auth state → update nav + redirect ─────────────────────
const navAuth = document.getElementById('nav-auth');
const navAuthLabel = document.getElementById('nav-auth-label');

navAuth.addEventListener('click', (e) => {
  if (state.auth.authenticated) {
    e.preventDefault();
    api.logout();
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
document.body.appendChild(debugToggle);

(async () => {
  try {
    await api.connect();
    console.log('[app] connected to', wsUrl);
    state.setConnected(true);
    await api.tryAutoLogin();
    api.startPolling();
  } catch (err) {
    console.warn('[app] initial connection failed, will retry:', err);
    api._scheduleReconnect();
  }
  // Activate router only after auth state is known
  router.start();
})();
