#!/usr/bin/env bash
# save-state.sh — Trigger an immediate state save on a running gameserver
#
# Usage:
#   ./save-state.sh                        # prod (port 8080)
#   ./save-state.sh dev                    # dev  (port 8180)
#   ./save-state.sh prod <token>           # explicit token
#   ./save-state.sh dev  <token>

set -euo pipefail

TARGET="${1:-prod}"
TOKEN="${2:-}"

case "$TARGET" in
    prod) PORT=8080; ENV_FILE=".env" ;;
    dev)  PORT=8180; ENV_FILE=".env.dev" ;;
    *)    echo "Usage: $0 [prod|dev] [token]" >&2; exit 1 ;;
esac

# Load token from localStorage hint or prompt
if [[ -z "$TOKEN" ]]; then
    echo "No token provided."
    echo "Get one from the browser console: localStorage.getItem('e3_jwt_token')"
    echo -n "Paste token: "
    read -r TOKEN
fi

URL="http://localhost:${PORT}/api/admin/save-state"
echo "Saving state on $TARGET ($URL) ..."

RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$URL" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json")

HTTP_CODE=$(echo "$RESPONSE" | tail -1)
BODY=$(echo "$RESPONSE" | head -1)

if [[ "$HTTP_CODE" == "200" ]]; then
    echo "OK: $BODY"
else
    echo "FAILED (HTTP $HTTP_CODE): $BODY" >&2
    exit 1
fi
