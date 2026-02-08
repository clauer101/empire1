#!/usr/bin/env bash
# ---------------------------------------------------------------
# restart.sh — GameServer Lifecycle Management
#
# Nutzung:
#   ./restart.sh           # Neustart (stop + start)
#   ./restart.sh restart   # Neustart (stop + start)
#   ./restart.sh stop      # Nur stoppen
#   ./restart.sh start     # Nur starten
#   ./restart.sh --kill    # Sofort beenden (SIGKILL) falls nötig
# ---------------------------------------------------------------
set -euo pipefail

# -- Konfiguration ------------------------------------------------
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV="/home/pi/e3/.venv/bin/python"
MODULE="gameserver.main"
PIDFILE="$PROJECT_DIR/.gameserver.pid"
LOG="$PROJECT_DIR/gameserver.log"

# Timeouts (Sekunden)
GRACEFUL_TIMEOUT=10
KILL_TIMEOUT=5

# -- Hilfsfunktionen -----------------------------------------------

find_server_pids() {
    # Findet alle PIDs, die den gameserver.main Prozess laufen haben
    pgrep -f "python.*${MODULE}" 2>/dev/null || true
}

stop_server() {
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

start_server() {
    echo "[INFO] Starte GameServer …"
    cd "$PROJECT_DIR"

    # Starte im Hintergrund, leite Ausgabe in Log um
    PYTHONPATH=src nohup "$VENV" -m "$MODULE" >> "$LOG" 2>&1 &
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

# -- Hauptprogramm --------------------------------------------------

CMD="${1:-restart}"  # Default: restart

case "$CMD" in
    stop)
        echo "========================================"
        echo " GameServer Stop"
        echo " $(date '+%Y-%m-%d %H:%M:%S')"
        echo "========================================"
        stop_server
        echo "========================================"
        echo " Fertig."
        echo "========================================"
        ;;
    start)
        echo "========================================"
        echo " GameServer Start"
        echo " $(date '+%Y-%m-%d %H:%M:%S')"
        echo "========================================"
        start_server
        echo "========================================"
        echo " Fertig."
        echo "========================================"
        ;;
    restart|"")
        echo "========================================"
        echo " GameServer Restart"
        echo " $(date '+%Y-%m-%d %H:%M:%S')"
        echo "========================================"
        stop_server
        start_server
        echo "========================================"
        echo " Fertig."
        echo "========================================"
        ;;
    *)
        echo "[FEHLER] Unbekannter Befehl: $CMD" >&2
        echo "" >&2
        echo "Nutzung:" >&2
        echo "  ./restart.sh           # Neustart (stop + start)" >&2
        echo "  ./restart.sh restart   # Neustart (stop + start)" >&2
        echo "  ./restart.sh stop      # Nur stoppen" >&2
        echo "  ./restart.sh start     # Nur starten" >&2
        exit 1
        ;;
esac