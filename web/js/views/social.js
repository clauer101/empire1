/**
 * Social view — global chat, private messages, battle reports.
 *
 * Tabs:
 *   Chat          — public global chat; @name sends privately
 *   Private       — private messages (sent & received, excl. battle reports)
 *   Battle Reports — system messages from battle engine (read-only)
 */

import { rest } from '../rest.js';

/** @type {import('../state.js').StateStore} */
let st;
/** @type {HTMLElement} */
let container;

/** current tab: 'chat' | 'battle' */
let _tab = 'chat';
/** cached API response */
let _data = null;
/** empire list for @-autocomplete */
let _empiresCache = [];
/** poll interval handle */
let _pollInterval = null;

// ── Init ────────────────────────────────────────────────────────────

function init(el, _api, _state) {
  container = el;
  st = _state;
  _renderShell();
}

function _renderShell() {
  container.style.cssText = 'display:flex;flex-direction:column;height:100%;';
  container.innerHTML = `
    <h2 class="battle-title">💬 Chat<span class="title-resources"><span class="title-gold"></span><span class="title-culture"></span><span class="title-life"></span></span></h2>

    <div style="display:flex;gap:6px;margin-bottom:8px;align-items:center;">
      <button id="tab-chat"   class="tab-btn active-tab">Chat</button>
      <button id="tab-battle" class="tab-btn">Battle Reports</button>
    </div>

    <div id="message-list" style="
      flex:1;
      overflow-y:auto;
      display:flex;
      flex-direction:column;
      gap:4px;
      min-height:0;
      padding:8px 4px;
    ">
      <div class="empty-state"><div class="empty-icon">💬</div><p>Loading…</p></div>
    </div>

    <!-- Input (hidden on battle tab) -->
    <div id="chat-input-area" style="
      position:sticky;
      bottom:0;
      background:var(--surface,#1a1f2e);
      padding:10px 0 4px;
      margin-top:4px;
    ">
      <div style="display:flex;gap:6px;align-items:flex-end;">
        <div style="flex:1;position:relative;">
          <input id="chat-input" type="text" maxlength="500"
            placeholder="Message… (@Name for private)"
            style="width:100%;padding:8px 12px;font-size:13px;">
          <div id="ac-dropdown" class="empire-ac-dropdown" style="bottom:100%;top:auto;margin-bottom:2px;"></div>
        </div>
        <button id="send-btn" class="btn-primary" style="white-space:nowrap;">Send</button>
      </div>
      <div id="send-feedback" style="margin-top:4px;font-size:0.82em;min-height:1em;"></div>
    </div>
  `;

  container.querySelector('#tab-chat').addEventListener('click',   () => _setTab('chat'));
  container.querySelector('#tab-battle').addEventListener('click',  () => _setTab('battle'));

  const input = container.querySelector('#chat-input');
  const sendBtn = container.querySelector('#send-btn');
  sendBtn.addEventListener('click', _onSend);
  input.addEventListener('keydown', e => { if (e.key === 'Enter' && !e.shiftKey) _onSend(); });

  _bindAtMentionAutocomplete(input, container.querySelector('#ac-dropdown'));
}

// ── Lifecycle ────────────────────────────────────────────────────────

async function enter() {
  _loadEmpires();

  // Pre-fill recipient if navigated from dashboard
  if (st.pendingMessageTarget) {
    const { name } = st.pendingMessageTarget;
    st.pendingMessageTarget = null;
    const input = container.querySelector('#chat-input');
    if (input) {
      input.value = `@${name} `;
      input.focus();
      input.setSelectionRange(input.value.length, input.value.length);
    }
    _setTab('chat');
  }

  await _refresh();
  _pollInterval = setInterval(_refresh, 8000);
}

function leave() {
  if (_pollInterval) { clearInterval(_pollInterval); _pollInterval = null; }
}

// ── Tab switching ────────────────────────────────────────────────────

