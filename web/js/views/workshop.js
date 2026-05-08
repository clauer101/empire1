/**
 * Workshop — per-stat upgrade shop for researched towers and critters.
 *
 * Data sources:
 *   state.summary  → resources.gold, completed_buildings, completed_research, item_upgrades
 *   state.items    → catalog (ItemDetails per IID)
 *   rest.getEraMap()  → structure_upgrade_def, critter_upgrade_def, labels_de
 */

import { rest } from '../rest.js';
import { state } from '../state.js';
import { eventBus } from '../events.js';

// ── Module state ──────────────────────────────────────────────
let _container = null;
let _selectedIid = null;
let _tab = 'structures'; // 'structures' | 'critters'
let _itemUpgrades = {}; // iid → { stat → level }
let _upgradeDefs = null; // { structure_upgrade_def, critter_upgrade_def }
let _eraLabels = {}; // era_key → German label
let _iidEraIndex = {}; // iid → era index 0–8
let _unsubSummary = null;
let _unsubItems = null;
let _gridScroll = { structures: 0, critters: 0 };
let _selectedByTab = { structures: null, critters: null };

// ── Stat definitions ──────────────────────────────────────────
const STRUCTURE_STATS = [
  { key: 'damage', label: 'Damage', unit: '' },
  { key: 'range', label: 'Range', unit: 'hex' },
  { key: 'reload', label: 'Reload Speed', unit: '%' },
  { key: 'effect_duration', label: 'Effect Duration', unit: 's' },
  { key: 'effect_value', label: 'Effect Value', unit: '%' },
];
const CRITTER_STATS = [
  { key: 'health', label: 'Health', unit: '' },
  { key: 'speed', label: 'Speed', unit: 'hex/s' },
  { key: 'armour', label: 'Armour', unit: '' },
];

// ── Helpers ───────────────────────────────────────────────────

function _gold() {
  return state.summary?.resources?.gold ?? 0;
}

function _fmtRes(val, digits = 0) {
  const v = val ?? 0;
  return v >= 1000
    ? Math.floor(v / 1000) + 'k'
    : Math.floor(v * Math.pow(10, digits)) / Math.pow(10, digits);
}

function _fillTitleResources() {
  if (!_container) return;
  const r = state.summary?.resources;
  if (!r) return;
  _container.querySelectorAll('.title-gold').forEach((el) => {
    el.textContent = '💰 ' + _fmtRes(r.gold);
  });
  _container.querySelectorAll('.title-culture').forEach((el) => {
    el.textContent = '🎭 ' + _fmtRes(r.culture);
  });
  _container.querySelectorAll('.title-life').forEach((el) => {
    el.innerHTML = '<span style="color:#e05c5c">❤</span> ' + _fmtRes(r.life, 0);
  });
}

function _catalog() {
  return state.items?.catalog ?? {};
}

/** IIDs that are fully completed (buildings + research → unlocks structures/critters) */
function _completedSet() {
  return new Set([
    ...(state.summary?.completed_buildings ?? []),
    ...(state.summary?.completed_research ?? []),
  ]);
}

/** All non-boss critters the player has unlocked (requirements met) */
function _unlockedCritters() {
  const catalog = _catalog();
  const completed = _completedSet();
  return Object.entries(catalog)
    .filter(([, info]) => {
      if (info.item_type !== 'critter') return false;
      if (info.is_boss) return false;
      const reqs = info.requirements ?? [];
      return reqs.every((r) => completed.has(r));
    })
    .map(([iid]) => iid)
    .reverse();
}

/** All structures the player has built at least once */
function _unlockedStructures() {
  const catalog = _catalog();
  const completed = _completedSet();
  return Object.keys(catalog)
    .filter((iid) => {
      const info = catalog[iid];
      if (info.item_type !== 'structure') return false;
      const reqs = info.requirements ?? [];
      return reqs.every((r) => completed.has(r));
    })
    .reverse();
}

