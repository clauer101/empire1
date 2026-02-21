/**
 * Army Composer view — create and edit armies with critter waves.
 */

import { eventBus } from '../events.js';
import { rest } from '../rest.js';

/** @type {import('../api.js').ApiClient} */
let api;
/** @type {import('../state.js').StateStore} */
let st;
/** @type {HTMLElement} */
let container;
let _unsub = [];
let _availableCritters = [];

/**
 * Calculate critter slot price based on current slots in wave.
 * Matches server-side sigmoid formula from empire_service.py
 * @param {number} slotNumber - The slot number (1-based)
 * @returns {number} Price in gold
 */
function calculateCritterSlotPrice(slotNumber) {
  const maxv = 13000, minv = 25, spread = 15, steep = 6;
  return minv + (maxv - minv) / (1 + Math.exp((-7 * slotNumber) / spread + steep));
}

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
        <div style="display:flex;flex-direction:column;align-items:flex-end;">
          <button id="create-army-btn" style="align-self:flex-end">Create</button>
          <div id="army-price-display" style="font-size:10px;margin-top:4px;color:var(--text-muted);"></div>
        </div>
      </div>
      <div id="army-create-msg"></div>
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
  _unsub.push(eventBus.on('state:summary', updateCreateArmyButton));
  
  // Load once on entry
  try {
    await rest.getSummary();
    updateCreateArmyButton();
    await rest.getMilitary();
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
    margin-top: 8px;
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
  
  // Check if this is a wave/critter-related message
  const armyGroup = inputElement.closest('.army-group');
  if (armyGroup) {
    // For wave/critter messages, show under the waves container
    const wavesContainer = armyGroup.querySelector('.waves-container');
    if (wavesContainer) {
      // Remove any existing messages in this army group
      const existingMsg = armyGroup.querySelector('.wave-message-container');
      if (existingMsg) {
        existingMsg.remove();
      }
      
      // Insert message after waves container
      const messageContainer = document.createElement('div');
      messageContainer.className = 'wave-message-container';
      messageContainer.appendChild(msgEl);
      wavesContainer.parentNode.insertBefore(messageContainer, wavesContainer.nextSibling);
    } else {
      // Fallback to old behavior
      inputElement.parentNode.insertBefore(msgEl, inputElement.nextSibling);
    }
  } else {
    // For non-wave messages (like army creation), use old behavior
    inputElement.parentNode.insertBefore(msgEl, inputElement.nextSibling);
  }
  
  setTimeout(() => {
    msgEl.remove();
    // Also remove the container if empty
    const messageContainer = msgEl.closest('.wave-message-container');
    if (messageContainer && !messageContainer.hasChildNodes()) {
      messageContainer.remove();
    }
  }, 3000);
}

function leave() {
  _unsub.forEach(fn => fn());
  _unsub = [];
}

function updateCreateArmyButton() {
  const armyPrice = st.summary?.army_price || 0;
  const currentGold = st.summary?.resources?.gold || 0;
  const canAfford = currentGold >= armyPrice;
  
  const btn = container.querySelector('#create-army-btn');
  const priceDisplay = container.querySelector('#army-price-display');
  
  if (btn && priceDisplay) {
    priceDisplay.textContent = `💰 ${Math.round(armyPrice)} Gold`;
    priceDisplay.style.color = canAfford ? 'var(--text-muted)' : 'var(--danger)';
    
    if (!canAfford) {
      btn.style.opacity = '0.5';
      btn.style.cursor = 'not-allowed';
      btn.title = `Not enough gold (${Math.round(armyPrice)} needed)`;
    } else {
      btn.style.opacity = '1';
      btn.style.cursor = 'pointer';
      btn.title = `Create army (${Math.round(armyPrice)} gold)`;
    }
  }
}

async function onCreateArmy() {
  const armyPrice = st.summary?.army_price || 0;
  const currentGold = st.summary?.resources?.gold || 0;
  
  if (currentGold < armyPrice) {
    const msgEl = container.querySelector('#army-create-msg');
    showMessage(msgEl, `Not enough gold (need ${Math.round(armyPrice)}, have ${Math.round(currentGold)})`, 'error');
    return;
  }
  
  const nameInput = container.querySelector('#army-name');
  const name = nameInput.value.trim();
  const msgEl = container.querySelector('#army-create-msg');
  
  if (!name) {
    showMessage(msgEl, 'Please enter army name', 'error');
    return;
  }
  
  try {
    const resp = await rest.createArmy(name);
    if (resp.success) {
      nameInput.value = '';
      showMessage(msgEl, `✓ Army "${name}" created! Cost: ${Math.round(resp.cost)} gold`, 'success');
      await rest.getSummary();
      await rest.getMilitary();
    } else {
      showMessage(msgEl, `✗ ${resp.error || 'Failed to create army'}`, 'error');
    }
  } catch (err) {
    console.error('Failed to create army:', err);
    showMessage(msgEl, '✗ Network error', 'error');
  }
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
        await rest.changeArmy(aid, newName);
        await rest.getMilitary();
      } catch (err) {
        console.error('Failed to change army name:', err);
      }
    } else {
      // Cancel: re-render
      await rest.getMilitary();
    }
  };

  const cancelChange = async () => {
    await rest.getMilitary();
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
  const canAfford = waveTile.getAttribute('data-can-afford') === 'true';
  
  if (!canAfford) {
    const price = waveTile.getAttribute('data-price') || '0';
    const currentGold = st.summary?.resources?.gold || 0;
    showMessage(waveTile, `Not enough gold (need ${price}, have ${Math.round(currentGold)})`, 'error');
    return;
  }
  
  const armyGroup = waveTile.closest('.army-group');
  const aid = parseInt(armyGroup.getAttribute('data-aid'), 10);

  try {
    const resp = await rest.buyWave(aid);
    if (resp.success) {
      showMessage(waveTile, `✓ Wave added! Cost: ${Math.round(resp.cost)} gold`, 'success');
      // Reload summary to update prices and gold
      await rest.getSummary();
      await rest.getMilitary();
    } else {
      showMessage(waveTile, `✗ ${resp.error || 'Failed to add wave'}`, 'error');
    }
  } catch (err) {
    console.error('Failed to add wave:', err);
    showMessage(waveTile, '✗ Network error', 'error');
  }
}

