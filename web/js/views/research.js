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
let hideCompleted = false;

function init(el, _api, _state) {
  container = el;
  api = _api;
  st = _state;

  container.innerHTML = `
    <h2>Research</h2>
    <div id="research-content">
      <div class="empty-state"><div class="empty-icon">◉</div><p>Loading research…</p></div>
    </div>
  `;
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

  const completed = new Set([
    ...(summary.completed_research || []),
    ...(summary.completed_buildings || []),
  ]);
  const researchQueue = summary.research_queue;  // Only this item is "researching"
  const knowledge = items.knowledge || {};

  let entries = Object.entries(knowledge).reverse();
  
  // Filter out completed items if toggle is active
  if (hideCompleted) {
    entries = entries.filter(([iid]) => !completed.has(iid));
  }

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
    
    // Format costs
    const costsStr = fmtCosts(info.costs, summary);

    return `<tr>
      <td class="col-name" data-label="Name">
        <div class="item-header" style="display:flex; align-items:flex-start; justify-content:space-between;">
          <div style="flex:1;">
            <div><strong>${info.name || iid}</strong></div>
            <div class="research-msg"></div>
            <div class="item-description" style="font-size:0.9em; color:#666; margin-top:4px;">${info.description || '—'}</div>
          </div>
          <div style="margin-left:12px;">
            ${status === 'available' 
              ? `<button class="btn-sm research-btn" data-iid="${iid}">Research</button>` 
              : `<span class="${badgeClass}">${badgeText}</span>`}
          </div>
        </div>
      </td>
      <td class="col-details" data-label="Details">
        <div class="detail-row"><span class="detail-label">Costs:</span> ${costsStr}</div>
        <div class="detail-row"><span class="detail-label">Effort:</span> <span style="font-variant-numeric:tabular-nums">${progressStr}</span></div>
        <div class="detail-row"><span class="detail-label">Effects:</span> ${fmtEffects(info.effects)}</div>
        <div class="detail-row"><span class="detail-label">Requires:</span> ${(info.requirements || []).map(r =>
          `<span class="badge ${completed.has(r) ? 'badge--completed' : 'badge--locked'}" style="margin-right:4px">${r}</span>`
        ).join('') || '—'}</div>
      </td>
    </tr>`;
  }).join('');

  el.innerHTML = `
    <div style="margin-bottom: 12px; display: flex; align-items: center; gap: 8px;">
      <label class="toggle-switch">
        <input type="checkbox" id="hide-completed-research" ${hideCompleted ? 'checked' : ''}>
        <span class="toggle-slider"></span>
      </label>
      <label for="hide-completed-research" style="font-size: 13px; cursor: pointer;">Hide completed</label>
    </div>
    <table class="items-table">
      <thead><tr><th>Name</th><th>Details</th></tr></thead>
      <tbody>${rows}</tbody>
    </table>
  `;

  // Add toggle event listener
  const toggleCheckbox = el.querySelector('#hide-completed-research');
  if (toggleCheckbox) {
    toggleCheckbox.addEventListener('change', (e) => {
      hideCompleted = e.target.checked;
      render();
    });
  }

  el.querySelectorAll('.research-btn').forEach(btn => {
    btn.addEventListener('click', async () => {
      btn.disabled = true;
      const iid = btn.dataset.iid;
      const currentRow = btn.closest('tr');
      const nameCell = currentRow.querySelector('.col-name');
      const msgEl = nameCell.querySelector('.research-msg');
      msgEl.textContent = '';
      
      try {
        const resp = await rest.buildItem(iid);
        if (resp.success) {
          msgEl.textContent = '✓ Research started!';
          msgEl.style.color = 'var(--success)';
          // Fetch fresh summary, which triggers render via event
          await rest.getSummary();
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

function fmtCosts(costs, summary) {
  if (!costs || Object.keys(costs).length === 0) return '—';
  
  const currentResources = summary?.resources || {};
  
  return Object.entries(costs)
    .map(([resource, cost]) => {
      const current = currentResources[resource] || 0;
      const canAfford = current >= cost;
      const color = canAfford ? 'var(--text)' : 'var(--danger)';
      
      // Format resource name with icon
      let icon = '';
      if (resource === 'gold') icon = '💰';
      else if (resource === 'culture') icon = '📚';
      else if (resource === 'life') icon = '❤️';
      
      const resourceName = resource.charAt(0).toUpperCase() + resource.slice(1);
      
      return `<span style="color:${color};margin-right:12px;white-space:nowrap;">${icon} ${Math.round(cost)} ${resourceName}</span>`;
    })
    .join('');
}

export default {
  id: 'research',
  title: 'Research',
  init,
  enter,
  leave,
};
