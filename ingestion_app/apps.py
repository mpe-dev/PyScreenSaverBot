from __future__ import annotations

from django.apps import AppConfig


class IngestionAppConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "ingestion_app"
    verbose_name = "Image Ingestion"
