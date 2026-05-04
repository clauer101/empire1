import { rest } from '../rest.js';

let container;

const PUSH_KEY = 'push_notifications_enabled';

async function _subscribePush() {
  if (!('serviceWorker' in navigator) || !('PushManager' in window)) return;
  const reg = await navigator.serviceWorker.ready;
  let sub = await reg.pushManager.getSubscription();
  if (sub) return; // already subscribed
  const res = await fetch('/api/push/vapid-public-key');
  const { key } = await res.json();
  const raw = atob(key.replace(/-/g, '+').replace(/_/g, '/'));
  const keyBytes = Uint8Array.from([...raw].map((c) => c.charCodeAt(0)));
  sub = await reg.pushManager.subscribe({ userVisibleOnly: true, applicationServerKey: keyBytes });
  await fetch('/api/push/subscribe', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${rest.getToken()}` },
    body: JSON.stringify({ subscription: sub.toJSON() }),
  });
}

async function _unsubscribePush() {
  if (!('serviceWorker' in navigator)) return;
  const reg = await navigator.serviceWorker.ready;
  const sub = await reg.pushManager.getSubscription();
  if (!sub) return;
  await fetch('/api/push/subscribe', {
    method: 'DELETE',
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${rest.getToken()}` },
    body: JSON.stringify({ subscription: sub.toJSON() }),
  });
  await sub.unsubscribe();
}

function init(el) {
  container = el;
}

function enter() {
  const isIos = /iphone|ipad|ipod/i.test(navigator.userAgent);
  const isStandalone =
    window.matchMedia('(display-mode: standalone)').matches || navigator.standalone === true;
  const pushSupported =
    'serviceWorker' in navigator &&
    'PushManager' in window &&
    window.isSecureContext &&
    (!isIos || isStandalone);
  const pushHint = !window.isSecureContext
    ? 'Requires HTTPS'
    : !('serviceWorker' in navigator)
      ? 'Service Worker not supported'
      : isIos && !isStandalone
        ? 'Add to home screen to enable'
        : !('PushManager' in window)
          ? 'Not supported in this browser'
          : '';
  const pushEnabled = localStorage.getItem(PUSH_KEY) === '1';

  container.innerHTML = `
    <div style="display:flex;flex-direction:column;align-items:center;justify-content:center;min-height:60vh;gap:20px;">
      <div style="font-size:1.2em;font-weight:bold;">Sign out of your account?</div>
      <button id="logout-confirm-btn" style="min-width:140px;">Sign Out</button>
      <div style="display:flex;flex-direction:column;align-items:center;gap:6px;margin-top:8px;">
        <div style="display:flex;align-items:center;gap:10px;">
          <label style="position:relative;display:inline-block;width:44px;height:24px;">
            <input type="checkbox" id="push-toggle" ${pushEnabled && pushSupported ? 'checked' : ''} ${pushSupported ? '' : 'disabled'} style="opacity:0;width:0;height:0;">
            <span id="push-track" style="position:absolute;cursor:${pushSupported ? 'pointer' : 'default'};inset:0;background:${pushEnabled && pushSupported ? 'var(--accent,#4fc3f7)' : 'var(--border,#444)'};border-radius:24px;transition:.2s;opacity:${pushSupported ? '1' : '0.4'};">
              <span id="push-knob" style="position:absolute;height:18px;width:18px;left:${pushEnabled && pushSupported ? '23px' : '3px'};bottom:3px;background:#fff;border-radius:50%;transition:.2s;"></span>
            </span>
          </label>
          <span style="font-size:0.9em;color:var(--text-dim);">Battle notifications</span>
        </div>
        ${!pushSupported ? `<span style="font-size:0.75em;color:var(--text-dim);">${pushHint}</span>` : ''}
      </div>
    </div>
  `;

  container.querySelector('#logout-confirm-btn').addEventListener('click', () => {
    rest.logout();
    window.location.hash = '#login';
  });

  const toggle = container.querySelector('#push-toggle');
  if (!pushSupported || !toggle) return;
  const knob = container.querySelector('#push-knob');
  const track = knob.parentElement;

  toggle.addEventListener('change', async () => {
    const on = toggle.checked;
    knob.style.left = on ? '23px' : '3px';
    track.style.background = on ? 'var(--accent,#4fc3f7)' : 'var(--border,#444)';
    if (on) {
      try {
        await _subscribePush();
        localStorage.setItem(PUSH_KEY, '1');
      } catch (e) {
        console.warn('[push] subscribe failed:', e);
        toggle.checked = false;
        knob.style.left = '3px';
        track.style.background = 'var(--border,#444)';
      }
    } else {
      await _unsubscribePush();
      localStorage.removeItem(PUSH_KEY);
    }
  });
}

function leave() {}

export default { id: 'logout', title: 'Sign Out', init, enter, leave };
