/**
 * Login view — auth_request + auto-login via URL params.
 */

/** @type {import('../api.js').ApiClient} */
let api;
/** @type {import('../state.js').StateStore} */
let st;
/** @type {HTMLElement} */
let container;

function init(el, _api, _state) {
  container = el;
  api = _api;
  st = _state;

  container.innerHTML = `
    <div class="login-wrapper">
      <div class="login-card">
        <h2>Login</h2>
        <div id="login-error" class="error-msg" hidden></div>
        <div class="form-group">
          <label for="login-user">Username</label>
          <input type="text" id="login-user" autocomplete="username" placeholder="Enter username">
        </div>
        <div class="form-group">
          <label for="login-pwd">Password</label>
          <input type="password" id="login-pwd" autocomplete="current-password" placeholder="Enter password">
        </div>
        <button id="login-btn" style="width:100%;justify-content:center">Login</button>
        <p class="form-footer">No account yet? <a href="#signup">Sign up</a></p>
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
    const resp = await api.login(user, pwd);
    if (resp.success) {
      window.location.hash = '#dashboard';
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
