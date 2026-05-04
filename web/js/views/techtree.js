/**
 * Tech Tree view — interactive knowledge dependency graph.
 */

import { eventBus } from '../events.js';
import { rest } from '../rest.js';
import { ItemOverlay } from '../lib/item_overlay.js';
import { fmtEffort } from '../lib/format.js';
import { ERA_ROMAN, ERA_KEYS, ERA_YAML_TO_KEY, ERA_LABEL_EN } from '../lib/eras.js';

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
    <h2 class="battle-title">⬡ Tech Tree<span class="title-resources"><span class="title-gold"></span><span class="title-culture"></span><span class="title-life"></span></span></h2>
    <div id="tt-wrap">
      <div class="empty-state"><div class="empty-icon">◉</div><p>Loading tech tree…</p></div>
    </div>
  `;
  _overlay = new ItemOverlay(_state);
  _overlay.mount(container);
}

async function enter() {
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

function _buildKnowledgeGroups() {
  const catalog = st.items?.catalog || {};
  const groups = {};
  for (const era of ERA_KEYS) groups[era] = [];
  for (const [iid, info] of Object.entries(catalog)) {
    if (info.item_type !== 'knowledge') continue;
    const key = ERA_YAML_TO_KEY[info.era] || null;
    if (key) groups[key].push(iid);
  }
  return groups;
}

function _layoutNodes() {
  if (!st.items) return {};
  const eras = ERA_KEYS;
  const knowledgeGroups = _buildKnowledgeGroups();
  const catalog = st.items?.catalog || {};
  const result = {};

  for (const era of eras) {
    const iids = knowledgeGroups[era] || [];
    if (iids.length === 0) {
      result[era] = [];
      continue;
    }

    // All IIDs placed in previous eras
    const allPlaced = new Set();
    for (const prevEra of eras) {
      if (prevEra === era) break;
      for (const iid of knowledgeGroups[prevEra] || []) allPlaced.add(iid);
    }

    const placed = new Set();
    const remaining = new Map(iids.map((iid) => [iid, catalog[iid] || { requirements: [] }]));
    const rows = [];

    while (remaining.size > 0) {
      const ready = [];
      for (const [iid, info] of remaining) {
        const reqs = (info.requirements || []).filter(
          (r) => r in catalog && catalog[r]?.item_type === 'knowledge'
        );
        const satisfied = reqs.every((r) => placed.has(r) || allPlaced.has(r));
        if (satisfied) ready.push(iid);
      }

      if (ready.length === 0) {
        ready.push(...remaining.keys());
      }

      // Sort by catalog order (stable)
      ready.sort((a, b) => iids.indexOf(a) - iids.indexOf(b));

      for (let i = 0; i < ready.length; i += 3) {
        rows.push(ready.slice(i, i + 3));
      }

      for (const iid of ready) {
        placed.add(iid);
        remaining.delete(iid);
      }
    }

    result[era] = rows;
  }

  return result;
}

/* ── Format helpers ──────────────────────────────────────── */

const _fmtEffort = fmtEffort;

function _fmtEffects(effects) {
  if (!effects || Object.keys(effects).length === 0) return '';
  return Object.entries(effects)
    .map(([k, v]) => {
      const sign = v > 0 ? '+' : '';
      if (k === 'gold_offset') {
        return `💰 ${sign}${v.toLocaleString('de-DE', { maximumFractionDigits: 1 })}/h`;
      }
      if (k === 'culture_offset') {
        return `🎭 ${sign}${v.toLocaleString('de-DE', { maximumFractionDigits: 1 })}/h`;
      }
      const name = k.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
      if (Math.abs(v) < 1) return `${name}: ${sign}${(v * 100).toFixed(0)}%`;
      return `${name}: ${sign}${v}`;
    })
    .join(', ');
}

/* ── Render (full DOM build — only on init or items change) ── */

let _rendered = false;

function render() {
  if (!st.items || !st.summary) return;

  _unlocksMap = _buildUnlocksMap();
  const layout = _layoutNodes();

  const wrap = container.querySelector('#tt-wrap');
  const eras = ERA_KEYS;
  const labels = ERA_LABEL_EN;
  const catalog = st.items.catalog || {};
  const knowledge = st.items.knowledge || {};

  let html = '<svg class="tt-svg" id="tt-svg"></svg><div id="tt-content">';

  eras.forEach((era, eraIdx) => {
    const rows = layout[era];
    if (!rows || rows.length === 0) return;

    if (eraIdx > 0) {
      html += '<div class="tt-era-divider"></div>';
    }

    html += `<div class="tt-era tt-era-bg-${eraIdx}" data-era="${era}">`;
    html += `<div class="tt-era-label">
      <span class="tt-era-roman">${ERA_ROMAN[era] || ''}</span>
      <span class="tt-era-name">${labels[era] || era}</span>
    </div>`;

    for (const row of rows) {
      html += '<div class="tt-row">';
      for (const iid of row) {
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

        html += `<div class="tt-node" data-iid="${iid}">
          <div class="tt-node-name" title="${iid}"><span class="tt-status-icon"></span>${name}</div>
          ${effort != null ? `<div class="tt-node-effort">⏱ ${_fmtEffort(effort)}</div>` : ''}
          ${effectsStr ? `<div class="tt-node-effects">✦ ${effectsStr}</div>` : ''}
          <div class="tt-node-locked" style="display:none">🔒</div>
          ${unlocksHtml}
        </div>`;
      }
      html += '</div>';
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

  // Draw connectors after DOM settles
  requestAnimationFrame(() => requestAnimationFrame(_drawConnectors));

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

function _updateStatus() {
  if (!_rendered || !st.summary) return;

  const knowledge = st.items?.knowledge || {};
  const completed = new Set([
    ...(st.summary.completed_research || []),
    ...(st.summary.completed_buildings || []),
  ]);
  const researchQueue = st.summary.research_queue;

  const catalog = st.items?.catalog || {};

  container.querySelectorAll('.tt-node').forEach((node) => {
    const iid = node.dataset.iid;
    const avail = knowledge[iid];
    const isCompleted = completed.has(iid);
    const isResearching = iid === researchQueue;
    const isAvailable = !!avail;
    const isLocked = !isCompleted && !isResearching && !isAvailable;

    // Update status class
    node.classList.toggle('tt-completed', isCompleted);
    node.classList.toggle('tt-researching', isResearching);
    node.classList.toggle('tt-available', isAvailable && !isCompleted && !isResearching);
    node.classList.toggle('tt-locked', isLocked);

    // Update status icon
    const icon = node.querySelector('.tt-status-icon');
    if (icon) icon.textContent = isResearching ? '🔬 ' : isCompleted ? '✓ ' : '';

    // Update lock indicator
    const lock = node.querySelector('.tt-node-locked');
    if (lock) lock.style.display = isLocked ? '' : 'none';

    // Update unlock badges: ready (all reqs met if this tech is researched) vs blocked
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
  _resizeTimer = setTimeout(_drawConnectors, 150);
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
