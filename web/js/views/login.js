/**
 * Login view — landing page + auth via REST API.
 */

import { rest } from '../rest.js';

/** @type {import('../api.js').ApiClient} */
let api;
/** @type {import('../state.js').StateStore} */
let st;
/** @type {HTMLElement} */
let container;

// [name, ext, aspectRatio]  ratio = frameW/frameH
const _CRITTERS = [
  ['warrior', 'webp', 2 / 3],
  ['knight', 'webp', 2 / 3],
  ['horseman_fast', 'webp', 1],
  ['legionary', 'webp', 2 / 3],
  ['swordman', 'webp', 2 / 3],
  ['ninja', 'webp', 2 / 3],
  ['musketeer', 'webp', 2 / 3],
  ['the_king', 'webp', 2 / 3],
  ['mech_warrior', 'webp', 1],
  ['specops', 'webp', 2 / 3],
  ['dragooner', 'webp', 1],
  ['samurai', 'webp', 2 / 3],
  ['crusader', 'webp', 2 / 3],
  ['siege_tank', 'webp', 1],
  ['pikeneer', 'webp', 2 / 3],
];

const _STRUCTURES = [
  'arrow_tower',
  'fire_tower',
  'catapults',
  'heavy_tower',
  'cannon_tower',
  'ice_tower',
  'rocket_tower',
  'mg_bunker',
  'tar_tower',
  'sniper_tower',
  'torch_tower',
  'ballista_tower',
];

const _RULERS = [
  { id: 'maja', name: 'Maja Soulstone', description: 'A brilliant archivist and time-scholar. Maja accelerates research and makes every discovery more rewarding — the ideal ruler for empires built on knowledge.', skills: [
    { name: 'Chrono-Scholar\'s Insight', description: 'Boosts your research speed.' },
    { name: 'Scholar\'s Bounty', description: 'Grants a gold lump sum for completing research.' },
    { name: 'Erudite Synergy', description: 'Enhances the productivity of scientists.' },
    { name: 'Grand Architect\'s Decree', description: 'Reduces the cost of workshop tech.' },
  ]},
  { id: 'nandi', name: 'Nandi', description: 'A charismatic cultural patron who inspires the people. Nandi amplifies citizen output and floods the empire with culture — the soul of a flourishing civilization.', skills: [
    { name: 'Voice of the Commons', description: 'Reduces the cost of citizen upgrades.' },
    { name: 'Symphony of Toil', description: 'Increases the effect of citizens.' },
    { name: 'Cultural Footprint', description: 'Reduces the costs of acquiring new land.' },
    { name: 'Grand Apotheosis', description: 'Grants a cultural blessing to your empire.' },
  ]},
  { id: 'lucien', name: 'Lucien Duskbane', description: 'A cunning merchant lord and master of commerce. Lucien turns every trade into gold and every building into an investment — the ruler for those who value wealth above all.', skills: [
    { name: 'Golden Interest', description: 'Increases the gold you gain.' },
    { name: 'Guild Monopoly', description: 'Reduces the cost of buildings.' },
    { name: 'Tribute of the Masses', description: 'Scientists and artists generate gold.' },
    { name: 'Grand Bailout', description: 'Provides a large lump sum of gold when a skill is upgraded.' },
  ]},
  { id: 'borin', name: 'Borin Stonehelm', description: 'A battle-hardened dwarf lord and master builder. Borin turns defense into dominance — reinforcing towers, reclaiming gold from sold structures, and outlasting every siege.', skills: [
    { name: 'Juggernauts Resolve', description: 'Largely regenerate life during battles.' },
    { name: 'Scrap and Salvage', description: 'Increases the refund you receive when selling towers.' },
    { name: 'Undying Defiance', description: 'Restores life after suffering a defeat.' },
    { name: 'Fortress Bastion', description: 'Increases the delay between incoming waves.' },
  ]},
  { id: 'alric', name: 'Alric Shadowmere', description: 'A shadowy tactician who moves armies like shadows across the map. Alric expands territory cheaply and strikes faster than any opponent can prepare for.', skills: [
    { name: 'Shadow Conscription', description: 'Reduces the cost of army slots.' },
    { name: 'Umbral Evolution', description: 'Reduces the cost of upgrading waves to the next era.' },
    { name: 'Grand Larceny', description: 'Increases your chances to steal an artifact.' },
    { name: 'Desolated Siege', description: 'Decreases the siege time of attacked empires.' },
  ]},
];


