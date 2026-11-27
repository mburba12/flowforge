from fastapi import APIRouter

from flowforge.api.routes import auth, health, platform, tenants
from flowforge.finance_final.router import router as finance_final_router
from flowforge.finance_completion.router import router as finance_completion_router
from flowforge.finance_advanced.router import router as finance_advanced_router
from flowforge.finance_workflows.router import router as finance_workflows_router
from flowforge.finance.router import router as finance_router
from flowforge.master_data.router import router as master_data_router
from flowforge.control_plane.router import router as control_plane_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(platform.router)
api_router.include_router(tenants.router)
api_router.include_router(control_plane_router)
api_router.include_router(master_data_router)
api_router.include_router(finance_router)
api_router.include_router(finance_workflows_router)
api_router.include_router(finance_advanced_router)
api_router.include_router(finance_completion_router)
api_router.include_router(finance_final_router)
