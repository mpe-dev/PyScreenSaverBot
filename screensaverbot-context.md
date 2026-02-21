# Telegram Image → Web Screensaver System
## Complete Technical Overview (Static Web Version)

---

# 1. Purpose

A self-hosted system that:

1. Receives images from a Telegram channel.
2. Stores them locally with sequential numbering.
3. Generates low-resolution previews (buffered).
4. Displays them via a static webpage slideshow.
5. Automatically deletes oldest images when storage exceeds a defined limit.
6. Uses centralized JSON configuration.
7. Logs all activity to a local log file.

Runs on:
- NAS
- Mini PC
- Small server
- Optional Docker container

No separate client application required.
The display device simply opens a fullscreen browser to the hosted webpage.

---

# 2. High-Level Architecture

## Components

### 1. FastAPI Backend
Responsibilities:
- Telegram webhook receiver
- Image storage
- Preview generation
- API for image metadata
- Static file hosting (HTML + JS)
- Background cleanup service
- Centralized logging
- Config loader (JSON)

### 2. Telegram Bot
- Created via BotFather
- Uses webhook (recommended)
- Sends image messages to backend endpoint
- Backend downloads highest resolution photo

### 3. Static Web Page (Frontend)
- Single HTML page
- Vanilla JavaScript (no heavy framework required)
- Runs fullscreen in browser
- Fetches images asynchronously from API
- Displays:
  - Phase 1: Preview collage
  - Phase 2: Full-resolution slideshow

---

# 3. System Flow

1. User sends image to Telegram channel.
2. Telegram sends webhook to:
   `/telegram/webhook`
3. Backend:
   - Validates message
   - Extracts photo
   - Downloads image
   - Saves sequentially
   - Generates preview
   - Logs event
4. Static webpage:
   - Fetches preview list
   - Shows collage
   - Loads full images
   - Runs slideshow
5. Cleanup service:
   - Checks folder size
   - Deletes oldest files if needed

---

# 4. Image Storage Strategy

## Folder Structure


/images → Full resolution images
/previews → Resized preview images
/logs → Log files
/config.json → Configuration


## Naming Convention

Sequential numeric filenames:


000001.jpg
000002.jpg
000003.jpg


On startup:
- Scan `/images`
- Determine highest number
- Continue incrementing

Benefits:
- Simple ordering
- Easy cleanup
- No filename collisions

---

# 5. Preview Buffer System

- Implemented using Pillow
- Generated once per image
- Stored on disk in `/previews`
- Reduced resolution (e.g., max width 400px)
- Never regenerated unless missing

Advantages:
- Low memory usage
- Low CPU usage
- Fast collage loading
- Async serving

---

# 6. API Design (FastAPI)

## Telegram Endpoint


POST /telegram/webhook


Handles:
- Message validation
- Photo detection
- Image download
- Sequential save
- Preview generation
- Logging

---

## Image APIs

### Get Preview List

GET /api/previews


Returns:
json
[
  { "filename": "000123.jpg", "preview_url": "/previews/000123.jpg" }
]

Get Full Image
GET /images/{filename}

Served as static file.

Auto-Generated Docs

FastAPI provides:

/docs

OpenAPI interactive documentation.

7. Static Webpage Behavior
Phase 1 – Collage Mode

Fetch preview list

Render grid

Low memory usage

Async loading

Phase 2 – Slideshow Mode

Iterate selected images

Load full-resolution image

Apply transition effect

Loop continuously

Runs fullscreen on display device.

8. Transition Effects

Configurable transitions:

burn (default)

fade

slide

zoom

random

Controlled by config file.

9. Folder Cleanup Service

Background async task.

Behavior

Runs every cleanup_interval_seconds

Calculates total folder size

If exceeds max_folder_size_mb:

Sort files by oldest

Delete oldest first

Log deletions

Prevents disk overflow automatically.

10. JSON Configuration File

Single centralized config file.

Example
{
  "folder_cleanup": {
    "max_folder_size_mb": 500,
    "cleanup_interval_seconds": 3600,
    "folder_path": "./images",
    "preview_folder_path": "./previews"
  },
  "telegram": {
    "bot_token": "YOUR_TELEGRAM_BOT_TOKEN",
    "chat_id": "YOUR_CHANNEL_CHAT_ID",
    "use_webhook": true,
    "webhook_url": "https://yourdomain.com/telegram/webhook"
  },
  "screensaver": {
    "grid_fetch_interval_seconds": 60,
    "slideshow_interval_seconds": 5,
    "transition": "burn",
    "transition_mode": "random",
    "available_transitions": ["burn", "fade", "zoom", "slide"]
  },
  "logging": {
    "log_file": "./logs/app.log",
    "log_level": "INFO"
  }
}

All modules read from this file at startup.

11. Logging System

Centralized logging module using Python logging.

Features

File-based logging

Configurable log level

Used across:

Telegram handler

Cleanup service

Preview generator

API routes

Example log output:

INFO  Image saved: 000123.jpg
INFO  Preview generated: 000123.jpg
WARNING Folder size exceeded. Deleting 000001.jpg
ERROR Failed to download Telegram image
12. Async & Performance Strategy

Async FastAPI endpoints

Async webhook handling

Async cleanup task

Static file serving

Preview buffering

No in-memory image storage

Optimized for:

Low CPU

Low RAM

Long-term unattended operation

13. Deployment Options

Direct Python + Uvicorn

Docker container

Reverse proxy (NGINX optional)

HTTPS required for Telegram webhook

Display device:

Open browser

Navigate to hosted URL

Enable fullscreen

Auto-refresh if desired

14. Final Result

A modular, configurable, self-hosted system that:

Ingests images from Telegram

Buffers previews

Displays slideshow in browser

Cleans up automatically

Logs all operations

Can be fully rebuilt from this document

Minimal dependencies.
No heavy frontend framework required.
Designed for stability and long-term unattended use