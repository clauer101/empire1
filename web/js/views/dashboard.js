/**
 * Dashboard view — empire summary overview.
 *
 * Displays: resources, citizens, build/research queue status,
 * army count, effects, artefacts.
 */

import { eventBus } from '../events.js';
import { formatEffect, fmtNumber } from '../i18n.js';
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
    <h2>Empire Dashboard</h2>
    <div id="dashboard-content">
      <div class="empty-state"><div class="empty-icon">◈</div><p>Loading empire data…</p></div>
    </div>
  `;
}

function enter() {
  // Register listeners first
  _unsub.push(eventBus.on('state:summary', render));
  _unsub.push(eventBus.on('state:items', () => { if (st.summary) render(st.summary); }));

  // Render immediately if summary already exists
  // (avoids race condition if event fired before listener was added)
  if (st.summary) {
    render(st.summary);
  } else {
    // Otherwise fetch it
    refresh();
  }
  
  // Ensure items are loaded (if not already)
  if (!st.items) {
    rest.getItems().catch(err => console.error('[dashboard] getItems failed:', err));
  }
}

function leave() {
  _unsub.forEach(fn => fn());
  _unsub = [];
}

async function refresh() {
  try {
    const summary = await rest.getSummary();
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
        <div class="panel-header">Grow Settlement</div>
        <div class="panel-row"><span class="label">Next citizen</span><span class="value">${fmt(price)} Culture</span></div>
        <div class="panel-row"><button id="buy-citizen-btn">Grow Settlement</button></div>
        <div class="panel-row" id="buy-citizen-msg"></div>
      </div>

      <div class="panel">
        <div class="panel-header">Production Modifiers</div>
        ${renderProductionModifiers(data.effects, data.citizens, data.citizen_effect, data.completed_buildings, st.items)}
      </div>

      <div class="panel">
        <div class="panel-header">Gold Income</div>
        ${renderResourceIncome('gold', data.effects, data.citizens, data.citizen_effect, data.base_gold, data.completed_buildings, st.items)}
      </div>

      <div class="panel">
        <div class="panel-header">Culture Income</div>
        ${renderResourceIncome('culture', data.effects, data.citizens, data.citizen_effect, data.base_culture, data.completed_buildings, st.items)}
      </div>

      <div class="panel">
        <div class="panel-header">Life Regeneration</div>
        ${renderResourceIncome('life', data.effects, data.citizens, data.citizen_effect, 0, data.completed_buildings, st.items)}
      </div>

      <div class="panel">
        <div class="panel-header">Military</div>
        <div class="panel-row"><span class="label">Armies</span><span class="value">${data.army_count ?? 0}</span></div>
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
        const resp = await rest.upgradeCitizen();
        if (resp.success) {
          msgEl.textContent = '✓ Citizen acquired!';
          msgEl.style.color = 'var(--success)';
          await refresh();
        } else if (resp.error) {
          msgEl.textContent = `✗ ${resp.error}`;
          msgEl.style.color = 'var(--danger)';
        }
      } catch (err) {
        msgEl.textContent = `✗ ${err.message}`;
        msgEl.style.color = 'var(--danger)';
      }
      btn.disabled = false;
    };
  }
  
  // Handle citizen +/- buttons
  const citizenBtns = el.querySelectorAll('.citizen-btn');
  citizenBtns.forEach(btn => {
    btn.onclick = async () => {
      const role = btn.dataset.role;
      const isMinus = btn.classList.contains('citizen-minus');
      
      // Ensure all roles are initialized
      const currentDistribution = {
        merchant: data.citizens?.merchant || 0,
        scientist: data.citizens?.scientist || 0,
        artist: data.citizens?.artist || 0,
      };
      
      if (isMinus) {
        if (currentDistribution[role] > 0) {
          currentDistribution[role]--;
        } else {
          return; // Can't go below 0
        }
      } else {
        currentDistribution[role]++;
      }
      
      try {
        btn.disabled = true;
        const resp = await rest.changeCitizen(currentDistribution);
        if (resp.success) {
          await refresh();
        } else if (resp.error) {
          console.error('[dashboard] change_citizen failed:', resp.error);
        }
      } catch (err) {
        console.error('[dashboard] change_citizen error:', err);
      } finally {
        btn.disabled = false;
      }
    };
  });
  // citizenPrice entfernt, Preis kommt vom Backend
}

function renderCitizens(citizens) {
  if (!citizens || Object.keys(citizens).length === 0) {
    return '<div class="panel-row"><span class="value">—</span></div>';
  }
  return Object.entries(citizens)
    .map(([k, v]) => {
      if (k === 'free') {
        // Free citizens: read-only, no buttons
        return `
          <div class="panel-row" style="display: flex; justify-content: space-between; align-items: center;">
            <span class="label">${k}</span>
            <span class="value" style="color: #999;">${v}</span>
          </div>
        `;
      }
      // Regular roles: show +/- buttons
      return `
        <div class="panel-row" style="display: flex; justify-content: space-between; align-items: center;">
          <span class="label">${k}</span>
          <div style="display: flex; gap: 4px; align-items: center;">
            <button class="citizen-btn citizen-minus" data-role="${k}" style="padding: 2px 6px; font-size: 12px;">−</button>
            <span class="value" style="min-width: 24px; text-align: center;">${v}</span>
            <button class="citizen-btn citizen-plus" data-role="${k}" style="padding: 2px 6px; font-size: 12px;">+</button>
          </div>
        </div>
      `;
    })
    .join('');
}

function renderProduction(label, items) {
  if (!items || typeof items !== 'object' || Object.keys(items).length === 0) {
    return `<div class="panel-row"><span class="label">${label}</span><span class="value">idle</span></div>`;
  }
  // Show only the first (current) item
  const entries = Object.entries(items);
  if (entries.length === 0) {
    return `<div class="panel-row"><span class="label">${label}</span><span class="value">idle</span></div>`;
  }
  const [iid, remaining] = entries[0];
  return `<div class="panel-row"><span class="label">${iid}</span><span class="value">${fmt(remaining)} left</span></div>`;
}

function renderProductionModifiers(effects, citizens, citizenEffect, completedBuildings, items) {
  let html = '';
  
  // Build speed modifier (NO citizen effect)
  const buildModifier = effects?.build_speed_modifier || 0;
  const buildMultiplier = 1 + buildModifier;
  
  // Collect building contributions
  let buildingContributions = [];
  if (completedBuildings && items?.buildings) {
    for (const iid of completedBuildings) {
      const item = items.buildings[iid];
      if (item?.effects?.build_speed_modifier > 0) {
        buildingContributions.push({
          name: item.name || iid,
          value: item.effects.build_speed_modifier
        });
      }
    }
  }
  
  // Build Speed section
  html += `<div class="panel-row"><span class="label">Construction Speed</span><span class="value">× ${buildMultiplier.toFixed(2)}</span></div>`;
  if (buildModifier > 0) {
    for (const contrib of buildingContributions) {
      html += `<div class="panel-row" style="font-size: 0.85em; margin-left: 12px;"><span class="label">+${(contrib.value * 100).toFixed(0)}%</span><span class="value">(${contrib.name})</span></div>`;
    }
  } else {
    html += `<div class="panel-row" style="font-size: 0.85em; margin-left: 12px;"><span class="value">no modifiers</span></div>`;
  }
  
  html += '<div class="panel-row" style="border-top: 1px solid #555; margin: 6px 0; padding-top: 6px;"></div>';
  
  // Research speed modifier (WITH scientist effect)
  const scientistCount = citizens?.scientist || 0;
  const scientistBonus = scientistCount * citizenEffect;
  const researchModifier = effects?.research_speed_modifier || 0;
  const researchMultiplier = 1 + scientistBonus + researchModifier;
  
  // Collect research contributions
  let researchContributions = [];
  if (completedBuildings && items?.buildings) {
    for (const iid of completedBuildings) {
      const item = items.buildings[iid];
      if (item?.effects?.research_speed_modifier > 0) {
        researchContributions.push({
          name: item.name || iid,
          value: item.effects.research_speed_modifier
        });
      }
    }
  }
  
  // Research Speed section
  html += `<div class="panel-row"><span class="label">Research Speed</span><span class="value">× ${researchMultiplier.toFixed(2)}</span></div>`;
  
  // Always show scientist bonus for research
  html += `<div class="panel-row" style="font-size: 0.85em; margin-left: 12px;"><span class="label">+${(scientistBonus * 100).toFixed(0)}%</span><span class="value">(${scientistCount} scientists × ${citizenEffect})</span></div>`;
  
  // Show building contributions
  if (researchModifier > 0) {
    for (const contrib of researchContributions) {
      html += `<div class="panel-row" style="font-size: 0.85em; margin-left: 12px;"><span class="label">+${(contrib.value * 100).toFixed(0)}%</span><span class="value">(${contrib.name})</span></div>`;
    }
  } 
  
  return html;
}

function renderResourceIncome(resourceType, effects, citizens, citizenEffect, baseAmount, completedBuildings, items) {
  let html = '';
  
  // Determine which citizen type and effect keys
  let citizenType, effectOffsetKey, effectModifierKey, citizenCount;
  if (resourceType === 'gold') {
    citizenType = 'merchant';
    effectOffsetKey = 'gold_offset';
    effectModifierKey = 'gold_modifier';
    citizenCount = citizens?.merchant || 0;
  } else if (resourceType === 'culture') {
    citizenType = 'artist';
    effectOffsetKey = 'culture_offset';
    effectModifierKey = 'culture_modifier';
    citizenCount = citizens?.artist || 0;
  } else if (resourceType === 'life') {
    citizenType = null; // No citizen effect for life
    effectOffsetKey = 'life_offset';
    effectModifierKey = null;
    citizenCount = 0;
  }

  // Base amount (only show if > 0)
  if (baseAmount > 0) {
    html += `<div class="panel-row"><span class="label">+${baseAmount.toFixed(2)}</span><span class="value">(base)</span></div>`;
  }
  
  // Building effects
  let totalOffset = baseAmount;
  if (completedBuildings && items?.buildings) {
    for (const iid of completedBuildings) {
      const item = items.buildings[iid];
      if (item?.effects?.[effectOffsetKey] > 0) {
        const offset = item.effects[effectOffsetKey];
        totalOffset += offset;
        html += `<div class="panel-row"><span class="label">+${offset.toFixed(2)}</span><span class="value">(${item.name || iid})</span></div>`;
      }
    }
  }
  
  // For life, only show offset without multiplier
  if (resourceType === 'life') {
    const color = '#90ee90'; // Light green for life
    html += '<div class="panel-row" style="border-top: 1px solid #555; margin: 6px 0; padding-top: 6px;"></div>';
    html += `<div class="panel-row" style="color: ${color}; font-weight: bold;"><span class="label">= ${totalOffset.toFixed(3)}/s</span></div>`;
    return html;
  }
  
  // Separator line
  html += '<div class="panel-row" style="border-top: 1px solid #555; margin: 6px 0; padding-top: 6px;"></div>';
  
  // Citizen bonus percentage
  const citizenBonus = citizenCount * citizenEffect;
  html += `<div class="panel-row"><span class="label">+${(citizenBonus * 100).toFixed(0)}%</span><span class="value">(${citizenCount} ${citizenType}s × ${citizenEffect})</span></div>`;
  
  // Effect modifiers from buildings
  let totalModifier = citizenBonus;
  let totalBuildingModifier = 0;
  if (completedBuildings && items?.buildings) {
    for (const iid of completedBuildings) {
      const item = items.buildings[iid];
      if (item?.effects?.[effectModifierKey] > 0) {
        const modifier = item.effects[effectModifierKey];
        totalBuildingModifier += modifier;
        html += `<div class="panel-row"><span class="label">+${(modifier * 100).toFixed(0)}%</span><span class="value">(${item.name || iid})</span></div>`;
      }
    }
  }
  totalModifier += totalBuildingModifier;
  
  // Final calculation line
  const multiplier = 1 + totalModifier;
  const total = totalOffset * multiplier;
  const color = resourceType === 'gold' ? '#4fc3f7' : '#ffa726';
  
  html += '<div class="panel-row" style="border-top: 1px solid #555; margin: 6px 0; padding-top: 6px;"></div>';
  html += `<div class="panel-row" style="color: ${color}; font-weight: bold;"><span class="label">= ${totalOffset.toFixed(2)} × ${multiplier.toFixed(2)}</span><span class="value">${total.toFixed(3)}/s</span></div>`;
  
  return html;
}

function renderEffects(effects) {
  if (!effects || Object.keys(effects).length === 0) {
    return '<div class="panel-row"><span class="value">—</span></div>';
  }
  return Object.entries(effects)
    .map(([k, v]) => `<div class="panel-row"><span class="label">${formatEffect(k, v)}</span><span class="value"></span></div>`)
    .join('');
}

function fmt(n) {
  return fmtNumber(n);
}

export default {
  id: 'dashboard',
  title: 'Dashboard',
  init,
  enter,
  leave,
};