function _critterEl([name, ext, ratio]) {
  const h = 60;
  const w = Math.round(h * ratio);
  return `<div class="lp-sprite lp-sprite--critter" title="${name}"
    style="width:${w}px;height:${h}px;background-image:url('/assets/sprites/critters/${name}/${name}.${ext}');"></div>`;
}

function _structureEl(name) {
  return `<div class="lp-sprite lp-sprite--structure" title="${name}"
    style="background-image:url('/assets/sprites/structures/${name}/${name}.webp');"></div>`;
}

function init(el, _api, _state) {
  container = el;
  api = _api;
  st = _state;

  const critterRow = _CRITTERS.map(_critterEl).join('');
  const structureRow = _STRUCTURES.map(_structureEl).join('');

  container.innerHTML = `
    <!-- ── Sticky top nav ───────────────────────── -->
    <div class="lp-topnav">
      <div class="lp-topnav-inner">
        <div id="login-error" class="error-msg" hidden></div>
        <div class="lp-topnav-actions">
          <input type="text" id="login-user" autocomplete="username" placeholder="Username" class="lp-topnav-input">
          <input type="password" id="login-pwd" autocomplete="current-password" placeholder="Password" class="lp-topnav-input">
          <button id="login-btn" class="lp-topnav-btn">Sign In</button>
        </div>
        <a href="#signup" class="lp-topnav-signup">New? Create Empire →</a>
      </div>
    </div>

    <div class="lp-wrap">

      <!-- ── Hero ──────────────────────────────── -->
      <div class="lp-hero">
        <img src="/assets/sprites/banner.webp" alt="Relics &amp; Rockets — Multiplayer Tower Defense Strategy Game"
             width="1024" height="254" fetchpriority="high">
        <div class="lp-hero__text">
          <h1 class="lp-title">Relics'n'Rockets</h1>
          <p class="lp-tagline">Rise from the Stone Age to the Future.<br>Research, build, defend, and conquer.</p>
          <p class="lp-mmotag">Join hundreds of players — forge alliances, pick your rivals, and leave your mark on a living world.</p>
          <p class="lp-early-access">⚠ Early Access — expect bugs, occasional outages, and frequent updates. Your feedback shapes the game.</p>
          <div class="lp-parade">${critterRow}</div>
        </div>
      </div>

      <!-- ── Features ──────────────────────────── -->
      <div class="lp-features">
        <div class="lp-feature">
          <div class="lp-feat-icon">🔬</div>
          <div class="lp-feat-title">Research</div>
          <div class="lp-feat-desc">Unlock 73 technologies across 9 eras — from early craftsmanship to cold fusion and space age engineering.</div>
        </div>
        <div class="lp-feature">
          <div class="lp-feat-icon">🏛</div>
          <div class="lp-feat-title">Buildings</div>
          <div class="lp-feat-desc">Erect markets, academies and barracks. Every structure strengthens your economy and fuels your war machine.</div>
        </div>
        <div class="lp-feature">
          <div class="lp-feat-icon">🛡</div>
          <div class="lp-feat-title">Defense</div>
          <div class="lp-feat-desc">Design your hex-map fortress. Place towers, traps and walls to stop every wave before it reaches your castle.</div>
        </div>
        <div class="lp-feature">
          <div class="lp-feat-icon">⚔</div>
          <div class="lp-feat-title">Army</div>
          <div class="lp-feat-desc">Compose armies from dozens of unit types — warriors, cavalry, tanks and beyond. Send them to raid rival empires.</div>
        </div>
      </div>

      <!-- ── Structure showcase ────────────────── -->
      <div class="lp-struct-row">${structureRow}</div>

      <!-- ── Rulers ───────────────────────────── -->
      <div class="lp-section-title">Choose your Ruler</div>
      <div class="lp-rulers-wrap">
        <button class="lp-rulers-arrow lp-rulers-arrow--prev" aria-label="Previous ruler">&#8249;</button>
        <div class="lp-rulers" id="lp-rulers-track">
          ${_RULERS.map(r => `
          <div class="lp-ruler-card" style="background-image:url('/assets/sprites/ruler/${r.id}/${r.id}_splash.webp')">
            <div class="lp-ruler-info">
              <div class="lp-ruler-name">${r.name}</div>
              <div class="lp-ruler-desc">${r.description}</div>
              <div class="lp-ruler-skills">
                ${r.skills.map(s => `<div class="lp-ruler-skill"><span class="lp-skill-name">${s.name}</span> — ${s.description}</div>`).join('')}
              </div>
            </div>
          </div>`).join('')}
        </div>
        <button class="lp-rulers-arrow lp-rulers-arrow--next" aria-label="Next ruler">&#8250;</button>
      </div>

      <!-- ── Epic Buildings ────────────────────── -->
      <div class="lp-section-title">✦ Defining Choices</div>
      <div class="lp-epic-teaser">
        <p>Each era confronts you with a decision that cannot be undone. Two powerful buildings — <strong>choose one, lose the other forever.</strong></p>
        <p>Will you invest in knowledge or military might? Expand your territory or fill your treasury? Strengthen your defenses or accelerate your advance? Every empire charts a different course.</p>
        <p class="lp-epic-teaser-hint">Every choice has consequences. No second chances.</p>
      </div>

    </div>
  `;

  const track = container.querySelector('#lp-rulers-track');
  const cardWidth = () => {
    const card = track?.querySelector('.lp-ruler-card');
    if (!card) return 220;
    return card.getBoundingClientRect().width + 12; // card + gap
  };
  container.querySelector('.lp-rulers-arrow--prev')?.addEventListener('click', () => {
    track?.scrollBy({ left: -cardWidth(), behavior: 'smooth' });
  });
  container.querySelector('.lp-rulers-arrow--next')?.addEventListener('click', () => {
    track?.scrollBy({ left: cardWidth(), behavior: 'smooth' });
  });

  container.querySelector('#login-btn').addEventListener('click', onLogin);
  container.querySelector('#login-pwd').addEventListener('keydown', (e) => {
    if (e.key === 'Enter') onLogin();
  });
}

