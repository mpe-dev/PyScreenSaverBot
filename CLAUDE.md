# PyScreenSaverBot — CLAUDE.md

## Project Purpose

A self-hosted screensaver system built as a **Django web application**: ingests images from configurable sources (Telegram bot, HTTP URL fetcher, and future sources), stores them locally, generates previews, and displays a fullscreen browser slideshow. All ingestion sources and screensaver behaviour are configured via the Django Admin UI. Designed for low-resource, long-term unattended operation on a NAS, mini PC, or small server.

---

## Architecture

| Component | Responsibility |
|---|---|
| **`ingestion_app`** | Pluggable ingestion layer: all image sources (Telegram, HTTP fetcher, future), shared save/preview pipeline, webhook view, management commands |
| **`screensaver_app`** | Slideshow Django template, `/api/previews` endpoint, `ScreensaverConfig`, `CleanupConfig`, cleanup management command |
| **Django Admin** | UI to configure all ingestion sources, screensaver settings, and cleanup thresholds |
| **Django Template (frontend)** | Single-page template + vanilla JS; collage mode → slideshow mode; no heavy framework |

---

## Django Project Structure

```
PyScreenSaverBot/
├── manage.py
├── requirements.txt
├── .flake8
├── screensaverbot/                    # Django project package
│   ├── settings.py
│   ├── urls.py                        # Root URL conf
│   ├── asgi.py
│   └── wsgi.py
│
├── ingestion_app/                     # Django app: all image ingestion sources
│   ├── admin.py                       # TelegramSourceConfig, HttpFetcherSourceConfig admin
│   ├── apps.py
│   ├── models.py                      # TelegramSourceConfig, HttpFetcherSourceConfig
│   ├── urls.py                        # POST /telegram/webhook
│   ├── views.py                       # Telegram webhook view
│   ├── services/
│   │   ├── __init__.py
│   │   ├── pipeline.py                # Shared: save_image(), generate_preview()
│   │   ├── telegram.py                # Telegram-specific: download image from API
│   │   └── http_fetcher.py            # HTTP source: fetch image from URL
│   └── management/
│       └── commands/
│           └── run_http_fetcher.py    # Polls all enabled HTTP sources on schedule
│
├── screensaver_app/                   # Django app: slideshow UI + API + cleanup
│   ├── admin.py                       # ScreensaverConfig, CleanupConfig admin
│   ├── apps.py
│   ├── models.py                      # ScreensaverConfig, CleanupConfig singletons
│   ├── urls.py                        # GET / and GET /api/previews
│   ├── views.py
│   ├── services.py                    # run_cleanup()
│   ├── templates/
│   │   └── screensaver_app/
│   │       └── index.html             # Slideshow HTML page (served at /)
│   └── management/
│       └── commands/
│           └── run_cleanup.py
│
├── media/
│   ├── images/                        # Full-resolution images (all sources)
│   └── previews/                      # Resized preview images
└── logs/
    └── app.log
```

---

## Ingestion Architecture

All image sources feed into the **same shared pipeline** in `ingestion_app/services/pipeline.py`.
Each source is responsible only for producing `bytes`; the pipeline handles saving and preview generation.

```
[Telegram webhook]  ──┐
                      ├──► pipeline.save_image(data: bytes) → Path
[HTTP Fetcher]  ──────┤         └──► pipeline.generate_preview(source: Path) → Path
                      │
[Future source] ──────┘
```

Adding a new source means:
1. Create a new model in `ingestion_app/models.py`
2. Register it in `ingestion_app/admin.py`
3. Add a fetcher service in `ingestion_app/services/`
4. Add a management command or webhook view — call `pipeline.save_image()` + `pipeline.generate_preview()`

---

## Django Apps

### `ingestion_app`

#### Shared Pipeline (`services/pipeline.py`)
- `save_image(data: bytes) -> Path` — writes image to `media/images/` using timestamp filename; logs save
- `generate_preview(source: Path) -> Path` — Pillow resize (max width ~400px), writes to `media/previews/`; skips if preview already exists; logs generation

---

#### Source 1: Telegram Bot

**Model: `TelegramSourceConfig`** — singleton (one record enforced); fields:

