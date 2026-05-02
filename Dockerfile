# syntax=docker/dockerfile:1
FROM python:3.12-slim AS base

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Install Python deps first (cached layer)
COPY python_server/pyproject.toml python_server/uv.lock ./
RUN uv sync --frozen --no-dev

# Copy source
COPY python_server/src ./src
COPY python_server/config ./config
COPY web ./web

# Non-root user
RUN useradd -r -u 1001 -s /sbin/nologin appuser \
    && mkdir -p /app/data /app/logs /home/appuser/.cache/uv \
    && chown -R appuser:appuser /app /home/appuser
USER appuser

ENV PYTHONPATH=/app/src \
    PYTHONUNBUFFERED=1 \
    UV_PROJECT_ENVIRONMENT=/app/.venv

# ── gameserver stage ──────────────────────────────────────────────────────────
FROM base AS gameserver
EXPOSE 8080 8765
CMD ["/app/.venv/bin/python", "-m", "gameserver.main", "--state_file", "/app/data/state.yaml", "--db_file", "/app/data/gameserver.db"]

# ── webserver stage ───────────────────────────────────────────────────────────
FROM base AS webserver
EXPOSE 8000
CMD ["/app/.venv/bin/python", "/app/web/fastapi_server.py", "--host", "0.0.0.0", "--port", "8000"]
