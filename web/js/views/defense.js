/**
 * Battle View — dedicated real-time tower defense battle display.
 *
 * This file is the thin orchestrator. Extracted submodules:
 *  - defense/era_data.js   — pure era/tower constants
 *  - defense/ws.js         — WebSocket lifecycle
 *  - defense/placement.js  — tile placement menu and map editor
 *  - defense/battle_ui.js  — battle message handlers, status panel, summary overlay
 */

import { HexGrid, getTileType, registerTileType } from '../lib/hex_grid.js';
import { hexKey } from '../lib/hex.js';
import { eventBus } from '../events.js';
import { rest } from '../rest.js';
import { debug } from '../debug.js';
import { ERA_KEYS, ERA_YAML_TO_KEY } from '../lib/eras.js';

import {
  _NON_TOWER,
  _ERA_CASTLE_SPRITES,
  _ROMAN_NUMERALS,
  STRUCTURE_COLORS,
  _buildEraStatsHTML,
} from './defense/era_data.js';
import { createBattleWs } from './defense/ws.js';
import { createPlacement } from './defense/placement.js';
import { createBattleUi } from './defense/battle_ui.js';
import { isGameFrozen } from '../lib/game_state.js';

// ── Wake Lock ─────────────────────────────────────────────────
let _wakeLock = null;
async function _acquireWakeLock() {
  if (!('wakeLock' in navigator)) return;
  try {
    _wakeLock = await navigator.wakeLock.request('screen');
  } catch (_) {}
}
function _releaseWakeLock() {
  if (_wakeLock) {
    _wakeLock.release();
    _wakeLock = null;
  }
}

// ── Shared module state ───────────────────────────────────────
/** @type {import('../state.js').StateStore} */
let st;
/** @type {HTMLElement} */
let container;
let _unsub = [];

let _structUpgDef = null;
let _critUpgDef = null;

function _applyStructUpgrades(s, iid) {
  const upgrades = st.summary?.item_upgrades?.[iid] ?? {};
  const d = _structUpgDef;
  if (!d) return s;
  const dmgLvl = upgrades.damage ?? 0;
  const rngLvl = upgrades.range ?? 0;
  const rldLvl = upgrades.reload ?? 0;
  const edLvl = upgrades.effect_duration ?? 0;
  const evLvl = upgrades.effect_value ?? 0;
  const ef = s.effects ? { ...s.effects } : {};
  if (edLvl && ef.burn_duration) ef.burn_duration *= 1 + (d.effect_duration / 100) * edLvl;
  if (evLvl && ef.burn_dps) ef.burn_dps *= 1 + (d.effect_value / 100) * evLvl;
  if (edLvl && ef.slow_duration) ef.slow_duration *= 1 + (d.effect_duration / 100) * edLvl;
  if (evLvl && ef.slow_ratio != null) ef.slow_ratio *= 1 + (d.effect_value / 100) * evLvl;
  return {
    ...s,
    damage: s.damage * (1 + (d.damage / 100) * dmgLvl),
    range: s.range * (1 + (d.range / 100) * rngLvl),
    reload_time_ms: s.reload_time_ms / (1 + (d.reload / 100) * rldLvl),
    effects: ef,
  };
}

/** @type {HexGrid|null} */
let grid = null;

let _pendingAttackId = null;
let _spectateDefenderUid = null;
let _lastCastleEra = null;
let _structureEraRoman = {};

// ── Client-side resource tick ────────────────────────────────
let _tickTimer = null;
let _tickSummary = null;
let _tickTs = null;

function _calcRate(resourceType, summary) {
  const fx = summary.effects || {};
  const citizens = summary.citizens || {};
  const effCe = summary.citizen_effect || 0; // backend already sends effective_citizen_effect
  if (resourceType === 'life') return (summary.base_life ?? 0) + (fx.life_regen_modifier || 0);
  if (resourceType === 'gold') {
    const offset = (summary.base_gold ?? 0) + (fx.gold_offset || 0);
    const mod = (citizens.merchant || 0) * effCe
      + ((citizens.artist || 0) + (citizens.scientist || 0)) * (fx.other_citizen_gold_modifier || 0)
      + (fx.gold_modifier || 0);
    return offset * (1 + mod);
  }
  const offset = (summary.base_culture ?? 0) + (fx.culture_offset || 0);
  const mod = (citizens.artist || 0) * effCe + (fx.culture_modifier || 0);
  return offset * (1 + mod);
}

function _fmtTitleResource(value, digits = 0) {
  const normalized = value ?? 0;
  if (normalized >= 1000) return Math.floor(normalized / 1000) + 'k';
  return Math.floor(normalized * Math.pow(10, digits)) / Math.pow(10, digits);
}

function _tickResources() {
  if (!_tickSummary || !_tickTs) return;
  const elapsedS = isGameFrozen() ? 0 : (Date.now() - _tickTs) / 1000;
  const res = _tickSummary.resources || {};
  const gold = (res.gold || 0) + _calcRate('gold', _tickSummary) * elapsedS;
  const culture = (res.culture || 0) + _calcRate('culture', _tickSummary) * elapsedS;
  const life = (res.life || 0) + _calcRate('life', _tickSummary) * elapsedS;
  const maxLife = _tickSummary.max_life ?? life;
  const clampedLife = Math.min(life, maxLife);
  const titleEl = container?.querySelector('.battle-title');
  if (!titleEl) return;
  const g = titleEl.querySelector('.title-gold');
  const c = titleEl.querySelector('.title-culture');
  const l = titleEl.querySelector('.title-life');
  if (g) g.textContent = '💰 ' + _fmtTitleResource(gold);
  if (c) c.textContent = '🎭 ' + _fmtTitleResource(culture);
  if (l) {
    const icon = l.querySelector('span');
    if (icon) {
      const textNode = l.childNodes[l.childNodes.length - 1];
      if (textNode && textNode.nodeType === Node.TEXT_NODE) {
        textNode.textContent = ' ' + _fmtTitleResource(clampedLife);
      }
    } else {
      l.textContent = '❤ ' + _fmtTitleResource(clampedLife);
    }
  }
}

