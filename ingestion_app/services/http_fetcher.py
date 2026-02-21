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
    logger.debug("fetch_image: GET %s", url)
    resp = requests.get(url, timeout=30)
    logger.debug("fetch_image: response status=%d Content-Type=%s",
                 resp.status_code, resp.headers.get("Content-Type", ""))
    resp.raise_for_status()

    content_type = resp.headers.get("Content-Type", "")
    if not content_type.startswith("image/"):
        raise ValueError(
            f"URL did not return an image (Content-Type: {content_type!r})"
        )

    logger.info("Fetched image from %s (%.1f KB, Content-Type: %s)",
                url, len(resp.content) / 1024, content_type)
    return resp.content


def is_due(source: HttpFetcherSourceConfig) -> bool:
    """Return True if *source* has never been fetched or its interval has elapsed."""
    if source.last_fetched_at is None:
        logger.debug("is_due: source=%s has never been fetched → due", source.name)
        return True

    interval = INTERVAL_SECONDS.get(source.fetch_interval, INTERVAL_SECONDS["daily"])
    next_fetch = source.last_fetched_at + timedelta(seconds=interval)
    due = timezone.now() >= next_fetch
    logger.debug("is_due: source=%s interval=%s last_fetched=%s next_fetch=%s due=%s",
                 source.name, source.fetch_interval, source.last_fetched_at, next_fetch, due)
    return due
