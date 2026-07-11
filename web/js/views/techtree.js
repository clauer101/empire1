/**
 * Tech Tree view — interactive knowledge dependency graph.
 */

import { eventBus } from '../events.js';
import { pageTitle } from '../lib/page_title.js';
import { rest } from '../rest.js';
import { ItemOverlay } from '../lib/item_overlay.js';
import { fmtEffort, fmtEffectsInline } from '../lib/format.js';
import { ERA_ROMAN, ERA_KEYS, ERA_YAML_TO_KEY, ERA_LABEL_EN } from '../lib/eras.js';
import { escHtml } from '../lib/html.js';

/** @type {import('../state.js').StateStore} */
let st;
/** @type {HTMLElement} */
let container;
let _unsub = [];
/** @type {ItemOverlay} */
let _overlay = null;

/* ── Cached data ─────────────────────────────────────────── */

let _unlocksMap = {}; // reverse dependency map

const _isTouchDevice = window.matchMedia('(pointer: coarse)').matches;
let _activeNode = null;

/* ── Lifecycle ───────────────────────────────────────────── */

function init(el, _api, _state) {
  container = el;
  st = _state;

  container.innerHTML = `
    <div id="tt-wrap">
      <div class="empty-state"><div class="empty-icon">◉</div><p>Loading tech tree…</p></div>
    </div>
  `;
  _overlay = new ItemOverlay(_state);
  _overlay.mount(container);
}

async function enter() {
  if (!((st.summary?.effects?.enable_techtree ?? 0) > 0)) {
    pageTitle.set('⬡ Tech Tree');
    container.innerHTML = `<div class="empty-state"><div class="empty-icon">🔒</div>
      <p>The Tech Tree unlocks once your empire reaches a certain size.<br>
      Keep building and researching to unlock it.</p></div>`;
    return;
  }
  pageTitle.set('⬡ Tech Tree');
  _unsub.push(eventBus.on('state:summary', _updateStatus));
  _unsub.push(eventBus.on('state:items', render));

  // Click outside node/overlay clears highlight
  _clickHandler = (e) => {
    if (!_activeNode) return;
    if (e.target.closest('.tt-node') || e.target.closest('.tt-overlay')) return;
    _clearHighlight();
    _activeNode = null;
  };
  document.addEventListener('click', _clickHandler);

  try {
    await Promise.all([rest.getSummary(), rest.getItems()]);
    render();
  } catch (err) {
    container.querySelector('#tt-wrap').innerHTML = `<div class="error-msg">${err.message}</div>`;
  }
}

let _clickHandler = null;

function leave() {
  _unsub.forEach((fn) => fn());
  _unsub = [];
  _activeNode = null;
  _rendered = false;
  if (_overlay) _overlay.hide();
  if (_clickHandler) {
    document.removeEventListener('click', _clickHandler);
    _clickHandler = null;
  }
  window.removeEventListener('resize', _resizeHandler);
  clearTimeout(_resizeTimer);
  _resizeTimer = null;
}

/* ── Build reverse-requirement map ───────────────────────── */

function _buildUnlocksMap() {
  const map = {};
  const catalog = st.items?.catalog || {};
  for (const [iid, info] of Object.entries(catalog)) {
    for (const req of info.requirements || []) {
      if (!map[req]) map[req] = [];
      map[req].push({ iid, name: info.name || iid, category: info.item_type || 'knowledge' });
    }
  }
  return map;
}

/* ── Layout: topological sort within each era ────────────── */

const _BRANCHES = ['main', 'left', 'right'];

function _buildKnowledgeGroups() {
  const catalog = st.items?.catalog || {};
  const groups = {};
  for (const era of ERA_KEYS) groups[era] = { main: [], left: [], right: [] };
  for (const [iid, info] of Object.entries(catalog)) {
    if (info.item_type !== 'knowledge') continue;
    const key = ERA_YAML_TO_KEY[info.era] || null;
    if (!key) continue;
    const branch = _BRANCHES.includes(info.branch) ? info.branch : 'main';
    groups[key][branch].push(iid);
  }
  return groups;
}