function _buildStructureEraRoman() {
  _structureEraRoman = {};
  const structures = st.items?.structures || {};
  for (const [iid, info] of Object.entries(structures)) {
    const key = ERA_YAML_TO_KEY[info.era] || null;
    if (!key) continue;
    const idx = ERA_KEYS.indexOf(key);
    if (idx >= 0) _structureEraRoman[iid.toUpperCase()] = _ROMAN_NUMERALS[idx];
  }
}

// ── Battle state ──────────────────────────────────────────────
let _battleState = {
  active: false,
  bid: null,
  defender_uid: null,
  defender_name: '',
  attacker_uids: [],
  attacker_name: '',
  elapsed_ms: 0,
  is_finished: false,
  defender_won: null,
  phase: 'waiting',
  time_since_start_s: 0,
  wave_info: null,
};

// ── Debug log ─────────────────────────────────────────────────
let _debugLogs = [];
const MAX_DEBUG_LOGS = 20;

function _addDebugLog(msg) {
  const timestamp = new Date().toLocaleTimeString();
  _debugLogs.unshift(`[${timestamp}] ${msg}`);
  if (_debugLogs.length > MAX_DEBUG_LOGS) _debugLogs.pop();
  console.log('[Battle.DEBUG]', msg);
  _updateDebugPanel();
}

function _updateDebugPanel() {
  const panel = container?.querySelector('#battle-debug-panel');
  if (!panel) return;
  panel.style.display = debug.enabled ? 'block' : 'none';
  if (!debug.enabled) return;
  const logList = panel.querySelector('#battle-debug-logs');
  if (logList)
    logList.innerHTML = _debugLogs
      .map(
        (log) =>
          `<div style="font-size:11px;padding:2px 0;font-family:monospace;color:#4a4">${log}</div>`
      )
      .join('');
}

// ── Era-dependent castle sprite ─────────────────────────────
function _updateCastleSprite(eraKey) {
  if (eraKey === _lastCastleEra) return;
  _lastCastleEra = eraKey;
  const url = _ERA_CASTLE_SPRITES[eraKey] || '/assets/sprites/bases/base.webp';
  registerTileType('castle', {
    label: 'Castle (Target)',
    color: '#4a4a1a',
    stroke: '#7a7a30',
    icon: null,
    spriteUrl: url,
  });
  if (grid) {
    grid._invalidateBase();
    grid._dirty = true;
  }
}

// ── Battle title ──────────────────────────────────────────────
function _setBattleTitle(label) {
  const titleEl = container?.querySelector('.battle-title');
  if (!titleEl) return;
  if (st?.summary) {
    _tickSummary = st.summary;
    _tickTs = Date.now();
    if (!_tickTimer) _tickTimer = setInterval(_tickResources, 1000);
  }
  const resources = st?.summary?.resources || {};
  titleEl.textContent = '';
  const labelSpan = document.createElement('span');
  labelSpan.textContent = label + ' ';
  const efxBtn = document.createElement('button');
  efxBtn.id = 'defense-effects-btn';
  efxBtn.className = 'prod-info-btn';
  efxBtn.title = 'Show defense effects';
  efxBtn.textContent = '🔍';
  labelSpan.appendChild(efxBtn);
  titleEl.appendChild(labelSpan);
  const resourceWrap = document.createElement('span');
  resourceWrap.className = 'title-resources';
  const goldEl = document.createElement('span');
  goldEl.className = 'title-gold';
  goldEl.textContent = '💰 ' + _fmtTitleResource(resources.gold);
  const cultureEl = document.createElement('span');
  cultureEl.className = 'title-culture';
  cultureEl.textContent = '🎭 ' + _fmtTitleResource(resources.culture);
  const lifeEl = document.createElement('span');
  lifeEl.className = 'title-life';
  const lifeIcon = document.createElement('span');
  lifeIcon.style.color = '#e05c5c';
  lifeIcon.textContent = '❤';
  lifeEl.append(lifeIcon, document.createTextNode(' ' + _fmtTitleResource(resources.life)));
  resourceWrap.append(goldEl, cultureEl, lifeEl);
  titleEl.append(resourceWrap);
}

// ── Defense Effects Overlay ─────────────────────────────────
function _defEffectRows(effectKey, completedBuildings, completedResearch, items, fmt, ownedArtifacts, rulerEffects) {
  const rows = [];
  for (const iid of completedBuildings || []) {
    const item = items?.buildings?.[iid];
    const val = item?.effects?.[effectKey];
    if (val)
      rows.push(`<div class="panel-row"><span class="label">${fmt(val)}</span><span class="value" style="color:#ccc">${item.name || iid}</span></div>`);
  }
  for (const iid of completedResearch || []) {
    const item = items?.knowledge?.[iid];
    const val = item?.effects?.[effectKey];
    if (val)
      rows.push(`<div class="panel-row"><span class="label">${fmt(val)}</span><span class="value" style="color:#ccc">${item.name || iid}</span></div>`);
  }
  for (const iid of ownedArtifacts || []) {
    const art = items?.catalog?.[iid];
    const val = art?.effects?.[effectKey];
    if (val)
      rows.push(`<div class="panel-row"><span class="label">${fmt(val)}</span><span class="value" style="color:#daa520">⚜ ${art.name || iid}</span></div>`);
  }
  const rulerVal = rulerEffects?.[effectKey];
  if (rulerVal)
    rows.push(`<div class="panel-row"><span class="label">${fmt(rulerVal)}</span><span class="value" style="color:#ffd54f">👑 Ruler</span></div>`);
  if (!rows.length)
    return `<div style="color:#555;font-size:0.85em;padding:2px 0">No items contribute yet</div>`;
  return rows.join('');
}

