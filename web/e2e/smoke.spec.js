/**
 * Smoke tests — golden-path flows for Relics & Rockets.
 *
 * Tests run sequentially (workers:1) against a live server.
 * Set BASE_URL and API_URL env vars to target dev/prod.
 *
 * Covered flows (per T4.3):
 *   1. Signup — new account creation
 *   2. Login  — existing account auth (uses UI form)
 *   3. Build  — Buildings view loads and shows items
 *   4. Tower  — Defense view loads and renders the hex canvas
 *   5. Army   — Army Composer view loads with army controls
 *   6. Status — Status view shows Known Empires section
 *   7. Logout — user can sign out
 *
 * Tests 3-7 use loginViaApi (inject JWT directly) to avoid the auth
 * rate limit of 5 requests/minute on the login endpoint.
 */

import { test, expect, ensureTestUser, loginAs, loginViaApi, appUrl } from './fixtures.js';

// ── 1. Signup ─────────────────────────────────────────────────────────────────

test('signup — new user can create an account', async ({ page }) => {
  const ts = Date.now();
  const user = `smoke_new_${ts}`;
  const pass = 'Smoke_N3w_P@ss!';

  await page.goto(appUrl('#signup'));
  // Wait for the signup form to be visible (the signup view is active)
  await page.waitForSelector('#signup-user', { timeout: 8000 });

  await page.fill('#signup-empire', `Empire_${ts}`);
  await page.fill('#signup-user', user);
  await page.fill('#signup-pwd', pass);
  await page.fill('#signup-pwd2', pass);
  await page.click('#signup-btn');

  // On success the router navigates to #login — wait for login form to become visible
  await page.waitForSelector('#login-user', { state: 'visible', timeout: 10000 });
  await expect(page.locator('#login-user')).toBeVisible();
});

// ── 2. Login ──────────────────────────────────────────────────────────────────

test('login — existing user can authenticate', async ({ page, request }) => {
  await ensureTestUser(request);
  await loginAs(page);

  // Dashboard panel visible
  await expect(page.locator('h2').filter({ hasText: /Empire Status/i })).toBeVisible();

  // JWT stored in localStorage
  const token = await page.evaluate(() => localStorage.getItem('e3_jwt_token'));
  expect(token).toBeTruthy();
});

// ── 3. Build — Buildings view loads ──────────────────────────────────────────

test('build — Buildings view renders buildable items', async ({ page, request }) => {
  await ensureTestUser(request);
  await loginViaApi(page, request);

  await page.goto(appUrl('#buildings'));
  // At least one item card must appear
  await page.waitForSelector('.item-card, [data-iid]', { timeout: 8000 });
  const cards = page.locator('.item-card, [data-iid]');
  await expect(cards.first()).toBeVisible();
});

// ── 4. Tower — Defense view loads ─────────────────────────────────────────────

test('tower — Defense view loads and renders the battle canvas', async ({ page, request }) => {
  await ensureTestUser(request);
  await loginViaApi(page, request);

  await page.goto(appUrl('#defense'));
  // Defense canvas (hex grid renderer) must be present
  await page.waitForSelector('#defense-canvas, canvas', { timeout: 12000 });
  await expect(page.locator('#defense-canvas, canvas').first()).toBeVisible();
});

// ── 5. Army — Army Composer view ──────────────────────────────────────────────

test('army — Army Composer view loads with create-army button', async ({ page, request }) => {
  await ensureTestUser(request);
  await loginViaApi(page, request);

  await page.goto(appUrl('#army'));
  // "Create Army" button must be present and visible
  await page.waitForSelector('#create-army-btn', { timeout: 8000 });
  await expect(page.locator('#create-army-btn')).toBeVisible();
});

// ── 6. Attack — Status view shows Known Empires ───────────────────────────────

test('attack — Status view shows Known Empires section', async ({ page, request }) => {
  await ensureTestUser(request);
  await loginViaApi(page, request);

  // Status view is the default after login — just poll the empires section
  await page.waitForSelector('#empires-section', { timeout: 12000 });
  const empiresSection = page.locator('#empires-section');
  await expect(empiresSection).toBeVisible();
  await expect(
    empiresSection.locator('.panel-header').filter({ hasText: /Known Empires/i })
  ).toBeVisible();
});

// ── 7. Logout ─────────────────────────────────────────────────────────────────

test('logout — user can sign out and is redirected to login', async ({ page, request }) => {
  await ensureTestUser(request);
  await loginViaApi(page, request);

  await page.goto(appUrl('#logout'));
  // Logout view shows a confirm button — click it
  await page.waitForSelector('#logout-confirm-btn', { timeout: 8000 });
  await page.click('#logout-confirm-btn');

  // After logout the router redirects to #login — wait for login form
  await page.waitForSelector('#login-user', { timeout: 8000 });
  await expect(page.locator('#login-user')).toBeVisible();

  // JWT cleared
  const token = await page.evaluate(() => localStorage.getItem('e3_jwt_token'));
  expect(token).toBeFalsy();
});
