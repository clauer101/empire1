#!/usr/bin/env bash
# Apply nginx.conf.example to the live site config, test, and reload nginx.
# Run from the repo root (or via SSH: bash /path/to/empire1/update_nginx.sh).
set -euo pipefail

cd "$(dirname "$0")"

sudo cp nginx.conf.example /etc/nginx/sites-available/empire1
sudo nginx -t
sudo systemctl reload nginx

echo "nginx config updated and reloaded."
