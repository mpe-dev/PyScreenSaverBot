from __future__ import annotations

import logging

from django.contrib import admin, messages
from django.http import HttpRequest

from .models import HttpFetcherSourceConfig, TelegramSourceConfig
from .services.http_fetcher import fetch_image
from .services.pipeline import generate_preview, save_image

logger = logging.getLogger(__name__)


@admin.register(TelegramSourceConfig)
class TelegramSourceConfigAdmin(admin.ModelAdmin):
    list_display = ("chat_id", "webhook_url", "enabled")
    fieldsets = (
        ("Bot credentials", {"fields": ("bot_token", "chat_id")}),
        ("Webhook", {"fields": ("webhook_url",)}),
        ("Status", {"fields": ("enabled",)}),
    )


@admin.register(HttpFetcherSourceConfig)
class HttpFetcherSourceConfigAdmin(admin.ModelAdmin):
    list_display = ("name", "url", "fetch_interval", "enabled", "last_fetched_at")
    list_filter = ("fetch_interval", "enabled")
    readonly_fields = ("last_fetched_at",)
    fieldsets = (
        ("Source", {"fields": ("name", "url")}),
        ("Schedule", {"fields": ("fetch_interval", "enabled")}),
        ("State", {"fields": ("last_fetched_at",)}),
    )

    def save_model(self, request: HttpRequest, obj: HttpFetcherSourceConfig,
                   form: object, change: bool) -> None:
        """On create or URL change: immediately test-fetch the endpoint."""
        super().save_model(request, obj, form, change)

        url_changed = not change or "url" in getattr(form, "changed_data", [])
        if not url_changed:
            return

        action = "Updated" if change else "Added"
        logger.info("%s HTTP source '%s' — testing endpoint: %s", action, obj.name, obj.url)

        try:
            data = fetch_image(obj.url)
            image_path = save_image(data)
            generate_preview(image_path)
            msg = (f"Endpoint test succeeded for '{obj.name}': "
                   f"fetched {len(data) / 1024:.1f} KB → saved {image_path.name}")
            logger.info(msg)
            self.message_user(request, msg, messages.SUCCESS)
        except Exception as exc:
            msg = f"Endpoint test failed for '{obj.name}' ({obj.url}): {exc}"
            logger.error(msg, exc_info=True)
            self.message_user(request, msg, messages.ERROR)
