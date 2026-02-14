/**
 * Social view — messaging between players.
 */

import { eventBus } from '../events.js';

/** @type {import('../state.js').StateStore} */
let st;
/** @type {HTMLElement} */
let container;
let _unsub = [];

function init(el, _api, _state) {
  container = el;
  st = _state;

  container.innerHTML = `
    <h2>Messages</h2>
    <div class="panel" style="margin-bottom:12px">
      <div class="panel-header">Send Message</div>
      <div class="form-row">
        <div class="form-group" style="margin-bottom:0;max-width:120px">
          <label for="msg-target-uid">Target UID</label>
          <input type="number" id="msg-target-uid" placeholder="UID">
        </div>
        <div class="form-group" style="margin-bottom:0;flex:3">
          <label for="msg-body">Message</label>
          <input type="text" id="msg-body" placeholder="Write a message…">
        </div>
        <button id="send-msg-btn" style="align-self:flex-end">Send</button>
      </div>
    </div>
    <div id="message-list">
      <div class="empty-state"><div class="empty-icon">✉</div><p>No messages loaded</p></div>
    </div>
  `;

  container.querySelector('#send-msg-btn').addEventListener('click', onSend);
  container.querySelector('#msg-body').addEventListener('keydown', (e) => {
    if (e.key === 'Enter') onSend();
  });
}

async function enter() {
  _unsub.push(eventBus.on('notification', () => refresh()));
  await refresh();
}

function leave() {
  _unsub.forEach(fn => fn());
  _unsub = [];
}

async function refresh() {
  // messaging not yet implemented on server
  renderMessages(null);
}

async function onSend() {
  // messaging not yet implemented on server
  console.warn('[Social] sendMessage not implemented');
}

function renderMessages(data) {
  const el = container.querySelector('#message-list');
  if (!data || !data.messages || data.messages.length === 0) {
    el.innerHTML = '<div class="empty-state"><div class="empty-icon">✉</div><p>No messages</p></div>';
    return;
  }
  el.innerHTML = data.messages.map(m => `
    <div class="card">
      <div class="card-title">UID ${m.from_uid || '?'}</div>
      <div class="card-meta">${m.body || ''}</div>
    </div>
  `).join('');
}

export default {
  id: 'social',
  title: 'Social',
  init,
  enter,
  leave,
};
