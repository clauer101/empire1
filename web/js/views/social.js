/**
 * Social view — battle reports.
 */

import { rest } from '../rest.js';
import { pageTitle } from '../lib/page_title.js';
import { escHtml, escAttr, hilite } from '../lib/html.js';

/** @type {import('../state.js').StateStore} */
let st;
/** @type {HTMLElement} */
let container;

/** cached API response */
let _data = null;
/** poll interval handle */
let _pollInterval = null;
/** expanded battle report message IDs */
let _openBattleReportIds = new Set();
/** active filter: 'player' | 'ai' | 'both' */
let _filterOpponent = 'both';
/** active filter: 'victory' | 'defeat' | 'both' */
let _filterOutcome = 'both';

// ── Init ────────────────────────────────────────────────────────────

function init(el, _api, _state) {
  container = el;
  st = _state;
  _renderShell();
}

const _T3 = {
  opponent: { vals: ['both', 'player', 'ai'],     labels: ['Any opponent', 'vs. Player', 'vs. AI'] },
  outcome:  { vals: ['both', 'victory', 'defeat'], labels: ['Any outcome',  'Victory', 'Defeat'] },
};

function _toggle3Html(group) {
  return `
    <div style="display:flex;align-items:center;gap:8px;">
      <div class="br-t3" data-group="${group}" data-pos="0" style="
        position:relative;width:66px;height:22px;border-radius:11px;flex-shrink:0;
        background:transparent;border:1px solid rgba(255,255,255,0.2);
        cursor:pointer;
        -webkit-tap-highlight-color:transparent;user-select:none;">
        <div class="br-t3-knob" style="position:absolute;top:0;left:0;
          width:22px;height:22px;border-radius:11px;
          background:var(--accent,#4fc3f7);
          transition:left .15s ease;pointer-events:none;"></div>
      </div>
      <span class="br-t3-val" style="font-size:12px;color:var(--text-dim);">${_T3[group].labels[0]}</span>
    </div>`;
}

function _setToggle3(track, pos) {
  const group = track.dataset.group;
  track.dataset.pos = String(pos);
  track.querySelector('.br-t3-knob').style.left = `${pos * 22}px`;
  track.parentElement.querySelector('.br-t3-val').textContent = _T3[group].labels[pos];
  if (group === 'opponent') _filterOpponent = _T3[group].vals[pos];
  else _filterOutcome = _T3[group].vals[pos];
  _applyFilters();
}

function _applyFilters() {
  const el = container.querySelector('#br-reports');
  if (!el) return;
  let visible = 0;
  el.querySelectorAll('.br-panel').forEach((panel) => {
    const ai = panel.dataset.ai === '1';
    const won = panel.dataset.won === '1';
    const showOpponent = _filterOpponent === 'both' || (_filterOpponent === 'ai' ? ai : !ai);
    const showOutcome  = _filterOutcome  === 'both' || (_filterOutcome  === 'victory' ? won : !won);
    const show = showOpponent && showOutcome;
    panel.style.display = show ? '' : 'none';
    if (show) visible++;
  });
  const empty = el.querySelector('#br-empty');
  if (empty) empty.style.display = visible ? 'none' : '';
}

function _renderShell() {
  container.style.cssText = 'display:flex;flex-direction:column;height:100%;overflow-x:hidden;';
  container.innerHTML = `
    <div id="br-filters" style="
      flex-shrink:0;
      display:flex;flex-direction:column;gap:6px;
      padding:8px 4px 4px;
      -webkit-tap-highlight-color:transparent;
    ">
      ${_toggle3Html('opponent')}
      ${_toggle3Html('outcome')}
    </div>
    <div id="message-list" style="
      flex:1;
      overflow-y:auto;
      min-height:0;
      padding:0 4px 8px;
    ">
      <div id="br-reports">
        <div class="empty-state"><div class="empty-icon">⚔</div><p>Loading…</p></div>
      </div>
    </div>
  `;

  container.querySelectorAll('.br-t3').forEach((track) => {
    track.addEventListener('click', () => {
      const pos = ((+track.dataset.pos) + 1) % 3;
      _setToggle3(track, pos);
    });
  });
}

// ── Lifecycle ────────────────────────────────────────────────────────

async function enter() {
  pageTitle.set('⚔ Battle Reports');
  await _refresh();
  _pollInterval = setInterval(_refresh, 8000);
}

function leave() {
  if (_pollInterval) {
    clearInterval(_pollInterval);
    _pollInterval = null;
  }
}

// ── Data ─────────────────────────────────────────────────────────────

async function _refresh() {
  try {
    _data = await rest.getMessages();
    _render(_data);
  } catch (err) {
    const el = container.querySelector('#br-reports');
    if (el)
      el.innerHTML = `<div class="error-msg" style="padding:12px">Error: ${_esc(err.message)}</div>`;
  }
}

// ── Render ────────────────────────────────────────────────────────────

function _render(data) {
  const el = container.querySelector('#br-reports');
  if (!el) return;

  if (!data) {
    el.innerHTML =
      '<div class="empty-state"><div class="empty-icon">⚔</div><p>No battle reports</p></div>';
    return;
  }

  const myUid = st.auth?.uid;
  _renderBattleReports(el, data.battle_reports || [], myUid);
  // Mark battle reports read
  (data.battle_reports || [])
    .filter((m) => !m.read)
    .forEach((m) => {
      rest.markMessageRead(m.id).catch(() => {});
      m.read = true;
    });
  if (data.unread_battle !== undefined) data.unread_battle = 0;
}

