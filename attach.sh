#!/usr/bin/env bash
# attach.sh — Follow live logs of a gameserver container
#
# Usage:
#   ./attach.sh        # prod gameserver
#   ./attach.sh prod   # prod gameserver
#   ./attach.sh dev    # dev gameserver

TARGET="${1:-prod}"

case "$TARGET" in
    prod) PROJECT="empire1-prod"; FILE="docker-compose.yml" ;;
    dev)  PROJECT="empire1-dev";  FILE="docker-compose.dev.yml" ;;
    *)    echo "Usage: $0 [prod|dev]" >&2; exit 1 ;;
esac

exec docker compose -p "$PROJECT" -f "$FILE" logs -f --tail=100 gameserver
