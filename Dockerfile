# ─────────────────────────────────────────────
# PyScreenSaverBot — Dockerfile
# Python 3.12-slim base; single image used by
# all services (web, http_fetcher, cleanup).
# ─────────────────────────────────────────────

FROM python:3.12-slim

# Prevent .pyc files and enable unbuffered logging
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# ── System dependencies required by Pillow ────
RUN apt-get update && apt-get install -y --no-install-recommends \
    libjpeg-dev \
    libpng-dev \
    libwebp-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# ── Python dependencies ───────────────────────
# Copy requirements first so this layer is cached unless deps change
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Application source ────────────────────────
COPY . .

# ── Runtime directories ───────────────────────
# Actual data is injected via docker-compose volumes;
# these ensure the paths exist in the image as fallback.
RUN mkdir -p media/images media/previews logs data staticfiles

# ── Collect static files ──────────────────────
# SECRET_KEY placeholder only used here — real key is injected at runtime.
RUN SECRET_KEY=build-placeholder python manage.py collectstatic --noinput

EXPOSE 8000

ENTRYPOINT ["sh", "docker-entrypoint.sh"]

# Default command: run Gunicorn web server.
# Overridden by cron services in docker-compose.yml.
CMD ["gunicorn", "screensaverbot.wsgi:application", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "2", \
     "--timeout", "60", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
