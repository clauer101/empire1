/**
 * Empire Stats view — sortable leaderboard of battle statistics.
 * Same lazy-scroll approach as globalempires.js.
 */

import { rest } from '../rest.js';
import { pageTitle } from '../lib/page_title.js';

/** @type {HTMLElement} */
let container;

let _empiresData = null;
let _sorted = null;
let _renderedStart = 0;
let _renderedEnd = 0;
let _savedScrollTop = -1;
let _sortKey = 'critters_killed';
let _sortDir = 'desc';

const INITIAL_WINDOW = 20;
const BATCH = 30;

const COLS = [
  { key: 'attacks_won_human',  label: 'Attacks Won',       fmt: fmtInt },
  { key: 'attacks_lost_human', label: 'Attacks Lost',      fmt: fmtInt },
  { key: 'defense_won_human',  label: 'Defense Won',       fmt: fmtInt },
  { key: 'defense_lost_human', label: 'Defense Lost',      fmt: fmtInt },
  { key: 'defense_won_ai',     label: 'Defense Won vs AI', fmt: fmtInt },
  { key: 'defense_lost_ai',    label: 'Defense Lost vs AI',fmt: fmtInt },
  { key: 'critters_killed',    label: 'Critters Killed',   fmt: fmtInt },
  { key: 'artifacts_stolen',   label: 'Artifacts Stolen',  fmt: fmtInt },
  { key: 'culture_won',        label: 'Culture Won',       fmt: fmtK   },
  { key: 'culture_stolen',     label: 'Culture Lost',      fmt: fmtK   },
  { key: 'research_won',       label: 'Research Won',      fmt: fmtK   },
  { key: 'research_stolen',    label: 'Research Lost',     fmt: fmtK   },
  { key: 'defense_gold_earned',label: 'Gold Earned',       fmt: fmtK   },
  { key: 'spies_sent',         label: 'Spies Sent',        fmt: fmtInt },
  { key: 'longest_battle_ms',  label: 'Longest Battle',    fmt: fmtMs  },
];

function fmtInt(v) {
  if (!v) return '—';
  return Number(v).toLocaleString();
}
function fmtK(v) {
  if (!v) return '—';
  const n = Number(v);
  if (n >= 1_000_000) return (n / 1_000_000).toFixed(1) + 'M';
  if (n >= 1_000) return (n / 1_000).toFixed(1) + 'k';
  return Math.round(n).toString();
}
function fmtMs(v) {
  if (!v) return '—';
  const s = Math.round(v / 1000);
  if (s < 60) return s + 's';
  const m = Math.floor(s / 60), r = s % 60;
  if (m < 60) return m + 'm' + (r ? ' ' + r + 's' : '');
  return Math.floor(m / 60) + 'h ' + (m % 60) + 'm';
}

function _sort(data) {
  const key = _sortKey;
  const dir = _sortDir === 'asc' ? 1 : -1;
  return [...data].sort((a, b) => {
    const av = a[key] ?? 0, bv = b[key] ?? 0;
    return av < bv ? -dir : av > bv ? dir : 0;
  });
}

// ── Init ─────────────────────────────────────────────────────────────────────

function init(el) {
  container = el;
  container.style.cssText = 'display:flex;flex-direction:column;height:100%;overflow-x:hidden;';
}

async function enter() {
  pageTitle.set('📊 Empire Stats');
  document.getElementById('app')?.classList.add('full-bleed');
  const isFirstVisit = _savedScrollTop < 0;
  if (!_empiresData) _render(null);
  try {
    const resp = await rest.getEmpires();
    _empiresData = resp.empires || [];
    _sorted = _sort(_empiresData);
  } catch (e) {
    _renderError(e.message);
    return;
  }
  _render(_sorted, !isFirstVisit);
  if (!isFirstVisit) {
    const scrollEl = container.querySelector('#es-scroll');
    if (scrollEl) scrollEl.scrollTop = _savedScrollTop;
  }
  if (isFirstVisit) _savedScrollTop = 0;
}

