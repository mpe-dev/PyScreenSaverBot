#!/bin/sh
# ─────────────────────────────────────────────
# PyScreenSaverBot — docker-entrypoint.sh
# Runs once at container start before the main CMD.
# ─────────────────────────────────────────────

set -e

echo "[entrypoint] Running database migrations..."
python manage.py migrate --noinput

echo "[entrypoint] Starting: $*"
exec "$@"
