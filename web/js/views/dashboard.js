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
/** @type {Array|null} cached empire list */
let _empiresData = null;

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

  // Load empire rankings
  refreshEmpires();
}

function leave() {
  _unsub.forEach(fn => fn());
  _unsub = [];
  _empiresData = null;
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

async function refreshEmpires() {
  try {
    const resp = await rest.getEmpires();
    _empiresData = resp.empires || [];
    const sec = container.querySelector('#empires-section');
    if (sec) sec.innerHTML = renderEmpiresSection(_empiresData);
    bindEmpiresEvents();
  } catch (err) {
    console.error('[dashboard] getEmpires failed:', err);
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
        <div class="panel-row" style="border-top: 1px solid var(--border-color); margin-top: 4px; padding-top: 4px;">
          <span class="label">Next citizen</span>
          <span class="value">${fmt(price)} Culture</span>
        </div>
        ${(r.culture ?? 0) >= price ? `<div class="panel-row"><button id="buy-citizen-btn">Grow Settlement</button></div>` : ''}
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

    <div id="attacks-bar" style="margin-top:12px">
      ${renderAttacksBar(data)}
    </div>

    <div id="empires-section" style="margin-top:8px">
      ${renderEmpiresSection(_empiresData)}
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
          await new Promise(r => setTimeout(r, 2000));
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

  // Bind empire list events (attack buttons, refresh)
  bindEmpiresEvents();

  // Bind incoming attack clicks
  el.querySelectorAll('.attack-in-clickable').forEach(entry => {
    entry.addEventListener('click', () => {
      const attackId = parseInt(entry.dataset.attackId, 10);
      const attackerUid = parseInt(entry.dataset.attackerUid, 10);
      st.pendingIncomingAttack = { attack_id: attackId, attacker_uid: attackerUid };
      window.location.hash = '#battle';
    });
  });
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
        if (resourceType === 'life') {
          html += `<div class="panel-row"><span class="label">+${offset.toFixed(3)}</span><span class="value">(${item.name || iid})</span></div>`;
        }else{
          html += `<div class="panel-row"><span class="label">+${offset.toFixed(2)}</span><span class="value">(${item.name || iid})</span></div>`;
        }
        
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
        html += `<div class="panel-row"><span class="label">+${(modifier * 100).toFixed()}%</span><span class="value">(${item.name || iid})</span></div>`;
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

// ── Attacks status bar ───────────────────────────────────

function _resolveEmpireName(uid) {
  if (_empiresData) {
    const e = _empiresData.find(x => x.uid === uid);
    if (e) return e.name;
  }
  return `#${uid}`;
}

function _fmtSecs(s) {
  if (s == null || s < 0) return '—';
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  const sec = Math.floor(s % 60);
  if (h > 0) return `${h}h ${m}m`;
  if (m > 0) return `${m}m ${sec}s`;
  return `${sec}s`;
}

const PHASE_LABEL = {
  travelling: { text: 'travelling', cls: 'phase-travelling' },
  in_siege:   { text: 'siege',      cls: 'phase-siege' },
  in_battle:  { text: 'battle',     cls: 'phase-battle' },
};

function _attackEntry(a, direction) {
  const pInfo = PHASE_LABEL[a.phase] || { text: a.phase, cls: '' };
  const otherUid  = direction === 'in' ? a.attacker_uid : a.defender_uid;
  const empName   = _resolveEmpireName(otherUid);
  const icon      = direction === 'in' ? '⚠' : '→';

  let countdown = '';
  let pct = 0;
  if (a.phase === 'travelling') {
    countdown = `<span class="atk-cd">${_fmtSecs(a.eta_seconds)}</span>`;
    pct = a.total_eta_seconds > 0
      ? Math.round((1 - a.eta_seconds / a.total_eta_seconds) * 100)
      : 0;
  } else if (a.phase === 'in_siege') {
    countdown = `<span class="atk-cd">${_fmtSecs(a.siege_remaining_seconds)}</span>`;
    pct = a.total_siege_seconds > 0
      ? Math.round((1 - a.siege_remaining_seconds / a.total_siege_seconds) * 100)
      : 0;
  } else if (a.phase === 'in_battle') {
    countdown = `<span class="atk-cd atk-cd-battle">⚔ battle!</span>`;
    pct = 100;
  }
  pct = Math.max(0, Math.min(100, pct));

  return `
    <div class="attack-entry attack-${direction}${direction === 'in' ? ' attack-in-clickable' : ''}" ${direction === 'in' ? `data-attack-id="${a.attack_id}" data-attacker-uid="${a.attacker_uid}" title="Click to open battle view" style="cursor:pointer"` : ''}>
      <div class="atk-row">
        <span class="atk-icon">${icon}</span>
        <span class="atk-name">${empName}</span>
        <span class="phase-tag ${pInfo.cls}">${pInfo.text}</span>
        ${countdown}
      </div>
      <div class="atk-progress-wrap">
        <div class="atk-progress-bar atk-progress-${a.phase.replace('_','-')}" style="width:${pct}%"></div>
      </div>
    </div>`;
}

function renderAttacksBar(data) {
  const incoming = (data.attacks_incoming || []);
  const outgoing = (data.attacks_outgoing || []);

  const inRows  = incoming.length
    ? incoming.map(a => _attackEntry(a, 'in')).join('')
    : '<div class="atk-empty">No active attacks</div>';
  const outRows = outgoing.length
    ? outgoing.map(a => _attackEntry(a, 'out')).join('')
    : '<div class="atk-empty">No active attacks</div>';

  const inHeader  = `Incoming${incoming.length ? ` <span class="atk-badge atk-badge-in">${incoming.length}</span>` : ''}`;
  const outHeader = `Outgoing${outgoing.length ? ` <span class="atk-badge atk-badge-out">${outgoing.length}</span>` : ''}`;

  return `
    <div class="panel attacks-bar-panel">
      <div class="attacks-bar-grid">
        <div>
          <div class="panel-header">${inHeader}</div>
          ${inRows}
        </div>
        <div>
          <div class="panel-header">${outHeader}</div>
          ${outRows}
        </div>
      </div>
    </div>`;
}

function renderEffects(effects) {
  if (!effects || Object.keys(effects).length === 0) {
    return '<div class="panel-row"><span class="value">—</span></div>';
  }
  return Object.entries(effects)
    .map(([k, v]) => `<div class="panel-row"><span class="label">${formatEffect(k, v)}</span><span class="value"></span></div>`)
    .join('');
}

function renderEmpiresSection(empires) {
  if (!empires) {
    return `<div class="panel"><div class="panel-header">Known Empires <button id="empires-refresh-btn" style="float:right;font-size:11px;padding:2px 6px;">↻</button></div><div class="panel-row"><span class="value">Loading…</span></div></div>`;
  }
  if (empires.length === 0) {
    return `<div class="panel"><div class="panel-header">Known Empires <button id="empires-refresh-btn" style="float:right;font-size:11px;padding:2px 6px;">↻</button></div><div class="panel-row"><span class="value">—</span></div></div>`;
  }

  const rows = empires.map((e, i) => `
    <div class="panel-row" style="display:grid;grid-template-columns:24px 1fr 90px 56px 46px;gap:6px;align-items:center;">
      <span style="color:#888;font-size:0.85em;">${i + 1}</span>
      <span class="label" style="font-weight:${e.is_self ? 'bold' : 'normal'};color:${e.is_self ? 'var(--accent, #4fc3f7)' : 'inherit'};">${e.name}${e.username ? ` <span style="color:#888;font-weight:normal;font-size:0.85em;">(${e.username})</span>` : ''}${e.is_self ? ' ★' : ''}</span>
      <span class="value" style="color:#ffa726;">${fmtNumber(e.culture)} ✦</span>
      ${e.is_self
        ? '<span></span><span></span>'
        : `<button class="attack-btn" data-uid="${e.uid}" data-name="${e.name}" style="font-size:11px;padding:2px 6px;background:var(--danger,#e53935);border-color:var(--danger,#e53935);">⚔</button>
           <button class="msg-btn" data-uid="${e.uid}" data-name="${e.name}" style="font-size:11px;padding:2px 6px;">✉</button>`
      }
    </div>
  `).join('');

  return `
    <div class="panel">
      <div class="panel-header">Known Empires <button id="empires-refresh-btn" style="float:right;font-size:11px;padding:2px 6px;">↻</button></div>
      <div style="display:grid;grid-template-columns:24px 1fr 90px 56px 46px;gap:6px;padding:4px 8px;font-size:0.78em;color:#888;border-bottom:1px solid var(--border-color);">
        <span>#</span><span>Name</span><span>Culture</span><span></span><span></span>
      </div>
      ${rows}
    </div>
  `;
}

function bindEmpiresEvents() {
  const sec = container.querySelector('#empires-section');
  if (!sec) return;

  const refreshBtn = sec.querySelector('#empires-refresh-btn');
  if (refreshBtn) refreshBtn.onclick = () => refreshEmpires();

  sec.querySelectorAll('.attack-btn').forEach(btn => {
    btn.onclick = () => onAttackClick(btn);
  });

  sec.querySelectorAll('.msg-btn').forEach(btn => {
    btn.onclick = () => onMessageClick(btn);
  });
}

function onMessageClick(btn) {
  const targetUid = parseInt(btn.dataset.uid, 10);
  const targetName = btn.dataset.name;
  st.pendingMessageTarget = { uid: targetUid, name: targetName };
  window.location.hash = '#social';
}

async function onAttackClick(btn) {
  const targetUid = parseInt(btn.dataset.uid, 10);
  const targetName = btn.dataset.name;
  st.pendingAttackTarget = { uid: targetUid, name: targetName };
  window.location.hash = '#army';
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
