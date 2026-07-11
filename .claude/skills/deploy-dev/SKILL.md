---
name: deploy-dev
description: Build the frontend (Vite) and deploy the dev environment. Use after any JS/CSS/backend change that should be visible on dev. Never deploys prod.
---

# Deploy to dev

Frontend build and deploy must always run together — dev serves `web/dist/`,
not raw source files.

```bash
export NVM_DIR="$HOME/.nvm" && . "$NVM_DIR/nvm.sh"
cd web && npm run build && cd .. && ./deploy.sh dev
```

- `npm run build` also regenerates `web/api.html` from `docs/API.md` and optimizes assets.
- Watch logs afterwards with `./attach.sh dev`.
- **Never** run `./deploy.sh prod` or `./deploy.sh both` from this skill —
  prod deploys require explicit user confirmation.
