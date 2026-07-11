---
name: e2e
description: Run the Playwright E2E smoke tests against the dev environment (never prod) including test-user cleanup.
---

# Playwright E2E tests (dev only)

**Never run against prod** (`localhost:8000` / `localhost:8080`) — tests create
accounts and mutate state. Prod is read-only.

```bash
cd web && BASE_URL=http://localhost:8100 API_URL=http://localhost:8180 npx playwright test
```

Prerequisite: the dev stack must be running (`./deploy.sh dev`).

Cleanup of the smoke-test user runs automatically via `web/e2e/globalTeardown.js`.
If a run aborts before teardown, delete manually:

```bash
curl -s -X DELETE http://localhost:8180/api/admin/user/smoke_test_user \
  -H "Authorization: Bearer $(cat data/dev/admin_token 2>/dev/null)"
```
