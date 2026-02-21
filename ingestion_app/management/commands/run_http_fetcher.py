from __future__ import annotations

import logging

from django.core.management.base import BaseCommand
from django.utils import timezone

from ingestion_app.models import HttpFetcherSourceConfig
from ingestion_app.services.http_fetcher import fetch_image, is_due
from ingestion_app.services.pipeline import generate_preview, save_image

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Fetch images from all enabled HTTP sources that are due for a refresh."

    def handle(self, *args: object, **options: object) -> None:
        started_at = timezone.now()
        logger.info("run_http_fetcher started at %s", started_at.isoformat())

        sources = HttpFetcherSourceConfig.objects.filter(enabled=True)
        total = sources.count()
        logger.info("run_http_fetcher: %d enabled source(s) found", total)

        fetched = 0
        skipped = 0
        failed = 0

        for source in sources:
            if not is_due(source):
                logger.info("[%s] not due yet (interval=%s, last_fetched=%s), skipping",
                            source.name, source.fetch_interval, source.last_fetched_at)
                skipped += 1
                continue

            logger.info("[%s] due — fetching %s", source.name, source.url)
            try:
                data = fetch_image(source.url)
                image_path = save_image(data)
                generate_preview(image_path)
                source.last_fetched_at = timezone.now()
                source.save(update_fields=["last_fetched_at"])
                logger.info("[%s] fetch complete: saved %s (%.1f KB)",
                            source.name, image_path.name, len(data) / 1024)
                fetched += 1
            except Exception as exc:
                logger.error("[%s] fetch failed: %s", source.name, exc, exc_info=True)
                failed += 1

        logger.info(
            "run_http_fetcher finished: %d fetched, %d skipped, %d failed (took %.1fs)",
            fetched, skipped, failed,
            (timezone.now() - started_at).total_seconds(),
        )
