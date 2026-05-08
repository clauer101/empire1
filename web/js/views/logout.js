import { rest } from '../rest.js';

let container;

function init(el) {
  container = el;
}

function enter() {
  container.innerHTML = `
    <div style="display:flex;flex-direction:column;align-items:center;justify-content:center;min-height:60vh;gap:20px;">
      <div style="font-size:1.2em;font-weight:bold;">Sign out of your account?</div>
      <button id="logout-confirm-btn" style="min-width:140px;">Sign Out</button>
    </div>
  `;

  container.querySelector('#logout-confirm-btn').addEventListener('click', () => {
    rest.logout();
    window.location.hash = '#login';
  });
}

function leave() {}

export default { id: 'logout', title: 'Sign Out', init, enter, leave };
