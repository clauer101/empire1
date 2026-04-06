/**
 * Buildings view — list buildings, show status, queue new builds.
 */

import { eventBus } from '../events.js';
import { formatEffect } from '../i18n.js';
import { rest } from '../rest.js';
import { ItemOverlay } from '../lib/item_overlay.js';
import { calcBuildSpeed } from '../lib/speed.js';

/** @type {import('../api.js').ApiClient} */
let api;
/** @type {import('../state.js').StateStore} */
let st;
/** @type {HTMLElement} */
let container;
let _unsub = [];
let hideCompleted = true; // default: hide completed items
/** @type {ItemOverlay} */
let _overlay = null;

function init(el, _api, _state) {
  container = el;
  api = _api;
  st = _state;

  container.innerHTML = `
    <h2 class="battle-title">🏗 Buildings<span class="title-resources"><span class="title-gold"></span><span class="title-culture"></span><span class="title-life"></span></span></h2>
    <div id="buildings-content">
      <div class="empty-state"><div class="empty-icon">▦</div><p>Loading buildings…</p></div>
    </div>
  `;
  _overlay = new ItemOverlay(_state);
  _overlay.mount(container);
}

async function enter() {
  _unsub.push(eventBus.on('state:summary', render));
  _unsub.push(eventBus.on('state:items', render));
  try {
    await Promise.all([rest.getSummary(), rest.getItems(), _overlay.ensureEraMap()]);
  } catch (err) {
    container.querySelector('#buildings-content').innerHTML =
      `<div class="error-msg">${err.message}</div>`;
  }
}

function leave() {
  _unsub.forEach(fn => fn());
  if (_overlay) _overlay.hide();
  _unsub = [];
  hideCompleted = true; // reset to default on leave
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

  const totalCost = (info) => Object.values(info.costs || {}).reduce((s, v) => s + v, 0);
  let entries = Object.entries(buildings).sort(([, a], [, b]) => totalCost(a) - totalCost(b));
  if (buildQueue) {
    entries.sort(([a], [b]) => (b === buildQueue) - (a === buildQueue));
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

    const fullEffort = info.effort;
    const stored = summary.buildings?.[iid];
    const remaining = (stored != null && stored < fullEffort) ? stored : fullEffort;
    const buildMultiplier = calcBuildSpeed(summary);
    const totalSecs  = buildMultiplier > 0 ? fullEffort / buildMultiplier : fullEffort;
    const remainSecs = buildMultiplier > 0 ? remaining  / buildMultiplier : remaining;
    const durationStr = fmtSecs(remainSecs);
    const pct = fullEffort > 0 ? Math.max(0, Math.min(100, (1 - remaining / fullEffort) * 100)) : 0;

    // Format costs
    const wasStarted = stored != null && stored < fullEffort;
    const costsStr = fmtCosts(info.costs, summary, wasStarted);

    return `<tr>
      <td class="col-name" data-label="Name">
        <div class="item-header" style="display:flex; align-items:flex-start; justify-content:space-between;">
          <div style="flex:1;">
            <div><strong>${status === 'in-progress' ? '🔨 ' : ''}${info.name || iid}</strong></div>
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
        <div class="detail-row"><span class="detail-label">Duration:</span> <span style="font-variant-numeric:tabular-nums">${durationStr}</span></div>
        <div style="background:var(--border-color,#333);border-radius:3px;height:6px;margin:2px 0 4px"><div style="background:#4fc3f7;width:${pct.toFixed(1)}%;height:100%;border-radius:3px;transition:width .5s"></div></div>
        ${info.costs && Object.keys(info.costs).length > 0 ? `<div class="detail-row"><span class="detail-label">Costs:</span> ${costsStr}</div>` : ''}
        ${info.effects && Object.keys(info.effects).length > 0 ? `<div class="detail-row"><span class="detail-label">Effects:</span>${fmtEffects(info.effects)}</div>` : ''}
        ${(unlocksMap[iid] || []).length > 0 ? `<div class="detail-row"><span class="detail-label">Required for:</span> ${(unlocksMap[iid] || []).map(u =>
          _overlay.linkBadge(u.iid, u.name, u.category)
        ).join('')}</div>` : ''}
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

  _overlay.bindBadgeClicks(el);

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

function fmtCosts(costs, summary, wasStarted = false) {
  if (!costs || Object.keys(costs).length === 0) return '—';

  const currentResources = summary?.resources || {};

  return Object.entries(costs)
    .map(([resource, cost]) => {
      const current = currentResources[resource] || 0;
      const canAfford = current >= cost;
      const color = canAfford ? 'var(--text)' : 'var(--danger)';
      const strike = wasStarted && resource === 'gold';

      // Format resource name with icon
      let icon = '';
      if (resource === 'gold') icon = '💰';
      else if (resource === 'culture') icon = '📚';
      else if (resource === 'life') icon = '❤️';

      const resourceName = resource.charAt(0).toUpperCase() + resource.slice(1);
      const extraStyle = strike ? 'text-decoration:line-through;opacity:0.45;' : '';

      return `<span style="color:${color};margin-right:12px;white-space:nowrap;${extraStyle}">${icon} ${Math.round(cost)} ${resourceName}</span>`;
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
