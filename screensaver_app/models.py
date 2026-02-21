from __future__ import annotations

from typing import Any

from django.db import models


class SingletonModel(models.Model):
    """Abstract base that enforces a single database row."""

    class Meta:
        abstract = True

    def save(self, *args: Any, **kwargs: Any) -> None:
        self.__class__.objects.exclude(pk=self.pk).delete()
        super().save(*args, **kwargs)

    def delete(self, *args: Any, **kwargs: Any) -> tuple[int, dict[str, int]]:
        return 0, {}

    @classmethod
    def get(cls) -> Any:
        """Return the singleton instance, creating it with defaults if missing."""
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class ScreensaverConfig(SingletonModel):
    """Display and transition settings for the slideshow (singleton)."""

    TRANSITION_CHOICES = [
        ("burn", "Burn"),
        ("fade", "Fade"),
        ("slide", "Slide"),
        ("zoom", "Zoom"),
        ("blur", "Blur"),
        ("flip", "Flip"),
        ("wipe-up", "Wipe Up"),
        ("wipe-down", "Wipe Down"),
        ("iris", "Iris"),
        ("newspaper", "Newspaper"),
        ("glitch", "Glitch"),
        ("squeeze", "Squeeze"),
    ]
    TRANSITION_MODE_CHOICES = [
        ("fixed", "Fixed — always use the selected transition"),
        ("random", "Random — pick a different transition each slide"),
    ]

    grid_fetch_interval_seconds = models.PositiveIntegerField(
        default=60,
        help_text="How often (seconds) the browser re-fetches the preview grid.",
    )
    slideshow_interval_seconds = models.PositiveIntegerField(
        default=5,
        help_text="How long (seconds) each image is displayed before advancing.",
    )
    transition = models.CharField(
        max_length=20,
        choices=TRANSITION_CHOICES,
        default="burn",
        help_text="Transition effect used when transition_mode is 'fixed'.",
    )
    transition_mode = models.CharField(
        max_length=20,
        choices=TRANSITION_MODE_CHOICES,
        default="random",
    )

    class Meta:
        verbose_name = "Screensaver Configuration"
        verbose_name_plural = "Screensaver Configuration"

    def __str__(self) -> str:
        return "Screensaver Configuration"


class CleanupConfig(SingletonModel):
    """Media folder size limits for the automatic cleanup command (singleton)."""

    max_folder_size_mb = models.PositiveIntegerField(
        default=500,
        help_text="Maximum total size of media/images/ in megabytes.",
    )
    cleanup_interval_seconds = models.PositiveIntegerField(
        default=3600,
        help_text="Informational only — actual schedule is set in cron/docker-compose.",
    )

    class Meta:
        verbose_name = "Cleanup Configuration"
        verbose_name_plural = "Cleanup Configuration"

    def __str__(self) -> str:
        return "Cleanup Configuration"


class AppLog(models.Model):
    """Persisted application log entries, written by DatabaseLogHandler."""

    LEVEL_CHOICES = [
        ("DEBUG", "Debug"),
        ("INFO", "Info"),
        ("WARNING", "Warning"),
        ("ERROR", "Error"),
        ("CRITICAL", "Critical"),
    ]

    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    level = models.CharField(max_length=10, choices=LEVEL_CHOICES, db_index=True)
    logger_name = models.CharField(max_length=200, db_index=True)
    message = models.TextField()

    class Meta:
        ordering = ["-timestamp"]
        verbose_name = "Log Entry"
        verbose_name_plural = "Log Entries"

    def __str__(self) -> str:
        return f"[{self.level}] {self.logger_name}: {self.message[:80]}"
