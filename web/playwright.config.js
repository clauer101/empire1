// @ts-check
import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright config for smoke tests.
 *
 * Target: the web server at BASE_URL (default: http://localhost:8000).
 * The web server must be running before tests execute — no webServer auto-start,
 * because prod/dev use Docker and the servers are managed externally.
 *
 * Run: npx playwright test
 * With custom target: BASE_URL=http://dev.relicsnrockets.io npx playwright test
 */
export default defineConfig({
  testDir: './e2e',
  testMatch: '**/*.spec.js',

  // Stop on first failure to keep feedback tight
  fullyParallel: false,
  retries: 1,
  workers: 1,
  timeout: 45000,

  reporter: [
    ['list'],
    ['html', { outputFolder: 'playwright-report', open: 'never' }],
  ],

  use: {
    baseURL: process.env.BASE_URL || 'http://localhost:8000',

    // API_URL points directly at the gameserver for REST helper calls
    // (bypasses nginx; used in test fixtures only)
    extraHTTPHeaders: {
      'Accept': 'application/json',
    },

    // Capture evidence on failure
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    trace: 'retain-on-failure',

    headless: true,
  },

  projects: [
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
  ],

  // Output artifacts next to config, gitignored
  outputDir: 'playwright-results',
});