| Field | Type | Description |
|---|---|---|
| `bot_token` | `str` | Telegram Bot API token |
| `chat_id` | `str` | Allowed channel/chat ID |
| `webhook_url` | `str` | Public HTTPS URL for webhook registration |
| `enabled` | `bool` | Enable/disable without deleting config |

**View** (`views.py`):
- `POST /telegram/webhook` — receives Telegram update JSON
- Validates `chat_id` against `TelegramSourceConfig`
- Extracts highest-resolution photo
- Delegates to `services/telegram.py` → `pipeline.save_image()` + `pipeline.generate_preview()`

**Service** (`services/telegram.py`):
- `download_image(file_id: str, bot_token: str) -> bytes` — calls Telegram `getFile` + download URL

---

#### Source 2: HTTP Image Fetcher

**Model: `HttpFetcherSourceConfig`** — multiple records allowed (one per source URL); fields:

| Field | Type | Description |
|---|---|---|
| `name` | `str` | Friendly label (e.g. "Daily Landscape Cam") |
| `url` | `str` | Direct image URL (must respond with image bytes) |
| `fetch_interval` | `str` | Choices: `hourly`, `daily`, `weekly`, `monthly` |
| `enabled` | `bool` | Enable/disable per source |
| `last_fetched_at` | `datetime \| None` | Timestamp of last successful fetch (null = never run) |

**Service** (`services/http_fetcher.py`):
- `fetch_image(url: str) -> bytes` — HTTP GET with timeout; validates `Content-Type` is an image; raises on failure
- `is_due(source: HttpFetcherSourceConfig) -> bool` — compares `last_fetched_at` + interval against `now()`

**Management command** (`run_http_fetcher.py`):
```
python manage.py run_http_fetcher
```
- Loads all `HttpFetcherSourceConfig` where `enabled=True`
- For each: calls `is_due()` → if yes: `fetch_image()` → `pipeline.save_image()` → `pipeline.generate_preview()` → updates `last_fetched_at`
- Logs each fetch attempt (success or failure)
- Designed to be run frequently (e.g. every hour via cron); interval logic is internal

Cron schedule (run hourly, let interval logic decide which sources are due):
```cron
0 * * * * /path/to/.venv/bin/python /path/to/manage.py run_http_fetcher
```

**Interval → seconds mapping** (internal to `services/http_fetcher.py`):

| Choice | Seconds |
|---|---|
| `hourly` | 3 600 |
| `daily` | 86 400 |
| `weekly` | 604 800 |
| `monthly` | 2 592 000 |

---

### `screensaver_app`

#### Models
- **`ScreensaverConfig`** — singleton; fields:
  - `grid_fetch_interval_seconds: int` (default: 60)
  - `slideshow_interval_seconds: int` (default: 5)
  - `transition: str` (choices: burn, fade, slide, zoom; default: burn)
  - `transition_mode: str` (choices: fixed, random; default: random)
- **`CleanupConfig`** — singleton; fields:
  - `max_folder_size_mb: int` (default: 500)
  - `cleanup_interval_seconds: int` (default: 3600)

#### Views
- `GET /` — renders `screensaver_app/index.html`; injects `ScreensaverConfig` values into template context
- `GET /api/previews` — returns JSON list of all preview files

#### Cleanup (`services.py` + management command)
```
python manage.py run_cleanup
```
- Reads `CleanupConfig` from DB
- Calculates total size of `media/images/`
- If exceeded: sort files by filename (oldest first) → delete until under limit
- Also deletes matching preview from `media/previews/`
- Logs every deletion

```cron
0 * * * * /path/to/.venv/bin/python /path/to/manage.py run_cleanup
```

---

## Django Admin

All runtime configuration is managed exclusively through Django Admin.

| Admin Section | Model | Type | Key Fields |
|---|---|---|---|
| **Telegram Source** | `TelegramSourceConfig` | Singleton | bot_token, chat_id, webhook_url, enabled |
| **HTTP Fetcher Sources** | `HttpFetcherSourceConfig` | Multi-record | name, url, fetch_interval, enabled, last_fetched_at (read-only) |
| **Screensaver** | `ScreensaverConfig` | Singleton | transition, transition_mode, intervals |
| **Cleanup** | `CleanupConfig` | Singleton | max_folder_size_mb, cleanup_interval_seconds |

