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
let _availableCritters = [];

function init(el, _api, _state) {
  container = el;
  api = _api;
  st = _state;

  container.innerHTML = `
    <h2>Army Composer</h2>
    
    <!-- ── Create Army Header ──────────────────────────── -->
    <div class="panel" style="margin-bottom:24px">
      <div class="panel-header">New Army</div>
      <div class="form-row">
        <div class="form-group" style="margin-bottom:0">
          <label for="army-name">Name</label>
          <input type="text" id="army-name" placeholder="Army name">
        </div>
        <button id="create-army-btn" style="align-self:flex-end">Create</button>
      </div>
    </div>

    <!-- ── Armies Overview ────────────────────────────── -->
    <h3>Your Armies</h3>
    <div id="army-list" class="army-tiles">
      <div class="empty-state"><div class="empty-icon">⚔</div><p>Loading armies…</p></div>
    </div>
  `;

  container.querySelector('#create-army-btn').addEventListener('click', onCreateArmy);
}

async function enter() {
  // Listen to military data updates (but only for this view)
  _unsub.push(eventBus.on('state:military', renderArmies));
  
  // Load once on entry
  try {
    await api.getMilitary();
  } catch (err) {
    console.error('Failed to load military data:', err);
  }
}

function showMessage(inputElement, text, type = 'error') {
  const msgId = `msg-${Date.now()}`;
  const msgEl = document.createElement('div');
  msgEl.id = msgId;
  msgEl.style.cssText = `
    font-size: 12px;
    padding: 4px 8px;
    margin-top: 4px;
    border-radius: var(--radius);
    color: white;
    text-align: center;
    animation: fadeIn 0.2s;
  `;
  
  if (type === 'error') {
    msgEl.style.background = 'var(--red, #d32f2f)';
  } else if (type === 'success') {
    msgEl.style.background = 'var(--green, #388e3c)';
  }
  
  msgEl.textContent = text;
  inputElement.parentNode.insertBefore(msgEl, inputElement.nextSibling);
  
  setTimeout(() => {
    msgEl.remove();
  }, 3000);
}

function leave() {
  _unsub.forEach(fn => fn());
  _unsub = [];
}

async function onCreateArmy() {
  const name = container.querySelector('#army-name').value.trim();
  if (!name) return;
  await api.createArmy(name);
  container.querySelector('#army-name').value = '';
  await api.getMilitary();
}

async function onEditArmyName(e) {
  const btn = e.currentTarget;
  const aid = parseInt(btn.getAttribute('data-aid'), 10);
  const armyGroup = btn.closest('.army-group');
  const nameHeader = armyGroup.querySelector('.army-name-header');
  const nameEl = armyGroup.querySelector('.army-name');
  const currentName = nameEl.textContent;

  // Replace name with input field
  nameHeader.innerHTML = `
    <input type="text" class="army-name-input" value="${currentName}" data-aid="${aid}" />
    <button class="army-confirm-btn" data-aid="${aid}" title="Save">✓</button>
    <button class="army-cancel-btn" data-aid="${aid}" title="Cancel">✕</button>
  `;

  const input = nameHeader.querySelector('.army-name-input');
  const confirmBtn = nameHeader.querySelector('.army-confirm-btn');
  const cancelBtn = nameHeader.querySelector('.army-cancel-btn');

  input.focus();
  input.select();

  const saveChange = async () => {
    const newName = input.value.trim();
    if (newName && newName !== currentName) {
      try {
        await api.changeArmy(aid, newName);
        await api.getMilitary();
      } catch (err) {
        console.error('Failed to change army name:', err);
      }
    } else {
      // Cancel: re-render
      await api.getMilitary();
    }
  };

  const cancelChange = async () => {
    await api.getMilitary();
  };

  input.addEventListener('keydown', (ev) => {
    if (ev.key === 'Enter') saveChange();
    if (ev.key === 'Escape') cancelChange();
  });

  confirmBtn.addEventListener('click', saveChange);
  cancelBtn.addEventListener('click', cancelChange);
}

async function onAddWave(e) {
  const waveTile = e.currentTarget;
  const wavesContainer = waveTile.closest('.waves-container');
  const armyGroup = wavesContainer.closest('.army-group');
  const aid = parseInt(armyGroup.getAttribute('data-aid'), 10);

  try {
    await api.addWave(aid);  // Server decides critter type (SLAVE)
    await api.getMilitary();
  } catch (err) {
    console.error('Failed to add wave:', err);
  }
}

async function onChangeCritter(e) {
  const select = e.currentTarget;
  const aid = parseInt(select.getAttribute('data-aid'), 10);
  const waveIdx = parseInt(select.getAttribute('data-wave-idx'), 10);
  const critterIid = select.value;

  if (!critterIid) return;

  try {
    await api.changeWave(aid, waveIdx, critterIid);
    await api.getMilitary();
  } catch (err) {
    console.error('Failed to change critter:', err);
  }
}

async function onIncreaseSlots(e) {
  const btn = e.currentTarget;
  const aid = parseInt(btn.getAttribute('data-aid'), 10);
  const waveIdx = parseInt(btn.getAttribute('data-wave-idx'), 10);
  const currentCount = parseInt(btn.getAttribute('data-count'), 10) || 1;
  const newCount = currentCount + 1;

  try {
    await api.changeWave(aid, waveIdx, undefined, newCount);
    await api.getMilitary();
  } catch (err) {
    console.error('Failed to increase critter count:', err);
  }
}

