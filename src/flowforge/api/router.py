from fastapi import APIRouter

from flowforge.api.routes import auth, health, platform, tenants
from flowforge.control_plane.router import router as control_plane_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(platform.router)
api_router.include_router(tenants.router)
api_router.include_router(control_plane_router)