/**
 * Assign each in-era knowledge item a vertical depth = the longest chain of
 * knowledge requirements leading to it, counting only requirements placed in
 * the SAME era (across all branches). Items whose requirements all live in
 * earlier eras get depth 0. This is what makes a branch item (e.g. a `left`
 * node) sit one row below its `main`-column requirement instead of being
 * pulled up to row 0. Returns a Map iid -> depth.
 */
function _eraDepths(eraIids, catalog) {
  const inEra = new Set(eraIids);
  const depth = new Map();
  const computing = new Set();
  const depthOf = (iid) => {
    if (depth.has(iid)) return depth.get(iid);
    if (computing.has(iid)) return 0; // cycle guard (shouldn't happen)
    computing.add(iid);
    const reqs = (catalog[iid]?.requirements || []).filter(
      (r) => inEra.has(r) && catalog[r]?.item_type === 'knowledge'
    );
    const d = reqs.length === 0 ? 0 : Math.max(...reqs.map((r) => depthOf(r) + 1));
    computing.delete(iid);
    depth.set(iid, d);
    return d;
  };
  for (const iid of eraIids) depthOf(iid);
  return depth;
}

function _layoutNodes() {
  if (!st.items) return {};
  const eras = ERA_KEYS;
  const knowledgeGroups = _buildKnowledgeGroups();
  const catalog = st.items?.catalog || {};
  const result = {};

  for (const era of eras) {
    const eraIids = [
      ...knowledgeGroups[era].main,
      ...knowledgeGroups[era].left,
      ...knowledgeGroups[era].right,
    ];
    const depths = _eraDepths(eraIids, catalog);
    const maxDepth = eraIids.length ? Math.max(...eraIids.map((iid) => depths.get(iid))) : -1;

    // Per branch, bucket items by their era-global depth. Each bucket is the
    // full set of items at that depth (main may hold several; left/right one).
    // A shared grid then renders one row per depth so all three columns of a
    // given level share the same row height and stay vertically aligned.
    const byDepth = { main: [], left: [], right: [] };
    for (const branch of _BRANCHES) {
      const iids = knowledgeGroups[era][branch] || [];
      const buckets = [];
      for (let d = 0; d <= maxDepth; d++) buckets.push([]);
      for (const iid of iids) buckets[depths.get(iid)].push(iid);
      for (const level of buckets) level.sort((a, b) => iids.indexOf(a) - iids.indexOf(b));
      byDepth[branch] = buckets;
    }

    result[era] = { maxDepth, byDepth, depths };
  }

  return result;
}

/* ── Format helpers ──────────────────────────────────────── */

const _fmtEffort = fmtEffort;

const _fmtEffects = fmtEffectsInline;

/* ── Render (full DOM build — only on init or items change) ── */

let _rendered = false;
let _lastRenderedMobile = false;

function _nodeHtml(iid, catalog, knowledge) {
  const catInfo = catalog[iid] || {};
  const avail = knowledge[iid];
  const name = avail?.name || catInfo.name || iid;
  const effort = avail?.effort;
  const effects = avail?.effects;
  const effectsStr = _fmtEffects(effects);

  const unlocks = _unlocksMap[iid] || [];
  let unlocksHtml = '';
  if (unlocks.length > 0) {
    unlocksHtml =
      '<div class="tt-unlocks">' +
      unlocks
        .map(
          (u) =>
            `<span class="tt-ubadge tt-cat-${u.category}" data-unlock="${u.iid}" title="${u.iid}">${u.name}</span>`
        )
        .join('') +
      '</div>';
  }

  const branchLabel = catInfo.branch && catInfo.branch !== 'main' ? `${catInfo.branch_label || 'optional'} branch` : '';

  return `<div class="tt-node" data-iid="${iid}">
    <div class="tt-node-name" title="${iid}"><span class="tt-status-icon"></span>${name}${avail?.advances_era ? '<span class="badge badge--era-advance" title="Completing this item advances your empire to a new era">⬆</span>' : ''}</div>
    ${branchLabel ? `<div class="tt-node-branch" style="font-size:0.7em;color:#4fc3f7;font-weight:600;">${escHtml(branchLabel)}</div>` : ''}
    ${effort != null ? `<div class="tt-node-effort">⏱ ${_fmtEffort(effort)}</div>` : ''}
    ${effectsStr ? `<div class="tt-node-effects">✦ ${effectsStr}</div>` : ''}
    <div class="tt-node-locked" style="display:none">🔒</div>
    ${unlocksHtml}
  </div>`;
}

