from __future__ import annotations

from django.contrib import admin
from django.http import HttpRequest
from django.utils.html import format_html

from .models import AppLog, CleanupConfig, ScreensaverConfig

_LEVEL_COLORS: dict[str, str] = {
    "DEBUG": "#888888",
    "INFO": "#2196F3",
    "WARNING": "#FF9800",
    "ERROR": "#f44336",
    "CRITICAL": "#9C27B0",
}


@admin.register(ScreensaverConfig)
class ScreensaverConfigAdmin(admin.ModelAdmin):
    list_display = ("transition", "transition_mode", "slideshow_interval_seconds",
                    "grid_fetch_interval_seconds")
    fieldsets = (
        ("Slideshow", {"fields": ("slideshow_interval_seconds",)}),
        ("Transition", {"fields": ("transition", "transition_mode")}),
        ("Grid refresh", {"fields": ("grid_fetch_interval_seconds",)}),
    )


@admin.register(CleanupConfig)
class CleanupConfigAdmin(admin.ModelAdmin):
    list_display = ("max_folder_size_mb", "cleanup_interval_seconds")


@admin.register(AppLog)
class AppLogAdmin(admin.ModelAdmin):
    list_display = ("timestamp", "colored_level", "logger_name", "message_preview")
    list_filter = ("level", "logger_name")
    search_fields = ("message", "logger_name")
    date_hierarchy = "timestamp"
    readonly_fields = ("timestamp", "level", "logger_name", "message")
    ordering = ("-timestamp",)
    list_per_page = 100

    @admin.display(description="Level", ordering="level")
    def colored_level(self, obj: AppLog) -> str:
        color = _LEVEL_COLORS.get(obj.level, "#888888")
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.level,
        )

    @admin.display(description="Message")
    def message_preview(self, obj: AppLog) -> str:
        return obj.message[:150]

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False

    def has_change_permission(self, request: HttpRequest, obj: object = None) -> bool:
        return False