function _setTab(tab) {
  _tab = tab;
  ['chat', 'battle'].forEach(t => {
    container.querySelector(`#tab-${t}`).classList.toggle('active-tab', t === tab);
  });
  // Hide input on battle tab
  const inputArea = container.querySelector('#chat-input-area');
  if (inputArea) inputArea.style.display = tab === 'battle' ? 'none' : '';
  _render(_data);
}

// ── Data ─────────────────────────────────────────────────────────────

async function _refresh() {
  try {
    _data = await rest.getMessages();
    _render(_data);
    _updateTabBadges(_data);
  } catch (err) {
    const el = container.querySelector('#message-list');
    if (el) el.innerHTML = `<div class="error-msg" style="padding:12px">Error: ${_esc(err.message)}</div>`;
  }
}

function _updateTabBadges(data) {
  if (!data) return;
  const chatBtn   = container.querySelector('#tab-chat');
  const battleBtn = container.querySelector('#tab-battle');
  if (chatBtn)   chatBtn.textContent   = `Chat${data.unread_private > 0 ? ` (${data.unread_private})` : ''}`;
  if (battleBtn) battleBtn.textContent = `Battle Reports${data.unread_battle > 0 ? ` (${data.unread_battle})` : ''}`;
}

// ── Render ────────────────────────────────────────────────────────────

function _render(data) {
  const el = container.querySelector('#message-list');
  if (!el) return;

  if (!data) {
    el.innerHTML = '<div class="empty-state"><div class="empty-icon">💬</div><p>No messages</p></div>';
    return;
  }

  const myUid = st.auth?.uid;
  const wasAtBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 60;

  if (_tab === 'chat') {
    _renderChat(el, data.global || [], data.private || [], myUid);
    // Mark unread private as read
    (data.private || []).filter(m => !m.read && m.to_uid === myUid).forEach(m => {
      rest.markMessageRead(m.id).catch(() => {});
      m.read = true;
    });
    if (data.unread_private !== undefined) data.unread_private = 0;
    _updateTabBadges(data);
    if (wasAtBottom) requestAnimationFrame(() => { el.scrollTop = el.scrollHeight; });
  } else {
    _renderBattleReports(el, data.battle_reports || [], myUid);
    // Mark battle reports read
    (data.battle_reports || []).filter(m => !m.read).forEach(m => {
      rest.markMessageRead(m.id).catch(() => {});
      m.read = true;
    });
    if (data.unread_battle !== undefined) data.unread_battle = 0;
    _updateTabBadges(data);
  }
}

function _renderChat(el, globalMsgs, privateMsgs, myUid) {
  const combined = [
    ...globalMsgs.map(m => ({ ...m, _private: false })),
    ...privateMsgs.map(m => ({ ...m, _private: true })),
  ].sort((a, b) => new Date(a.sent_at) - new Date(b.sent_at));

  if (!combined.length) {
    el.innerHTML = '<div class="empty-state" style="padding:20px 0"><div class="empty-icon">💬</div><p>No messages yet. Say hi!</p></div>';
    return;
  }
  el.innerHTML = combined.map(m => {
    const isMe = m.from_uid === myUid;
    const privateLabel = m._private
      ? '<span style="color:var(--text-dim);font-size:10px;margin-left:4px;">(private)</span>'
      : '';
    const privatePeer = m._private
      ? (isMe
          ? `<span style="color:var(--text-dim);font-size:10px;"> → ${_esc(m.to_name)}${m.to_username ? ' (' + _esc(m.to_username) + ')' : ''}</span>`
          : '')
      : '';
    return `
      <div style="display:flex;flex-direction:column;align-items:${isMe ? 'flex-end' : 'flex-start'};gap:1px;">
        <span style="font-size:10px;color:var(--text-dim);padding:0 6px;display:flex;align-items:center;gap:2px;">
          ${_esc(m.from_name)}${m.from_username ? ' (' + _esc(m.from_username) + ')' : ''}${privatePeer}${privateLabel} · ${_fmtTime(m.sent_at)}
        </span>
        <div style="
          max-width:80%;
          background:${m._private ? (isMe ? 'rgba(79,195,247,0.12)' : 'rgba(255,167,38,0.12)') : (isMe ? 'var(--accent-dim,#1a3a4a)' : 'var(--surface-alt)')};
          border:1px solid ${m._private ? (isMe ? '#4fc3f7' : '#ffa726') : (isMe ? 'var(--accent)' : 'var(--border)')};
          border-radius:${isMe ? '12px 12px 4px 12px' : '12px 12px 12px 4px'};
          padding:7px 12px;
          font-size:13px;
          word-break:break-word;
          white-space:pre-wrap;
        ">${_linkify(_esc(m.body))}</div>
      </div>`;
  }).join('');
}



