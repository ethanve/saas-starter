"""File upload routes."""

from fastapi import APIRouter, HTTPException, UploadFile, status

from app.auth.dependencies import CurrentUser
from app.core.storage import save_upload

router = APIRouter(prefix="/upload", tags=["upload"])

MAX_UPLOAD_SIZE = 100 * 1024 * 1024  # 100MB


@router.post("")
async def upload_file(
    file: UploadFile,
    user: CurrentUser,
) -> dict[str, str]:
    if not file.filename:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "No filename provided")

    content = await file.read()
    if len(content) > MAX_UPLOAD_SIZE:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "File too large")

    key = await save_upload(file.filename, content)
    return {"key": key, "filename": file.filename, "size": len(content)}