async function onDecreaseSlots(e) {
  const btn = e.currentTarget;
  const aid = parseInt(btn.getAttribute('data-aid'), 10);
  const waveIdx = parseInt(btn.getAttribute('data-wave-idx'), 10);
  const currentCount = parseInt(btn.getAttribute('data-count'), 10) || 1;
  
  // Don't allow decreasing below 1 slot
  if (currentCount <= 1) {
    return;
  }
  
  const newCount = currentCount - 1;

  try {
    await api.changeWave(aid, waveIdx, undefined, newCount);
    await api.getMilitary();
  } catch (err) {
    console.error('Failed to decrease critter count:', err);
  }
}

async function onAttackOpponent(e) {
  const btn = e.currentTarget;
  const aid = parseInt(btn.getAttribute('data-aid'), 10);
  
  const inputId = `target-uid-${aid}`;
  const input = container.querySelector(`#${inputId}`);
  const targetUidStr = input.value.trim();

  if (!targetUidStr) {
    showMessage(input, 'Please enter target Empire ID', 'error');
    return;
  }

  const targetUid = parseInt(targetUidStr, 10);
  if (isNaN(targetUid) || targetUid < 1) {
    showMessage(input, 'Invalid Empire ID (must be ≥ 1)', 'error');
    return;
  }

  try {
    const resp = await api.attackOpponent(targetUid, aid);
    if (resp.success) {
      showMessage(input, `Attack launched! ETA: ${Math.round(resp.eta_seconds)}s`, 'success');
    } else {
      showMessage(input, `Attack failed: ${resp.error}`, 'error');
    }
  } catch (err) {
    console.error('Failed to launch attack:', err);
    showMessage(input, 'Network error', 'error');
  }
}

function renderArmies(data) {
  const el = container.querySelector('#army-list');
  if (!data) {
    el.innerHTML = '<div class="empty-state"><div class="empty-icon">⚔</div><p>No data available</p></div>';
    return;
  }


  // Store available critters
  _availableCritters = data.available_critters || [];

  const armies = data.armies || [];
  if (armies.length === 0) {
    el.innerHTML = '<div class="empty-state"><div class="empty-icon">⚔</div><p>No armies yet. Create one above to get started.</p></div>';
    return;
  }

  el.classList.add('armies-container');
  el.innerHTML = armies.map((a, idx) => `
    <div class="army-group" data-aid="${a.aid}">
      <div class="army-name-header">
        <div class="army-name">${a.name} <span class="army-id"></span></div>(ID: ${a.aid})
        <button class="army-edit-btn" title="Edit army name" data-aid="${a.aid}">
          <span class="edit-icon">✎</span>
        </button>
      </div>
      <div class="army-attack-row">
        <input type="number" id="target-uid-${a.aid}" class="target-uid-input" placeholder="Target Empire ID" data-aid="${a.aid}" min="1" />
        <button class="army-attack-btn" data-aid="${a.aid}" title="Launch attack">⚔ Attack</button>
      </div>
      <div class="waves-container">
        ${(a.waves || []).length > 0 ? `
          ${(a.waves || []).map((w, i) => `
            <div class="wave-tile" data-aid="${a.aid}" data-wave-idx="${i}">
              <div class="wave-tile-header">
                <select class="wave-critter-select" data-aid="${a.aid}" data-wave-idx="${i}">
                  <option value="">-- Select --</option>
                  ${_availableCritters.map(c => `
                    <option value="${c.iid}" ${c.iid === w.iid ? 'selected' : ''}>
                      ${c.name}
                    </option>
                  `).join('')}
                </select>
              </div>
              <div class="wave-tile-body">
                <button class="wave-slots-btn wave-slots-decrease" data-aid="${a.aid}" data-wave-idx="${i}" data-count="${w.slots || 0}" title="Remove critter" ${(w.slots || 0) <= 1 ? 'disabled' : ''}>-</button>
                <div class="wave-tile-count">${w.slots || 0}</div>
                <button class="wave-slots-btn wave-slots-increase" data-aid="${a.aid}" data-wave-idx="${i}" data-count="${w.slots || 0}" title="Add critter">+</button>
              </div>
              <div class="wave-tile-footer">
                <span class="wave-time">${w.spawn_interval_ms}ms</span>
              </div>
            </div>
          `).join('')}
        ` : ''}
        <div class="wave-tile wave-tile-add">
          <div class="wave-tile-plus">+</div>
        </div>
      </div>
      ${idx < armies.length - 1 ? '<div class="army-separator"></div>' : ''}
    </div>
  `).join('');

  // Attach edit button listeners
  el.querySelectorAll('.army-edit-btn').forEach(btn => {
    btn.addEventListener('click', (e) => onEditArmyName(e));
  });

  // Attach wave-add button listeners
  el.querySelectorAll('.wave-tile-add').forEach(btn => {
    btn.addEventListener('click', (e) => onAddWave(e));
  });

  // Attach critter select listeners
  el.querySelectorAll('.wave-critter-select').forEach(select => {
    select.addEventListener('change', (e) => onChangeCritter(e));
  });

  // Attach slots button listeners
  el.querySelectorAll('.wave-slots-increase').forEach(btn => {
    btn.addEventListener('click', (e) => onIncreaseSlots(e));
  });

  el.querySelectorAll('.wave-slots-decrease').forEach(btn => {
    btn.addEventListener('click', (e) => onDecreaseSlots(e));
  });

  // Attach attack button listeners
  el.querySelectorAll('.army-attack-btn').forEach(btn => {
    btn.addEventListener('click', (e) => onAttackOpponent(e));
  });
}

export default {
  id: 'army',
  title: 'Army Composer',
  init,
  enter,
  leave,
};
