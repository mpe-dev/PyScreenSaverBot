#!/bin/sh
# ─────────────────────────────────────────────
# PyScreenSaverBot — docker-entrypoint.sh
# Runs once at container start before the main CMD.
# ─────────────────────────────────────────────

set -e

echo "[entrypoint] Running database migrations..."
python manage.py migrate --noinput

echo "[entrypoint] Creating default admin user (if not exists)..."
python manage.py shell -c "
from django.contrib.auth.models import User
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', '', 'admin')
    print('[entrypoint] Default admin user created (admin/admin).')
else:
    print('[entrypoint] Admin user already exists, skipping.')
"

echo "[entrypoint] Starting: $*"
exec "$@"
