/**
 * Generic item queue view factory.
 *
 * Used by buildings.js and research.js. All view-specific parameters are
 * passed via a config object so the rendering logic lives in one place.
 *
 * @param {object} cfg
 * @param {string}   cfg.id              - Route id
 * @param {string}   cfg.title           - Page title (with emoji)
 * @param {string}   cfg.contentId       - DOM id for the scrollable content div
 * @param {string}   cfg.loadingIcon     - Empty state icon character
 * @param {string}   cfg.loadingText     - Loading placeholder text
 * @param {string}   cfg.emptyText       - Text when no items are available
 * @param {string}   cfg.toggleId        - DOM id for the hide-completed checkbox
 * @param {string}   cfg.queueKey        - summary key for the active item (e.g. 'build_queue')
 * @param {string}   cfg.categoryKey     - items key for the item map (e.g. 'buildings')
 * @param {string}   cfg.storedKey       - summary key for progress map (e.g. 'buildings')
 * @param {string[]} cfg.completedKeys   - summary array keys marking completion
 * @param {string}   cfg.defaultCategory - fallback item_type for unlocksMap
 * @param {Function} cfg.speedFn         - calcBuildSpeed or calcResearchSpeed
 * @param {string}   cfg.progressColor   - CSS color for progress bar fill
 * @param {string}   cfg.actionIcon      - Icon shown on the action button / in-progress name
 * @param {string}   cfg.actionLabel     - Button label ('Build' / 'Research')
 * @param {string}   cfg.actionVerb      - In-progress badge text ('building' / 'researching')
 * @param {string}   cfg.msgClass        - CSS class for the inline feedback message div
 * @param {string}   cfg.btnClass        - CSS class for the action button
 * @param {string}   cfg.successMsg      - Success message after starting
 * @param {Function} cfg.apiAction       - (iid) => Promise — REST call to start the item
 */

import { eventBus } from '../events.js';
import { formatEffect } from '../i18n.js';
import { rest } from '../rest.js';
import { ItemOverlay } from './item_overlay.js';
import { fmtSecs } from './format.js';
import { ERA_YAML_TO_KEY, ERA_ROMAN } from './eras.js';

