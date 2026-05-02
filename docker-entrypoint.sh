#!/bin/sh
# Run Alembic migrations then start the gameserver
set -e

DB_FILE="${1:-/app/data/gameserver.db}"
STATE_FILE="${2:-/app/data/state.yaml}"

echo "Running database migrations on $DB_FILE ..."
DB_FILE="$DB_FILE" /app/.venv/bin/alembic -c /app/alembic.ini upgrade head

echo "Starting gameserver ..."
exec /app/.venv/bin/python -m gameserver.main \
    --state_file "$STATE_FILE" \
    --db_file "$DB_FILE"
