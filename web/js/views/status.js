/**
 * Dashboard view — empire summary overview.
 *
 * Displays: resources, citizens, build/research queue status,
 * army count, effects, artifacts.
 */

import { eventBus } from '../events.js';
import { formatEffect, fmtNumber } from '../i18n.js';
import { fmtEffectRow, fmtEffectValue, fmtEffectLabel } from '../lib/format.js';
import { rest } from '../rest.js';
import { calcBuildSpeed, calcResearchSpeed } from '../lib/speed.js';
import { isGameFrozen } from '../lib/game_state.js';
/** @type {import('../api.js').ApiClient} */
let api;
/** @type {import('../state.js').StateStore} */
let st;
/** @type {HTMLElement} */
let container;
let _unsub = [];
/** @type {Array|null} cached empire list */
let _empiresData = null;
let _empiresTimer = null;
let _tickTimer = null;
let _tickData = null;
let _tickTs = null;
let _rafId = null;

// Live resource counter — runs independently of server polls
const _liveRes = { gold: 0, culture: 0 };
const _liveRate = { gold: 0, culture: 0 }; // per hour
let _liveTimer = null;

const _ROMAN = ['', 'I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX'];
function _toRoman(n) {
  return _ROMAN[n] || String(n);
}

function init(el, _api, _state) {
  container = el;
  api = _api;
  st = _state;

  container.innerHTML = `
    <h2 class="battle-title">🏰 Empire Status<span class="title-resources"><span class="title-gold"></span><span class="title-culture"></span><span class="title-life"></span></span></h2>
    <div id="dashboard-content">
      <div class="empty-state"><div class="empty-icon">◈</div><p>Loading empire data…</p></div>
    </div>
  `;

  const _titleEl = container.querySelector('.battle-title');
  if (_titleEl) {
    const _resourceWrap = _titleEl.querySelector('.title-resources');
    _titleEl.textContent = '';
    const _labelSpan = document.createElement('span');
    _labelSpan.textContent = '🏰 Empire Status ';
    const _efxBtn = document.createElement('button');
    _efxBtn.id = 'status-effects-btn';
    _efxBtn.className = 'prod-info-btn';
    _efxBtn.title = 'Show production details';
    _efxBtn.textContent = '🔍';
    _efxBtn.addEventListener('click', () => { if (st.summary) _showProductionOverlay(st.summary); });
    _labelSpan.appendChild(_efxBtn);
    _titleEl.appendChild(_labelSpan);
    if (_resourceWrap) _titleEl.appendChild(_resourceWrap);
  }
}

function enter() {
  // Register listeners first
  _unsub.push(eventBus.on('state:summary', render));
  _unsub.push(
    eventBus.on('state:items', () => {
      if (st.summary) render(st.summary);
    })
  );

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
    rest.getItems().catch((err) => console.error('[dashboard] getItems failed:', err));
  }

  // Load empire rankings and poll for new players every 30s
  refreshEmpires();
  _empiresTimer = setInterval(refreshEmpires, 30_000);
}

function leave() {
  _unsub.forEach((fn) => fn());
  _unsub = [];
  _empiresData = null;
  if (_empiresTimer) {
    clearInterval(_empiresTimer);
    _empiresTimer = null;
  }
  if (_tickTimer) {
    clearInterval(_tickTimer);
    _tickTimer = null;
  }
  if (_rafId) {
    cancelAnimationFrame(_rafId);
    _rafId = null;
  }
  if (render._stopRaf) {
    render._stopRaf();
    render._stopRaf = null;
  }
  if (_liveTimer) {
    clearInterval(_liveTimer);
    _liveTimer = null;
  }
  _tickData = null;
  _tickTs = null;
}

async function refresh() {
  try {
    const summary = await rest.getSummary();
    st.setSummary(summary);
  } catch (err) {
    if (err.message.includes('Unauthorized')) return; // router already redirects to login
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

    // Re-render attack lists now that empire names are known
    const summary = st.summary;
    if (summary) {
      const incEl = container.querySelector('#attacks-incoming-list');
      const outEl = container.querySelector('#attacks-outgoing-list');
      if (incEl) {
        const inc = summary.attacks_incoming || [];
        incEl.innerHTML = inc.length
          ? inc.map((a) => _attackEntry(a, 'in')).join('')
          : `<div style="color:#666;font-size:0.85em;padding:2px 0">No incoming attacks</div>`;
      }
      if (outEl) {
        const out = summary.attacks_outgoing || [];
        outEl.innerHTML = out.length
          ? out.map((a) => _attackEntry(a, 'out')).join('')
          : `<div style="color:#666;font-size:0.85em;padding:2px 0">No outgoing attacks</div>`;
      }
      _bindAttackEntryClicks(container.querySelector('#dashboard-content'));
    }
  } catch (err) {
    console.error('[dashboard] getEmpires failed:', err);
  }
}

