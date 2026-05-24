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
import { setEndRally, isGameFrozen, setSeasonResetActive } from './lib/game_state.js';
import { debug } from './debug.js';
import { formatEffect } from './i18n.js';
import { ERA_ROMAN, ERA_LABEL_EN, ERA_SPRITE_KEY } from './lib/eras.js';
import { pageTitle } from './lib/page_title.js';
import { fmtRes } from './lib/format.js';

import loginView from './views/login.js';
import dashView, { getCultureLeaderName, onLeaderUpdated } from './views/status.js?v=20260514a';
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
import globalmapView from './views/globalmap.js';
import globalempiresView from './views/globalempires.js';
import rulerView from './views/ruler.js';
import seasonResultsView from './views/seasonresults.js';

// ── Determine REST URL ─────────────────────────────────────
const params = new URLSearchParams(window.location.search);
const restUrl = params.get('rest') || window.location.origin;

// ── Instantiate core objects ───────────────────────────────
rest.init(restUrl);
pageTitle.init();
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
  globalmapView,
  globalempiresView,
  rulerView,
  seasonResultsView,
  logoutView,
].forEach((v) => router.register(v));

// ── Toast notifications for push messages ──────────────────
eventBus.on('quick_message', (data) =>
  showToast(data.message || data.text || JSON.stringify(data))
);
eventBus.on('notification', (data) => showToast(data.message || data.text || JSON.stringify(data)));
eventBus.on('ui:gold:spend', (amount) => { _liveGold = Math.max(0, _liveGold - amount); _tickTitleResources(); });

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


function _tickTitleResources() {
  const elapsed = isGameFrozen() ? 0 : (Date.now() - _liveTs) / 3600000; // hours
  const gold = _liveGold + _rateGold * elapsed;
  const culture = _liveCulture + _rateCulture * elapsed;
  appEl.querySelectorAll('.title-gold').forEach((el) => {
    el.textContent = '💰 ' + fmtRes(gold);
  });
  appEl.querySelectorAll('.title-culture').forEach((el) => {
    el.textContent = '🎭 ' + fmtRes(culture);
  });
}

function _updateTitleResources(r, rates) {
  _liveGold = r.gold ?? 0;
  _liveCulture = r.culture ?? 0;
  _rateGold = rates?.gold ?? 0;
  _rateCulture = rates?.culture ?? 0;
  _liveTs = Date.now();
  appEl.querySelectorAll('.title-life').forEach((el) => {
    el.innerHTML = '<span style="color:#e05c5c">❤︎</span> ' + fmtRes(r.life, 0);
  });
  if (!_liveTicker) _liveTicker = setInterval(_tickTitleResources, 100);
  _tickTitleResources();
}

// ── Incoming attack alarm on dashboard nav link ──────────────
const navMsgBadge = document.getElementById('nav-msg-badge');
const navDashboard = document.getElementById('nav-dashboard');
const navDefense = document.getElementById('nav-defense');
const navArmy = document.getElementById('nav-army');
const navTechtree = document.getElementById('nav-techtree');
const navWorkshop = document.getElementById('nav-workshop');
const navMessages = document.getElementById('nav-messages');

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
let _eraMap = null;
let _endRally = null; // { active, effects, seconds_remaining, end_criterion } from summary
let _selfName = '';