async function onLogin() {
  const user = document.getElementById('login-user').value.trim();
  const pwd = document.getElementById('login-pwd').value;
  const errEl = document.getElementById('login-error');

  if (!user || !pwd) {
    errEl.textContent = 'Username and password required';
    errEl.hidden = false;
    return;
  }

  try {
    const resp = await rest.login(user, pwd);
    if (resp.success) {
      window.location.hash = '#status';
    } else {
      errEl.textContent = resp.reason || 'Login failed';
      errEl.hidden = false;
    }
  } catch (err) {
    errEl.textContent = err.message;
    errEl.hidden = false;
  }
}

function enter() {
  document.getElementById('app')?.classList.add('lp-view');
  const errEl = document.getElementById('login-error');
  if (errEl) errEl.hidden = true;
  // Move topnav outside #app so mobile overflow constraints don't apply
  const topnav = container.querySelector('.lp-topnav');
  const app = document.getElementById('app');
  if (topnav && app?.parentNode) {
    app.parentNode.insertBefore(topnav, app);
    // Let layout settle, then tell CSS how tall the topnav is (for banner offset)
    requestAnimationFrame(() => {
      document.documentElement.style.setProperty('--lp-topnav-h', topnav.offsetHeight + 'px');
    });
  }
}

function leave() {
  document.getElementById('app')?.classList.remove('lp-view');
  // Restore topnav back inside the login container
  const topnav = document.querySelector('.lp-topnav');
  if (topnav && container) {
    container.insertBefore(topnav, container.firstChild);
  }
}

export default {
  id: 'login',
  title: 'Login',
  init,
  enter,
  leave,
};
