#!/usr/bin/env bash
# ---------------------------------------------------------------
# restart.sh — GameServer & WebServer Lifecycle Management
#
# Nutzung:
#   ./restart.sh                    # Neustart beider Server
#   ./restart.sh restart            # Neustart beider Server
#   ./restart.sh stop               # Stop beider Server
#   ./restart.sh start              # Start beider Server
#   ./restart.sh gameserver         # GameServer restart
#   ./restart.sh gameserver stop    # GameServer stop
#   ./restart.sh gameserver start   # GameServer start
#   ./restart.sh webserver          # WebServer restart
#   ./restart.sh webserver stop     # WebServer stop
#   ./restart.sh webserver start    # WebServer start
#
# Optionen:
#   --state_file <path>             # Benutzerdefinierte State-Datei
#   --enable-cache                  # Browser-Cache aktivieren (Standard: No-Cache)
#
# Beispiele:
#   ./restart.sh gameserver --state_file state2.yaml
#   ./restart.sh --state_file custom_state.yaml gameserver start
#   ./restart.sh webserver --enable-cache
# ---------------------------------------------------------------
set -euo pipefail

# -- Konfiguration ------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHON_SERVER_DIR="$SCRIPT_DIR/python_server"
VENV="$SCRIPT_DIR/.venv/bin/python"
MODULE="gameserver.main"
PIDFILE="$PYTHON_SERVER_DIR/.gameserver.pid"
LOG="$PYTHON_SERVER_DIR/gameserver.log"

# WebServer-Konfiguration
WEB_DIR="$SCRIPT_DIR/web"
WEB_PIDFILE="$PYTHON_SERVER_DIR/.webserver.pid"
WEB_LOG="$PYTHON_SERVER_DIR/webserver.log"
WEB_PORT="8000"

# Timeouts (Sekunden)
GRACEFUL_TIMEOUT=10
KILL_TIMEOUT=5

# -- Farben --------------------------------------------------------
RED='\033[1;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# -- Hilfsfunktionen -----------------------------------------------

find_server_pids() {
    # Findet alle PIDs, die den gameserver.main Prozess laufen haben
    pgrep -f "python.*${MODULE}" 2>/dev/null || true
}

find_webserver_pids() {
    # Findet alle PIDs für den WebServer (FastAPI/Uvicorn)
    pgrep -f "uvicorn.*fastapi_server" 2>/dev/null || pgrep -f "python.*fastapi_server.py" 2>/dev/null || true
}

stop_gameserver() {
    local pids
    pids=$(find_server_pids)

    if [[ -z "$pids" ]]; then
        echo "[INFO] Kein laufender GameServer gefunden."
        return 0
    fi

    echo "[INFO] GameServer läuft (PIDs: $pids) — sende SIGTERM …"
    kill -TERM $pids 2>/dev/null || true

    # Warte auf graceful shutdown
    local waited=0
    while [[ $waited -lt $GRACEFUL_TIMEOUT ]]; do
        sleep 1
        waited=$((waited + 1))
        pids=$(find_server_pids)
        if [[ -z "$pids" ]]; then
            echo "[OK]   GameServer nach ${waited}s sauber beendet."
            return 0
        fi
        echo "[WAIT] Warte auf Shutdown … (${waited}/${GRACEFUL_TIMEOUT}s)"
    done

    # Graceful hat nicht geklappt → SIGKILL
    pids=$(find_server_pids)
    if [[ -n "$pids" ]]; then
        echo "[WARN] Graceful Shutdown fehlgeschlagen — sende SIGKILL …"
        kill -KILL $pids 2>/dev/null || true
        sleep 1
        pids=$(find_server_pids)
        if [[ -n "$pids" ]]; then
            echo "[FEHLER] Konnte GameServer nicht beenden (PIDs: $pids)" >&2
            return 1
        fi
        echo "[OK]   GameServer per SIGKILL beendet."
    fi
}

