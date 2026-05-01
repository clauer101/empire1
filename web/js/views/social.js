/**
 * Social view — battle reports.
 */

import { rest } from '../rest.js';
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

// ── Init ────────────────────────────────────────────────────────────

function init(el, _api, _state) {
  container = el;
  st = _state;
  _renderShell();
}

function _renderShell() {
  container.style.cssText = 'display:flex;flex-direction:column;height:100%;overflow-x:hidden;';
  container.innerHTML = `
    <h2 class="battle-title">⚔ Battle Reports<span class="title-resources"><span class="title-gold"></span><span class="title-culture"></span><span class="title-life"></span></span></h2>

    <a href="https://discord.gg/U4SEZB5BT" target="_blank" rel="noopener" style="
      display:flex;align-items:center;gap:8px;
      background:#5865F2;color:#fff;
      border-radius:6px;padding:8px 14px;
      font-size:13px;font-weight:600;text-decoration:none;
      margin-bottom:10px;flex-shrink:0;
      box-sizing:border-box;width:100%;overflow:hidden;
    ">
      <svg width="20" height="20" viewBox="0 0 71 55" fill="white" xmlns="http://www.w3.org/2000/svg"><path d="M60.1 4.9A58.5 58.5 0 0 0 45.5.4a.2.2 0 0 0-.2.1 40.8 40.8 0 0 0-1.8 3.7 54 54 0 0 0-16.2 0A37.7 37.7 0 0 0 25.5.5a.2.2 0 0 0-.2-.1 58.4 58.4 0 0 0-14.6 4.5.2.2 0 0 0-.1.1C1.6 18.1-.9 30.9.3 43.5c0 .1.1.1.1.2a58.8 58.8 0 0 0 17.7 8.9.2.2 0 0 0 .2-.1 42 42 0 0 0 3.6-5.9.2.2 0 0 0-.1-.3 38.7 38.7 0 0 1-5.5-2.6.2.2 0 0 1 0-.4l1.1-.8a.2.2 0 0 1 .2 0c11.6 5.3 24.1 5.3 35.5 0a.2.2 0 0 1 .2 0l1.1.8a.2.2 0 0 1 0 .4 36.1 36.1 0 0 1-5.5 2.6.2.2 0 0 0-.1.3 47.1 47.1 0 0 0 3.6 5.9.2.2 0 0 0 .2.1 58.6 58.6 0 0 0 17.8-8.9.2.2 0 0 0 .1-.2c1.5-15-2.5-27.7-10.6-39.1a.2.2 0 0 0-.1-.1zM23.7 35.8c-3.5 0-6.4-3.2-6.4-7.2s2.8-7.2 6.4-7.2c3.6 0 6.5 3.3 6.4 7.2 0 4-2.8 7.2-6.4 7.2zm23.7 0c-3.5 0-6.4-3.2-6.4-7.2s2.8-7.2 6.4-7.2c3.6 0 6.5 3.3 6.4 7.2 0 4-2.8 7.2-6.4 7.2z"/></svg>
      Join our Discord
    </a>

    <div id="message-list" style="
      flex:1;
      overflow-y:auto;
      display:flex;
      flex-direction:column;
      gap:4px;
      min-height:0;
      padding:8px 4px;
    ">
      <div class="empty-state"><div class="empty-icon">⚔</div><p>Loading…</p></div>
    </div>
  `;
}

// ── Lifecycle ────────────────────────────────────────────────────────

async function enter() {
  await _refresh();
  _pollInterval = setInterval(_refresh, 8000);
}

function leave() {
  if (_pollInterval) { clearInterval(_pollInterval); _pollInterval = null; }
}

// ── Data ─────────────────────────────────────────────────────────────

async function _refresh() {
  try {
    _data = await rest.getMessages();
    _render(_data);
  } catch (err) {
    const el = container.querySelector('#message-list');
    if (el) el.innerHTML = `<div class="error-msg" style="padding:12px">Error: ${_esc(err.message)}</div>`;
  }
}

// ── Render ────────────────────────────────────────────────────────────

function _render(data) {
  const el = container.querySelector('#message-list');
  if (!el) return;

  if (!data) {
    el.innerHTML = '<div class="empty-state"><div class="empty-icon">⚔</div><p>No battle reports</p></div>';
    return;
  }

  const myUid = st.auth?.uid;
  _renderBattleReports(el, data.battle_reports || [], myUid);
  // Mark battle reports read
  (data.battle_reports || []).filter(m => !m.read).forEach(m => {
    rest.markMessageRead(m.id).catch(() => {});
    m.read = true;
  });
  if (data.unread_battle !== undefined) data.unread_battle = 0;
}

function _parseBattleReportSummary(body) {
  const lines = body.split('\n');
  const result = lines[0] || '';
  const opponentLine = lines.find((l, i) => i > 0 && /^[⚔🛡]/.test(l.trimStart()) && !l.includes('──'));
  const opponent = opponentLine ? opponentLine.replace(/^[⚔🛡]\s*\w+:\s*/u, '').trim() : '';
  return { result, opponent };
}

function _renderBattleReports(el, messages, myUid) {
  const cutoff = Date.now() - 3 * 24 * 60 * 60 * 1000;
  messages = messages.filter(m => new Date(m.sent_at).getTime() >= cutoff);
  if (!messages.length) {
    el.innerHTML = '<div class="empty-state"><div class="empty-icon">⚔</div><p>No battle reports in the last 3 days.</p></div>';
    return;
  }
  el.innerHTML = messages.map((m, idx) => {
    const unreadDot = !m.read
      ? '<span style="display:inline-block;width:7px;height:7px;border-radius:50%;background:var(--warning,#ffa726);margin-right:5px;flex-shrink:0;"></span>'
      : '';
    const { result, opponent } = _parseBattleReportSummary(m.body || '');
    const detailId = 'br-detail-' + idx;
    const won = /Won/i.test(result);
    const resultColor = won ? 'var(--success,#66bb6a)' : 'var(--danger,#ef5350)';
    return `
      <div class="panel" style="margin-bottom:6px;padding:0;${!m.read ? 'border-left:3px solid var(--warning,#ffa726);' : ''}">
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
  }).join('');

  // Restore open state
  el.querySelectorAll('.br-header').forEach(btn => {
    const msgId = btn.dataset.msgId;
    const detail = el.querySelector('#' + btn.dataset.target);
    if (detail && msgId && _openBattleReportIds.has(msgId)) {
      detail.style.display = '';
      btn.querySelector('.br-chevron').textContent = '▲';
    }
  });

  // Bind toggle
  el.querySelectorAll('.br-header').forEach(btn => {
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
  const tz  = 'Europe/Berlin';
  const now = new Date();
  const dateStr = d.toLocaleDateString('de-DE', { timeZone: tz });
  const nowStr  = now.toLocaleDateString('de-DE', { timeZone: tz });
  const yest    = new Date(now); yest.setDate(now.getDate() - 1);
  const time    = d.toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit', timeZone: tz });
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