function leave() {
  const scrollEl = container.querySelector('#es-scroll');
  if (scrollEl) _savedScrollTop = scrollEl.scrollTop;
  document.getElementById('app')?.classList.remove('full-bleed');
  _teardownScroll();
  _empiresData = null;
  _sorted = null;
}

// ── Row rendering ─────────────────────────────────────────────────────────────

function _rowHtml(e, rank) {
  const cells = COLS.map(col => {
    const v = col.fmt(e[col.key]);
    const active = col.key === _sortKey;
    return `<td style="text-align:center;padding:3px 6px;font-size:0.77em;white-space:nowrap;color:${active ? 'var(--accent,#4fc3f7)' : v === '—' ? '#444' : 'var(--text,#e0e0e6)'};">${v}</td>`;
  }).join('');
  const bg = e.is_self ? 'rgba(20,20,31,0.97)' : 'var(--bg,#0e0e1a)';
  const selfStyle = e.is_self ? 'background:rgba(255,255,255,0.06);' : '';
  return `<tr class="es-row${e.is_self ? ' es-self' : ''}" style="${selfStyle}">
    <td style="position:sticky;left:0;z-index:1;background:${bg};padding:3px 6px;white-space:nowrap;font-size:0.82em;">
      <span style="color:#666;font-size:0.85em;margin-right:4px;">${rank + 1}</span><span style="color:${e.is_self ? 'var(--accent,#4fc3f7)' : 'inherit'};max-width:120px;overflow:hidden;text-overflow:ellipsis;display:inline-block;vertical-align:bottom;">${e.name}${e.is_self ? ' ★' : ''}</span>
    </td>
    ${cells}
  </tr>`;
}

// ── Lazy scroll ───────────────────────────────────────────────────────────────

let _scrollEl = null;
let _onScroll = null;

function _teardownScroll() {
  if (_scrollEl && _onScroll) _scrollEl.removeEventListener('scroll', _onScroll);
  _scrollEl = null;
  _onScroll = null;
}

function _tbody() {
  return container.querySelector('#es-rows tbody') ?? null;
}

function _appendBottom() {
  if (!_sorted || _renderedEnd >= _sorted.length) return;
  const tb = _tbody();
  if (!tb) return;
  const next = _sorted.slice(_renderedEnd, _renderedEnd + BATCH);
  next.forEach((e, j) => tb.insertAdjacentHTML('beforeend', _rowHtml(e, _renderedEnd + j)));
  _renderedEnd += next.length;
  _updateLabel();
}

function _prependTop() {
  if (!_sorted || _renderedStart <= 0) return;
  const tb = _tbody();
  if (!tb) return;
  const batchStart = Math.max(0, _renderedStart - BATCH);
  const next = _sorted.slice(batchStart, _renderedStart);
  const prevH = tb.scrollHeight;
  const frag = document.createElement('tbody');
  next.forEach((e, j) => frag.insertAdjacentHTML('beforeend', _rowHtml(e, batchStart + j)));
  while (frag.firstElementChild) tb.insertBefore(frag.firstElementChild, tb.firstChild);
  if (_scrollEl) _scrollEl.scrollTop += tb.scrollHeight - prevH;
  _renderedStart = batchStart;
  _updateLabel();
}

function _updateLabel() {
  const el = container.querySelector('#es-range');
  if (el && _sorted) el.textContent = `#${_renderedStart + 1}–${_renderedEnd} of ${_sorted.length}`;
}

function _initLazyScroll() {
  _teardownScroll();
  _scrollEl = container.querySelector('#es-scroll');
  if (!_scrollEl) return;
  _onScroll = () => {
    if (_scrollEl.scrollTop + _scrollEl.clientHeight >= _scrollEl.scrollHeight - 120) _appendBottom();
    if (_scrollEl.scrollTop <= 120) _prependTop();
  };
  _scrollEl.addEventListener('scroll', _onScroll);
  const fill = () => {
    if (_scrollEl.scrollHeight <= _scrollEl.clientHeight) {
      if (_renderedEnd < (_sorted?.length ?? 0)) { _appendBottom(); requestAnimationFrame(fill); }
      else if (_renderedStart > 0) { _prependTop(); requestAnimationFrame(fill); }
    }
  };
  requestAnimationFrame(fill);
}

