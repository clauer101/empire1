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
import { formatEffect } from './i18n.js';

import loginView   from './views/login.js';
import dashView    from './views/status.js';
import buildView   from './views/buildings.js';
import resView     from './views/research.js';
import armyView    from './views/army.js';
import treeView    from './views/techtree.js';
import battleView  from './views/defense.js';
import socialView  from './views/social.js';
import signupView  from './views/signup.js';
import replayView  from './views/replay.js';

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
[loginView, signupView, dashView, buildView, resView, armyView, treeView, battleView, socialView, replayView]
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

// ── Gold display in page title ──────────────────────────────
let _lastResources = null;

function _fmtRes(val, digits = 0) {
  const v = val ?? 0;
  return v >= 1000 ? (Math.floor(v / 100) / 10) + 'k' : Math.floor(v * Math.pow(10, digits)) / Math.pow(10, digits);
}

function _updateTitleResources(r) {
  appEl.querySelectorAll('.title-gold').forEach(el => { el.textContent = '💰 ' + _fmtRes(r.gold); });
  appEl.querySelectorAll('.title-culture').forEach(el => { el.textContent = '🎭 ' + _fmtRes(r.culture); });
  appEl.querySelectorAll('.title-life').forEach(el => { el.innerHTML = '<span style="color:#e05c5c">❤</span> ' + _fmtRes(r.life, 1); });
}

// ── Incoming attack alarm on dashboard nav link ──────────────
const navMsgBadge = document.getElementById('nav-msg-badge');
const navDashboard = document.getElementById('nav-dashboard');
const navDefense = document.getElementById('nav-defense');

// When the user explicitly clicks the defense nav link while already on the
// defense view (e.g. after spectating an outgoing attack), force a full
// leave()/enter() cycle so spectator state is cleared and their own map loads.
if (navDefense) {
  navDefense.addEventListener('click', () => {
    if (router.currentRoute() === 'defense') {
      // Clear any pending spectate context so enter() treats this as own defense
      state.pendingSpectateAttack = null;
      battleView.leave();
      battleView.enter();
    }
    // Otherwise the normal hash-change navigation handles it
  });
}
const ERA_ROMAN = {
  STEINZEIT: 'I', NEOLITHIKUM: 'II', BRONZEZEIT: 'III', EISENZEIT: 'IV',
  MITTELALTER: 'V', RENAISSANCE: 'VI', INDUSTRIALISIERUNG: 'VII',
  MODERNE: 'VIII', ZUKUNFT: 'IX',
};

const ERA_LABEL_EN = {
  STEINZEIT: 'Stone Age', NEOLITHIKUM: 'Neolithic', BRONZEZEIT: 'Bronze Age',
  EISENZEIT: 'Iron Age', MITTELALTER: 'Middle Ages', RENAISSANCE: 'Renaissance',
  INDUSTRIALISIERUNG: 'Industrial Age', MODERNE: 'Modern Age', ZUKUNFT: 'Future',
};

const ERA_SPRITE_KEY = {
  STEINZEIT: 'stone', NEOLITHIKUM: 'neolithicum', BRONZEZEIT: 'bronze',
  EISENZEIT: 'iron', MITTELALTER: 'middle_ages', RENAISSANCE: 'renaissance',
  INDUSTRIALISIERUNG: 'industrial', MODERNE: 'modern', ZUKUNFT: 'future',
};

let _eraEffects = {}; // loaded from /api/era-map

function _fmtOffset(secs) {
  const h = Math.floor(secs / 3600);
  const m = Math.floor((secs % 3600) / 60);
  if (h > 0 && m > 0) return `${h}h ${m}m`;
  if (h > 0) return `${h}h`;
  return `${m}m`;
}

// ── Era overlay ─────────────────────────────────────────────
let _eraOverlay = null;
let _currentEra = null;

function _buildEraOverlay() {
  const el = document.createElement('div');
  el.id = 'era-overlay';
  el.innerHTML = `<div class="era-panel">
    <button class="era-close">✕</button>
    <div class="era-numeral"></div>
    <div class="era-name"></div>
    <img class="era-base-img" src="" alt="">
    <div class="era-effects"></div>
  </div>`;
  document.body.appendChild(el);
  el.addEventListener('click', (e) => { if (e.target === el) _hideEraOverlay(); });
  el.querySelector('.era-close').addEventListener('click', _hideEraOverlay);
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && _eraOverlay?.classList.contains('visible')) _hideEraOverlay();
  });
  return el;
}

async function _showEraOverlay() {
  if (!_currentEra) return;
  if (!_eraOverlay) _eraOverlay = _buildEraOverlay();
  // Fetch era effects from server if not yet loaded
  if (!Object.keys(_eraEffects).length) {
    try {
      const eraMap = await rest.getEraMap();
      _eraEffects = eraMap.era_effects || {};
    } catch (_) { /* use empty */ }
  }
  const era = _currentEra;
  const sprite = ERA_SPRITE_KEY[era] || 'stone';
  const effects = _eraEffects[era] || {};
  _eraOverlay.querySelector('.era-numeral').textContent = ERA_ROMAN[era] || '';
  _eraOverlay.querySelector('.era-name').textContent = ERA_LABEL_EN[era] || era;
  _eraOverlay.querySelector('.era-base-img').src = `/assets/sprites/bases/base_${sprite}.webp`;
  const effectRows = Object.entries(effects).map(([k, v]) =>
    `<div class="era-effect-row">${formatEffect(k, v)}</div>`
  ).join('');
  _eraOverlay.querySelector('.era-effects').innerHTML = effectRows;
  _eraOverlay.classList.add('visible');
}

function _hideEraOverlay() {
  _eraOverlay?.classList.remove('visible');
}

const navBrand = document.getElementById('nav-brand');
if (navBrand) navBrand.addEventListener('click', _showEraOverlay);

eventBus.on('state:summary', (data) => {
  if (data?.resources) {
    _lastResources = data.resources;
    _updateTitleResources(data.resources);
  }
  if (navBrand && data?.current_era) {
    _currentEra = data.current_era;
    navBrand.textContent = ERA_ROMAN[data.current_era] || data.current_era;
  }
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
