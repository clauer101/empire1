/**
 * Army Composer view — create and edit armies with critter waves.
 */

import { eventBus } from '../events.js';
import { rest } from '../rest.js';
import { escHtml, hilite } from '../lib/html.js';
import { ERA_KEYS, ERA_YAML_TO_KEY, ERA_ROMAN, ERA_LABEL_EN } from '../lib/eras.js';
import { _buildEraStatsHTML } from './defense/era_data.js';

/** @type {import('../api.js').ApiClient} */
let api;
/** @type {import('../state.js').StateStore} */
let st;
/** @type {HTMLElement} */
let container;
let _unsub = [];
let _availableCritters = [];
let _critterSprites = {}; // iid → {sprite, animation} for all critters incl. locked
let _empiresCache = [];
/** iid.toUpperCase() → Roman numeral string (e.g. "III") */
let _critterEraRoman = {};
let _critUpgDef = null; // critter_upgrade_def from era-map
let _waveEraCosts = []; // wave_era_costs from era-map
let _critterSlotParams = null; // {u, y, z, v}
let _etaTicker = null; // interval for live ETA countdown

function _waveEraPrice(eraIndex) {
  if (!_waveEraCosts.length) return 0;
  if (eraIndex < _waveEraCosts.length) return _waveEraCosts[eraIndex];
  return _waveEraCosts[_waveEraCosts.length - 1];
}

function _slotPrice(slots) {
  const p = _critterSlotParams;
  if (!p) return 0;
  return p.u + slots * p.y * Math.pow(slots + p.z, p.v);
}

function _applyCritUpgrades(c) {
  const upgrades = st.summary?.item_upgrades?.[c.iid] ?? {};
  const d = _critUpgDef;
  if (!d) return c;
  const hpLvl = upgrades.health ?? 0;
  const spdLvl = upgrades.speed ?? 0;
  const armLvl = upgrades.armour ?? 0;
  return {
    ...c,
    health: c.health * (1 + (d.health / 100) * hpLvl),
    speed: c.speed * (1 + (d.speed / 100) * spdLvl),
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
    const roman = idx >= 0 ? ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX'][idx] : '';
    _critterEraRoman[iid.toUpperCase()] = roman;
  }
}

function _armyEffectRows(effectKey, completedBuildings, completedResearch, items, fmt) {
  const rows = [];
  for (const iid of completedBuildings || []) {
    const item = items?.buildings?.[iid];
    const val = item?.effects?.[effectKey];
    if (val)
      rows.push(
        `<div class="panel-row"><span class="label">${fmt(val)}</span><span class="value" style="color:#ccc">${item.name || iid}</span></div>`
      );
  }
  for (const iid of completedResearch || []) {
    const item = items?.knowledge?.[iid];
    const val = item?.effects?.[effectKey];
    if (val)
      rows.push(
        `<div class="panel-row"><span class="label">${fmt(val)}</span><span class="value" style="color:#ccc">${item.name || iid}</span></div>`
      );
  }
  if (!rows.length)
    return `<div style="color:#555;font-size:0.85em;padding:2px 0">No items contribute yet</div>`;
  return rows.join('');
}

function _showArmyEffectsOverlay() {
  document.querySelector('.army-effects-overlay')?.remove();
  const summary = st.summary || {};
  const effects = summary.effects || {};
  const completedBuildings = summary.completed_buildings || [];
  const completedResearch = summary.completed_research || [];
  const items = st.items || {};

  const eraBase = summary.era_travel_base_seconds ?? summary.travel_time_seconds ?? 0;
  const travelOffset = effects.travel_offset || 0;
  const travelTotal = summary.travel_time_seconds ?? (eraBase + travelOffset);

  function _fmtS(s) {
    return (s / 3600).toFixed(2).replace(/\.?0+$/, '') + 'h';
  }

  function section(icon, title, color, rows, footer) {
    const footerHtml = footer
      ? `<div class="panel-row" style="border-top:1px solid #444;margin-top:6px;padding-top:6px">
          <span class="label" style="color:#ddd;font-weight:bold">Total</span>
          <span class="value" style="color:#fff;font-weight:bold">${footer}</span>
        </div>`
      : '';
    return `
      <div class="prod-overlay-section">
        <div class="prod-overlay-title"><span style="color:${color}">${icon} ${title}</span></div>
        ${rows}
        ${footerHtml}
      </div>`;
  }

  // Travel time: base row + per-item offsets
  const travelBaseRow = `<div class="panel-row"><span class="label">${_fmtS(eraBase)}</span><span class="value" style="color:#ccc">Era base (${summary.current_era || '?'})</span></div>`;
  const travelOffsetRows = _armyEffectRows('travel_offset', completedBuildings, completedResearch, items, (v) => (v < 0 ? '' : '+') + _fmtS(v));
  const travelRows = travelBaseRow + (travelOffset !== 0 ? travelOffsetRows : '<div style="color:#555;font-size:0.85em;padding:2px 0">No items contribute yet</div>');

  // Artifact steal chances
  const baseVictory = summary.base_artifact_steal_victory ?? 0;
  const baseDefeat = summary.base_artifact_steal_defeat ?? 0;
  const stealVictoryMod = effects.artifact_steal_victory_modifier || 0;
  const stealDefeatMod = effects.artifact_steal_defeat_modifier || 0;
  const totalVictory = baseVictory + stealVictoryMod;
  const totalDefeat = baseDefeat + stealDefeatMod;

  function _fmtPct(v) { return (v * 100).toFixed(1) + '%'; }

  const stealVictoryBaseRow = `<div class="panel-row"><span class="label">${_fmtPct(baseVictory)}</span><span class="value" style="color:#ccc">Base chance</span></div>`;
  const stealVictoryModRows = _armyEffectRows('artifact_steal_victory_modifier', completedBuildings, completedResearch, items, (v) => (v >= 0 ? '+' : '') + _fmtPct(v));
  const stealVictoryRows = stealVictoryBaseRow + (stealVictoryMod !== 0 ? stealVictoryModRows : '<div style="color:#555;font-size:0.85em;padding:2px 0">No items contribute yet</div>');

  const stealDefeatBaseRow = `<div class="panel-row"><span class="label">${_fmtPct(baseDefeat)}</span><span class="value" style="color:#ccc">Base chance</span></div>`;
  const stealDefeatModRows = _armyEffectRows('artifact_steal_defeat_modifier', completedBuildings, completedResearch, items, (v) => (v >= 0 ? '+' : '') + _fmtPct(v));
  const stealDefeatRows = stealDefeatBaseRow + (stealDefeatMod !== 0 ? stealDefeatModRows : '<div style="color:#555;font-size:0.85em;padding:2px 0">No items contribute yet</div>');

  // Spy workshop
  const spyWorkshop = effects.spy_workshop || 0;
  const spyContent = `<div class="panel-row">
    <span class="label" style="color:#ccc">Workshop intel (upgrades) visible in spy reports</span>
    <span class="value" style="color:${spyWorkshop > 0 ? '#4fc3f7' : '#555'};font-weight:bold">${spyWorkshop > 0 ? 'Active' : 'No'}</span>
  </div>`;

  const overlay = document.createElement('div');
  overlay.className = 'prod-overlay army-effects-overlay';
  overlay.innerHTML = `
    <div class="prod-overlay-box">
      <button class="prod-overlay-close" title="Close">✕</button>
      <div style="font-weight:bold;font-size:1.05em;margin-bottom:12px">⚔ Army Effects</div>
      ${section('🕐', 'Travel Time', '#ffa726', travelRows, _fmtS(travelTotal))}
      ${section('🏆', 'Artifact Steal — Victory', '#c9a84c', stealVictoryRows, _fmtPct(totalVictory))}
      ${section('💀', 'Artifact Steal — Defeat', '#e57373', stealDefeatRows, _fmtPct(totalDefeat))}
      ${section('🕵', 'Spy Capabilities', '#4fc3f7', spyContent, '')}
    </div>`;

  overlay.addEventListener('click', (e) => {
    if (e.target === overlay || e.target.classList.contains('prod-overlay-close')) overlay.remove();
  });
  document.body.appendChild(overlay);
}

