/**
 * App bootstrap — wires together Router, views, status sidebar.
 *
 * Economy communication goes through REST (rest.js).
 * WebSocket is only used on the defense page (managed by defense.js).
 */

import { rest } from './rest.js';
import { state } from './state.js';
import { eventBus } from './events.js';
import { Router } from './router.js';
import { debug } from './debug.js';

import loginView   from './views/login.js';
import dashView    from './views/status.js';
import buildView   from './views/buildings.js';
import resView     from './views/research.js';
import armyView    from './views/army.js';
import battleView  from './views/defense.js';
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
[loginView, signupView, dashView, buildView, resView, armyView, battleView, socialView]
  .forEach(v => router.register(v));

// ── Toast notifications for push messages ──────────────────
eventBus.on('quick_message', (data) => showToast(data.message || data.text || JSON.stringify(data)));
eventBus.on('notification',  (data) => showToast(data.message || data.text || JSON.stringify(data)));

// ── Item completed: immediately refresh items + summary ────
eventBus.on('server:item_completed', () => {
  Promise.all([rest.getSummary(), rest.getItems()]).catch(() => {});
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

// ── Incoming attack alarm on dashboard nav link ──────────────
const navMsgBadge = document.getElementById('nav-msg-badge');
const navDashboard = document.getElementById('nav-dashboard');
const navDefense = document.getElementById('nav-defense');
eventBus.on('state:summary', (data) => {
  const incoming = data?.attacks_incoming || [];
  const hasIncoming = incoming.length > 0;
  const hasActive = incoming.some(a => a.phase === 'in_siege' || a.phase === 'in_battle');

  if (navDashboard) navDashboard.classList.toggle('alarm', hasIncoming && !hasActive);
  if (navDefense)   navDefense.classList.toggle('alarm', hasActive);

  // Unread messages badge
  const unread = data?.unread_messages || 0;
  if (navMsgBadge) {
    navMsgBadge.textContent = unread > 9 ? '9+' : String(unread);
    navMsgBadge.style.display = unread > 0 ? '' : 'none';
  }
});

// ── Summary polling (every 5s while authenticated) ─────────
let _pollTimer = null;
let _prevCompletedCount = -1;

function startPolling() {
  if (_pollTimer) return;
  _pollTimer = setInterval(async () => {
    if (!state.auth.authenticated) return;
    try {
      const summary = await rest.getSummary();
      const count = ((summary?.completed_buildings ?? []).length)
                  + ((summary?.completed_research  ?? []).length);
      // First poll: just record baseline, don't fetch yet
      if (_prevCompletedCount === -1) {
        _prevCompletedCount = count;
        return;
      }
      // If any new item completed since last poll → refresh item catalog
      if (count > _prevCompletedCount) {
        rest.getItems().catch(() => {});
      }
      _prevCompletedCount = count;
    } catch (_) { /* ignore */ }
  }, 5000);
}

function stopPolling() {
  if (_pollTimer) { clearInterval(_pollTimer); _pollTimer = null; }
  _prevCompletedCount = -1;
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
    const target = router.pendingRoute || 'status';
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

  // 2. Activate router (no WS needed — defense view manages its own)
  router.start();
})();
