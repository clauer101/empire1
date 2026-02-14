/**
 * Research view — knowledge tech tree, queue research.
 */

import { eventBus } from '../events.js';
import { formatEffect } from '../i18n.js';
import { rest } from '../rest.js';

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
    await Promise.all([rest.getSummary(), rest.getItems()]);
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
  const completed = new Set([
    ...(summary.completed_research || []),
    ...(summary.completed_buildings || []),
  ]);
  const researchQueue = summary.research_queue;  // Only this item is "researching"
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
    else if (iid === researchQueue) status = 'in-progress';

    const badgeClass = `badge badge--${status}`;
    const badgeText = status === 'in-progress' ? 'researching' : status;

    // Calculate progress: full_effort - remaining = done
    const fullEffort = info.effort;
    const remaining = summary.knowledge?.[iid] ?? fullEffort;  // If not started, remaining = full effort
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
      <td>
        ${status === 'available'
          ? `<button class="btn-sm research-btn" data-iid="${iid}">Research</button><div class="research-msg"></div>`
          : ''}
      </td>
    </tr>`;
  }).join('');

  el.innerHTML = `<table>
    <thead><tr><th>Name</th><th>Description</th><th>Effort</th><th>Effects</th><th>Requires</th><th>Status</th><th></th></tr></thead>
    <tbody>${rows}</tbody>
  </table>`;

  el.querySelectorAll('.research-btn').forEach(btn => {
    btn.addEventListener('click', async () => {
      btn.disabled = true;
      const msgEl = btn.nextElementSibling;
      msgEl.textContent = '';
      const iid = btn.dataset.iid;
      const currentRow = btn.closest('tr');
      const currentStatusCell = currentRow.querySelector('td:nth-child(6)');
      const currentActionCell = currentRow.querySelector('td:nth-child(7)');
      
      try {
        const resp = await rest.buildItem(iid);
        if (resp.success) {
          const rows = el.querySelectorAll('tbody tr');
          
          // Clear old research status (change from "researching" to "available")
          rows.forEach(row => {
            const statusSpan = row.querySelector('td:nth-child(6) span');
            const actionCell = row.querySelector('td:nth-child(7)');
            if (statusSpan && statusSpan.textContent === 'researching') {
              statusSpan.className = 'badge badge--available';
              statusSpan.textContent = 'available';
              // Re-add button
              const oldIid = row.querySelector('strong').textContent.trim();
              actionCell.innerHTML = `<button class="btn-sm research-btn" data-iid="${oldIid}">Research</button><div class="research-msg"></div>`;
            }
          });
          
          // Update current research to "researching"
          currentStatusCell.querySelector('span').className = 'badge badge--in-progress';
          currentStatusCell.querySelector('span').textContent = 'researching';
          currentActionCell.innerHTML = '';
          
          msgEl.textContent = '✓ Research started!';
          msgEl.style.color = 'var(--success)';
        } else if (resp.error) {
          msgEl.textContent = `✗ ${resp.error}`;
          msgEl.style.color = 'var(--danger)';
        }
      } catch (err) {
        msgEl.textContent = `✗ ${err.message}`;
        msgEl.style.color = 'var(--danger)';
      } finally {
        btn.disabled = false;
        // Auto-hide message after 3s
        setTimeout(() => {
          msgEl.textContent = '';
        }, 3000);
      }
    });
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
  id: 'research',
  title: 'Research',
  init,
  enter,
  leave,
};