async function onChangeCritter(e) {
  const select = e.currentTarget;
  const aid = parseInt(select.getAttribute('data-aid'), 10);
  const waveIdx = parseInt(select.getAttribute('data-wave-idx'), 10);
  const critterIid = select.value;

  if (!critterIid) return;

  try {
    await rest.changeWave(aid, waveIdx, critterIid);
    await rest.getMilitary();
  } catch (err) {
    console.error('Failed to change critter:', err);
  }
}

async function onIncreaseSlots(e) {
  const btn = e.currentTarget;
  const canAfford = btn.getAttribute('data-can-afford') === 'true';
  
  if (!canAfford) {
    const price = btn.getAttribute('data-price') || '0';
    const currentGold = st.summary?.resources?.gold || 0;
    showMessage(btn.closest('.wave-tile'), `Not enough gold (need ${price}, have ${Math.round(currentGold)})`, 'error');
    return;
  }
  
  const aid = parseInt(btn.getAttribute('data-aid'), 10);
  const waveIdx = parseInt(btn.getAttribute('data-wave-idx'), 10);

  try {
    const resp = await rest.buyCritterSlot(aid, waveIdx);
    if (resp.success) {
      showMessage(btn.closest('.wave-tile'), `✓ Critter added! Cost: ${Math.round(resp.cost)} gold`, 'success');
      // Reload summary to update prices and gold
      await rest.getSummary();
      await rest.getMilitary();
    } else {
      showMessage(btn.closest('.wave-tile'), `✗ ${resp.error || 'Failed to add critter'}`, 'error');
    }
  } catch (err) {
    console.error('Failed to increase critter count:', err);
    showMessage(btn.closest('.wave-tile'), '✗ Network error', 'error');
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
    await rest.changeWave(aid, waveIdx, undefined, newCount);
    await rest.getMilitary();
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
    const resp = await rest.attackOpponent(targetUid, aid);
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

  // Get prices from summary
  const wavePrice = st.summary?.wave_price || 0;
  const currentGold = st.summary?.resources?.gold || 0;
  const canAffordWave = currentGold >= wavePrice;

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
          ${(a.waves || []).map((w, i) => {
            // Calculate slot price for this specific wave
            const nextSlotPrice = calculateCritterSlotPrice((w.slots || 0) + 1);
            const canAffordSlot = currentGold >= nextSlotPrice;
            return `
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
                <button class="wave-slots-btn wave-slots-increase" data-aid="${a.aid}" data-wave-idx="${i}" data-count="${w.slots || 0}" 
                  title="${canAffordSlot ? `Add critter (${Math.round(nextSlotPrice)} gold)` : `Not enough gold (${Math.round(nextSlotPrice)} needed)`}"
                  style="position:relative;${canAffordSlot ? '' : 'opacity:0.5;cursor:not-allowed;'}"
                  data-price="${Math.round(nextSlotPrice)}"
                  data-can-afford="${canAffordSlot}">
                  <span style="font-size:16px;">+</span>
                  <span style="position:absolute;bottom:-18px;left:50%;transform:translateX(-50%);font-size:9px;white-space:nowrap;color:${canAffordSlot ? 'var(--text)' : 'var(--danger)'};">
                    💰${Math.round(nextSlotPrice)}
                  </span>
                </button>
              </div>
              ${w.spawn_interval_ms ? `<div class="wave-tile-footer"><span class="wave-time">${w.spawn_interval_ms}ms</span></div>` : ''}
            </div>
          `;}).join('')}
        ` : ''}
        <div class="wave-tile wave-tile-add" data-aid="${a.aid}" 
          title="${canAffordWave ? `Add wave (${Math.round(wavePrice)} gold)` : `Not enough gold (${Math.round(wavePrice)} needed)`}"
          style="${canAffordWave ? '' : 'opacity:0.5;cursor:not-allowed;'}"
          data-price="${Math.round(wavePrice)}"
          data-can-afford="${canAffordWave}">
          <div class="wave-tile-plus">+</div>
          <div style="font-size:11px;margin-top:4px;color:${canAffordWave ? 'var(--text)' : 'var(--danger)'};">
            💰 ${Math.round(wavePrice)}
          </div>
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
