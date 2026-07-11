/**
 * Reset Password view — reached via #reset-password/<token> links from
 * password reset emails. Standalone page (not an overlay), like legal.js.
 */

import { rest } from '../rest.js';
import { pageTitle } from '../lib/page_title.js';

let container;

function _tokenFromHash() {
  const hash = window.location.hash.replace('#', '');
  const slashIdx = hash.indexOf('/');
  return slashIdx > 0 ? hash.substring(slashIdx + 1) : '';
}

function init(el) {
  container = el;
}

function enter() {
  pageTitle.set('Reset Password');
  const token = _tokenFromHash();

  container.innerHTML = `
    <div style="max-width:360px;margin:64px auto;padding:24px;background:var(--surface);border-radius:var(--radius);display:flex;flex-direction:column;gap:12px;">
      <div style="font-weight:600;font-size:1.1em;">Reset Password</div>
      <input type="password" id="rp-new" placeholder="New password" autocomplete="new-password" style="width:100%;box-sizing:border-box;" />
      <input type="password" id="rp-new2" placeholder="Repeat new password" autocomplete="new-password" style="width:100%;box-sizing:border-box;" />
      <div id="rp-msg" style="font-size:0.85em;min-height:16px;"></div>
      <button id="rp-confirm" style="width:100%;">Set New Password</button>
      <a href="#login" style="text-align:center;font-size:0.85em;color:var(--text-dim);">Back to login</a>
    </div>
  `;

  const newPwd = container.querySelector('#rp-new');
  const newPwd2 = container.querySelector('#rp-new2');
  const msg = container.querySelector('#rp-msg');
  const btn = container.querySelector('#rp-confirm');

  if (!token) {
    msg.textContent = '✗ Missing reset token — please use the link from your email.';
    msg.style.color = 'var(--danger)';
    btn.disabled = true;
  }

  btn.addEventListener('click', async () => {
    const next = newPwd.value;
    const next2 = newPwd2.value;
    if (next.length < 4) {
      msg.textContent = 'New password must be at least 4 characters';
      msg.style.color = 'var(--danger)';
      return;
    }
    if (next !== next2) {
      msg.textContent = 'New passwords do not match';
      msg.style.color = 'var(--danger)';
      return;
    }
    btn.disabled = true;
    try {
      const resp = await rest.resetPassword(token, next);
      if (resp.success) {
        msg.textContent = '✓ Password reset! Redirecting to login…';
        msg.style.color = 'var(--success)';
        setTimeout(() => { window.location.hash = '#login'; }, 1500);
      } else {
        msg.textContent = `✗ ${resp.error || 'Failed'}`;
        msg.style.color = 'var(--danger)';
        btn.disabled = false;
      }
    } catch (err) {
      msg.textContent = `✗ ${err.message}`;
      msg.style.color = 'var(--danger)';
      btn.disabled = false;
    }
  });

  newPwd2.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') btn.click();
  });
}

function leave() {}

export default { id: 'reset-password', title: 'Reset Password', init, enter, leave };
