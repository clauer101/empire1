/**
 * Army Composer view — create and edit armies with critter waves.
 */

import { eventBus } from '../events.js';
import { rest } from '../rest.js';
import { escHtml, hilite } from '../lib/html.js';

/** @type {import('../api.js').ApiClient} */
let api;
/** @type {import('../state.js').StateStore} */
let st;
/** @type {HTMLElement} */
let container;
let _unsub = [];
let _availableCritters = [];
let _empiresCache = [];

function init(el, _api, _state) {
  container = el;
  api = _api;
  st = _state;

  container.innerHTML = `
    <h2 class="battle-title">🗡 Army Composer<span class="title-resources"><span class="title-gold"></span><span class="title-culture"></span><span class="title-life"></span></span></h2>

    <div id="attack-target-banner" style="display:none;margin-bottom:12px;padding:8px 12px;background:rgba(229,57,53,0.15);border:1px solid var(--danger,#e53935);border-radius:var(--radius);color:var(--danger,#e53935);font-weight:bold;"></div>
    
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
    <h3>Your Armies <span style="font-size:11px;font-weight:400;color:var(--text-dim)">— regenerated after each battle</span></h3>
    <div id="army-list" class="army-tiles">
      <div class="empty-state"><div class="empty-icon">⚔</div><p>Loading armies…</p></div>
    </div>

    <!-- ── Critter Picker Overlay ──────────────────────── -->
    <div class="tile-overlay" id="critter-overlay" style="display:none;">
      <div class="tile-overlay__content" style="width:min(680px,95vw)">
        <div class="tile-overlay__header">
          <h3>Critter wählen</h3>
          <button class="tile-overlay__close" id="critter-overlay-close">✕</button>
        </div>
        <div class="tile-overlay__body" id="critter-overlay-body"></div>
      </div>
    </div>
  `;

  container.querySelector('#create-army-btn').addEventListener('click', onCreateArmy);

  // Bind critter overlay close
  const critterOverlay = container.querySelector('#critter-overlay');
  const _closeOverlay = () => critterOverlay.classList.remove('is-open');
  container.querySelector('#critter-overlay-close').addEventListener('click', _closeOverlay);
  critterOverlay.addEventListener('click', (e) => {
    if (e.target === critterOverlay) _closeOverlay();
  });
  // Close on Escape
  const _onKeyDown = (e) => {
    if (e.key === 'Escape') _closeOverlay();
  };
  document.addEventListener('keydown', _onKeyDown);
  _unsub.push(() => document.removeEventListener('keydown', _onKeyDown));
}

