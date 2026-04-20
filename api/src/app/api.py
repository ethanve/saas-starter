"""API router aggregation."""

from fastapi import APIRouter

from app.area.routes import router as area_router
from app.auth.magic_link.routes import router as magic_link_router
from app.auth.routes import router as auth_router
from app.household.routes import router as household_router
from app.project.routes import router as project_router
from app.sync.routes import router as sync_router
from app.task.routes import router as task_router
from app.upload.routes import router as upload_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth_router)
api_router.include_router(magic_link_router)
api_router.include_router(household_router)
api_router.include_router(area_router)
api_router.include_router(project_router)
api_router.include_router(task_router)
api_router.include_router(sync_router)
api_router.include_router(upload_router)