function _parseBattleReportSummary(body) {
  const lines = body.split('\n');
  const result = lines[0] || '';
  const opponentLine = lines.find(
    (l, i) => i > 0 && /^[⚔🛡]/u.test(l.trimStart()) && !l.includes('──')
  );
  const opponent = opponentLine ? opponentLine.replace(/^[⚔🛡]\s*\w+:\s*/u, '').trim() : '';
  return { result, opponent };
}

function _isAiBattle(body) {
  return /Attacker\(s\):\s*AI\b/m.test(body || '');
}

function _renderBattleReports(el, messages, myUid) {
  const cutoff = Date.now() - 3 * 24 * 60 * 60 * 1000;
  messages = messages.filter((m) => new Date(m.sent_at).getTime() >= cutoff);

  el.innerHTML =
    '<div id="br-empty" class="empty-state" style="display:none"><div class="empty-icon">⚔</div><p>No matching battle reports.</p></div>' +
    (messages.length === 0
      ? '<div class="empty-state"><div class="empty-icon">⚔</div><p>No battle reports in the last 3 days.</p></div>'
      : messages
        .map((m, idx) => {
          const unreadDot = !m.read
            ? '<span style="display:inline-block;width:7px;height:7px;border-radius:50%;background:var(--warning,#ffa726);margin-right:5px;flex-shrink:0;"></span>'
            : '';
          const { result, opponent } = _parseBattleReportSummary(m.body || '');
          const detailId = 'br-detail-' + idx;
          const won = /Won/i.test(result) || /^🕵/u.test(result);
          const isAi = _isAiBattle(m.body);
          const resultColor = won ? 'var(--success,#66bb6a)' : 'var(--danger,#ef5350)';
          return `
      <div class="panel br-panel" data-ai="${isAi ? 1 : 0}" data-won="${won ? 1 : 0}"
           style="margin-bottom:6px;padding:0;${!m.read ? 'border-left:3px solid var(--warning,#ffa726);' : ''}">
        <button class="br-header" data-target="${detailId}" data-msg-id="${m.id}"
          style="width:100%;display:flex;align-items:center;justify-content:space-between;gap:8px;
                 padding:10px 14px;background:none;border:none;cursor:pointer;text-align:left;">
          <span style="display:flex;align-items:center;gap:6px;min-width:0;">
            ${unreadDot}
            <span style="font-weight:600;color:${resultColor};word-break:break-word;">${_esc(result)}</span>
            ${opponent ? '<span style="color:var(--text-dim);font-size:12px;word-break:break-word;">vs ' + _esc(opponent) + '</span>' : ''}
          </span>
          <span style="display:flex;align-items:center;gap:8px;flex-shrink:0;">
            <span style="font-size:11px;color:var(--text-dim);">${_fmtTime(m.sent_at)}</span>
            <span class="br-chevron" style="font-size:11px;color:var(--text-dim);">▼</span>
          </span>
        </button>
        <div id="${detailId}" style="display:none;padding:0 14px 12px;">
          <div style="font-family:monospace;font-size:12px;line-height:1.6;white-space:pre-wrap;word-break:break-word;">${_linkify(_esc(m.body))}</div>
        </div>
      </div>`;
        })
        .join(''));

  // Restore open state
  el.querySelectorAll('.br-header').forEach((btn) => {
    const msgId = btn.dataset.msgId;
    const detail = el.querySelector('#' + btn.dataset.target);
    if (detail && msgId && _openBattleReportIds.has(msgId)) {
      detail.style.display = '';
      btn.querySelector('.br-chevron').textContent = '▲';
    }
  });

  // Bind toggle
  el.querySelectorAll('.br-header').forEach((btn) => {
    btn.addEventListener('click', () => {
      const detail = el.querySelector('#' + btn.dataset.target);
      if (!detail) return;
      const open = detail.style.display !== 'none';
      detail.style.display = open ? 'none' : '';
      btn.querySelector('.br-chevron').textContent = open ? '▼' : '▲';
      const msgId = btn.dataset.msgId;
      if (msgId) {
        if (open) _openBattleReportIds.delete(msgId);
        else _openBattleReportIds.add(msgId);
      }
    });
  });

  _applyFilters();
}

// ── Helpers ───────────────────────────────────────────────────────────

const _esc = escHtml;

function _linkify(html) {
  return html.replace(/#replay\/([\w]+)/g, (_, key) => {
    const parts = key.match(/^(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})_(\d+)$/);
    const label = parts
      ? `${parts[1]}-${parts[2]}-${parts[3]} ${parts[4]}:${parts[5]}:${parts[6]} #${parts[7]}`
      : `#${key}`;
    return `<a href="#replay/${key}" style="color:var(--accent,#4fc3f7);">▶ Replay ${label}</a>`;
  });
}

function _fmtTime(sent_at) {
  if (!sent_at) return '';
  const d = new Date(sent_at);
  if (isNaN(d)) return sent_at.replace('T', ' ');
  const tz = 'Europe/Berlin';
  const now = new Date();
  const dateStr = d.toLocaleDateString('de-DE', { timeZone: tz });
  const nowStr = now.toLocaleDateString('de-DE', { timeZone: tz });
  const yest = new Date(now);
  yest.setDate(now.getDate() - 1);
  const time = d.toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit', timeZone: tz });
  if (dateStr === nowStr) return time;
  if (dateStr === yest.toLocaleDateString('de-DE', { timeZone: tz })) return `Yesterday ${time}`;
  return dateStr + ' ' + time;
}

export default {
  id: 'social',
  title: 'Social',
  init,
  enter,
  leave,
};
