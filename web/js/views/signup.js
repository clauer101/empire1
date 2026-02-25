/**
 * Signup view — create a new account via REST API.
 */

import { rest } from '../rest.js';

/** @type {import('../api.js').ApiClient} */
let api;
/** @type {import('../state.js').StateStore} */
let st;
/** @type {HTMLElement} */
let container;

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

function init(el, _api, _state) {
  container = el;
  api = _api;
  st = _state;

  container.innerHTML = `
    <div class="login-wrapper">
      <div class="login-card">
        <h2>Create Account</h2>
        <div id="signup-error" class="error-msg" hidden></div>
        <div class="form-group">
          <label for="signup-empire">Empire Name</label>
          <input type="text" id="signup-empire" placeholder="Name your empire" maxlength="30">
        </div>
        <div class="form-group">
          <label for="signup-user">Alias (Username)</label>
          <input type="text" id="signup-user" autocomplete="username" placeholder="Choose a username" maxlength="20">
        </div>
        <div class="form-group">
          <label for="signup-email">Email</label>
          <input type="email" id="signup-email" placeholder="you@example.com">
        </div>
        <div class="form-group">
          <label for="signup-pwd">Password</label>
          <input type="password" id="signup-pwd" autocomplete="new-password" placeholder="Choose a password">
        </div>
        <div class="form-group">
          <label for="signup-pwd2">Confirm Password</label>
          <input type="password" id="signup-pwd2" autocomplete="new-password" placeholder="Repeat password">
        </div>
        <button id="signup-btn" style="width:100%;justify-content:center">Sign Up</button>
        <p class="dsgvo-notice">
          Mit der Registrierung werden Name und E-Mail-Adresse zur Verwaltung
          deines Kontos verarbeitet (Art.&nbsp;6 Abs.&nbsp;1 lit.&nbsp;b DSGVO).
          <a href="/datenschutz.html" target="_blank" rel="noopener">Mehr erfahren</a>
        </p>
        <p class="form-footer">Already have an account? <a href="#login">Log in</a></p>
      </div>
    </div>
  `;

  container.querySelector('#signup-btn').addEventListener('click', onSignup);
  container.querySelector('#signup-pwd2').addEventListener('keydown', (e) => {
    if (e.key === 'Enter') onSignup();
  });
}

function showError(msg) {
  const el = container.querySelector('#signup-error');
  el.textContent = msg;
  el.hidden = false;
}

async function onSignup() {
  const empire = container.querySelector('#signup-empire').value.trim();
  const user = container.querySelector('#signup-user').value.trim();
  const email = container.querySelector('#signup-email').value.trim();
  const pwd = container.querySelector('#signup-pwd').value;
  const pwd2 = container.querySelector('#signup-pwd2').value;
  const errEl = container.querySelector('#signup-error');
  errEl.hidden = true;

  // ── Client-side validation ──────────────────────────────
  if (!empire) { showError('Empire name is required'); return; }
  if (!user)   { showError('Username is required'); return; }
  if (!email)  { showError('Email is required'); return; }
  if (!EMAIL_RE.test(email)) { showError('Invalid email format'); return; }
  if (!pwd)    { showError('Password is required'); return; }
  if (pwd.length < 4) { showError('Password must be at least 4 characters'); return; }
  if (pwd !== pwd2) { showError('Passwords do not match'); return; }

  try {
    const resp = await rest.signup(user, pwd, email, empire);
    if (resp.success) {
      window.location.hash = '#login';
    } else {
      showError(resp.reason || 'Signup failed');
    }
  } catch (err) {
    showError(err.message);
  }
}

function enter() {
  const errEl = container.querySelector('#signup-error');
  if (errEl) errEl.hidden = true;
}

function leave() {}

export default {
  id: 'signup',
  title: 'Sign Up',
  init,
  enter,
  leave,
};