async function _showDefenseEffectsOverlay() {
  document.querySelector('.def-effects-overlay')?.remove();
  const summary = st.summary || {};
  const effects = summary.effects || {};
  const rulerName = summary.ruler?.name || '';

  const overlay = document.createElement('div');
  overlay.className = 'prod-overlay def-effects-overlay';
  overlay.innerHTML = `<div class="prod-overlay-box"><button class="prod-overlay-close" title="Close">✕</button><div style="color:#888;padding:20px">Loading…</div></div>`;
  overlay.addEventListener('click', (e) => {
    if (e.target === overlay || e.target.classList.contains('prod-overlay-close')) overlay.remove();
  });
  document.body.appendChild(overlay);

  let effectSources = {};
  try { effectSources = await rest.getEffectSources(); } catch (_) {}

  const siegeTotal = effects.siege_offset || 0;
  const waveTotal = effects.wave_delay_offset || 0;
  const restoreTotal = effects.restore_life_after_loss_offset || 0;
  const siegeModifier = effects.siege_time_modifier || 0;

  function section(icon, title, color, totalStr, rowsHtml) {
    return `<div class="prod-overlay-section"><div class="prod-overlay-title"><span style="color:${color}">${icon} ${title}</span></div>${rowsHtml}<div class="panel-row" style="border-top:1px solid #444;margin-top:6px;padding-top:6px"><span class="label" style="color:#ddd;font-weight:bold">Total</span><span class="value" style="color:#fff;font-weight:bold">${totalStr}</span></div></div>`;
  }

  function sectionNoTotal(icon, title, color, rowsHtml) {
    return `<div class="prod-overlay-section"><div class="prod-overlay-title"><span style="color:${color}">${icon} ${title}</span></div>${rowsHtml}</div>`;
  }

  const fmtDur = (s) => s >= 3600 ? (s / 3600).toFixed(1) + 'h' : s >= 60 ? Math.floor(s / 60) + 'm ' + Math.round(s % 60) + 's' : s.toFixed(0) + 's';

  const _items = st.items;
  function _name(iid) {
    return _items?.buildings?.[iid]?.name || _items?.knowledge?.[iid]?.name || _items?.catalog?.[iid]?.name || iid;
  }
  function sourceRows(key, fmt) {
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

  let siegeRows = sourceRows('siege_offset', (v) => `${v > 0 ? '+' : ''}${v.toFixed(0)}s`);
  siegeRows += '<div class="panel-row" style="border-top:1px solid #555;margin:6px 0;padding-top:6px"></div>';
  siegeRows += sourceRows('siege_time_modifier', (v) => `-${(v * 100).toFixed(0)}%`);
  const siegeFinal = siegeTotal * (1 - siegeModifier);
  siegeRows += '<div class="panel-row" style="border-top:1px solid #555;margin:6px 0;padding-top:6px"></div>';
  siegeRows += siegeModifier > 0
    ? `<div class="panel-row" style="color:#ffa726;font-weight:bold"><span class="label">= ${fmtDur(siegeTotal)} × ${((1 - siegeModifier) * 100).toFixed(0)}%</span><span class="value">${fmtDur(siegeFinal)}</span></div>`
    : `<div class="panel-row" style="color:#ffa726;font-weight:bold"><span class="label">= ${fmtDur(siegeTotal)}</span></div>`;

  const waveRows = sourceRows('wave_delay_offset', (v) => `+${(v / 1000).toFixed(1)}s`);
  const restoreRows = sourceRows('restore_life_after_loss_offset', (v) => `+${v.toFixed(1)} ❤`);
  const battleRegenMod = effects.restore_life_during_battle_modifier || 0;
  const battleRegenRows = sourceRows('restore_life_during_battle_modifier', (v) => `+${(v * 100).toFixed(0)}%`);

  const tiles = grid ? [...grid.tiles.values()] : [];
  const eraStatsHTML = `<div class="prod-overlay-section"><div class="prod-overlay-title"><span style="color:#9B59B6">🏰 Tower Era Distribution</span></div>${_buildEraStatsHTML(tiles)}</div>`;

  const box = overlay.querySelector('.prod-overlay-box');
  box.innerHTML = `
    <button class="prod-overlay-close" title="Close">✕</button>
    <div style="font-weight:bold;font-size:1.05em;margin-bottom:12px">🛡 Defense Effects</div>
    ${eraStatsHTML}
    ${sectionNoTotal('⏳', 'Siege Delay', '#ffa726', siegeRows)}
    ${section('🌊', 'Wave Delay', '#4fc3f7', `+${(waveTotal / 1000).toFixed(1)}s`, waveRows)}
    ${section('❤', 'Restore Life after Defeat', '#e05c5c', `+${restoreTotal.toFixed(1)}`, restoreRows)}
    ${section('❤️', 'Battle Life Regen', '#e05c5c', `+${battleRegenMod.toFixed(3)}/s extra while defending`, battleRegenRows)}
  `;
  box.addEventListener('click', (e) => {
    if (e.target.classList.contains('prod-overlay-close')) overlay.remove();
  });
}

// ── Map error helpers ─────────────────────────────────────────
let _mapErrorTimeout = null;

function _showMapError(msg) {
  const wrap = container.querySelector('#canvas-wrap');
  if (!wrap) return;
  let el = wrap.querySelector('.map-error-msg');
  if (!el) {
    el = document.createElement('div');
    el.className = 'map-error-msg';
    wrap.insertBefore(el, wrap.firstChild);
  }
  el.textContent = msg;
  el.style.opacity = '1';
  clearTimeout(_mapErrorTimeout);
  _mapErrorTimeout = setTimeout(() => {
    el.style.opacity = '0';
  }, 2500);
}

function _showPersistentError(msg) {
  clearTimeout(_mapErrorTimeout);
  _mapErrorTimeout = null;
  const wrap = container.querySelector('#canvas-wrap');
  if (!wrap) return;
  let el = wrap.querySelector('.map-error-msg');
  if (!el) {
    el = document.createElement('div');
    el.className = 'map-error-msg';
    wrap.insertBefore(el, wrap.firstChild);
  }
  el.textContent = msg;
  el.style.opacity = '1';
}

function _clearMapError() {
  clearTimeout(_mapErrorTimeout);
  _mapErrorTimeout = null;
  const wrap = container.querySelector('#canvas-wrap');
  if (!wrap) return;
  const el = wrap.querySelector('.map-error-msg');
  if (el) el.style.opacity = '0';
}

// ── Submodule instances (created in init) ─────────────────────
let _placement = null;
let _battleUi = null;
let _ws = null;

function _makePlacementCtx() {
  return {
    getGrid: () => grid,
    getContainer: () => container,
    getSt: () => st,
    getBattleState: () => _battleState,
    getSpectateUid: () => _spectateDefenderUid,
    getStructureEraRoman: () => _structureEraRoman,
    applyStructUpgrades: _applyStructUpgrades,
    showMapError: _showMapError,
    showPersistentError: _showPersistentError,
    clearMapError: _clearMapError,
    getTileType,
    rest,
  };
}

function _makeBattleUiCtx() {
  return {
    getGrid: () => grid,
    getContainer: () => container,
    getSt: () => st,
    getBattleState: () => _battleState,
    setBattleState: (obj) => {
      _battleState = obj;
    },
    getPendingAttackId: () => _pendingAttackId,
    getSpectateUid: () => _spectateDefenderUid,
    addDebugLog: _addDebugLog,
    acquireWakeLock: _acquireWakeLock,
    releaseWakeLock: _releaseWakeLock,
    showPersistentError: _showPersistentError,
    clearMapError: _clearMapError,
    setBattleTitle: _setBattleTitle,
    updateCastleSprite: _updateCastleSprite,
    rest,
    hexKey,
    placement: null, // set after _placement is created
  };
}

function _makeWsCtx() {
  return {
    getSt: () => st,
    getContainer: () => container,
    getPendingAttackId: () => _pendingAttackId,
    getSpectateUid: () => _spectateDefenderUid,
    getBattleState: () => _battleState,
    onMessage(msg) {
      if (!_battleUi) return;
      switch (msg.type) {
        case 'battle_setup':
          _battleUi.onBattleSetup(msg);
          break;
        case 'battle_update':
          _battleUi.onBattleUpdate(msg);
          break;
        case 'battle_summary':
          _battleUi.onBattleSummary(msg);
          break;
        case 'battle_status':
          _battleUi.onBattleStatus(msg);
          break;
        case 'structure_update':
          _battleUi.onStructureUpdate(msg);
          break;
      }
    },
    addDebugLog: _addDebugLog,
    updateBattleStatusVisibility(visible) {
      const info = container?.querySelector('#battle-status-info');
      if (info) info.style.display = visible ? 'contents' : 'none';
      requestAnimationFrame(_fitCanvas);
    },
    updateStatusFromBattleMsg: () => _battleUi?.updateStatusFromBattleMsg(),
    setBattlePhase: (phase) => {
      _battleState.phase = phase;
    },
    setPendingAttackId: (id) => {
      _pendingAttackId = id;
    },
  };
}

// ── Canvas helpers ────────────────────────────────────────────
function _fitCanvas() {
  const wrap = container.querySelector('#canvas-wrap');
  if (!wrap) return;
  const body = container.querySelector('.battle-view__body');
  if (!body) return;
  const topOffset = Math.round(body.getBoundingClientRect().top);
  const appStyle = getComputedStyle(document.getElementById('app') || document.body);
  const padBottom = parseFloat(appStyle.paddingBottom) || 0;
  wrap.style.height = `calc(100dvh - ${topOffset + padBottom}px)`;
  grid?._resize();
}

function _registerStructureTileTypes() {
  const items = st.items || {};
  const structures = items.structures || {};
  const catalog = items.catalog || {};

  const allStructureIids = new Set([
    ...Object.keys(structures),
    ...Object.entries(catalog)
      .filter(([, v]) => v.item_type === 'structure')
      .map(([iid]) => iid),
  ]);

  let colorIdx = 0;
  for (const iid of allStructureIids) {
    const info = structures[iid] || catalog[iid] || {};
    const colorDef = STRUCTURE_COLORS[colorIdx % STRUCTURE_COLORS.length];
    colorIdx++;
    registerTileType(iid, {
      label: info.name || iid,
      color: colorDef.color,
      stroke: colorDef.stroke,
      icon: null,
      spriteUrl: info.sprite ? '/' + info.sprite : null,
      serverData: info,
    });
  }

  if (grid) {
    grid._invalidateBase();
    grid._dirty = true;
  }
}

function _initCanvas() {
  const wrap = container.querySelector('#canvas-wrap');
  const canvas = container.querySelector('#battle-canvas');

  grid = new HexGrid({
    canvas,
    cols: 6,
    rows: 6,
    hexSize: 28,
    onTileClick: (q, r, tile) => {
      const tileData = tile || grid.getTile(q, r);
      const isOnPath = grid.battlePath?.some((p) => p.q === q && p.r === r);
      const inBattle = _battleState.phase === 'in_battle';

      const isTower =
        tileData &&
        !['void', 'empty', 'path', 'castle', 'spawnpoint'].includes(tileData.type) &&
        !isOnPath;
      if (isTower) {
        const isMobile = window.innerWidth <= 1100;
        const rangeActive =
          grid.rangeOverlay && grid.rangeOverlay.q === q && grid.rangeOverlay.r === r;
        _setRangeOverlay(q, r, tileData);
        if (isMobile && !rangeActive) {
          // Mobile first tap: range circle only
          return;
        }
        // Desktop: always fall through to show details in side panel
        // Mobile second tap: fall through to open overlay
      }

      if (isOnPath) {
        grid.rangeOverlay = null;
        grid._dirty = true;
        if (inBattle) {
          _showTileDetails(q, r, { type: 'path' });
        } else if (tileData?.type === 'castle' || tileData?.type === 'spawnpoint') {
          _showTileDetails(q, r, tileData);
        } else if (tileData?.type === 'empty' && _spectateDefenderUid == null) {
          _placement?.openPlacementMenu(q, r);
        }
        return;
      }

      if (!tileData || tileData.type === 'void') {
        grid.rangeOverlay = null;
        grid._dirty = true;
        _showTileDetails(q, r, tileData);
        return;
      }
      if (tileData.type === 'castle' || tileData.type === 'spawnpoint') {
        grid.rangeOverlay = null;
        grid._dirty = true;
        if (!inBattle) _showTileDetails(q, r, tileData);
        return;
      }
      if (tileData.type === 'empty') {
        grid.rangeOverlay = null;
        grid._dirty = true;
        if (_spectateDefenderUid == null) _placement?.openPlacementMenu(q, r);
        return;
      }

      _showTileDetails(q, r, tileData);
    },
    onTileHover: null,
    onTileDrop: null,
  });

  const updateSize = () => {
    const rect = wrap.getBoundingClientRect();
    canvas.style.width = rect.width + 'px';
    canvas.style.height = rect.height + 'px';
    grid._resize();
  };
  updateSize();
  window.addEventListener('resize', updateSize);
  _unsub.push(() => window.removeEventListener('resize', updateSize));
}

// ── Tower tile details overlay ────────────────────────────────
function _showTileDetails(q, r, tile) {
  const overlayBody = container.querySelector('#tower-overlay-body');
  const overlay = container.querySelector('#tower-overlay');
  const propsContent = container.querySelector('#tower-props-content');

  if (!tile) return;

  const t = getTileType(tile.type);
  const _isDefender = _spectateDefenderUid == null;

  // void tile — buy option
  if (tile.type === 'void') {
    const tilePrice = st.summary?.tile_price || 0;
    const currentGold = st.summary?.resources?.gold || 0;
    const canAfford = currentGold >= tilePrice;
    const buyHTML =
      '<div class="props-tile">' +
      '<div class="props-row"><span class="label">Type</span><span class="value">Void</span></div>' +
      (_isDefender
        ? '<div class="props-divider"></div>' +
          '<div class="props-row"><span class="label">Cost</span><span class="value" style="color:' +
          (canAfford ? 'var(--text)' : 'var(--danger)') +
          '">💰 ' +
          Math.round(tilePrice) +
          ' Gold</span></div>' +
          '<button id="buy-tile-btn" class="btn" style="width:100%;margin-top:8px;"' +
          (canAfford ? '' : ' disabled title="Not enough gold"') +
          '>Buy Tile</button>' +
          '<div id="buy-tile-msg" style="margin-top:6px;font-size:12px;text-align:center;"></div>'
        : '') +
      '</div>';

    if (propsContent) propsContent.innerHTML = buyHTML;
    if (overlayBody) {
      overlayBody.innerHTML = buyHTML;
      if (window.innerWidth <= 1100) overlay.style.display = 'flex';
    }

    const buyHandler = async (btnEl, msgEl) => {
      btnEl.disabled = true;
      msgEl.textContent = '';
      try {
        const resp = await rest.buyTile(q, r);
        if (resp.success) {
          msgEl.textContent = '✓ Tile purchased!';
          msgEl.style.color = 'var(--success)';
          await rest.getSummary();
          const response = await rest.loadMap();
          if (response && response.tiles) {
            grid.fromJSON({ tiles: response.tiles });
            grid.addVoidNeighbors();
            const path = response.path ? response.path.map(([q, r]) => ({ q, r })) : null;
            grid.setDisplayPath(path);
            grid._dirty = true;
          }
          if (overlay) overlay.style.display = 'none';
        } else {
          msgEl.textContent = '✗ ' + (resp.error || 'Failed to buy tile');
          msgEl.style.color = 'var(--danger)';
          btnEl.disabled = false;
        }
      } catch (err) {
        msgEl.textContent = '✗ ' + err.message;
        msgEl.style.color = 'var(--danger)';
        btnEl.disabled = false;
      }
    };
    [propsContent, overlayBody].forEach((root) => {
      if (!root) return;
      const b = root.querySelector('#buy-tile-btn');
      const m = root.querySelector('#buy-tile-msg');
      if (b && m) b.addEventListener('click', () => buyHandler(b, m));
    });
    return;
  }

  // Tower tile info
  let towerInfo = '';
  let _goldCost;
  if (t.serverData) {
    const s = _applyStructUpgrades(t.serverData, tile.type);
    _goldCost = s.costs?.gold;
    const _currentGold = st.summary?.resources?.gold || 0;
    const _costColor = _goldCost && _currentGold < _goldCost ? 'var(--danger)' : 'var(--text)';
    const _tileSelect = (tile && tile.select) || s.select || 'first';
    const _selectLabels = { first: '▶ First', last: '◀ Last', random: '⁇ Random' };
    const _selectBtns = _isDefender
      ? ['first', 'last', 'random']
          .map(
            (v) =>
              `<button class="btn select-btn${_tileSelect === v ? ' select-btn--active' : ''}" data-select="${v}" style="flex:1;padding:3px 0;font-size:11px;">${_selectLabels[v]}</button>`
          )
          .join('')
      : `<span style="font-size:11px;color:var(--muted,#888)">${_selectLabels[_tileSelect]}</span>`;
    const _spriteThumb = t.spriteUrl
      ? '<div class="props-sprite-thumb" style="text-align:center;margin:6px 0 4px"><span style="display:inline-block;width:56px;height:56px;border-radius:6px;background:' +
        t.color +
        ';border:1px solid ' +
        t.stroke +
        ';background-image:url(' +
        t.spriteUrl +
        ');background-size:contain;background-repeat:no-repeat;background-position:center;"></span></div>'
      : '';
    let _efxHtml = '';
    if (s.effects && Object.keys(s.effects).length > 0) {
      const _efxParts = [];
      const ef = s.effects;
      if (ef.burn_duration || ef.burn_dps)
        _efxParts.push(
          '<span>🔥 ' +
            ((ef.burn_duration || 0) / 1000).toFixed(2) +
            's @ ' +
            parseFloat((ef.burn_dps || 0).toFixed(2)) +
            ' dps</span>'
        );
      if (ef.slow_duration || ef.slow_ratio != null)
        _efxParts.push(
          '<span>❄ ' +
            ((ef.slow_duration || 0) / 1000).toFixed(2) +
            's @ ' +
            Math.round((ef.slow_ratio || 0) * 100) +
            '% speed</span>'
        );
      if (ef.splash_radius) _efxParts.push('<span>💥 ' + ef.splash_radius + ' hex</span>');
      Object.entries(ef).forEach(([k, v]) => {
        if (
          !['burn_duration', 'burn_dps', 'slow_duration', 'slow_ratio', 'splash_radius'].includes(k)
        ) {
          _efxParts.push(
            '<span>' + k + ': ' + (typeof v === 'number' ? parseFloat(v.toFixed(2)) : v) + '</span>'
          );
        }
      });
      _efxHtml =
        '<div class="props-row effects-row"><span class="label">Effects</span><span class="value effects-list">' +
        _efxParts.join('') +
        '</span></div>';
    }
    const _upgLevels = st.summary?.item_upgrades?.[tile.type] ?? {};
    const _totalUpgLvl = Object.values(_upgLevels).reduce((a, b) => a + b, 0);
    const _upgLabel =
      _totalUpgLvl > 0
        ? ` <span style="font-size:10px;color:#c9a84c;margin-left:4px">⬆ Lv ${_totalUpgLvl}</span>`
        : '';
    towerInfo =
      _spriteThumb +
      '<div class="props-divider"></div>' +
      '<div class="props-section-label">Tower Stats' +
      _upgLabel +
      '</div>' +
      (_goldCost
        ? '<div class="props-row"><span class="label">Cost</span><span class="value" style="color:' +
          _costColor +
          '">💰 ' +
          Math.round(_goldCost).toLocaleString() +
          ' Gold</span></div>'
        : '') +
      '<div class="props-row"><span class="label">Damage</span><span class="value">' +
      (s.damage || 0).toFixed(2) +
      '</span></div>' +
      '<div class="props-row"><span class="label">Range</span><span class="value">🎯 ' +
      (s.range || 0).toFixed(2) +
      ' hex</span></div>' +
      '<div class="props-row"><span class="label">Reload</span><span class="value">' +
      ((s.reload_time_ms || 0) / 1000).toFixed(2) +
      ' s</span></div>' +
      _efxHtml +
      '<div class="props-divider"></div>' +
      '<div class="props-section-label">Target Select</div>' +
      '<div id="select-btns" style="display:flex;gap:4px;margin-top:4px;">' +
      _selectBtns +
      '</div>';
  } else if (!['path', 'castle', 'spawnpoint', 'empty'].includes(tile.type)) {
    return;
  }

  const detailsHTML =
    '<div class="props-tile">' +
    '<div class="props-row"><span class="label">Type</span><span class="value">' +
    '<span class="palette-swatch--sm" style="background:' +
    t.color +
    ';border-color:' +
    t.stroke +
    '"></span>' +
    t.label +
    '</span></div>' +
    towerInfo +
    (_isDefender &&
    tile.type !== 'path' &&
    !(_battleState.phase === 'in_battle' && (tile.type === 'castle' || tile.type === 'spawnpoint'))
      ? '<div class="props-divider"></div>' +
        '<button id="empty-tile-btn" class="btn btn-danger" style="width:100%;margin-top:4px;">🗑 Empty Tile' +
        (_goldCost ? ' (💰 ' + Math.round(_goldCost * ((st.summary?.tower_sell_refund ?? 0.3) + (st.summary?.effects?.tower_sell_refund_modifier ?? 0))).toLocaleString() + ' refund)' : '') +
        '</button>'
      : '') +
    '</div>';

  if (propsContent) propsContent.innerHTML = detailsHTML;
  if (overlayBody) {
    overlayBody.innerHTML = detailsHTML;
    const _hasContent = towerInfo || tile.type !== 'empty';
    if (window.innerWidth <= 1100 && _hasContent) overlay.style.display = 'flex';
  }

  const _doEmpty = () => {
    grid.setTile(q, r, 'empty');
    _placement?.checkPathAndSave();
    if (overlay) overlay.style.display = 'none';
    if (propsContent) propsContent.innerHTML = '';
  };

  const _bindSelectBtns = (root) => {
    if (!root) return;
    root.querySelectorAll('.select-btn').forEach((btn) => {
      btn.addEventListener('click', () => {
        const val = btn.dataset.select;
        const tileData = grid.getTile(q, r);
        if (tileData) {
          tileData.select = val === 'first' ? undefined : val;
          grid._dirty = true;
          _ws?.send({ type: 'set_structure_select', hex_q: q, hex_r: r, select: val });
          _placement?.autoSave();
        }
        root.querySelectorAll('.select-btn').forEach((b) => {
          b.classList.toggle('select-btn--active', b.dataset.select === val);
        });
      });
    });
  };

  [propsContent, overlayBody].forEach((root) => {
    if (!root) return;
    const b = root.querySelector('#empty-tile-btn');
    if (b) b.addEventListener('click', _doEmpty);
    _bindSelectBtns(root);
  });
}

// ── Mobile visibility lifecycle ─────────────────────────────
function _onVisibilityChange() {
  if (document.visibilityState === 'hidden') {
    if (_ws?.isConnected()) {
      _addDebugLog('📱 Screen off → closing WS');
      _ws.disconnect();
    }
  } else if (document.visibilityState === 'visible') {
    if (!_ws?.isConnected()) {
      _addDebugLog('📱 Screen on → reconnecting WS');
      _ws?.connectIfNeeded();
    }
  }
}

function _setRangeOverlay(q, r, tileData) {
  if (!grid) return;
  const t = getTileType(tileData.type);
  const s = t.serverData ? _applyStructUpgrades(t.serverData, tileData.type) : null;
  const range = s?.range ?? 0;
  if (range > 0) {
    grid.rangeOverlay = { q, r, radius: range };
  } else {
    grid.rangeOverlay = null;
  }
  grid._dirty = true;
}

async function _loadMapBackground() {
  try {
    const res = await fetch('/api/maps');
    if (!res.ok) return;
    const { maps } = await res.json();
    if (maps && maps.length > 0 && grid) await grid.setMapBackground(maps[0].url);
  } catch (e) {
    console.warn('[Battle] map background not loaded:', e.message);
  }
}

// ── View lifecycle ──────────────────────────────────────────
function init(el, _api, _state) {
  container = el;
  st = _state;

  // Create submodule instances
  _placement = createPlacement(_makePlacementCtx());
  const buiCtx = _makeBattleUiCtx();
  _battleUi = createBattleUi(buiCtx);
  buiCtx.placement = _placement; // inject after both created
  _ws = createBattleWs(_makeWsCtx());
  // Expose rest for ws.js (it uses window._restModule as fallback)
  window._restModule = rest;

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

  container.innerHTML = `
    <div class="battle-view">
      <h2 class="battle-title">⚔ Defense<span class="title-resources"><span class="title-gold"></span><span class="title-culture"></span><span class="title-life"></span></span></h2>

      <div class="battle-status" id="battle-status">
        <div id="battle-status-info" style="display:none;grid-column:1/-1;display:none;">
        <div class="battle-status__item" style="grid-column: 1 / -1;">
          <div style="display:flex; justify-content:space-between; align-items:center; width:100%">
            <div><span class="label">Defender</span> <span class="value" id="battle-defender" style="color:var(--accent)">-</span></div>
            <div style="text-align:right"><span class="label">Attacker</span> <span class="value" id="battle-attacker" style="color:var(--danger)">-</span></div>
          </div>
        </div>
        <div class="battle-status__item" style="grid-column: 1 / -1;">
          <div style="display:flex; justify-content:space-between; align-items:center; width:100%">
            <div><span class="label">Status</span> <span class="value" id="battle-status-text">Waiting...</span></div>
            <div style="text-align:right"><span class="label">Time</span> <span class="value" id="battle-elapsed">00:00</span></div>
          </div>
        </div>
        <div class="battle-status__item" style="grid-column: 1 / -1;">
          <div style="display:flex; justify-content:space-between; align-items:center; width:100%">
            <span class="label">Next Wave</span><span class="value" id="battle-next-wave">-</span>
          </div>
        </div>
        </div>
        <div class="battle-status__item" id="fight-now-item" style="display:none;grid-column: 1 / -1;">
          <button id="fight-now-btn" style="width:100%;background:var(--danger,#e53935);border:none;color:#fff;padding:8px 16px;border-radius:var(--radius,4px);font-size:1em;font-weight:bold;cursor:pointer;letter-spacing:0.5px;">⚔ Fight now!</button>
        </div>
      </div>

      <div id="map-error-banner" style="display:none;padding:6px 12px;margin:0;background:#8a3a3a;color:#ffcccc;border-left:4px solid #c85a5a;border-radius:2px;font-size:0.85rem;flex-shrink:0;"></div>
      <div class="battle-view__body">
        <div class="battle-canvas-wrap" id="canvas-wrap">
          <button id="map-save" style="display:none;position:absolute;top:8px;right:8px;z-index:10;font-size:11px;padding:3px 10px;" title="Save path layout">💾 Save</button>
          <canvas id="battle-canvas"></canvas>
        </div>
        <aside class="battle-view__props" id="tower-props">
          <div class="panel">
            <div class="panel-header">Tower Details</div>
            <div id="tower-props-content" class="props-empty">Click a tower to inspect</div>
          </div>
        </aside>
      </div>

      <div class="battle-summary-overlay" id="battle-summary" style="display:none;">
        <div class="battle-summary-card">
          <h3 id="summary-title">Battle Complete</h3>
          <div id="summary-content"></div>
          <button id="summary-close" class="btn-primary">Close</button>
        </div>
      </div>

      <div class="tile-place-menu" id="tile-place-menu" style="display:none;">
        <div class="tile-place-menu__content">
          <div class="tile-place-menu__header">
            <span>Place Tower</span>
            <button class="tile-overlay__close" id="tile-place-close">✕</button>
          </div>
          <div class="tpm-items" id="tpm-items"></div>
        </div>
      </div>

      <div class="tile-overlay" id="tower-overlay" style="display:none;">
        <div class="tile-overlay__content">
          <div class="tile-overlay__header">
            <h3>Tower Details</h3>
            <button class="tile-overlay__close" id="tower-overlay-close">✕</button>
          </div>
          <div class="tile-overlay__body" id="tower-overlay-body"></div>
        </div>
      </div>

      <div id="battle-debug-panel" style="position:absolute;bottom:12px;right:12px;width:300px;background:rgba(0,0,0,0.85);border:1px solid #4a4;border-radius:4px;padding:8px;max-height:200px;overflow-y:auto;z-index:999;">
        <div style="font-size:12px;font-weight:bold;color:#4a4;margin-bottom:4px;">⚙ Battle Debug</div>
        <div id="battle-debug-logs" style="font-family:monospace;color:#4a4;font-size:10px;"></div>
      </div>
    </div>
  `;

  container.addEventListener('click', (e) => {
    if (e.target.id === 'defense-effects-btn') _showDefenseEffectsOverlay();
  });

  container.querySelector('#summary-close').addEventListener('click', () => {
    container.querySelector('#battle-summary').style.display = 'none';
    window.location.hash = '#status';
  });

  container.querySelector('#fight-now-btn').addEventListener('click', async () => {
    const btn = container.querySelector('#fight-now-btn');
    btn.disabled = true;
    btn.style.opacity = '0.5';
    if (!_pendingAttackId) return;
    btn.textContent = 'Sending...';
    try {
      const resp = await rest.skipSiege(_pendingAttackId);
      if (resp.success) {
        btn.textContent = '✓ Siege ended!';
        setTimeout(() => {
          btn.textContent = '⚔ Fight now!';
          btn.disabled = false;
          btn.style.opacity = '';
        }, 3000);
      } else {
        btn.textContent = `✗ ${resp.error || 'Error'}`;
        setTimeout(() => {
          btn.textContent = '⚔ Fight now!';
          btn.disabled = false;
          btn.style.opacity = '';
        }, 2500);
      }
    } catch (err) {
      btn.textContent = '✗ Request failed';
      setTimeout(() => {
        btn.textContent = '⚔ Fight now!';
        btn.disabled = false;
      }, 2500);
    }
  });

  container.querySelector('#map-save').addEventListener('click', () => _placement?.saveMap());

  const placeMenu = container.querySelector('#tile-place-menu');
  container.querySelector('#tile-place-close').addEventListener('click', () => {
    placeMenu.style.display = 'none';
  });
  placeMenu.addEventListener('click', (e) => {
    if (e.target === placeMenu) placeMenu.style.display = 'none';
  });

  const closeBtn = container.querySelector('#tower-overlay-close');
  const towerOverlay = container.querySelector('#tower-overlay');
  if (closeBtn)
    closeBtn.addEventListener('click', () => {
      towerOverlay.style.display = 'none';
    });
  if (towerOverlay)
    towerOverlay.addEventListener('click', (e) => {
      if (e.target === towerOverlay) towerOverlay.style.display = 'none';
    });

  const _onKeyDown = (e) => {
    if (e.key === 'Escape') {
      placeMenu.style.display = 'none';
      const overlay = container.querySelector('#tower-overlay');
      if (overlay) overlay.style.display = 'none';
    }
  };
  document.addEventListener('keydown', _onKeyDown);
  _unsub.push(() => document.removeEventListener('keydown', _onKeyDown));
}

async function enter() {
  _debugLogs = [];
  _updateDebugPanel();
  _initCanvas();
  requestAnimationFrame(_fitCanvas);

  _updateCastleSprite(st.summary?.current_era || 'stone');

  _battleState = {
    active: false,
    bid: null,
    defender_uid: null,
    defender_name: '',
    attacker_uids: [],
    attacker_name: '',
    elapsed_ms: 0,
    is_finished: false,
    defender_won: null,
    phase: 'waiting',
    time_since_start_s: 0,
    wave_info: null,
  };
  _battleUi.updateStatusFromBattleMsg();

  if (st.pendingSpectateAttack) {
    _pendingAttackId = st.pendingSpectateAttack.attack_id;
    _spectateDefenderUid = st.pendingSpectateAttack.defender_uid;
    st.pendingSpectateAttack = null;
  }
  if (st.pendingIncomingAttack) {
    _pendingAttackId = st.pendingIncomingAttack.attack_id;
    st.pendingIncomingAttack = null;
  }

  if (_pendingAttackId == null) {
    const incoming = st.summary?.attacks_incoming || [];
    const battleAttack = incoming.find((a) => a.phase === 'in_battle');
    if (battleAttack) {
      _pendingAttackId = battleAttack.attack_id;
    } else {
      const siegeAttacks = incoming.filter((a) => a.phase === 'in_siege');
      if (siegeAttacks.length > 0) {
        const soonest = siegeAttacks.reduce((a, b) =>
          (a.siege_time ?? Infinity) <= (b.siege_time ?? Infinity) ? a : b
        );
        _pendingAttackId = soonest.attack_id;
      } else if (incoming.length > 0) {
        const nearest = incoming.reduce((a, b) =>
          (a.eta_seconds ?? Infinity) <= (b.eta_seconds ?? Infinity) ? a : b
        );
        _pendingAttackId = nearest.attack_id;
      }
    }
  }

  _unsub.push(
    eventBus.on('state:items', () => {
      _buildStructureEraRoman();
      _registerStructureTileTypes();
    })
  );
  _unsub.push(
    eventBus.on('state:summary', (data) => {
      if (!_ws?.isConnected()) _ws?.connectIfNeeded();
      if (_spectateDefenderUid == null && data?.current_era) _updateCastleSprite(data.current_era);
      if (data && st?.summary) {
        _tickSummary = st.summary;
        _tickTs = Date.now();
      }
    })
  );

  try {
    const [, eraMap] = await Promise.all([rest.getItems(), rest.getEraMap()]);
    if (eraMap) {
      _structUpgDef = eraMap.structure_upgrade_def ?? null;
      _critUpgDef = eraMap.critter_upgrade_def ?? null;
    }
  } catch (err) {
    console.warn('[Battle] could not load items:', err.message);
  }

  _buildStructureEraRoman();
  _registerStructureTileTypes();

  if (_spectateDefenderUid != null) {
    const props = container.querySelector('#tower-props');
    if (props) props.style.display = 'none';
    const body = container.querySelector('.battle-view__body');
    if (body) body.style.gridTemplateColumns = '1fr';
    _setBattleTitle('👁 Spectating...');
  } else {
    const props = container.querySelector('#tower-props');
    if (props) props.style.display = '';
    const body = container.querySelector('.battle-view__body');
    if (body) body.style.gridTemplateColumns = '';
    _setBattleTitle('⚔ Defense');
    try {
      const response = await rest.loadMap();
      if (response && response.tiles) {
        grid.fromJSON({ tiles: response.tiles });
        grid.addVoidNeighbors();
        grid._centerGrid();
        const path = response.path ? response.path.map(([q, r]) => ({ q, r })) : null;
        grid.setDisplayPath(path);
        if (!path) {
          let hasSp = false,
            hasCa = false;
          for (const [, d] of grid.tiles) {
            if (d.type === 'spawnpoint') hasSp = true;
            if (d.type === 'castle') hasCa = true;
          }
          if (hasSp && hasCa) {
            _showPersistentError(
              '⚠️ Kein Pfad von Spawnpoint zu Castle — bitte Hindernisse entfernen.'
            );
            _placement?.markPathDirty();
          }
        } else {
          _clearMapError();
        }
      }
    } catch (err) {
      console.warn('[Battle] could not load map from server:', err.message);
    }
  }

  _ws?.connectIfNeeded();

  document.addEventListener('visibilitychange', _onVisibilityChange);
  _unsub.push(() => document.removeEventListener('visibilitychange', _onVisibilityChange));

  _battleUi.startStatusLoop();
  _loadMapBackground();
}

function leave() {
  _releaseWakeLock();
  const wrap = container.querySelector('#canvas-wrap');
  if (wrap) wrap.style.height = '';
  _unsub.forEach((fn) => fn());
  _unsub = [];
  _pendingAttackId = null;
  _spectateDefenderUid = null;
  _lastCastleEra = null;
  _placement?.cancelAutoSave();
  const menu = container?.querySelector('#tile-place-menu');
  if (menu) menu.style.display = 'none';
  if (grid) {
    grid.destroy();
    grid = null;
  }
  _battleUi.stopStatusLoop();
  if (_tickTimer) {
    clearInterval(_tickTimer);
    _tickTimer = null;
  }
  _tickSummary = null;
  _tickTs = null;
  _ws?.disconnect();
}

// ── Export ──────────────────────────────────────────────────
export default { id: 'defense', title: 'Defense', init, enter, leave };
