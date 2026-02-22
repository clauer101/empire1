/**
 * Social view — messaging between players.
 */

import { rest } from '../rest.js';

/** @type {import('../state.js').StateStore} */
let st;
/** @type {HTMLElement} */
let container;
let _unsub = [];
/** current tab: 'inbox' | 'sent' */
let _tab = 'inbox';
/** cached response from server */
let _data = null;

function init(el, _api, _state) {
  container = el;
  st = _state;
  _renderShell();
}

function _renderShell() {
  container.innerHTML = `
    <h2>Messages</h2>

    <div class="panel" style="margin-bottom:12px">
      <div class="panel-header">New Message</div>
      <div class="form-row" style="gap:8px;align-items:flex-end;">
        <div class="form-group" style="margin-bottom:0;max-width:140px">
          <label for="msg-target-uid">Recipient (Name or ID)</label>
          <input type="text" id="msg-target-uid" placeholder="Empire name or UID">
        </div>
        <div class="form-group" style="margin-bottom:0;flex:3">
          <label for="msg-body">Message</label>
          <input type="text" id="msg-body" placeholder="Write a message…" maxlength="500">
        </div>
        <button id="send-msg-btn">Send</button>
      </div>
      <div id="send-msg-feedback" style="margin-top:6px;font-size:0.85em;"></div>
    </div>

    <div style="display:flex;gap:6px;margin-bottom:8px;">
      <button id="tab-inbox" class="tab-btn active-tab">Inbox</button>
      <button id="tab-sent" class="tab-btn">Sent</button>
      <span style="flex:1"></span>
      <button id="refresh-msg-btn" style="font-size:11px;padding:2px 8px;">↻</button>
    </div>

    <div id="message-list">
      <div class="empty-state"><div class="empty-icon">✉</div><p>Loading…</p></div>
    </div>
  `;

  container.querySelector('#send-msg-btn').addEventListener('click', onSend);
  container.querySelector('#msg-body').addEventListener('keydown', e => { if (e.key === 'Enter') onSend(); });
  container.querySelector('#tab-inbox').addEventListener('click', () => setTab('inbox'));
  container.querySelector('#tab-sent').addEventListener('click', () => setTab('sent'));
  container.querySelector('#refresh-msg-btn').addEventListener('click', refresh);
}

async function enter() {
  // Pre-fill recipient if navigated from dashboard
  if (st.pendingMessageTarget) {
    const { uid, name } = st.pendingMessageTarget;
    st.pendingMessageTarget = null;
    const input = container.querySelector('#msg-target-uid');
    if (input) {
      input.value = name || uid;
      container.querySelector('#msg-body')?.focus();
    }
  }
  await refresh();
}

function leave() {
  _unsub.forEach(fn => fn());
  _unsub = [];
}

function setTab(tab) {
  _tab = tab;
  container.querySelector('#tab-inbox').classList.toggle('active-tab', tab === 'inbox');
  container.querySelector('#tab-sent').classList.toggle('active-tab', tab === 'sent');
  renderMessages(_data);
}

async function refresh() {
  const listEl = container.querySelector('#message-list');
  listEl.innerHTML = '<div class="empty-state"><div class="empty-icon">✉</div><p>Loading…</p></div>';
  try {
    _data = await rest.getMessages();
    renderMessages(_data);
  } catch (err) {
    listEl.innerHTML = `<div class="error-msg">Error: ${err.message}</div>`;
  }
}

