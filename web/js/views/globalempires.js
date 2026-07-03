/**
 * Global Empires view — leaderboard with lazy scroll, centered on own empire.
 * Stats are on the separate Empire Stats page.
 */

import { rest } from '../rest.js';
import { pageTitle } from '../lib/page_title.js';
import { state } from '../state.js';
import { showIconLegend } from '../lib/format.js';

/** @type {HTMLElement} */
let container;

let _empiresData = null;
let _renderedStart = 0;
let _renderedEnd = 0;
let _savedScrollTop = -1;

const INITIAL_WINDOW = 10;
const BATCH = 20;

// ── Init ────────────────────────────────────────────────────────────────────

function init(el) {
  container = el;
  container.style.cssText = 'display:flex;flex-direction:column;height:100%;overflow-x:hidden;';
  container.addEventListener('click', e => {
    if (e.target.closest('.icon-legend-trigger')) showIconLegend();
  });
}

async function enter() {
  pageTitle.set('🌍 Known Empires');
  document.getElementById('app')?.classList.add('full-bleed');
  const isFirstVisit = _savedScrollTop < 0;
  if (!_empiresData) _render(null);
  try {
    const resp = await rest.getEmpires();
    _empiresData = (resp.empires || []).slice().sort((a, b) => (b.culture ?? 0) - (a.culture ?? 0));
  } catch (e) {
    _renderError(e.message);
    return;
  }
  _render(_empiresData, !isFirstVisit);
  if (!isFirstVisit) {
    const scrollEl = container.querySelector('#ge-scroll');
    if (scrollEl) scrollEl.scrollTop = _savedScrollTop;
  }
  if (isFirstVisit) _savedScrollTop = 0;
}

function leave() {
  const scrollEl = container.querySelector('#ge-scroll');
  if (scrollEl) _savedScrollTop = scrollEl.scrollTop;
  document.getElementById('app')?.classList.remove('full-bleed');
  _teardownScroll();
  _empiresData = null;
}

// ── Helpers ──────────────────────────────────────────────────────────────────

function _toRoman(n) {
  const vals = [1000,900,500,400,100,90,50,40,10,9,5,4,1];
  const syms = ['M','CM','D','CD','C','XC','L','XL','X','IX','V','IV','I'];
  let out = '';
  for (let i = 0; i < vals.length; i++) { while (n >= vals[i]) { out += syms[i]; n -= vals[i]; } }
  return out;
}

function _fmtCulture(n) {
  if (n == null) return '0';
  if (n >= 1_000_000) return (n / 1_000_000).toFixed(1) + 'M';
  if (n >= 1_000) return (n / 1_000).toFixed(1) + 'K';
  return String(Math.round(n));
}

function _dot(online) {
  return `<span style="display:inline-block;width:7px;height:7px;border-radius:50%;flex-shrink:0;background:${online ? 'var(--success,#66bb6a)' : '#3a3a4a'};${online ? 'box-shadow:0 0 4px var(--success,#66bb6a)' : ''}"></span>`;
}

// ── Row rendering ─────────────────────────────────────────────────────────────