`last_fetched_at` is displayed as read-only in the HTTP Fetcher admin — updated only by the management command.

---

## URL Structure

| Method | Path | Handler | Description |
|---|---|---|---|
| `GET` | `/` | `screensaver_app.views` | Slideshow HTML page |
| `POST` | `/telegram/webhook` | `ingestion_app.views` | Telegram webhook receiver |
| `GET` | `/api/previews` | `screensaver_app.views` | Preview list JSON |
| `GET` | `/media/images/<filename>` | Django `MEDIA_ROOT` | Full-resolution image |
| `GET` | `/media/previews/<filename>` | Django `MEDIA_ROOT` | Preview image |
| `GET` | `/admin/` | Django Admin | All configuration UI |

`/api/previews` response shape:
```json
[
  { "filename": "20260220_134512_003721.jpg", "preview_url": "/media/previews/20260220_134512_003721.jpg" }
]
```

---

## File Naming

Timestamp-based filenames — applied uniformly regardless of ingestion source:

Format: `YYYYMMDD_HHMMSS_ffffff.jpg`
Example: `20260220_134512_003721.jpg`

- `YYYYMMDD` — date (UTC)
- `HHMMSS` — time 24h (UTC)
- `ffffff` — microseconds (uniqueness for rapid bursts)

Generated with: `datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")`

Benefits:
- Source-agnostic — same naming for Telegram, HTTP fetcher, and future sources
- Guaranteed unique — no collision even under concurrent receives
- Natural chronological sort by filename — no `getmtime` needed
- No startup scan required
- Human-readable — encodes exactly when the image arrived

---

## Frontend Behavior

Served as a Django template at `GET /`. Vanilla JS, no frontend framework.

- **Phase 1 – Collage mode:** fetch `/api/previews` → render preview grid (async, low memory)
- **Phase 2 – Slideshow mode:** iterate full-resolution images → apply transition → loop continuously
- JS reads screensaver settings injected into the template via Django context (intervals, transition)
- Runs fullscreen in browser; display device simply opens the hosted URL

### Transition Effects

`burn` (default), `fade`, `slide`, `zoom`, `random` — configured in `ScreensaverConfig` via Django Admin.

---

## Django Settings Highlights

```python
# screensaverbot/settings.py

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "whitenoise.runserver_nostatic",  # serves static files in dev via WhiteNoise
    "ingestion_app",
    "screensaver_app",
]

MIDDLEWARE = [
    # WhiteNoise must be second, immediately after SecurityMiddleware
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    ...
]

STATIC_ROOT = BASE_DIR / "staticfiles"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "data" / "db.sqlite3",   # matches Docker volume mount
    }
}

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "file": {
            "class": "logging.FileHandler",
            "filename": BASE_DIR / "logs" / "app.log",
        },
    },
    "root": {
        "handlers": ["file"],
        "level": "INFO",
    },
}
```

Secrets (`SECRET_KEY`, `bot_token`) must be provided via environment variables — never hardcoded.

---

## Key Implementation Details

- **Shared pipeline:** `ingestion_app/services/pipeline.py` is the single entry point for all sources — no source writes files directly.
- **Preview generation:** Pillow, max width ~400px; skipped if preview already exists on disk.
- **Singleton models:** `TelegramSourceConfig`, `ScreensaverConfig`, `CleanupConfig` enforce single-row via overridden `save()` (clears existing rows) and blocked `delete()`.
- **HTTP fetcher interval logic:** `is_due()` checks `last_fetched_at`; management command runs on cron — no persistent scheduler process needed.
- **Logging:** Django `LOGGING` config; file-based; used across webhook view, HTTP fetcher command, pipeline, and cleanup command.
- **No in-memory image storage** — optimized for low CPU/RAM.
- **Media files in dev:** served via `django.views.static.serve` when `DEBUG=True`; use NGINX in production.

---

## Deployment

### Docker (recommended)

