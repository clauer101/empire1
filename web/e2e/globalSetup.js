/**
 * Playwright globalSetup — runs once before all tests.
 *
 * Verifies that the target API_URL is the DEV environment (port 8180).
 * Refuses to run against prod (port 8080) to prevent test data pollution.
 */

const API_URL = process.env.API_URL || 'http://localhost:8180';

export default async function globalSetup() {
  const url = new URL(API_URL);
  if (url.port === '8080') {
    throw new Error(
      `\n\nE2E tests must NOT run against prod (port 8080).\n` +
      `Use the dev environment instead:\n` +
      `  BASE_URL=http://localhost:8100 API_URL=http://localhost:8180 npx playwright test\n`
    );
  }
}