/**
 * Render an era as a 3-column CSS grid (left | main | right) with one grid row
 * per depth level. Because all three cells of a level share the same grid row,
 * the grid stretches that row to the tallest node in it, keeping branch nodes
 * aligned with the main-column node they depend on — no fixed-height guessing.
 */
// Visual left-to-right column order of the grid (differs from _BRANCHES,
// which lists `main` first for layout bucketing).
const _GRID_COLUMNS = ['left', 'main', 'right'];

const _GRID_COL_INDEX = { left: 1, main: 2, right: 3 };

function _eraGridHtml(eraLayout, catalog, knowledge) {
  const { maxDepth, byDepth } = eraLayout;
  let html = '<div class="tt-era-grid">';
  // Every cell is pinned to its (depth row, branch column) explicitly, so a
  // main cell that wraps internally cannot push later depth rows down for the
  // other columns — each depth level stays a single shared grid row.
  for (let d = 0; d <= maxDepth; d++) {
    for (const branch of _GRID_COLUMNS) {
      const cellIids = byDepth[branch][d] || [];
      if (cellIids.length === 0) continue; // empty cells need no DOM node
      const col = _GRID_COL_INDEX[branch];
      const style = `grid-row:${d + 1};grid-column:${col}`;
      html += `<div class="tt-cell tt-cell-${branch}" style="${style}">`;
      for (const iid of cellIids) html += _nodeHtml(iid, catalog, knowledge);
      html += '</div>';
    }
  }
  html += '</div>';
  return html;
}

const _MOBILE_BREAKPOINT = 700;
function _isMobileLayout() {
  return window.innerWidth <= _MOBILE_BREAKPOINT;
}

/**
 * Mobile layout: same era-global depth model as desktop, but with no separate
 * left/right columns — every item (branch items included) is treated exactly
 * like a main item and sorted by catalog order within its depth level. Each
 * depth level is one row laid out as a 3-column grid.
 */
function _mobileEraHtml(eraLayout, catalog, knowledge) {
  const { maxDepth, byDepth } = eraLayout;
  if (maxDepth < 0) return '';

  let html = '<div class="tt-mobile-flow">';
  for (let d = 0; d <= maxDepth; d++) {
    const level = [...byDepth.left[d], ...byDepth.main[d], ...byDepth.right[d]];
    if (level.length === 0) continue;
    html += '<div class="tt-mobile-level">';
    for (const iid of level) html += _nodeHtml(iid, catalog, knowledge);
    html += '</div>';
  }
  html += '</div>';
  return html;
}

