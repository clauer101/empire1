/**
 * Army Composer view — create and edit armies with critter waves.
 */

import { eventBus } from '../events.js';
import { rest } from '../rest.js';
import { escHtml, hilite } from '../lib/html.js';
import { ERA_KEYS, ERA_YAML_TO_KEY, ERA_ROMAN, ERA_LABEL_EN } from '../lib/eras.js';

/** @type {import('../api.js').ApiClient} */
let api;
/** @type {import('../state.js').StateStore} */
let st;
/** @type {HTMLElement} */
let container;
let _unsub = [];
let _availableCritters = [];
let _critterSprites = {};  // iid → {sprite, animation} for all critters incl. locked
let _empiresCache = [];
/** iid.toUpperCase() → Roman numeral string (e.g. "III") */
let _critterEraRoman = {};
let _critUpgDef = null; // critter_upgrade_def from era-map

function _applyCritUpgrades(c) {
  const upgrades = st.summary?.item_upgrades?.[c.iid] ?? {};
  const d = _critUpgDef;
  if (!d) return c;
  const hpLvl  = upgrades.health ?? 0;
  const spdLvl = upgrades.speed  ?? 0;
  const armLvl = upgrades.armour ?? 0;
  return {
    ...c,
    health: c.health * (1 + (d.health / 100) * hpLvl),
    speed:  c.speed  * (1 + (d.speed  / 100) * spdLvl),
    armour: (c.armour || 0) * (1 + (d.armour / 100) * armLvl),
  };
}

function _buildCritterEraRoman() {
  _critterEraRoman = {};
  const critters = st.items?.critters || {};
  for (const [iid, info] of Object.entries(critters)) {
    const key = ERA_YAML_TO_KEY[info.era] || null;
    if (!key) continue;
    const idx = ERA_KEYS.indexOf(key);
    const roman = idx >= 0 ? ['I','II','III','IV','V','VI','VII','VIII','IX'][idx] : '';
    _critterEraRoman[iid.toUpperCase()] = roman;
  }
}

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
    const [,, eraMap] = await Promise.all([rest.getItems(), rest.getMilitary(), rest.getEraMap()]);
    if (eraMap) _critUpgDef = eraMap.critter_upgrade_def ?? null;
    _buildCritterEraRoman();
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