// Maps item.era (YAML string) → era index 0–8, matching ERA_ITEM_TO_INDEX in Python
const _ERA_ITEM_TO_INDEX = {
  STONE_AGE: 0,
  NEOLITHIC: 1,
  BRONZE_AGE: 2,
  IRON_AGE: 3,
  MEDIEVAL: 4,
  RENAISSANCE: 5,
  INDUSTRIAL: 6,
  MODERN: 7,
  FUTURE: 8,
};

function _calcPrice(iid) {
  const eraIdx = _iidEraIndex[iid] ?? 0;
  const costs = _upgradeDefs?.item_upgrade_base_costs ?? [];
  const baseCost = costs[eraIdx] ?? costs[costs.length - 1] ?? 0;
  const iidUpgrades = _itemUpgrades[iid] ?? {};
  const totalLevels = Object.values(iidUpgrades).reduce((a, b) => a + b, 0);
  // Quadratic scaling: base * (totalLevels + 1)^2
  return Math.round(baseCost * Math.pow(totalLevels + 1, 2) * 10) / 10;
}

// Maps calcKey → def key in upgradeDefs (when they differ)
const _DEF_KEY_MAP = { slow_value: 'effect_value' };

function _currentValue(baseVal, stat, level, defs) {
  if (!defs || level === 0) return baseVal;
  const defKey = _DEF_KEY_MAP[stat] ?? stat;
  const bonusPerLevel = defs[defKey] ?? 0;
  if (stat === 'reload') {
    // Reload time decreases via division (matches defense.js and battle_service)
    return baseVal / (1 + (bonusPerLevel / 100) * level);
  }
  return baseVal * (1 + (bonusPerLevel / 100) * level);
}

function _fmtVal(val) {
  return val.toFixed(2);
}

function _perLevelText(stat, defs) {
  if (!defs) return '';
  const v = defs[stat];
  if (v == null) return '';
  return `+${v}% /lvl`;
}

// ── Render helpers ────────────────────────────────────────────

function _statRows(iid, statDefs, upgradeDefs) {
  const catalog = _catalog();
  const item = catalog[iid] ?? {};
  const iidUpgrades = _itemUpgrades[iid] ?? {};
  const gold = _gold();
  const price = _calcPrice(iid);
  const canAfford = gold >= price && price > 0;

  const efx = item.effects ?? {};
  const hasSlow = 'slow_duration' in efx;
  const hasBurn = 'burn_duration' in efx;
  const hasSplash = 'splash_radius' in efx;

  return statDefs
    .map(({ key, label, unit }) => {
      let displayLabel = label;
      let displayBase;
      let displayUnit = unit;
      let calcKey = key; // used for _currentValue direction; key stays as API stat name

      if (key === 'reload') {
        displayBase = (item.reload_time_ms ?? 0) / 1000;
        displayUnit = 's';
      } else if (key === 'effect_duration') {
        if (hasSlow) {
          displayLabel = 'Slow Duration';
          displayBase = (efx.slow_duration ?? 0) / 1000;
          displayUnit = 's';
        } else if (hasBurn) {
          displayLabel = 'Burn Duration';
          displayBase = (efx.burn_duration ?? 0) / 1000;
          displayUnit = 's';
        } else return null; // no duration effect → skip row
      } else if (key === 'effect_value') {
        if (hasSplash) {
          displayLabel = 'Splash Radius';
          displayBase = efx.splash_radius ?? 0;
          displayUnit = 'hex';
        } else if (hasSlow) {
          displayLabel = 'Slow Effect';
          displayBase = efx.slow_ratio ?? 0;
          displayUnit = '';
          calcKey = 'slow_value';
        } else if (hasBurn) {
          displayLabel = 'Burn DPS';
          displayBase = efx.burn_dps ?? 0;
          displayUnit = '';
        } else return null; // no value effect → skip row
      } else {
        displayBase = item[key] ?? 0;
      }

      const level = iidUpgrades[key] ?? 0;
      const curVal = _currentValue(displayBase, calcKey, level, upgradeDefs);
      const hasBase = displayBase > 0;

      const btnColor = canAfford ? '#c9a84c' : 'var(--danger, #e53935)';
      const btnStyle = `
      background:transparent;color:${btnColor};
      border:1px solid ${btnColor};border-radius:var(--radius,4px);
      padding:2px 10px;font-size:12px;cursor:${canAfford ? 'pointer' : 'not-allowed'};
      opacity:${canAfford ? '1' : '0.6'};white-space:nowrap;flex-shrink:0;
    `.replace(/\s+/g, ' ');

      return `
      <tr class="ws-stat-row" data-stat="${key}" data-iid="${iid}">
        <td style="padding:6px 8px;color:var(--text-dim,#888);font-size:13px;">${displayLabel}</td>
        <td style="padding:6px 8px;font-size:13px;text-align:right;">${hasBase ? _fmtVal(curVal) + ' ' + displayUnit : '—'}</td>
        <td style="padding:6px 8px;font-size:13px;text-align:center;color:#c9a84c;font-weight:bold;">${level}</td>
        <td style="padding:6px 8px;font-size:13px;text-align:right;color:#7ec8a4;">${hasBase ? _fmtVal(_currentValue(displayBase, calcKey, level + 1, upgradeDefs)) + ' ' + displayUnit : '—'}</td>
        <td style="padding:6px 8px;text-align:right;">
          ${price > 0 ? `<button class="ws-upgrade-btn" data-stat="${key}" data-iid="${iid}" style="${btnStyle}" ${canAfford ? '' : 'disabled'}>💰${price.toFixed(2)}</button>` : `<span style="font-size:11px;color:var(--text-dim,#888);">—</span>`}
        </td>
      </tr>`;
    })
    .filter(Boolean)
    .join('');
}