export function createQueueView(cfg) {
  let api, st, container;
  let _unsub = [];
  let hideCompleted = true;
  let _overlay = null;
  let _tickTimer = null;
  let _tickRemainSecs = null;
  let _tickTs = null;

  function init(el, _api, _state) {
    container = el;
    api = _api;
    st = _state;

    container.innerHTML = `
      <h2 class="battle-title">${cfg.heading || cfg.title}<span class="title-resources"><span class="title-gold"></span><span class="title-culture"></span><span class="title-life"></span></span></h2>
      <div id="${cfg.contentId}">
        <div class="empty-state"><div class="empty-icon">${cfg.loadingIcon}</div><p>${cfg.loadingText}</p></div>
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
      if (err.message.includes('Unauthorized')) return; // router already redirects to login
      container.querySelector(`#${cfg.contentId}`).innerHTML =
        `<div class="error-msg">${err.message}</div>`;
    }
  }

  function leave() {
    _unsub.forEach((fn) => fn());
    if (_overlay) _overlay.hide();
    _unsub = [];
    hideCompleted = true;
    if (_tickTimer) {
      clearInterval(_tickTimer);
      _tickTimer = null;
    }
    _tickRemainSecs = null;
    _tickTs = null;
  }

  function _fmtEffects(effects) {
    if (!effects || Object.keys(effects).length === 0) return ' —';
    const items = Object.entries(effects)
      .map(([k, v]) => `<li>${formatEffect(k, v)}</li>`)
      .join('');
    return `<ul class="effects-list">${items}</ul>`;
  }

  function _fmtCosts(costs, summary, wasStarted = false, buildingDiscount = 0) {
    if (!costs || Object.keys(costs).length === 0) return '—';
    const res = summary?.resources || {};
    return Object.entries(costs)
      .map(([resource, cost]) => {
        const discounted = resource === 'gold' && buildingDiscount > 0
          ? cost * Math.max(0, 1 - buildingDiscount)
          : cost;
        const canAfford = (res[resource] || 0) >= discounted;
        const color = canAfford ? 'var(--text)' : 'var(--danger)';
        const strike = wasStarted && resource === 'gold';
        const icon =
          resource === 'gold'
            ? '💰'
            : resource === 'culture'
              ? '📚'
              : resource === 'life'
                ? '❤️'
                : '';
        const name = resource.charAt(0).toUpperCase() + resource.slice(1);
        const extra = strike ? 'text-decoration:line-through;opacity:0.45;' : '';
        return `<span style="color:${color};margin-right:12px;white-space:nowrap;${extra}">${icon} ${Math.round(discounted)} ${name}</span>`;
      })
      .join('');
  }

  function render() {
    const el = container.querySelector(`#${cfg.contentId}`);
    const items = st.items;
    const summary = st.summary;
    if (!items || !summary) return;

const completed = new Set(cfg.completedKeys.flatMap((k) => summary[k] || []));
    const activeQueue = summary[cfg.queueKey];
    const itemMap = items[cfg.categoryKey] || {};

    // Build reverse-requirement map from full catalog
    const catalog = items.catalog || {};

    // Compute excluded set: items blocked by a completed item's excludes (both directions)
    const excluded = new Set();
    for (const compIid of completed) {
      for (const excl of (catalog[compIid]?.excludes || [])) excluded.add(excl);
    }
    for (const [iid, info] of Object.entries(catalog)) {
      if (!completed.has(iid)) {
        for (const excl of (info.excludes || [])) {
          if (completed.has(excl)) excluded.add(iid);
        }
      }
    }
    const _allByIid = Object.assign(
      {},
      items.buildings || {},
      items.knowledge || {},
      items.structures || {},
      items.critters || {}
    );
    const unlocksMap = {};
    for (const [depIid, depInfo] of Object.entries(catalog)) {
      const category = depInfo.item_type || cfg.defaultCategory;
      const name = depInfo.name || _allByIid[depIid]?.name || depIid;
      for (const req of depInfo.requirements || []) {
        if (!unlocksMap[req]) unlocksMap[req] = [];
        unlocksMap[req].push({ iid: depIid, name, category });
      }
    }

    const totalCost = (info) => Object.values(info.costs || {}).reduce((s, v) => s + v, 0);
    let entries = Object.entries(itemMap).sort(([, a], [, b]) => totalCost(a) - totalCost(b));
    if (activeQueue) {
      entries.sort(([a], [b]) => (b === activeQueue) - (a === activeQueue));
    }
    if (hideCompleted) {
      entries = entries.filter(([iid]) => !completed.has(iid) && !excluded.has(iid));
    }

    if (entries.length === 0) {
      el.innerHTML = `<div class="empty-state"><p>${cfg.emptyText}</p></div>`;
      return;
    }

    const rows = entries
      .map(([iid, info]) => {
        let status = 'available';
        if (completed.has(iid)) status = 'completed';
        else if (excluded.has(iid)) status = 'excluded';
        else if (iid === activeQueue) status = 'in-progress';

        const badgeText = status === 'in-progress' ? cfg.actionVerb : status;

        const fullEffort = info.effort;
        const stored = summary[cfg.storedKey]?.[iid];
        const remaining = stored != null && stored < fullEffort ? stored : fullEffort;
        const multiplier = cfg.speedFn(summary);
        const remainSecs = multiplier > 0 ? remaining / multiplier : remaining;
        const pct =
          fullEffort > 0 ? Math.max(0, Math.min(100, (1 - remaining / fullEffort) * 100)) : 0;
        const wasStarted = stored != null && stored < fullEffort;

        const imgUrl = info.image ? `/${info.image}/${info.image.split('/').pop()}.webp` : '';
        return `<tr>
        <td class="col-name" data-label="Name" style="padding:0;">
          <div class="item-header" style="position:relative;display:flex;align-items:flex-start;justify-content:space-between;overflow:hidden;height:100%;padding:8px 12px;box-sizing:border-box;">
            ${imgUrl ? `<div class="item-bg" style="position:absolute;inset:0;background-size:cover;background-position:center;background-repeat:no-repeat;filter:blur(0.2px);transform:scale(1.02);" data-bg="${imgUrl}"></div><div class="item-bg-overlay" style="position:absolute;inset:0;background:rgba(0,0,0,0.55);display:none;"></div>` : ''}
            <div style="flex:1;position:relative;">
              <div><strong style="font-size:1.1em;">${status === 'in-progress' ? cfg.actionIcon : ''}${info.name || iid}</strong>${info.era ? `<span style="font-size:0.75em;color:#c9a84c;margin-left:6px;font-weight:400;">${ERA_ROMAN[ERA_YAML_TO_KEY[info.era]] || ''}</span>` : ''}</div>
              <div class="${cfg.msgClass}"></div>
              <div class="item-description" style="font-size:0.9em; color:#aaa; margin-top:4px;">${info.description || '—'}</div>
            </div>
            <div style="margin-left:12px;position:relative;">
              ${
                status === 'available'
                  ? `<button class="btn-sm ${cfg.btnClass}" data-iid="${iid}">${cfg.actionLabel}</button>`
                  : status === 'excluded'
                    ? `<span class="badge badge--excluded">excluded</span>`
                    : `<span class="badge badge--${status}">${badgeText}</span>`
              }
            </div>
          </div>
        </td>
        <td class="col-details" data-label="Details">
          <div class="detail-row"><span class="detail-label">Duration:</span> <span style="font-variant-numeric:tabular-nums"${status === 'in-progress' ? ` data-active-cd data-remain="${remainSecs.toFixed(2)}" data-full="${fullEffort}" data-mult="${multiplier.toFixed(6)}"` : ''}>${fmtSecs(remainSecs)}</span></div>
          <div style="background:var(--border-color,#333);border-radius:3px;height:6px;margin:2px 0 4px"><div class="queue-progress-bar" style="background:${cfg.progressColor};width:${pct.toFixed(1)}%;height:100%;border-radius:3px;transition:width .5s"></div></div>
          ${info.costs && Object.keys(info.costs).length > 0 ? `<div class="detail-row"><span class="detail-label">Costs:</span> ${_fmtCosts(info.costs, summary, wasStarted, cfg.categoryKey === 'buildings' ? (summary?.effects?.building_cost_modifier ?? 0) : 0)}</div>` : ''}
          ${info.effects && Object.keys(info.effects).length > 0 ? `<div class="detail-row"><span class="detail-label">Effects:</span>${_fmtEffects(info.effects)}</div>` : ''}
          ${(unlocksMap[iid] || []).length > 0 ? `<div class="detail-row"><span class="detail-label">Required for:</span> ${(unlocksMap[iid] || []).map((u) => _overlay.linkBadge(u.iid, u.name, u.category)).join('')}</div>` : ''}
          ${(info.excludes || []).length > 0 ? `<div class="detail-row"><span class="detail-label" style="color:var(--danger,#ef5350)">Excludes:</span> ${(info.excludes).map((e) => { const ci = catalog[e]; return ci ? _overlay.linkBadge(e, ci.name || e, ci.item_type || 'building') : `<span class="tt-ubadge">${e}</span>`; }).join('')}</div>` : ''}
        </td>
      </tr>`;
      })
      .join('');

    el.innerHTML = `
      <div style="margin-bottom: 12px; display: flex; align-items: center; gap: 8px;">
        <label class="toggle-switch">
          <input type="checkbox" id="${cfg.toggleId}" ${hideCompleted ? 'checked' : ''}>
          <span class="toggle-slider"></span>
        </label>
        <label for="${cfg.toggleId}" style="font-size: 13px; cursor: pointer;">Hide completed &amp; excluded</label>
      </div>
      <table class="items-table">
        <thead><tr><th>Name</th><th>Details</th></tr></thead>
        <tbody>${rows}</tbody>
      </table>
    `;

    // Start/stop client-side countdown for the active item
    const cdSpan = el.querySelector('[data-active-cd]');
    if (cdSpan) {
      _tickRemainSecs = parseFloat(cdSpan.dataset.remain);
      _tickTs = Date.now();
      if (!_tickTimer) _tickTimer = setInterval(_tick, 1000);
    } else {
      if (_tickTimer) {
        clearInterval(_tickTimer);
        _tickTimer = null;
      }
      _tickRemainSecs = null;
      _tickTs = null;
    }

    el.querySelectorAll('.item-bg[data-bg]').forEach((bgDiv) => {
      const url = bgDiv.dataset.bg;
      const img = new Image();
      img.onload = () => {
        bgDiv.style.backgroundImage = `url('${url}')`;
        const overlay = bgDiv.nextElementSibling;
        if (overlay && overlay.classList.contains('item-bg-overlay')) overlay.style.display = '';
      };
      img.src = url;
    });

    el.querySelector(`#${cfg.toggleId}`).addEventListener('change', (e) => {
      hideCompleted = e.target.checked;
      render();
    });

    _overlay.bindBadgeClicks(el);

    el.querySelectorAll(`.${cfg.btnClass}`).forEach((btn) => {
      btn.addEventListener('click', async () => {
        btn.disabled = true;
        const iid = btn.dataset.iid;
        const msgEl = btn.closest('tr').querySelector(`.${cfg.msgClass}`);
        msgEl.textContent = '';
        try {
          const resp = await cfg.apiAction(iid);
          if (resp.success) {
            msgEl.textContent = cfg.successMsg;
            msgEl.style.color = 'var(--success)';
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
          setTimeout(() => {
            msgEl.textContent = '';
          }, 3000);
        }
      });
    });
  }

  function _tick() {
    if (_tickRemainSecs == null || _tickTs == null) return;
    const el = container.querySelector(`#${cfg.contentId}`);
    if (!el) return;
    const cdSpan = el.querySelector('[data-active-cd]');
    if (!cdSpan) return;

    const elapsed = (Date.now() - _tickTs) / 1000;
    const remaining = Math.max(0, _tickRemainSecs - elapsed);
    cdSpan.textContent = fmtSecs(remaining);

    const fullEffort = parseFloat(cdSpan.dataset.full);
    const mult = parseFloat(cdSpan.dataset.mult);
    if (fullEffort > 0 && mult > 0) {
      const remainEffort = remaining * mult;
      const pct = Math.max(0, Math.min(100, (1 - remainEffort / fullEffort) * 100));
      const bar = cdSpan.closest('td')?.querySelector('.queue-progress-bar');
      if (bar) bar.style.width = pct.toFixed(1) + '%';
    }
  }

  return { id: cfg.id, title: cfg.title, init, enter, leave };
}