function showMessage(inputElement, text, type = 'error', persistent = false) {
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
  
  if (!persistent) {
    setTimeout(() => {
      msgEl.remove();
      // Also remove the container if empty
      const messageContainer = msgEl.closest('.wave-message-container');
      if (messageContainer && !messageContainer.hasChildNodes()) {
        messageContainer.remove();
      }
    }, 3000);
  }
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
    const resp = await rest.changeWave(aid, waveIdx, critterIid);
    if (resp?.success === false) {
      console.warn('change critter rejected:', resp.error);
      return;
    }
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
function _openCritterOverlay(aid, waveIdx, currentIid, maxEra = 0, nextEraPrice = 0, nextSlotPrice = 0, currentSlots = 0) {
  const overlay = container.querySelector('#critter-overlay');
  const body = container.querySelector('#critter-overlay-body');
  if (!overlay || !body) return;

  const currentGold = st.summary?.resources?.gold || 0;
  const MAX_ERA_INDEX = 8;
  const eraKey = ERA_KEYS[maxEra] || ERA_KEYS[0];
  const eraLabel = ERA_LABEL_EN[eraKey] || eraKey;
  const eraRoman = ERA_ROMAN[eraKey] || 'I';
  const isMaxEra = maxEra >= MAX_ERA_INDEX;
  const canAffordEra = !isMaxEra && currentGold >= nextEraPrice;
  const canAffordSlot = currentGold >= nextSlotPrice;

  const nextEraKey = ERA_KEYS[maxEra + 1];
  const nextEraLabel = nextEraKey ? ERA_LABEL_EN[nextEraKey] : null;

  body.innerHTML = `
    <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:8px;margin-bottom:14px;">
      <!-- Slots -->
      <div style="display:flex;align-items:center;justify-content:space-between;gap:10px;padding:10px 14px;background:rgba(255,255,255,0.04);border:1px solid var(--border);border-radius:var(--radius);flex-wrap:wrap;">
        <div style="min-width:0;">
          <div style="font-size:18px;font-weight:700;color:var(--accent);line-height:1.1;">${currentSlots}</div>
          <div style="font-size:10px;color:var(--text-dim);margin-top:2px;">Slots · critters per wave</div>
        </div>
        <button id="wave-slot-upgrade-btn"
            style="flex-shrink:0;font-size:11px;padding:4px 10px;background:transparent;color:${canAffordSlot ? 'var(--accent)' : 'var(--danger)'};border:1px solid ${canAffordSlot ? 'var(--accent)' : 'var(--danger)'};border-radius:var(--radius);cursor:${canAffordSlot ? 'pointer' : 'not-allowed'};opacity:${canAffordSlot ? '1' : '0.6'};"
            data-can-afford="${canAffordSlot}" title="${canAffordSlot ? `Add slot (${Math.round(nextSlotPrice)} gold)` : 'Not enough gold'}">
          +1 · 💰${Math.round(nextSlotPrice)}
        </button>
      </div>
      <!-- Era -->
      <div style="display:flex;align-items:center;justify-content:space-between;gap:10px;padding:10px 14px;background:rgba(255,255,255,0.04);border:1px solid var(--border);border-radius:var(--radius);flex-wrap:wrap;">
        <div style="min-width:0;">
          <div style="font-size:18px;font-weight:700;color:#c9a84c;line-height:1.1;">${eraRoman} <span style="font-size:12px;font-weight:400;color:var(--text-dim);">${eraLabel}</span></div>
          <div style="font-size:10px;color:var(--text-dim);margin-top:2px;">Max era · unlocks critter types</div>
        </div>
        ${isMaxEra
          ? `<span style="font-size:10px;color:var(--text-dim);flex-shrink:0;">Max</span>`
          : `<button id="wave-era-upgrade-btn"
              style="flex-shrink:0;font-size:11px;padding:4px 10px;background:transparent;color:${canAffordEra ? '#c9a84c' : 'var(--danger)'};border:1px solid ${canAffordEra ? '#c9a84c' : 'var(--danger)'};border-radius:var(--radius);cursor:${canAffordEra ? 'pointer' : 'not-allowed'};opacity:${canAffordEra ? '1' : '0.6'};"
              data-can-afford="${canAffordEra}" title="${canAffordEra ? `Unlock ${nextEraLabel}` : 'Not enough gold'}">
              ${ERA_ROMAN[nextEraKey] || ''} · 💰${Math.round(nextEraPrice)}
            </button>`
        }
      </div>
    </div>
    <div class="critter-picker-grid">
      ${[..._availableCritters].reverse().map(c => {
        const isSelected = c.iid === currentIid;
        const isMuted = (c.era_index ?? 0) > maxEra;
        const u = _applyCritUpgrades(c);
        const upgLevels = st.summary?.item_upgrades?.[c.iid] ?? {};
        const totalUpgLvl = Object.values(upgLevels).reduce((a, b) => a + b, 0);
        return `
          <button class="critter-pick-tile${isSelected ? ' critter-pick-tile--selected' : ''}${isMuted ? ' critter-pick-tile--muted' : ''}"
              data-iid="${c.iid}" ${isMuted ? 'title="Era not unlocked for this wave"' : ''}>
            <div class="cpt-sprite" style="${isMuted ? 'opacity:0.35;filter:grayscale(1);' : ''}">
              <canvas class="critter-sprite-canvas" data-iid="${c.iid}" data-sprite="${c.sprite || ''}" data-animation="${c.animation || ''}" width="64" height="64"></canvas>
            </div>
            <div class="cpt-name" style="display:flex;align-items:baseline;gap:4px;overflow:hidden;${isMuted ? 'opacity:0.4;' : ''}">
              <span style="overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">${c.name}${c.is_boss ? ' 👑' : ''}</span>
              ${_critterEraRoman[c.iid.toUpperCase()] ? `<span class="era-roman-badge" style="font-size:9px;flex-shrink:0;">${_critterEraRoman[c.iid.toUpperCase()]}</span>` : ''}
              ${totalUpgLvl > 0 ? `<span style="font-size:9px;color:#c9a84c;flex-shrink:0;">⬆${totalUpgLvl}</span>` : ''}
            </div>
            <div class="cpt-stats" style="${isMuted ? 'opacity:0.4;' : ''}">
              <span class="cpt-stat cpt-hp" title="Health">❤ ${(u.health || 0).toFixed(1)}</span>
              ${u.armour ? `<span class="cpt-stat cpt-arm" title="Armour">🛡 ${u.armour.toFixed(2)}</span>` : ''}
              <span class="cpt-stat cpt-spd" title="Speed">⚡ ${(u.speed || 0).toFixed(2)}</span>
              ${c.slots > 1 ? `<span class="cpt-stat cpt-slots" title="Slot cost">${c.slots} Slots</span>` : ''}
              ${c.time_between_ms ? `<span class="cpt-stat cpt-interval" title="Time between spawns">⏱ ${(c.time_between_ms / 1000).toFixed(1)}s</span>` : ''}
            </div>
          </button>`;
      }).join('')}
    </div>
  `;

  _initCritterCanvases(body);

  // Slot upgrade button
  const slotUpgradeBtn = body.querySelector('#wave-slot-upgrade-btn');
  if (slotUpgradeBtn) {
    slotUpgradeBtn.addEventListener('click', async () => {
      if (slotUpgradeBtn.getAttribute('data-can-afford') !== 'true') return;
      slotUpgradeBtn.disabled = true;
      try {
        const resp = await rest.buyCritterSlot(aid, waveIdx);
        if (resp.success) {
          overlay.classList.remove('is-open');
          await rest.getSummary();
          await rest.getMilitary();
        } else {
          slotUpgradeBtn.textContent = `✗ ${resp.error || 'Failed'}`;
          setTimeout(() => { slotUpgradeBtn.disabled = false; }, 2000);
        }
      } catch {
        slotUpgradeBtn.disabled = false;
      }
    });
  }

  // Era upgrade button
  const eraUpgradeBtn = body.querySelector('#wave-era-upgrade-btn');
  if (eraUpgradeBtn) {
    eraUpgradeBtn.addEventListener('click', async () => {
      if (eraUpgradeBtn.getAttribute('data-can-afford') !== 'true') return;
      eraUpgradeBtn.disabled = true;
      try {
        const resp = await rest.buyWaveEra(aid, waveIdx);
        if (resp.success) {
          overlay.classList.remove('is-open');
          await rest.getSummary();
          await rest.getMilitary();
        } else {
          eraUpgradeBtn.textContent = `✗ ${resp.error || 'Failed'}`;
          setTimeout(() => { eraUpgradeBtn.disabled = false; }, 2000);
        }
      } catch {
        eraUpgradeBtn.disabled = false;
      }
    });
  }

  // Bind tile clicks (muted critters are not selectable)
  body.querySelectorAll('.critter-pick-tile').forEach(btn => {
    btn.addEventListener('click', async () => {
      if (btn.classList.contains('critter-pick-tile--muted')) return;
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
      showMessage(input, `✗ ${resp.error || 'Attack failed'}`, 'error', true);
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

  // Store available critters and sprite lookup for all critters (incl. locked)
  _availableCritters = data.available_critters || [];
  _critterSprites = data.critter_sprites || {};

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
            const spriteInfo = _critterSprites[w.iid] || {};
            const critterSlotCost = selectedCritter?.slots || 1;
            const numCritters = critterCountInWave(w.slots || 0, critterSlotCost);
            const hasSprite = w.iid && (spriteInfo.sprite || spriteInfo.animation);
            return `
            <div class="wave-tile" data-aid="${a.aid}" data-wave-idx="${i}">
              <button class="wave-critter-btn" data-aid="${a.aid}" data-wave-idx="${i}" data-current-iid="${w.iid || ''}" data-max-era="${w.max_era ?? 0}" data-next-era-price="${w.next_era_price ?? 0}" data-next-slot-price="${w.next_slot_price ?? 0}" data-slots="${w.slots || 0}">
                <span class="wave-tile__edit-hint">✎</span>
                ${hasSprite
                  ? `<canvas class="wave-tile__sprite critter-sprite-canvas" data-iid="${w.iid}" data-sprite="${spriteInfo.sprite || ''}" data-animation="${spriteInfo.animation || ''}" width="72" height="72"
                        style="image-rendering:pixelated;"></canvas>`
                  : `<div class="wave-tile__no-critter">＋</div>`
                }
                <div class="wave-tile__count">${hasSprite ? numCritters : ''}</div>
              </button>
              <div class="wave-tile__footer">
                <span class="wave-tile__slots">${w.slots || 0} Slots</span>
                <span class="wave-tile__era era-roman-badge" title="${ERA_LABEL_EN[ERA_KEYS[w.max_era ?? 0]] || ''}" style="font-size:0.75em;">${ERA_ROMAN[ERA_KEYS[w.max_era ?? 0]] || 'I'}</span>
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
      const maxEra = parseInt(btn.getAttribute('data-max-era') || '0', 10);
      const nextEraPrice = parseFloat(btn.getAttribute('data-next-era-price') || '0');
      const nextSlotPrice = parseFloat(btn.getAttribute('data-next-slot-price') || '0');
      const currentSlots = parseInt(btn.getAttribute('data-slots') || '0', 10);
      _openCritterOverlay(aid, waveIdx, currentIid, maxEra, nextEraPrice, nextSlotPrice, currentSlots);
    });
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