onLeaderUpdated(() => {
  if (_endRally?.active) _updateRallyBanner(_endRally, _selfName);
});

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
    <div class="era-season"></div>
    <div class="era-numeral"></div>
    <div class="era-name"></div>
    <img class="era-base-img" src="" alt="">
    <div class="era-effects"></div>
    <div class="era-rally" style="display:none">
      <div class="era-rally-title">⚔ End Rally Active</div>
      <div class="era-rally-effects"></div>
      <div class="era-rally-timer"></div>
    </div>
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
  // Fetch era map from server if not yet loaded
  if (!_eraMap) {
    try {
      _eraMap = await rest.getEraMap();
      _eraEffects = _eraMap.era_effects || {};
    } catch (_) {
      /* use empty */
    }
  }
  const era = _currentEra;
  const sprite = ERA_SPRITE_KEY[era] || 'stone';
  const effects = _eraEffects[era] || {};
  const seasonNum = _eraMap?.season_number ?? 1;
  const seasonTitle = _eraMap?.season_title ?? '';
  const seasonEl = _eraOverlay.querySelector('.era-season');
  if (seasonEl) {
    seasonEl.style.display = '';
    seasonEl.innerHTML = `<span class="era-season-num">Season ${seasonNum}</span>`
      + (seasonTitle ? `<span class="era-season-title">${seasonTitle}</span>` : '');
  }
  _eraOverlay.querySelector('.era-numeral').textContent = ERA_ROMAN[era] || '';
  _eraOverlay.querySelector('.era-name').textContent = ERA_LABEL_EN[era] || era;
  _eraOverlay.querySelector('.era-base-img').src = `/assets/sprites/bases/base_${sprite}.webp`;
  const effectRows = Object.entries(effects)
    .map(([k, v]) => `<div class="era-effect-row">${formatEffect(k, v)}</div>`)
    .join('');
  _eraOverlay.querySelector('.era-effects').innerHTML = effectRows;
  // Show end-rally section if active
  const rallyEl = _eraOverlay.querySelector('.era-rally');
  if (_endRally?.active) {
    const rallyEffectRows = Object.entries(_endRally.effects || {})
      .map(([k, v]) => `<div class="era-effect-row">${formatEffect(k, v)}</div>`)
      .join('');
    _eraOverlay.querySelector('.era-rally-effects').innerHTML = rallyEffectRows;
    const secsLeft = _endRally.seconds_remaining || 0;
    _eraOverlay.querySelector('.era-rally-timer').textContent =
      `Ends in ${_fmtOffset(secsLeft)}`;
    rallyEl.style.display = '';
  } else {
    rallyEl.style.display = 'none';
  }
  _eraOverlay.classList.add('visible');
}

function _hideEraOverlay() {
  _eraOverlay?.classList.remove('visible');
}

const navBrand = document.getElementById('nav-brand');
if (navBrand) navBrand.addEventListener('click', _showEraOverlay);

window.addEventListener('empire:attack', (e) => {
  const { uid, name } = e.detail || {};
  if (!uid) return;
  state.pendingAttackTarget = { uid: parseInt(uid, 10), name: name || '' };
  window.location.hash = '#army';
});

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
  if (data?.end_rally) {
    _endRally = data.end_rally;
    _selfName = data.name || _selfName;
    setEndRally(data.end_rally);
    _updateRallyBanner(data.end_rally, _selfName, data);
  }
  _updateSeasonResetBanner(data);
  const incoming = data?.attacks_incoming || [];
  const hasIncoming = incoming.length > 0;
  const hasActive = incoming.some((a) => a.phase === 'in_siege' || a.phase === 'in_battle');

  if (navDashboard) navDashboard.classList.remove('alarm');
  if (navDefense) navDefense.classList.toggle('alarm', hasActive);

  // Feature-gated nav links — hidden until the empire unlocks the effect
  const ef2 = data.effects || {};
  if (navArmy) navArmy.style.display = (ef2.enable_army ?? 0) > 0 ? '' : 'none';
  if (navTechtree) navTechtree.style.display = (ef2.enable_techtree ?? 0) > 0 ? '' : 'none';
  if (navWorkshop) navWorkshop.style.display = (ef2.enable_workshop ?? 0) > 0 ? '' : 'none';
  if (navMessages) navMessages.style.display = (ef2.enable_messages ?? 0) > 0 ? '' : 'none';

  // Unread messages badge
  const unread = data?.unread_messages || 0;
  if (navMsgBadge) {
    navMsgBadge.textContent = unread > 9 ? '9+' : String(unread);
    navMsgBadge.style.display = unread > 0 ? '' : 'none';
  }
});

// ── End-rally banner ─────────────────────────────────────────
let _rallySecondsRemaining = 0;
let _rallySecondsTs = 0; // Date.now() when _rallySecondsRemaining was set
let _rallyCountdownTimer = null;
let _rallyBannerBaseText = '';
let _rallyBannerBaseHtml = '';

