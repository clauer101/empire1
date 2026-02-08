/**
 * Buildings view — list buildings, show status, queue new builds.
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
    <h2>Buildings</h2>
    <div class="form-row" style="margin-bottom:16px">
      <input type="text" id="buildings-filter" placeholder="Filter buildings…" style="max-width:280px">
    </div>
    <div id="buildings-content">
      <div class="empty-state"><div class="empty-icon">▦</div><p>Loading buildings…</p></div>
    </div>
  `;

  container.querySelector('#buildings-filter').addEventListener('input', () => render());
}

async function enter() {
  _unsub.push(eventBus.on('state:summary', render));
  _unsub.push(eventBus.on('state:items', render));
  try {
    await Promise.all([api.getSummary(), api.getItems()]);
  } catch (err) {
    container.querySelector('#buildings-content').innerHTML =
      `<div class="error-msg">${err.message}</div>`;
  }
}

function leave() {
  _unsub.forEach(fn => fn());
  _unsub = [];
}

function render() {
  const el = container.querySelector('#buildings-content');
  const items = st.items;
  const summary = st.summary;
  if (!items || !summary) return;

  const filter = (container.querySelector('#buildings-filter')?.value || '').toLowerCase();
  const completed = new Set(summary.completed_buildings || []);
  const active = new Set(summary.active_buildings || []);
  const buildings = items.buildings || {};

  const entries = Object.entries(buildings)
    .filter(([iid, info]) => {
      const name = (info.name || iid).toLowerCase();
      return !filter || name.includes(filter) || iid.toLowerCase().includes(filter);
    });

  if (entries.length === 0) {
    el.innerHTML = '<div class="empty-state"><p>No buildings found</p></div>';
    return;
  }

  const rows = entries.map(([iid, info]) => {
    let status = 'available';
    if (completed.has(iid)) status = 'completed';
    else if (active.has(iid)) status = 'in-progress';

    const badgeClass = `badge badge--${status}`;
    const badgeText = status === 'in-progress' ? 'building' : status;

    return `<tr>
      <td>${info.name || iid}</td>
      <td style="font-variant-numeric:tabular-nums">${fmtEffort(info.effort)}</td>
      <td>${(info.requirements || []).join(', ') || '—'}</td>
      <td><span class="${badgeClass}">${badgeText}</span></td>
      <td>${status === 'available'
        ? `<button class="btn-sm build-btn" data-iid="${iid}">Build</button>`
        : ''}</td>
    </tr>`;
  }).join('');

  el.innerHTML = `<table>
    <thead><tr><th>Name</th><th>Effort</th><th>Requires</th><th>Status</th><th></th></tr></thead>
    <tbody>${rows}</tbody>
  </table>`;

  el.querySelectorAll('.build-btn').forEach(btn => {
    btn.addEventListener('click', () => api.buildItem(btn.dataset.iid));
  });
}

function fmtEffort(n) {
  if (n == null) return '—';
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000)     return `${(n / 1_000).toFixed(1)}K`;
  return String(n);
}

export default {
  id: 'buildings',
  title: 'Buildings',
  init,
  enter,
  leave,
};
