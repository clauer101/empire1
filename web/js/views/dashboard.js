/**
 * Dashboard view — empire summary overview.
 *
 * Displays: resources, citizens, build/research queue status,
 * army count, effects, artefacts.
 */

import { eventBus } from '../events.js';

/** @type {import('../api.js').ApiClient} */
let api;
/** @type {import('../state.js').StateStore} */
let st;
/** @type {HTMLElement} */
let container;
let _unsub = [];

function init(el, _api, _state) {
  container = el;
  api = _api;
  st = _state;

  container.innerHTML = `
    <h2>Empire Dashboard</h2>
    <div id="dashboard-content">
      <div class="empty-state"><div class="empty-icon">◈</div><p>Loading empire data…</p></div>
    </div>
  `;
}

function enter() {
  refresh();
  _unsub.push(eventBus.on('state:summary', render));
}

function leave() {
  _unsub.forEach(fn => fn());
  _unsub = [];
}

async function refresh() {
  try {
    const summary = await api.getSummary();
    st.setSummary(summary);
  } catch (err) {
    container.querySelector('#dashboard-content').innerHTML =
      `<div class="error-msg">Failed to load: ${err.message}</div>`;
  }
}

function render(data) {
  const el = container.querySelector('#dashboard-content');
  if (!data) {
    el.innerHTML = '<div class="empty-state"><div class="empty-icon">◈</div><p>No empire data available</p></div>';
    return;
  }
  const r = data.resources || {};

  const price = data.citizen_price;
  el.innerHTML = `
    <div style="display:grid; grid-template-columns:repeat(auto-fill, minmax(280px,1fr)); gap:8px;">

      <div class="panel">
        <div class="panel-header">Resources</div>
        <div class="panel-row"><span class="label">Gold</span><span class="value">${fmt(r.gold)}</span></div>
        <div class="panel-row"><span class="label">Culture</span><span class="value">${fmt(r.culture)}</span></div>
        <div class="panel-row"><span class="label">Life</span><span class="value">${fmt(r.life ?? data.life ?? 0)} / ${fmt(data.max_life ?? 0)}</span></div>
      </div>

      <div class="panel">
        <div class="panel-header">Citizens</div>
        ${renderCitizens(data.citizens)}
      </div>

      <div class="panel">
        <div class="panel-header">Buy Citizen</div>
        <div class="panel-row"><span class="label">Next price</span><span class="value">${fmt(price)} Culture</span></div>
        <div class="panel-row"><button id="buy-citizen-btn">Buy Citizen</button></div>
        <div class="panel-row" id="buy-citizen-msg"></div>
      </div>

      <div class="panel">
        <div class="panel-header">Production</div>
        ${renderProduction('Building', data.active_buildings)}
        ${renderProduction('Research', data.active_research)}
      </div>

      <div class="panel">
        <div class="panel-header">Military</div>
        <div class="panel-row"><span class="label">Armies</span><span class="value">${data.army_count ?? 0}</span></div>
      </div>

      <div class="panel">
        <div class="panel-header">Effects</div>
        ${renderEffects(data.effects)}
      </div>

      <div class="panel">
        <div class="panel-header">Artefacts</div>
        <div class="panel-row"><span class="value">${(data.artefacts || []).join(', ') || '—'}</span></div>
      </div>

    </div>
  `;
  const btn = el.querySelector('#buy-citizen-btn');
  if (btn) {
    btn.onclick = async () => {
      btn.disabled = true;
      const msgEl = el.querySelector('#buy-citizen-msg');
      msgEl.textContent = '';
      try {
        const resp = await api.upgradeCitizen();
        if (resp && resp.success) {
          msgEl.textContent = 'Citizen bought!';
          await refresh();
        } else {
          msgEl.textContent = resp && resp.error ? resp.error : 'Failed.';
        }
      } catch (err) {
        msgEl.textContent = err.message;
      }
      btn.disabled = false;
    };
  }
  // citizenPrice entfernt, Preis kommt vom Backend
}

function renderCitizens(citizens) {
  if (!citizens || Object.keys(citizens).length === 0) {
    return '<div class="panel-row"><span class="value">—</span></div>';
  }
  return Object.entries(citizens)
    .map(([k, v]) => `<div class="panel-row"><span class="label">${k}</span><span class="value">${v}</span></div>`)
    .join('');
}

function renderProduction(label, items) {
  if (!items || typeof items !== 'object' || Object.keys(items).length === 0) {
    return `<div class="panel-row"><span class="label">${label}</span><span class="value">idle</span></div>`;
  }
  return Object.entries(items)
    .map(([iid, remaining]) => `<div class="panel-row"><span class="label">${iid}</span><span class="value">${fmt(remaining)} left</span></div>`)
    .join('');
}

function renderEffects(effects) {
  if (!effects || Object.keys(effects).length === 0) {
    return '<div class="panel-row"><span class="value">—</span></div>';
  }
  return Object.entries(effects)
    .map(([k, v]) => `<div class="panel-row"><span class="label">${k}</span><span class="value">${v}</span></div>`)
    .join('');
}

function fmt(n) {
  if (n == null) return '—';
  if (typeof n !== 'number') return String(n);
  return n.toLocaleString('de-DE');
}

export default {
  id: 'dashboard',
  title: 'Dashboard',
  init,
  enter,
  leave,
};
