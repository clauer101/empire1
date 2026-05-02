"""Prometheus metrics definitions for the game server."""

from prometheus_client import Gauge, Counter, Info

# Server info
server_info = Info("gameserver", "Game server version and config")

# Connections
ws_connections = Gauge("gameserver_ws_connections", "Active WebSocket connections")

# Game state
empires_total = Gauge("gameserver_empires_total", "Total number of empires (excluding AI)")
attacks_active = Gauge("gameserver_attacks_active", "Active attacks in flight")

# Game loop
tick_duration_ms = Gauge("gameserver_tick_duration_ms", "Average game loop tick duration in ms")
tick_count_total = Counter("gameserver_tick_count_total", "Total game loop ticks since start")

# Requests
http_requests_total = Counter(
    "gameserver_http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status"],
)
