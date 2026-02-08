/**
 * App bootstrap — wires together ApiClient, Router, views, status sidebar.
 */

import { ApiClient } from './api.js';
import { state } from './state.js';
import { eventBus } from './events.js';
import { Router } from './router.js';
import { initStatusBar } from './views/statusbar.js';

import loginView   from './views/login.js';
import dashView    from './views/dashboard.js';
import buildView   from './views/buildings.js';
import resView     from './views/research.js';
import compView    from './views/composer.js';
import armyView    from './views/army.js';
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
[loginView, signupView, dashView, buildView, resView, compView, armyView, socialView]
  .forEach(v => router.register(v));

// ── Initialize status sidebar ──────────────────────────────
initStatusBar(document.getElementById('status-bar'));

// ── Toast notifications for push messages ──────────────────
eventBus.on('quick_message', (data) => showToast(data.message || data.text || JSON.stringify(data)));
eventBus.on('notification',  (data) => showToast(data.message || data.text || JSON.stringify(data)));

function showToast(text) {
  const container = document.getElementById('toast-container');
  if (!container) return;
  const el = document.createElement('div');
  el.className = 'toast';
  el.textContent = text;
  container.appendChild(el);
  setTimeout(() => el.remove(), 5000);
}

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
    router.navigate('dashboard');
  }
});

// ── Start ──────────────────────────────────────────────────
// Show UI immediately, connect in the background
router.start();

(async () => {
  try {
    await api.connect();
    console.log('[app] connected to', wsUrl);
    state.setConnected(true);  // ensure status bar reflects connection
    await api.tryAutoLogin();
    api.startPolling();
  } catch (err) {
    console.warn('[app] initial connection failed, will retry:', err);
    // connect() rejects on error but onclose also triggers reconnect;
    // if it didn't (e.g. error before open), kick it manually
    api._scheduleReconnect();
  }
})();
