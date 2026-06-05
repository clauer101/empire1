#!/usr/bin/env bash
# deploy.sh — Build and redeploy Docker containers
#
# Usage:
#   ./deploy.sh              # deploy both prod and dev
#   ./deploy.sh prod         # deploy prod only
#   ./deploy.sh dev          # deploy dev only
#   ./deploy.sh prod stop    # stop prod
#   ./deploy.sh dev stop     # stop dev
#   ./deploy.sh -f prod      # force deploy prod even if battles are ongoing
#   ./deploy.sh -f           # force deploy both

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

GREEN='\033[1;32m'
YELLOW='\033[1;33m'
RED='\033[1;31m'
NC='\033[0m'

FORCE=0
ARGS=()
for arg in "$@"; do
    if [[ "$arg" == "-f" ]]; then
        FORCE=1
    else
        ARGS+=("$arg")
    fi
done
set -- "${ARGS[@]+"${ARGS[@]}"}"

save_state_before_stop() {
    local env="$1"
    local port="$2"
    local token_file=".admin-token-${env}"

    if [[ ! -f "$token_file" ]]; then
        echo -e "${RED}[WARN] No $token_file found — skipping pre-deploy state save${NC}"
        return
    fi

    # Skip if nothing is listening yet (first deploy)
    if ! curl -s --connect-timeout 1 "http://localhost:${port}/api/health" >/dev/null 2>&1; then
        echo "  No server on :${port} — skipping state save"
        return
    fi

    local token
    token=$(cat "$token_file")
    echo "  Saving state before stop ($env)..."
    local resp
    resp=$(curl -s -o /dev/null -w "%{http_code}" -X POST \
        "http://localhost:${port}/api/admin/save-state" \
        -H "Authorization: Bearer $token" \
        -H "Content-Type: application/json" 2>/dev/null || echo "000")

    if [[ "$resp" == "200" ]]; then
        echo -e "${GREEN}  State saved (HTTP 200)${NC}"
        sleep 1  # give save a moment to complete
    else
        echo -e "${RED}  State save failed (HTTP $resp) — continuing deploy${NC}"
    fi
}

build_assets() {
    echo "  Building frontend..."
    (export NVM_DIR="$HOME/.nvm" && . "$NVM_DIR/nvm.sh" && cd web && npm run build --silent)
}

# Check for ongoing battles via the admin status API.
# Prints a warning and returns 1 if battles are in progress, 0 otherwise.
check_battles() {
    local env="$1"
    local port="$2"
    local token_file=".admin-token-${env}"

    if [[ ! -f "$token_file" ]]; then
        echo -e "${YELLOW}  [WARN] No $token_file — skipping battle check${NC}"
        return 0
    fi

    if ! curl -s --connect-timeout 1 "http://localhost:${port}/api/health" >/dev/null 2>&1; then
        return 0  # server not running, nothing to check
    fi

    local token
    token=$(cat "$token_file")
    local resp
    resp=$(curl -s --connect-timeout 2 \
        "http://localhost:${port}/api/admin/status" \
        -H "Authorization: Bearer $token" 2>/dev/null || echo "{}")

    local battle_count
    battle_count=$(echo "$resp" | python3 -c \
        "import sys,json; d=json.load(sys.stdin); print(sum(1 for a in d.get('attacks',[]) if a.get('phase')=='in_battle'))" \
        2>/dev/null || echo "0")

    if [[ "$battle_count" -gt 0 ]]; then
        echo -e "${RED}  ✗ $battle_count active battle(s) on $env — deploy aborted${NC}"
        echo -e "${RED}    Use -f to force deployment${NC}"
        return 1
    fi
    return 0
}

deploy() {
    local env="$1"
    local compose_file="$2"
    local project="$3"
    local port="$4"

    echo -e "${YELLOW}========================================"
    echo " Deploy: $env"
    echo " $(date '+%Y-%m-%d %H:%M:%S')"
    echo -e "========================================${NC}"

    if [[ "$FORCE" -eq 0 ]]; then
        if ! check_battles "$env" "$port"; then
            exit 1
        fi
    else
        # Still run the check to print a warning, but don't abort
        local token_file=".admin-token-${env}"
        if [[ -f "$token_file" ]] && curl -s --connect-timeout 1 "http://localhost:${port}/api/health" >/dev/null 2>&1; then
            local token resp battle_count
            token=$(cat "$token_file")
            resp=$(curl -s --connect-timeout 2 \
                "http://localhost:${port}/api/admin/status" \
                -H "Authorization: Bearer $token" 2>/dev/null || echo "{}")
            battle_count=$(echo "$resp" | python3 -c \
                "import sys,json; d=json.load(sys.stdin); print(sum(1 for a in d.get('attacks',[]) if a.get('phase')=='in_battle'))" \
                2>/dev/null || echo "0")
            if [[ "$battle_count" -gt 0 ]]; then
                echo -e "${YELLOW}  ⚠ $battle_count active battle(s) on $env — deploying anyway (-f)${NC}"
            fi
        fi
    fi

    docker compose -p "$project" -f "$compose_file" build

    save_state_before_stop "$env" "$port"
    docker compose -p "$project" -f "$compose_file" down

    docker compose -p "$project" -f "$compose_file" up -d
    docker compose -p "$project" -f "$compose_file" ps

    echo -e "${GREEN}[OK] $env deployed${NC}"
}

TARGET="${1:-both}"
ACTION="${2:-deploy}"

stop_env() {
    local env="$1"
    local compose_file="$2"
    local project="$3"
    local port="$4"

    echo -e "${YELLOW}========================================"
    echo " Stop: $env"
    echo " $(date '+%Y-%m-%d %H:%M:%S')"
    echo -e "========================================${NC}"

    save_state_before_stop "$env" "$port"
    docker compose -p "$project" -f "$compose_file" down

    echo -e "${GREEN}[OK] $env stopped${NC}"
}

case "$TARGET" in
    prod)
        [[ "$ACTION" == "stop" ]] \
            && stop_env "prod" "docker-compose.yml" "empire1-prod" "8080" \
            || { build_assets; deploy "prod" "docker-compose.yml" "empire1-prod" "8080"; }
        ;;
    dev)
        [[ "$ACTION" == "stop" ]] \
            && stop_env "dev" "docker-compose.dev.yml" "empire1-dev" "8180" \
            || { build_assets; deploy "dev" "docker-compose.dev.yml" "empire1-dev" "8180"; }
        ;;
    both|"")
        build_assets
        deploy "prod" "docker-compose.yml" "empire1-prod" "8080"
        deploy "dev"  "docker-compose.dev.yml" "empire1-dev" "8180"
        ;;
    *)
        echo "Usage: $0 [-f] [prod|dev|both] [stop]" >&2
        exit 1
        ;;
esac
