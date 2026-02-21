from __future__ import annotations

import logging
from pathlib import Path

from django.conf import settings

from .models import CleanupConfig

logger = logging.getLogger(__name__)


def run_cleanup() -> None:
    """Delete the oldest images (and their previews) until the folder is under the limit."""
    logger.info("run_cleanup: starting")
    config = CleanupConfig.get()
    images_dir = Path(settings.MEDIA_ROOT) / "images"
    previews_dir = Path(settings.MEDIA_ROOT) / "previews"

    if not images_dir.exists():
        logger.info("run_cleanup: images directory does not exist yet, nothing to do")
        return

    # Collect all image files; sort ascending = oldest filename first
    files = sorted(f for f in images_dir.iterdir() if f.is_file())
    if not files:
        logger.info("run_cleanup: no images found, nothing to do")
        return

    # Snapshot sizes before starting deletions
    sizes: dict[Path, int] = {f: f.stat().st_size for f in files}
    total_bytes = sum(sizes.values())
    limit_bytes = config.max_folder_size_mb * 1024 * 1024

    used_mb = total_bytes / 1024 / 1024
    logger.info("run_cleanup: %d images, %.1f MB used / %d MB limit",
                len(files), used_mb, config.max_folder_size_mb)

    if total_bytes <= limit_bytes:
        logger.info("run_cleanup: within limit, no action needed")
        return

    logger.info("run_cleanup: over limit by %.1f MB, starting deletion",
                (total_bytes - limit_bytes) / 1024 / 1024)

    deleted_images = 0
    deleted_previews = 0

    for f in files:
        if total_bytes <= limit_bytes:
            break

        size_kb = sizes[f] / 1024
        f.unlink()
        total_bytes -= sizes[f]
        deleted_images += 1
        logger.info("Deleted image: %s (%.1f KB)", f.name, size_kb)

        preview = previews_dir / f.name
        if preview.exists():
            preview.unlink()
            deleted_previews += 1
            logger.info("Deleted preview: %s", f.name)

    logger.info(
        "run_cleanup: finished — deleted %d image(s) + %d preview(s), %.1f MB remaining",
        deleted_images, deleted_previews, total_bytes / 1024 / 1024,
    )
