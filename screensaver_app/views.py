from __future__ import annotations

import logging
from pathlib import Path

from django.conf import settings
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render

from .models import ScreensaverConfig

logger = logging.getLogger(__name__)

_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}


def index(request: HttpRequest) -> HttpResponse:
    """Serve the fullscreen slideshow page."""
    config = ScreensaverConfig.get()
    return render(request, "screensaver_app/index.html", {
        "grid_fetch_interval_seconds": config.grid_fetch_interval_seconds,
        "slideshow_interval_seconds": config.slideshow_interval_seconds,
        "transition": config.transition,
        "transition_mode": config.transition_mode,
    })


def api_previews(request: HttpRequest) -> JsonResponse:
    """Return a JSON list of all available preview files, sorted chronologically."""
    previews_dir = Path(settings.MEDIA_ROOT) / "previews"
    result: list[dict[str, str]] = []

    if previews_dir.exists():
        for f in sorted(previews_dir.iterdir()):
            if f.is_file() and f.suffix.lower() in _IMAGE_EXTENSIONS:
                result.append({
                    "filename": f.name,
                    "preview_url": f"{settings.MEDIA_URL}previews/{f.name}",
                })

    return JsonResponse(result, safe=False)
