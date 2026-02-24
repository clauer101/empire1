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

  // Inject responsive grid style once
  if (!document.getElementById('dashboard-grid-style')) {
    const s = document.createElement('style');
    s.id = 'dashboard-grid-style';
    s.textContent = `
      .dashboard-4col{display:grid;gap:8px;grid-template-columns:repeat(4,1fr)}
      .dashboard-2col{display:grid;gap:8px;grid-template-columns:repeat(2,1fr)}
      @media(max-width:700px){.dashboard-4col,.dashboard-2col{grid-template-columns:1fr}}
      .csl-wrap{padding:4px 0 8px}
      .csl-track{position:relative;height:18px;border-radius:9px;overflow:visible;margin:8px 4px}
      .csl-seg{position:absolute;top:0;height:100%;transition:left .1s,width .1s}
      .csl-seg:first-child{border-radius:9px 0 0 9px}
      .csl-seg:last-child{border-radius:0 9px 9px 0}
      .csl-merchant{background:#4fc3f7}
      .csl-scientist{background:#ffa726}
      .csl-artist{background:#81c784}
      .csl-handle{position:absolute;top:50%;width:18px;height:18px;margin-top:-9px;margin-left:-9px;border-radius:50%;background:#fff;border:2px solid #555;cursor:grab;box-shadow:0 1px 4px rgba(0,0,0,.5);z-index:2;touch-action:none}
      .csl-handle:active{cursor:grabbing;border-color:var(--accent,#4fc3f7)}
      .csl-labels{display:flex;justify-content:space-between;font-size:0.82em;margin-top:4px;padding:0 4px}
      .csl-lbl{display:flex;flex-direction:column;align-items:center;gap:1px}
      .csl-lbl span{color:#bbb;font-size:0.9em}
      .csl-lbl strong{font-size:1.1em}
      .csl-hint{font-size:0.8em;color:#888;text-align:center;margin-bottom:2px;font-style:italic}
    `;
    document.head.appendChild(s);
  }

  container.innerHTML = `
    <h2>Empire Status</h2>
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
    <div class="dashboard-2col">

      <div class="panel">
        <div class="panel-header">Resources</div>
        <div class="panel-row"><span class="label">🪙 Gold</span><span class="value">${fmt(r.gold)}</span></div>
        <div class="panel-row"><span class="label">🎭 Culture</span><span class="value">${fmt(r.culture)}</span></div>
        <div class="panel-row"><span class="label">❤️ Life</span><span class="value">${fmt(r.life ?? data.life ?? 0)} / ${fmt(data.max_life ?? 0)}</span></div>
        <div style="border-top:1px solid var(--border-color);margin:8px 0 4px"></div>
        <div class="panel-header" style="margin-bottom:4px">Citizens</div>
        ${renderCitizens(data.citizens)}
        <div class="panel-row" style="border-top: 1px solid var(--border-color); margin-top: 4px; padding-top: 4px;">
          <span class="label">Next citizen</span>
          <span class="value">${fmt(price)} Culture</span>
        </div>
        ${(r.culture ?? 0) >= price ? `<div class="panel-row"><button id="buy-citizen-btn">Grow Settlement</button></div>` : ''}
        <div class="panel-row" id="buy-citizen-msg"></div>
      </div>

      <div class="panel">
        <div class="panel-header">Incoming</div>
        ${(() => {
          const inc = data.attacks_incoming || [];
          if (!inc.length) return `<div style="color:#666;font-size:0.85em;padding:2px 0">No incoming attacks</div>`;
          return inc.map(a => _attackEntry(a, 'in')).join('');
        })()}

        <div class="panel-header" style="margin-top:8px">Outgoing</div>
        ${(() => {
          const out = data.attacks_outgoing || [];
          if (!out.length) return `<div style="color:#666;font-size:0.85em;padding:2px 0">No outgoing attacks</div>`;
          return out.map(a => _attackEntry(a, 'out')).join('');
        })()}

        <div style="border-top:1px solid var(--border-color);margin:8px 0 4px"></div>
        <div class="panel-header">Research</div>
        ${(() => {
          const iid = data.research_queue;
          if (!iid) return `<div style="color:#666;font-size:0.85em;padding:2px 0">idle</div>`;
          const remaining = data.knowledge?.[iid] ?? 0;
          const effort = st?.items?.knowledge?.[iid]?.effort || 0;
          const itemName = st?.items?.knowledge?.[iid]?.name || iid;
          // Research speed: base_research_speed + research_speed_offset + research_speed_modifier + scientists * citizen_effect
          const scientistBonus = (data.citizens?.scientist || 0) * (data.citizen_effect || 0);
          const researchMultiplier = ((data.base_research_speed ?? 1) + (data.effects?.research_speed_offset || 0)) * (1 + (data.effects?.research_speed_modifier || 0) + scientistBonus);
          const wallSecs = researchMultiplier > 0 ? remaining / researchMultiplier : remaining;
          const pct = effort > 0 ? Math.max(0, Math.min(100, (1 - remaining / effort) * 100)) : 0;
          return `
            <div class="panel-row"><span class="label">${itemName}</span><span class="value" style="font-size:0.85em">${_fmtSecs(wallSecs)}</span></div>
            <div style="background:var(--border-color,#333);border-radius:3px;height:6px;margin:2px 0 4px">
              <div style="background:#ffa726;width:${pct.toFixed(1)}%;height:100%;border-radius:3px;transition:width .5s"></div>
            </div>`;
        })()}

        <div class="panel-header" style="margin-top:6px">Building</div>
        ${(() => {
          const iid = data.build_queue;
          if (!iid) return `<div style="color:#666;font-size:0.85em;padding:2px 0">idle</div>`;
          const remaining = data.buildings?.[iid] ?? 0;
          const effort = st?.items?.buildings?.[iid]?.effort || 0;
          const itemName = st?.items?.buildings?.[iid]?.name || iid;
          // Build speed: (base_build_speed + build_speed_offset) * (1 + build_speed_modifier)
          const buildMultiplier = ((data.base_build_speed ?? 1) + (data.effects?.build_speed_offset || 0)) * (1 + (data.effects?.build_speed_modifier || 0));
          const wallSecs = buildMultiplier > 0 ? remaining / buildMultiplier : remaining;
          const pct = effort > 0 ? Math.max(0, Math.min(100, (1 - remaining / effort) * 100)) : 0;
          return `
            <div class="panel-row"><span class="label">${itemName}</span><span class="value" style="font-size:0.85em">${_fmtSecs(wallSecs)}</span></div>
            <div style="background:var(--border-color,#333);border-radius:3px;height:6px;margin:2px 0 4px">
              <div style="background:#4fc3f7;width:${pct.toFixed(1)}%;height:100%;border-radius:3px;transition:width .5s"></div>
            </div>`;
        })()}
      </div>

    </div>

    <div id="empires-section" style="margin-top:8px">
      ${renderEmpiresSection(_empiresData)}
    </div>

    <div class="dashboard-4col" style="margin-top:8px;">

      <div class="panel">
        <div class="panel-header">Construction Speed</div>
        ${renderBuildSpeed(data.effects, data.completed_buildings, data.completed_research, st.items, data.base_build_speed)}
        <div class="panel-header" style="margin-top:10px">Research Speed</div>
        ${renderResearchSpeed(data.effects, data.citizens, data.citizen_effect, data.completed_buildings, data.completed_research, st.items, data.base_research_speed)}
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
  
  // Replace old citizen-btn handler with slider init
  _initCitizenSlider(el, data);

  // citizenPrice entfernt, Preis kommt vom Backend

  // Bind empire list events (attack buttons, refresh)
  bindEmpiresEvents();

  // Bind incoming attack clicks
  el.querySelectorAll('.attack-in-clickable').forEach(entry => {
    entry.addEventListener('click', () => {
      const attackId = parseInt(entry.dataset.attackId, 10);
      const attackerUid = parseInt(entry.dataset.attackerUid, 10);
      st.pendingIncomingAttack = { attack_id: attackId, attacker_uid: attackerUid };
      window.location.hash = '#defense';
    });
  });
}

function renderCitizens(citizens) {
  if (!citizens) return '<div class="panel-row"><span class="value">—</span></div>';
  const m = citizens.merchant || 0;
  const s = citizens.scientist || 0;
  const a = citizens.artist || 0;
  const total = m + s + a;
  if (total === 0) return '<div class="panel-row"><span class="value" style="color:#666;">No citizens yet</span></div>';
  const p1 = total > 0 ? (m / total * 100).toFixed(2) : 33.33;
  const p2 = total > 0 ? ((m + s) / total * 100).toFixed(2) : 66.66;
  const hint = (total >= 1 && total <= 5)
    ? `<div class="csl-hint">Drag the handles to assign citizens to tasks</div>`
    : '';
  return `${hint}
    <div class="csl-wrap" data-merchant="${m}" data-scientist="${s}" data-artist="${a}" data-total="${total}">
      <div class="csl-track">
        <div class="csl-seg csl-merchant" style="left:0;width:${p1}%"></div>
        <div class="csl-seg csl-scientist" style="left:${p1}%;width:${(p2-p1).toFixed(2)}%"></div>
        <div class="csl-seg csl-artist" style="left:${p2}%;width:${(100-p2).toFixed(2)}%"></div>
        <div class="csl-handle" id="csl-h1" style="left:${p1}%"></div>
        <div class="csl-handle" id="csl-h2" style="left:${p2}%"></div>
      </div>
      <div class="csl-labels">
        <div class="csl-lbl"><span>🫂 Merchant</span><strong id="csl-lbl-m">${m}</strong></div>
        <div class="csl-lbl"><span>🔭 Scientist</span><strong id="csl-lbl-s">${s}</strong></div>
        <div class="csl-lbl"><span>🎨 Artist</span><strong id="csl-lbl-a">${a}</strong></div>
      </div>
    </div>
  `;
}

function _initCitizenSlider(el, data) {
  const wrap = el.querySelector('.csl-wrap');
  if (!wrap) return;

  const total = parseInt(wrap.dataset.total, 10);
  if (total < 1) return;

  const track = wrap.querySelector('.csl-track');
  const h1 = wrap.querySelector('#csl-h1');
  const h2 = wrap.querySelector('#csl-h2');
  const segM = wrap.querySelector('.csl-merchant');
  const segS = wrap.querySelector('.csl-scientist');
  const segA = wrap.querySelector('.csl-artist');
  const lblM = wrap.querySelector('#csl-lbl-m');
  const lblS = wrap.querySelector('#csl-lbl-s');
  const lblA = wrap.querySelector('#csl-lbl-a');

  // Current state (integer steps out of total)
  let steps1 = parseInt(wrap.dataset.merchant, 10); // left handle = merchant count
  let steps2 = steps1 + parseInt(wrap.dataset.scientist, 10); // right handle = merchant+scientist

  function pct(steps) { return (steps / total * 100).toFixed(2) + '%'; }

  function updateDOM() {
    const p1 = steps1 / total * 100;
    const p2 = steps2 / total * 100;
    h1.style.left = p1.toFixed(2) + '%';
    h2.style.left = p2.toFixed(2) + '%';
    segM.style.width = p1.toFixed(2) + '%';
    segS.style.left  = p1.toFixed(2) + '%';
    segS.style.width = (p2 - p1).toFixed(2) + '%';
    segA.style.left  = p2.toFixed(2) + '%';
    segA.style.width = (100 - p2).toFixed(2) + '%';
    lblM.textContent = steps1;
    lblS.textContent = steps2 - steps1;
    lblA.textContent = total - steps2;
    // When handles overlap, raise the contextually correct one:
    // at far left (all artists) h2 should be on top so user can drag right
    // at far right (all merchants) h1 should be on top so user can drag left
    // in the middle with overlap, h1 on top (left drag is more natural)
    if (steps1 === steps2) {
      h1.style.zIndex = steps1 >= total ? '3' : '3';
      h2.style.zIndex = steps2 <= 0    ? '4' : '2';
    } else {
      h1.style.zIndex = '2';
      h2.style.zIndex = '2';
    }
  }

  let _sendTimer = null;
  function scheduleApiCall() {
    clearTimeout(_sendTimer);
    _sendTimer = setTimeout(async () => {
      const dist = { merchant: steps1, scientist: steps2 - steps1, artist: total - steps2 };
      try {
        const resp = await rest.changeCitizen(dist);
        if (resp.success) refresh();
        else if (resp.error) console.error('[citizen-slider]', resp.error);
      } catch (e) { console.error('[citizen-slider]', e); }
    }, 300);
  }

  function dragHandle(handle, isH1, e) {
    e.preventDefault();
    const rect = track.getBoundingClientRect();
    const startX = e.touches ? e.touches[0].clientX : e.clientX;

    // When both handles are at the same position we can't know ahead of time
    // which one to move. Defer the decision to the first pixel of movement:
    //   drag left  → move h1 (shrink merchants / grow artists)
    //   drag right → move h2 (shrink artists  / grow merchants)
    const overlapping = steps1 === steps2;
    let resolved = overlapping ? null : isH1; // null = not yet decided

    function onMove(ev) {
      const clientX = ev.touches ? ev.touches[0].clientX : ev.clientX;

      // Resolve direction on first move while handles overlap
      if (resolved === null) {
        const dx = clientX - startX;
        if (dx === 0) return; // no movement yet
        resolved = dx < 0; // true = isH1, false = isH2
      }

      const frac = Math.max(0, Math.min(1, (clientX - rect.left) / rect.width));
      const raw = Math.round(frac * total);
      if (resolved) {
        steps1 = Math.max(0, Math.min(steps2, raw));
      } else {
        steps2 = Math.max(steps1, Math.min(total, raw));
      }
      updateDOM();
      scheduleApiCall();
    }

    function onUp() {
      document.removeEventListener('mousemove', onMove);
      document.removeEventListener('mouseup', onUp);
      document.removeEventListener('touchmove', onMove);
      document.removeEventListener('touchend', onUp);
    }

    document.addEventListener('mousemove', onMove);
    document.addEventListener('mouseup', onUp);
    document.addEventListener('touchmove', onMove, { passive: false });
    document.addEventListener('touchend', onUp);
  }

  h1.addEventListener('mousedown',  e => dragHandle(h1, true,  e));
  h1.addEventListener('touchstart', e => dragHandle(h1, true,  e), { passive: false });
  h2.addEventListener('mousedown',  e => dragHandle(h2, false, e));
  h2.addEventListener('touchstart', e => dragHandle(h2, false, e), { passive: false });

  // Set initial z-indices in case handles already overlap on first render
  updateDOM();
}

function renderProduction(label, items) {  if (!items || typeof items !== 'object' || Object.keys(items).length === 0) {
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

function renderBuildSpeed(effects, completedBuildings, completedResearch, items, baseBuildSpeed) {
  baseBuildSpeed = baseBuildSpeed ?? 1.0;
  const buildOffset   = effects?.build_speed_offset   || 0;
  const buildModifier = effects?.build_speed_modifier || 0;
  const totalOffset   = baseBuildSpeed + buildOffset;
  const multiplier    = 1 + buildModifier;
  const effective     = totalOffset * multiplier;

  let html = '';
  html += `<div class="panel-row"><span class="label">+${baseBuildSpeed.toFixed(2)}</span><span class="value">(base)</span></div>`;
  if (completedBuildings && items?.buildings) {
    for (const iid of completedBuildings) {
      const item = items.buildings[iid];
      if (item?.effects?.build_speed_offset > 0)
        html += `<div class="panel-row"><span class="label">+${item.effects.build_speed_offset.toFixed(2)}</span><span class="value">(${item.name || iid})</span></div>`;
    }
  }
  if (completedResearch && items?.knowledge) {
    for (const iid of completedResearch) {
      const item = items.knowledge[iid];
      if (item?.effects?.build_speed_offset > 0)
        html += `<div class="panel-row"><span class="label">+${item.effects.build_speed_offset.toFixed(2)}</span><span class="value">(${item.name || iid})</span></div>`;
    }
  }
  html += '<div class="panel-row" style="border-top:1px solid #555;margin:6px 0;padding-top:6px"></div>';
  if (buildModifier > 0) {
    if (completedBuildings && items?.buildings) {
      for (const iid of completedBuildings) {
        const item = items.buildings[iid];
        if (item?.effects?.build_speed_modifier > 0)
          html += `<div class="panel-row"><span class="label">+${(item.effects.build_speed_modifier * 100).toFixed(0)}%</span><span class="value">(${item.name || iid})</span></div>`;
      }
    }
    if (completedResearch && items?.knowledge) {
      for (const iid of completedResearch) {
        const item = items.knowledge[iid];
        if (item?.effects?.build_speed_modifier > 0)
          html += `<div class="panel-row"><span class="label">+${(item.effects.build_speed_modifier * 100).toFixed(0)}%</span><span class="value">(${item.name || iid})</span></div>`;
      }
    }
  }
  html += '<div class="panel-row" style="border-top:1px solid #555;margin:6px 0;padding-top:6px"></div>';
  html += `<div class="panel-row" style="color:#4fc3f7;font-weight:bold"><span class="label">= ${totalOffset.toFixed(2)} × ${multiplier.toFixed(2)}</span><span class="value">${effective.toFixed(3)}/s</span></div>`;
  return html;
}

function renderResearchSpeed(effects, citizens, citizenEffect, completedBuildings, completedResearch, items, baseResearchSpeed) {
  baseResearchSpeed   = baseResearchSpeed ?? 1.0;
  const scientistCount = citizens?.scientist || 0;
  const scientistBonus = scientistCount * citizenEffect;
  const researchOffset   = effects?.research_speed_offset   || 0;
  const researchModifier = effects?.research_speed_modifier || 0;
  const totalOffset   = baseResearchSpeed + researchOffset;
  const multiplier    = 1 + researchModifier + scientistBonus;
  const effective     = totalOffset * multiplier;

  let html = '';
  html += `<div class="panel-row"><span class="label">+${baseResearchSpeed.toFixed(2)}</span><span class="value">(base)</span></div>`;
  if (completedBuildings && items?.buildings) {
    for (const iid of completedBuildings) {
      const item = items.buildings[iid];
      if (item?.effects?.research_speed_offset > 0)
        html += `<div class="panel-row"><span class="label">+${item.effects.research_speed_offset.toFixed(2)}</span><span class="value">(${item.name || iid})</span></div>`;
    }
  }
  if (completedResearch && items?.knowledge) {
    for (const iid of completedResearch) {
      const item = items.knowledge[iid];
      if (item?.effects?.research_speed_offset > 0)
        html += `<div class="panel-row"><span class="label">+${item.effects.research_speed_offset.toFixed(2)}</span><span class="value">(${item.name || iid})</span></div>`;
    }
  }
  html += '<div class="panel-row" style="border-top:1px solid #555;margin:6px 0;padding-top:6px"></div>';
  html += `<div class="panel-row"><span class="label">+${(scientistBonus * 100).toFixed(0)}%</span><span class="value">(${scientistCount} 🔭 × ${citizenEffect})</span></div>`;
  if (completedBuildings && items?.buildings) {
    for (const iid of completedBuildings) {
      const item = items.buildings[iid];
      if (item?.effects?.research_speed_modifier > 0)
        html += `<div class="panel-row"><span class="label">+${(item.effects.research_speed_modifier * 100).toFixed(0)}%</span><span class="value">(${item.name || iid})</span></div>`;
    }
  }
  if (completedResearch && items?.knowledge) {
    for (const iid of completedResearch) {
      const item = items.knowledge[iid];
      if (item?.effects?.research_speed_modifier > 0)
        html += `<div class="panel-row"><span class="label">+${(item.effects.research_speed_modifier * 100).toFixed(0)}%</span><span class="value">(${item.name || iid})</span></div>`;
    }
  }
  html += '<div class="panel-row" style="border-top:1px solid #555;margin:6px 0;padding-top:6px"></div>';
  html += `<div class="panel-row" style="color:#ffa726;font-weight:bold"><span class="label">= ${totalOffset.toFixed(2)} × ${multiplier.toFixed(2)}</span><span class="value">${effective.toFixed(3)}/s</span></div>`;
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

function _resolveEmpireUsername(uid) {
  if (_empiresData) {
    const e = _empiresData.find(x => x.uid === uid);
    if (e) return e.username || '';
  }
  return '';
}

function _fmtSecs(s) {
  if (s == null || s < 0) return '—';
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  const sec = Math.floor(s % 60);
  if (h > 0) return `${h}h ${m}m ${sec}s`;
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
  const rawName   = direction === 'in'
    ? (a.army_name || _resolveEmpireName(otherUid))
    : _resolveEmpireName(otherUid);
  const username  = direction === 'in'
    ? (a.attacker_username || _resolveEmpireUsername(otherUid))
    : _resolveEmpireUsername(otherUid);
  const empName   = username ? `${rawName} (${username})` : rawName;
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
    return `<div class="panel"><div class="panel-header">Known Empires</div><div class="panel-row"><span class="value">Loading…</span></div></div>`;
  }
  if (empires.length === 0) {
    return `<div class="panel"><div class="panel-header">Known Empires</div><div class="panel-row"><span class="value">—</span></div></div>`;
  }

  const rows = empires.map((e, i) => `
    <div class="panel-row" style="display:grid;grid-template-columns:24px 1fr 90px 56px 46px;gap:6px;align-items:center;">
      <span style="color:#888;font-size:0.85em;">${i + 1}</span>
      <span class="label" style="font-weight:${e.is_self ? 'bold' : 'normal'};color:${e.is_self ? 'var(--accent, #4fc3f7)' : 'inherit'};">${e.name}${e.username ? ` <span style="color:#888;font-weight:normal;font-size:0.85em;">(${e.username})</span>` : ''}${e.is_self ? ' ★' : ''}</span>
      <span class="value" style="color:#ffa726;">${fmtNumber(e.culture)} ✦</span>
      ${e.is_self
        ? '<span></span><span></span>'
        : `<button class="attack-btn" data-uid="${e.uid}" data-name="${e.name}" style="font-size:11px;padding:2px 6px;background:var(--danger,#e53935);border-color:var(--danger,#e53935);display:inline-flex;align-items:center;justify-content:center;">⚔</button>
           <button class="msg-btn" data-uid="${e.uid}" data-name="${e.name}" style="font-size:11px;padding:2px 6px;display:inline-flex;align-items:center;justify-content:center;">✉</button>`
      }
    </div>
  `).join('');

  return `
    <div class="panel">
      <div class="panel-header">Known Empires</div>
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
  id: 'status',
  title: 'Status',
  init,
  enter,
  leave,
};