stop_webserver() {
    local pids
    pids=$(find_webserver_pids)

    if [[ -z "$pids" ]]; then
        echo "[INFO] Kein laufender WebServer gefunden."
        return 0
    fi

    echo "[INFO] WebServer läuft (PIDs: $pids) — sende SIGTERM …"
    kill -TERM $pids 2>/dev/null || true

    # Warte auf graceful shutdown
    local waited=0
    while [[ $waited -lt $GRACEFUL_TIMEOUT ]]; do
        sleep 1
        waited=$((waited + 1))
        pids=$(find_webserver_pids)
        if [[ -z "$pids" ]]; then
            echo "[OK]   WebServer nach ${waited}s sauber beendet."
            return 0
        fi
        echo "[WAIT] Warte auf Shutdown … (${waited}/${GRACEFUL_TIMEOUT}s)"
    done

    # Graceful hat nicht geklappt → SIGKILL
    pids=$(find_webserver_pids)
    if [[ -n "$pids" ]]; then
        echo "[WARN] Graceful Shutdown fehlgeschlagen — sende SIGKILL …"
        kill -KILL $pids 2>/dev/null || true
        sleep 1
        pids=$(find_webserver_pids)
        if [[ -n "$pids" ]]; then
            echo "[FEHLER] Konnte WebServer nicht beenden (PIDs: $pids)" >&2
            return 1
        fi
        echo "[OK]   WebServer per SIGKILL beendet."
    fi
}

stop_server() {
    stop_gameserver
    stop_webserver
}

