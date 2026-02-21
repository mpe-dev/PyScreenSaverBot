from __future__ import annotations

from django.contrib import admin

from .models import CleanupConfig, ScreensaverConfig


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
