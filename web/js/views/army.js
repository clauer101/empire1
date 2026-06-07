/**
 * Army Composer view — create and edit armies with critter waves.
 */

import { eventBus } from '../events.js';
import { pageTitle } from '../lib/page_title.js';
import { rest } from '../rest.js';
import { escHtml, hilite } from '../lib/html.js';
import { ERA_KEYS, ERA_YAML_TO_KEY, ERA_ROMAN, ERA_LABEL_EN } from '../lib/eras.js';
import { _buildEraStatsHTML } from './defense/era_data.js';
import { isGameFrozen } from '../lib/game_state.js';

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
let _resetScroll = false; // set when navigating here from external context (e.g. attack button)

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

async function _showArmyEffectsOverlay() {
  document.querySelector('.army-effects-overlay')?.remove();
  const summary = st.summary || {};
  const effects = summary.effects || {};

  const overlay = document.createElement('div');
  overlay.className = 'prod-overlay army-effects-overlay';
  overlay.innerHTML = `<div class="prod-overlay-box"><button class="prod-overlay-close" title="Close">✕</button><div style="color:#888;padding:20px">Loading…</div></div>`;
  overlay.addEventListener('click', (e) => {
    if (e.target === overlay || e.target.classList.contains('prod-overlay-close')) overlay.remove();
  });
  document.body.appendChild(overlay);

  let effectSources = {};
  try { effectSources = await rest.getEffectSources(); } catch (_) {}

  const eraBase = summary.era_travel_base_seconds ?? summary.travel_time_seconds ?? 0;
  const travelOffset = effects.travel_offset || 0;
  const travelTotal = summary.travel_time_seconds ?? (eraBase + travelOffset);

  function _fmtS(s) { return (s / 3600).toFixed(2).replace(/\.?0+$/, '') + 'h'; }
  function _fmtPct(v) { return (v * 100).toFixed(1) + '%'; }

  function section(icon, title, color, rows, footer) {
    const footerHtml = footer
      ? `<div class="panel-row" style="border-top:1px solid #444;margin-top:6px;padding-top:6px"><span class="label" style="color:#ddd;font-weight:bold">Total</span><span class="value" style="color:#fff;font-weight:bold">${footer}</span></div>`
      : '';
    return `<div class="prod-overlay-section"><div class="prod-overlay-title"><span style="color:${color}">${icon} ${title}</span></div>${rows}${footerHtml}</div>`;
  }

  const _items = st.items;
  function _name(iid) {
    return _items?.buildings?.[iid]?.name || _items?.knowledge?.[iid]?.name || _items?.catalog?.[iid]?.name || iid;
  }
  function sourceRows(key, fmt, rulerName) {
    const src = effectSources[key] || {};
    let html = '';
    for (const [iid, v] of Object.entries(src.buildings || {}))
      if (v) html += `<div class="panel-row"><span class="label">${fmt(v)}</span><span class="value">${_name(iid)}</span></div>`;
    for (const [iid, v] of Object.entries(src.knowledge || {}))
      if (v) html += `<div class="panel-row"><span class="label">${fmt(v)}</span><span class="value">${_name(iid)}</span></div>`;
    for (const [iid, v] of Object.entries(src.artifacts || {}))
      if (v) html += `<div class="panel-row"><span class="label">${fmt(v)}</span><span class="value" style="color:#FFD700">⚜ ${_name(iid)}</span></div>`;
    if (src.ruler && rulerName)
      html += `<div class="panel-row"><span class="label">${fmt(src.ruler)}</span><span class="value" style="color:#FFD700">👑 ${rulerName}</span></div>`;
    if (src.end_rally)
      html += `<div class="panel-row"><span class="label">${fmt(src.end_rally)}</span><span class="value" style="color:#87CEEB">⚔ End Rally</span></div>`;
    if (src.era)
      html += `<div class="panel-row"><span class="label">${fmt(src.era)}</span><span class="value" style="color:#87CEEB">Era</span></div>`;
    return html || `<div style="color:#555;font-size:0.85em;padding:2px 0">No items contribute yet</div>`;
  }

  const rulerName = summary.ruler?.name || '';
  const baseVictory = summary.base_artifact_steal_victory ?? 0;
  const baseDefeat = summary.base_artifact_steal_defeat ?? 0;
  const stealVictoryMod = effects.artifact_steal_victory_modifier || 0;
  const stealDefeatMod = effects.artifact_steal_defeat_modifier || 0;

  const travelRows = `<div class="panel-row"><span class="label">${_fmtS(eraBase)}</span><span class="value" style="color:#ccc">Era base (${summary.current_era || '?'})</span></div>`
    + (travelOffset !== 0 ? sourceRows('travel_offset', (v) => (v < 0 ? '' : '+') + _fmtS(v), rulerName) : '<div style="color:#555;font-size:0.85em;padding:2px 0">No items contribute yet</div>');

  const stealVictoryRows = `<div class="panel-row"><span class="label">${_fmtPct(baseVictory)}</span><span class="value" style="color:#ccc">Base chance</span></div>`
    + (stealVictoryMod !== 0 ? sourceRows('artifact_steal_victory_modifier', (v) => (v >= 0 ? '+' : '') + _fmtPct(v), rulerName) : '<div style="color:#555;font-size:0.85em;padding:2px 0">No items contribute yet</div>');

  const stealDefeatRows = `<div class="panel-row"><span class="label">${_fmtPct(baseDefeat)}</span><span class="value" style="color:#ccc">Base chance</span></div>`
    + (stealDefeatMod !== 0 ? sourceRows('artifact_steal_defeat_modifier', (v) => (v >= 0 ? '+' : '') + _fmtPct(v), rulerName) : '<div style="color:#555;font-size:0.85em;padding:2px 0">No items contribute yet</div>');

  const spyWorkshop = effects.spy_workshop || 0;
  const spyContent = `<div class="panel-row"><span class="label" style="color:#ccc">Workshop intel (upgrades) visible in spy reports</span><span class="value" style="color:${spyWorkshop > 0 ? '#4fc3f7' : '#555'};font-weight:bold">${spyWorkshop > 0 ? 'Active' : 'No'}</span></div>`;

  const siegeCorruption = effects.enemy_siege_time_modifier || 0;
  const siegeCorruptionRows = sourceRows('enemy_siege_time_modifier', (v) => `-${(v * 100).toFixed(0)}%`, rulerName);

  const box = overlay.querySelector('.prod-overlay-box');
  box.innerHTML = `
    <button class="prod-overlay-close" title="Close">✕</button>
    <div style="font-weight:bold;font-size:1.05em;margin-bottom:12px">⚔ Army Effects</div>
    ${section('🕐', 'Travel Time', '#ffa726', travelRows, _fmtS(travelTotal))}
    ${section('⚔️', 'Siege Corruption', '#ef9a9a', siegeCorruptionRows, siegeCorruption > 0 ? `-${(siegeCorruption * 100).toFixed(0)}% enemy siege time` : 'No reduction')}
    ${section('🏆', 'Artifact Steal — Victory', '#c9a84c', stealVictoryRows, _fmtPct(baseVictory + stealVictoryMod))}
    ${section('💀', 'Artifact Steal — Defeat', '#e57373', stealDefeatRows, _fmtPct(baseDefeat + stealDefeatMod))}
    ${section('🕵', 'Spy Capabilities', '#4fc3f7', spyContent, '')}
  `;
  box.addEventListener('click', (e) => {
    if (e.target.classList.contains('prod-overlay-close')) overlay.remove();
  });
}

