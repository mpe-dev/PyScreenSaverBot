from __future__ import annotations

import logging
from datetime import timedelta

import requests
from django.utils import timezone

from ingestion_app.models import HttpFetcherSourceConfig

logger = logging.getLogger(__name__)

# Maps the fetch_interval choice value to seconds
INTERVAL_SECONDS: dict[str, int] = {
    "hourly": 3_600,
    "daily": 86_400,
    "weekly": 604_800,
    "monthly": 2_592_000,
}


def fetch_image(url: str) -> bytes:
    """Fetch raw image bytes from *url*.

    Validates that the response Content-Type is an image.
    Raises ValueError or requests.HTTPError on failure.
    """
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()

    content_type = resp.headers.get("Content-Type", "")
    if not content_type.startswith("image/"):
        raise ValueError(
            f"URL did not return an image (Content-Type: {content_type!r})"
        )

    logger.info("Fetched image from %s (%d bytes)", url, len(resp.content))
    return resp.content


def is_due(source: HttpFetcherSourceConfig) -> bool:
    """Return True if *source* has never been fetched or its interval has elapsed."""
    if source.last_fetched_at is None:
        return True

    interval = INTERVAL_SECONDS.get(source.fetch_interval, INTERVAL_SECONDS["daily"])
    return timezone.now() >= source.last_fetched_at + timedelta(seconds=interval)
