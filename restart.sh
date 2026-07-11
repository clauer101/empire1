#!/usr/bin/env bash
# ---------------------------------------------------------------
# restart.sh — GameServer Lifecycle Management
#
# Usage:
#   ./restart.sh                    # restart GameServer
#   ./restart.sh restart            # restart GameServer
#   ./restart.sh stop               # stop GameServer
#   ./restart.sh start              # start GameServer
#   ./restart.sh gameserver         # GameServer restart
#   ./restart.sh gameserver stop    # GameServer stop
#   ./restart.sh gameserver start   # GameServer start
#
# Options:
#   --state_file <path>             # custom state file
#
# Examples:
#   ./restart.sh gameserver --state_file state2.yaml
#   ./restart.sh --state_file custom_state.yaml gameserver start
# ---------------------------------------------------------------
set -euo pipefail

# -- Configuration ------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHON_SERVER_DIR="$SCRIPT_DIR/python_server"
VENV="$SCRIPT_DIR/.venv/bin/python"
MODULE="gameserver.main"
PIDFILE="$PYTHON_SERVER_DIR/.gameserver.pid"
LOG="$PYTHON_SERVER_DIR/gameserver.log"

# Timeouts (seconds)
GRACEFUL_TIMEOUT=10

# -- Colors --------------------------------------------------------
RED='\033[1;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# -- Helper functions -----------------------------------------------

find_server_pids() {
    pgrep -f "python.*${MODULE}" 2>/dev/null || true
}

stop_gameserver() {
    local pids
    pids=$(find_server_pids)

    if [[ -z "$pids" ]]; then
        echo "[INFO] No running GameServer found."
        return 0
    fi

    echo "[INFO] GameServer running (PIDs: $pids) — sending SIGTERM …"
    kill -TERM $pids 2>/dev/null || true

    local waited=0
    while [[ $waited -lt $GRACEFUL_TIMEOUT ]]; do
        sleep 1
        waited=$((waited + 1))
        pids=$(find_server_pids)
        if [[ -z "$pids" ]]; then
            echo "[OK]   GameServer stopped cleanly after ${waited}s."
            return 0
        fi
        echo "[WAIT] Waiting for shutdown … (${waited}/${GRACEFUL_TIMEOUT}s)"
    done

    pids=$(find_server_pids)
    if [[ -n "$pids" ]]; then
        echo "[WARN] Graceful shutdown failed — sending SIGKILL …"
        kill -KILL $pids 2>/dev/null || true
        sleep 1
        pids=$(find_server_pids)
        if [[ -n "$pids" ]]; then
            echo "[ERROR] Could not stop GameServer (PIDs: $pids)" >&2
            return 1
        fi
        echo "[OK]   GameServer stopped via SIGKILL."
    fi
}

