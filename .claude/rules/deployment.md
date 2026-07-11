# Deployment Rules

**Never deploy to prod without explicit user confirmation. Never write to
`data/prod/gameserver.db` while the server runs** (corrupts the aiosqlite
connection → readonly errors for all writes).

```bash
./deploy.sh prod       # build + deploy prod (requires user confirmation!)
./deploy.sh dev        # build + deploy dev
./deploy.sh both       # build + deploy both (requires user confirmation!)
./deploy.sh <env> stop # save state + stop
```

Frontend changes: always run the Vite build first (see `frontend.md`).

Live logs:
```bash
./attach.sh            # prod gameserver logs
./attach.sh dev        # dev gameserver logs
```

State and DB persistence:
- Prod: `data/prod/state.yaml`, `data/prod/gameserver.db`
- Dev:  `data/dev/state.yaml`,  `data/dev/gameserver.db`

## nginx API Routing

nginx proxies `/api/*` via a regex whitelist. When adding a **new REST endpoint**,
add its prefix to the whitelist in `nginx.conf.example` (both dev and prod server
blocks):

```
location ~ ^/api/(auth|empire|...|YOUR_NEW_PREFIX)(/|$)
```

Then:
```bash
sudo cp nginx.conf.example /etc/nginx/sites-available/empire1 && sudo nginx -t && sudo systemctl reload nginx
```

Symptom if forgotten: endpoint returns 404 from the webserver even though
`curl localhost:8180/api/your-endpoint` works.
