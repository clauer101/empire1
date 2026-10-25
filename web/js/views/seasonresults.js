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
    _render(data?.empires || [], data?.season_number ?? 1, data?.season_title ?? '', data?.next_season_start ?? '', myUid, data?.era_firsts ?? [], data?.era_order ?? [], data?.longest_single_artifact_holds ?? [], data?.season_podium ?? []);
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

function _render(empires, seasonNumber, seasonTitle, nextSeasonStart, myUid, eraFirsts, eraOrder, longestSingleArtifactHolds, seasonPodium) {
  if (!empires.length) {
    container.innerHTML = `<div class="sr-wrap"><div class="sr-error">No data available.</div></div>`;
    return;
  }

  const podiumHtml = _podiumHtml(empires, seasonPodium);
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
            ${_longestSingleArtifactHoldHtml(longestSingleArtifactHolds, myUid)}
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

function _podiumHtml(empires, seasonPodium) {
  const medals = [
    { rank: 1, icon: '🥇', cls: 'sr-gold' },
    { rank: 2, icon: '🥈', cls: 'sr-silver' },
    { rank: 3, icon: '🥉', cls: 'sr-bronze' },
  ];
  // Places are pooled by mutual alliance server-side: a place can be a
  // two-empire team ranked on combined culture, or a single empire that
  // outscores the teams on its own.
  const places = seasonPodium || [];

  let html = '';
  for (const m of medals) {
    const p = places[m.rank - 1];
    if (!p || !p.members?.length) continue;
    const isTeam = p.members.length > 1;
    html += `
      <div class="sr-podium-entry ${m.cls}${isTeam ? ' sr-podium-team' : ''}">
        <span class="sr-medal">${m.icon}</span>
        <span class="sr-empire-name">${p.members.map(e => _esc(e.name)).join(' & ')}</span>
        <span class="sr-culture">${fmtRes(p.pooled_culture)} culture${isTeam ? ' (team)' : ''}</span>
      </div>`;
  }

  // Culture lines below the podium: the winning score first (pooled for a
  // team), then the best individual score so solo performance stays visible.
  const topPlace = places[0];
  const topIsTeam = (topPlace?.members?.length ?? 0) > 1;
  if (topPlace?.members?.length) {
    html += `
    <div class="sr-culture-line">
      🎭 Most Culture Points${topIsTeam ? ' (Team)' : ''}: <strong>${topPlace.members.map(e => _esc(e.name)).join(' & ')}</strong>
      <span class="sr-value">(${fmtRes(topPlace.pooled_culture)})</span>
    </div>`;
  }

  const cultureLeader = [...empires].sort((a, b) => b.culture - a.culture);
  const topCulture = cultureLeader[0]?.culture ?? 0;
  const cultureWinners = cultureLeader.filter(e => e.culture >= topCulture);
  // Skip the individual line when place 1 is that same solo empire — the two
  // lines would otherwise repeat one name and one number.
  const soloWinnerIsBestIndividual =
    !topIsTeam && cultureWinners.length === 1 && topPlace?.members?.[0]?.uid === cultureWinners[0].uid;
  if (!soloWinnerIsBestIndividual) {
    html += `
    <div class="sr-culture-line">
      🎖 Best Individual: <strong>${cultureWinners.map(e => _esc(e.name)).join(', ')}</strong>
      <span class="sr-value">(${fmtRes(topCulture)})</span>
    </div>`;
  }

  return html;
}

function _allAwardsHtml(empires, myUid) {
  // eslint-disable-next-line eqeqeq -- uid may be int from API vs string from JWT
  const me = myUid != null ? empires.find(e => e.uid == myUid) : null;

  const awards = [
    { icon: '🏺', label: 'Most Artifacts Secured',        desc: 'Artifacts held at season end.',                                              key: 'artifacts',                   fmt: n => `${n}` },
    { icon: '🏰', label: 'Most Powerful Defense',          desc: 'Sum of gold costs of all towers placed on the map.',                         key: 'tower_gold',                  fmt: n => `${fmtRes(n)} gold` },
    { icon: '⚔',  label: 'Most Powerful Army',             desc: 'Estimated critter combat value: critter worth × critter count per wave.',    key: 'army_gold',                   fmt: n => `${fmtRes(n)} gold` },
    { icon: '🗺',  label: 'Most Territory',                 desc: 'Number of non-void tiles owned.',                                            key: 'tile_count',                  fmt: n => `${n} tiles` },
    { icon: '⚙',  label: 'Most Workshop Investment',       desc: 'Total gold spent on all item upgrades across towers and critters.',          key: 'workshop_gold',               fmt: n => `${fmtRes(n)} gold` },
    { icon: '⚔',  label: 'Most Army Gold Invested',        desc: 'Total gold spent on waves, slots, and era upgrades (cumulative cost).',      key: 'peak_army_cost',              fmt: n => `${fmtRes(n)} gold` },
    { icon: '🗼', label: 'Most Upgraded Single Tower',     desc: 'Highest total upgrade levels on a single tower type.',   key: 'max_tower_upgrade_sum',   fmt: n => `${n} levels`, nameExtra: e => e.max_tower_upgrade_name  || '' },
    { icon: '🐉', label: 'Most Upgraded Single Critter',   desc: 'Highest total upgrade levels on a single critter type.', key: 'max_critter_upgrade_sum', fmt: n => `${n} levels`, nameExtra: e => e.max_critter_upgrade_name || '' },
    { icon: '🔬', label: 'Most Research Done',              desc: 'Total research effort of all completed knowledge items.',                    key: 'research_effort',             fmt: (n, e) => `${fmtRes(n)} effort, ${e.research_count} items` },
    { icon: '🏛',  label: 'Most Buildings Done',            desc: 'Total build effort of all completed buildings.',                             key: 'buildings_effort',            fmt: (n, e) => `${fmtRes(n)} effort, ${e.buildings_count} items` },
    { icon: '💀', label: 'Most Critters Killed',            desc: 'Total critters defeated in defense battles.',                               key: 'critters_killed',             fmt: n => fmtRes(n) },
    { icon: '🏗', label: 'Most Towers Placed',              desc: 'Total towers ever placed on the map, including replacements.',              key: 'towers_placed',               fmt: n => `${n}` },
    { icon: '💸', label: 'Most Towers Sold',                desc: 'Total towers ever sold or removed.',                                        key: 'towers_sold',                 fmt: n => `${n}` },
    { icon: '🕵', label: 'Most Spies Sent',                 desc: 'Total spy missions launched against other players.',                        key: 'spies_sent',                  fmt: n => `${n}` },
    { icon: '🏺', label: 'Most Artifacts Stolen',           desc: 'Total artifacts taken from other players.',                                 key: 'artifacts_stolen',            fmt: n => `${n}` },
    { icon: '💰', label: 'Most Gold Earned from Defense',   desc: 'Gold collected from critter kills via tower bonus rewards.',                key: 'defense_gold_earned',         fmt: n => `${fmtRes(n)} gold` },
    { icon: '🎭', label: 'Most Culture Lost to Attackers',  desc: 'Total culture taken away by successful enemy attacks.',                     key: 'culture_stolen',              fmt: n => fmtRes(n) },
    { icon: '🔬', label: 'Most Research Plundered',         desc: 'Total research effort stolen from other players.',                          key: 'research_stolen',             fmt: n => `${fmtRes(n)} effort` },
    { icon: '🎭', label: 'Most Culture Won',                desc: 'Total culture gained from winning attack battles.',                         key: 'culture_won',                 fmt: n => fmtRes(n) },
    { icon: '⏱', label: 'Longest Battle Survived',         desc: 'Duration of the longest defense battle without a breach.',                  key: 'longest_battle_ms',           fmt: n => fmtSecs(Math.round(n / 1000)) },
    { icon: '🐉', label: 'Most Upgraded Critter',           desc: 'Total workshop upgrade levels across all critter types combined.',          key: 'critter_upgrade_levels',      fmt: n => `${n} levels` },
    { icon: '🗼', label: 'Most Upgraded Tower',             desc: 'Total workshop upgrade levels across all tower types combined.',            key: 'tower_upgrade_levels',        fmt: n => `${n} levels` },
    { icon: '⏳', label: 'Longest Artifact Hold',           desc: 'Longest time a single artifact was held without being stolen.',             key: 'longest_artifact_hold_secs',  fmt: n => fmtSecs(n) },
    { icon: '⚔',  label: 'Most Attacks Sent (Human)',       desc: 'Total attack missions launched against human players.',                     key: 'attacks_sent_human',          fmt: n => `${n}` },
    { icon: '🛡', label: 'Most Attacks Suffered (Human)',   desc: 'Total incoming attacks received from human players.',                       key: 'attacks_received_human',      fmt: n => `${n}` },
    { icon: '🤖', label: 'Most AI Attacks Defeated',        desc: 'Total AI wave attacks successfully repelled.',                              key: 'defense_won_ai',              fmt: n => `${n}` },
    { icon: '💀', label: 'Most AI Attacks Lost',            desc: 'Total AI wave attacks that breached the castle.',                           key: 'defense_lost_ai',             fmt: n => `${n}` },
    { icon: '🛡', label: 'Most Attackers at Once',          desc: 'Peak number of distinct attackers in a single battle.',                     key: 'peak_incoming_attacks',       fmt: n => `${n}` },
    { icon: '⚔',  label: 'Most Incoming Armies at Once',   desc: 'Peak number of simultaneously active incoming attacks (including queued).', key: 'peak_incoming',               fmt: n => `${n}` },
  ];

  return awards.map(({ icon, label, desc, key, fmt, nameExtra }) => {
    const eName = (e) => {
      const extra = nameExtra ? nameExtra(e) : '';
      return extra ? `${_esc(e.name)} (${_esc(extra)})` : _esc(e.name);
    };

    const sorted = [...empires].sort((a, b) => (b[key] ?? 0) - (a[key] ?? 0));
    const top = sorted[0]?.[key] ?? 0;
    const rank1 = sorted.filter(e => (e[key] ?? 0) >= top);
    const rest2 = sorted.filter(e => !rank1.some(w => w.uid === e.uid));
    const top2val = rest2[0]?.[key] ?? null;
    const rank2 = top2val != null ? rest2.filter(e => (e[key] ?? 0) >= top2val) : [];
    const rest3 = rest2.filter(e => !rank2.some(w => w.uid === e.uid));
    const top3val = rest3[0]?.[key] ?? null;
    const rank3 = top3val != null ? rest3.filter(e => (e[key] ?? 0) >= top3val) : [];

    // eslint-disable-next-line eqeqeq
    const myRankGroup = me
      ? (rank1.some(e => e.uid == me.uid) ? 1
        : rank2.some(e => e.uid == me.uid) ? 2
        : rank3.some(e => e.uid == me.uid) ? 3
        : null)
      : null;
    const myPos = me
      ? sorted.findIndex(e => e.uid == me.uid) + 1 // eslint-disable-line eqeqeq
      : null;

    const nameStr = rank1.length
      ? rank1.map(e => `<strong>${eName(e)}</strong>`).join(', ')
      : '<span class="sr-none">—</span>';
    const valStr = fmt(top, rank1[0]);

    const sub2 = rank2.length
      ? `<span class="sr-award-sub">2nd: ${rank2.map(e => eName(e)).join(', ')} (${fmt(top2val, rank2[0])})</span>`
      : '';
    const sub3 = rank3.length
      ? `<span class="sr-award-sub">3rd: ${rank3.map(e => eName(e)).join(', ')} (${fmt(top3val, rank3[0])})</span>`
      : '';
    const myValStr = (me && myRankGroup == null && myPos != null)
      ? `<span class="sr-my-value">You: #${myPos} (${fmt(me[key] ?? 0, me)})</span>`
      : (me && myRankGroup != null && myRankGroup > 1)
      ? `<span class="sr-my-value">You: #${myRankGroup}</span>`
      : '';

    return `
      <div class="sr-award-row">
        <span class="sr-award-icon">${icon}</span>
        <span class="sr-award-label">${label}<span class="sr-award-desc">${_esc(desc)}</span></span>
        <span class="sr-award-winner">
          <span class="sr-award-top">${nameStr}: ${valStr}</span>
          ${sub2}${sub3}
          ${myValStr}
        </span>
      </div>`;
  }).join('');
}

function _longestSingleArtifactHoldHtml(rows, myUid) {
  if (!rows || !rows.length) return '';

  const rowStr = (r) => `${_esc(r.empire_name)} held <strong>${_esc(r.artifact_name)}</strong>: ${fmtSecs(r.held_secs)}`;

  const sorted = [...rows].sort((a, b) => (b.held_secs ?? 0) - (a.held_secs ?? 0));
  const top = sorted[0]?.held_secs ?? 0;
  const rank1 = sorted.filter(r => r.held_secs >= top);
  const rest2 = sorted.slice(rank1.length);
  const top2val = rest2[0]?.held_secs ?? null;
  const rank2 = top2val != null ? rest2.filter(r => r.held_secs >= top2val) : [];
  const rest3 = rest2.slice(rank2.length);
  const top3val = rest3[0]?.held_secs ?? null;
  const rank3 = top3val != null ? rest3.filter(r => r.held_secs >= top3val) : [];

  // eslint-disable-next-line eqeqeq -- uid may be int from API vs string from JWT
  const isMyRow = (r) => myUid != null && r.uid == myUid;
  const myRankGroup = rank1.some(isMyRow) ? 1 : rank2.some(isMyRow) ? 2 : rank3.some(isMyRow) ? 3 : null;
  const myBestIdx = myUid != null ? sorted.findIndex(isMyRow) : -1;
  const myBestRow = myBestIdx >= 0 ? sorted[myBestIdx] : null;

  const nameStr = rank1.map(r => `<strong>${rowStr(r)}</strong>`).join(', ');
  const sub2 = rank2.length ? `<span class="sr-award-sub">2nd: ${rank2.map(rowStr).join(', ')}</span>` : '';
  const sub3 = rank3.length ? `<span class="sr-award-sub">3rd: ${rank3.map(rowStr).join(', ')}</span>` : '';
  const myValStr = (myBestRow && myRankGroup == null)
    ? `<span class="sr-my-value">You: #${myBestIdx + 1} (${rowStr(myBestRow)})</span>`
    : (myBestRow && myRankGroup != null && myRankGroup > 1)
    ? `<span class="sr-my-value">You: #${myRankGroup}</span>`
    : '';

  return `
    <div class="sr-award-row">
      <span class="sr-award-icon">📜</span>
      <span class="sr-award-label">Longest Single Artifact Hold<span class="sr-award-desc">The artifact held longest by a single empire without being stolen, across all players.</span></span>
      <span class="sr-award-winner">
        <span class="sr-award-top">${nameStr}</span>
        ${sub2}${sub3}
        ${myValStr}
      </span>
    </div>`;
}

const _ERA_LABELS = {
  stone: 'Stone Age', neolithic: 'Neolithic', bronze: 'Bronze Age', iron: 'Iron Age',
  medieval: 'Medieval', renaissance: 'Renaissance', industrial: 'Industrial',
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

export default { id: 'season-results', title: 'Season Results', init, enter, leave };
