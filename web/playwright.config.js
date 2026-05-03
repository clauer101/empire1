// @ts-check
import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright config for smoke tests.
 *
 * Target: DEV environment by default (localhost:8100 web, localhost:8180 gameserver).
 * NEVER run against prod — globalSetup enforces this by rejecting port 8080.
 *
 * Run:  npx playwright test
 *       BASE_URL=http://localhost:8100 API_URL=http://localhost:8180 npx playwright test
 *
 * Cleanup: set ADMIN_PASS env var so globalTeardown can delete the smoke test user.
 *   ADMIN_PASS=... npx playwright test
 */
export default defineConfig({
  testDir: './e2e',
  testMatch: '**/*.spec.js',

  globalSetup:    './e2e/globalSetup.js',
  globalTeardown: './e2e/globalTeardown.js',

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
    // Default to dev environment — never prod
    baseURL: process.env.BASE_URL || 'http://localhost:8100',

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
