/**
 * Season Results view — end-of-season leaderboard.
 * Route: #season-results
 * Accessible via the "(view results)" link in the game-over banner.
 */

import { rest } from '../rest.js';
import { fmtRes } from '../lib/format.js';
import { pageTitle } from '../lib/page_title.js';

let container;

// ── Init ────────────────────────────────────────────────────

function init(el, _api, _state) {
  container = el;
  container.style.cssText = 'display:flex;flex-direction:column;height:100%;overflow-y:auto;';
}

// ── Enter / Leave ───────────────────────────────────────────

async function enter() {
  pageTitle.set('Season Results');
  document.getElementById('app')?.classList.add('sr-fullbleed');
  _renderLoading();
  try {
    const data = await rest.getSeasonResults();
    _render(data?.empires || [], data?.season_number ?? 1, data?.season_title ?? '', data?.next_season_start ?? '');
  } catch (err) {
    _renderError(err);
  }
}

function leave() {
  document.getElementById('app')?.classList.remove('sr-fullbleed');
}

// ── Render ──────────────────────────────────────────────────

function _renderLoading() {
  container.innerHTML = `
    <div class="sr-wrap">
      <div class="sr-loading">Loading season results…</div>
    </div>`;
}

function _renderError(err) {
  container.innerHTML = `
    <div class="sr-wrap">
      <div class="sr-error">Season results are not yet available.<br><small>${err?.message || ''}</small></div>
    </div>`;
}

function _render(empires, seasonNumber, seasonTitle, nextSeasonStart) {
  if (!empires.length) {
    container.innerHTML = `<div class="sr-wrap"><div class="sr-error">No data available.</div></div>`;
    return;
  }

  const podiumHtml = _podiumHtml(empires);
  const awardsHtml = _awardsHtml(empires);
  const titleHtml = seasonTitle
    ? `<div class="sr-season-label">Season ${seasonNumber}</div><h1 class="sr-title">${_esc(seasonTitle)}</h1>`
    : `<h1 class="sr-title">Season ${seasonNumber} Results</h1>`;

  container.innerHTML = `
    <div class="sr-wrap">
      <div class="sr-bg-mobile"></div>

      <picture class="sr-banner-picture">
        <source media="(max-width: 640px)" srcset="/assets/sprites/images/season1_end_portrait.webp">
        <img class="sr-banner-img" src="/assets/sprites/images/season1_end_landscape.webp" alt="Season End">
      </picture>

      <div class="sr-content">
        ${titleHtml}

        <div class="sr-podium">
          ${podiumHtml}
        </div>

        <div class="sr-awards-section">
          <h2 class="sr-awards-title">Category Awards</h2>
          <div class="sr-awards">
            ${awardsHtml}
          </div>
        </div>

        ${nextSeasonStart ? `<div class="sr-next-season">${_nextSeasonText(nextSeasonStart)}</div>` : ''}
      </div>
    </div>`;
}

function _podiumHtml(empires) {
  const medals = [
    { rank: 1, icon: '🥇', cls: 'sr-gold',   label: '' },
    { rank: 2, icon: '🥈', cls: 'sr-silver', label: '' },
    { rank: 3, icon: '🥉', cls: 'sr-bronze', label: '' },
  ];
  let html = '';
  for (const m of medals) {
    const e = empires[m.rank - 1];
    if (!e) continue;
    html += `
      <div class="sr-podium-entry ${m.cls}">
        <span class="sr-medal">${m.icon}</span>
        <span class="sr-empire-name">${_esc(e.name)}</span>
        <span class="sr-culture">${fmtRes(e.culture)} culture</span>
      </div>`;
  }

  // Most culture points line (below podium)
  const cultureLeader = [...empires].sort((a, b) => b.culture - a.culture);
  const topCulture = cultureLeader[0]?.culture ?? 0;
  const cultureWinners = cultureLeader.filter(e => e.culture >= topCulture);
  html += `
    <div class="sr-culture-line">
      🎭 Most Culture Points: <strong>${cultureWinners.map(e => _esc(e.name)).join(', ')}</strong>
      <span class="sr-value">(${fmtRes(topCulture)})</span>
    </div>`;

  return html;
}

function _awardsHtml(empires) {
  const awards = [
    { icon: '🏺', label: 'Most Artifacts Secured',      key: 'artifacts',       fmt: n => `${n}` },
    { icon: '🏰', label: 'Most Powerful Defense',        key: 'tower_gold',      fmt: n => `${fmtRes(n)} gold` },
    { icon: '⚔',  label: 'Most Powerful Army',           key: 'army_gold',       fmt: n => `${fmtRes(n)} gold` },
    { icon: '🗺',  label: 'Most Territory',               key: 'tile_count',      fmt: n => `${n} tiles` },
    { icon: '⚙',  label: 'Most Workshop Investment',     key: 'workshop_gold',    fmt: n => `${fmtRes(n)} gold` },
    { icon: '🔬', label: 'Most Research Done',            key: 'research_effort',  fmt: (n, e) => `${fmtRes(n)} effort, ${e.research_count} items` },
    { icon: '🏛',  label: 'Most Buildings Done',          key: 'buildings_effort', fmt: (n, e) => `${fmtRes(n)} effort, ${e.buildings_count} items` },
  ];

  return awards.map(({ icon, label, key, fmt }) => {
    const top = Math.max(...empires.map(e => e[key] ?? 0));
    const winners = empires.filter(e => (e[key] ?? 0) >= top && top > 0);
    const nameStr = winners.length
      ? winners.map(e => `<strong>${_esc(e.name)}</strong>`).join(', ')
      : '<span class="sr-none">—</span>';
    const valStr = top > 0 ? `<span class="sr-value">(${fmt(top, winners[0])})</span>` : '';
    return `
      <div class="sr-award-row">
        <span class="sr-award-icon">${icon}</span>
        <span class="sr-award-label">${label}</span>
        <span class="sr-award-winner">${nameStr} ${valStr}</span>
      </div>`;
  }).join('');
}

function _nextSeasonText(isoDate) {
  try {
    const d = new Date(isoDate);
    const opts = { year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit', timeZoneName: 'short' };
    return `The next season starts on <strong>${d.toLocaleDateString('en-US', opts)}</strong>. See you then!`;
  } catch {
    return `The next season starts on <strong>${_esc(isoDate)}</strong>. See you then!`;
  }
}

function _esc(str) {
  return String(str ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
}

// ── Export ──────────────────────────────────────────────────

export default { id: 'season-results', init, enter, leave };