function _fmtRallyTime(secs) {
  if (secs >= 86400) return `${Math.floor(secs / 86400)}d`;
  const h = Math.floor(secs / 3600);
  const m = Math.floor((secs % 3600) / 60);
  const s = Math.floor(secs % 60);
  return `${h}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
}

function _tickRallyBanner() {
  const banner = document.getElementById('rally-banner');
  if (!banner || banner.style.display === 'none') return;
  const elapsed = (Date.now() - _rallySecondsTs) / 1000;
  const secs = Math.max(0, _rallySecondsRemaining - elapsed);
  const timeStr = _fmtRallyTime(secs);
  banner.innerHTML = `${_rallyBannerBaseHtml} (season ends in ${timeStr})`;
  // Switch from per-day to countdown when under 1 day
  if (secs < 86400 && !_rallyCountdownTimer) {
    _rallyCountdownTimer = setInterval(_tickRallyBanner, 1000);
  }
}

function _updateGameOverBanner(rally, data) {
  const banner = document.getElementById('game-over-banner');
  if (!banner) return;
  const frozen = rally?.activated_at && !rally?.active;
  // Hide once leadtime is reached — season-reset banner takes over
  const nsl = data?.next_season_leadtime;
  const _utcMs = s => s ? new Date(s.endsWith('Z') || s.includes('+') ? s : s + 'Z').getTime() : 0;
  const inLeadtime = nsl && Date.now() >= _utcMs(nsl);
  // Also hide if wipe already happened (nsl cleared, no rally criterion left)
  const resetTriggered = !!data?.season_reset_triggered;
  const postWipe = resetTriggered && !nsl;
  if (!frozen || inLeadtime || postWipe) { banner.style.display = 'none'; return; }
  const winner = rally.culture_leader_name || getCultureLeaderName() || rally.triggered_by_name || '?';
  const winnerSafe = winner.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
  banner.innerHTML = `🏆 <strong>${winnerSafe}</strong> has won the season — Congratulations! <a href="#season-results" style="color:#ffd700;font-weight:bold;margin-left:10px;text-decoration:underline;">(view results)</a>`;
  banner.style.display = 'block';
  requestAnimationFrame(() => {
    document.documentElement.style.setProperty('--rally-banner-h', banner.offsetHeight + 'px');
  });
}

function _updateRallyBanner(rally, selfName, data) {
  const banner = document.getElementById('rally-banner');
  if (!banner) return;
  if (!rally?.active) {
    banner.style.display = 'none';
    if (!rally?.activated_at) document.documentElement.style.setProperty('--rally-banner-h', '0px');
    if (_rallyCountdownTimer) { clearInterval(_rallyCountdownTimer); _rallyCountdownTimer = null; }
    _updateGameOverBanner(rally, data);
    return;
  }
  const builderName = rally.triggered_by_name || '?';
  const builderUid = rally.triggered_by_uid;
  const criterion = rally.end_criterion_name || rally.end_criterion || 'the wonder';
  const leaderName = rally.culture_leader_name || getCultureLeaderName() || builderName;
  const leadingLabel = leaderName === selfName ? 'You are leading' : `${leaderName} is leading`;
  const nameLink = builderUid != null && builderName !== selfName
    ? `<a href="#army" data-attack-uid="${builderUid}" data-attack-name="${builderName}" style="color:inherit;font-weight:700;text-decoration:underline;cursor:pointer">${builderName}</a>`
    : `<strong>${builderName}</strong>`;
  _rallyBannerBaseText = `⚔ ${builderName} has built ${criterion} — ${leadingLabel}, go get them!`;
  _rallyBannerBaseHtml = `⚔ ${nameLink} has built ${criterion} — ${leadingLabel}, go get them!`;
  _rallySecondsRemaining = rally.seconds_remaining || 0;
  _rallySecondsTs = Date.now();
  // Start per-second countdown only when under 1 day
  if (_rallySecondsRemaining < 86400 && !_rallyCountdownTimer) {
    _rallyCountdownTimer = setInterval(_tickRallyBanner, 1000);
  }
  _tickRallyBanner();
  banner.style.display = 'block';
  requestAnimationFrame(() => {
    document.documentElement.style.setProperty('--rally-banner-h', banner.offsetHeight + 'px');
  });

  if (!banner._attackListenerAdded) {
    banner._attackListenerAdded = true;
    banner.addEventListener('click', (e) => {
      const a = e.target.closest('[data-attack-uid]');
      if (!a) return;
      e.preventDefault();
      const uid = parseInt(a.dataset.attackUid, 10);
      const name = a.dataset.attackName || '';
      state.pendingAttackTarget = { uid, name };
      window.location.hash = '#army';
    });
  }
}

// ── Season Reset Banner ──────────────────────────────────────
let _seasonResetTimer = null;
let _seasonResetTarget = 0; // epoch ms of next_season_start

function _tickSeasonResetBanner() {
  const banner = document.getElementById('season-reset-banner');
  if (!banner || banner.style.display === 'none') return;
  const secsLeft = Math.max(0, (_seasonResetTarget - Date.now()) / 1000);
  const h = Math.floor(secsLeft / 3600);
  const m = Math.floor((secsLeft % 3600) / 60);
  const s = Math.floor(secsLeft % 60);
  const timeStr = secsLeft >= 86400
    ? `${Math.floor(secsLeft / 86400)}d`
    : `${h}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
  const base = banner.dataset.baseText || '';
  banner.textContent = `${base} starts in ${timeStr}`;
}

