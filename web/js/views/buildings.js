/**
 * Buildings view — list buildings, show status, queue new builds.
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
let hideCompleted = null; // null = auto: computed on first render

function init(el, _api, _state) {
  container = el;
  api = _api;
  st = _state;

  container.innerHTML = `
    <h2>Buildings</h2>
    <div id="buildings-content">
      <div class="empty-state"><div class="empty-icon">▦</div><p>Loading buildings…</p></div>
    </div>
  `;
}

async function enter() {
  _unsub.push(eventBus.on('state:summary', render));
  _unsub.push(eventBus.on('state:items', render));
  try {
    await Promise.all([rest.getSummary(), rest.getItems()]);
  } catch (err) {
    container.querySelector('#buildings-content').innerHTML =
      `<div class="error-msg">${err.message}</div>`;
  }
}

function leave() {
  _unsub.forEach(fn => fn());
  _unsub = [];
  hideCompleted = null; // reset so next visit re-evaluates the default
}

function render() {
  const el = container.querySelector('#buildings-content');
  const items = st.items;
  const summary = st.summary;
  if (!items || !summary) return;

  const completed = new Set([
    ...(summary.completed_buildings || []),
    ...(summary.completed_research || []),
  ]);
  const buildQueue = summary.build_queue;  // Only this item is "building"
  const buildings = items.buildings || {};

  // Build reverse-requirement map from full catalog (includes locked items)
  const catalog = items.catalog || {};
  // Fallback to per-category items for name lookup when not in catalog
  const _allByIid = Object.assign(
    {},
    items.buildings || {},
    items.knowledge || {},
    items.structures || {},
    items.critters || {},
  );
  const unlocksMap = {};
  for (const [depIid, depInfo] of Object.entries(catalog)) {
    const category = depInfo.item_type || 'building';
    const name = depInfo.name || _allByIid[depIid]?.name || depIid;
    for (const req of (depInfo.requirements || [])) {
      if (!unlocksMap[req]) unlocksMap[req] = [];
      unlocksMap[req].push({ iid: depIid, name, category });
    }
  }

  let entries = Object.entries(buildings).reverse();

  // Auto-default: hide completed only when 5+ buildings are done
  if (hideCompleted === null) {
    const completedBuildingCount = Object.keys(buildings).filter(iid => completed.has(iid)).length;
    hideCompleted = completedBuildingCount >= 5;
  }

  // Filter out completed items if toggle is active
  if (hideCompleted) {
    entries = entries.filter(([iid]) => !completed.has(iid));
  }

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

    // Build speed: (base_build_speed + build_speed_offset) * (1 + build_speed_modifier)
    const fullEffort = info.effort;
    const remaining = summary.buildings?.[iid] ?? fullEffort;  // If not started, remaining = full effort
    const buildMultiplier = ((summary.base_build_speed ?? 1) + (summary.effects?.build_speed_offset || 0)) * (1 + (summary.effects?.build_speed_modifier || 0));
    const totalSecs  = buildMultiplier > 0 ? fullEffort / buildMultiplier : fullEffort;
    const remainSecs = buildMultiplier > 0 ? remaining  / buildMultiplier : remaining;
    const durationStr = status === 'in-progress'
      ? `${fmtSecs(remainSecs)} remaining / ${fmtSecs(totalSecs)}`
      : fmtSecs(totalSecs);

    // Format costs
    const costsStr = fmtCosts(info.costs, summary);

    return `<tr>
      <td class="col-name" data-label="Name">
        <div class="item-header" style="display:flex; align-items:flex-start; justify-content:space-between;">
          <div style="flex:1;">
            <div><strong>${info.name || iid}</strong></div>
            <div class="build-msg"></div>
            <div class="item-description" style="font-size:0.9em; color:#666; margin-top:4px;">${info.description || '—'}</div>
          </div>
          <div style="margin-left:12px;">
            ${status === 'available' 
              ? `<button class="btn-sm build-btn" data-iid="${iid}">Build</button>` 
              : `<span class="${badgeClass}">${badgeText}</span>`}
          </div>
        </div>
      </td>
      <td class="col-details" data-label="Details">
        <div class="detail-row"><span class="detail-label">Costs:</span> ${costsStr}</div>
        <div class="detail-row"><span class="detail-label">Duration:</span> <span style="font-variant-numeric:tabular-nums">${durationStr}</span></div>
        <div class="detail-row"><span class="detail-label">Effects:</span>${fmtEffects(info.effects)}</div>
        <div class="detail-row"><span class="detail-label">Required for:</span> ${(unlocksMap[iid] || []).map(u =>
          `<span class="badge badge--unlock-${u.category} ${completed.has(u.iid) ? 'badge--completed' : ''}" style="margin-right:4px">${u.name}</span>`
        ).join('') || '—'}</div>
      </td>
    </tr>`;
  }).join('');

  el.innerHTML = `
    <div style="margin-bottom: 12px; display: flex; align-items: center; gap: 8px;">
      <label class="toggle-switch">
        <input type="checkbox" id="hide-completed-buildings" ${hideCompleted ? 'checked' : ''}>
        <span class="toggle-slider"></span>
      </label>
      <label for="hide-completed-buildings" style="font-size: 13px; cursor: pointer;">Hide completed</label>
    </div>
    <table class="items-table">
      <thead><tr><th>Name</th><th>Details</th></tr></thead>
      <tbody>${rows}</tbody>
    </table>
  `;

  // Add toggle event listener
  const toggleCheckbox = el.querySelector('#hide-completed-buildings');
  if (toggleCheckbox) {
    toggleCheckbox.addEventListener('change', (e) => {
      hideCompleted = e.target.checked;
      render();
    });
  }

  el.querySelectorAll('.build-btn').forEach(btn => {
    btn.addEventListener('click', async () => {
      btn.disabled = true;
      const iid = btn.dataset.iid;
      const currentRow = btn.closest('tr');
      const nameCell = currentRow.querySelector('.col-name');
      const msgEl = nameCell.querySelector('.build-msg');
      msgEl.textContent = '';
      
      try {
        const resp = await rest.buildItem(iid);
        if (resp.success) {
          msgEl.textContent = '✓ Building started!';
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
  if (!effects || Object.keys(effects).length === 0) return ' —';
  const items = Object.entries(effects)
    .map(([k, v]) => `<li>${formatEffect(k, v)}</li>`)
    .join('');
  return `<ul class="effects-list">${items}</ul>`;
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

function fmtSecs(s) {
  if (s == null || s < 0) return '—';
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  const sec = Math.floor(s % 60);
  if (h > 0) return `${h}h ${m}m ${sec}s`;
  if (m > 0) return `${m}m ${sec}s`;
  return `${sec}s`;
}

export default {
  id: 'buildings',
  title: 'Buildings',
  init,
  enter,
  leave,
};
