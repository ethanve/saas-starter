"""Local file storage service."""

import os
import uuid

from loguru import logger

from app.core.config import settings


def get_upload_dir() -> str:
    upload_dir = settings.upload_dir
    os.makedirs(upload_dir, exist_ok=True)
    return upload_dir


async def save_upload(filename: str, content: bytes) -> str:
    """Save an uploaded file and return its storage key."""
    upload_dir = get_upload_dir()
    file_id = uuid.uuid4().hex
    safe_filename = os.path.basename(filename)
    key = f"{file_id}/{safe_filename}"
    file_path = os.path.join(upload_dir, file_id)
    os.makedirs(file_path, exist_ok=True)

    full_path = os.path.join(file_path, safe_filename)
    with open(full_path, "wb") as f:
        f.write(content)

    logger.info("File saved: {key}", key=key)
    return key


def get_file_path(key: str) -> str:
    """Get the full filesystem path for a storage key."""
    return os.path.join(get_upload_dir(), key)


def file_exists(key: str) -> bool:
    return os.path.exists(get_file_path(key))