function _rowHtml(e, rankIndex, selfEra) {
  const armyEnabled = (state.summary?.effects?.enable_army ?? 0) > 0;
  const canAttack = armyEnabled && e.era >= selfEra - 1;
  const attackBtn = !e.is_self && canAttack
    ? `<button class="attack-btn" data-uid="${e.uid}" data-name="${e.name}" style="font-size:11px;padding:3px 8px;background:var(--danger,#e53935);border-color:var(--danger,#e53935);">⚔</button>`
    : '';

  const currentMedal = e.season_place === 1 ? '🥇' : e.season_place === 2 ? '🥈' : e.season_place === 3 ? '🥉' : '';
  const pastMedal = e.past_champion ? '🎖️' : '';
  const selfStyle = e.is_self ? 'background:rgba(255,255,255,0.06);' : '';
  return `<div class="ge-row panel-row${e.is_self ? ' ge-self' : ''}" style="display:flex;flex-direction:row;align-items:center;padding:4px 8px;gap:8px;border-bottom:1px solid var(--border-color,#2a2a3a);${selfStyle}">
    <span style="color:#888;font-size:0.8em;min-width:22px;">${rankIndex + 1}</span>
    ${_dot(e.online)}
    <div style="min-width:0;flex:1;">
      <div style="font-weight:${e.is_self ? 'bold' : 'normal'};color:${e.is_self ? 'var(--accent,#4fc3f7)' : 'inherit'};overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">
        ${e.name} <span style="font-size:0.8em;color:#c9a84c;">${_toRoman(e.era || 1)}</span>
        ${e.username ? `<span style="color:#888;font-weight:normal;font-size:0.82em;">(${e.username}${(e.is_bot || currentMedal || pastMedal) ? `<span class="icon-legend-trigger" style="cursor:pointer;">${e.is_bot ? ' 🤖' : ''}${currentMedal ? ' ' + currentMedal : ''}${pastMedal ? ' ' + pastMedal : ''}</span>` : ''})</span>` : ''}
        ${e.is_self ? ' ★' : ''}
      </div>
      <div style="color:#ffa726;font-size:0.82em;">${_fmtCulture(e.resources?.culture ?? e.culture ?? 0)} ✦
        ${(e.artifact_count || 0) > 0 ? `<span class="icon-legend-trigger" style="margin-left:6px;color:#c9a84c;cursor:pointer;">${'⚜'.repeat(e.artifact_count)}</span>` : ''}
      </div>
    </div>
    ${attackBtn}
  </div>`;
}

function _bindAttackBtns(parent) {
  parent.querySelectorAll('.attack-btn').forEach((btn) => {
    btn.onclick = () => window.dispatchEvent(
      new CustomEvent('empire:attack', { detail: { uid: btn.dataset.uid, name: btn.dataset.name } })
    );
  });
}

// ── Lazy scroll ───────────────────────────────────────────────────────────────

let _scrollEl = null;
let _onScroll = null;

function _teardownScroll() {
  if (_scrollEl && _onScroll) _scrollEl.removeEventListener('scroll', _onScroll);
  _scrollEl = null;
  _onScroll = null;
}

function _appendBottom() {
  const empires = _empiresData;
  if (!empires || _renderedEnd >= empires.length) return;
  const selfEra = (empires.find((e) => e.is_self) || {}).era || 1;
  const target = container.querySelector('#ge-rows');
  if (!target) return;
  const next = empires.slice(_renderedEnd, _renderedEnd + BATCH);
  const wrapper = document.createElement('div');
  next.forEach((e, j) => wrapper.insertAdjacentHTML('beforeend', _rowHtml(e, _renderedEnd + j, selfEra).trim()));
  const frag = document.createDocumentFragment();
  while (wrapper.firstElementChild) { const n = wrapper.firstElementChild; _bindAttackBtns(n); frag.appendChild(n); }
  target.appendChild(frag);
  _renderedEnd += next.length;
  _updateCountLabel();
}

function _prependTop() {
  const empires = _empiresData;
  if (!empires || _renderedStart <= 0) return;
  const selfEra = (empires.find((e) => e.is_self) || {}).era || 1;
  const target = container.querySelector('#ge-rows');
  if (!target) return;
  const batchStart = Math.max(0, _renderedStart - BATCH);
  const next = empires.slice(batchStart, _renderedStart);
  const prevHeight = target.scrollHeight;
  const wrapper = document.createElement('div');
  next.forEach((e, j) => wrapper.insertAdjacentHTML('beforeend', _rowHtml(e, batchStart + j, selfEra).trim()));
  const frag = document.createDocumentFragment();
  while (wrapper.firstElementChild) { const n = wrapper.firstElementChild; _bindAttackBtns(n); frag.appendChild(n); }
  target.insertBefore(frag, target.firstChild);
  if (_scrollEl) _scrollEl.scrollTop += target.scrollHeight - prevHeight;
  _renderedStart = batchStart;
  _updateCountLabel();
}

