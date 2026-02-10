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
#
# Beispiele:
#   ./restart.sh gameserver --state_file state2.yaml
#   ./restart.sh --state_file custom_state.yaml gameserver start
# ---------------------------------------------------------------
set -euo pipefail

# -- Konfiguration ------------------------------------------------
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
BASE_DIR="$(dirname "$PROJECT_DIR")"
VENV="/home/pi/e3/.venv/bin/python"
MODULE="gameserver.main"
PIDFILE="$PROJECT_DIR/.gameserver.pid"
LOG="$PROJECT_DIR/gameserver.log"

# WebServer-Konfiguration
WEB_DIR="$BASE_DIR/web"
WEB_PIDFILE="$PROJECT_DIR/.webserver.pid"
WEB_LOG="$PROJECT_DIR/webserver.log"
WEB_PORT="8000"

# Timeouts (Sekunden)
GRACEFUL_TIMEOUT=10
KILL_TIMEOUT=5

# -- Hilfsfunktionen -----------------------------------------------

find_server_pids() {
    # Findet alle PIDs, die den gameserver.main Prozess laufen haben
    pgrep -f "python.*${MODULE}" 2>/dev/null || true
}

find_webserver_pids() {
    # Findet alle PIDs für den WebServer (Python HTTP-Server)
    pgrep -f "python.*-m http.server.*$WEB_PORT" 2>/dev/null || true
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
    local state_file="${1:-state.yaml}"  # State-Datei als Parameter, default "state.yaml"
    echo "[INFO] Starte GameServer …"
    echo "       State-Datei: $state_file"
    cd "$PROJECT_DIR"

    # Starte im Hintergrund, leite Ausgabe in Log um
    # Übergebe --state_file Parameter wenn nicht die Standard-State-Datei
    if [[ "$state_file" != "state.yaml" ]]; then
        PYTHONPATH=src nohup "$VENV" -m "$MODULE" --state_file "$state_file" >> "$LOG" 2>&1 &
    else
        PYTHONPATH=src nohup "$VENV" -m "$MODULE" >> "$LOG" 2>&1 &
    fi
    local pid=$!
    echo "$pid" > "$PIDFILE"

    # Kurz warten und prüfen ob der Prozess lebt
    sleep 2
    if kill -0 "$pid" 2>/dev/null; then
        echo "[OK]   GameServer gestartet (PID: $pid)"
        echo "       Log: $LOG"
        echo "       Dashboard: http://$(hostname -I | awk '{print $1}'):9000/"
        echo "       WebSocket: ws://$(hostname -I | awk '{print $1}'):8765/"
    else
        echo "[FEHLER] GameServer konnte nicht gestartet werden." >&2
        echo "         Siehe Log: $LOG" >&2
        tail -20 "$LOG" >&2
        return 1
    fi
}

start_webserver() {
    echo "[INFO] Starte WebServer …"
    
    # Prüfe ob das Web-Verzeichnis existiert
    if [[ ! -d "$WEB_DIR" ]]; then
        echo "[FEHLER] WebServer-Verzeichnis nicht gefunden: $WEB_DIR" >&2
        return 1
    fi

    cd "$WEB_DIR"

    # Starte SimpleHTTPServer im Hintergrund
    nohup "$VENV" -m http.server $WEB_PORT >> "$WEB_LOG" 2>&1 &
    local pid=$!
    echo "$pid" > "$WEB_PIDFILE"

    # Kurz warten und prüfen ob der Prozess lebt
    sleep 2
    if kill -0 "$pid" 2>/dev/null; then
        echo "[OK]   WebServer gestartet (PID: $pid)"
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
    local state_file="${1:-state.yaml}"
    start_gameserver "$state_file"
    echo ""
    start_webserver
}

# -- Argument-Parsing ------------------------------------------------

STATE_FILE=""       # Benutzerdefinierte State-Datei (optional)
CMD="restart"       # Default command
SUBCMD=""           # Optional subcommand

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        --state_file)
            if [[ -z "${2:-}" ]]; then
                echo "[FEHLER] --state_file erfordert einen Pfad" >&2
                exit 1
            fi
            STATE_FILE="$2"
            shift 2
            ;;
        *)
            # Non-option argument
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
        start_gameserver "$STATE_FILE"
        echo ""
        start_webserver
        echo "========================================"
        echo " Fertig."
        echo "========================================"
        ;;
    gameserver)
        if [[ -n "$SUBCMD" ]]; then
            # Subcommand gegeben: gameserver stop/start
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
                    start_gameserver "$STATE_FILE"
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
            # Kein Subcommand: Neustart
            echo "========================================"
            echo " Restart GameServer"
            echo " $(date '+%Y-%m-%d %H:%M:%S')"
            echo "========================================"
            stop_gameserver
            start_gameserver "$STATE_FILE"
            echo "========================================"
            echo " Fertig."
            echo "========================================"
        fi
        ;;
    webserver)
        if [[ -n "$SUBCMD" ]]; then
            # Subcommand gegeben: webserver stop/start
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
            # Kein Subcommand: Neustart
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
        start_gameserver "$CONFIG_DIR"
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