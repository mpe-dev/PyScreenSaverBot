from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

from django.conf import settings
from PIL import Image

logger = logging.getLogger(__name__)

PREVIEW_MAX_WIDTH = 400


def save_image(data: bytes) -> Path:
    """Decode *data*, convert to JPEG, and write to media/images/.

    Always saves as a real JPEG regardless of the source format (WEBP, PNG,
    GIF, etc.) so the .jpg extension is accurate and browsers can display it.
    Returns the Path of the saved file.
    """
    import io

    images_dir = Path(settings.MEDIA_ROOT) / "images"
    images_dir.mkdir(parents=True, exist_ok=True)

    filename = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f") + ".jpg"
    dest = images_dir / filename

    logger.debug("save_image: decoding %d bytes (source format detection)", len(data))
    with Image.open(io.BytesIO(data)) as img:
        source_format = img.format or "unknown"
        source_size = img.size
        jpeg_img = img.convert("RGB")
        jpeg_img.save(dest, "JPEG", quality=90, optimize=True)

    saved_bytes = dest.stat().st_size
    logger.info("Image saved: %s | source=%s %dx%d | jpeg=%.1f KB",
                filename, source_format, *source_size, saved_bytes / 1024)
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
        logger.debug("generate_preview: skipping %s (preview already exists)", source.name)
        return dest

    logger.debug("generate_preview: opening %s", source.name)
    with Image.open(source) as img:
        img = img.convert("RGB")
        original_size = (img.width, img.height)
        ratio = PREVIEW_MAX_WIDTH / img.width
        new_size = (PREVIEW_MAX_WIDTH, max(1, int(img.height * ratio)))
        logger.debug("generate_preview: resizing %s from %dx%d → %dx%d",
                     source.name, *original_size, *new_size)
        thumb = img.resize(new_size, Image.LANCZOS)
        thumb.save(dest, "JPEG", quality=85, optimize=True)

    logger.info("Preview generated: %s (%dx%d → %dx%d)",
                source.name, *original_size, *new_size)
    return dest
