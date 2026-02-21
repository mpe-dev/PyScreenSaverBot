from __future__ import annotations

import logging

from django.core.management.base import BaseCommand
from django.utils import timezone

from screensaver_app.services import run_cleanup

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Delete oldest images when media/images/ exceeds the configured size limit."

    def handle(self, *args: object, **options: object) -> None:
        logger.info("run_cleanup command started at %s", timezone.now().isoformat())
        run_cleanup()
        logger.info("run_cleanup command finished")
