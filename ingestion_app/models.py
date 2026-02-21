from __future__ import annotations

from django.db import models


class SingletonModel(models.Model):
    """Abstract base that enforces a single database row.

    Subclasses may only ever have one record. Attempting to save a second
    record silently replaces the first. Deletion is blocked.
    """

    class Meta:
        abstract = True

    def save(self, *args: object, **kwargs: object) -> None:
        # Delete every other row before saving so only one row exists.
        self.__class__.objects.exclude(pk=self.pk).delete()
        super().save(*args, **kwargs)

    def delete(self, *args: object, **kwargs: object) -> tuple[int, dict[str, int]]:
        # Prevent deletion of the singleton configuration row.
        return 0, {}


class TelegramSourceConfig(SingletonModel):
    """Configuration for the Telegram Bot ingestion source (singleton)."""

    bot_token = models.CharField(max_length=200, help_text="Telegram Bot API token.")
    chat_id = models.CharField(
        max_length=100,
        help_text="Only updates from this chat/channel ID will be accepted.",
    )
    webhook_url = models.URLField(
        max_length=500,
        help_text="Public HTTPS URL registered with Telegram as the webhook endpoint.",
    )
    enabled = models.BooleanField(
        default=True,
        help_text="Disable to stop processing Telegram updates without deleting config.",
    )

    class Meta:
        verbose_name = "Telegram Source"
        verbose_name_plural = "Telegram Source"

    def __str__(self) -> str:
        return f"Telegram Bot (chat_id={self.chat_id})"


class HttpFetcherSourceConfig(models.Model):
    """Configuration for a single HTTP image-fetching source.

    Multiple records are allowed — one per remote image URL.
    """

    INTERVAL_CHOICES = [
        ("hourly", "Hourly"),
        ("daily", "Daily"),
        ("weekly", "Weekly"),
        ("monthly", "Monthly"),
    ]

    name = models.CharField(
        max_length=200,
        help_text='Friendly label for this source, e.g. "Daily Landscape Cam".',
    )
    url = models.URLField(
        max_length=2000,
        help_text="Direct image URL. The server must return image bytes.",
    )
    fetch_interval = models.CharField(
        max_length=20,
        choices=INTERVAL_CHOICES,
        default="daily",
        help_text="How often to fetch a new image from this URL.",
    )
    enabled = models.BooleanField(default=True)
    last_fetched_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp of the last successful fetch. Updated automatically.",
    )

    class Meta:
        verbose_name = "HTTP Fetcher Source"
        verbose_name_plural = "HTTP Fetcher Sources"

    def __str__(self) -> str:
        return f"{self.name} ({self.url[:60]})"