function _renderBattleReports(el, messages, myUid) {
  if (!messages.length) {
    el.innerHTML = '<div class="empty-state"><div class="empty-icon">⚔</div><p>No battle reports yet</p></div>';
    return;
  }
  el.innerHTML = messages.map(m => {
    const unreadDot = !m.read
      ? '<span style="display:inline-block;width:7px;height:7px;border-radius:50%;background:var(--warning,#ffa726);margin-right:5px;flex-shrink:0;"></span>'
      : '';
    return `
      <div class="panel" style="margin-bottom:6px;padding:10px 14px;${!m.read ? 'border-left:3px solid var(--warning,#ffa726);' : ''}">
        <div style="display:flex;justify-content:space-between;font-size:11px;color:var(--text-dim);margin-bottom:6px;">
          <span style="display:flex;align-items:center;">${unreadDot}⚔ Battle Report</span>
          <span>${_fmtTime(m.sent_at)}</span>
        </div>
        <div style="font-family:monospace;font-size:12px;line-height:1.6;white-space:pre-wrap;word-break:break-word;">${_linkify(_esc(m.body))}</div>
      </div>`;
  }).join('');
}

// ── Send ─────────────────────────────────────────────────────────────

async function _onSend() {
  const input    = container.querySelector('#chat-input');
  const sendBtn  = container.querySelector('#send-btn');
  const feedback = container.querySelector('#send-feedback');
  const text = input.value.trim();

  feedback.textContent = '';
  feedback.style.color = '';

  if (!text) return;

  // Detect @mention at start → private message
  const mentionMatch = text.match(/^@(\S+)\s+([\s\S]+)$/);
  let toUid = null;
  let body  = text;

  if (mentionMatch) {
    const targetName = mentionMatch[1];
    body = mentionMatch[2].trim();
    if (!body) {
      feedback.style.color = 'var(--danger,#ef5350)';
      feedback.textContent = '✗ Message body cannot be empty.';
      return;
    }
    sendBtn.disabled = true;
    try {
      ({ uid: toUid } = await rest.resolveEmpire(targetName));
    } catch (err) {
      feedback.style.color = 'var(--danger,#ef5350)';
      feedback.textContent = `✗ ${err.message}`;
      sendBtn.disabled = false;
      return;
    }
  }

  sendBtn.disabled = true;
  try {
    const resp = await rest.sendMessage(toUid, body);
    if (resp.success) {
      input.value = '';
      await _refresh();
      if (toUid) {
        _setTab('chat');
      } else {
        // scroll to bottom after send
        const el = container.querySelector('#message-list');
        if (el) requestAnimationFrame(() => { el.scrollTop = el.scrollHeight; });
      }
    } else {
      feedback.style.color = 'var(--danger,#ef5350)';
      feedback.textContent = `✗ ${resp.error || 'Failed to send'}`;
    }
  } catch (err) {
    feedback.style.color = 'var(--danger,#ef5350)';
    feedback.textContent = `✗ ${err.message}`;
  } finally {
    sendBtn.disabled = false;
  }
}

// ── @mention Autocomplete ─────────────────────────────────────────────

