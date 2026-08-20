/**
 * Empire Details — standalone sub-page for a single empire.
 * Shows name/points always, plus the contents of the last spy report if one
 * has been captured. Reached from a row's 🏰 button in status.js /
 * globalempires.js (never linked in the main nav).
 */

import { rest } from '../rest.js';
import { pageTitle } from '../lib/page_title.js';
import { state } from '../state.js';
import { showIconLegend, fmtAllianceStatus, fmtSecs, fmtEffectRow } from '../lib/format.js';
import { buildSpyReportBodyHtml } from '../lib/spy_report_overlay.js';

/** @type {HTMLElement} */
let container;
let _uid = null;
let _empire = null;
let _allEmpires = [];

function _diplomacyEnabled() {
  return true;
}

function init(el) {
  container = el;
  container.style.cssText = 'display:flex;flex-direction:column;height:100%;overflow-y:auto;';
  container.addEventListener('click', (e) => {
    if (e.target.closest('.icon-legend-trigger')) showIconLegend();
    if (e.target.closest('.empire-spy-btn')) _onSpyClick(e.target.closest('.empire-spy-btn'));
    if (e.target.closest('.empire-diplomacy-btn')) _onDiplomacyClick(e.target.closest('.empire-diplomacy-btn'));
    if (e.target.closest('.tt-back')) window.history.back();
  });
}

async function enter() {
  pageTitle.set('🏰 Empire Details');
  document.getElementById('app')?.classList.add('full-bleed');

  const hash = window.location.hash.replace('#', '');
  const slashIdx = hash.indexOf('/');
  _uid = slashIdx > 0 ? parseInt(hash.substring(slashIdx + 1), 10) : null;

  if (!_uid) {
    _renderError('No empire specified.');
    return;
  }

  _render(null);

  let empire;
  try {
    const resp = await rest.getEmpires();
    _allEmpires = resp.empires || [];
    empire = _allEmpires.find((e) => e.uid === _uid) || null;
  } catch (e) {
    _renderError(e.message);
    return;
  }

  if (!empire) {
    _renderError('Empire not found.');
    return;
  }

  try {
    const spyResp = await rest.getSpyReports();
    state.setSpyReports(spyResp.reports || []);
  } catch (e) {
    console.warn('Failed to load spy reports:', e);
  }

  try {
    await rest.getMilitary();
  } catch (e) {
    console.warn('Failed to load military data:', e);
  }

  _render(empire);
}

function leave() {
  document.getElementById('app')?.classList.remove('full-bleed');
  _uid = null;
  _empire = null;
  _allEmpires = [];
}

// ── Helpers ──────────────────────────────────────────────────────────────────

function _toRoman(n) {
  const vals = [1000, 900, 500, 400, 100, 90, 50, 40, 10, 9, 5, 4, 1];
  const syms = ['M', 'CM', 'D', 'CD', 'C', 'XC', 'L', 'XL', 'X', 'IX', 'V', 'IV', 'I'];
  let out = '';
  for (let i = 0; i < vals.length; i++) { while (n >= vals[i]) { out += syms[i]; n -= vals[i]; } }
  return out;
}

function _fmtCulture(n) {
  if (n == null) return '0';
  if (n >= 1_000_000) return (n / 1_000_000).toFixed(1) + 'M';
  if (n >= 1_000) return (n / 1_000).toFixed(1) + 'K';
  return String(Math.round(n));
}

function _dot(online) {
  return `<span style="display:inline-block;width:7px;height:7px;border-radius:50%;flex-shrink:0;background:${online ? 'var(--success,#66bb6a)' : '#3a3a4a'};${online ? 'box-shadow:0 0 4px var(--success,#66bb6a)' : ''}"></span>`;
}