function _updateSeasonResetBanner(data) {
  const banner = document.getElementById('season-reset-banner');
  if (!banner) return;

  const resetTriggered = !!data?.season_reset_triggered;
  const nss = data?.next_season_start;
  const nsl = data?.next_season_leadtime;
  const _toUtcMs = s => s ? new Date(s.endsWith('Z') || s.includes('+') ? s : s + 'Z').getTime() : 0;
  const inLeadtime = nsl && Date.now() >= _toUtcMs(nsl);
  // Show only once the leadtime timestamp is reached; resetTriggered alone
  // (set at rally end) is not enough — the game-over banner owns that phase.
  const shouldShow = inLeadtime || (resetTriggered && !nsl);

  setSeasonResetActive(resetTriggered);

  if (!shouldShow) {
    banner.style.display = 'none';
    if (_seasonResetTimer) { clearInterval(_seasonResetTimer); _seasonResetTimer = null; }
    document.documentElement.style.setProperty('--rally-banner-h', '0px');
    return;
  }

  const nextTitle = data?.next_season_title || '';
  const nextNum = (data?.season_number ?? 0) + 1;
  if (resetTriggered) {
    banner.dataset.baseText = `🌅 Season ${data?.season_number ?? ''} has ended — next season '${nextTitle || `Season ${nextNum}`}'`;
  } else {
    banner.dataset.baseText = `🌅 New season starting soon — Season ${nextNum}${nextTitle ? ': ' + nextTitle : ''}`;
  }
  _seasonResetTarget = _toUtcMs(nss);
  _tickSeasonResetBanner();
  banner.style.display = 'block';
  requestAnimationFrame(() => {
    document.documentElement.style.setProperty('--rally-banner-h', banner.offsetHeight + 'px');
  });
  if (!_seasonResetTimer) _seasonResetTimer = setInterval(_tickSeasonResetBanner, 1000);
}

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
  // 0. Load era-map for season-reset banner (no auth required)
  try {
    const eraMap = await rest.getEraMap();
    _eraEffects = eraMap.era_effects || {};
    _updateSeasonResetBanner(eraMap);
    // End-rally banner only shown when logged in
    if (eraMap.end_rally && state.auth?.authenticated) {
      _endRally = eraMap.end_rally;
      setEndRally(eraMap.end_rally);
      _updateRallyBanner(eraMap.end_rally, '', eraMap);
    }
  } catch (_) {
    /* non-fatal */
  }

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