function _renderDetail_html(iid) {
  const catalog = _catalog();
  const item = catalog[iid];
  if (!item) return '<div style="padding:32px;color:var(--text-dim,#888);">Item not found.</div>';

  const isStructure = item.item_type === 'structure';
  const statDefs = isStructure ? STRUCTURE_STATS : CRITTER_STATS;
  const upgradeDefs = isStructure
    ? _upgradeDefs?.structure_upgrade_def
    : _upgradeDefs?.critter_upgrade_def;

  const eraLabel = _eraLabels[item.era] ?? item.era ?? '';
  const iidUpgrades = _itemUpgrades[iid] ?? {};
  const totalLevels = Object.values(iidUpgrades).reduce((a, b) => a + b, 0);

  const spritePath = item.sprite ? '/' + item.sprite : null;
  const thumbHtml = isStructure
    ? spritePath
      ? `<img src="${spritePath}" alt="${item.name ?? iid}"
               style="width:72px;height:72px;object-fit:contain;border-radius:8px;
                      background:rgba(255,255,255,0.04);padding:4px;"
               onerror="this.style.display='none'">`
      : ''
    : `<canvas class="ws-critter-canvas" width="72" height="72"
               data-iid="${iid}" ${spritePath ? `data-sprite="${spritePath}"` : ''}
               style="border-radius:8px;background:rgba(255,255,255,0.04);"></canvas>`;

  return `
    <div style="padding:20px 24px;">
      <div style="display:flex;align-items:flex-start;gap:20px;margin-bottom:20px;">
        ${thumbHtml}
        <div>
          <div style="font-size:18px;font-weight:bold;margin-bottom:4px;">${item.name ?? iid}</div>
          <div style="font-size:12px;color:var(--text-dim,#888);margin-bottom:6px;">${eraLabel}</div>
          ${
            totalLevels > 0
              ? `<div style="font-size:12px;background:rgba(201,168,76,0.15);color:#c9a84c;padding:2px 8px;border-radius:12px;display:inline-block;">⬆ ${totalLevels} upgrade${totalLevels !== 1 ? 's' : ''}</div>`
              : `<div style="font-size:12px;color:var(--text-dim,#888);">No upgrades yet</div>`
          }
        </div>
      </div>

      <table style="width:100%;border-collapse:collapse;">
        <thead>
          <tr style="border-bottom:1px solid rgba(255,255,255,0.08);">
            <th style="padding:4px 8px;text-align:left;font-size:11px;color:var(--text-dim,#888);font-weight:normal;">Stat</th>
            <th style="padding:4px 8px;text-align:right;font-size:11px;color:var(--text-dim,#888);font-weight:normal;">Current</th>
            <th style="padding:4px 8px;text-align:center;font-size:11px;color:var(--text-dim,#888);font-weight:normal;">Lvl</th>
            <th style="padding:4px 8px;text-align:right;font-size:11px;color:var(--text-dim,#888);font-weight:normal;">Next</th>
            <th style="padding:4px 8px;text-align:right;font-size:11px;color:var(--text-dim,#888);font-weight:normal;">Upgrade</th>
          </tr>
        </thead>
        <tbody>
          ${_statRows(iid, statDefs, upgradeDefs)}
        </tbody>
      </table>

    </div>`;
}

