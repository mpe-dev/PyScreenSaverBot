from __future__ import annotations

import logging

import requests

logger = logging.getLogger(__name__)

_TELEGRAM_API = "https://api.telegram.org"


def download_image(file_id: str, bot_token: str) -> bytes:
    """Download a photo from Telegram by file_id and return its raw bytes.

    Raises requests.HTTPError on any non-2xx response.
    """
    # Step 1: resolve file_id → file_path
    get_file_url = f"{_TELEGRAM_API}/bot{bot_token}/getFile"
    resp = requests.get(get_file_url, params={"file_id": file_id}, timeout=10)
    resp.raise_for_status()
    file_path: str = resp.json()["result"]["file_path"]

    # Step 2: download the file bytes
    download_url = f"{_TELEGRAM_API}/file/bot{bot_token}/{file_path}"
    resp = requests.get(download_url, timeout=30)
    resp.raise_for_status()

    logger.info("Downloaded Telegram image: %s (%d bytes)", file_path, len(resp.content))
    return resp.content