function init(el, _api, _state) {
  container = el;
  api = _api;
  st = _state;

  container.innerHTML = `
    <div id="attack-target-banner" style="display:none;margin-bottom:12px;padding:8px 12px;background:rgba(229,57,53,0.15);border:1px solid var(--danger,#e53935);border-radius:var(--radius);color:var(--danger,#e53935);font-weight:bold;"></div>

    <!-- ── Global Target Input (always visible, top) ──── -->
    <div id="global-target-wrap" style="margin-bottom:12px;">
      <div style="display:flex;gap:6px;align-items:center;">
        <div class="empire-ac-wrap" style="position:relative;flex:1;">
          <input type="text" id="global-target-input" class="target-uid-input" placeholder="Target empire…" autocomplete="off" style="width:100%;box-sizing:border-box;padding-right:28px;" />
          <button id="global-target-clear" title="Clear" style="position:absolute;right:4px;top:50%;transform:translateY(-50%);background:none;border:none;cursor:pointer;color:#888;font-size:18px;line-height:1;padding:0 2px;">✕</button>
          <div class="empire-ac-dropdown"></div>
        </div>
      </div>
    </div>

    <!-- ── New Army Name Overlay ─────────────────────────── -->
    <div id="new-army-overlay" style="display:none;position:fixed;inset:0;z-index:9999;background:rgba(0,0,0,0.55);align-items:center;justify-content:center;">
      <div style="background:var(--panel-bg,#1e1e2e);border:1px solid var(--border-color);border-radius:var(--radius,8px);padding:14px 16px;min-width:240px;max-width:90vw;display:flex;flex-direction:column;gap:8px;position:relative;">
        <button id="new-army-close" style="position:absolute;top:6px;right:8px;background:none;border:none;cursor:pointer;color:#888;font-size:16px;line-height:1;">✕</button>
        <div style="font-weight:bold;padding-right:20px;">New Army</div>
        <input type="text" id="new-army-name" placeholder="Name" maxlength="120" style="width:100%;box-sizing:border-box;" />
        <div id="new-army-msg" style="font-size:0.82em;min-height:14px;"></div>
        <button id="new-army-confirm" style="width:100%;">Buy</button>
      </div>
    </div>

    <!-- ── Spy Report Overlay ─────────────────────────── -->
    <div id="spy-report-overlay" style="display:none;position:fixed;inset:0;z-index:9999;background:rgba(0,0,0,0.65);align-items:center;justify-content:center;">
      <div style="background:var(--panel-bg,#1e1e2e);border:1px solid rgba(150,100,220,0.5);border-radius:var(--radius,8px);padding:20px;min-width:280px;max-width:min(520px,92vw);max-height:80vh;overflow-y:auto;position:relative;">
        <button id="spy-report-close" style="position:absolute;top:8px;right:12px;background:none;border:none;cursor:pointer;color:#888;font-size:18px;line-height:1;">✕</button>
        <div id="spy-report-body"></div>
      </div>
    </div>

    <!-- ── Armies Overview ────────────────────────────── -->
    <div id="army-list" class="army-tiles">
      <div class="empty-state"><div class="empty-icon">⚔</div><p>Loading armies…</p></div>
    </div>

    <!-- ── New Army Tile (bottom) ─────────────────────── -->
    <button id="create-army-btn" style="width:100%;display:flex;align-items:center;justify-content:center;gap:10px;padding:10px 16px;margin-top:12px;border-radius:var(--radius,8px);font-size:13px;font-weight:600;">
      <span>⚔ + New Army</span>
      <span id="army-price-display" style="font-size:10px;opacity:0.7;"></span>
    </button>

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
      .wave-tile{transition:transform 0.15s ease;}
      .wave-tile--dragging{opacity:0;pointer-events:none;}
      .wave-tile[draggable="true"]{cursor:grab;user-select:none;-webkit-user-select:none;-webkit-touch-callout:none;}
      .wave-tile[draggable="true"]:active{cursor:grabbing;}
    `;
    document.head.appendChild(s);
  }

  const newArmyOverlay = document.getElementById('new-army-overlay');
  container.querySelector('#create-army-btn').addEventListener('click', () => {
    document.getElementById('new-army-name').value = '';
    document.getElementById('new-army-msg').textContent = '';
    newArmyOverlay.style.display = 'flex';
    document.getElementById('new-army-name').focus();
  });
  document.getElementById('new-army-close').addEventListener('click', () => {
    newArmyOverlay.style.display = 'none';
  });
  document.getElementById('new-army-confirm').addEventListener('click', onCreateArmy);
  document.getElementById('new-army-name').addEventListener('keydown', (e) => {
    if (e.key === 'Enter') onCreateArmy();
    if (e.key === 'Escape') newArmyOverlay.style.display = 'none';
  });
  newArmyOverlay.addEventListener('click', (e) => {
    if (e.target === newArmyOverlay) newArmyOverlay.style.display = 'none';
  });

  // Move fixed overlays to document.body so they're not inside #shell's stacking context
  // (otherwise the rally banner at z-index:99 outside #shell beats them despite z-index:9999)
  document.body.appendChild(container.querySelector('#new-army-overlay'));
  document.body.appendChild(container.querySelector('#spy-report-overlay'));
  document.body.appendChild(container.querySelector('#critter-overlay'));

  // ── Global target input ─────────────────────────────────────
  const globalTargetInput = container.querySelector('#global-target-input');

  function _syncGlobalTarget(_name) {
    // no-op: per-army inputs removed; global input is the single source
  }

  container.querySelector('#global-target-clear').addEventListener('click', () => {
    globalTargetInput.value = '';
    _syncGlobalTarget('');
  });

  _bindAutocomplete(globalTargetInput);
  globalTargetInput.addEventListener('input', () => {
    _syncGlobalTarget(globalTargetInput.value);
    _updateMapBtn();
  });
  globalTargetInput.addEventListener('change', () => _syncGlobalTarget(globalTargetInput.value));
  globalTargetInput.addEventListener('blur', () => setTimeout(() => _syncGlobalTarget(globalTargetInput.value), 100));

  // Spy attack button is rendered inside #army-list by renderArmies; listener attached there.

  // Bind spy report overlay close
  const spyOverlay = document.getElementById('spy-report-overlay');
  document.getElementById('spy-report-close').addEventListener('click', () => {
    spyOverlay.style.display = 'none';
  });
  spyOverlay.addEventListener('click', (e) => {
    if (e.target === spyOverlay) spyOverlay.style.display = 'none';
  });

  // Bind critter overlay close
  const critterOverlay = document.getElementById('critter-overlay');
  const _closeOverlay = () => critterOverlay.classList.remove('is-open');
  document.getElementById('critter-overlay-close').addEventListener('click', _closeOverlay);
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
  pageTitle.set('🗡 Army Composer', {
    id: 'army-effects-btn', title: 'Show army effects', onClick: _showArmyEffectsOverlay,
  });
  // Listen to military data updates (but only for this view)
  _unsub.push(eventBus.on('state:military', renderArmies));
  _unsub.push(eventBus.on('state:military', () => _startEtaTicker()));
  _unsub.push(eventBus.on('state:military', _updateSpyButton));
  _unsub.push(eventBus.on('state:items', () => { if (st.military) renderArmies(st.military); }));
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
    if (!err.message.includes('Unauthorized')) console.error('Failed to load military data:', err);
  }

  // Pre-fill target inputs if navigated here from the empire list
  if (st.pendingAttackTarget) {
    const { uid, name } = st.pendingAttackTarget;
    st.pendingAttackTarget = null;
    _resetScroll = true;
    const val = name || String(uid);
    const globalInput = container.querySelector('#global-target-input');
    if (globalInput) {
      globalInput.value = val;
      _updateMapBtn();
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
    if (isGameFrozen()) return;
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
  // Hide overlays (they live on document.body across navigations)
  const _newArmyOv = document.getElementById('new-army-overlay');
  if (_newArmyOv) _newArmyOv.style.display = 'none';
  const _spyOv = document.getElementById('spy-report-overlay');
  if (_spyOv) _spyOv.style.display = 'none';
  const _critterOv = document.getElementById('critter-overlay');
  if (_critterOv) _critterOv.classList.remove('is-open');
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
  const nameInput = document.getElementById('new-army-name');
  const msgEl = document.getElementById('new-army-msg');
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

  const confirmBtn = document.getElementById('new-army-confirm');
  confirmBtn.disabled = true;
  try {
    const resp = await rest.createArmy(name);
    if (resp.success) {
      document.getElementById('new-army-overlay').style.display = 'none';
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
    <input type="text" class="army-name-input" data-aid="${aid}" maxlength="120" />
    <button class="army-confirm-btn" data-aid="${aid}" title="Save">✓</button>
    <button class="army-cancel-btn" data-aid="${aid}" title="Cancel">✕</button>
  `;

  const input = nameHeader.querySelector('.army-name-input');
  input.value = currentName;
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

async function onSetRulerWave(aid, waveIdx, rulerIid) {
  try {
    const resp = await rest.setRulerWave(aid, waveIdx, rulerIid);
    if (resp?.success === false) {
      console.warn('set ruler wave rejected:', resp.error);
      return false;
    }
    await rest.getMilitary();
    return true;
  } catch (err) {
    console.error('Failed to set ruler wave:', err);
    return false;
  }
}

async function onChangeCritter(aid, waveIdx, critterIid, currentRulerIid = null) {
  if (!critterIid) return;
  try {
    // If this wave has a ruler assigned, remove it first before setting a critter
    if (currentRulerIid) {
      await rest.setRulerWave(aid, waveIdx, '');
    }
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
      if (!iid) { canvas.style.display = 'none'; return; }
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
 * Return ruler combat stats for display.
 * Uses backend-computed values from summary.ruler.combat_stats (quadratic formula).
 * animation is still read from the item catalog (static sprite metadata).
 * Returns null if data is unavailable.
 */
function _rulerStats(rulerType, _level) {
  const catalog = st.items?.rulers?.[rulerType];
  const combat = st.summary?.ruler?.combat_stats;
  if (!combat) return null;
  return {
    health: combat.health,
    speed: combat.speed,
    armour: combat.armour,
    damage: combat.damage,
    animation: catalog?.critter?.animation || '',
  };
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
  currentSlots = 0,
  currentRulerIid = null
) {
  const overlay = document.getElementById('critter-overlay');
  const body = document.getElementById('critter-overlay-body');
  if (!overlay || !body) return;

  const currentGold = st.summary?.resources?.gold || 0;
  const _fx = st.summary?.effects || {};
  const _waveDiscount = _fx.wave_cost_modifier || 0;
  const _eraDiscount = _fx.wave_era_cost_modifier || 0;
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
          <div id="wave-slot-count" style="font-size:18px;font-weight:700;color:var(--accent);line-height:1.1;">${currentSlots}</div>
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
      ${(() => {
        const ruler = st.summary?.ruler;
        if (!ruler?.type) return '';

        const armies = st.military?.armies || [];
        let rulerInOtherWave = false;
        for (const a of armies) {
          for (let wi = 0; wi < (a.waves || []).length; wi++) {
            if (a.waves[wi].iid === ruler.type && !(a.aid === aid && wi === waveIdx)) {
              rulerInOtherWave = true;
            }
          }
        }

        const isSelected = currentRulerIid === ruler.type;
        const stats = _rulerStats(ruler.type, ruler.level);
        const animation = stats?.animation || '';
        const isMuted = rulerInOtherWave && !isSelected;

        return `
        <button class="critter-pick-tile${isSelected ? ' critter-pick-tile--selected' : ''}${isMuted ? ' critter-pick-tile--muted' : ''}"
            data-ruler-pick="${ruler.type}"
            ${isMuted ? 'title="Ruler already assigned to another wave"' : isSelected ? 'title="Click to remove ruler from this wave"' : ''}>
          <div class="cpt-sprite" style="${isMuted ? 'opacity:0.35;filter:grayscale(1);' : ''}">
            <canvas class="critter-sprite-canvas" data-animation="${animation}" width="64" height="64"></canvas>
          </div>
          <div class="cpt-name" style="display:flex;align-items:baseline;gap:4px;overflow:hidden;${isMuted ? 'opacity:0.4;' : ''}">
            <span style="overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">👑 ${ruler.name}</span>
            <span class="era-roman-badge" style="font-size:9px;flex-shrink:0;">Lv.${ruler.level}</span>
          </div>
          <div class="cpt-stats" style="${isMuted ? 'opacity:0.4;' : ''}">
            ${stats ? `
              <span class="cpt-stat cpt-hp" title="Health">❤ ${stats.health.toFixed(1)}</span>
              ${stats.armour ? `<span class="cpt-stat cpt-arm" title="Armour">🛡 ${stats.armour.toFixed(2)}</span>` : ''}
              <span class="cpt-stat cpt-spd" title="Speed">⚡ ${stats.speed.toFixed(2)}</span>
            ` : ''}
          </div>
        </button>`;
      })()}
      ${(() => {
        const currentArmy = (st.military?.armies || []).find((a) => a.aid === aid);
        const bossesInArmy = new Set(
          (currentArmy?.waves || [])
            .filter((w, wi) => wi !== waveIdx && _availableCritters.find((c) => c.iid === w.iid && c.is_boss))
            .map((w) => w.iid)
        );
        return [..._availableCritters]
        .reverse()
        .map((c) => {
          const isSelected = c.iid === currentIid;
          const isMuted = (c.era_index ?? 0) > maxEra || (c.is_boss && bossesInArmy.has(c.iid));
          const u = _applyCritUpgrades(c);
          const upgLevels = st.summary?.item_upgrades?.[c.iid] ?? {};
          const totalUpgLvl = Object.values(upgLevels).reduce((a, b) => a + b, 0);
          return `
          <button class="critter-pick-tile${isSelected ? ' critter-pick-tile--selected' : ''}${isMuted ? ' critter-pick-tile--muted' : ''}"
              data-iid="${c.iid}" ${c.is_boss && bossesInArmy.has(c.iid) ? 'title="Boss already used in another wave of this army"' : isMuted ? 'title="Era not unlocked for this wave"' : ''}>
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
        .join('');
      })()}
    </div>
  `;

  _initCritterCanvases(body);

  // Slot upgrade button
  const slotUpgradeBtn = body.querySelector('#wave-slot-upgrade-btn');
  if (slotUpgradeBtn) {
    slotUpgradeBtn.addEventListener('click', async () => {
      if (slotUpgradeBtn.getAttribute('data-can-afford') !== 'true') return;
      slotUpgradeBtn.disabled = true;
      slotUpgradeBtn.setAttribute('data-can-afford', 'false');
      const resp = await rest.buyCritterSlot(aid, waveIdx);
      if (!resp.success) {
        slotUpgradeBtn.disabled = false;
        slotUpgradeBtn.setAttribute('data-can-afford', 'true');
        return;
      }
      const [, milResp] = await Promise.all([rest.getSummary(), rest.getMilitary()]);
      const updatedArmy = (milResp?.armies || []).find((a) => a.aid === aid);
      const updatedWave = updatedArmy?.waves?.[waveIdx];
      const serverNextSlotPrice = updatedWave?.next_slot_price ?? nextSlotPrice;
      const newSlots = updatedWave?.slots ?? currentSlots + 1;
      const slotCountEl = body.querySelector('#wave-slot-count');
      if (slotCountEl) slotCountEl.textContent = newSlots;
      slotUpgradeBtn.textContent = `+1 · 💰${Math.round(serverNextSlotPrice)}`;
      slotUpgradeBtn.disabled = false;
      slotUpgradeBtn.setAttribute('data-can-afford', 'true');
    });
  }

  // Era upgrade button
  const eraUpgradeBtn = body.querySelector('#wave-era-upgrade-btn');
  if (eraUpgradeBtn) {
    eraUpgradeBtn.addEventListener('click', async () => {
      if (eraUpgradeBtn.getAttribute('data-can-afford') !== 'true') return;
      const newMaxEra = maxEra + 1;
      const newNextEraPrice = _waveEraPrice(newMaxEra + 1) * Math.max(0, 1 - _eraDiscount);
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
      const rulerType = btn.dataset.rulerPick;
      if (rulerType) {
        // Toggle: click selected ruler tile removes it, click unselected assigns it
        overlay.classList.remove('is-open');
        await onSetRulerWave(aid, waveIdx, currentRulerIid === rulerType ? '' : rulerType);
        return;
      }
      const iid = btn.dataset.iid;
      overlay.classList.remove('is-open');
      await onChangeCritter(aid, waveIdx, iid, currentRulerIid);
    });
  });

  overlay.classList.add('is-open');
}

/**
 * Wire up drag-and-drop (desktop) and long-press drag (mobile) for wave reordering.
 *
 * Visual model: the dragged tile becomes an invisible placeholder (opacity:0) that
 * stays in its original DOM position. All other tiles shift via CSS transform to
 * slide into their new positions in real time, showing a gap at the drop target.
 * On drop, one insertBefore finalizes the DOM order, clears transforms, and calls
 * the backend. The approach avoids double-reorder bugs.
 */
function _initWaveDragDrop(wavesContainer, aid) {
  const tiles = () => [...wavesContainer.querySelectorAll('.wave-tile:not(.wave-tile-add)')];

  let _srcEl      = null;
  let _srcIdx     = -1;
  let _dstIdx     = -1;
  let _cachedStep = 0;   // tile step (width+gap) for same-row shift animation
  let _tileLefts  = [];  // offsetLeft of each tile at drag start (for shift animation, 1-row)
  let _tileRects  = [];  // {left,top,right,bottom,width,height} snapshot for 2-D touch detection

  // Slide non-src tiles to visually show a gap at dstIdx.
  function _applyShifts(srcIdx, dstIdx) {
    tiles().forEach((t, i) => {
      if (i === srcIdx) return;
      let shift = 0;
      if (srcIdx < dstIdx && i > srcIdx && i < dstIdx) shift = -_cachedStep;
      else if (srcIdx > dstIdx && i >= dstIdx && i < srcIdx) shift = _cachedStep;
      t.style.transform = shift ? `translateX(${Math.round(shift)}px)` : '';
    });
  }

  // Commit reorder: disable transition → clear transforms instantly → DOM move →
  // re-enable transition next frame. This prevents the jump-back animation glitch.
  function _finalize(srcIdx, dstIdx) {
    if (!_srcEl) return;
    const all = tiles();

    all.forEach(t => { t.style.transition = 'none'; t.style.transform = ''; });
    _srcEl.classList.remove('wave-tile--dragging');

    const noMove = dstIdx === srcIdx || dstIdx === srcIdx + 1;
    let newIds = null;
    if (!noMove) {
      const addTile = wavesContainer.querySelector('.wave-tile-add');
      const refTile = dstIdx >= all.length ? (addTile ?? null) : all[dstIdx];
      wavesContainer.insertBefore(_srcEl, refTile);
      newIds = tiles().map(t => parseInt(t.dataset.waveId, 10));
    }

    _srcEl = null; _srcIdx = -1; _dstIdx = -1; _cachedStep = 0; _tileLefts = []; _tileRects = [];

    requestAnimationFrame(() => tiles().forEach(t => { t.style.transition = ''; }));

    if (newIds) {
      if (!newIds.some(isNaN) && new Set(newIds).size === newIds.length) {
        rest.reorderWaves(aid, newIds).then(r => {
          if (!r?.success) rest.getMilitary();
        });
      } else {
        rest.getMilitary();
      }
    }
  }

  function _reset() {
    if (!_srcEl) return;
    tiles().forEach(t => { t.style.transition = 'none'; t.style.transform = ''; });
    _srcEl.classList.remove('wave-tile--dragging');
    _srcEl = null; _srcIdx = -1; _dstIdx = -1; _cachedStep = 0; _tileLefts = []; _tileRects = [];
    requestAnimationFrame(() => tiles().forEach(t => { t.style.transition = ''; }));
  }

  // Row-aware insertion index from touch coordinates.
  // Groups non-src tiles by visual row, finds the closest row to ty,
  // then resolves the before/after position by tx within that row.
  function _dstFromTouch(tx, ty) {
    const rects = _tileRects;
    const n = rects.length;

    // Build row groups from non-src tiles (group tiles whose tops differ by < half tile height)
    const rows = []; // each entry: sorted array of tile indices in one row
    for (let i = 0; i < n; i++) {
      if (i === _srcIdx) continue;
      const top = rects[i].top;
      let placed = false;
      for (const row of rows) {
        if (Math.abs(rects[row[0]].top - top) < rects[i].height * 0.6) {
          row.push(i); placed = true; break;
        }
      }
      if (!placed) rows.push([i]);
    }
    if (rows.length === 0) return _dstIdx;

    // Find the row whose vertical midpoint is closest to ty
    let bestRow = rows[0];
    let bestDist = Infinity;
    for (const row of rows) {
      const r = rects[row[0]];
      const dist = Math.abs(ty - (r.top + r.bottom) / 2);
      if (dist < bestDist) { bestDist = dist; bestRow = row; }
    }

    // Sort row tiles left→right, then resolve x position
    bestRow.sort((a, b) => rects[a].left - rects[b].left);
    for (let k = 0; k < bestRow.length; k++) {
      const i = bestRow[k];
      const mid = rects[i].left + rects[i].width / 2;
      if (tx < mid - _DEADZONE) return i;        // insert before tile i
      if (tx <= mid + _DEADZONE) return _dstIdx;  // dead zone: keep current
      if (k === bestRow.length - 1) return i + 1; // after last tile in this row
    }
    return _dstIdx;
  }

  // ── Desktop: HTML5 Drag & Drop ───────────────────────────────────
  function _onDragStart(e) {
    const all = tiles();
    _srcEl      = e.currentTarget;
    _srcIdx     = all.indexOf(_srcEl);
    _dstIdx     = _srcIdx;
    _cachedStep = all.length >= 2 ? all[1].offsetLeft - all[0].offsetLeft : (all[0]?.offsetWidth ?? 80) + 8;
    _tileLefts  = all.map(t => t.offsetLeft);
    e.dataTransfer.effectAllowed = 'move';
    e.dataTransfer.setData('text/plain', _srcEl.dataset.waveId);
    e.dataTransfer.setDragImage(_srcEl, e.offsetX, e.offsetY);
    requestAnimationFrame(() => _srcEl?.classList.add('wave-tile--dragging'));
  }

  function _onDragOver(e) {
    if (!_srcEl) return;
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
    const overEl  = e.currentTarget;
    const overIdx = tiles().indexOf(overEl);
    if (overIdx === -1 || overEl === _srcEl) return;

    // Dead zone: only commit if cursor is clearly past the midpoint (20% of tile width)
    const rect   = overEl.getBoundingClientRect();
    const dzone  = rect.width * 0.2;
    const mid    = rect.left + rect.width / 2;
    let dst;
    if (e.clientX < mid - dzone) dst = overIdx;
    else if (e.clientX > mid + dzone) dst = overIdx + 1;
    else return; // in dead zone — keep current dstIdx

    if (dst === _dstIdx) return;
    _dstIdx = dst;
    _applyShifts(_srcIdx, _dstIdx);
  }

  function _onDrop(e) {
    e.preventDefault();
    if (!_srcEl) return;
    _finalize(_srcIdx, _dstIdx === -1 ? _srcIdx : _dstIdx);
  }

  function _onDragEnd() { _reset(); }

  // ── Mobile: long-press → touch drag ─────────────────────────────
  let _longPressTimer = null;
  let _ghost          = null;
  let _touchStartX    = 0;
  let _touchStartY    = 0;
  let _isTouchDrag    = false;
  const _DEADZONE     = 18; // px: don't flip dstIdx when finger is near tile midpoint

  const _blockSelect = e => e.preventDefault();

  function _cancelLongPress() {
    clearTimeout(_longPressTimer);
    _longPressTimer = null;
    document.removeEventListener('selectstart', _blockSelect);
  }
  function _removeGhost() { _ghost?.remove(); _ghost = null; }

  function _onTouchStart(e) {
    if (e.touches.length !== 1) return;
    _touchStartX = e.touches[0].clientX;
    _touchStartY = e.touches[0].clientY;
    _isTouchDrag = false;
    const tile = e.currentTarget;
    document.addEventListener('selectstart', _blockSelect);
    _longPressTimer = setTimeout(() => {
      document.removeEventListener('selectstart', _blockSelect);
      const all   = tiles();
      _srcEl      = tile;
      _srcIdx     = all.indexOf(tile);
      _dstIdx     = _srcIdx;
      _cachedStep = all.length >= 2 ? all[1].offsetLeft - all[0].offsetLeft : (all[0]?.offsetWidth ?? 80) + 8;
      _tileLefts  = all.map(t => t.offsetLeft);
      // Snapshot viewport-relative rects for 2-D touch detection.
      // getBoundingClientRect is safe here because touchmove prevents scroll during drag.
      _tileRects  = all.map(t => { const r = t.getBoundingClientRect(); return { left: r.left, top: r.top, right: r.right, bottom: r.bottom, width: r.width, height: r.height }; });
      _isTouchDrag = true;
      tile.classList.add('wave-tile--dragging');
      const rect = tile.getBoundingClientRect();
      _ghost = tile.cloneNode(true);
      // Canvas pixel content is not copied by cloneNode — replace each with a snapshot img
      tile.querySelectorAll('canvas').forEach((src, i) => {
        const dst = _ghost.querySelectorAll('canvas')[i];
        if (!dst) return;
        try {
          const img = document.createElement('img');
          img.src = src.toDataURL();
          img.style.cssText = dst.style.cssText;
          img.style.width  = dst.style.width  || src.style.width  || src.width  + 'px';
          img.style.height = dst.style.height || src.style.height || src.height + 'px';
          dst.replaceWith(img);
        } catch (_) { /* tainted canvas — leave blank */ }
      });
      _ghost.style.cssText = `position:fixed;pointer-events:none;z-index:9999;opacity:0.85;` +
        `width:${rect.width}px;height:${rect.height}px;` +
        `left:${rect.left + rect.width / 2}px;top:${rect.top + rect.height / 2}px;` +
        `transform:translate(-50%,-50%) scale(1.08);` +
        `border-radius:var(--radius,8px);box-shadow:0 6px 24px rgba(0,0,0,0.7);transition:none;`;
      document.body.appendChild(_ghost);
      navigator.vibrate?.(40);
    }, 500);
  }

  function _onTouchMove(e) {
    if (!_isTouchDrag) {
      const dx = e.touches[0].clientX - _touchStartX;
      const dy = e.touches[0].clientY - _touchStartY;
      if (Math.abs(dx) > 8 || Math.abs(dy) > 8) _cancelLongPress();
      return;
    }
    e.preventDefault();
    const tx = e.touches[0].clientX;
    const ty = e.touches[0].clientY;
    if (_ghost) { _ghost.style.left = `${tx}px`; _ghost.style.top = `${ty}px`; }

    // 2-D row-aware position detection using cached viewport rects.
    const newDst = _dstFromTouch(tx, ty);

    if (newDst !== _dstIdx) {
      _dstIdx = newDst;
      _applyShifts(_srcIdx, _dstIdx);
    }
  }

  function _onTouchEnd() {
    _cancelLongPress();
    _removeGhost();
    if (!_isTouchDrag) { _isTouchDrag = false; return; }
    _isTouchDrag = false;
    _finalize(_srcIdx, _dstIdx);
  }

  // ── Attach listeners ──────────────────────────────────────────────
  tiles().forEach(tile => {
    tile.setAttribute('draggable', 'true');
    tile.addEventListener('dragstart',   _onDragStart);
    tile.addEventListener('dragover',    _onDragOver);
    tile.addEventListener('drop',        _onDrop);
    tile.addEventListener('dragend',     _onDragEnd);
    tile.addEventListener('touchstart',  _onTouchStart,  { passive: true });
    tile.addEventListener('touchmove',   _onTouchMove,   { passive: false });
    tile.addEventListener('touchend',    _onTouchEnd);
    tile.addEventListener('touchcancel', _onTouchEnd);
  });

  // Container-level handlers so drops on gaps between tiles are accepted
  // (without these the browser shows a "forbidden" cursor over the gaps).
  wavesContainer.addEventListener('dragover', e => {
    if (!_srcEl) return;
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
  });
  wavesContainer.addEventListener('drop', e => {
    e.preventDefault();
    if (!_srcEl) return;
    _finalize(_srcIdx, _dstIdx === -1 ? _srcIdx : _dstIdx);
  });
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
  const errorEl = btn.closest('.army-group')?.querySelector('.army-attack-error');
  btn.disabled = state === 'loading';
  btn.style.opacity = state === 'loading' ? '0.5' : '';
  btn.style.cursor = state === 'loading' ? 'default' : '';
  if (state === 'loading') {
    btn.innerHTML = `<span>⚔ ${label2}</span>`;
  } else {
    btn.innerHTML = `<span>⚔ Attack</span>`;
  }
  if (errorEl) errorEl.textContent = state === 'error' ? label2 : '';
}

function _updateSpyButton() {
  // Button lives inside #army-list (re-rendered each time), so this is a no-op;
  // state is baked in during renderArmies. Only called after manual spy dispatch.
  const btn = container.querySelector('#spy-attack-btn');
  if (!btn) return;
  const statusEl = container.querySelector('#spy-status-msg');

  const activeSpies = (st.military?.attacks_outgoing || []).filter((a) => a.is_spy);
  if (activeSpies.length > 0) {
    const eta = fmtTravelTime(activeSpies[0].eta_seconds);
    btn.disabled = true;
    btn.style.opacity = '0.5';
    btn.style.cursor = 'default';
    btn.innerHTML = `<span>🕵 Dispatched</span><span style="font-size:0.75em;opacity:0.7;">ETA: ${eta}</span>`;
    if (statusEl) statusEl.textContent = '';
  } else {
    btn.disabled = false;
    btn.style.opacity = '';
    btn.style.cursor = '';
    btn.innerHTML = `<span>🕵 Send Spy</span><span id="spy-eta-label" style="font-size:0.75em;opacity:0.7;"></span>`;
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
  const spyInput = container.querySelector('#global-target-input');
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
  const overlay = document.getElementById('spy-report-overlay');
  const body = document.getElementById('spy-report-body');
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

    <div style="font-size:13px;font-weight:600;margin-bottom:6px;margin-top:10px;color:var(--accent,#4fc3f7);">⚜ Artifacts</div>
    <div style="border-top:1px solid rgba(255,255,255,0.1);padding-top:8px;margin-bottom:10px;">
      ${(msg.artifacts || []).length > 0
        ? (msg.artifacts).map((a) => `<div style="padding:2px 0;font-size:12px;">⚜ ${escHtml(a)}</div>`).join('')
        : '<div style="opacity:0.4;font-size:12px;">none</div>'}
    </div>

    <div style="font-size:13px;font-weight:600;margin-bottom:6px;margin-top:10px;color:var(--accent,#4fc3f7);">👑 Ruler</div>
    <div style="border-top:1px solid rgba(255,255,255,0.1);padding-top:8px;margin-bottom:10px;">
      ${msg.ruler
        ? `<div style="font-size:12px;">👑 ${escHtml(msg.ruler.name)} &mdash; <span style="color:#aaa">Lv ${msg.ruler.level}</span></div>`
        : '<div style="opacity:0.4;font-size:12px;">none</div>'}
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

  const query = (container.querySelector('#global-target-input')?.value.trim()) || '';

  if (!query) {
    _setAttackBtnState(btn, 'error', 'Enter a target empire');
    setTimeout(() => _setAttackBtnState(btn, 'ready'), 2000);
    return;
  }

  _setAttackBtnState(btn, 'loading', 'Searching…');
  let targetUid, targetName;
  try {
    ({ uid: targetUid, name: targetName } = await rest.resolveEmpire(query));
  } catch (err) {
    _setAttackBtnState(btn, 'error', err.message);
    setTimeout(() => _setAttackBtnState(btn, 'ready'), 2500);
    return;
  }

  _setAttackBtnState(btn, 'loading', 'Launching…');
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
      _setAttackBtnState(btn, 'error', resp.error || 'Attack failed');
      setTimeout(() => _setAttackBtnState(btn, 'ready'), 3000);
    }
  } catch (err) {
    console.error('Failed to launch attack:', err);
    _setAttackBtnState(btn, 'error', 'Network error');
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
  if (!critterSlots || critterSlots <= 0) return Math.max(1, waveSlots);
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
    input.dispatchEvent(new Event('input', { bubbles: true }));
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

  let _debounceTimer = null;
  const _debouncedSearch = () => {
    clearTimeout(_debounceTimer);
    _debounceTimer = setTimeout(_search, 300);
  };
  input.addEventListener('input', _debouncedSearch);
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

  // Preserve scroll position before re-render
  const scrollY = window.scrollY;

  // Store available critters and sprite lookup for all critters (incl. locked)
  _availableCritters = data.available_critters || [];
  _critterSprites = data.critter_sprites || {};

  const armies = data.armies || [];

  if (armies.length === 0) {
    const activeSpies0 = (st.military?.attacks_outgoing || []).filter((a) => a.is_spy);
    const spyDisabled0 = activeSpies0.length > 0;
    const spyEta0 = spyDisabled0 ? fmtTravelTime(activeSpies0[0].eta_seconds) : '';
    const spyTravelTime0 = st.summary?.travel_time_seconds;
    const spyTravelLabel0 = spyTravelTime0 ? `✈ ${fmtTravelTime(Math.round(spyTravelTime0 / 2))}` : '';
    el.innerHTML = `
      <div class="army-group" style="margin-bottom:12px;">
        <div class="army-name-header">
          <div class="army-name">🕵 Spy Army</div>
          <button id="spy-attack-btn" class="army-attack-btn" style="display:flex;flex-direction:column;align-items:center;justify-content:center;gap:1px;line-height:1.2;${spyDisabled0 ? 'opacity:0.5;cursor:default;' : ''}" ${spyDisabled0 ? 'disabled' : ''}>
            ${spyDisabled0
              ? `<span>🕵 Dispatched</span><span style="font-size:0.75em;opacity:0.7;">ETA: ${spyEta0}</span>`
              : `<span>🕵 Send Spy</span><span id="spy-eta-label" style="font-size:0.75em;opacity:0.7;">${spyTravelLabel0}</span>`}
          </button>
        </div>
        <p id="spy-army-desc" style="font-size:11px;color:var(--text-dim);margin:0 0 10px;">Sends a spy to the target empire. The spy reveals enemy defense information.</p>
        <div id="spy-status-msg" style="font-size:11px;color:var(--text-dim);min-height:14px;"></div>
      </div>
      <div class="army-separator"></div>
      <div class="empty-state"><div class="empty-icon">⚔</div><p>No armies yet. Create one below to get started.</p></div>`;
    el.querySelector('#spy-attack-btn')?.addEventListener('click', onSpyAttack);
    return;
  }

  const currentGold = st.summary?.resources?.gold || 0;

  const travelTime = st.summary?.travel_time_seconds;
  const travelLabel = travelTime ? fmtTravelTime(travelTime) : '';

  el.classList.add('armies-container');

  // Build spy tile HTML
  const activeSpies = (st.military?.attacks_outgoing || []).filter((a) => a.is_spy);
  const spyDisabled = activeSpies.length > 0;
  const spyEta = spyDisabled ? fmtTravelTime(activeSpies[0].eta_seconds) : '';
  const spyTravelTime = st.summary?.travel_time_seconds;
  const spyTravelLabel = spyTravelTime ? `✈ ${fmtTravelTime(Math.round(spyTravelTime / 2))}` : '';
  const firstName = armies.length > 0 ? `"${escHtml(armies[0].name)}"` : 'your first army';
  const spyTileHtml = `
    <div class="army-group" style="margin-bottom:12px;">
      <div class="army-name-header">
        <div class="army-name">🕵 Spy Army</div>
        <button id="spy-attack-btn" class="army-attack-btn" style="display:flex;flex-direction:column;align-items:center;justify-content:center;gap:1px;line-height:1.2;${spyDisabled ? 'opacity:0.5;cursor:default;' : ''}" ${spyDisabled ? 'disabled' : ''}>
          ${spyDisabled
            ? `<span>🕵 Dispatched</span><span style="font-size:0.75em;opacity:0.7;">ETA: ${spyEta}</span>`
            : `<span>🕵 Send Spy</span><span id="spy-eta-label" style="font-size:0.75em;opacity:0.7;">${spyTravelLabel}</span>`}
        </button>
      </div>
      <p id="spy-army-desc" style="font-size:11px;color:var(--text-dim);margin:0 0 10px;">Sends a spy to the target empire. Your spy disguises as ${firstName}. The spy reveals enemy defense information.</p>
      <div id="spy-status-msg" style="font-size:11px;color:var(--text-dim);min-height:14px;"></div>
    </div>
    <div class="army-separator"></div>
  `;

  el.innerHTML = spyTileHtml + armies
    .map((a, idx) => {
      const realAtk = (st.military?.attacks_outgoing || []).find(
        (atk) => !atk.is_spy && atk.army_aid === a.aid
      );
      const spyAtk = (st.military?.attacks_outgoing || []).find(
        (atk) => atk.is_spy && atk.army_name === a.name
      );
      const armyInBattle = !!realAtk && realAtk.phase === 'in_battle';
      const btnDisabled = !!realAtk;
      let btnContent;
      const _atkPhaseLabel = (atk) => {
        if (atk.phase === 'in_siege') return '🏰 In Siege';
        if (atk.phase === 'in_battle') return '⚔ In Battle';
        return '⚔ Attacking';
      };
      const _atkEtaLine = (atk) => {
        if (atk.phase === 'in_siege') {
          const endTs = Date.now() + atk.siege_remaining_seconds * 1000;
          return `<span class="eta-live" data-eta-ts="${endTs}" data-eta-prefix="Siege" style="font-size:0.75em;opacity:0.7;">Siege: ${fmtTravelTime(atk.siege_remaining_seconds)}</span>`;
        }
        if (atk.phase === 'traveling' || atk.phase === 'traveling') {
          const endTs = Date.now() + atk.eta_seconds * 1000;
          return `<span class="eta-live" data-eta-ts="${endTs}" data-eta-prefix="ETA" style="font-size:0.75em;opacity:0.7;">ETA: ${fmtTravelTime(atk.eta_seconds)}</span>`;
        }
        return '';
      };
      const _targetName = (atk) => {
        const emp = _empiresCache.find((e) => e.uid === atk.defender_uid);
        return emp ? emp.name : `#${atk.defender_uid}`;
      };
      const _twoLine = (line1, line2) =>
        `<span style="display:flex;flex-direction:column;align-items:center;gap:1px;"><span>${line1}</span>${line2}</span>`;
      if (spyAtk && realAtk) {
        btnContent = _twoLine(`${_atkPhaseLabel(realAtk)} · 🕵`, `<span style="font-size:0.75em;opacity:0.7;">→ ${escHtml(_targetName(realAtk))}</span>${_atkEtaLine(realAtk)}`);
      } else if (spyAtk) {
        btnContent = _twoLine(`🕵 Spy`, `<span style="font-size:0.75em;opacity:0.7;">→ ${escHtml(_targetName(spyAtk))}</span>${_atkEtaLine(spyAtk)}`);
      } else if (realAtk) {
        btnContent = _twoLine(_atkPhaseLabel(realAtk), `<span style="font-size:0.75em;opacity:0.7;">→ ${escHtml(_targetName(realAtk))}</span>${_atkEtaLine(realAtk)}`);
      } else {
        btnContent = travelLabel
          ? _twoLine('⚔ Attack', `<span style="font-size:0.75em;opacity:0.7;">✈ ${travelLabel}</span>`)
          : `<span>⚔ Attack</span>`;
      }
      return `
    <div class="army-group" data-aid="${a.aid}" data-in-battle="${armyInBattle}">
      <div class="army-name-header">
        <div class="army-name">${a.name} <span class="army-id"></span></div>
        <button class="army-edit-btn" title="Edit army name" data-aid="${a.aid}">
          <span class="edit-icon">✎</span>
        </button>
        <button class="army-attack-btn" data-aid="${a.aid}" title="Launch attack"
          style="display:flex;flex-direction:column;align-items:center;justify-content:center;gap:1px;line-height:1.2;${btnDisabled ? 'opacity:0.5;cursor:default;' : ''}"
          ${btnDisabled ? 'disabled' : ''}>
          ${btnContent}
        </button>
      </div>
      <div class="army-attack-row">
        <div class="army-attack-error" style="font-size:11px;color:var(--danger);min-height:14px;"></div>
      </div>
      <div class="waves-container">
        ${
          (a.waves || []).length > 0
            ? `
          ${(a.waves || [])
            .map((w, i) => {
              const nextSlotPrice = w.next_slot_price || 0;
              const canAffordSlot = currentGold >= nextSlotPrice;
              const isRulerWave = !!(st.items?.rulers?.[w.iid]);
              const selectedCritter = _availableCritters.find((c) => c.iid === w.iid);
              const rulerCatalog = isRulerWave ? st.items?.rulers?.[w.iid] : null;
              const rulerAnimation = rulerCatalog?.critter?.animation || '';
              const spriteInfo = isRulerWave
                ? { animation: rulerAnimation, sprite: '' }
                : (_critterSprites[w.iid] || {});
              const critterSlotCost = selectedCritter?.slots || 1;
              const numCritters = isRulerWave ? 1 : critterCountInWave(w.slots || 0, critterSlotCost);
              const hasSprite = isRulerWave
                ? !!rulerAnimation
                : (w.iid && (spriteInfo.sprite || spriteInfo.animation));
              const rulerName = isRulerWave ? (st.summary?.ruler?.name || w.iid) : '';
              return `
            <div class="wave-tile${isRulerWave ? ' wave-tile--ruler' : ''}" data-aid="${a.aid}" data-wave-idx="${i}" data-wave-id="${w.wave_id}">
              <button class="wave-critter-btn" data-aid="${a.aid}" data-wave-idx="${i}" data-current-iid="${w.iid || ''}" data-max-era="${w.max_era ?? 0}" data-next-era-price="${w.next_era_price ?? 0}" data-next-slot-price="${w.next_slot_price ?? 0}" data-slots="${w.slots || 0}" data-is-ruler="${isRulerWave ? 'true' : ''}" ${armyInBattle ? 'disabled title="Army is in battle"' : ''} style="${armyInBattle ? 'opacity:0.45;cursor:not-allowed;' : ''}">
                <span class="wave-tile__edit-hint">${armyInBattle ? '🔒' : '✎'}</span>
                ${
                  hasSprite
                    ? `<canvas class="wave-tile__sprite critter-sprite-canvas" data-iid="${w.iid || ''}" data-sprite="${spriteInfo.sprite || ''}" data-animation="${spriteInfo.animation || ''}" width="72" height="72"
                        style="image-rendering:pixelated;"></canvas>`
                    : `<div class="wave-tile__no-critter">＋</div>`
                }
                <div class="wave-tile__count">${isRulerWave ? '👑' : selectedCritter?.is_boss ? '★' : (hasSprite ? numCritters : '')}</div>
              </button>
              <div class="wave-tile__footer">
                ${isRulerWave
                  ? `<span style="font-size:9px;color:#c9a84c;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:100%;" title="${rulerName}">👑 ${rulerName}</span>`
                  : `<span class="wave-tile__slots">${w.slots || 0} Slots</span>
                     <span class="wave-tile__era era-roman-badge" title="${ERA_LABEL_EN[ERA_KEYS[w.max_era ?? 0]] || ''}" style="font-size:0.75em;">${ERA_ROMAN[ERA_KEYS[w.max_era ?? 0]] || 'I'}</span>`
                }
              </div>
            </div>
          `;
            })
            .join('')}
        `
            : ''
        }
        ${(() => {
          if (armyInBattle) return '';
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
      const currentRulerIid = btn.getAttribute('data-is-ruler') ? currentIid : null;
      _openCritterOverlay(
        aid,
        waveIdx,
        currentIid,
        maxEra,
        nextEraPrice,
        nextSlotPrice,
        currentSlots,
        currentRulerIid
      );
    });
  });

  // Attach spy attack button (rendered inside #army-list now)
  const spyBtn = el.querySelector('#spy-attack-btn');
  if (spyBtn) spyBtn.addEventListener('click', onSpyAttack);

  // Attach attack button listeners
  el.querySelectorAll('.army-attack-btn:not(#spy-attack-btn)').forEach((btn) => {
    btn.addEventListener('click', (e) => onAttackOpponent(e));
  });

  // Initialize critter sprite canvases (wave buttons)
  _initCritterCanvases(el);

  // Wire drag-and-drop reordering for each army's wave container
  el.querySelectorAll('.army-group[data-aid]').forEach(group => {
    if (group.dataset.inBattle === 'true') return; // no reorder during active combat
    const wavesContainer = group.querySelector('.waves-container');
    if (wavesContainer) _initWaveDragDrop(wavesContainer, parseInt(group.dataset.aid, 10));
  });

  // Restore scroll position after re-render (skip if we just navigated here externally)
  if (_resetScroll) {
    _resetScroll = false;
    requestAnimationFrame(() => window.scrollTo(0, 0));
  } else {
    requestAnimationFrame(() => window.scrollTo(0, scrollY));
  }

  _updateSpyButton();
}

export default {
  id: 'army',
  title: 'Army Composer',
  init,
  enter,
  leave,
};
