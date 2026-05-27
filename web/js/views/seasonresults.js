/**
 * Season Results view — end-of-season leaderboard.
 * Route: #season-results
 * Accessible via the "(view results)" link in the game-over banner.
 */

import { rest } from '../rest.js';
import { fmtRes, fmtSecs } from '../lib/format.js';
import { pageTitle } from '../lib/page_title.js';

let container;
let _state = null;

// ── Init ────────────────────────────────────────────────────

function init(el, _api, state) {
  container = el;
  container.style.cssText = 'display:flex;flex-direction:column;height:100%;overflow-y:auto;';
  _state = state;
}

// ── Enter / Leave ───────────────────────────────────────────

async function enter() {
  pageTitle.set('Season Results');
  document.getElementById('app')?.classList.add('sr-fullbleed');
  _renderLoading();
  try {
    const data = await rest.getSeasonResults();
    const myUid = _state?.auth?.uid ?? null;
    _render(data?.empires || [], data?.season_number ?? 1, data?.season_title ?? '', data?.next_season_start ?? '', myUid, data?.era_firsts ?? [], data?.era_order ?? []);
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

function _render(empires, seasonNumber, seasonTitle, nextSeasonStart, myUid, eraFirsts, eraOrder) {
  if (!empires.length) {
    container.innerHTML = `<div class="sr-wrap"><div class="sr-error">No data available.</div></div>`;
    return;
  }

  const podiumHtml = _podiumHtml(empires);
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
          <h2 class="sr-awards-title">Honorable Mentions</h2>
          <div class="sr-awards">
            ${_allAwardsHtml(empires, myUid)}
          </div>
        </div>

        ${eraFirsts.length ? `
        <div class="sr-awards-section">
          <h2 class="sr-awards-title">First in Era</h2>
          ${_eraFirstsTableHtml(eraFirsts, eraOrder, myUid)}
        </div>` : ''}

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

function _allAwardsHtml(empires, myUid) {
  // eslint-disable-next-line eqeqeq -- uid may be int from API vs string from JWT
  const me = myUid != null ? empires.find(e => e.uid == myUid) : null;

  const awards = [
    { icon: '🏺', label: 'Most Artifacts Secured',       key: 'artifacts',        fmt: n => `${n}` },
    { icon: '🏰', label: 'Most Powerful Defense',         key: 'tower_gold',       fmt: n => `${fmtRes(n)} gold` },
    { icon: '⚔',  label: 'Most Powerful Army',            key: 'army_gold',        fmt: n => `${fmtRes(n)} gold` },
    { icon: '🗺',  label: 'Most Territory',                key: 'tile_count',       fmt: n => `${n} tiles` },
    { icon: '⚙',  label: 'Most Workshop Investment',      key: 'workshop_gold',    fmt: n => `${fmtRes(n)} gold` },
    { icon: '🔬', label: 'Most Research Done',             key: 'research_effort',  fmt: (n, e) => `${fmtRes(n)} effort, ${e.research_count} items` },
    { icon: '🏛',  label: 'Most Buildings Done',           key: 'buildings_effort', fmt: (n, e) => `${fmtRes(n)} effort, ${e.buildings_count} items` },
    { icon: '💀', label: 'Most Critters Killed',           key: 'critters_killed',  fmt: n => fmtRes(n) },
    { icon: '🏗', label: 'Most Towers Placed',             key: 'towers_placed',    fmt: n => `${n}` },
    { icon: '💸', label: 'Most Towers Sold',               key: 'towers_sold',      fmt: n => `${n}` },
    { icon: '🕵', label: 'Most Spies Sent',                key: 'spies_sent',       fmt: n => `${n}` },
    { icon: '🏺', label: 'Most Artifacts Stolen',          key: 'artifacts_stolen', fmt: n => `${n}` },
    { icon: '🏆', label: 'Peak Artifacts Held',            key: 'peak_artifacts_held', fmt: n => `${n} at once` },
    { icon: '💰', label: 'Most Gold Earned from Defense',  key: 'defense_gold_earned', fmt: n => `${fmtRes(n)} gold` },
    { icon: '🎭', label: 'Most Culture Stolen',            key: 'culture_stolen',   fmt: n => fmtRes(n) },
    { icon: '🔬', label: 'Most Research Stolen',           key: 'research_stolen',  fmt: n => `${fmtRes(n)} effort` },
    { icon: '🎭', label: 'Most Culture Won',               key: 'culture_won',      fmt: n => fmtRes(n) },
    { icon: '⏱', label: 'Longest Battle Survived',        key: 'longest_battle_ms', fmt: n => fmtSecs(Math.round(n / 1000)) },
    { icon: '🌟', label: 'First to Reach New Eras',        key: 'first_era_reached', fmt: n => `${n} era${n !== 1 ? 's' : ''}` },
    { icon: '🐉', label: 'Most Upgraded Critter',            key: 'critter_upgrade_levels', fmt: n => `${n} levels` },
    { icon: '🗼', label: 'Most Upgraded Tower',              key: 'tower_upgrade_levels',   fmt: n => `${n} levels` },
    { icon: '⏳', label: 'Longest Artifact Hold',           key: 'longest_artifact_hold_secs', fmt: n => fmtSecs(n) },
    { icon: '⚔',  label: 'Most Attacks Sent (Human)',       key: 'attacks_sent_human',     fmt: n => `${n}` },
    { icon: '🛡', label: 'Most Attacks Suffered (Human)',   key: 'attacks_received_human', fmt: n => `${n}` },
    { icon: '🤖', label: 'Most AI Attacks Defeated',        key: 'defense_won_ai',         fmt: n => `${n}` },
    { icon: '💀', label: 'Most AI Attacks Lost',            key: 'defense_lost_ai',        fmt: n => `${n}` },
  ];

  return awards.map(({ icon, label, key, fmt }) => {
    const top = Math.max(...empires.map(e => e[key] ?? 0));
    const winners = empires.filter(e => (e[key] ?? 0) >= top);
    // eslint-disable-next-line eqeqeq
    const isWinner = me && winners.some(e => e.uid == me.uid);
    const nameStr = winners.length
      ? winners.map(e => `<strong>${_esc(e.name)}</strong>`).join(', ')
      : '<span class="sr-none">—</span>';
    const valStr = fmt(top, winners[0]);
    const myValStr = (!isWinner && me)
      ? `<span class="sr-my-value">(You: ${fmt(me[key] ?? 0, me)})</span>`
      : '';
    return `
      <div class="sr-award-row">
        <span class="sr-award-icon">${icon}</span>
        <span class="sr-award-label">${label}</span>
        <span class="sr-award-winner">
          <span class="sr-award-top">${nameStr}: ${valStr}</span>
          ${myValStr}
        </span>
      </div>`;
  }).join('');
}

const _ERA_LABELS = {
  stone: 'Stone Age', neolithic: 'Neolithic', bronze: 'Bronze Age', iron: 'Iron Age',
  middle_ages: 'Middle Ages', renaissance: 'Renaissance', industrial: 'Industrial',
  modern: 'Modern', future: 'Future',
};

function _eraFirstsTableHtml(eraFirsts, eraOrder, myUid) {
  const byEra = {};
  for (const row of eraFirsts) byEra[row.era_key] = row;
  const eras = eraOrder.length ? eraOrder : Object.keys(byEra);
  let rows = '';
  for (const era of eras) {
    const row = byEra[era];
    if (!row) continue;
    // eslint-disable-next-line eqeqeq
    const isMe = myUid != null && row.uid == myUid;
    rows += `<tr class="${isMe ? 'sr-era-first-me' : ''}">
      <td class="sr-era-name">${_ERA_LABELS[era] ?? era}</td>
      <td class="sr-era-empire">${isMe ? '<strong>' : ''}${_esc(row.empire_name)}${isMe ? '</strong>' : ''}</td>
    </tr>`;
  }
  return `<table class="sr-era-firsts-table"><tbody>${rows}</tbody></table>`;
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
