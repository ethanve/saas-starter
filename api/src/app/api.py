"""API router aggregation."""

from fastapi import APIRouter

from app.auth.oauth.routes import router as oauth_router
from app.auth.routes import router as auth_router
from app.organization.routes import router as organization_router
from app.upload.routes import router as upload_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth_router)
api_router.include_router(oauth_router)
api_router.include_router(organization_router)
api_router.include_router(upload_router)
