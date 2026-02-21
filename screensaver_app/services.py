from __future__ import annotations

import logging
from pathlib import Path

from django.conf import settings

from .models import CleanupConfig

logger = logging.getLogger(__name__)


def run_cleanup() -> None:
    """Delete the oldest images (and their previews) until the folder is under the limit."""
    config = CleanupConfig.get()
    images_dir = Path(settings.MEDIA_ROOT) / "images"
    previews_dir = Path(settings.MEDIA_ROOT) / "previews"

    if not images_dir.exists():
        logger.info("Cleanup: images directory does not exist yet, nothing to do")
        return

    # Collect all image files; sort ascending = oldest filename first
    files = sorted(f for f in images_dir.iterdir() if f.is_file())
    if not files:
        logger.info("Cleanup: no images found")
        return

    # Snapshot sizes before starting deletions
    sizes: dict[Path, int] = {f: f.stat().st_size for f in files}
    total_bytes = sum(sizes.values())
    limit_bytes = config.max_folder_size_mb * 1024 * 1024

    used_mb = total_bytes / 1024 / 1024
    logger.info(
        "Cleanup: %.1f MB used / %d MB limit", used_mb, config.max_folder_size_mb
    )

    if total_bytes <= limit_bytes:
        logger.info("Cleanup: within limit, no action needed")
        return

    for f in files:
        if total_bytes <= limit_bytes:
            break

        f.unlink()
        total_bytes -= sizes[f]
        logger.info("Deleted image: %s", f.name)

        preview = previews_dir / f.name
        if preview.exists():
            preview.unlink()
            logger.info("Deleted preview: %s", f.name)

    logger.info(
        "Cleanup complete: %.1f MB remaining", total_bytes / 1024 / 1024
    )