function render() {
  if (!st.items || !st.summary) return;

  _unlocksMap = _buildUnlocksMap();
  const layout = _layoutNodes();

  const wrap = container.querySelector('#tt-wrap');
  const eras = ERA_KEYS;
  const labels = ERA_LABEL_EN;
  const catalog = st.items.catalog || {};
  const knowledge = st.items.knowledge || {};
  const mobile = _isMobileLayout();
  _lastRenderedMobile = mobile;

  let html = '<svg class="tt-svg" id="tt-svg"></svg><div id="tt-content">';

  eras.forEach((era, eraIdx) => {
    const eraLayout = layout[era];
    const hasAny = eraLayout && eraLayout.maxDepth >= 0;
    if (!hasAny) return;

    if (eraIdx > 0) {
      html += '<div class="tt-era-divider"></div>';
    }

    html += `<div class="tt-era tt-era-bg-${eraIdx}" data-era="${era}">`;
    html += `<div class="tt-era-label">
      <span class="tt-era-roman">${ERA_ROMAN[era] || ''}</span>
      <span class="tt-era-name">${labels[era] || era}</span>
    </div>`;

    if (mobile) {
      html += _mobileEraHtml(eraLayout, catalog, knowledge);
    } else {
      html += _eraGridHtml(eraLayout, catalog, knowledge);
    }

    html += '</div>';
  });

  html += '</div>';
  wrap.innerHTML = html;

  // Bind node interactions (once)
  wrap.querySelectorAll('.tt-node').forEach((node) => {
    const iid = node.dataset.iid;

    node.addEventListener('mouseenter', () => {
      if (_isTouchDevice || _activeNode) return;
      _highlightChain(iid);
    });
    node.addEventListener('mouseleave', () => {
      if (_isTouchDevice || _activeNode) return;
      _clearHighlight();
    });
    node.addEventListener('click', (e) => {
      e.stopPropagation();
      if (_isTouchDevice) {
        if (_activeNode === iid) {
          _overlay.show(iid);
        } else {
          _clearHighlight();
          _activeNode = iid;
          _highlightChain(iid);
        }
      } else {
        _highlightChain(iid);
        _activeNode = iid;
        _overlay.show(iid);
      }
    });
  });

  // Draw connectors after layout has settled. The desktop grid keeps branch
  // nodes aligned with their requirement structurally, so no margin pass runs.
  requestAnimationFrame(() =>
    requestAnimationFrame(() => {
      _drawConnectors();
    })
  );

  // Resize handler
  clearTimeout(_resizeTimer);
  _resizeTimer = null;
  window.removeEventListener('resize', _resizeHandler);
  window.addEventListener('resize', _resizeHandler);

  _rendered = true;

  // Apply current status
  _updateStatus();

  // Scroll to the player's current era
  _scrollToCurrentEra();
}

/* ── Status update (lightweight — no DOM rebuild) ────────── */

function _buildExcludedSet(completed, catalog) {
  const excluded = new Set();
  for (const compIid of completed) {
    for (const excl of (catalog[compIid]?.excludes || [])) {
      excluded.add(excl);
    }
  }
  for (const [iid, info] of Object.entries(catalog)) {
    if (!completed.has(iid)) {
      for (const excl of (info.excludes || [])) {
        if (completed.has(excl)) excluded.add(iid);
      }
    }
  }
  return excluded;
}

function _updateStatus() {
  if (!_rendered || !st.summary) return;

  const knowledge = st.items?.knowledge || {};
  const completed = new Set([
    ...(st.summary.completed_research || []),
    ...(st.summary.completed_buildings || []),
  ]);
  const researchQueue = st.summary.research_queue;
  const catalog = st.items?.catalog || {};
  const excluded = _buildExcludedSet(completed, catalog);

  container.querySelectorAll('.tt-node').forEach((node) => {
    const iid = node.dataset.iid;
    const avail = knowledge[iid];
    const isCompleted = completed.has(iid);
    const isExcluded = !isCompleted && excluded.has(iid);
    const isResearching = iid === researchQueue;
    const isAvailable = !!avail && !isExcluded;
    const isLocked = !isCompleted && !isExcluded && !isResearching && !isAvailable;

    node.classList.toggle('tt-completed', isCompleted);
    node.classList.toggle('tt-excluded', isExcluded);
    node.classList.toggle('tt-researching', isResearching);
    node.classList.toggle('tt-available', isAvailable && !isCompleted && !isResearching);
    node.classList.toggle('tt-locked', isLocked);

    const icon = node.querySelector('.tt-status-icon');
    if (icon) icon.textContent = isResearching ? '🔬 ' : isCompleted ? '✓ ' : isExcluded ? '✕ ' : '';

    const lock = node.querySelector('.tt-node-locked');
    if (lock) lock.style.display = isLocked ? '' : 'none';

    const hypothetical = new Set([...completed, iid]);
    node.querySelectorAll('.tt-ubadge[data-unlock]').forEach((badge) => {
      const uInfo = catalog[badge.dataset.unlock];
      const allMet = (uInfo?.requirements || []).every((r) => hypothetical.has(r));
      badge.classList.toggle('tt-ubadge-ready', allMet);
      badge.classList.toggle('tt-ubadge-blocked', !allMet);
    });
  });

}