async function _onSpyClick(btn) {
  if (btn.disabled) return;
  const targetUid = parseInt(btn.dataset.uid, 10);
  btn.disabled = true;
  const statusEl = container.querySelector('#empire-spy-status');
  if (statusEl) statusEl.textContent = 'Dispatching spy…';
  try {
    const resp = await rest.spyAttack(targetUid);
    if (resp.success) {
      await rest.getMilitary();
      _render(_empire);
    } else {
      btn.disabled = false;
      if (statusEl) statusEl.textContent = resp.error || 'Error';
    }
  } catch (e) {
    btn.disabled = false;
    if (statusEl) statusEl.textContent = e.message;
  }
}

function _onDiplomacyClick(btn) {
  if (btn.disabled || !_empire) return;
  const targetUid = parseInt(btn.dataset.uid, 10);
  const costRatio = state.summary?.alliance_culture_cost ?? 0;
  const myCulture = state.summary?.resources?.culture ?? 0;
  const myCost = myCulture * costRatio;
  const status = _empire.alliance_status;

  // Accepting a request (pending_received → allied) would form a NEW
  // alliance. Currently only one active alliance is allowed at a time
  // (server-enforced in diplomacy.py via EmpireService.get_max_alliances —
  // a flat cap for now, but designed so a future building/knowledge/trophy
  // effect could raise it per-empire). Warn here before the accept dialog
  // instead of letting the request round-trip and fail server-side.
  const currentAllyCount = _allEmpires.filter((e) => e.alliance_status === 'allied').length;
  if (status === 'pending_received' && currentAllyCount > 0) {
    const currentAlly = _allEmpires.find((e) => e.alliance_status === 'allied');
    _showDiplomacyConfirmOverlay(
      'Already Allied',
      `<p style="margin:0 0 10px;">You are already allied with <strong>${currentAlly?.name ?? 'another empire'}</strong>. You must break that alliance before you can accept a new one from ${_empire.name}.</p>`,
      null,
    );
    return;
  }

  let title, bodyHtml;
  if (status === 'allied') {
    title = 'Break Alliance?';
    bodyHtml = `<p style="margin:0 0 10px;">Breaking this alliance will cost you <strong style="color:var(--danger,#e53935)">${_fmtCulture(myCost)} culture</strong> (${Math.round(costRatio * 100)}% of your current culture). This amount is destroyed — it is not sent to ${_empire.name}.</p>`;
  } else if (status === 'pending_received') {
    const theirCulture = _empire.resources?.culture ?? _empire.culture ?? 0;
    const theirCost = theirCulture * costRatio;
    title = 'Form Alliance?';
    bodyHtml = `<p style="margin:0 0 10px;">Accepting this alliance will immediately cost you <strong style="color:var(--danger,#e53935)">${_fmtCulture(myCost)} culture</strong> (${Math.round(costRatio * 100)}% of your current culture), and you will receive <strong style="color:var(--success,#66bb6a)">${_fmtCulture(theirCost)} culture</strong> from ${_empire.name} in return.</p>`;
  } else if (status === 'pending_sent') {
    title = 'Cancel Request?';
    bodyHtml = `<p style="margin:0 0 10px;">This withdraws your pending alliance request to ${_empire.name}. No culture is charged.</p>`;
  } else {
    title = 'Request Alliance?';
    bodyHtml = `<p style="margin:0 0 10px;">This sends an alliance request to ${_empire.name}. No culture is charged now — once ${_empire.name} accepts, you will each pay ${Math.round(costRatio * 100)}% of your own culture to the other (currently ${_fmtCulture(myCost)} for you).</p>`;
  }

  _showDiplomacyConfirmOverlay(title, bodyHtml, () => _doToggleAlliance(targetUid));
}

