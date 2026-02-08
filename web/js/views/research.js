/**
 * Research view — knowledge tech tree, queue research.
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
    <h2>Research</h2>
    <div class="form-row" style="margin-bottom:16px">
      <input type="text" id="research-filter" placeholder="Filter research…" style="max-width:280px">
    </div>
    <div id="research-content">
      <div class="empty-state"><div class="empty-icon">◉</div><p>Loading research…</p></div>
    </div>
  `;

  container.querySelector('#research-filter').addEventListener('input', () => render());
}

async function enter() {
  _unsub.push(eventBus.on('state:summary', render));
  _unsub.push(eventBus.on('state:items', render));
  try {
    await Promise.all([api.getSummary(), api.getItems()]);
  } catch (err) {
    container.querySelector('#research-content').innerHTML =
      `<div class="error-msg">${err.message}</div>`;
  }
}

function leave() {
  _unsub.forEach(fn => fn());
  _unsub = [];
}

function render() {
  const el = container.querySelector('#research-content');
  const items = st.items;
  const summary = st.summary;
  if (!items || !summary) return;

  const filter = (container.querySelector('#research-filter')?.value || '').toLowerCase();
  const completed = new Set(summary.completed_research || []);
  const active = new Set(summary.active_research || []);
  const knowledge = items.knowledge || {};

  const entries = Object.entries(knowledge)
    .filter(([iid, info]) => {
      const name = (info.name || iid).toLowerCase();
      return !filter || name.includes(filter) || iid.toLowerCase().includes(filter);
    });

  if (entries.length === 0) {
    el.innerHTML = '<div class="empty-state"><p>No research found</p></div>';
    return;
  }

  const rows = entries.map(([iid, info]) => {
    let status = 'available';
    if (completed.has(iid)) status = 'completed';
    else if (active.has(iid)) status = 'in-progress';

    // check if requirements are met
    const reqsMet = (info.requirements || []).every(r => completed.has(r));
    if (status === 'available' && !reqsMet) status = 'locked';

    const badgeClass = `badge badge--${status}`;
    const badgeText = status === 'in-progress' ? 'researching' : status;

    return `<tr>
      <td>${info.name || iid}</td>
      <td style="font-variant-numeric:tabular-nums">${fmtEffort(info.effort)}</td>
      <td>${(info.requirements || []).map(r =>
        `<span class="badge ${completed.has(r) ? 'badge--completed' : 'badge--locked'}" style="margin-right:4px">${r}</span>`
      ).join('') || '—'}</td>
      <td><span class="${badgeClass}">${badgeText}</span></td>
      <td>${status === 'available'
        ? `<button class="btn-sm research-btn" data-iid="${iid}">Research</button>`
        : ''}</td>
    </tr>`;
  }).join('');

  el.innerHTML = `<table>
    <thead><tr><th>Name</th><th>Effort</th><th>Requires</th><th>Status</th><th></th></tr></thead>
    <tbody>${rows}</tbody>
  </table>`;

  el.querySelectorAll('.research-btn').forEach(btn => {
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
  id: 'research',
  title: 'Research',
  init,
  enter,
  leave,
};