async function _loadEmpires() {
  try {
    const resp = await rest.getEmpires();
    _empiresCache = resp.empires || [];
  } catch (_) {}
}

function _bindAtMentionAutocomplete(input, dropdown) {
  let _filtered = [];
  let _activeIdx = -1;

  function _render(items, q) {
    _filtered = items;
    _activeIdx = -1;
    if (!items.length) { dropdown.style.display = 'none'; return; }
    const shown = items.slice(0, 10);
    dropdown.innerHTML = shown.map((e, i) =>
      `<div class="empire-ac-item" data-idx="${i}">
        <span class="eac-label">${_hilite(e.name, q)}
          <span class="eac-meta">${e.username ? '(@' + _hilite(e.username, q) + ')' : ''}</span>
        </span>
      </div>`
    ).join('');
    dropdown.style.display = 'block';
    dropdown.querySelectorAll('.empire-ac-item').forEach(el => {
      el.addEventListener('mousedown', ev => { ev.preventDefault(); _select(parseInt(el.dataset.idx, 10)); });
    });
    dropdown.querySelectorAll('.empire-ac-item').forEach((el, i) => {
      el.classList.toggle('empire-ac-item--active', i === _activeIdx);
    });
  }

  function _select(idx) {
    const empire = _filtered[idx];
    if (!empire) return;
    // Replace the @partial with @name + space
    const val = input.value;
    const atPos = val.lastIndexOf('@');
    input.value = val.slice(0, atPos) + `@${empire.name} `;
    dropdown.style.display = 'none';
    input.focus();
  }

  function _highlight() {
    dropdown.querySelectorAll('.empire-ac-item').forEach((el, i) => {
      el.classList.toggle('empire-ac-item--active', i === _activeIdx);
    });
  }

  function _search() {
    const val = input.value;
    // Find last @ that hasn't been followed by a space yet
    const atPos = val.lastIndexOf('@');
    if (atPos === -1) { dropdown.style.display = 'none'; return; }
    const afterAt = val.slice(atPos + 1);
    if (afterAt.includes(' ')) { dropdown.style.display = 'none'; return; }
    if (!afterAt) { dropdown.style.display = 'none'; return; }
    const q = afterAt.toLowerCase();
    const matches = _empiresCache.filter(e =>
      e.name.toLowerCase().includes(q) || (e.username || '').toLowerCase().includes(q)
    );
    _render(matches, q);
  }

  input.addEventListener('input', _search);
  input.addEventListener('keydown', e => {
    if (dropdown.style.display === 'none') return;
    const count = Math.min(_filtered.length, 10);
    if (e.key === 'ArrowDown')  { e.preventDefault(); _activeIdx = Math.min(_activeIdx + 1, count - 1); _highlight(); }
    else if (e.key === 'ArrowUp') { e.preventDefault(); _activeIdx = Math.max(_activeIdx - 1, 0); _highlight(); }
    else if (e.key === 'Enter' && _activeIdx >= 0) { e.preventDefault(); _select(_activeIdx); }
    else if (e.key === 'Escape') { dropdown.style.display = 'none'; }
  });
  input.addEventListener('blur', () => setTimeout(() => { dropdown.style.display = 'none'; }, 150));
}

// ── Helpers ───────────────────────────────────────────────────────────

function _esc(str) {
  return String(str)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;')
    .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

function _escAttr(str) {
  return String(str).replace(/&/g, '&amp;').replace(/"/g, '&quot;');
}

function _hilite(str, q) {
  if (!q) return _esc(str);
  const s = String(str);
  const idx = s.toLowerCase().indexOf(q.toLowerCase());
  if (idx === -1) return _esc(s);
  return _esc(s.slice(0, idx))
    + '<mark class="eac-hl">' + _esc(s.slice(idx, idx + q.length)) + '</mark>'
    + _esc(s.slice(idx + q.length));
}

function _linkify(html) {
  // Match both new datetime keys (20260101_120000_42) and legacy numeric bids
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