function _scrollToCurrentEra() {
  const era = st.summary?.current_era;
  if (!era) return;
  const eraEl = container.querySelector(`.tt-era[data-era="${era}"]`);
  if (!eraEl) return;
  requestAnimationFrame(() => {
    eraEl.scrollIntoView({ behavior: 'smooth', block: 'start' });
  });
}

let _resizeTimer = null;
function _resizeHandler() {
  clearTimeout(_resizeTimer);
  _resizeTimer = setTimeout(() => {
    if (_isMobileLayout() !== _lastRenderedMobile) {
      render();
    } else {
      _drawConnectors();
    }
  }, 150);
}

/* ── SVG Connectors ──────────────────────────────────────── */

function _drawConnectors() {
  const svg = container.querySelector('#tt-svg');
  const wrap = container.querySelector('#tt-wrap');
  if (!svg || !wrap) return;

  const wrapRect = wrap.getBoundingClientRect();
  svg.setAttribute('width', wrap.scrollWidth);
  svg.setAttribute('height', wrap.scrollHeight);
  svg.innerHTML = '';

  const catalog = st.items?.catalog || {};
  const nodePos = {};

  wrap.querySelectorAll('.tt-node').forEach((el) => {
    if (el.style.display === 'none') return;
    const rect = el.getBoundingClientRect();
    nodePos[el.dataset.iid] = {
      cx: rect.left + rect.width / 2 - wrapRect.left + wrap.scrollLeft,
      top: rect.top - wrapRect.top + wrap.scrollTop,
      bottom: rect.bottom - wrapRect.top + wrap.scrollTop,
    };
  });

  // Draw lines from requirement → dependent
  for (const [iid, pos] of Object.entries(nodePos)) {
    const info = catalog[iid];
    if (!info) continue;
    for (const req of info.requirements || []) {
      const source = nodePos[req];
      if (!source) continue;
      const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
      line.setAttribute('x1', source.cx);
      line.setAttribute('y1', source.bottom);
      line.setAttribute('x2', pos.cx);
      line.setAttribute('y2', pos.top);
      line.dataset.from = req;
      line.dataset.to = iid;
      svg.appendChild(line);
    }
  }
}

/* ── Highlight ───────────────────────────────────────────── */

function _highlightChain(iid) {
  const catalog = st.items?.catalog || {};
  const connected = new Set([iid]);

  // Direct prerequisites
  const info = catalog[iid];
  for (const req of info?.requirements || []) {
    if (req in catalog && catalog[req]?.item_type === 'knowledge') connected.add(req);
  }

  // Direct successors
  for (const [kid, kInfo] of Object.entries(catalog)) {
    if (kInfo.item_type === 'knowledge' && (kInfo.requirements || []).includes(iid)) {
      connected.add(kid);
    }
  }

  container.querySelectorAll('.tt-node').forEach((el) => {
    if (connected.has(el.dataset.iid)) {
      el.classList.add('hl');
      el.classList.remove('dimmed');
    } else {
      el.classList.add('dimmed');
      el.classList.remove('hl');
    }
  });

  container.querySelectorAll('#tt-svg line').forEach((line) => {
    const directlyConnected = line.dataset.from === iid || line.dataset.to === iid;
    if (directlyConnected) {
      line.classList.add('hl');
      line.classList.remove('dimmed');
    } else {
      line.classList.add('dimmed');
      line.classList.remove('hl');
    }
  });
}

function _clearHighlight() {
  container.querySelectorAll('.tt-node.hl, .tt-node.dimmed').forEach((el) => {
    el.classList.remove('hl', 'dimmed');
  });
  container.querySelectorAll('#tt-svg line.hl, #tt-svg line.dimmed').forEach((line) => {
    line.classList.remove('hl', 'dimmed');
  });
}

export default {
  id: 'techtree',
  title: 'Tech Tree',
  init,
  enter,
  leave,
};