function _updateCountLabel() {
  const el = container.querySelector('#ge-range');
  if (!el || !_empiresData) return;
  el.textContent = `#${_renderedStart + 1}–${_renderedEnd} of ${_empiresData.length}`;
}

function _initLazyScroll() {
  _teardownScroll();
  _scrollEl = container.querySelector('#ge-scroll');
  if (!_scrollEl) return;
  _onScroll = () => {
    const nearBottom = _scrollEl.scrollTop + _scrollEl.clientHeight >= _scrollEl.scrollHeight - 120;
    const nearTop = _scrollEl.scrollTop <= 120;
    if (nearBottom) _appendBottom();
    if (nearTop) _prependTop();
  };
  _scrollEl.addEventListener('scroll', _onScroll);
  const _fill = () => {
    const canScrollMore = _scrollEl.scrollHeight > _scrollEl.clientHeight;
    if (!canScrollMore) {
      const didBottom = _renderedEnd < (_empiresData?.length ?? 0);
      const didTop = _renderedStart > 0;
      if (didBottom) { _appendBottom(); requestAnimationFrame(_fill); }
      else if (didTop) { _prependTop(); requestAnimationFrame(_fill); }
    }
  };
  requestAnimationFrame(_fill);
}

// ── Render ────────────────────────────────────────────────────────────────────

function _renderError(msg) {
  container.innerHTML = `<div style="padding:16px"><div class="panel-header" style="margin-bottom:12px">Known Empires</div><div class="error-msg">${msg}</div></div>`;
}


function _render(empires, preserveScroll = false) {
  if (!empires) {
    container.innerHTML = `<div style="padding:16px"><div class="panel-header" style="margin-bottom:12px">Known Empires</div><div class="panel-row"><span class="value">Loading…</span></div></div>`;
    return;
  }
  if (empires.length === 0) {
    container.innerHTML = `<div style="padding:16px"><div class="panel-header" style="margin-bottom:12px">Known Empires</div><div class="panel-row"><span class="value">—</span></div></div>`;
    return;
  }

  const selfIdx = empires.findIndex((e) => e.is_self);
  const selfEra = selfIdx >= 0 ? (empires[selfIdx].era || 1) : 1;

  _renderedStart = Math.max(0, selfIdx - INITIAL_WINDOW);
  _renderedEnd   = Math.min(empires.length, selfIdx + INITIAL_WINDOW + 1);
  const slice = empires.slice(_renderedStart, _renderedEnd);

  const rows = slice.map((e, i) => _rowHtml(e, _renderedStart + i, selfEra)).join('');

  container.innerHTML = `
    <div style="display:flex;flex-direction:column;gap:0;width:100%;box-sizing:border-box;height:100%;padding:8px 0 0;">
      <div style="flex-shrink:0;padding:4px 8px;">
        <span style="color:#666;font-size:0.8em;" id="ge-range">#${_renderedStart + 1}–${_renderedEnd} of ${empires.length}</span>
      </div>
      <div id="ge-scroll" style="overflow-y:auto;flex:1;overscroll-behavior-y:contain;">
        <div id="ge-rows" class="panel" style="padding:0;overflow:hidden;width:100%;border-radius:0;">${rows}</div>
      </div>
    </div>`;

  _bindAttackBtns(container);
  _initLazyScroll();

  if (!preserveScroll) {
    const scrollEl = container.querySelector('#ge-scroll');
    const selfEl = container.querySelector('.ge-self');
    if (scrollEl && selfEl) {
      requestAnimationFrame(() => {
        const top = selfEl.offsetTop - scrollEl.clientHeight / 2 + selfEl.clientHeight / 2;
        scrollEl.scrollTop = Math.max(0, top);
      });
    }
  }
}

export default {
  id: 'globalempires',
  title: 'Known Empires',
  init,
  enter,
  leave,
};
