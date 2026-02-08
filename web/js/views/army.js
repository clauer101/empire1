/**
 * Army Composer view — create and edit armies with critter waves.
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
    <h2>Army Composer</h2>
    <div class="panel" style="margin-bottom:12px">
      <div class="panel-header">Create Army</div>
      <div class="form-row">
        <div class="form-group" style="margin-bottom:0">
          <label for="army-name">Name</label>
          <input type="text" id="army-name" placeholder="Army name">
        </div>
        <div class="form-group" style="margin-bottom:0;max-width:160px">
          <label for="army-direction">Direction</label>
          <select id="army-direction">
            <option value="north">North</option>
            <option value="south">South</option>
            <option value="east">East</option>
            <option value="west">West</option>
          </select>
        </div>
        <button id="create-army-btn" style="align-self:flex-end">Create</button>
      </div>
    </div>
    <div id="army-list">
      <div class="empty-state"><div class="empty-icon">⚔</div><p>Loading armies…</p></div>
    </div>
  `;

  container.querySelector('#create-army-btn').addEventListener('click', onCreateArmy);
}

async function enter() {
  _unsub.push(eventBus.on('state:military', renderArmies));
  try {
    await api.getMilitary();
  } catch (err) {
    container.querySelector('#army-list').innerHTML =
      `<div class="error-msg">${err.message}</div>`;
  }
}

function leave() {
  _unsub.forEach(fn => fn());
  _unsub = [];
}

async function onCreateArmy() {
  const name = container.querySelector('#army-name').value.trim();
  const dir = container.querySelector('#army-direction').value;
  if (!name) return;
  await api.createArmy(dir, name);
  container.querySelector('#army-name').value = '';
  await api.getMilitary();
}

function renderArmies(data) {
  const el = container.querySelector('#army-list');
  if (!data) {
    el.innerHTML = '<div class="empty-state"><div class="empty-icon">⚔</div><p>No data available</p></div>';
    return;
  }

  const armies = data.armies || [];
  if (armies.length === 0) {
    el.innerHTML = '<div class="empty-state"><div class="empty-icon">⚔</div><p>No armies yet. Create one above.</p></div>';
    return;
  }

  el.innerHTML = armies.map(a => `
    <div class="card">
      <div class="card-title">${a.name || a.aid}</div>
      <div class="card-meta">Direction: ${a.direction || '?'} · Waves: ${(a.waves || []).length}</div>
      ${(a.waves || []).map((w, i) => `
        <div class="panel" style="margin-top:8px">
          <div class="panel-row">
            <span class="label">Wave ${i + 1}</span>
            <span class="value">${w.critter || '?'} × ${w.count || 0}</span>
          </div>
        </div>
      `).join('')}
      <div style="margin-top:8px">
        <button class="btn-sm btn-ghost add-wave-btn" data-aid="${a.aid}">+ Add Wave</button>
      </div>
    </div>
  `).join('');
}

export default {
  id: 'army',
  title: 'Army Composer',
  init,
  enter,
  leave,
};
