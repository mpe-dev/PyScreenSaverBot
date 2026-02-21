from __future__ import annotations

from django.core.management.base import BaseCommand

from screensaver_app.services import run_cleanup


class Command(BaseCommand):
    help = "Delete oldest images when media/images/ exceeds the configured size limit."

    def handle(self, *args: object, **options: object) -> None:
        run_cleanup()
