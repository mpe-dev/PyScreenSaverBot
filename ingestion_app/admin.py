from __future__ import annotations

from django.contrib import admin

from .models import HttpFetcherSourceConfig, TelegramSourceConfig


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