async function enter() {
  // Listen to military data updates (but only for this view)
  _unsub.push(eventBus.on('state:military', renderArmies));
  _unsub.push(eventBus.on('state:summary', updateCreateArmyButton));
  
  // Load once on entry
  _loadEmpires();
  try {
    await rest.getSummary();
    updateCreateArmyButton();
    await rest.getMilitary();
  } catch (err) {
    console.error('Failed to load military data:', err);
  }

  // Pre-fill target inputs if navigated here from the empire list
  if (st.pendingAttackTarget) {
    const { uid, name } = st.pendingAttackTarget;
    st.pendingAttackTarget = null;
    // Fill all target-uid inputs with the empire name and scroll to first one
    const inputs = container.querySelectorAll('.target-uid-input');
    inputs.forEach(inp => { inp.value = name || uid; });
    if (inputs.length > 0) {
      inputs[0].scrollIntoView({ behavior: 'smooth', block: 'center' });
      inputs[0].focus();
    }
    // Show a banner so the user knows what the pre-filled target is
    const banner = container.querySelector('#attack-target-banner');
    if (banner) {
      banner.textContent = `⚔ Ziel: ${name} (ID ${uid})`;
      banner.style.display = '';
    }
  } else {
    const banner = container.querySelector('#attack-target-banner');
    if (banner) banner.style.display = 'none';
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

async function onChangeCritter(aid, waveIdx, critterIid) {
  if (!critterIid) return;
  try {
    await rest.changeWave(aid, waveIdx, critterIid);
    await rest.getMilitary();
  } catch (err) {
    console.error('Failed to change critter:', err);
  }
}

const _SPRITE_EXTS = ['.png', '.webp', '.jpg'];

/**
 * Initialize canvas elements with class .critter-sprite-canvas.
 * Uses data-sprite (exact resolved path) when available.
 * Falls back to data-animation folder or data-iid with extension probing.
 * Extracts the first frame (top-left) from a 4×4 sprite sheet,
 * preserving the original aspect ratio (letterboxed into the canvas).
 */
function _initCritterCanvases(el) {
  el.querySelectorAll('.critter-sprite-canvas').forEach(canvas => {
    const drawFrame = (img) => {
      const ctx = canvas.getContext('2d');
      const fw = img.width / 4;
      const fh = img.height / 4;
      const scale = Math.min(canvas.width / fw, canvas.height / fh);
      const dx = Math.floor((canvas.width  - fw * scale) / 2);
      const dy = Math.floor((canvas.height - fh * scale) / 2);
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.drawImage(img, 0, 0, fw, fh, dx, dy, fw * scale, fh * scale);
    };

    // If we have an exact resolved path, use it directly
    const sprite = canvas.dataset.sprite;
    if (sprite) {
      const img = new Image();
      img.onload = () => drawFrame(img);
      img.onerror = () => { canvas.style.display = 'none'; };
      img.src = sprite;
      return;
    }

    // Fallback: probe extensions
    let baseUrl;
    const anim = canvas.dataset.animation;
    if (anim) {
      const folder = anim.replace(/^\//, '');
      const name = folder.split('/').pop();
      baseUrl = `${folder}/${name}`;
    } else {
      const iid = canvas.dataset.iid;
      baseUrl = `assets/sprites/critters/${iid.toLowerCase()}/${iid.toLowerCase()}`;
    }
    function tryLoad(idx) {
      if (idx >= _SPRITE_EXTS.length) { canvas.style.display = 'none'; return; }
      const img = new Image();
      img.onload = () => drawFrame(img);
      img.onerror = () => tryLoad(idx + 1);
      img.src = baseUrl + _SPRITE_EXTS[idx];
    }
    tryLoad(0);
  });
}

/**
 * Open the critter picker overlay for a specific wave.
 * Shows all available critters as tiles with stats.
 */
function _openCritterOverlay(aid, waveIdx, currentIid) {
  const overlay = container.querySelector('#critter-overlay');
  const body = container.querySelector('#critter-overlay-body');
  if (!overlay || !body) return;

  const currentGold = st.summary?.resources?.gold || 0;

  body.innerHTML = `
    <div class="critter-picker-grid">
      ${[..._availableCritters].reverse().map(c => {
        const isSelected = c.iid === currentIid;
        return `
          <button class="critter-pick-tile${isSelected ? ' critter-pick-tile--selected' : ''}"
              data-iid="${c.iid}">
            <div class="cpt-sprite">
              <canvas class="critter-sprite-canvas" data-iid="${c.iid}" data-sprite="${c.sprite || ''}" data-animation="${c.animation || ''}" width="64" height="64"></canvas>
            </div>
            <div class="cpt-name">${c.name}${c.is_boss ? ' 👑' : ''}</div>
            <div class="cpt-stats">
              <span class="cpt-stat cpt-hp" title="Health">❤ ${(c.health || 0).toFixed(1)}</span>
              ${c.armour ? `<span class="cpt-stat cpt-arm" title="Armour">🛡 ${c.armour}</span>` : ''}
              <span class="cpt-stat cpt-spd" title="Speed">⚡ ${(c.speed || 0).toFixed(2)}</span>
              ${c.slots > 1 ? `<span class="cpt-stat cpt-slots" title="Slot cost">${c.slots} Slots</span>` : ''}
            </div>
          </button>`;
      }).join('')}
    </div>
  `;

  _initCritterCanvases(body);

  // Bind tile clicks
  body.querySelectorAll('.critter-pick-tile').forEach(btn => {
    btn.addEventListener('click', async () => {
      const iid = btn.dataset.iid;
      overlay.classList.remove('is-open');
      await onChangeCritter(aid, waveIdx, iid);
    });
  });

  overlay.classList.add('is-open');
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
      showMessage(btn.closest('.wave-tile'), `✗ ${resp.error || 'Failed to add slot'}`, 'error');
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
  const query = input.value.trim();

  if (!query) {
    showMessage(input, 'Bitte Ziel-Empire eingeben (Name oder ID)', 'error');
    return;
  }

  btn.disabled = true;
  let targetUid, targetName;
  try {
    ({ uid: targetUid, name: targetName } = await rest.resolveEmpire(query));
  } catch (err) {
    showMessage(input, err.message, 'error');
    btn.disabled = false;
    return;
  }

  try {
    const resp = await rest.attackOpponent(targetUid, aid);
    if (resp.success) {
      showMessage(input, `⚔ Angriff auf ${targetName} gestartet! ETA: ${Math.round(resp.eta_seconds)}s`, 'success');
    } else {
      showMessage(input, `✗ ${resp.error || 'Angriff fehlgeschlagen'}`, 'error');
    }
  } catch (err) {
    console.error('Failed to launch attack:', err);
    showMessage(input, 'Netzwerkfehler', 'error');
  } finally {
    btn.disabled = false;
  }
}

function fmtTravelTime(seconds) {
  if (!seconds || seconds <= 0) return '';
  const s = Math.round(seconds);
  if (s < 60) return `${s}s`;
  const m = Math.floor(s / 60), r = s % 60;
  if (m < 60) return r ? `${m}m ${r}s` : `${m}m`;
  const h = Math.floor(m / 60), rm = m % 60;
  return rm ? `${h}h ${rm}m` : `${h}h`;
}

/**
 * How many critters will spawn in a wave given its slot capacity
 * and the slot cost of the selected critter type.
 * @param {number} waveSlots - Total slot capacity of the wave
 * @param {number} critterSlots - Slot cost per critter (default 1)
 * @returns {number}
 */
function critterCountInWave(waveSlots, critterSlots = 1) {
  if (!critterSlots || critterSlots < 1) return waveSlots;
  return Math.floor(waveSlots / critterSlots);
}

// ── Empire Autocomplete ──────────────────────────────────────────

async function _loadEmpires() {
  try {
    const resp = await rest.getEmpires();
    _empiresCache = resp.empires || [];
  } catch (err) {
    console.warn('Failed to load empire list:', err);
  }
}

const _escHtml = escHtml;
const _hilite = (str, q) => hilite(str, q);

function _bindAutocomplete(input) {
  const dropdown = input.nextElementSibling;
  if (!dropdown || !dropdown.classList.contains('empire-ac-dropdown')) return;

  let _activeIdx = -1;
  let _filtered = [];

  function _render(items, q) {
    _filtered = items;
    _activeIdx = -1;
    if (!items.length) { dropdown.style.display = 'none'; return; }
    const shown = items.slice(0, 12);
    dropdown.innerHTML = shown.map((e, i) =>
      `<div class="empire-ac-item" data-idx="${i}">
        <span class="eac-label">${_hilite(e.name, q)} <span class="eac-meta">${e.username ? '(@' + _hilite(e.username, q) + ', ' : '('}uid:${_hilite(String(e.uid), q)})${e.is_self ? ' <em>(you)</em>' : ''}</span></span>
      </div>`
    ).join('');
    dropdown.style.display = 'block';
    dropdown.querySelectorAll('.empire-ac-item').forEach(el => {
      el.addEventListener('mousedown', ev => {
        ev.preventDefault();
        _selectItem(parseInt(el.dataset.idx, 10));
      });
    });
  }

  function _selectItem(idx) {
    const empire = _filtered[idx];
    if (!empire) return;
    input.value = empire.name;
    dropdown.style.display = 'none';
  }

  function _highlight() {
    dropdown.querySelectorAll('.empire-ac-item').forEach((el, i) => {
      el.classList.toggle('empire-ac-item--active', i === _activeIdx);
    });
  }

  function _search() {
    const q = input.value.trim().toLowerCase();
    if (!q) { dropdown.style.display = 'none'; return; }
    const matches = _empiresCache.filter(e =>
      e.name.toLowerCase().includes(q) ||
      (e.username || '').toLowerCase().includes(q) ||
      String(e.uid).includes(q)
    );
    _render(matches, q);
  }

  input.addEventListener('input', _search);
  input.addEventListener('focus', () => { if (input.value.trim()) _search(); });
  input.addEventListener('blur', () => { setTimeout(() => { dropdown.style.display = 'none'; }, 150); });
  input.addEventListener('keydown', e => {
    if (dropdown.style.display === 'none') return;
    const count = Math.min(_filtered.length, 12);
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      _activeIdx = Math.min(_activeIdx + 1, count - 1);
      _highlight();
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      _activeIdx = Math.max(_activeIdx - 1, 0);
      _highlight();
    } else if (e.key === 'Enter' && _activeIdx >= 0) {
      e.preventDefault();
      _selectItem(_activeIdx);
    } else if (e.key === 'Escape') {
      dropdown.style.display = 'none';
    }
  });
}

function renderArmies(data) {
  const el = container.querySelector('#army-list');
  if (!data) {
    el.innerHTML = '<div class="empty-state"><div class="empty-icon">⚔</div><p>No data available</p></div>';
    return;
  }

  // Preserve scroll position and target-uid input values before re-render
  const scrollY = window.scrollY;

  const savedTargets = {};
  el.querySelectorAll('.target-uid-input').forEach(inp => {
    if (inp.value) savedTargets[inp.dataset.aid] = inp.value;
  });

  // Store available critters
  _availableCritters = data.available_critters || [];

  const armies = data.armies || [];
  if (armies.length === 0) {
    el.innerHTML = '<div class="empty-state"><div class="empty-icon">⚔</div><p>No armies yet. Create one above to get started.</p></div>';
    return;
  }

  const currentGold = st.summary?.resources?.gold || 0;

  const travelTime = st.summary?.travel_time_seconds;
  const travelLabel = travelTime ? fmtTravelTime(travelTime) : '';

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
        <div class="empire-ac-wrap">
          <input type="text" id="target-uid-${a.aid}" class="target-uid-input" placeholder="Ziel-Empire (Name oder ID)" data-aid="${a.aid}" autocomplete="off" />
          <div class="empire-ac-dropdown"></div>
        </div>
        <button class="army-attack-btn" data-aid="${a.aid}" title="Launch attack" style="display:flex;flex-direction:column;align-items:center;gap:1px;line-height:1.2;">
          <span>⚔ Attack</span>
          ${travelLabel ? `<span style="font-size:10px;opacity:0.7;">✈ ${travelLabel}</span>` : ''}
        </button>
      </div>
      <div class="waves-container">
        ${(a.waves || []).length > 0 ? `
          ${(a.waves || []).map((w, i) => {
            const nextSlotPrice = w.next_slot_price || 0;
            const canAffordSlot = currentGold >= nextSlotPrice;
            const selectedCritter = _availableCritters.find(c => c.iid === w.iid);
            const critterSlotCost = selectedCritter?.slots || 1;
            const numCritters = critterCountInWave(w.slots || 0, critterSlotCost);
            return `
            <div class="wave-tile" data-aid="${a.aid}" data-wave-idx="${i}">
              <button class="wave-critter-btn" data-aid="${a.aid}" data-wave-idx="${i}" data-current-iid="${w.iid || ''}">
                <span class="wave-tile__edit-hint">✎</span>
                ${selectedCritter
                  ? `<canvas class="wave-tile__sprite critter-sprite-canvas" data-iid="${selectedCritter.iid}" data-sprite="${selectedCritter.sprite || ''}" data-animation="${selectedCritter.animation || ''}" width="72" height="72"
                        style="image-rendering:pixelated;"></canvas>`
                  : `<div class="wave-tile__no-critter">＋</div>`
                }
                <div class="wave-tile__count">${selectedCritter ? numCritters : ''}</div>
              </button>
              <div class="wave-tile__footer">
                <span class="wave-tile__slots">${w.slots || 0} sl</span>
                <button class="wave-slots-btn wave-slots-increase" data-aid="${a.aid}" data-wave-idx="${i}" data-count="${w.slots || 0}"
                  title="${canAffordSlot ? `Add slot (${Math.round(nextSlotPrice)} gold)` : `Not enough gold (${Math.round(nextSlotPrice)} needed)`}"
                  ${canAffordSlot ? '' : 'style="opacity:0.5;cursor:not-allowed;"'}
                  data-price="${Math.round(nextSlotPrice)}"
                  data-can-afford="${canAffordSlot}">
                  + <span style="color:${canAffordSlot ? 'var(--accent)' : 'var(--danger)'};">💰${Math.round(nextSlotPrice)}</span>
                </button>
              </div>
            </div>
          `;}).join('')}
        ` : ''}
        ${(() => {
          const wp = a.next_wave_price || 0;
          const canAff = currentGold >= wp;
          return `<div class="wave-tile wave-tile-add" data-aid="${a.aid}"
            title="${canAff ? `Add wave (${Math.round(wp)} gold)` : `Not enough gold (${Math.round(wp)} needed)`}"
            style="${canAff ? '' : 'opacity:0.5;cursor:not-allowed;'}"
            data-price="${Math.round(wp)}"
            data-can-afford="${canAff}">
            <div class="wave-tile-plus">+</div>
            <div style="font-size:11px;margin-top:4px;color:${canAff ? 'var(--text)' : 'var(--danger)'};">
              💰 ${Math.round(wp)}
            </div>
          </div>`;
        })()}
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

  // Attach critter picker button listeners
  el.querySelectorAll('.wave-critter-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      const aid = parseInt(btn.getAttribute('data-aid'), 10);
      const waveIdx = parseInt(btn.getAttribute('data-wave-idx'), 10);
      const currentIid = btn.getAttribute('data-current-iid') || '';
      _openCritterOverlay(aid, waveIdx, currentIid);
    });
  });

  // Attach slots button listeners
  el.querySelectorAll('.wave-slots-increase').forEach(btn => {
    btn.addEventListener('click', (e) => onIncreaseSlots(e));
  });

  // Attach attack button listeners
  el.querySelectorAll('.army-attack-btn').forEach(btn => {
    btn.addEventListener('click', (e) => onAttackOpponent(e));
  });

  // Restore target-uid values that were present before re-render
  Object.entries(savedTargets).forEach(([aid, val]) => {
    const inp = el.querySelector(`.target-uid-input[data-aid="${aid}"]`);
    if (inp) inp.value = val;
  });

  // Initialize critter sprite canvases (wave buttons)
  _initCritterCanvases(el);

  // Bind autocomplete on all target-empire inputs
  el.querySelectorAll('.target-uid-input').forEach(_bindAutocomplete);

  // Restore scroll position after re-render
  requestAnimationFrame(() => window.scrollTo(0, scrollY));
}

export default {
  id: 'army',
  title: 'Army Composer',
  init,
  enter,
  leave,
};
