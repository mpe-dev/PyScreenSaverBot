from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

from django.conf import settings
from PIL import Image

logger = logging.getLogger(__name__)

PREVIEW_MAX_WIDTH = 400


def save_image(data: bytes) -> Path:
    """Write raw image bytes to media/images/ with a timestamp-based filename.

    Returns the Path of the saved file.
    """
    images_dir = Path(settings.MEDIA_ROOT) / "images"
    images_dir.mkdir(parents=True, exist_ok=True)

    filename = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f") + ".jpg"
    dest = images_dir / filename
    dest.write_bytes(data)

    logger.info("Image saved: %s", filename)
    return dest


def generate_preview(source: Path) -> Path:
    """Create a resized preview of *source* in media/previews/.

    Skips generation if the preview already exists on disk.
    Returns the Path of the preview file.
    """
    previews_dir = Path(settings.MEDIA_ROOT) / "previews"
    previews_dir.mkdir(parents=True, exist_ok=True)

    dest = previews_dir / source.name
    if dest.exists():
        return dest

    with Image.open(source) as img:
        img = img.convert("RGB")
        ratio = PREVIEW_MAX_WIDTH / img.width
        new_size = (PREVIEW_MAX_WIDTH, max(1, int(img.height * ratio)))
        thumb = img.resize(new_size, Image.LANCZOS)
        thumb.save(dest, "JPEG", quality=85, optimize=True)

    logger.info("Preview generated: %s", source.name)
    return dest