async function onSend() {
  const uidInput = container.querySelector('#msg-target-uid');
  const bodyInput = container.querySelector('#msg-body');
  const feedback = container.querySelector('#send-msg-feedback');
  const btn = container.querySelector('#send-msg-btn');

  const query = uidInput.value.trim();
  const body = bodyInput.value.trim();

  feedback.style.color = '';
  feedback.textContent = '';

  if (!query) {
    feedback.style.color = 'var(--danger, #e53935)';
    feedback.textContent = '✗ Please enter a recipient (name or UID).';
    return;
  }
  if (!body) {
    feedback.style.color = 'var(--danger, #e53935)';
    feedback.textContent = '✗ Message cannot be empty.';
    return;
  }

  btn.disabled = true;
  let toUid, toName;
  try {
    ({ uid: toUid, name: toName } = await rest.resolveEmpire(query));
  } catch (err) {
    feedback.style.color = 'var(--danger, #e53935)';
    feedback.textContent = `✗ ${err.message}`;
    btn.disabled = false;
    return;
  }

  try {
    const resp = await rest.sendMessage(toUid, body);
    if (resp.success) {
      feedback.style.color = 'var(--success, #4caf50)';
      feedback.textContent = `✓ Message sent to ${toName}!`;
      bodyInput.value = '';
      await refresh();
      setTab('sent');
      setTimeout(() => { feedback.textContent = ''; }, 4000);
    } else {
      feedback.style.color = 'var(--danger, #e53935)';
      feedback.textContent = `✗ ${resp.error || 'Failed to send'}`;
    }
  } catch (err) {
    feedback.style.color = 'var(--danger, #e53935)';
    feedback.textContent = `✗ ${err.message}`;
  } finally {
    btn.disabled = false;
  }
}

function renderMessages(data) {
  const el = container.querySelector('#message-list');
  if (!data) {
    el.innerHTML = '<div class="empty-state"><div class="empty-icon">✉</div><p>No messages</p></div>';
    return;
  }

  // Update tab counters
  const unread = data.unread || 0;
  container.querySelector('#tab-inbox').textContent =
    `Inbox${unread > 0 ? ` (${unread})` : ''}`;
  container.querySelector('#tab-sent').textContent = 'Sent';

  const list = _tab === 'inbox' ? (data.inbox || []) : (data.sent || []);

  if (list.length === 0) {
    el.innerHTML = '<div class="empty-state"><div class="empty-icon">✉</div><p>No messages</p></div>';
    return;
  }

  const myUid = st.auth?.uid;

  el.innerHTML = list.map(m => {
    const isInbox = m.to_uid === myUid;
    const counterpart = isInbox ? m.from_name : m.to_name;
    const counterpartLabel = isInbox ? `From: ${counterpart}` : `To: ${counterpart}`;
    const unreadDot = (isInbox && !m.read)
      ? '<span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:var(--accent,#4fc3f7);margin-right:6px;"></span>'
      : '';
    return `
      <div class="panel" style="margin-bottom:6px;padding:8px 12px;${!m.read && isInbox ? 'border-left:3px solid var(--accent,#4fc3f7);' : ''}" data-msg-id="${m.id}">
        <div style="display:flex;justify-content:space-between;font-size:0.82em;color:#888;margin-bottom:4px;">
          <span>${unreadDot}${counterpartLabel}</span>
          <span>${m.sent_at || ''}</span>
        </div>
        <div style="word-break:break-word;">${escHtml(m.body)}</div>
      </div>
    `;
  }).join('');

  // Mark unread inbox messages as read when viewed
  if (_tab === 'inbox') {
    list.filter(m => !m.read).forEach(m => {
      rest.markMessageRead(m.id).catch(() => {});
    });
    // Optimistically mark as read in local cache
    if (data.inbox) data.inbox.forEach(m => { m.read = true; });
    if (data.unread !== undefined) data.unread = 0;
    const inboxBtn = container.querySelector('#tab-inbox');
    if (inboxBtn) inboxBtn.textContent = 'Inbox';
    // Clear navbar badge immediately
    const badge = document.getElementById('nav-msg-badge');
    if (badge) { badge.textContent = '0'; badge.style.display = 'none'; }
  }
}

function escHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

export default {
  id: 'social',
  title: 'Social',
  init,
  enter,
  leave,
};
