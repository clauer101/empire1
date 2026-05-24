import { rest } from '../rest.js';

let container;

const CARD = 'background:var(--surface);border-radius:var(--radius);padding:20px 24px;width:100%;max-width:340px;box-sizing:border-box;display:flex;flex-direction:column;gap:12px;';
const LABEL = 'font-size:0.75em;font-weight:600;text-transform:uppercase;letter-spacing:0.06em;color:var(--text-dim,#888);margin-bottom:2px;';
const BTN = 'width:100%;padding:9px 0;font-size:0.95em;text-align:center;';

function _renameAllowed(summary) {
  if (!summary?.season_reset_triggered) return false;
  const toUtcMs = s => s ? new Date(s.endsWith('Z') || s.includes('+') ? s : s + 'Z').getTime() : 0;
  const now = Date.now();
  const leadtime = toUtcMs(summary.next_season_leadtime);
  // Allow rename after wipe; season_reset_triggered is cleared by server once new season starts
  return now >= leadtime;
}

function init(el) {
  container = el;
}

async function enter() {
  let summary = null;
  try { const r = await rest.getSummary(); summary = r; } catch (_) {}
  const showRename = _renameAllowed(summary);

  container.innerHTML = `
    <div style="display:flex;flex-direction:column;align-items:center;padding:32px 16px;gap:16px;">

      <div style="${CARD}">
        <div style="${LABEL}">Community</div>
        <a href="https://discord.gg/U4SEZB5BT" target="_blank" rel="noopener" style="
          display:flex;align-items:center;justify-content:center;gap:8px;
          background:#5865F2;color:#fff;border-radius:6px;
          padding:9px 0;width:100%;font-size:0.95em;font-weight:600;text-decoration:none;box-sizing:border-box;
        ">
          <svg width="18" height="18" viewBox="0 0 71 55" fill="white" xmlns="http://www.w3.org/2000/svg"><path d="M60.1 4.9A58.5 58.5 0 0 0 45.5.4a.2.2 0 0 0-.2.1 40.8 40.8 0 0 0-1.8 3.7 54 54 0 0 0-16.2 0A37.7 37.7 0 0 0 25.5.5a.2.2 0 0 0-.2-.1 58.4 58.4 0 0 0-14.6 4.5.2.2 0 0 0-.1.1C1.6 18.1-.9 30.9.3 43.5c0 .1.1.1.1.2a58.8 58.8 0 0 0 17.7 8.9.2.2 0 0 0 .2-.1 42 42 0 0 0 3.6-5.9.2.2 0 0 0-.1-.3 38.7 38.7 0 0 1-5.5-2.6.2.2 0 0 1 0-.4l1.1-.8a.2.2 0 0 1 .2 0c11.6 5.3 24.1 5.3 35.5 0a.2.2 0 0 1 .2 0l1.1.8a.2.2 0 0 1 0 .4 36.1 36.1 0 0 1-5.5 2.6.2.2 0 0 0-.1.3 47.1 47.1 0 0 0 3.6 5.9.2.2 0 0 0 .2.1 58.6 58.6 0 0 0 17.8-8.9.2.2 0 0 0 .1-.2c1.5-15-2.5-27.7-10.6-39.1a.2.2 0 0 0-.1-.1zM23.7 35.8c-3.5 0-6.4-3.2-6.4-7.2s2.8-7.2 6.4-7.2c3.6 0 6.5 3.3 6.4 7.2 0 4-2.8 7.2-6.4 7.2zm23.7 0c-3.5 0-6.4-3.2-6.4-7.2s2.8-7.2 6.4-7.2c3.6 0 6.5 3.3 6.4 7.2 0 4-2.8 7.2-6.4 7.2z"/></svg>
          Join our Discord
        </a>
      </div>

      ${showRename ? `
      <div style="${CARD}">
        <div style="${LABEL}">Empire</div>
        <button id="rename-empire-btn" style="${BTN}">Rename Empire</button>
      </div>` : ''}

      <div style="${CARD}">
        <div style="${LABEL}">Account</div>
        <button id="logout-confirm-btn" style="${BTN}">Sign Out</button>
      </div>

    </div>

    <div id="rename-overlay" style="display:none;position:fixed;inset:0;z-index:9999;background:rgba(0,0,0,0.55);align-items:center;justify-content:center;">
      <div style="background:var(--surface);border-radius:var(--radius);padding:24px;min-width:280px;max-width:360px;width:90%;position:relative;display:flex;flex-direction:column;gap:12px;">
        <button id="rename-close" style="position:absolute;top:6px;right:8px;background:none;border:none;cursor:pointer;color:#888;font-size:16px;">✕</button>
        <div style="font-weight:600;font-size:1.05em;">Rename your Empire</div>
        <input type="text" id="rename-input" placeholder="New empire name" maxlength="40" style="width:100%;box-sizing:border-box;" />
        <div id="rename-msg" style="font-size:0.82em;min-height:14px;"></div>
        <button id="rename-confirm" style="width:100%;">Rename</button>
      </div>
    </div>
  `;

  container.querySelector('#logout-confirm-btn').addEventListener('click', () => {
    rest.logout();
    window.location.hash = '#login';
  });

  const overlay = container.querySelector('#rename-overlay');
  const input = container.querySelector('#rename-input');
  const msg = container.querySelector('#rename-msg');

  container.querySelector('#rename-empire-btn')?.addEventListener('click', () => {
    input.value = summary?.name || '';
    msg.textContent = '';
    overlay.style.display = 'flex';
    input.focus();
    input.select();
  });

  container.querySelector('#rename-close').addEventListener('click', () => {
    overlay.style.display = 'none';
  });

  overlay.addEventListener('click', (e) => {
    if (e.target === overlay) overlay.style.display = 'none';
  });

  container.querySelector('#rename-confirm').addEventListener('click', async () => {
    const name = input.value.trim();
    if (name.length < 3) { msg.textContent = 'Name must be at least 3 characters'; msg.style.color = 'var(--danger)'; return; }
    const btn = container.querySelector('#rename-confirm');
    btn.disabled = true;
    try {
      const resp = await rest.renameEmpire(name);
      if (resp.success) {
        msg.textContent = '✓ Empire renamed!';
        msg.style.color = 'var(--success)';
        setTimeout(() => { overlay.style.display = 'none'; }, 1200);
      } else {
        msg.textContent = `✗ ${resp.error || 'Failed'}`;
        msg.style.color = 'var(--danger)';
      }
    } catch (err) {
      msg.textContent = `✗ ${err.message}`;
      msg.style.color = 'var(--danger)';
    } finally {
      btn.disabled = false;
    }
  });

  input.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') container.querySelector('#rename-confirm').click();
  });
}

function leave() {}

export default { id: 'logout', title: 'Settings', init, enter, leave };
