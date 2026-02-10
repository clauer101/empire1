/**
 * Status sidebar — live quick-status panels on the right.
 *
 * Shows: connection state, resources, build/research progress,
 * military overview.
 */

import { eventBus } from '../events.js';
import { state } from '../state.js';

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
      <div class="progress"><div class="progress-fill" id="sb-build-bar"></div></div>
      <div class="panel-row" style="margin-top:8px">
        <span class="label">Research</span>
        <span class="value" id="sb-research">idle</span>
      </div>
      <div class="progress"><div class="progress-fill" id="sb-research-bar"></div></div>
    </div>

    <div class="panel" id="sb-military">
      <div class="panel-header">Military</div>
      <div class="panel-row">
        <span class="label">Armies</span>
        <span class="value" id="sb-armies">—</span>
      </div>
      <div id="sb-attacks"></div>
    </div>
  `;

  // Subscribe to state events
  _unsub.push(eventBus.on('state:connected',    () => setConnected(true)));
  _unsub.push(eventBus.on('state:disconnected',  () => setConnected(false)));
  _unsub.push(eventBus.on('state:auth',           onAuth));
  _unsub.push(eventBus.on('state:summary',        onSummary));
  _unsub.push(eventBus.on('state:items',           () => { if (state.summary) onSummary(state.summary); }));
  _unsub.push(eventBus.on('state:military',        onMilitary));
  _unsub.push(eventBus.on('server:attack_phase_changed',  onAttackPhaseChanged));
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

  // Build queue — build_queue is the IID, remaining from active_buildings
  const activeBld = data.active_buildings || {};
  const bldEl = _el.querySelector('#sb-building');
  const bBar = _el.querySelector('#sb-build-bar');
  if (data.build_queue) {
    const iid = data.build_queue;
    const remaining = activeBld[iid];
    if (remaining != null) {
      const total = state.items?.buildings?.[iid]?.effort || remaining || 1;
      const pct = Math.min(100, Math.max(0, (1 - remaining / total) * 100));
      bldEl.textContent = `${state.items?.buildings?.[iid]?.name || iid} (${fmtEffort(remaining)})`;
      bBar.style.width = `${pct.toFixed(0)}%`;
    } else {
      bldEl.textContent = 'idle';
      bBar.style.width = '0%';
    }
  } else {
    bldEl.textContent = 'idle';
    bBar.style.width = '0%';
  }

  // Research queue — research_queue is the IID, remaining from active_research
  const activeRes = data.active_research || {};
  const resEl = _el.querySelector('#sb-research');
  const rBar = _el.querySelector('#sb-research-bar');
  if (data.research_queue) {
    const iid = data.research_queue;
    const remaining = activeRes[iid];
    if (remaining != null) {
      const total = state.items?.knowledge?.[iid]?.effort || remaining || 1;
      const pct = Math.min(100, Math.max(0, (1 - remaining / total) * 100));
      resEl.textContent = `${state.items?.knowledge?.[iid]?.name || iid} (${fmtEffort(remaining)})`;
      rBar.style.width = `${pct.toFixed(0)}%`;
    } else {
      resEl.textContent = 'idle';
      rBar.style.width = '0%';
    }
  } else {
    resEl.textContent = 'idle';
    rBar.style.width = '0%';
  }

  // Attacks progress
  const attacksEl = _el.querySelector('#sb-attacks');
  const outgoing = data.attacks_outgoing || [];
  const incoming = data.attacks_incoming || [];

  if (outgoing.length === 0 && incoming.length === 0) {
    attacksEl.innerHTML = '';
    return;
  }

  let html = '';

  for (const atk of outgoing) {
    const total = atk.total_eta_seconds || 60;
    const remaining = atk.eta_seconds || 0;
    const pct = Math.min(100, Math.max(0, (1 - remaining / total) * 100));
    const armyName = _findArmyName([], atk.army_aid);
    const phaseStr = atk.phase || 'travelling';
    html += `
      <div class="panel-row" style="margin-top:8px">
        <span class="label">⚔ ${armyName}</span>
        <span class="value" title="Phase: ${phaseStr}">${fmtTime(remaining)}</span>
      </div>
      <div class="progress"><div class="progress-fill" style="width:${pct.toFixed(0)}%"></div></div>
    `;
  }

  for (const atk of incoming) {
    const phaseStr = atk.phase || 'travelling';
    
    if (phaseStr === 'in_battle') {
      // Battle ongoing: full red bar + link to composer
      html += `
        <div class="panel-row" style="margin-top:8px">
          <span class="value"><a href="#composer" style="color:var(--danger);font-weight:bold">⚠ BATTLE ONGOING</a></span>
        </div>
        <div class="progress"><div class="progress-fill" style="width:100%; background:var(--danger)"></div></div>
      `;
    } else if (phaseStr === 'in_siege') {
      // Siege phase: show remaining siege time
      const totalSiege = atk.total_siege_seconds || 30;
      const remainingSiege = atk.siege_remaining_seconds || 0;
      const pct = Math.min(100, Math.max(0, (1 - remainingSiege / totalSiege) * 100));
      html += `
        <div class="panel-row" style="margin-top:8px">
          <span class="label">⚠ Siege ongoing</span>
          <span class="value" title="Phase: ${phaseStr}">${fmtTime(remainingSiege)}</span>
        </div>
        <div class="progress"><div class="progress-fill" style="width:${pct.toFixed(0)}%; background:var(--danger)"></div></div>
      `;
    } else {
      // Travelling phase: show ETA
      const total = atk.total_eta_seconds || 60;
      const remaining = atk.eta_seconds || 0;
      const pct = Math.min(100, Math.max(0, (1 - remaining / total) * 100));
      html += `
        <div class="panel-row" style="margin-top:8px">
          <span class="label">⚠ Incoming</span>
          <span class="value" title="Phase: ${phaseStr}">${fmtTime(remaining)}</span>
        </div>
        <div class="progress"><div class="progress-fill" style="width:${pct.toFixed(0)}%; background:var(--danger)"></div></div>
      `;
    }
  }

  attacksEl.innerHTML = html;
}

function onMilitary(data) {
  if (!data) return;
  const armies = data.armies || [];
  _el.querySelector('#sb-armies').textContent = armies.length;
}

function _findArmyName(armies, aid) {
  for (const a of armies) {
    if (a.aid === aid) return a.name;
  }
  return `Army ${aid}`;
}

function onAttackPhaseChanged(msg) {
  if (!msg) return;
  // Refresh summary data when phase changes to update attack display
  if (state.summary) {
    onSummary(state.summary);
  }
}

function fmtTime(seconds) {
  if (seconds == null || seconds <= 0) return 'arrived';
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return m > 0 ? `${m}m ${s}s` : `${s}s`;
}

function fmt(n) {
  if (n == null) return '—';
  if (typeof n !== 'number') return String(n);
  return n.toLocaleString('de-DE');
}

function fmtEffort(n) {
  if (n == null) return '—';
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000)     return `${(n / 1_000).toFixed(1)}K`;
  return String(Math.round(n));
}
