/**
 * Playwright globalTeardown — runs once after all tests.
 *
 * Deletes the smoke test user from the dev environment so each run
 * starts clean and no test accounts accumulate in the database.
 *
 * Requires ADMIN_USER and ADMIN_PASS env vars (default: eem / from ADMIN_PASS).
 * Silently skips if the admin credentials are not set.
 */

const API_URL    = process.env.API_URL    || 'http://localhost:8180';
const ADMIN_USER = process.env.ADMIN_USER || 'eem';
const ADMIN_PASS = process.env.ADMIN_PASS || '';
const TEST_USER  = 'smoke_test_user';

export default async function globalTeardown() {
  if (!ADMIN_PASS) {
    console.warn('[teardown] ADMIN_PASS not set — skipping smoke user cleanup');
    return;
  }

  try {
    // Get admin JWT
    const loginResp = await fetch(`${API_URL}/api/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username: ADMIN_USER, password: ADMIN_PASS }),
    });
    const loginBody = await loginResp.json();
    if (!loginBody.success) {
      console.warn(`[teardown] Admin login failed: ${loginBody.reason}`);
      return;
    }

    // Delete test user
    const delResp = await fetch(`${API_URL}/api/admin/users/${TEST_USER}`, {
      method: 'DELETE',
      headers: { Authorization: `Bearer ${loginBody.token}` },
    });
    const delBody = await delResp.json();
    if (delBody.ok) {
      console.log(`[teardown] Deleted smoke test user '${TEST_USER}'`);
    } else {
      console.warn(`[teardown] Could not delete '${TEST_USER}': ${JSON.stringify(delBody)}`);
    }
  } catch (err) {
    console.warn(`[teardown] Cleanup error: ${err.message}`);
  }
}
