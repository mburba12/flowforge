from fastapi import APIRouter

from flowforge.api.routes import auth, health, platform, tenants
from flowforge.payroll_tax_final.router import router as payroll_tax_final_router
from flowforge.workforce_ultimate.router import router as workforce_ultimate_router
from flowforge.workforce_completion.router import router as workforce_completion_router
from flowforge.workforce_final.router import router as workforce_final_router
from flowforge.commerce_completion.router import router as commerce_completion_router
from flowforge.commerce_final.router import router as commerce_final_router
from flowforge.crm_completion.router import router as crm_completion_router
from flowforge.crm_final.router import router as crm_final_router
from flowforge.crm_sales.router import router as crm_sales_router
from flowforge.foundation_final.router import router as foundation_final_router
from flowforge.foundation_completion.router import router as foundation_completion_router
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
api_router.include_router(foundation_completion_router)
api_router.include_router(foundation_final_router)
api_router.include_router(crm_sales_router)
api_router.include_router(crm_final_router)
api_router.include_router(crm_completion_router)
api_router.include_router(commerce_final_router)
api_router.include_router(commerce_completion_router)
api_router.include_router(workforce_final_router)
api_router.include_router(workforce_completion_router)
api_router.include_router(workforce_ultimate_router)
api_router.include_router(payroll_tax_final_router)