start_gameserver() {
    local state_file="${1:-python_server/state.yaml}"
    # Resolve to absolute path before cd-ing into a subdirectory
    if [[ "$state_file" != /* ]]; then
        state_file="$SCRIPT_DIR/$state_file"
    fi

    # Stop any already-running instance to avoid "Address already in use"
    local existing_pids
    existing_pids=$(find_server_pids)
    if [[ -n "$existing_pids" ]]; then
        echo "[INFO] Laufender GameServer gefunden (PIDs: $existing_pids) — stoppe zuerst …"
        stop_gameserver
    fi

    echo "[INFO] Starte GameServer …"
    echo "       State-Datei: $state_file"
    cd "$PYTHON_SERVER_DIR"

    # Starte im Hintergrund, leite Ausgabe in Log um
    PYTHONPATH=src nohup "$VENV" -m "$MODULE" --state_file "$state_file" >> "$LOG" 2>&1 &
    local pid=$!
    echo "$pid" > "$PIDFILE"

    # Kurz warten und prüfen ob der Prozess lebt
    sleep 2
    if kill -0 "$pid" 2>/dev/null; then
        echo "[OK]   GameServer gestartet (PID: $pid)"
        echo "       Log: $LOG"
        echo "       DevTools: http://$(hostname -I | awk '{print $1}'):${WEB_PORT}/tools"
        echo "       WebSocket: ws://$(hostname -I | awk '{print $1}'):8765/"
    else
        echo -e "${RED}╔══════════════════════════════════════════╗${NC}" >&2
        echo -e "${RED}║  FEHLER: GameServer konnte nicht starten ║${NC}" >&2
        echo -e "${RED}╚══════════════════════════════════════════╝${NC}" >&2
        echo -e "${YELLOW}Log: $LOG${NC}" >&2
        echo -e "${YELLOW}── Letzte Zeilen ──────────────────────────${NC}" >&2
        tail -20 "$LOG" >&2
        echo -e "${YELLOW}───────────────────────────────────────────${NC}" >&2
        return 1
    fi
}

start_webserver() {
    echo "[INFO] Starte WebServer (FastAPI + Uvicorn) …"

    if [[ ! -d "$WEB_DIR" ]]; then
        echo "[FEHLER] WebServer-Verzeichnis nicht gefunden: $WEB_DIR" >&2
        return 1
    fi

    if [[ ! -f "$WEB_DIR/fastapi_server.py" ]]; then
        echo "[FEHLER] fastapi_server.py nicht gefunden: $WEB_DIR/fastapi_server.py" >&2
        return 1
    fi

    cd "$WEB_DIR"

    local cache_flag=""
    if [[ "$ENABLE_CACHE" == false ]]; then
        cache_flag="--no-cache"
    fi
    nohup "$VENV" "$WEB_DIR/fastapi_server.py" --port $WEB_PORT $cache_flag >> "$WEB_LOG" 2>&1 &
    local pid=$!
    echo "$pid" > "$WEB_PIDFILE"

    sleep 3
    if kill -0 "$pid" 2>/dev/null; then
        echo "[OK]   WebServer gestartet (PID: $pid)"
        if [[ "$ENABLE_CACHE" == true ]]; then
            echo "       Mode: FastAPI (Production, Cache aktiv)"
        else
            echo "       Mode: FastAPI (Development, No-Cache)"
        fi
        echo "       Log: $WEB_LOG"
        echo "       URL: http://$(hostname -I | awk '{print $1}'):${WEB_PORT}/"
    else
        echo "[FEHLER] WebServer konnte nicht gestartet werden." >&2
        echo "         Siehe Log: $WEB_LOG" >&2
        tail -20 "$WEB_LOG" >&2
        return 1
    fi
}

start_server() {
    local state_file="${1:-python_server/state.yaml}"
    start_gameserver "$state_file"
    echo ""
    start_webserver
}

# -- Argument-Parsing ------------------------------------------------

STATE_FILE=""
ENABLE_CACHE=true
CMD="restart"
SUBCMD=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --enable-cache)
            ENABLE_CACHE=true
            shift
            ;;
        --state_file)
            if [[ -z "${2:-}" ]]; then
                echo "[FEHLER] --state_file erfordert einen Pfad" >&2
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

# -- Hauptprogramm --------------------------------------------------

case "$CMD" in
    stop)
        echo "========================================"
        echo " Stop GameServer & WebServer"
        echo " $(date '+%Y-%m-%d %H:%M:%S')"
        echo "========================================"
        stop_gameserver
        echo ""
        stop_webserver
        echo "========================================"
        echo " Fertig."
        echo "========================================"
        ;;
    start)
        echo "========================================"
        echo " Start GameServer & WebServer"
        echo " $(date '+%Y-%m-%d %H:%M:%S')"
        echo "========================================"
        start_gameserver "${STATE_FILE:-python_server/state.yaml}"
        echo ""
        start_webserver
        echo "========================================"
        echo " Fertig."
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
                    echo " Fertig."
                    echo "========================================"
                    ;;
                start)
                    echo "========================================"
                    echo " Start GameServer"
                    echo " $(date '+%Y-%m-%d %H:%M:%S')"
                    echo "========================================"
                    start_gameserver "${STATE_FILE:-python_server/state.yaml}"
                    echo "========================================"
                    echo " Fertig."
                    echo "========================================"
                    ;;
                *)
                    echo "[FEHLER] Unbekannter Subcommand: $SUBCMD" >&2
                    echo "Gültig: stop, start" >&2
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
            echo " Fertig."
            echo "========================================"
        fi
        ;;
    webserver)
        if [[ -n "$SUBCMD" ]]; then
            case "$SUBCMD" in
                stop)
                    echo "========================================"
                    echo " Stop WebServer"
                    echo " $(date '+%Y-%m-%d %H:%M:%S')"
                    echo "========================================"
                    stop_webserver
                    echo "========================================"
                    echo " Fertig."
                    echo "========================================"
                    ;;
                start)
                    echo "========================================"
                    echo " Start WebServer"
                    echo " $(date '+%Y-%m-%d %H:%M:%S')"
                    echo "========================================"
                    start_webserver
                    echo "========================================"
                    echo " Fertig."
                    echo "========================================"
                    ;;
                *)
                    echo "[FEHLER] Unbekannter Subcommand: $SUBCMD" >&2
                    echo "Gültig: stop, start" >&2
                    exit 1
                    ;;
            esac
        else
            echo "========================================"
            echo " Restart WebServer"
            echo " $(date '+%Y-%m-%d %H:%M:%S')"
            echo "========================================"
            stop_webserver
            start_webserver
            echo "========================================"
            echo " Fertig."
            echo "========================================"
        fi
        ;;
    restart|"")
        echo "========================================"
        echo " Restart GameServer & WebServer"
        echo " $(date '+%Y-%m-%d %H:%M:%S')"
        echo "========================================"
        stop_gameserver
        echo ""
        stop_webserver
        echo ""
        start_gameserver "${STATE_FILE:-python_server/state.yaml}"
        echo ""
        start_webserver
        echo "========================================"
        echo " Fertig."
        echo "========================================"
        ;;
    *)
        echo "[FEHLER] Unbekannter Befehl: $CMD" >&2
        echo "" >&2
        echo "Nutzung:" >&2
        echo "  ./restart.sh                    # Neustart beider Server" >&2
        echo "  ./restart.sh restart            # Neustart beider Server" >&2
        echo "  ./restart.sh stop               # Stop beider Server" >&2
        echo "  ./restart.sh start              # Start beider Server" >&2
        echo "  ./restart.sh gameserver         # GameServer restart" >&2
        echo "  ./restart.sh gameserver stop    # GameServer stop" >&2
        echo "  ./restart.sh gameserver start   # GameServer start" >&2
        echo "  ./restart.sh webserver          # WebServer restart" >&2
        echo "  ./restart.sh webserver stop     # WebServer stop" >&2
        echo "  ./restart.sh webserver start    # WebServer start" >&2
        exit 1
        ;;
esac
