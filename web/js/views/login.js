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
  ['warrior',      'png',  2/3],
  ['knight',       'webp', 2/3],   // 170×256
  ['horseman_fast','png',  1  ],   // 80×80
  ['legionary',    'webp', 2/3],   // 170×256
  ['swordman',     'png',  2/3],
  ['ninja',        'webp', 2/3],
  ['musketeer',    'webp', 2/3],
  ['the_king',     'png',  2/3],   // 39×58
  ['mech_warrior', 'webp', 1  ],   // 50×50
  ['specops',      'png',  2/3],
  ['dragooner',    'webp', 1  ],   // 80×80
  ['samurai',      'webp', 2/3],
  ['crusader',     'webp', 2/3],
  ['siege_tank',   'webp', 1  ],   // 80×80
  ['pikeneer',     'png',  2/3],
];

const _STRUCTURES = [
  'arrow_tower', 'fire_tower', 'catapults', 'heavy_tower',
  'cannon_tower', 'ice_tower', 'rocket_tower', 'mg_bunker',
  'tar_tower', 'sniper_tower', 'torch_tower', 'ballista_tower',
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

  const critterRow   = _CRITTERS.map(_critterEl).join('');
  const structureRow = _STRUCTURES.map(_structureEl).join('');

  container.innerHTML = `
    <div class="lp-wrap">

      <!-- ── Hero ──────────────────────────────── -->
      <div class="lp-hero">
        <img src="/assets/banner.webp" alt="Relics &amp; Rockets — Multiplayer Tower Defense Strategy Game"
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

      <!-- ── Login card ────────────────────────── -->
      <div class="lp-login-wrap">
        <div class="login-card">
          <h2 class="battle-title" style="margin-bottom:20px;">🔑 Sign In</h2>
          <div id="login-error" class="error-msg" hidden></div>
          <div class="form-group">
            <label for="login-user">Username</label>
            <input type="text" id="login-user" autocomplete="username" placeholder="Enter username">
          </div>
          <div class="form-group">
            <label for="login-pwd">Password</label>
            <input type="password" id="login-pwd" autocomplete="current-password" placeholder="Enter password">
          </div>
          <button id="login-btn" style="width:100%;justify-content:center">Sign In</button>
          <p class="form-footer">No empire yet? <a href="#signup">Create one →</a></p>
        </div>
      </div>

    </div>
  `;

  container.querySelector('#login-btn').addEventListener('click', onLogin);
  container.querySelector('#login-pwd').addEventListener('keydown', (e) => {
    if (e.key === 'Enter') onLogin();
  });
}

async function onLogin() {
  const user = container.querySelector('#login-user').value.trim();
  const pwd = container.querySelector('#login-pwd').value;
  const errEl = container.querySelector('#login-error');

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
  const errEl = container.querySelector('#login-error');
  if (errEl) errEl.hidden = true;
}

function leave() {}

export default {
  id: 'login',
  title: 'Login',
  init,
  enter,
  leave,
};