The project ships with a ready-to-run Docker setup. All services share the same image.

**Files:**

| File | Purpose |
|---|---|
| `Dockerfile` | Builds the single shared image (Python 3.12-slim + Pillow deps + Gunicorn) |
| `docker-entrypoint.sh` | Runs `migrate` on startup, then hands off to the service command |
| `docker-compose.yml` | Orchestrates `web`, `http_fetcher`, and `cleanup` services |
| `.dockerignore` | Excludes `.venv`, `media/`, `data/`, `logs/`, `.env` from build context |
| `.env.example` | Template for required environment variables — copy to `.env` |
| `requirements.txt` | Pinned Python dependencies |

**Quick start:**
```bash
cp .env.example .env          # fill in SECRET_KEY and ALLOWED_HOSTS
docker compose up -d          # build image and start all three services
docker compose logs -f        # follow combined logs
```

**Services started by `docker compose up`:**

| Service | Role | Restart |
|---|---|---|
| `web` | Django + Gunicorn on port 8000 | always |
| `http_fetcher` | Runs `run_http_fetcher` every hour | always |
| `cleanup` | Runs `run_cleanup` every hour | always |

**Persistent volumes (bind-mounted to host):**

| Host path | Container path | Contents |
|---|---|---|
| `./data/` | `/app/data/` | SQLite database (`db.sqlite3`) |
| `./media/` | `/app/media/` | Full-res images + previews |
| `./logs/` | `/app/logs/` | `app.log` |

> `settings.py` must set `DATABASES['default']['NAME'] = BASE_DIR / "data" / "db.sqlite3"`

**Host port** is controlled by `HOST_PORT` in `.env` (default: `8000`).

**Static files** are served by WhiteNoise (no NGINX required for basic use).
For production with NGINX, add an `nginx` service to `docker-compose.yml` and proxy to `web:8000`.

**HTTPS** is required for Telegram webhook registration — use NGINX + Let's Encrypt or a reverse proxy (Traefik, Caddy) in front of the `web` container.

```
[Telegram]         → HTTPS POST /telegram/webhook ──┐
[HTTP sources]     → http_fetcher container  ────────┤
[Future sources]   → (webhook or loop)  ─────────────┴──► [web container: Django + Gunicorn]
                                                               ↕ ./media (bind mount)
[Browser display]  ← GET / + /api/previews ──────────────── [screensaver_app]
                                                               ↕
[Admin user]       ← /admin/ ────────────────────────────── [Django Admin]
```

### Bare metal (alternative)

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
gunicorn screensaverbot.wsgi:application --bind 0.0.0.0:8000 --workers 2
```

Schedule management commands via system cron:
```cron
0 * * * * /path/to/.venv/bin/python /path/to/manage.py run_http_fetcher
0 * * * * /path/to/.venv/bin/python /path/to/manage.py run_cleanup
```

---

## Tech Stack

- Python 3.12 (Docker image) / 3.10+ (bare metal minimum)
- Django 4.x + Gunicorn
- WhiteNoise (static file serving without NGINX)
- Pillow (image processing)
- `requests` (HTTP fetcher)
- Telegram Bot API (webhook mode)
- Vanilla HTML/JS (no frontend framework)
- SQLite (default; swap to PostgreSQL if needed)
- Docker + Docker Compose (deployment)

---

## Code Standards

### Python Version
- **Python 3.10+** minimum (required for modern union type syntax and pattern matching)

### Type Annotations
- **All functions must be fully type-annotated** — parameters and return types
- Use `from __future__ import annotations` at the top of every module
- Use `typing` / `collections.abc` types where needed (`list[str]`, `dict[str, Any]`, `Optional`, etc.)
- No use of bare `dict`, `list`, or `tuple` without type parameters

```python
# correct
def save_image(data: bytes) -> Path:
    ...

# incorrect — no types
def save_image(data):
    ...
```

### Linting — flake8
- All code must pass `flake8` with zero errors before commit
- Max line length: **100** characters
- `.flake8` config at project root:

```ini
[flake8]
max-line-length = 100
exclude = .git,__pycache__,.venv,migrations
```

- Run before committing:
```bash
flake8 .
```