function init(el, _api, _state) {
  container = el;
  api = _api;
  st = _state;

  container.innerHTML = `
    <h2 class="battle-title">🗡 Army Composer<span class="title-resources"><span class="title-gold"></span><span class="title-culture"></span><span class="title-life"></span></span></h2>

    <div id="attack-target-banner" style="display:none;margin-bottom:12px;padding:8px 12px;background:rgba(229,57,53,0.15);border:1px solid var(--danger,#e53935);border-radius:var(--radius);color:var(--danger,#e53935);font-weight:bold;"></div>
    
    <!-- ── Create Army Button ──────────────────────────── -->
    <div style="margin-bottom:16px;">
      <button id="create-army-btn" style="display:flex;flex-direction:column;align-items:center;gap:2px;line-height:1.2;">
        <span>+ New Army</span>
        <span id="army-price-display" style="font-size:10px;opacity:0.7;"></span>
      </button>
    </div>

    <!-- ── New Army Name Overlay ─────────────────────────── -->
    <div id="new-army-overlay" style="display:none;position:fixed;inset:0;z-index:200;background:rgba(0,0,0,0.55);align-items:center;justify-content:center;">
      <div style="background:var(--panel-bg,#1e1e2e);border:1px solid var(--border-color);border-radius:var(--radius,8px);padding:14px 16px;min-width:240px;max-width:90vw;display:flex;flex-direction:column;gap:8px;position:relative;">
        <button id="new-army-close" style="position:absolute;top:6px;right:8px;background:none;border:none;cursor:pointer;color:#888;font-size:16px;line-height:1;">✕</button>
        <div style="font-weight:bold;padding-right:20px;">New Army</div>
        <input type="text" id="new-army-name" placeholder="Name" style="width:100%;box-sizing:border-box;" />
        <div id="new-army-msg" style="font-size:0.82em;min-height:14px;"></div>
        <button id="new-army-confirm" style="width:100%;">Buy</button>
      </div>
    </div>

    <!-- ── Spy Attack ─────────────────────────────────── -->
    <div id="spy-attack-panel" style="margin-bottom:18px;padding:10px 12px;background:rgba(100,60,180,0.12);border:1px solid rgba(150,100,220,0.35);border-radius:var(--radius,8px);">
      <div id="spy-panel-title" style="font-size:13px;font-weight:600;margin-bottom:8px;color:var(--text-dim);">🕵 Spy Attack <span style="font-size:11px;font-weight:400;">(disguises as first army, half travel time)</span></div>
      <div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap;">
        <div class="empire-ac-wrap" style="position:relative;flex:1;min-width:140px;">
          <input type="text" id="spy-target-input" class="target-uid-input" placeholder="Target empire" autocomplete="off" style="width:100%;box-sizing:border-box;padding-right:24px;" />
          <button id="spy-target-clear" title="Clear" style="position:absolute;right:4px;top:50%;transform:translateY(-50%);background:none;border:none;cursor:pointer;color:#888;font-size:18px;line-height:1;padding:0 2px;">✕</button>
          <div class="empire-ac-dropdown"></div>
        </div>
        <button id="spy-attack-btn" style="display:flex;flex-direction:column;align-items:center;gap:1px;line-height:1.2;white-space:nowrap;">
          <span>🕵 Send Spy</span>
          <span id="spy-eta-label" style="font-size:10px;opacity:0.7;"></span>
        </button>
      </div>
      <div id="spy-status-msg" style="font-size:12px;margin-top:6px;min-height:14px;"></div>
    </div>

    <!-- ── Spy Report Overlay ─────────────────────────── -->
    <div id="spy-report-overlay" style="display:none;position:fixed;inset:0;z-index:300;background:rgba(0,0,0,0.65);align-items:center;justify-content:center;">
      <div style="background:var(--panel-bg,#1e1e2e);border:1px solid rgba(150,100,220,0.5);border-radius:var(--radius,8px);padding:20px;min-width:280px;max-width:min(520px,92vw);max-height:80vh;overflow-y:auto;position:relative;">
        <button id="spy-report-close" style="position:absolute;top:8px;right:12px;background:none;border:none;cursor:pointer;color:#888;font-size:18px;line-height:1;">✕</button>
        <div id="spy-report-body"></div>
      </div>
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

  if (!document.getElementById('dashboard-grid-style')) {
    const s = document.createElement('style');
    s.id = 'dashboard-grid-style';
    s.textContent = `
      .prod-overlay{position:fixed;inset:0;background:rgba(0,0,0,.75);z-index:9999;display:flex;align-items:flex-start;justify-content:center;padding:24px 12px;overflow-y:auto}
      .prod-overlay-box{background:var(--panel-bg,#1e1e1e);border:1px solid var(--border-color,#444);border-radius:8px;width:100%;max-width:480px;padding:16px 18px;position:relative}
      .prod-overlay-close{position:absolute;top:10px;right:12px;background:none;border:none;color:#aaa;font-size:1.4em;cursor:pointer;line-height:1;padding:0}
      .prod-overlay-section{margin-bottom:14px}
      .prod-overlay-title{font-size:0.78em;font-weight:bold;text-transform:uppercase;letter-spacing:.05em;color:#888;margin-bottom:5px;padding-bottom:3px;border-bottom:1px solid var(--border-color,#444)}
      .prod-info-btn{background:none;border:none;color:#4fc3f7;font-size:0.95em;cursor:pointer;padding:0 0 0 5px;line-height:1;vertical-align:middle;opacity:.8}
      .prod-info-btn:hover{opacity:1}
    `;
    document.head.appendChild(s);
  }

  const _titleEl = container.querySelector('.battle-title');
  if (_titleEl) {
    const _resourceWrap = _titleEl.querySelector('.title-resources');
    _titleEl.textContent = '';
    const _labelSpan = document.createElement('span');
    _labelSpan.textContent = '🗡 Army Composer ';
    const _efxBtn = document.createElement('button');
    _efxBtn.id = 'army-effects-btn';
    _efxBtn.className = 'prod-info-btn';
    _efxBtn.title = 'Show army effects';
    _efxBtn.textContent = '🔍';
    _efxBtn.addEventListener('click', _showArmyEffectsOverlay);
    _labelSpan.appendChild(_efxBtn);
    _titleEl.appendChild(_labelSpan);
    if (_resourceWrap) _titleEl.appendChild(_resourceWrap);
  }

  const newArmyOverlay = container.querySelector('#new-army-overlay');
  container.querySelector('#create-army-btn').addEventListener('click', () => {
    container.querySelector('#new-army-name').value = '';
    container.querySelector('#new-army-msg').textContent = '';
    newArmyOverlay.style.display = 'flex';
    container.querySelector('#new-army-name').focus();
  });
  container.querySelector('#new-army-close').addEventListener('click', () => {
    newArmyOverlay.style.display = 'none';
  });
  container.querySelector('#new-army-confirm').addEventListener('click', onCreateArmy);
  container.querySelector('#new-army-name').addEventListener('keydown', (e) => {
    if (e.key === 'Enter') onCreateArmy();
    if (e.key === 'Escape') newArmyOverlay.style.display = 'none';
  });
  newArmyOverlay.addEventListener('click', (e) => {
    if (e.target === newArmyOverlay) newArmyOverlay.style.display = 'none';
  });

  // Bind spy attack panel
  const spyInput = container.querySelector('#spy-target-input');
  container.querySelector('#spy-target-clear').addEventListener('click', () => {
    spyInput.value = '';
  });
  _bindAutocomplete(spyInput);
  container.querySelector('#spy-attack-btn').addEventListener('click', onSpyAttack);

  // Bind spy report overlay close
  const spyOverlay = container.querySelector('#spy-report-overlay');
  container.querySelector('#spy-report-close').addEventListener('click', () => {
    spyOverlay.style.display = 'none';
  });
  spyOverlay.addEventListener('click', (e) => {
    if (e.target === spyOverlay) spyOverlay.style.display = 'none';
  });

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
  _unsub.push(eventBus.on('state:military', () => _startEtaTicker()));
  _unsub.push(eventBus.on('state:military', _updateSpyButton));
  _unsub.push(eventBus.on('state:summary', updateCreateArmyButton));
  _unsub.push(eventBus.on('server:spy_report', _onSpyReport));

  // Load once on entry
  _loadEmpires();
  try {
    await rest.getSummary();
    updateCreateArmyButton();
    const [, , eraMap] = await Promise.all([rest.getItems(), rest.getMilitary(), rest.getEraMap()]);
    if (eraMap) {
      _critUpgDef = eraMap.critter_upgrade_def ?? null;
      _waveEraCosts = eraMap.wave_era_costs ?? [];
      _critterSlotParams = eraMap.critter_slot_params ?? null;
    }
    _buildCritterEraRoman();
    _updateSpyEta();
  } catch (err) {
    console.error('Failed to load military data:', err);
  }

  // Pre-fill target inputs if navigated here from the empire list
  if (st.pendingAttackTarget) {
    const { uid, name } = st.pendingAttackTarget;
    st.pendingAttackTarget = null;
    // Fill all target-uid inputs with the empire name and scroll to first one
    const inputs = container.querySelectorAll('.target-uid-input');
    inputs.forEach((inp) => {
      inp.value = name || uid;
    });
    if (inputs.length > 0) {
      inputs[0].scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
    const banner = container.querySelector('#attack-target-banner');
    if (banner) banner.style.display = 'none';
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

function _startEtaTicker() {
  if (_etaTicker) return;
  _etaTicker = setInterval(() => {
    container.querySelectorAll('.eta-live[data-eta-ts]').forEach((el) => {
      const ts = Number(el.dataset.etaTs);
      const remaining = (ts - Date.now()) / 1000;
      const prefix = el.dataset.etaPrefix || 'ETA';
      el.textContent = remaining > 0 ? `${prefix}: ${fmtTravelTime(remaining)}` : 'Arriving…';
    });
  }, 1000);
}

function leave() {
  _unsub.forEach((fn) => fn());
  _unsub = [];
  if (_etaTicker) {
    clearInterval(_etaTicker);
    _etaTicker = null;
  }
}

function updateCreateArmyButton() {
  const armyPrice = st.summary?.army_price || 0;
  const currentGold = st.summary?.resources?.gold || 0;
  const canAfford = currentGold >= armyPrice;
  const btn = container.querySelector('#create-army-btn');
  const priceDisplay = container.querySelector('#army-price-display');
  if (!btn) return;
  priceDisplay.textContent = `💰 ${Math.round(armyPrice)} Gold`;
  priceDisplay.style.color = canAfford ? '' : 'var(--danger)';
  btn.style.opacity = canAfford ? '1' : '0.5';
  btn.title = canAfford
    ? `Armee kaufen (${Math.round(armyPrice)} Gold)`
    : `Nicht genug Gold (${Math.round(armyPrice)} benötigt)`;
}

async function onCreateArmy() {
  const armyPrice = st.summary?.army_price || 0;
  const currentGold = st.summary?.resources?.gold || 0;
  const nameInput = container.querySelector('#new-army-name');
  const msgEl = container.querySelector('#new-army-msg');
  const name = nameInput.value.trim();

  if (!name) {
    msgEl.textContent = 'Please enter a name';
    msgEl.style.color = 'var(--danger)';
    return;
  }
  if (currentGold < armyPrice) {
    msgEl.textContent = `Not enough gold (${Math.round(armyPrice)} needed)`;
    msgEl.style.color = 'var(--danger)';
    return;
  }

  const confirmBtn = container.querySelector('#new-army-confirm');
  confirmBtn.disabled = true;
  try {
    const resp = await rest.createArmy(name);
    if (resp.success) {
      container.querySelector('#new-army-overlay').style.display = 'none';
      await rest.getSummary();
      await rest.getMilitary();
    } else {
      msgEl.textContent = `✗ ${resp.error || 'Failed'}`;
      msgEl.style.color = 'var(--danger)';
    }
  } catch (err) {
    console.error('Failed to create army:', err);
    msgEl.textContent = '✗ Network error';
    msgEl.style.color = 'var(--danger)';
  } finally {
    confirmBtn.disabled = false;
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
    showMessage(
      waveTile,
      `Not enough gold (need ${price}, have ${Math.round(currentGold)})`,
      'error'
    );
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

const _SPRITE_EXTS = ['.webp'];

/**
 * Initialize canvas elements with class .critter-sprite-canvas.
 * Uses data-sprite (exact resolved path) when available.
 * Falls back to data-animation folder or data-iid with extension probing.
 * Extracts the first frame (top-left) from a 4×4 sprite sheet,
 * preserving the original aspect ratio (letterboxed into the canvas).
 */
function _initCritterCanvases(el) {
  el.querySelectorAll('.critter-sprite-canvas').forEach((canvas) => {
    const drawFrame = (img) => {
      const ctx = canvas.getContext('2d');
      const fw = img.width / 4;
      const fh = img.height / 4;
      const scale = Math.min(canvas.width / fw, canvas.height / fh);
      const dx = Math.floor((canvas.width - fw * scale) / 2);
      const dy = Math.floor((canvas.height - fh * scale) / 2);
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.drawImage(img, 0, 0, fw, fh, dx, dy, fw * scale, fh * scale);
    };

    // If we have an exact resolved path, use it directly
    const sprite = canvas.dataset.sprite;
    if (sprite) {
      const img = new Image();
      img.onload = () => drawFrame(img);
      img.onerror = () => {
        canvas.style.display = 'none';
      };
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
      if (idx >= _SPRITE_EXTS.length) {
        canvas.style.display = 'none';
        return;
      }
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
function _openCritterOverlay(
  aid,
  waveIdx,
  currentIid,
  maxEra = 0,
  nextEraPrice = 0,
  nextSlotPrice = 0,
  currentSlots = 0
) {
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
        ${
          isMaxEra
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
      ${[..._availableCritters]
        .reverse()
        .map((c) => {
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
        })
        .join('')}
    </div>
  `;

  _initCritterCanvases(body);

  // Slot upgrade button
  const slotUpgradeBtn = body.querySelector('#wave-slot-upgrade-btn');
  if (slotUpgradeBtn) {
    slotUpgradeBtn.addEventListener('click', async () => {
      if (slotUpgradeBtn.getAttribute('data-can-afford') !== 'true') return;
      const newSlots = currentSlots + 1;
      const newNextSlotPrice = _slotPrice(newSlots + 1);
      _openCritterOverlay(
        aid,
        waveIdx,
        currentIid,
        maxEra,
        nextEraPrice,
        newNextSlotPrice,
        newSlots
      );
      rest.buyCritterSlot(aid, waveIdx).then((resp) => {
        if (!resp.success) {
          _openCritterOverlay(
            aid,
            waveIdx,
            currentIid,
            maxEra,
            nextEraPrice,
            nextSlotPrice,
            currentSlots
          );
        } else {
          Promise.all([rest.getSummary(), rest.getMilitary()]);
        }
      });
    });
  }

  // Era upgrade button
  const eraUpgradeBtn = body.querySelector('#wave-era-upgrade-btn');
  if (eraUpgradeBtn) {
    eraUpgradeBtn.addEventListener('click', async () => {
      if (eraUpgradeBtn.getAttribute('data-can-afford') !== 'true') return;
      const newMaxEra = maxEra + 1;
      const newNextEraPrice = _waveEraPrice(newMaxEra + 1);
      _openCritterOverlay(
        aid,
        waveIdx,
        currentIid,
        newMaxEra,
        newNextEraPrice,
        nextSlotPrice,
        currentSlots
      );
      rest.buyWaveEra(aid, waveIdx).then((resp) => {
        if (!resp.success) {
          _openCritterOverlay(
            aid,
            waveIdx,
            currentIid,
            maxEra,
            nextEraPrice,
            nextSlotPrice,
            currentSlots
          );
        } else {
          Promise.all([rest.getSummary(), rest.getMilitary()]);
        }
      });
    });
  }

  // Bind tile clicks (muted critters are not selectable)
  body.querySelectorAll('.critter-pick-tile').forEach((btn) => {
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
    showMessage(
      btn.closest('.wave-tile'),
      `Not enough gold (need ${price}, have ${Math.round(currentGold)})`,
      'error'
    );
    return;
  }

  const aid = parseInt(btn.getAttribute('data-aid'), 10);
  const waveIdx = parseInt(btn.getAttribute('data-wave-idx'), 10);

  try {
    const resp = await rest.buyCritterSlot(aid, waveIdx);
    if (resp.success) {
      showMessage(
        btn.closest('.wave-tile'),
        `✓ Critter added! Cost: ${Math.round(resp.cost)} gold`,
        'success'
      );
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

function _setAttackBtnState(btn, state, label2 = '') {
  btn.disabled = state !== 'ready';
  btn.style.opacity = state === 'ready' ? '' : '0.5';
  btn.style.cursor = state === 'ready' ? '' : 'default';
  if (state === 'ready') {
    btn.innerHTML = `<span>⚔ Attack</span>`;
  } else {
    const color = state === 'error' ? 'var(--danger)' : 'inherit';
    btn.innerHTML = `<span style="color:${color}">${state === 'error' ? '✗' : '⚔'} ${label2 || ''}</span>`;
  }
}

function _updateSpyButton() {
  const btn = container.querySelector('#spy-attack-btn');
  const statusEl = container.querySelector('#spy-status-msg');
  const titleEl = container.querySelector('#spy-panel-title');
  if (!btn) return;

  const armies = st.military?.armies || [];
  const firstArmy = armies.length ? armies.reduce((a, b) => (a.aid < b.aid ? a : b)) : null;
  if (titleEl && firstArmy) {
    titleEl.innerHTML = `🕵 Spy Attack <span style="font-size:11px;font-weight:400;">(disguises as "${escHtml(firstArmy.name)}", half travel time)</span>`;
  }

  const activeSpies = (st.military?.attacks_outgoing || []).filter((a) => a.is_spy);
  if (activeSpies.length > 0) {
    const eta = fmtTravelTime(activeSpies[0].eta_seconds);
    btn.disabled = true;
    btn.style.opacity = '0.5';
    btn.style.cursor = 'default';
    btn.innerHTML = `<span>🕵 Dispatched</span><span style="font-size:10px;opacity:0.7;">ETA: ${eta}</span>`;
    if (statusEl) statusEl.textContent = '';
  } else {
    btn.disabled = false;
    btn.style.opacity = '';
    btn.style.cursor = '';
    btn.innerHTML = `<span>🕵 Send Spy</span><span id="spy-eta-label" style="font-size:10px;opacity:0.7;"></span>`;
    _updateSpyEta();
  }
}

function _updateSpyEta() {
  const travelTime = st.summary?.travel_time_seconds;
  const etaEl = container.querySelector('#spy-eta-label');
  if (etaEl && travelTime) {
    const spyTime = Math.round(travelTime / 2);
    etaEl.textContent = `✈ ${fmtTravelTime(spyTime)}`;
  }
}

async function onSpyAttack() {
  const spyInput = container.querySelector('#spy-target-input');
  const spyBtn = container.querySelector('#spy-attack-btn');
  const statusEl = container.querySelector('#spy-status-msg');
  const etaLabel = container.querySelector('#spy-eta-label');
  const query = spyInput.value.trim();

  statusEl.textContent = '';
  if (!query) {
    statusEl.style.color = 'var(--danger, #e53935)';
    statusEl.textContent = 'Please enter a target empire.';
    return;
  }

  spyBtn.disabled = true;
  statusEl.style.color = 'var(--text-dim)';
  statusEl.textContent = 'Resolving target…';

  let targetUid;
  try {
    ({ uid: targetUid } = await rest.resolveEmpire(query));
  } catch (err) {
    spyBtn.disabled = false;
    statusEl.style.color = 'var(--danger, #e53935)';
    statusEl.textContent = err.message.slice(0, 60);
    return;
  }

  statusEl.textContent = 'Dispatching spy…';
  try {
    const resp = await rest.spyAttack(targetUid);
    if (resp.success) {
      const eta = fmtTravelTime(Math.round(resp.eta_seconds));
      etaLabel.textContent = eta ? `ETA: ${eta}` : '';
      spyBtn.innerHTML = `<span>🕵 Dispatched</span><span style="font-size:10px;opacity:0.7;">ETA: ${eta}</span>`;
      statusEl.style.color = 'var(--success, #388e3c)';
      statusEl.textContent = `Spy on the way — report arrives in ${eta}.`;
      setTimeout(() => {
        spyBtn.innerHTML = `<span>🕵 Send Spy</span><span id="spy-eta-label" style="font-size:10px;opacity:0.7;"></span>`;
        spyBtn.disabled = false;
        statusEl.textContent = '';
      }, 5000);
    } else {
      spyBtn.disabled = false;
      statusEl.style.color = 'var(--danger, #e53935)';
      statusEl.textContent = (resp.error || 'Error').slice(0, 60);
    }
  } catch (err) {
    spyBtn.disabled = false;
    statusEl.style.color = 'var(--danger, #e53935)';
    statusEl.textContent = 'Network error.';
  }
}

function _onSpyReport(msg) {
  const overlay = container.querySelector('#spy-report-overlay');
  const body = container.querySelector('#spy-report-body');
  if (!overlay || !body) return;

  const era = msg.era || '?';
  const defName = msg.defender_name || `Player ${msg.defender_uid}`;

  const structHtml = (msg.structures || [])
    .map((s) => {
      const upg = Object.entries(s.upgrades || {})
        .filter(([, v]) => v > 0)
        .map(([k, v]) => {
          const abbr = {
            damage: 'dmg',
            range: 'rng',
            reload: 'rld',
            effect_duration: 'eff_dur',
            effect_value: 'eff_val',
          };
          return `<span style="background:rgba(255,255,255,0.08);border-radius:3px;padding:1px 4px;font-size:11px;">${abbr[k] || k}+${v}</span>`;
        })
        .join(' ');
      return `<div style="display:flex;justify-content:space-between;align-items:center;padding:3px 0;border-bottom:1px solid rgba(255,255,255,0.06);">
      <span>🗼 ${escHtml(s.name)}</span>
      <span>${upg || '<span style="opacity:0.4;font-size:11px;">no upgrades</span>'}</span>
    </div>`;
    })
    .join('');

  const critterHtml = (msg.critters || [])
    .map((c) => {
      const upg = Object.entries(c.upgrades || {})
        .filter(([, v]) => v > 0)
        .map(([k, v]) => {
          const abbr = { health: 'hp', speed: 'spd', armour: 'arm' };
          return `<span style="background:rgba(255,255,255,0.08);border-radius:3px;padding:1px 4px;font-size:11px;">${abbr[k] || k}+${v}</span>`;
        })
        .join(' ');
      return `<div style="display:flex;justify-content:space-between;align-items:center;padding:3px 0;border-bottom:1px solid rgba(255,255,255,0.06);">
      <span>⚔ ${escHtml(c.name)}</span>
      <span>${upg || '<span style="opacity:0.4;font-size:11px;">no upgrades</span>'}</span>
    </div>`;
    })
    .join('');

  const eraDistHTML = _buildEraStatsHTML(msg.placed_towers || []);

  const pathLenHtml = msg.path_length != null
    ? `<span style="background:rgba(255,255,255,0.08);border-radius:3px;padding:1px 6px;font-size:12px;font-family:monospace;">${msg.path_length} tiles</span>`
    : '<span style="opacity:0.4;font-size:12px;">unknown</span>';
  const towerCountHtml = `<span style="background:rgba(255,255,255,0.08);border-radius:3px;padding:1px 6px;font-size:12px;font-family:monospace;">${(msg.placed_towers || []).length}</span>`;

  body.innerHTML = `
    <h3 style="margin:0 0 4px;font-size:15px;">🕵 Spy Report</h3>
    <div style="font-size:12px;color:var(--text-dim);margin-bottom:10px;">${escHtml(defName)}</div>

    <div style="font-size:13px;font-weight:600;margin-bottom:6px;color:var(--accent,#4fc3f7);">🛡 Defense Intelligence</div>
    <div style="border-top:1px solid rgba(255,255,255,0.1);padding-top:8px;margin-bottom:6px;">
      <div style="font-size:12px;margin-bottom:3px;">🛤 Path length: ${pathLenHtml}</div>
      <div style="font-size:12px;margin-bottom:8px;">🏰 Towers placed: ${towerCountHtml}</div>
      ${eraDistHTML}
    </div>

    <div style="font-size:13px;font-weight:600;margin-bottom:6px;margin-top:10px;color:var(--accent,#4fc3f7);">🔬 Workshop Intelligence &mdash; ${escHtml(era)}</div>
    <div style="border-top:1px solid rgba(255,255,255,0.1);padding-top:8px;">
      <div style="font-size:12px;color:var(--text-dim);margin-bottom:4px;">Towers</div>
      <div style="margin-bottom:10px;">${structHtml || '<div style="opacity:0.4;font-size:12px;">none</div>'}</div>
      <div style="font-size:12px;color:var(--text-dim);margin-bottom:4px;">Units</div>
      <div>${critterHtml || '<div style="opacity:0.4;font-size:12px;">none</div>'}</div>
    </div>
  `;

  overlay.style.display = 'flex';
}

async function onAttackOpponent(e) {
  const btn = e.currentTarget;
  const aid = parseInt(btn.getAttribute('data-aid'), 10);

  const inputId = `target-uid-${aid}`;
  const input = container.querySelector(`#${inputId}`);
  const query = input.value.trim();

  if (!query) {
    _setAttackBtnState(btn, 'error', 'Ziel eingeben');
    setTimeout(() => _setAttackBtnState(btn, 'ready'), 2000);
    return;
  }

  _setAttackBtnState(btn, 'loading', 'Wird gesucht…');
  let targetUid, targetName;
  try {
    ({ uid: targetUid, name: targetName } = await rest.resolveEmpire(query));
  } catch (err) {
    _setAttackBtnState(btn, 'error', err.message.slice(0, 20));
    setTimeout(() => _setAttackBtnState(btn, 'ready'), 2500);
    return;
  }

  _setAttackBtnState(btn, 'loading', 'Startet…');
  try {
    const resp = await rest.attackOpponent(targetUid, aid);
    if (resp.success) {
      const eta = fmtTravelTime(Math.round(resp.eta_seconds));
      btn.innerHTML = `<span>⚔ Attacking</span><span style="font-size:10px;opacity:0.7;">ETA: ${eta}</span>`;
      btn.disabled = true;
      btn.style.opacity = '0.5';
      btn.style.cursor = 'default';
      await rest.getMilitary();
    } else {
      _setAttackBtnState(btn, 'error', (resp.error || 'Fehler').slice(0, 22));
      setTimeout(() => _setAttackBtnState(btn, 'ready'), 3000);
    }
  } catch (err) {
    console.error('Failed to launch attack:', err);
    _setAttackBtnState(btn, 'error', 'Netzwerkfehler');
    setTimeout(() => _setAttackBtnState(btn, 'ready'), 2500);
  }
}

function fmtTravelTime(seconds) {
  if (!seconds || seconds <= 0) return '';
  const s = Math.round(seconds);
  if (s < 60) return `${s}s`;
  const m = Math.floor(s / 60),
    r = s % 60;
  if (m < 60) return r ? `${m}m ${r}s` : `${m}m`;
  const h = Math.floor(m / 60),
    rm = m % 60;
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
  if (!critterSlots || critterSlots < 1) return Math.max(1, waveSlots);
  return Math.max(1, Math.floor(waveSlots / critterSlots));
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
  const dropdown = input.closest('.empire-ac-wrap')?.querySelector('.empire-ac-dropdown');
  if (!dropdown) return;

  let _activeIdx = -1;
  let _filtered = [];

  function _render(items, q) {
    _filtered = items;
    _activeIdx = -1;
    if (!items.length) {
      dropdown.style.display = 'none';
      return;
    }
    const shown = items.slice(0, 12);
    dropdown.innerHTML = shown
      .map(
        (e, i) =>
          `<div class="empire-ac-item" data-idx="${i}">
        <span class="eac-label">${_hilite(e.name, q)} <span class="eac-meta">${e.username ? '(@' + _hilite(e.username, q) + ', ' : '('}uid:${_hilite(String(e.uid), q)})${e.is_self ? ' <em>(you)</em>' : ''}</span></span>
      </div>`
      )
      .join('');
    dropdown.style.display = 'block';
    dropdown.querySelectorAll('.empire-ac-item').forEach((el) => {
      el.addEventListener('mousedown', (ev) => {
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
    if (!q) {
      dropdown.style.display = 'none';
      return;
    }
    const matches = _empiresCache.filter(
      (e) =>
        e.name.toLowerCase().includes(q) ||
        (e.username || '').toLowerCase().includes(q) ||
        String(e.uid).includes(q)
    );
    _render(matches, q);
  }

  input.addEventListener('input', _search);
  input.addEventListener('focus', () => {
    if (input.value.trim()) _search();
  });
  input.addEventListener('blur', () => {
    setTimeout(() => {
      dropdown.style.display = 'none';
    }, 150);
  });
  input.addEventListener('keydown', (e) => {
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
    el.innerHTML =
      '<div class="empty-state"><div class="empty-icon">⚔</div><p>No data available</p></div>';
    return;
  }

  // Preserve scroll position and target-uid input values before re-render
  const scrollY = window.scrollY;

  const savedTargets = {};
  el.querySelectorAll('.target-uid-input').forEach((inp) => {
    if (inp.value) savedTargets[inp.dataset.aid] = inp.value;
  });

  // Store available critters and sprite lookup for all critters (incl. locked)
  _availableCritters = data.available_critters || [];
  _critterSprites = data.critter_sprites || {};

  const armies = data.armies || [];
  if (armies.length === 0) {
    el.innerHTML =
      '<div class="empty-state"><div class="empty-icon">⚔</div><p>No armies yet. Create one above to get started.</p></div>';
    return;
  }

  const currentGold = st.summary?.resources?.gold || 0;

  const travelTime = st.summary?.travel_time_seconds;
  const travelLabel = travelTime ? fmtTravelTime(travelTime) : '';

  el.classList.add('armies-container');
  el.innerHTML = armies
    .map((a, idx) => {
      const realAtk = (st.military?.attacks_outgoing || []).find(
        (atk) => !atk.is_spy && atk.army_aid === a.aid
      );
      const spyAtk = (st.military?.attacks_outgoing || []).find(
        (atk) => atk.is_spy && atk.army_name === a.name
      );
      const btnDisabled = !!realAtk;
      let btnContent;
      const _atkPhaseLabel = (atk) => {
        if (atk.phase === 'in_siege') return '🏰 In Siege';
        if (atk.phase === 'in_battle') return '⚔ In Battle';
        return '⚔ Attacking';
      };
      const _atkEtaSpan = (atk) => {
        if (atk.phase === 'in_siege') {
          const endTs = Date.now() + atk.siege_remaining_seconds * 1000;
          return `<span class="eta-live" data-eta-ts="${endTs}" data-eta-prefix="Siege" style="font-size:10px;opacity:0.7;">Siege: ${fmtTravelTime(atk.siege_remaining_seconds)}</span>`;
        }
        if (atk.phase === 'travelling' || atk.phase === 'traveling') {
          const endTs = Date.now() + atk.eta_seconds * 1000;
          return `<span class="eta-live" data-eta-ts="${endTs}" data-eta-prefix="ETA" style="font-size:10px;opacity:0.7;">ETA: ${fmtTravelTime(atk.eta_seconds)}</span>`;
        }
        return '';
      };
      const _targetName = (atk) => {
        const emp = _empiresCache.find((e) => e.uid === atk.defender_uid);
        return emp ? emp.name : `#${atk.defender_uid}`;
      };
      const _targetSpan = (atk) =>
        `<span style="font-size:10px;opacity:0.7;">→ ${escHtml(_targetName(atk))}</span>`;
      if (spyAtk && realAtk) {
        btnContent = `<span>${_atkPhaseLabel(realAtk)} · 🕵 "${a.name}"</span>${_targetSpan(realAtk)}${_atkEtaSpan(realAtk)}`;
      } else if (spyAtk) {
        btnContent = `<span>🕵 "${a.name}"</span>${_targetSpan(spyAtk)}${_atkEtaSpan(spyAtk)}`;
      } else if (realAtk) {
        btnContent = `<span>${_atkPhaseLabel(realAtk)}</span>${_targetSpan(realAtk)}${_atkEtaSpan(realAtk)}`;
      } else {
        btnContent = `<span>⚔ Attack</span>${travelLabel ? `<span style="font-size:10px;opacity:0.7;">✈ ${travelLabel}</span>` : ''}`;
      }
      return `
    <div class="army-group" data-aid="${a.aid}">
      <div class="army-name-header">
        <div class="army-name">${a.name} <span class="army-id"></span></div>(ID: ${a.aid})
        <button class="army-edit-btn" title="Edit army name" data-aid="${a.aid}">
          <span class="edit-icon">✎</span>
        </button>
      </div>
      <div class="army-attack-row">
        <div class="empire-ac-wrap" style="position:relative;">
          <input type="text" id="target-uid-${a.aid}" class="target-uid-input" placeholder="Ziel-Empire (Name oder ID)" data-aid="${a.aid}" autocomplete="off" style="padding-right:24px;" />
          <button class="target-uid-clear" data-aid="${a.aid}" title="Löschen" style="position:absolute;right:4px;top:50%;transform:translateY(-50%);background:none;border:none;cursor:pointer;color:#888;font-size:18px;line-height:1;padding:0 2px;">✕</button>
          <div class="empire-ac-dropdown"></div>
        </div>
        <button class="army-attack-btn" data-aid="${a.aid}" title="Launch attack"
          style="display:flex;flex-direction:column;align-items:center;gap:1px;line-height:1.2;${btnDisabled ? 'opacity:0.5;cursor:default;' : ''}"
          ${btnDisabled ? 'disabled' : ''}>
          ${btnContent}
        </button>
      </div>
      <div class="waves-container">
        ${
          (a.waves || []).length > 0
            ? `
          ${(a.waves || [])
            .map((w, i) => {
              const nextSlotPrice = w.next_slot_price || 0;
              const canAffordSlot = currentGold >= nextSlotPrice;
              const selectedCritter = _availableCritters.find((c) => c.iid === w.iid);
              const spriteInfo = _critterSprites[w.iid] || {};
              const critterSlotCost = selectedCritter?.slots || 1;
              const numCritters = critterCountInWave(w.slots || 0, critterSlotCost);
              const hasSprite = w.iid && (spriteInfo.sprite || spriteInfo.animation);
              return `
            <div class="wave-tile" data-aid="${a.aid}" data-wave-idx="${i}">
              <button class="wave-critter-btn" data-aid="${a.aid}" data-wave-idx="${i}" data-current-iid="${w.iid || ''}" data-max-era="${w.max_era ?? 0}" data-next-era-price="${w.next_era_price ?? 0}" data-next-slot-price="${w.next_slot_price ?? 0}" data-slots="${w.slots || 0}">
                <span class="wave-tile__edit-hint">✎</span>
                ${
                  hasSprite
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
          `;
            })
            .join('')}
        `
            : ''
        }
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
  `;
    })
    .join('');

  // Attach edit button listeners
  el.querySelectorAll('.army-edit-btn').forEach((btn) => {
    btn.addEventListener('click', (e) => onEditArmyName(e));
  });

  // Attach wave-add button listeners
  el.querySelectorAll('.wave-tile-add').forEach((btn) => {
    btn.addEventListener('click', (e) => onAddWave(e));
  });

  // Attach critter picker button listeners
  el.querySelectorAll('.wave-critter-btn').forEach((btn) => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      const aid = parseInt(btn.getAttribute('data-aid'), 10);
      const waveIdx = parseInt(btn.getAttribute('data-wave-idx'), 10);
      const currentIid = btn.getAttribute('data-current-iid') || '';
      const maxEra = parseInt(btn.getAttribute('data-max-era') || '0', 10);
      const nextEraPrice = parseFloat(btn.getAttribute('data-next-era-price') || '0');
      const nextSlotPrice = parseFloat(btn.getAttribute('data-next-slot-price') || '0');
      const currentSlots = parseInt(btn.getAttribute('data-slots') || '0', 10);
      _openCritterOverlay(
        aid,
        waveIdx,
        currentIid,
        maxEra,
        nextEraPrice,
        nextSlotPrice,
        currentSlots
      );
    });
  });

  // Attach attack button listeners
  el.querySelectorAll('.army-attack-btn').forEach((btn) => {
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

  // Bind clear buttons
  el.querySelectorAll('.target-uid-clear').forEach((btn) => {
    btn.addEventListener('click', () => {
      const aid = btn.getAttribute('data-aid');
      const inp = el.querySelector(`#target-uid-${aid}`);
      if (inp) inp.value = '';
    });
  });

  // Restore scroll position after re-render
  requestAnimationFrame(() => window.scrollTo(0, scrollY));

  _updateSpyButton();
}

export default {
  id: 'army',
  title: 'Army Composer',
  init,
  enter,
  leave,
};
