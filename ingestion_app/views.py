from __future__ import annotations

import json
import logging

from django.http import HttpRequest, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .models import TelegramSourceConfig
from .services.pipeline import generate_preview, save_image
from .services.telegram import download_image

logger = logging.getLogger(__name__)


@csrf_exempt
@require_POST
def telegram_webhook(request: HttpRequest) -> JsonResponse:
    """Receive a Telegram update, validate it, and save any photo to disk."""
    logger.debug("Telegram webhook received: %d bytes from %s",
                 len(request.body), request.META.get("REMOTE_ADDR", "?"))

    try:
        body: dict = json.loads(request.body)
    except json.JSONDecodeError:
        logger.warning("Telegram webhook received invalid JSON body")
        return JsonResponse({"error": "invalid JSON"}, status=400)

    try:
        config = TelegramSourceConfig.objects.get()
    except TelegramSourceConfig.DoesNotExist:
        logger.error("TelegramSourceConfig is not configured in admin")
        return JsonResponse({"error": "not configured"}, status=500)

    if not config.enabled:
        logger.debug("Telegram source is disabled, ignoring update")
        return JsonResponse({"ok": True})

    # Support both private messages and channel posts
    message: dict = body.get("message") or body.get("channel_post") or {}
    if not message:
        logger.debug("Telegram update contains no message/channel_post, ignoring")
        return JsonResponse({"ok": True})

    # Validate originating chat
    chat_id = str(message.get("chat", {}).get("id", ""))
    if chat_id != config.chat_id:
        logger.warning("Rejected Telegram update from unexpected chat_id=%s (expected %s)",
                       chat_id, config.chat_id)
        return JsonResponse({"ok": True})

    photos: list[dict] = message.get("photo", [])
    if not photos:
        logger.debug("Telegram message from chat_id=%s has no photos, ignoring", chat_id)
        return JsonResponse({"ok": True})

    # Telegram provides multiple resolutions; pick the largest
    best = max(photos, key=lambda p: p.get("file_size", 0))
    file_id: str = best["file_id"]
    logger.debug("Processing photo: file_id=%s file_size=%s",
                 file_id, best.get("file_size", "?"))

    try:
        data = download_image(file_id, config.bot_token)
        image_path = save_image(data)
        generate_preview(image_path)
        logger.info("Telegram image saved successfully: %s (%d bytes)",
                    image_path.name, len(data))
    except Exception as exc:
        logger.error("Failed to process Telegram image file_id=%s: %s",
                     file_id, exc, exc_info=True)
        return JsonResponse({"error": str(exc)}, status=500)

    return JsonResponse({"ok": True})
