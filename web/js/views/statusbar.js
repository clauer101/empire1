/**
 * Status sidebar — live quick-status panels on the right.
 *
 * Shows: connection state, resources, build/research progress,
 * military overview.
 */

import { eventBus } from '../events.js';

let _el;
let _unsub = [];

/**
 * Initialize the status sidebar.
 * @param {HTMLElement} container  #status-bar element
 */
export function initStatusBar(container) {
  _el = container;

  _el.innerHTML = `
    <div class="panel" id="sb-connection">
      <div class="panel-header">Connection</div>
      <div class="panel-row">
        <span class="label"><span class="conn-dot offline" id="sb-conn-dot"></span>Status</span>
        <span class="value" id="sb-conn-text">Offline</span>
      </div>
      <div class="panel-row">
        <span class="label">Player</span>
        <span class="value" id="sb-player">—</span>
      </div>
    </div>

    <div class="panel" id="sb-resources">
      <div class="panel-header">Resources</div>
      <div class="panel-row">
        <span class="label">Gold</span>
        <span class="value" id="sb-gold">—</span>
      </div>
      <div class="panel-row">
        <span class="label">Culture</span>
        <span class="value" id="sb-culture">—</span>
      </div>
      <div class="panel-row">
        <span class="label">Life</span>
        <span class="value" id="sb-life">—</span>
      </div>
    </div>

    <div class="panel" id="sb-production">
      <div class="panel-header">Production</div>
      <div class="panel-row">
        <span class="label">Building</span>
        <span class="value" id="sb-building">idle</span>
      </div>
      <div class="progress"><div class="progress-fill" id="sb-build-bar" style="width:0%"></div></div>
      <div class="panel-row" style="margin-top:8px">
        <span class="label">Research</span>
        <span class="value" id="sb-research">idle</span>
      </div>
      <div class="progress"><div class="progress-fill" id="sb-research-bar" style="width:0%"></div></div>
    </div>

    <div class="panel" id="sb-military">
      <div class="panel-header">Military</div>
      <div class="panel-row">
        <span class="label">Armies</span>
        <span class="value" id="sb-armies">—</span>
      </div>
    </div>
  `;

  // Subscribe to state events
  _unsub.push(eventBus.on('state:connected',    () => setConnected(true)));
  _unsub.push(eventBus.on('state:disconnected',  () => setConnected(false)));
  _unsub.push(eventBus.on('state:auth',           onAuth));
  _unsub.push(eventBus.on('state:summary',        onSummary));
  _unsub.push(eventBus.on('state:military',        onMilitary));
}

function setConnected(online) {
  const dot  = _el.querySelector('#sb-conn-dot');
  const text = _el.querySelector('#sb-conn-text');
  dot.className = `conn-dot ${online ? 'online' : 'offline'}`;
  text.textContent = online ? 'Online' : 'Offline';
}

function onAuth(auth) {
  _el.querySelector('#sb-player').textContent =
    auth.authenticated ? (auth.username || `UID ${auth.uid}`) : '—';
}

function onSummary(data) {
  if (!data) return;
  const r = data.resources || {};
  _el.querySelector('#sb-gold').textContent    = fmt(r.gold);
  _el.querySelector('#sb-culture').textContent = fmt(r.culture);
  _el.querySelector('#sb-life').textContent    =
    `${fmt(r.life ?? data.life ?? 0)} / ${fmt(data.max_life ?? 0)}`;

  // Build queue
  const bld = data.active_buildings;
  const bldEl = _el.querySelector('#sb-building');
  bldEl.textContent = bld?.length ? bld[0] : 'idle';

  // Research queue
  const res = data.active_research;
  const resEl = _el.querySelector('#sb-research');
  resEl.textContent = res?.length ? res[0] : 'idle';

  // Progress bars (if percent fields exist)
  const bBar = _el.querySelector('#sb-build-bar');
  const rBar = _el.querySelector('#sb-research-bar');
  bBar.style.width = `${data.build_progress ?? 0}%`;
  rBar.style.width = `${data.research_progress ?? 0}%`;
}

function onMilitary(data) {
  if (!data) return;
  const armies = data.armies || [];
  _el.querySelector('#sb-armies').textContent = armies.length;
}

function fmt(n) {
  if (n == null) return '—';
  if (typeof n !== 'number') return String(n);
  return n.toLocaleString('de-DE');
}
