/**
 * App bootstrap — wires together Router, views, status sidebar.
 *
 * Economy communication goes through REST (rest.js).
 * WebSocket is only used on the defense page (managed by defense.js).
 */

import { rest } from './rest.js';
import { state } from './state.js';
import { prefetchAllSprites } from './lib/sprite_prefetcher.js';
import { eventBus } from './events.js';
import { Router } from './router.js';
import { debug } from './debug.js';
import { formatEffect } from './i18n.js';
import { ERA_ROMAN, ERA_LABEL_EN, ERA_SPRITE_KEY } from './lib/eras.js';

import loginView from './views/login.js';
import dashView from './views/status.js?v=20260413a';
import buildView from './views/buildings.js';
import resView from './views/research.js';
import armyView from './views/army.js';
import treeView from './views/techtree.js';
import battleView from './views/defense.js';
import socialView from './views/social.js';
import signupView from './views/signup.js';
import replayView from './views/replay.js';
import workshopView from './views/workshop.js';
import logoutView from './views/logout.js';

// ── Determine REST URL ─────────────────────────────────────
const params = new URLSearchParams(window.location.search);
const restUrl = params.get('rest') || window.location.origin;

// ── Instantiate core objects ───────────────────────────────
rest.init(restUrl);
const appEl = document.getElementById('app');
const router = new Router(appEl, null, state);

// On REST unauthorized, redirect to login
eventBus.on('rest:unauthorized', () => {
  rest.logout();
  router.navigate('login');
});

// ── Register views ─────────────────────────────────────────
[
  loginView,
  signupView,
  dashView,
  buildView,
  resView,
  armyView,
  treeView,
  battleView,
  socialView,
  replayView,
  workshopView,
  logoutView,
].forEach((v) => router.register(v));

// ── Toast notifications for push messages ──────────────────
eventBus.on('quick_message', (data) =>
  showToast(data.message || data.text || JSON.stringify(data))
);
eventBus.on('notification', (data) => showToast(data.message || data.text || JSON.stringify(data)));

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

// ── Resource live ticker ─────────────────────────────────────
let _lastResources = null;
let _liveGold = 0;
let _liveCulture = 0;
let _rateGold = 0; // per hour
let _rateCulture = 0; // per hour
let _liveTs = 0;
let _liveTicker = null;

function _fmtRes(val, digits = 0) {
  const v = val ?? 0;
  return v >= 1000
    ? Math.floor(v / 1000) + 'k'
    : Math.floor(v * Math.pow(10, digits)) / Math.pow(10, digits);
}

function _tickTitleResources() {
  const elapsed = (Date.now() - _liveTs) / 3600000; // hours
  const gold = _liveGold + _rateGold * elapsed;
  const culture = _liveCulture + _rateCulture * elapsed;
  appEl.querySelectorAll('.title-gold').forEach((el) => {
    el.textContent = '💰 ' + _fmtRes(gold);
  });
  appEl.querySelectorAll('.title-culture').forEach((el) => {
    el.textContent = '🎭 ' + _fmtRes(culture);
  });
}

function _updateTitleResources(r, rates) {
  _liveGold = r.gold ?? 0;
  _liveCulture = r.culture ?? 0;
  _rateGold = rates?.gold ?? 0;
  _rateCulture = rates?.culture ?? 0;
  _liveTs = Date.now();
  appEl.querySelectorAll('.title-life').forEach((el) => {
    el.innerHTML = '<span style="color:#e05c5c">❤</span> ' + _fmtRes(r.life, 0);
  });
  if (!_liveTicker) _liveTicker = setInterval(_tickTitleResources, 100);
  _tickTitleResources();
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
  el.addEventListener('click', (e) => {
    if (e.target === el) _hideEraOverlay();
  });
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
    } catch (_) {
      /* use empty */
    }
  }
  const era = _currentEra;
  const sprite = ERA_SPRITE_KEY[era] || 'stone';
  const effects = _eraEffects[era] || {};
  _eraOverlay.querySelector('.era-numeral').textContent = ERA_ROMAN[era] || '';
  _eraOverlay.querySelector('.era-name').textContent = ERA_LABEL_EN[era] || era;
  _eraOverlay.querySelector('.era-base-img').src = `/assets/sprites/bases/base_${sprite}.webp`;
  const effectRows = Object.entries(effects)
    .map(([k, v]) => `<div class="era-effect-row">${formatEffect(k, v)}</div>`)
    .join('');
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
    const ef = data.effects || {};
    const ci = data.citizens || {};
    const ce = data.citizen_effect || 0;
    const goldRate =
      (data.base_gold ?? 0 + (ef.gold_offset || 0)) *
      (1 + (ci.merchant || 0) * ce + (ef.gold_modifier || 0));
    const cultureRate =
      (data.base_culture ?? 0 + (ef.culture_offset || 0)) *
      (1 + (ci.artist || 0) * ce + (ef.culture_modifier || 0));
    _updateTitleResources(data.resources, { gold: goldRate, culture: cultureRate });
  }
  if (navBrand && data?.current_era) {
    _currentEra = data.current_era;
    navBrand.textContent = ERA_ROMAN[data.current_era] || data.current_era;
  }
  const incoming = data?.attacks_incoming || [];
  const hasIncoming = incoming.length > 0;
  const hasActive = incoming.some((a) => a.phase === 'in_siege' || a.phase === 'in_battle');

  if (navDashboard) navDashboard.classList.remove('alarm');
  if (navDefense) navDefense.classList.toggle('alarm', hasActive);

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
      const count =
        (summary?.completed_buildings ?? []).length + (summary?.completed_research ?? []).length;
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
    } catch (_) {
      /* ignore */
    }
  }, 5000);
}

function stopPolling() {
  if (_pollTimer) {
    clearInterval(_pollTimer);
    _pollTimer = null;
  }
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
    window.location.hash = '#logout';
  }
});

eventBus.on('state:auth', (auth) => {
  if (auth.authenticated) {
    navAuthLabel.textContent = 'Settings';
    navAuth.href = '#';
    prefetchAllSprites().catch(() => {});
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

// Register Service Worker for sprite caching + push notifications
if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('/sw.js').catch(() => {});
}

(async () => {
  // 1. Try REST auto-login (validates stored JWT or credentials)
  try {
    await rest.tryAutoLogin();
  } catch (err) {
    console.warn('[app] REST auto-login failed:', err.message);
  }

  // 2. Activate router (no WS needed — defense view manages its own)
  router.start();

  // 3. Prefetch all sprites in the background after login
  if (state.auth?.authenticated) {
    prefetchAllSprites().catch(() => {});
  }
})();