function render(data) {
  const el = container.querySelector('#dashboard-content');
  if (!data) {
    el.innerHTML =
      '<div class="empty-state"><div class="empty-icon">◈</div><p>No empire data available</p></div>';
    return;
  }
  const r = data.resources || {};

  const price = data.citizen_price;
  el.innerHTML = `
    <div class="dashboard-2col">

      <div class="panel">
        <div class="panel-header">Resources</div>
        <div class="panel-row"><span class="label">💰 Gold</span><span class="value"><span data-live-res="gold">${fmt(r.gold)}</span> <span style="color:#888;font-size:0.85em">(+${fmtPerH(calcIncome('gold', data.effects, data.citizens, data.citizen_effect, data.base_gold))}/h)</span></span></div>
        <div class="panel-row"><span class="label">🎭 Culture</span><span class="value"><span data-live-res="culture">${fmt(r.culture)}</span> <span style="color:#888;font-size:0.85em">(+${fmtPerH(calcIncome('culture', data.effects, data.citizens, data.citizen_effect, data.base_culture))}/h)</span></span></div>
        <div class="panel-row"><span class="label">❤️ Life</span><span class="value">${Math.floor(r.life ?? data.life ?? 0)} / ${Math.floor(data.max_life ?? 0)} <span style="color:#888;font-size:0.85em">(+${fmtPerH(calcIncome('life', data.effects, data.citizens, data.citizen_effect, 0))}/h)</span></span></div>
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
        ${(() => {
          const arts = data.artifacts || [];
          if (!arts.length) return '';
          const catalog = st?.items?.catalog || {};
          const badges = arts
            .map((iid) => {
              const name = catalog[iid]?.name || iid;
              const type = catalog[iid]?.type || 'normal';
              return `<span class="art-badge art-badge-${type} art-badge-clickable" data-iid="${iid}">⚜ ${name}</span>`;
            })
            .join('');
          return `<div class="panel-header">Artifacts</div><div class="art-badge-list">${badges}</div><div style="border-top:1px solid var(--border-color);margin:8px 0 4px"></div>`;
        })()}
        <div class="panel-header">Incoming</div>
        <div id="attacks-incoming-list">${(() => {
          const inc = data.attacks_incoming || [];
          if (!inc.length)
            return `<div style="color:#666;font-size:0.85em;padding:2px 0">No incoming attacks</div>`;
          return inc.map((a) => _attackEntry(a, 'in')).join('');
        })()}</div>

        <div class="panel-header" style="margin-top:8px">Outgoing</div>
        <div id="attacks-outgoing-list">${(() => {
          const out = data.attacks_outgoing || [];
          if (!out.length)
            return `<div style="color:#666;font-size:0.85em;padding:2px 0">No outgoing attacks</div>`;
          return out.map((a) => _attackEntry(a, 'out')).join('');
        })()}</div>

        <div style="border-top:1px solid var(--border-color);margin:8px 0 4px"></div>
        <div class="panel-header">Research</div>
        ${(() => {
          const iid = data.research_queue;
          if (!iid) return `<div style="color:#666;font-size:0.85em;padding:2px 0">idle</div>`;
          const remaining = data.knowledge?.[iid] ?? 0;
          const effort = st?.items?.knowledge?.[iid]?.effort || 0;
          const itemName = st?.items?.knowledge?.[iid]?.name || iid;
          const researchMultiplier = calcResearchSpeed(data);
          const wallSecs = researchMultiplier > 0 ? remaining / researchMultiplier : remaining;
          const wallTotal = researchMultiplier > 0 ? effort / researchMultiplier : effort;
          const pct = effort > 0 ? Math.max(0, Math.min(100, (1 - remaining / effort) * 100)) : 0;
          return `
            <div class="panel-row"><span class="label">🔬 ${itemName}</span><span class="value" style="font-size:0.85em" data-queue-cd="research" data-remain="${wallSecs.toFixed(2)}" data-pct-start="${pct.toFixed(2)}" data-wall-total="${wallTotal.toFixed(2)}">${_fmtSecs(wallSecs)}</span></div>
            <div style="background:var(--border-color,#333);border-radius:3px;height:6px;margin:2px 0 4px">
              <div data-queue-bar="research" style="background:#ffa726;width:${pct.toFixed(1)}%;height:100%;border-radius:3px;transition:width .5s"></div>
            </div>`;
        })()}

        <div class="panel-header" style="margin-top:6px">Building</div>
        ${(() => {
          const iid = data.build_queue;
          if (!iid) return `<div style="color:#666;font-size:0.85em;padding:2px 0">idle</div>`;
          const remaining = data.buildings?.[iid] ?? 0;
          const effort = st?.items?.buildings?.[iid]?.effort || 0;
          const itemName = st?.items?.buildings?.[iid]?.name || iid;
          const buildMultiplier = calcBuildSpeed(data);
          const wallSecs = buildMultiplier > 0 ? remaining / buildMultiplier : remaining;
          const wallTotal = buildMultiplier > 0 ? effort / buildMultiplier : effort;
          const pct = effort > 0 ? Math.max(0, Math.min(100, (1 - remaining / effort) * 100)) : 0;
          return `
            <div class="panel-row"><span class="label">🔨 ${itemName}</span><span class="value" style="font-size:0.85em" data-queue-cd="build" data-remain="${wallSecs.toFixed(2)}" data-pct-start="${pct.toFixed(2)}" data-wall-total="${wallTotal.toFixed(2)}">${_fmtSecs(wallSecs)}</span></div>
            <div style="background:var(--border-color,#333);border-radius:3px;height:6px;margin:2px 0 4px">
              <div data-queue-bar="build" style="background:#4fc3f7;width:${pct.toFixed(1)}%;height:100%;border-radius:3px;transition:width .5s"></div>
            </div>`;
        })()}
      </div>

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
          await new Promise((r) => setTimeout(r, 2000));
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

  // Bind artifact badge clicks
  el.querySelectorAll('.art-badge-clickable').forEach((badge) => {
    badge.addEventListener('click', () => _showArtifactOverlay(badge.dataset.iid));
  });

  // Replace old citizen-btn handler with slider init
  _initCitizenSlider(el, data);

  // citizenPrice entfernt, Preis kommt vom Backend

  // Bind empire list events (attack buttons, refresh)
  bindEmpiresEvents();

  // Snapshot for client-side countdown ticking
  _tickData = data;
  _tickTs = Date.now();
  if (!_tickTimer) _tickTimer = setInterval(_tick, 1000);

  // Update live counter base/rate from fresh server data and (re)start counter
  const r2 = data.resources || {};
  _liveRes.gold = r2.gold ?? 0;
  _liveRes.culture = r2.culture ?? 0;
  _liveRate.gold = calcIncome(
    'gold',
    data.effects,
    data.citizens,
    data.citizen_effect,
    data.base_gold
  );
  _liveRate.culture = calcIncome(
    'culture',
    data.effects,
    data.citizens,
    data.citizen_effect,
    data.base_culture
  );
  _startLiveCounter();

  _bindAttackEntryClicks(el);
}

function _bindAttackEntryClicks(el) {
  if (!el) return;
  el.querySelectorAll('.attack-in-clickable').forEach((entry) => {
    entry.addEventListener('click', () => {
      const attackId = parseInt(entry.dataset.attackId, 10);
      const attackerUid = parseInt(entry.dataset.attackerUid, 10);
      st.pendingIncomingAttack = { attack_id: attackId, attacker_uid: attackerUid };
      window.location.hash = '#defense';
    });
  });

  el.querySelectorAll('.atk-watch-entry').forEach((entry) => {
    entry.addEventListener('click', () => {
      const attackId = parseInt(entry.dataset.attackId, 10);
      const defenderUid = parseInt(entry.dataset.defenderUid, 10);
      st.pendingSpectateAttack = { attack_id: attackId, defender_uid: defenderUid };
      window.location.hash = '#defense';
    });
  });
}

function _tick() {
  if (!_tickData || !_tickTs) return;
  if (isGameFrozen()) return;
  const el = container.querySelector('#dashboard-content');
  if (!el) return;
  const elapsedS = (Date.now() - _tickTs) / 1000;

  el.querySelectorAll('[data-atk-cd]').forEach((span) => {
    const remain = Math.max(0, parseFloat(span.dataset.remain) - elapsedS);
    span.textContent = _fmtSecs(remain);
    const total = parseFloat(span.dataset.total);
    if (total > 0) {
      const pct = Math.max(0, Math.min(100, (1 - remain / total) * 100));
      const bar = span.closest('.attack-entry')?.querySelector('[data-atk-bar]');
      if (bar) bar.style.width = pct.toFixed(1) + '%';
    }
  });

  el.querySelectorAll('[data-atk-battle-elapsed]').forEach((span) => {
    const elapsed = parseFloat(span.dataset.atkBattleElapsed) + elapsedS;
    span.textContent = '⚔ ' + _fmtSecs(elapsed);
  });

  el.querySelectorAll('[data-queue-cd]').forEach((span) => {
    const remain = Math.max(0, parseFloat(span.dataset.remain) - elapsedS);
    span.textContent = _fmtSecs(remain);
    const wallTotal = parseFloat(span.dataset.wallTotal);
    if (wallTotal > 0) {
      const pct = Math.min(100, parseFloat(span.dataset.pctStart) + (elapsedS / wallTotal) * 100);
      const bar = el.querySelector(`[data-queue-bar="${span.dataset.queueCd}"]`);
      if (bar) bar.style.width = pct.toFixed(1) + '%';
    }
  });
}

function _startLiveCounter() {
  if (_liveTimer) return; // already running
  _liveTimer = setInterval(() => {
    if (isGameFrozen()) return; // resources frozen, display stays at snapshot
    _liveRes.gold += _liveRate.gold / 10;
    _liveRes.culture += _liveRate.culture / 10;
    const el = container.querySelector('#dashboard-content');
    if (!el) return;
    const goldSpan = el.querySelector('[data-live-res="gold"]');
    const cultSpan = el.querySelector('[data-live-res="culture"]');
    if (goldSpan) goldSpan.textContent = fmt(_liveRes.gold);
    if (cultSpan) cultSpan.textContent = fmt(_liveRes.culture);
  }, 100);
}

function _showProductionOverlay(data) {
  // Remove any existing overlay
  document.querySelector('.prod-overlay')?.remove();

  const items = st.items;
  const effects = data.effects || {};
  const citizens = data.citizens || {};
  const citizenEffect = data.citizen_effect || 0;
  const completedBuildings = data.completed_buildings || [];
  const completedResearch = data.completed_research || [];

  function section(title, html) {
    return `<div class="prod-overlay-section"><div class="prod-overlay-title">${title}</div>${html}</div>`;
  }

  const artifacts = data.artifacts || [];
  const rallyEffects = (data.end_rally?.active && data.end_rally?.effects) ? data.end_rally.effects : {};
  const rulerEffects = data.ruler_effects || {};
  const rulerName = data.ruler?.name || '';
  const goldHtml = renderResourceIncome(
    'gold',
    effects,
    citizens,
    citizenEffect,
    data.base_gold,
    completedBuildings,
    items,
    completedResearch,
    artifacts,
    rallyEffects,
    rulerEffects,
    rulerName
  );
  const cultureHtml = renderResourceIncome(
    'culture',
    effects,
    citizens,
    citizenEffect,
    data.base_culture,
    completedBuildings,
    items,
    completedResearch,
    artifacts,
    rallyEffects,
    rulerEffects,
    rulerName
  );
  const lifeHtml = renderResourceIncome(
    'life',
    effects,
    citizens,
    citizenEffect,
    0,
    completedBuildings,
    items,
    completedResearch,
    artifacts,
    rallyEffects,
    rulerEffects,
    rulerName
  );
  const buildHtml = renderBuildSpeed(
    effects,
    completedBuildings,
    completedResearch,
    items,
    data.base_build_speed,
    artifacts,
    rulerEffects,
    rulerName
  );
  const researchHtml = renderResearchSpeed(
    effects,
    citizens,
    citizenEffect,
    completedBuildings,
    completedResearch,
    items,
    data.base_research_speed,
    artifacts,
    rulerEffects,
    rulerName
  );
  const restoreHtml = renderRestoreLife(
    effects,
    completedBuildings,
    completedResearch,
    items,
    artifacts,
    data.base_restore_life ?? 1,
    rulerEffects,
    rulerName
  );

  const overlay = document.createElement('div');
  overlay.className = 'prod-overlay';
  overlay.innerHTML = `
    <div class="prod-overlay-box">
      <button class="prod-overlay-close" title="Close">✕</button>
      <div style="font-weight:bold;font-size:1.05em;margin-bottom:12px">Production Details</div>
      ${section('<span style="color:#FFD700">● Gold Income</span>', goldHtml)}
      ${section('<span style="color:#ffa726">● Culture Income</span>', cultureHtml)}
      ${section('<span style="color:#90ee90">● Life Regen</span>', lifeHtml)}
      ${section('<span style="color:#4fc3f7">● Construction Speed</span>', buildHtml)}
      ${section('<span style="color:#ffa726">● Research Speed</span>', researchHtml)}
      ${restoreHtml ? section('<span style="color:#ef9a9a">● Restore Life After Defeat</span>', restoreHtml) : ''}
      ${(() => {
        const ttm = effects.travel_time_modifier || 0;
        const rallyTtm = rallyEffects.travel_time_modifier || 0;
        const stm = effects.siege_time_modifier || 0;
        const rallyStm = rallyEffects.siege_time_modifier || 0;
        let html = '';
        if (ttm > 0) {
          html += `<div class="panel-row"><span class="label">-${(ttm * 100).toFixed(0)}%</span><span class="value">travel time</span></div>`;
          if (rallyTtm > 0)
            html += `<div class="panel-row"><span class="label" style="padding-left:12px">↳ -${(rallyTtm * 100).toFixed(0)}%</span><span class="value">(⚔ End Rally)</span></div>`;
        }
        if (stm > 0) {
          html += `<div class="panel-row"><span class="label">-${(stm * 100).toFixed(0)}%</span><span class="value">siege time</span></div>`;
          if (rallyStm > 0)
            html += `<div class="panel-row"><span class="label" style="padding-left:12px">↳ -${(rallyStm * 100).toFixed(0)}%</span><span class="value">(⚔ End Rally)</span></div>`;
        }
        return html ? section('<span style="color:#ce93d8">● Army Effects</span>', html) : '';
      })()}
    </div>
  `;

  // Close on backdrop click or ✕ button
  overlay.addEventListener('click', (e) => {
    if (e.target === overlay || e.target.classList.contains('prod-overlay-close')) {
      overlay.remove();
    }
  });

  document.body.appendChild(overlay);
}

function _showArtifactOverlay(iid) {
  document.querySelector('.art-detail-overlay')?.remove();

  const catalog = st?.items?.catalog || {};
  const a = catalog[iid] || {};
  const name = a.name || iid;
  const desc = a.description || '';
  const type = a.type || 'normal';
  const effects = a.effects || {};
  const sprite = a.sprite ? '/' + a.sprite : null;
  const typeColor = type === 'legendary' ? '#ab47bc' : '#c9a84c';

  const effectRows = Object.entries(effects)
    .map(([k, v]) => `<div class="panel-row"><span class="label" style="color:#aaa">${fmtEffectLabel(k)}:</span><span class="value">${fmtEffectValue(k, v)}</span></div>`)
    .join('');

  const bgStyle = sprite
    ? `background-image:linear-gradient(to bottom,rgba(14,14,22,0.15) 0%,rgba(14,14,22,0.7) 55%,rgba(14,14,22,0.88) 100%),url('${sprite}');background-size:cover;background-position:center top;background-repeat:no-repeat;`
    : '';

  const overlay = document.createElement('div');
  overlay.className = 'art-detail-overlay prod-overlay';
  overlay.style.alignItems = 'center';
  overlay.innerHTML = `
    <div class="prod-overlay-box" style="${bgStyle}max-width:380px">
      <button class="prod-overlay-close" title="Close">✕</button>
      <div style="color:${typeColor};font-size:1.1em;font-weight:700;margin-bottom:4px">⚜ ${name}</div>
      <div style="font-size:11px;color:#666;font-family:monospace;margin-bottom:10px">${iid}</div>
      ${desc ? `<div style="color:#ccc;font-size:0.9em;margin-bottom:12px;line-height:1.5">${desc}</div>` : ''}
      ${effectRows ? `<div style="font-weight:600;font-size:0.78em;color:#888;text-transform:uppercase;letter-spacing:1px;margin-bottom:6px">Effects</div>${effectRows}` : ''}
    </div>
  `;

  overlay.addEventListener('click', (e) => {
    if (e.target === overlay || e.target.classList.contains('prod-overlay-close')) {
      overlay.remove();
    }
  });

  document.body.appendChild(overlay);
}

function renderCitizens(citizens) {
  if (!citizens) return '<div class="panel-row"><span class="value">—</span></div>';
  const m = citizens.merchant || 0;
  const s = citizens.scientist || 0;
  const a = citizens.artist || 0;
  const total = m + s + a;
  if (total === 0)
    return '<div class="panel-row"><span class="value" style="color:#666;">No citizens yet</span></div>';
  const p1 = total > 0 ? ((m / total) * 100).toFixed(2) : 33.33;
  const p2 = total > 0 ? (((m + s) / total) * 100).toFixed(2) : 66.66;
  const hint =
    total >= 1 && total <= 5
      ? `<div class="csl-hint">Drag the handles to assign citizens to tasks</div>`
      : '';
  return `${hint}
    <div class="csl-wrap" data-merchant="${m}" data-scientist="${s}" data-artist="${a}" data-total="${total}">
      <div class="csl-track">
        <div class="csl-seg csl-merchant" style="left:0;width:${p1}%"></div>
        <div class="csl-seg csl-scientist" style="left:${p1}%;width:${(p2 - p1).toFixed(2)}%"></div>
        <div class="csl-seg csl-artist" style="left:${p2}%;width:${(100 - p2).toFixed(2)}%"></div>
        <div class="csl-handle" id="csl-h1" style="left:${p1}%;background:#ffa726">🔭</div>
        <div class="csl-handle" id="csl-h2" style="left:${p2}%;background:#81c784">🎨</div>
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

  function pct(steps) {
    return ((steps / total) * 100).toFixed(2) + '%';
  }

  function updateDOM() {
    const p1 = (steps1 / total) * 100;
    const p2 = (steps2 / total) * 100;
    h1.style.left = p1.toFixed(2) + '%';
    h2.style.left = p2.toFixed(2) + '%';
    segM.style.width = p1.toFixed(2) + '%';
    segS.style.left = p1.toFixed(2) + '%';
    segS.style.width = (p2 - p1).toFixed(2) + '%';
    segA.style.left = p2.toFixed(2) + '%';
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
      h2.style.zIndex = steps2 <= 0 ? '4' : '2';
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
      } catch (e) {
        console.error('[citizen-slider]', e);
      }
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

  h1.addEventListener('mousedown', (e) => dragHandle(h1, true, e));
  h1.addEventListener('touchstart', (e) => dragHandle(h1, true, e), { passive: false });
  h2.addEventListener('mousedown', (e) => dragHandle(h2, false, e));
  h2.addEventListener('touchstart', (e) => dragHandle(h2, false, e), { passive: false });

  // Set initial z-indices in case handles already overlap on first render
  updateDOM();
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

function renderBuildSpeed(
  effects,
  completedBuildings,
  completedResearch,
  items,
  baseBuildSpeed,
  ownedArtifacts,
  rulerEffects = {},
  rulerName = ''
) {
  baseBuildSpeed = baseBuildSpeed ?? 1.0;
  const buildOffset = effects?.build_speed_offset || 0;
  const buildModifier = effects?.build_speed_modifier || 0;
  const effective = calcBuildSpeed({ base_build_speed: baseBuildSpeed, effects });

  let html = '';
  html += `<div class="panel-row"><span class="label">+${baseBuildSpeed.toFixed(2)}</span><span class="value">(base)</span></div>`;
  let itemBuildOffset = 0;
  if (completedBuildings && items?.buildings) {
    for (const iid of completedBuildings) {
      const item = items.buildings[iid];
      if (item?.effects?.build_speed_offset > 0) {
        itemBuildOffset += item.effects.build_speed_offset;
        html += `<div class="panel-row"><span class="label">+${item.effects.build_speed_offset.toFixed(2)}</span><span class="value">(${item.name || iid})</span></div>`;
      }
    }
  }
  if (completedResearch && items?.knowledge) {
    for (const iid of completedResearch) {
      const item = items.knowledge[iid];
      if (item?.effects?.build_speed_offset > 0) {
        itemBuildOffset += item.effects.build_speed_offset;
        html += `<div class="panel-row"><span class="label">+${item.effects.build_speed_offset.toFixed(2)}</span><span class="value">(${item.name || iid})</span></div>`;
      }
    }
  }
  for (const iid of ownedArtifacts || []) {
    const art = items?.catalog?.[iid];
    if (art?.effects?.build_speed_offset > 0) {
      itemBuildOffset += art.effects.build_speed_offset;
      html += `<div class="panel-row"><span class="label">+${art.effects.build_speed_offset.toFixed(2)}</span><span class="value">⚜ ${art.name || iid}</span></div>`;
    }
  }
  const rulerBuildOffset = rulerEffects.build_speed_offset || 0;
  if (rulerBuildOffset > 0.0005 && rulerName)
    html += `<div class="panel-row"><span class="label">+${rulerBuildOffset.toFixed(2)}</span><span class="value">(👑 ${rulerName})</span></div>`;
  const eraBuildOffset = buildOffset - rulerBuildOffset - itemBuildOffset;
  if (eraBuildOffset > 0.0005)
    html += `<div class="panel-row"><span class="label">+${eraBuildOffset.toFixed(2)}</span><span class="value">(Era)</span></div>`;
  html +=
    '<div class="panel-row" style="border-top:1px solid #555;margin:6px 0;padding-top:6px"></div>';
  let itemBuildModifier = 0;
  if (completedBuildings && items?.buildings) {
    for (const iid of completedBuildings) {
      const item = items.buildings[iid];
      if (item?.effects?.build_speed_modifier > 0) {
        itemBuildModifier += item.effects.build_speed_modifier;
        html += `<div class="panel-row"><span class="label">+${(item.effects.build_speed_modifier * 100).toFixed(0)}%</span><span class="value">(${item.name || iid})</span></div>`;
      }
    }
  }
  if (completedResearch && items?.knowledge) {
    for (const iid of completedResearch) {
      const item = items.knowledge[iid];
      if (item?.effects?.build_speed_modifier > 0) {
        itemBuildModifier += item.effects.build_speed_modifier;
        html += `<div class="panel-row"><span class="label">+${(item.effects.build_speed_modifier * 100).toFixed(0)}%</span><span class="value">(${item.name || iid})</span></div>`;
      }
    }
  }
  for (const iid of ownedArtifacts || []) {
    const art = items?.catalog?.[iid];
    if (art?.effects?.build_speed_modifier > 0) {
      itemBuildModifier += art.effects.build_speed_modifier;
      html += `<div class="panel-row"><span class="label">+${(art.effects.build_speed_modifier * 100).toFixed(0)}%</span><span class="value">⚜ ${art.name || iid}</span></div>`;
    }
  }
  const rulerBuildModifier = rulerEffects.build_speed_modifier || 0;
  if (rulerBuildModifier > 0.0005 && rulerName)
    html += `<div class="panel-row"><span class="label">+${(rulerBuildModifier * 100).toFixed(0)}%</span><span class="value">(👑 ${rulerName})</span></div>`;
  const eraBuildModifier = buildModifier - rulerBuildModifier - itemBuildModifier;
  if (eraBuildModifier > 0.0005)
    html += `<div class="panel-row"><span class="label">+${(eraBuildModifier * 100).toFixed(0)}%</span><span class="value">(Era)</span></div>`;
  const totalOffset = baseBuildSpeed + buildOffset;
  const multiplier = 1 + buildModifier;
  html +=
    '<div class="panel-row" style="border-top:1px solid #555;margin:6px 0;padding-top:6px"></div>';
  html += `<div class="panel-row" style="color:#4fc3f7;font-weight:bold"><span class="label">= ${totalOffset.toFixed(2)} × ${multiplier.toFixed(2)}</span><span class="value">${effective.toFixed(3)}/s</span></div>`;
  return html;
}

function renderResearchSpeed(
  effects,
  citizens,
  citizenEffect,
  completedBuildings,
  completedResearch,
  items,
  baseResearchSpeed,
  ownedArtifacts,
  rulerEffects = {},
  rulerName = ''
) {
  baseResearchSpeed = baseResearchSpeed ?? 1.0;
  const researchOffset = effects?.research_speed_offset || 0;
  const researchModifier = effects?.research_speed_modifier || 0;
  const scientistCount = citizens?.scientist || 0;
  const scientistBonus = scientistCount * citizenEffect;
  const totalOffset = baseResearchSpeed + researchOffset;
  const multiplier = 1 + researchModifier + scientistBonus;
  const effective = calcResearchSpeed({
    base_research_speed: baseResearchSpeed,
    effects,
    citizens,
    citizen_effect: citizenEffect,
  });

  let html = '';
  html += `<div class="panel-row"><span class="label">+${baseResearchSpeed.toFixed(2)}</span><span class="value">(base)</span></div>`;
  let itemResearchOffset = 0;
  if (completedBuildings && items?.buildings) {
    for (const iid of completedBuildings) {
      const item = items.buildings[iid];
      if (item?.effects?.research_speed_offset > 0) {
        itemResearchOffset += item.effects.research_speed_offset;
        html += `<div class="panel-row"><span class="label">+${item.effects.research_speed_offset.toFixed(2)}</span><span class="value">(${item.name || iid})</span></div>`;
      }
    }
  }
  if (completedResearch && items?.knowledge) {
    for (const iid of completedResearch) {
      const item = items.knowledge[iid];
      if (item?.effects?.research_speed_offset > 0) {
        itemResearchOffset += item.effects.research_speed_offset;
        html += `<div class="panel-row"><span class="label">+${item.effects.research_speed_offset.toFixed(2)}</span><span class="value">(${item.name || iid})</span></div>`;
      }
    }
  }
  for (const iid of ownedArtifacts || []) {
    const art = items?.catalog?.[iid];
    if (art?.effects?.research_speed_offset > 0) {
      itemResearchOffset += art.effects.research_speed_offset;
      html += `<div class="panel-row"><span class="label">+${art.effects.research_speed_offset.toFixed(2)}</span><span class="value">⚜ ${art.name || iid}</span></div>`;
    }
  }
  const rulerResearchOffset = rulerEffects.research_speed_offset || 0;
  if (rulerResearchOffset > 0.0005 && rulerName)
    html += `<div class="panel-row"><span class="label">+${rulerResearchOffset.toFixed(2)}</span><span class="value">(👑 ${rulerName})</span></div>`;
  const eraResearchOffset = researchOffset - rulerResearchOffset - itemResearchOffset;
  if (eraResearchOffset > 0.0005)
    html += `<div class="panel-row"><span class="label">+${eraResearchOffset.toFixed(2)}</span><span class="value">(Era)</span></div>`;
  html +=
    '<div class="panel-row" style="border-top:1px solid #555;margin:6px 0;padding-top:6px"></div>';
  html += `<div class="panel-row"><span class="label">+${(scientistBonus * 100).toFixed(0)}%</span><span class="value">(${scientistCount} 🔭 × ${citizenEffect})</span></div>`;
  let itemResearchModifier = 0;
  if (completedBuildings && items?.buildings) {
    for (const iid of completedBuildings) {
      const item = items.buildings[iid];
      if (item?.effects?.research_speed_modifier > 0) {
        itemResearchModifier += item.effects.research_speed_modifier;
        html += `<div class="panel-row"><span class="label">+${(item.effects.research_speed_modifier * 100).toFixed(0)}%</span><span class="value">(${item.name || iid})</span></div>`;
      }
    }
  }
  if (completedResearch && items?.knowledge) {
    for (const iid of completedResearch) {
      const item = items.knowledge[iid];
      if (item?.effects?.research_speed_modifier > 0) {
        itemResearchModifier += item.effects.research_speed_modifier;
        html += `<div class="panel-row"><span class="label">+${(item.effects.research_speed_modifier * 100).toFixed(0)}%</span><span class="value">(${item.name || iid})</span></div>`;
      }
    }
  }
  for (const iid of ownedArtifacts || []) {
    const art = items?.catalog?.[iid];
    if (art?.effects?.research_speed_modifier > 0) {
      itemResearchModifier += art.effects.research_speed_modifier;
      html += `<div class="panel-row"><span class="label">+${(art.effects.research_speed_modifier * 100).toFixed(0)}%</span><span class="value">⚜ ${art.name || iid}</span></div>`;
    }
  }
  const rulerResearchModifier = rulerEffects.research_speed_modifier || 0;
  if (rulerResearchModifier > 0.0005 && rulerName)
    html += `<div class="panel-row"><span class="label">+${(rulerResearchModifier * 100).toFixed(0)}%</span><span class="value">(👑 ${rulerName})</span></div>`;
  const eraResearchModifier = researchModifier - rulerResearchModifier - itemResearchModifier;
  if (eraResearchModifier > 0.0005)
    html += `<div class="panel-row"><span class="label">+${(eraResearchModifier * 100).toFixed(0)}%</span><span class="value">(Era)</span></div>`;
  html +=
    '<div class="panel-row" style="border-top:1px solid #555;margin:6px 0;padding-top:6px"></div>';
  html += `<div class="panel-row" style="color:#ffa726;font-weight:bold"><span class="label">= ${totalOffset.toFixed(2)} × ${multiplier.toFixed(2)}</span><span class="value">${effective.toFixed(3)}/s</span></div>`;
  return html;
}

function renderRestoreLife(effects, completedBuildings, completedResearch, items, ownedArtifacts, baseRestore, rulerEffects = {}, rulerName = '') {
  const key = 'restore_life_after_loss_offset';
  let html = '';
  let bonus = 0;

  for (const iid of completedBuildings || []) {
    const item = items?.buildings?.[iid];
    if (item?.effects?.[key] > 0) {
      bonus += item.effects[key];
      html += `<div class="panel-row"><span class="label">+${Math.round(item.effects[key])}</span><span class="value">(${item.name || iid})</span></div>`;
    }
  }
  for (const iid of completedResearch || []) {
    const item = items?.knowledge?.[iid];
    if (item?.effects?.[key] > 0) {
      bonus += item.effects[key];
      html += `<div class="panel-row"><span class="label">+${Math.round(item.effects[key])}</span><span class="value">(${item.name || iid})</span></div>`;
    }
  }
  for (const iid of ownedArtifacts || []) {
    const art = items?.catalog?.[iid];
    if (art?.effects?.[key] > 0) {
      bonus += art.effects[key];
      html += `<div class="panel-row"><span class="label">+${Math.round(art.effects[key])}</span><span class="value">⚜ ${art.name || iid}</span></div>`;
    }
  }
  if (!bonus) return '';

  // Ruler contribution
  const rulerContrib = rulerEffects[key] || 0;
  if (rulerContrib > 0.05 && rulerName)
    html += `<div class="panel-row"><span class="label">+${Math.round(rulerContrib)}</span><span class="value">(👑 ${rulerName})</span></div>`;

  // Era contribution
  const eraContrib = (effects?.[key] || 0) - rulerContrib - bonus;
  if (eraContrib > 0.05)
    html += `<div class="panel-row"><span class="label">+${Math.round(eraContrib)}</span><span class="value">(Era)</span></div>`;

  const totalBonus = Math.round(effects?.[key] || bonus);
  const base = Math.round(baseRestore ?? 1);

  html +=
    '<div class="panel-row" style="border-top:1px solid #555;margin:6px 0;padding-top:6px"></div>';
  html += `<div class="panel-row" style="color:#ef9a9a;font-weight:bold"><span class="label">= ${base + totalBonus} (${base} +${totalBonus})</span></div>`;
  return html;
}

function fmtPerH(perSecond) {
  const h = perSecond * 3600;
  if (Math.abs(h) >= 1e6) return (h / 1e6).toFixed(1) + 'M';
  if (Math.abs(h) >= 1e3) return Math.round(h / 1e3) + 'k';
  if (Math.abs(h) >= 10) return Math.round(h) + '';
  return h.toFixed(1);
}

// effects[key] from the backend is already the full aggregated sum of all
// building + knowledge contributions (see empire_service.recalculate_effects).
// Do NOT iterate completedBuildings here — that would double-count.
function calcIncome(resourceType, effects, citizens, citizenEffect, baseAmount) {
  baseAmount = baseAmount ?? 0;
  if (resourceType === 'life') {
    return baseAmount + (effects?.life_regen_modifier || 0);
  }
  if (resourceType === 'gold') {
    const offset = baseAmount + (effects?.gold_offset || 0);
    const modifier =
      (citizens?.merchant || 0) * (citizenEffect || 0) + (effects?.gold_modifier || 0);
    return offset * (1 + modifier);
  }
  // culture
  const offset = baseAmount + (effects?.culture_offset || 0);
  const modifier =
    (citizens?.artist || 0) * (citizenEffect || 0) + (effects?.culture_modifier || 0);
  return offset * (1 + modifier);
}

function renderResourceIncome(
  resourceType,
  effects,
  citizens,
  citizenEffect,
  baseAmount,
  completedBuildings,
  items,
  completedResearch,
  ownedArtifacts,
  rallyEffects = {},
  rulerEffects = {},
  rulerName = ''
) {
  completedResearch = completedResearch || [];
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
    effectOffsetKey = 'life_regen_modifier';
    effectModifierKey = null;
    citizenCount = 0;
  }

  // Base amount (only show if > 0)
  baseAmount = baseAmount ?? 0;
  const toH = (v) => v * 3600;
  const fmtH = (v) => {
    const h = toH(v);
    if (Math.abs(h) >= 1e6) return (h / 1e6).toFixed(1) + 'M';
    if (Math.abs(h) >= 1e3) return Math.round(h / 1e3) + 'k';
    if (Math.abs(h) >= 10) return Math.round(h) + '';
    return h.toFixed(1);
  };

  if (baseAmount > 0) {
    html += `<div class="panel-row"><span class="label">+${fmtH(baseAmount)}</span><span class="value">(base)</span></div>`;
  }

  // Building & Research effects (offsets)
  let totalOffset = baseAmount;
  function addOffsetSources(catalog) {
    if (!catalog) return;
    for (const iid of completedBuildings.concat(completedResearch)) {
      const item = catalog.buildings?.[iid] || catalog.knowledge?.[iid];
      if (item?.effects?.[effectOffsetKey] > 0) {
        const offset = item.effects[effectOffsetKey];
        totalOffset += offset;
        html += `<div class="panel-row"><span class="label">+${fmtH(offset)}</span><span class="value">(${item.name || iid})</span></div>`;
      }
    }
    // Artifact offsets
    for (const iid of ownedArtifacts || []) {
      const art = catalog.catalog?.[iid];
      if (art?.effects?.[effectOffsetKey]) {
        const offset = art.effects[effectOffsetKey];
        totalOffset += offset;
        html += `<div class="panel-row"><span class="label">${offset > 0 ? '+' : ''}${fmtH(offset)}</span><span class="value">⚜ ${art.name || iid}</span></div>`;
      }
    }
  }
  addOffsetSources(items);

  // Helper to add artifact modifiers (called after the buildings/research modifier loop)
  function addArtifactModifiers() {
    for (const iid of ownedArtifacts || []) {
      const art = items?.catalog?.[iid];
      if (art?.effects?.[effectModifierKey] > 0) {
        const modifier = art.effects[effectModifierKey];
        totalModifier += modifier;
        html += `<div class="panel-row"><span class="label">+${(modifier * 100).toFixed()}%</span><span class="value">⚜ ${art.name || iid}</span></div>`;
      }
    }
  }

  // Rally offset contribution (shown separately before Era)
  const rallyOffset = rallyEffects[effectOffsetKey] || 0;
  if (rallyOffset > 0.0005) {
    html += `<div class="panel-row"><span class="label">+${fmtH(rallyOffset)}</span><span class="value">(⚔ End Rally)</span></div>`;
  }

  // Ruler offset contribution
  const rulerOffset = rulerEffects[effectOffsetKey] || 0;
  if (rulerOffset > 0.0005 && rulerName) {
    html += `<div class="panel-row"><span class="label">+${fmtH(rulerOffset)}</span><span class="value">(👑 ${rulerName})</span></div>`;
  }

  // Era offset contribution (difference between aggregated backend value and item sum, minus rally and ruler)
  const eraOffset = (effects[effectOffsetKey] || 0) - rallyOffset - rulerOffset - (totalOffset - baseAmount);
  if (eraOffset > 0.0005) {
    html += `<div class="panel-row"><span class="label">+${fmtH(eraOffset)}</span><span class="value">(Era)</span></div>`;
    totalOffset += eraOffset;
  }
  totalOffset += rallyOffset + rulerOffset;

  // For life, only show offset without multiplier
  if (resourceType === 'life') {
    const color = '#90ee90';
    html +=
      '<div class="panel-row" style="border-top: 1px solid #555; margin: 6px 0; padding-top: 6px;"></div>';
    html += `<div class="panel-row" style="color: ${color}; font-weight: bold;"><span class="label">= ${fmtH(totalOffset)}/h</span></div>`;
    return html;
  }

  // Separator line
  html +=
    '<div class="panel-row" style="border-top: 1px solid #555; margin: 6px 0; padding-top: 6px;"></div>';

  // Citizen bonus percentage
  const citizenBonus = citizenCount * citizenEffect;
  html += `<div class="panel-row"><span class="label">+${(citizenBonus * 100).toFixed(0)}%</span><span class="value">(${citizenCount} ${citizenType}s × ${citizenEffect})</span></div>`;

  // Effect modifiers from buildings/research
  let totalModifier = citizenBonus;
  for (const iid of completedBuildings.concat(completedResearch)) {
    const item = items?.buildings?.[iid] || items?.knowledge?.[iid];
    if (item?.effects?.[effectModifierKey] > 0) {
      const modifier = item.effects[effectModifierKey];
      totalModifier += modifier;
      html += `<div class="panel-row"><span class="label">+${(modifier * 100).toFixed()}%</span><span class="value">(${item.name || iid})</span></div>`;
    }
  }
  addArtifactModifiers();

  // Ruler modifier contribution
  const rulerModifier = effectModifierKey ? (rulerEffects[effectModifierKey] || 0) : 0;
  if (rulerModifier > 0.0005 && rulerName) {
    totalModifier += rulerModifier;
    html += `<div class="panel-row"><span class="label">+${(rulerModifier * 100).toFixed(0)}%</span><span class="value">(👑 ${rulerName})</span></div>`;
  }

  // Era modifier contribution
  const eraModifier = effectModifierKey
    ? (effects[effectModifierKey] || 0) - rulerModifier - (totalModifier - citizenBonus - rulerModifier)
    : 0;
  if (eraModifier > 0.0005) {
    totalModifier += eraModifier;
    html += `<div class="panel-row"><span class="label">+${(eraModifier * 100).toFixed(0)}%</span><span class="value">(Era)</span></div>`;
  }

  // Final calculation line
  const multiplier = 1 + totalModifier;
  const total = totalOffset * multiplier;
  const color = resourceType === 'gold' ? '#4fc3f7' : '#ffa726';

  html +=
    '<div class="panel-row" style="border-top: 1px solid #555; margin: 6px 0; padding-top: 6px;"></div>';
  html += `<div class="panel-row" style="color: ${color}; font-weight: bold;"><span class="label">= ${fmtH(totalOffset)} × ${multiplier.toFixed(2)}</span><span class="value">${fmtH(total)}/h</span></div>`;

  return html;
}

