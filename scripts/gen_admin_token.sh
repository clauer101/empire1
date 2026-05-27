#!/usr/bin/env bash
# Generate admin JWT tokens for dev and/or prod and write them to data/*/admin_token.
#
# Usage:
#   ./scripts/gen_admin_token.sh          # both dev and prod
#   ./scripts/gen_admin_token.sh dev      # dev only
#   ./scripts/gen_admin_token.sh prod     # prod only

set -euo pipefail
cd "$(dirname "$0")/.."

ADMIN_USER="eem"
EXPIRY_SECONDS=$((12 * 2592000))   # 30 days (matches jwt_auth.py)

_gen() {
  local env="$1"         # dev | prod
  local env_file="$2"    # .env.dev | .env
  local db_path="$3"     # data/dev/gameserver.db | data/prod/gameserver.db
  local out="$4"         # data/dev/admin_token | data/prod/admin_token

  if [[ ! -f "$env_file" ]]; then
    echo "[$env] ERROR: $env_file not found" >&2
    return 1
  fi
  if [[ ! -f "$db_path" ]]; then
    echo "[$env] ERROR: $db_path not found" >&2
    return 1
  fi

  local secret
  secret=$(grep -E '^JWT_SECRET=' "$env_file" | cut -d= -f2-)
  if [[ -z "$secret" ]]; then
    echo "[$env] ERROR: JWT_SECRET not found in $env_file" >&2
    return 1
  fi

  local uid
  uid=$(python3 - <<PYEOF
import sqlite3, sys
db = sqlite3.connect("$db_path")
row = db.execute("SELECT uid FROM users WHERE username=?", ("$ADMIN_USER",)).fetchone()
if row is None:
    print("NOT_FOUND")
else:
    print(row[0])
PYEOF
)

  if [[ "$uid" == "NOT_FOUND" ]]; then
    echo "[$env] ERROR: user '$ADMIN_USER' not found in $db_path" >&2
    return 1
  fi

  local token
  token=$(python3 - <<PYEOF
import jwt, time
payload = {
    "uid": $uid,
    "iat": int(time.time()),
    "exp": int(time.time()) + $EXPIRY_SECONDS,
}
print(jwt.encode(payload, "$secret", algorithm="HS256"))
PYEOF
)

  mkdir -p "$(dirname "$out")"
  echo "$token" > "$out"
  # Also write to .admin-token-<env> which deploy.sh reads
  echo "$token" > ".admin-token-${env}"
  echo "[$env] uid=$uid → $out + .admin-token-${env}"
}

TARGET="${1:-both}"

if [[ "$TARGET" == "dev" || "$TARGET" == "both" ]]; then
  _gen dev .env.dev data/dev/gameserver.db data/dev/admin_token
fi

if [[ "$TARGET" == "prod" || "$TARGET" == "both" ]]; then
  _gen prod .env data/prod/gameserver.db data/prod/admin_token
fi