function _itemGridHtml(iids, isStructure) {
  const catalog = _catalog();
  if (iids.length === 0) {
    return `<div style="padding:24px 16px;color:var(--text-dim,#888);font-size:13px;">Nothing unlocked yet.</div>`;
  }
  return (
    `<div style="display:flex;flex-wrap:nowrap;gap:8px;padding:10px;">` +
    iids
      .map((iid) => {
        const item = catalog[iid] ?? {};
        const iidUpgrades = _itemUpgrades[iid] ?? {};
        const totalLevels = Object.values(iidUpgrades).reduce((a, b) => a + b, 0);
        const isSelected = iid === _selectedIid;
        const spritePath = item.sprite ? '/' + item.sprite : null;

        const thumbHtml = isStructure
          ? spritePath
            ? `<img src="${spritePath}" alt="" style="width:48px;height:48px;object-fit:contain;" onerror="this.style.display='none'">`
            : `<div style="width:48px;height:48px;background:rgba(255,255,255,0.06);border-radius:4px;"></div>`
          : `<canvas class="ws-critter-canvas" width="48" height="48"
                   data-iid="${iid}" ${spritePath ? `data-sprite="${spritePath}"` : ''}></canvas>`;

        return `
        <div class="ws-item-row" data-iid="${iid}" style="
          position:relative;cursor:pointer;border-radius:8px;padding:8px;width:80px;
          background:${isSelected ? 'rgba(201,168,76,0.15)' : 'rgba(255,255,255,0.04)'};
          border:1px solid ${isSelected ? 'rgba(201,168,76,0.5)' : 'rgba(255,255,255,0.08)'};
          transition:background 0.1s;text-align:center;flex-shrink:0;">
          <div style="display:flex;justify-content:center;margin-bottom:5px;">${thumbHtml}</div>
          <div style="font-size:10px;line-height:1.2;overflow:hidden;display:-webkit-box;
               -webkit-line-clamp:2;-webkit-box-orient:vertical;color:${isSelected ? '#c9a84c' : 'inherit'};">
            ${item.name ?? iid}
          </div>
          ${
            totalLevels > 0
              ? `<div style="position:absolute;top:3px;right:4px;font-size:9px;
            background:rgba(201,168,76,0.25);color:#c9a84c;padding:0 4px;border-radius:8px;">⬆${totalLevels}</div>`
              : ''
          }
        </div>`;
      })
      .join('') +
    `</div>`
  );
}

const _SPRITE_EXTS = ['.webp'];

function _initCanvases(el) {
  el.querySelectorAll('.ws-critter-canvas').forEach((canvas) => {
    const drawFrame = (img) => {
      const ctx = canvas.getContext('2d');
      const fw = img.width / 4,
        fh = img.height / 4;
      const scale = Math.min(canvas.width / fw, canvas.height / fh);
      const dx = Math.floor((canvas.width - fw * scale) / 2);
      const dy = Math.floor((canvas.height - fh * scale) / 2);
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.drawImage(img, 0, 0, fw, fh, dx, dy, fw * scale, fh * scale);
    };

    if (canvas.dataset.sprite) {
      const img = new Image();
      img.onload = () => drawFrame(img);
      img.onerror = () => {
        canvas.style.display = 'none';
      };
      img.src = canvas.dataset.sprite;
      return;
    }

    const iid = canvas.dataset.iid.toLowerCase();
    const base = `assets/sprites/critters/${iid}/${iid}`;
    const tryLoad = (idx) => {
      if (idx >= _SPRITE_EXTS.length) {
        canvas.style.display = 'none';
        return;
      }
      const img = new Image();
      img.onload = () => drawFrame(img);
      img.onerror = () => tryLoad(idx + 1);
      img.src = base + _SPRITE_EXTS[idx];
    };
    tryLoad(0);
  });
}

function _renderDetail() {
  if (!_container || !_selectedIid) return;
  const detailEl = _container.querySelector('#ws-detail');
  if (!detailEl) return;
  detailEl.innerHTML = _renderDetail_html(_selectedIid);
  requestAnimationFrame(() => _initCanvases(detailEl));
  detailEl.querySelectorAll('.ws-upgrade-btn').forEach((btn) => {
    btn.addEventListener('click', _onUpgradeClick);
  });
}

function _render() {
  if (!_container) return;

  const structureIids = _unlockedStructures();
  const critterIids = _unlockedCritters();
  const iids = _tab === 'structures' ? structureIids : critterIids;

  // Ensure selected IID is valid for current tab
  if (_selectedIid && !iids.includes(_selectedIid)) _selectedIid = null;
  if (!_selectedIid && iids.length > 0) _selectedIid = iids[0];

  const tabBtn = (id, label, active) => `
    <button class="ws-tab" data-tab="${id}"
      style="padding:6px 16px;font-size:13px;cursor:pointer;
             background:${active ? 'rgba(201,168,76,0.15)' : 'transparent'};
             color:${active ? '#c9a84c' : 'var(--text-dim,#888)'};
             border:1px solid ${active ? 'rgba(201,168,76,0.4)' : 'rgba(255,255,255,0.1)'};
             border-radius:var(--radius,4px);transition:all 0.15s;">
      ${label} (${id === 'structures' ? structureIids.length : critterIids.length})
    </button>`;

  _container.innerHTML = `
    <h2 class="battle-title">⚙ Workshop
      <span class="title-resources"><span class="title-gold"></span><span class="title-culture"></span><span class="title-life"></span></span>
    </h2>
    <div style="padding:8px 16px 4px;display:flex;gap:8px;flex-shrink:0;border-bottom:1px solid rgba(255,255,255,0.08);">
      ${tabBtn('structures', '🛡 Towers', _tab === 'structures')}
      ${tabBtn('critters', '⚔ Critters', _tab === 'critters')}
    </div>
    <div style="display:flex;flex-direction:column;flex:1;min-height:0;overflow:hidden;">
      <!-- Item grid (top, horizontal scroll) -->
      <div class="ws-grid-scroller" style="flex-shrink:0;overflow-x:auto;overflow-y:hidden;
                  border-bottom:1px solid rgba(255,255,255,0.08);">
        ${_itemGridHtml(iids, _tab === 'structures')}
      </div>

      <!-- Detail panel (below, fills remaining space) -->
      <div id="ws-detail" style="flex:1;overflow-y:auto;">
        ${
          _selectedIid
            ? _renderDetail_html(_selectedIid)
            : `
          <div style="padding:32px;color:var(--text-dim,#888);font-size:13px;">
            Select an item above.
          </div>`
        }
      </div>
    </div>`;

  // Restore scroll position for current tab
  const newScroller = _container.querySelector('.ws-grid-scroller');
  if (newScroller) newScroller.scrollLeft = _gridScroll[_tab] ?? 0;

  _fillTitleResources();
  _bindEvents();
  requestAnimationFrame(() => _initCanvases(_container));
}

function _bindEvents() {
  if (!_container) return;

  _container.querySelectorAll('.ws-tab').forEach((btn) => {
    btn.addEventListener('click', () => {
      const scroller = _container.querySelector('.ws-grid-scroller');
      if (scroller) _gridScroll[_tab] = scroller.scrollLeft;
      _selectedByTab[_tab] = _selectedIid;
      _tab = btn.dataset.tab;
      _selectedIid = _selectedByTab[_tab];
      _render();
    });
  });

  _container.querySelectorAll('.ws-item-row').forEach((row) => {
    row.addEventListener('click', () => {
      const scroller = _container.querySelector('.ws-grid-scroller');
      if (scroller) _gridScroll[_tab] = scroller.scrollLeft;
      _selectedIid = row.dataset.iid;
      _selectedByTab[_tab] = _selectedIid;
      _render();
    });
  });

  _container.querySelectorAll('.ws-upgrade-btn').forEach((btn) => {
    btn.addEventListener('click', _onUpgradeClick);
  });
}

async function _onUpgradeClick(e) {
  const btn = e.currentTarget;
  const iid = btn.dataset.iid;
  const stat = btn.dataset.stat;
  if (!iid || !stat) return;

  btn.disabled = true;
  btn.textContent = '…';

  try {
    const resp = await rest.buyItemUpgrade(iid, stat);
    if (resp.success) {
      // Update local upgrade state from response
      _itemUpgrades = resp.item_upgrades ?? _itemUpgrades;
      if (state.summary) {
        state.summary.resources = state.summary.resources ?? {};
        if (resp.gold != null) {
          state.summary.resources.gold = resp.gold;
        } else {
          state.summary.resources.gold = (state.summary.resources.gold ?? 0) - (resp.cost ?? 0);
        }
        state.summary.item_upgrades = _itemUpgrades;
      }
      _render();
    } else {
      btn.disabled = false;
      btn.textContent = resp.error ?? 'Error';
      setTimeout(() => _renderDetail(), 1500);
    }
  } catch (err) {
    btn.disabled = false;
    btn.textContent = 'Error';
    setTimeout(() => _renderDetail(), 1500);
  }
}

// ── View lifecycle ────────────────────────────────────────────

function init(el, _api, _state) {
  _container = el;
}

async function enter() {
  _unsubSummary = eventBus.on('state:summary', () => {
    _itemUpgrades = state.summary?.item_upgrades ?? _itemUpgrades;
    _renderDetail();
  });
  _unsubItems = eventBus.on('state:items', () => _render());

  // Load data in parallel
  const [, , eraMap] = await Promise.all([rest.getSummary(), rest.getItems(), rest.getEraMap()]);

  // Pick up item_upgrades from summary
  _itemUpgrades = state.summary?.item_upgrades ?? {};
  _upgradeDefs = eraMap ?? null;
  _eraLabels = eraMap?.labels_de ?? {};

  // Build iid → era index from era-map groups
  _iidEraIndex = {};
  const ERA_KEYS = eraMap?.eras ?? [];
  for (const cat of ['structures', 'critters']) {
    const groups = eraMap?.[cat] ?? {};
    for (const [eraKey, iids] of Object.entries(groups)) {
      const idx = ERA_KEYS.indexOf(eraKey);
      if (idx < 0) continue;
      for (const iid of iids) _iidEraIndex[iid] = idx;
    }
  }

  _render();
}

function leave() {
  if (_unsubSummary) {
    _unsubSummary();
    _unsubSummary = null;
  }
  if (_unsubItems) {
    _unsubItems();
    _unsubItems = null;
  }
  _selectedIid = null;
}

export default { id: 'workshop', title: 'Workshop', init, enter, leave };
