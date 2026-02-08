/**
 * Empire Composer view — hex map editor for placing structures.
 */

import { eventBus } from '../events.js';

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
    <h2>Empire Composer</h2>
    <div class="form-row" style="margin-bottom:16px">
      <div class="form-group" style="max-width:220px;margin-bottom:0">
        <label for="structure-select">Place Structure</label>
        <select id="structure-select"><option value="">Select structure…</option></select>
      </div>
      <button class="btn-ghost" id="delete-mode-btn">Delete Mode</button>
    </div>
    <div class="panel" id="hex-map-container" style="min-height:400px;">
      <div class="empty-state">
        <div class="empty-icon">⬡</div>
        <p>Hex map will render here</p>
      </div>
    </div>
  `;
}

async function enter() {
  _unsub.push(eventBus.on('state:items', renderStructureList));
  try {
    await Promise.all([api.getSummary(), api.getItems()]);
    renderStructureList();
  } catch (err) {
    container.querySelector('#hex-map-container').innerHTML =
      `<div class="error-msg">${err.message}</div>`;
  }
}

function leave() {
  _unsub.forEach(fn => fn());
  _unsub = [];
}

function renderStructureList() {
  const select = container.querySelector('#structure-select');
  const items = st.items;
  if (!items || !items.structures) return;

  select.innerHTML = '<option value="">Select structure…</option>';
  for (const [iid, info] of Object.entries(items.structures || {})) {
    const opt = document.createElement('option');
    opt.value = iid;
    opt.textContent = info.name || iid;
    select.appendChild(opt);
  }
}

export default {
  id: 'composer',
  title: 'Empire Composer',
  init,
  enter,
  leave,
};