start_gameserver() {
    local state_file="${1:-python_server/state.yaml}"
    if [[ "$state_file" != /* ]]; then
        state_file="$SCRIPT_DIR/$state_file"
    fi

    local existing_pids
    existing_pids=$(find_server_pids)
    if [[ -n "$existing_pids" ]]; then
        echo "[INFO] Running GameServer found (PIDs: $existing_pids) — stopping first …"
        stop_gameserver
    fi

    echo "[INFO] Starting GameServer …"
    echo "       State file: $state_file"
    cd "$PYTHON_SERVER_DIR"

    # Load .env from repo root if present
    local env_file="$SCRIPT_DIR/.env"
    if [[ -f "$env_file" ]]; then
        set -a
        # shellcheck source=/dev/null
        source "$env_file"
        set +a
        echo "       Env: $env_file loaded"
    fi

    PYTHONPATH=src nohup "$VENV" -m "$MODULE" --state_file "$state_file" >> "$LOG" 2>&1 &
    local pid=$!
    echo "$pid" > "$PIDFILE"

    sleep 2
    if kill -0 "$pid" 2>/dev/null; then
        echo "[OK]   GameServer started (PID: $pid)"
        echo "       Log: $LOG"
        echo "       URL: https://relicsnrockets.io/"
        echo "       DevTools: https://relicsnrockets.io/tools/"
    else
        echo -e "${RED}╔══════════════════════════════════════════╗${NC}" >&2
        echo -e "${RED}║  ERROR: GameServer failed to start       ║${NC}" >&2
        echo -e "${RED}╚══════════════════════════════════════════╝${NC}" >&2
        echo -e "${YELLOW}Log: $LOG${NC}" >&2
        echo -e "${YELLOW}── Last lines ─────────────────────────────${NC}" >&2
        tail -20 "$LOG" >&2
        echo -e "${YELLOW}───────────────────────────────────────────${NC}" >&2
        return 1
    fi
}

# -- Argument parsing ------------------------------------------------

STATE_FILE=""
CMD="restart"
SUBCMD=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --state_file)
            if [[ -z "${2:-}" ]]; then
                echo "[ERROR] --state_file requires a path" >&2
                exit 1
            fi
            STATE_FILE="$2"
            shift 2
            ;;
        *)
            if [[ -z "$CMD" ]] || [[ "$CMD" == "restart" ]]; then
                CMD="$1"
            elif [[ -z "$SUBCMD" ]]; then
                SUBCMD="$1"
            fi
            shift
            ;;
    esac
done

# -- Main --------------------------------------------------

case "$CMD" in
    stop)
        echo "========================================"
        echo " Stop GameServer"
        echo " $(date '+%Y-%m-%d %H:%M:%S')"
        echo "========================================"
        stop_gameserver
        echo "========================================"
        echo " Done."
        echo "========================================"
        ;;
    start)
        echo "========================================"
        echo " Start GameServer"
        echo " $(date '+%Y-%m-%d %H:%M:%S')"
        echo "========================================"
        start_gameserver "${STATE_FILE:-python_server/state.yaml}"
        echo "========================================"
        echo " Done."
        echo "========================================"
        ;;
    gameserver)
        if [[ -n "$SUBCMD" ]]; then
            case "$SUBCMD" in
                stop)
                    echo "========================================"
                    echo " Stop GameServer"
                    echo " $(date '+%Y-%m-%d %H:%M:%S')"
                    echo "========================================"
                    stop_gameserver
                    echo "========================================"
                    echo " Done."
                    echo "========================================"
                    ;;
                start)
                    echo "========================================"
                    echo " Start GameServer"
                    echo " $(date '+%Y-%m-%d %H:%M:%S')"
                    echo "========================================"
                    start_gameserver "${STATE_FILE:-python_server/state.yaml}"
                    echo "========================================"
                    echo " Done."
                    echo "========================================"
                    ;;
                *)
                    echo "[ERROR] Unknown subcommand: $SUBCMD" >&2
                    echo "Valid: stop, start" >&2
                    exit 1
                    ;;
            esac
        else
            echo "========================================"
            echo " Restart GameServer"
            echo " $(date '+%Y-%m-%d %H:%M:%S')"
            echo "========================================"
            stop_gameserver
            start_gameserver "${STATE_FILE:-python_server/state.yaml}"
            echo "========================================"
            echo " Done."
            echo "========================================"
        fi
        ;;
    restart|"")
        echo "========================================"
        echo " Restart GameServer"
        echo " $(date '+%Y-%m-%d %H:%M:%S')"
        echo "========================================"
        stop_gameserver
        start_gameserver "${STATE_FILE:-python_server/state.yaml}"
        echo "========================================"
        echo " Done."
        echo "========================================"
        ;;
    *)
        echo "[ERROR] Unknown command: $CMD" >&2
        echo "" >&2
        echo "Usage:" >&2
        echo "  ./restart.sh                    # restart GameServer" >&2
        echo "  ./restart.sh restart            # restart GameServer" >&2
        echo "  ./restart.sh stop               # stop GameServer" >&2
        echo "  ./restart.sh start              # start GameServer" >&2
        echo "  ./restart.sh gameserver         # GameServer restart" >&2
        echo "  ./restart.sh gameserver stop    # GameServer stop" >&2
        echo "  ./restart.sh gameserver start   # GameServer start" >&2
        exit 1
        ;;
esac