function _showDiplomacyConfirmOverlay(title, bodyHtml, onConfirm) {
  document.querySelector('.diplomacy-confirm-overlay')?.remove();
  const overlay = document.createElement('div');
  overlay.className = 'diplomacy-confirm-overlay prod-overlay';
  overlay.style.alignItems = 'center';
  // onConfirm === null means this is a notice-only dialog (e.g. "already
  // allied elsewhere") — show a single acknowledgment button, no action.
  const buttonsHtml = onConfirm
    ? `<button id="diplomacy-confirm-cancel" style="background:#333;color:#ccc;border:none;border-radius:4px;padding:7px 18px;cursor:pointer;">Cancel</button>
       <button id="diplomacy-confirm-ok" style="background:var(--danger,#e53935);color:#fff;border:none;border-radius:4px;padding:7px 18px;font-weight:700;cursor:pointer;">Confirm</button>`
    : `<button id="diplomacy-confirm-cancel" style="background:var(--accent,#4fc3f7);color:#111;border:none;border-radius:4px;padding:7px 18px;font-weight:700;cursor:pointer;">OK</button>`;
  overlay.innerHTML = `
    <div class="prod-overlay-box" style="max-width:380px;">
      <button class="prod-overlay-close" title="Close">✕</button>
      <div style="font-weight:bold;font-size:1.05em;margin-bottom:12px;">${title}</div>
      ${bodyHtml}
      <div style="display:flex;justify-content:flex-end;gap:10px;margin-top:14px;">
        ${buttonsHtml}
      </div>
    </div>
  `;
  const close = () => overlay.remove();
  overlay.addEventListener('click', (e) => {
    if (e.target === overlay || e.target.classList.contains('prod-overlay-close')) close();
  });
  overlay.querySelector('#diplomacy-confirm-cancel').addEventListener('click', close);
  if (!onConfirm) {
    document.body.appendChild(overlay);
    return;
  }
  overlay.querySelector('#diplomacy-confirm-ok').addEventListener('click', () => {
    close();
    onConfirm();
  });
  document.body.appendChild(overlay);
}

async function _doToggleAlliance(targetUid) {
  try {
    const toggleResp = await rest.toggleAlliance(targetUid);
    const resp = await rest.getEmpires();
    _allEmpires = resp.empires || [];
    const empire = _allEmpires.find((e) => e.uid === targetUid) || null;
    await rest.getSummary().catch(() => {});
    if (empire) _render(empire);
    if (!toggleResp.success) {
      const statusEl = container.querySelector('#empire-spy-status');
      if (statusEl) {
        statusEl.style.color = 'var(--danger, #e53935)';
        statusEl.textContent = toggleResp.error || 'Could not update alliance.';
      }
    }
  } catch (e) {
    console.warn('Diplomacy toggle failed:', e);
  }
}

// ── Render ────────────────────────────────────────────────────────────────────

function _backBtnHtml() {
  return `<button class="tt-back" style="margin-bottom:8px;">← Back</button>`;
}

function _renderError(msg) {
  container.innerHTML = `<div style="padding:16px">${_backBtnHtml()}<div class="panel-header" style="margin-bottom:12px">Empire Details</div><div class="error-msg">${msg}</div></div>`;
}

