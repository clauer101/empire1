/**
 * Buildings view — list buildings, show status, queue new builds.
 */

import { eventBus } from '../events.js';
import { formatEffect } from '../i18n.js';

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
  const completed = new Set([
    ...(summary.completed_buildings || []),
    ...(summary.completed_research || []),
  ]);
  const buildQueue = summary.build_queue;  // Only this item is "building"
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
    else if (iid === buildQueue) status = 'in-progress';

    const badgeClass = `badge badge--${status}`;
    const badgeText = status === 'in-progress' ? 'building' : status;

    // Calculate progress: full_effort - remaining = done
    const fullEffort = info.effort;
    const remaining = summary.buildings?.[iid] ?? fullEffort;  // If not started, remaining = full effort
    const done = Math.max(0, fullEffort - remaining);
    const progressStr = `${fmtEffort(done)}/${fmtEffort(fullEffort)}`;

    return `<tr>
      <td><strong>${info.name || iid}</strong></td>
      <td style="max-width:250px; font-size:0.9em; color:#666">${info.description || '—'}</td>
      <td style="font-variant-numeric:tabular-nums">${progressStr}</td>
      <td>${fmtEffects(info.effects)}</td>
      <td>${(info.requirements || []).map(r =>
        `<span class="badge ${completed.has(r) ? 'badge--completed' : 'badge--locked'}" style="margin-right:4px">${r}</span>`
      ).join('') || '—'}</td>
      <td><span class="${badgeClass}">${badgeText}</span></td>
      <td>${status === 'available'
        ? `<button class="btn-sm build-btn" data-iid="${iid}">Build</button>`
        : ''}</td>
    </tr>`;
  }).join('');

  el.innerHTML = `<table>
    <thead><tr><th>Name</th><th>Description</th><th>Effort</th><th>Effects</th><th>Requires</th><th>Status</th><th></th></tr></thead>
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
  return String(Math.round(n));
}

function fmtEffects(effects) {
  if (!effects || Object.keys(effects).length === 0) return '—';
  return Object.entries(effects)
    .map(([k, v]) => `<span class="badge" style="margin-right:6px">${formatEffect(k, v)}</span>`)
    .join('');
}

export default {
  id: 'buildings',
  title: 'Buildings',
  init,
  enter,
  leave,
};
