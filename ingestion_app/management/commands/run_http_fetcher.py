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
        sources = HttpFetcherSourceConfig.objects.filter(enabled=True)
        logger.info("run_http_fetcher: checking %d source(s)", sources.count())

        for source in sources:
            if not is_due(source):
                logger.info("[%s] not due yet, skipping", source.name)
                continue

            logger.info("[%s] fetching %s", source.name, source.url)
            try:
                data = fetch_image(source.url)
                image_path = save_image(data)
                generate_preview(image_path)
                source.last_fetched_at = timezone.now()
                source.save(update_fields=["last_fetched_at"])
                logger.info("[%s] saved: %s", source.name, image_path.name)
            except Exception as exc:
                logger.error("[%s] failed: %s", source.name, exc)