function _render(empire) {
  if (!empire) {
    container.innerHTML = `<div style="padding:16px">${_backBtnHtml()}<div class="panel-header" style="margin-bottom:12px">Empire Details</div><div class="panel-row"><span class="value">Loading…</span></div></div>`;
    return;
  }
  _empire = empire;

  const points = _fmtCulture(empire.resources?.culture ?? empire.culture ?? 0);
  const selfEra = empire.era || 1;
  const armyEnabled = (state.summary?.effects?.enable_army ?? 0) > 0;
  const canSpy = !empire.is_self && armyEnabled;

  const activeSpies = (state.military?.attacks_outgoing || []).filter((a) => a.is_spy);
  const spyDisabled = activeSpies.length > 0;
  const spyEta = spyDisabled ? fmtSecs(activeSpies[0].eta_seconds) : '';
  const travelTime = state.summary?.travel_time_seconds;
  const spyTravelLabel = travelTime ? `✈ ${fmtSecs(Math.round(travelTime / 2))}` : '';

  const spyBtn = canSpy
    ? `<button class="empire-spy-btn" data-uid="${empire.uid}" style="font-size:13px;padding:6px 14px;background:var(--danger,#e53935);border-color:var(--danger,#e53935);color:#fff;border-radius:var(--radius,4px);cursor:${spyDisabled ? 'default' : 'pointer'};display:flex;flex-direction:column;align-items:center;gap:1px;line-height:1.2;${spyDisabled ? 'opacity:0.5;' : ''}" ${spyDisabled ? 'disabled' : ''}>
        ${spyDisabled
          ? `<span>🕵 Dispatched</span><span style="font-size:0.75em;opacity:0.8;">ETA: ${spyEta}</span>`
          : `<span>🕵 Send Spy</span><span style="font-size:0.75em;opacity:0.8;">${spyTravelLabel}</span>`}
      </button>`
    : '';
  const diplomacyBtn = !empire.is_self
    ? (() => {
        const { label, badgeClass } = fmtAllianceStatus(empire.alliance_status);
        const enabled = _diplomacyEnabled();
        return `<button class="badge ${badgeClass}${enabled ? ' empire-diplomacy-btn' : ''}" data-uid="${empire.uid}" ${enabled ? '' : 'disabled'} style="font-size:13px;padding:6px 14px;border-radius:var(--radius,4px);border:none;${enabled ? 'cursor:pointer;' : 'cursor:not-allowed;opacity:0.5;'}">${label}</button>`;
      })()
    : '';
  const allianceCostPct = Math.round((state.summary?.alliance_culture_cost ?? 0) * 100);
  const allianceInfoHtml = (!empire.is_self && empire.alliance_status === 'pending_sent' && allianceCostPct > 0)
    ? `<div style="font-size:11px;color:var(--text-dim);margin-top:6px;">Once the alliance forms, ${allianceCostPct}% of each empire's culture will be transferred to the other.</div>`
    : '';

  const allyBonus = empire.alliance_status === 'allied' ? (empire.ally_ruler_bonus || {}) : {};
  const allyRulerName = empire.ally_ruler_name || '';
  const allyBonusHtml = Object.keys(allyBonus).length > 0
    ? `<div class="panel" style="padding:16px;margin-top:12px;">
        <div style="font-weight:600;font-size:0.78em;color:#888;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;">🤝 Alliance Bonus from ${allyRulerName ? `${allyRulerName} (${empire.name})` : `${empire.name}'s Ruler`}</div>
        ${Object.entries(allyBonus).map(([k, v]) => `<div class="tt-dp-row">${fmtEffectRow(k, v)}</div>`).join('')}
      </div>`
    : '';

  const report = state.spyReports?.get(empire.uid);
  const reportHtml = report
    ? `<div class="panel" style="padding:16px;margin-top:12px;">${buildSpyReportBodyHtml(report)}</div>`
    : `<div class="panel" style="padding:16px;margin-top:12px;"><span style="opacity:0.5;font-size:0.9em;">No spy report available yet.</span></div>`;

  container.innerHTML = `
    <div style="padding:12px;">
      ${_backBtnHtml()}
      <div class="panel" style="padding:16px;">
        <div style="display:flex;align-items:center;gap:8px;">
          ${_dot(empire.online)}
          <div style="font-weight:bold;font-size:1.2em;color:${empire.is_self ? 'var(--accent,#4fc3f7)' : 'inherit'};">
            ${empire.name} <span style="font-size:0.7em;color:#c9a84c;">${_toRoman(selfEra)}</span>
            ${empire.is_self ? ' ★' : ''}
          </div>
        </div>
        <div style="color:#ffa726;font-size:0.95em;margin-top:6px;">${points} ✦ points</div>
        <div style="display:flex;gap:8px;margin-top:14px;align-items:center;">
          ${spyBtn}
          ${diplomacyBtn}
        </div>
        ${allianceInfoHtml}
        <div id="empire-spy-status" style="font-size:11px;color:var(--text-dim);margin-top:6px;min-height:14px;"></div>
      </div>
      ${allyBonusHtml}
      ${reportHtml}
    </div>
  `;
}

export default {
  id: 'empire',
  title: 'Empire Details',
  init,
  enter,
  leave,
};