// ── Attacks status bar ───────────────────────────────────

function _resolveEmpireName(uid) {
  if (uid === 0 || uid === '0') return 'AI';
  if (_empiresData) {
    const e = _empiresData.find((x) => x.uid === uid);
    if (e) return e.name;
  }
  return `#${uid}`;
}

function _resolveEmpireUsername(uid) {
  if (_empiresData) {
    const e = _empiresData.find((x) => x.uid === uid);
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
  in_siege: { text: 'siege', cls: 'phase-siege' },
  in_battle: { text: 'battle', cls: 'phase-battle' },
};

function _attackEntry(a, direction) {
  const pInfo = PHASE_LABEL[a.phase] || { text: a.phase, cls: '' };
  const otherUid = direction === 'in' ? a.attacker_uid : a.defender_uid;
  const empireName = _resolveEmpireName(otherUid);
  const isAI = otherUid === 0 || otherUid === '0';
  const username = isAI
    ? ''
    : direction === 'in'
      ? a.attacker_username || _resolveEmpireUsername(otherUid)
      : _resolveEmpireUsername(otherUid);
  const empLabel = isAI ? 'AI' : username ? `${empireName} (${username})` : empireName;
  const armyName = a.army_name || '';
  const displayedArmyName =
    armyName && a.is_spy && direction === 'out' ? `"${armyName}"` : armyName;
  // Show army name as primary label; empire/username as secondary hint
  const empName = displayedArmyName
    ? `${displayedArmyName}<span class="atk-empire-hint"> · ${empLabel}</span>`
    : empLabel;

  const showWatch = direction === 'out' && (a.phase === 'in_siege' || a.phase === 'in_battle');

  // For outgoing attacks in siege/battle: the whole entry is clickable (spectate)
  const outClickable = showWatch;
  const outDataAttrs = outClickable
    ? `data-attack-id="${a.attack_id}" data-defender-uid="${a.defender_uid}" title="Watch battle" style="cursor:pointer"`
    : '';

  let countdown = '';
  let pct = 0;
  if (a.phase === 'travelling') {
    countdown = `<span class="atk-cd" data-atk-cd="${a.attack_id}" data-remain="${a.eta_seconds.toFixed(2)}" data-total="${a.total_eta_seconds.toFixed(2)}">${_fmtSecs(a.eta_seconds)}</span>`;
    pct = a.total_eta_seconds > 0 ? Math.round((1 - a.eta_seconds / a.total_eta_seconds) * 100) : 0;
  } else if (a.phase === 'in_siege') {
    countdown = `<span class="atk-cd" data-atk-cd="${a.attack_id}" data-remain="${a.siege_remaining_seconds.toFixed(2)}" data-total="${a.total_siege_seconds.toFixed(2)}">${_fmtSecs(a.siege_remaining_seconds)}</span>`;
    pct =
      a.total_siege_seconds > 0
        ? Math.round((1 - a.siege_remaining_seconds / a.total_siege_seconds) * 100)
        : 0;
  } else if (a.phase === 'in_battle') {
    const elapsed = a.battle_elapsed_seconds ?? 0;
    countdown = `<span class="atk-cd atk-cd-battle" data-atk-battle-elapsed="${elapsed.toFixed(2)}">⚔ ${_fmtSecs(elapsed)}</span>`;
    pct = 100;
  }
  pct = Math.max(0, Math.min(100, pct));

  // Icon: ⚠ for incoming, 👁 for watchable outgoing, → otherwise
  const icon = direction === 'in' ? '⚠' : showWatch ? '👁' : '→';

  return `
    <div class="attack-entry attack-${direction}${direction === 'in' ? ' attack-in-clickable' : ''}${outClickable ? ' atk-watch-entry' : ''}" ${direction === 'in' ? `data-attack-id="${a.attack_id}" data-attacker-uid="${a.attacker_uid}" title="Click to open battle view" style="cursor:pointer"` : outDataAttrs}>
      <div class="atk-row">
        <span class="atk-icon">${icon}</span>
        <span class="atk-name">${empName}</span>
        <span class="phase-tag ${pInfo.cls}">${pInfo.text}</span>
        ${countdown}
      </div>
      <div class="atk-progress-wrap">
        <div class="atk-progress-bar atk-progress-${a.phase.replace('_', '-')}" data-atk-bar="${a.attack_id}" style="width:${pct}%"></div>
      </div>
    </div>`;
}

function renderAttacksBar(data) {
  const incoming = data.attacks_incoming || [];
  const outgoing = data.attacks_outgoing || [];

  const inRows = incoming.length
    ? incoming.map((a) => _attackEntry(a, 'in')).join('')
    : '<div class="atk-empty">No active attacks</div>';
  const outRows = outgoing.length
    ? outgoing.map((a) => _attackEntry(a, 'out')).join('')
    : '<div class="atk-empty">No active attacks</div>';

  const inHeader = `Incoming${incoming.length ? ` <span class="atk-badge atk-badge-in">${incoming.length}</span>` : ''}`;
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
    .map(
      ([k, v]) =>
        `<div class="panel-row"><span class="label">${formatEffect(k, v)}</span><span class="value"></span></div>`
    )
    .join('');
}

function renderEmpiresSection(empires) {
  if (!empires) {
    return `<div class="panel"><div class="panel-header">Known Empires</div><div class="panel-row"><span class="value">Loading…</span></div></div>`;
  }
  if (empires.length === 0) {
    return `<div class="panel"><div class="panel-header">Known Empires</div><div class="panel-row"><span class="value">—</span></div></div>`;
  }

  const dot = (online) =>
    `<span style="display:inline-block;width:7px;height:7px;border-radius:50%;flex-shrink:0;background:${online ? 'var(--success,#66bb6a)' : '#3a3a4a'};${online ? 'box-shadow:0 0 4px var(--success,#66bb6a)' : ''}"></span>`;

  const selfEra = (empires.find((e) => e.is_self) || {}).era || 1;
  const canAttack = (targetEra) => targetEra >= selfEra - 1;

  const rows = empires
    .map(
      (e, i) => `
    <div class="panel-row" style="display:flex;flex-direction:row;align-items:stretch;padding:4px 8px;gap:8px;border-bottom:1px solid var(--border-color,#2a2a3a);">
      <div style="display:flex;align-items:center;gap:5px;flex:1;min-width:0;">
        <span style="color:#888;font-size:0.8em;min-width:16px;">${i + 1}</span>
        ${dot(e.online)}
        <div style="min-width:0;">
          <div style="font-weight:${e.is_self ? 'bold' : 'normal'};color:${e.is_self ? 'var(--accent,#4fc3f7)' : 'inherit'};overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">${e.name} <span style="font-size:0.8em;color:#c9a84c;">${_toRoman(e.era || 1)}</span>${e.username ? ` <span style="color:#888;font-weight:normal;font-size:0.82em;">(${e.username})</span>` : ''}${e.is_self ? ' ★' : ''}</div>
          <div style="color:#ffa726;font-size:0.82em;">${fmtNumber(e.resources?.culture ?? e.culture)} ✦${(e.artifact_count || 0) > 0 ? `<span class="art-info-trigger" style="margin-left:6px;color:#c9a84c;cursor:pointer;font-size:1.25em;letter-spacing:2px;vertical-align:middle;" title="What are artifacts?">${'⚜'.repeat(e.artifact_count)}</span>` : ''}</div>
        </div>
      </div>
      <div style="display:flex;flex-direction:row;align-items:center;gap:4px;">
        ${
          !e.is_self && canAttack(e.era || 1)
            ? `
          <button class="attack-btn" data-uid="${e.uid}" data-name="${e.name}" style="font-size:11px;padding:3px 8px;background:var(--danger,#e53935);border-color:var(--danger,#e53935);">⚔</button>
        `
            : ''
        }
      </div>
    </div>
  `
    )
    .join('');

  return `
    <div class="panel">
      <div class="panel-header">Known Empires</div>
      ${rows}
    </div>
  `;
}

function bindEmpiresEvents() {
  const sec = container.querySelector('#empires-section');
  if (!sec) return;

  sec.querySelectorAll('.attack-btn').forEach((btn) => {
    btn.onclick = () => onAttackClick(btn);
  });

  sec.querySelectorAll('.art-info-trigger').forEach((el) => {
    el.onclick = (e) => {
      e.stopPropagation();
      _showArtifactInfoOverlay();
    };
  });
}

function _showArtifactInfoOverlay() {
  document.querySelector('.art-info-overlay')?.remove();
  const overlay = document.createElement('div');
  overlay.className = 'art-info-overlay tt-overlay visible';
  overlay.innerHTML = `
    <div class="tt-panel">
      <button class="tt-close">&times;</button>
      <div class="tt-dp-name" style="color:#c9a84c">⚜ Artifacts</div>
      <div class="tt-dp-desc" style="margin-top:10px;font-style:normal;line-height:1.7;font-size:0.92em">
        <p style="margin-bottom:10px">Artifacts are powerful ancient objects that grant their owner extraordinary advantages — boosting gold income, culture, research speed, and more.</p>
        <p style="margin-bottom:10px">They are rare and highly coveted. When you defeat an enemy empire in battle, there is a chance to seize one of their artifacts for yourself.</p>
        <p>Even in defeat, a small chance remains: a skilled attacker may still manage to claim an artifact from the defender — so no raid is ever truly wasted.</p>
      </div>
    </div>
  `;
  overlay.addEventListener('click', (e) => {
    if (e.target === overlay || e.target.classList.contains('tt-close')) overlay.remove();
  });
  document.body.appendChild(overlay);
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
