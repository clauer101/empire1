/**
 * Eternal Ranking view — all-time culture table across every season.
 *
 * The server returns every empire that cleared the entry threshold, ranked
 * (GET /api/empires/eternal). All of them are listed here — the threshold is
 * what keeps the table short, so there is no windowing and no gap to mark.
 *
 * Three columns: Total (all seasons summed), Current (the running season —
 * during a season reset the one about to start) and Seasons (how many
 * seasons the empire actually scored in).
 */

import { rest } from '../rest.js';
import { pageTitle } from '../lib/page_title.js';
import { fmtEffort } from '../lib/format.js';
import { escHtml } from '../lib/html.js';

/** @type {HTMLElement} */
let container;

let _data = null;

// ── Init ────────────────────────────────────────────────────────────────────

function init(el) {
  container = el;
  container.style.cssText = 'display:flex;flex-direction:column;height:100%;overflow-x:hidden;';
}

async function enter() {
  pageTitle.set('🏆 Eternal Ranking');
  document.getElementById('app')?.classList.add('full-bleed');
  if (!_data) _render(null);
  try {
    _data = await rest.getEternalRanking();
  } catch (e) {
    _renderError(e.message);
    return;
  }
  _render(_data);
  const selfEl = container.querySelector('.er-self');
  const scrollEl = container.querySelector('#er-scroll');
  if (selfEl && scrollEl) {
    requestAnimationFrame(() => {
      const top = selfEl.offsetTop - scrollEl.clientHeight / 2 + selfEl.clientHeight / 2;
      scrollEl.scrollTop = Math.max(0, top);
    });
  }
}

function leave() {
  document.getElementById('app')?.classList.remove('full-bleed');
  _data = null;
}

// ── Rendering ───────────────────────────────────────────────────────────────

function _medal(rank) {
  if (rank === 1) return '🥇';
  if (rank === 2) return '🥈';
  if (rank === 3) return '🥉';
  return '';
}

function _rowHtml(row) {
  const nameColor = row.is_self ? 'var(--accent,#4fc3f7)' : 'inherit';
  const bg = row.is_self ? 'background:rgba(255,255,255,0.06);' : '';
  const cell = 'text-align:right;padding:4px 8px;font-size:0.8em;white-space:nowrap;';
  return `<tr class="er-row${row.is_self ? ' er-self' : ''}" style="${bg}">
    <td style="padding:4px 8px;text-align:right;color:#666;font-size:0.8em;">${row.rank}</td>
    <td style="padding:4px 8px;font-size:0.85em;color:${nameColor};max-width:160px;overflow:hidden;text-overflow:ellipsis;">${_medal(row.rank)}${escHtml(row.name)}${row.is_bot ? ' 🤖' : ''}${row.is_self ? ' ★' : ''}</td>
    <td style="${cell}color:var(--accent,#4fc3f7);font-weight:600;">${fmtEffort(row.total_culture)}</td>
    <td style="${cell}color:var(--text-dim,#9999a8);">${fmtEffort(row.current_culture)}</td>
    <td style="${cell}color:var(--text-dim,#9999a8);">${row.seasons_played}</td>
  </tr>`;
}

function _renderError(msg) {
  container.innerHTML = `<div style="padding:16px"><div class="panel-header">Eternal Ranking</div><div class="error-msg">${escHtml(msg)}</div></div>`;
}

function _render(data) {
  if (!data) {
    container.innerHTML = `<div style="padding:16px"><div class="panel-header">Eternal Ranking</div><div class="panel-row"><span class="value">Loading…</span></div></div>`;
    return;
  }
  const ranking = data.ranking || [];
  if (ranking.length === 0) {
    const bar = data.min_culture ? fmtEffort(data.min_culture) : null;
    container.innerHTML = `<div style="padding:16px"><div class="panel-header">Eternal Ranking</div><div class="panel-row"><span class="value">${bar ? `No empire has reached ${bar} culture yet.` : '—'}</span></div></div>`;
    return;
  }

  const rows = ranking.map(_rowHtml).join('');
  const finishedSeasons = (data.seasons || []).length;
  const entryBar = data.min_culture ? fmtEffort(data.min_culture) : null;
  const place = data.self_rank
    ? `Your place: <span style="color:var(--accent,#4fc3f7)">#${data.self_rank}</span> of ${data.total}`
    : `Not ranked yet${entryBar ? ` — ${entryBar} culture needed to enter` : ''} (${data.total} ranked)`;

  container.innerHTML = `
    <div style="display:flex;flex-direction:column;width:100%;box-sizing:border-box;height:100%;padding:8px 0 0;">
      <div style="flex-shrink:0;padding:4px 10px 8px;">
        <div style="font-size:0.85em;">${place}</div>
        <div style="color:#666;font-size:0.75em;margin-top:2px;">
          Total = ${finishedSeasons} finished season${finishedSeasons === 1 ? '' : 's'} plus the current one · Current = season ${data.current_season}${data.current_season_title ? ` "${escHtml(data.current_season_title)}"` : ''} · Seasons = seasons scored in
        </div>
        ${entryBar ? `<div style="color:#666;font-size:0.7em;margin-top:2px;">Empires below ${entryBar} culture are not listed</div>` : ''}
      </div>
      <div id="er-scroll" style="overflow-y:auto;overflow-x:auto;flex:1;overscroll-behavior:contain;">
        <table style="border-collapse:separate;border-spacing:0;width:100%;font-size:13px;">
          <thead>
            <tr>
              ${_headerCell('#', 'right')}
              ${_headerCell('Empire', 'left')}
              ${_headerCell('Total', 'right')}
              ${_headerCell('Current', 'right')}
              ${_headerCell('Seasons', 'right')}
            </tr>
          </thead>
          <tbody>${rows}</tbody>
        </table>
      </div>
    </div>`;
}

function _headerCell(label, align) {
  return `<th style="padding:3px 8px 8px;text-align:${align};font-size:0.7em;font-weight:600;color:var(--text-dim,#9999a8);border-bottom:1px solid var(--border-color,#2a2a3a);white-space:nowrap;">${label}</th>`;
}

export default {
  id: 'ranking',
  title: 'Eternal Ranking',
  init,
  enter,
  leave,
};