// ── Render ────────────────────────────────────────────────────────────────────

function _renderError(msg) {
  container.innerHTML = `<div style="padding:16px"><div class="panel-header">Empire Stats</div><div class="error-msg">${msg}</div></div>`;
}

function _headerCells() {
  return COLS.map(col => {
    const active = col.key === _sortKey;
    const arrow = active ? (_sortDir === 'desc' ? '▼' : '▲') : '';
    const inner = arrow
      ? `${col.label} <span style="font-size:0.8em;">${arrow}</span>`
      : col.label;
    return `<th data-col="${col.key}" style="padding:3px 6px 8px;text-align:center;font-size:0.7em;font-weight:600;color:${active ? 'var(--accent,#4fc3f7)' : 'var(--text-dim,#9999a8)'};border-bottom:1px solid var(--border-color,#2a2a3a);cursor:pointer;user-select:none;vertical-align:bottom;">
      <span style="writing-mode:vertical-rl;transform:rotate(180deg);display:inline-block;white-space:nowrap;">${inner}</span>
    </th>`;
  }).join('');
}

function _render(data, preserveScroll = false) {
  if (!data) {
    container.innerHTML = `<div style="padding:16px"><div class="panel-header">Empire Stats</div><div class="panel-row"><span class="value">Loading…</span></div></div>`;
    return;
  }
  if (data.length === 0) {
    container.innerHTML = `<div style="padding:16px"><div class="panel-header">Empire Stats</div><div class="panel-row"><span class="value">—</span></div></div>`;
    return;
  }

  _renderedStart = 0;
  _renderedEnd = Math.min(data.length, INITIAL_WINDOW);
  const slice = data.slice(_renderedStart, _renderedEnd);

  const rows = slice.map((e, i) => _rowHtml(e, i)).join('');

  container.innerHTML = `
    <div style="display:flex;flex-direction:column;gap:0;width:100%;box-sizing:border-box;height:100%;padding:8px 0 0;">
      <div style="flex-shrink:0;padding:4px 8px;">
        <span style="color:#666;font-size:0.8em;" id="es-range">#${_renderedStart + 1}–${_renderedEnd} of ${data.length}</span>
      </div>
      <div id="es-scroll" style="overflow-y:auto;overflow-x:hidden;flex:1;overscroll-behavior:contain;">
        <div id="es-hscroll" style="overflow-x:auto;overscroll-behavior-x:none;">
          <table id="es-rows" style="border-collapse:separate;border-spacing:0;font-size:13px;">
            <thead>
              <tr>
                <th style="position:sticky;left:0;z-index:2;background:var(--bg,#0e0e1a);padding:3px 6px;text-align:left;font-size:0.7em;color:var(--text-dim,#9999a8);border-bottom:1px solid var(--border-color,#2a2a3a);"># Empire</th>
                ${_headerCells()}
              </tr>
            </thead>
            <tbody>${rows}</tbody>
          </table>
        </div>
      </div>
    </div>`;

  // Sort on header click
  container.querySelector('thead').addEventListener('click', (ev) => {
    const th = ev.target.closest('th[data-col]');
    if (!th) return;
    const col = th.dataset.col;
    if (_sortKey === col) {
      _sortDir = _sortDir === 'desc' ? 'asc' : 'desc';
    } else {
      _sortKey = col;
      _sortDir = 'desc';
    }
    _sorted = _sort(_empiresData);
    _render(_sorted, false);
  });

  _initLazyScroll();

  if (!preserveScroll) {
    const scrollEl = container.querySelector('#es-scroll');
    const selfEl = container.querySelector('.es-self');
    if (scrollEl && selfEl) {
      requestAnimationFrame(() => {
        const top = selfEl.offsetTop - scrollEl.clientHeight / 2 + selfEl.clientHeight / 2;
        scrollEl.scrollTop = Math.max(0, top);
      });
    }
  }
}

export default {
  id: 'empirestats',
  title: 'Empire Stats',
  init,
  enter,
  leave,
};
