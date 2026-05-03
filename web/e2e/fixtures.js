/**
 * Shared Playwright fixtures and helpers for smoke tests.
 *
 * The SPA determines its REST base URL from ?rest=<url> or window.location.origin.
 * In production, nginx proxies /api → gameserver, so origin works.
 * In direct-to-webserver tests (no nginx), we pass ?rest=API_URL so the SPA
 * hits the gameserver directly.
 *
 * Environment variables:
 *   BASE_URL  — web server URL (default: http://localhost:8000)
 *   API_URL   — gameserver REST URL (default: http://localhost:8080)
 *
 * When BASE_URL and API_URL share the same origin (production via nginx),
 * the ?rest param is omitted. When they differ (local dev), it's appended.
 */
import { test, expect } from '@playwright/test';

export const TEST_USER   = 'smoke_test_user';
export const TEST_PASS   = 'Smoke_T3st_P@ss!';
export const TEST_EMPIRE = 'SmokeEmpire';

const BASE_URL = process.env.BASE_URL || 'http://localhost:8000';
const API_URL  = process.env.API_URL  || 'http://localhost:8080';

// Cache the login token for the test session to avoid hitting the 5/minute rate limit
let _cachedToken = null;

/** URL to open in browser — appends ?rest= when API differs from BASE */
export function appUrl(hash = '') {
  const base = new URL(BASE_URL);
  const api  = new URL(API_URL);
  const restParam = (base.origin !== api.origin) ? `?rest=${API_URL}` : '';
  return `${BASE_URL}/${restParam}${hash}`;
}

/**
 * Create the test account via REST if it doesn't exist yet.
 * Safe to call multiple times — already-exists responses are ignored.
 */
export async function ensureTestUser(request) {
  const resp = await request.post(`${API_URL}/api/auth/signup`, {
    data: { username: TEST_USER, password: TEST_PASS, empire_name: TEST_EMPIRE },
  });
  if (!resp.ok()) {
    const body = await resp.json().catch(() => ({}));
    // success=false with "already" in reason = account exists, that's fine
    if (body.success === false && !String(body.reason || '').toLowerCase().includes('taken')) {
      throw new Error(`ensureTestUser failed: ${resp.status()} ${JSON.stringify(body)}`);
    }
  }
}

/**
 * Log in via the UI login form and wait for the dashboard to appear.
 * After a successful login the router sets window.location.hash to '#status'
 * and the Empire Status panel becomes visible.
 *
 * Note: auth endpoints are rate-limited to 5/minute. Use loginViaApi for tests
 * that don't specifically need to test the login form UI.
 */
export async function loginAs(page, username = TEST_USER, password = TEST_PASS) {
  await page.goto(appUrl('#login'));
  await page.waitForSelector('#login-user', { timeout: 8000 });
  await page.fill('#login-user', username);
  await page.fill('#login-pwd', password);
  await page.click('#login-btn');

  // After successful login the router navigates to #status — wait for the empires section
  await page.waitForSelector('#empires-section', { timeout: 15000 });
}

/**
 * Log in by injecting a JWT obtained via the REST API directly into localStorage,
 * then navigate to #status. Bypasses the login form — avoids the auth rate limit
 * (5/minute) when many tests run sequentially.
 */
export async function loginViaApi(page, request, username = TEST_USER, password = TEST_PASS) {
  // Reuse a cached token to avoid the 5/minute auth rate limit
  if (!_cachedToken || username !== TEST_USER) {
    const resp = await request.post(`${API_URL}/api/auth/login`, {
      data: { username, password },
    });
    const body = await resp.json();
    if (!body.success) throw new Error(`loginViaApi failed: ${JSON.stringify(body)}`);
    if (username === TEST_USER) _cachedToken = body.token;
    body.token = body.token; // keep local ref
    var token = body.token;
  } else {
    var token = _cachedToken;
  }

  // Inject token via addInitScript so it's in localStorage before app.js runs.
  // Then do a full page load to #status so tryAutoLogin picks it up.
  await page.addInitScript(
    ([tok, user]) => {
      localStorage.setItem('e3_jwt_token', tok);
      localStorage.setItem('e3_username', user);
    },
    [token, username]
  );
  await page.goto(appUrl('#status'));
  await page.waitForSelector('#empires-section', { timeout: 15000 });
}

export { test, expect };
