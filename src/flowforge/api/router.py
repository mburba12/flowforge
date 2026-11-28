from fastapi import APIRouter

from flowforge.api.routes import auth, health, platform, tenants, users
from flowforge.bg08_completion.router import router as bg08_completion_router
from flowforge.bg08_final.router import router as bg08_final_router
from flowforge.bg09_final.router import router as bg09_router
from flowforge.bg10_final.router import router as bg10_router
from flowforge.bg11_final.router import router as bg11_router
from flowforge.bg13_ops.router import router as bg13_ops_router
from flowforge.commerce_completion.router import router as commerce_completion_router
from flowforge.commerce_final.router import router as commerce_final_router
from flowforge.control_plane.router import router as control_plane_router
from flowforge.crm_completion.router import router as crm_completion_router
from flowforge.crm_final.router import router as crm_final_router
from flowforge.crm_sales.router import router as crm_sales_router
from flowforge.finance.router import router as finance_router
from flowforge.finance_advanced.router import router as finance_advanced_router
from flowforge.finance_completion.router import router as finance_completion_router
from flowforge.finance_final.router import router as finance_final_router
from flowforge.finance_workflows.router import router as finance_workflows_router
from flowforge.foundation_completion.router import router as foundation_completion_router
from flowforge.foundation_final.router import router as foundation_final_router
from flowforge.master_data.router import router as master_data_router
from flowforge.payroll_tax_completion.router import router as payroll_tax_completion_router
from flowforge.payroll_tax_final.router import router as payroll_tax_final_router
from flowforge.workforce_completion.router import router as workforce_completion_router
from flowforge.workforce_final.router import router as workforce_final_router
from flowforge.workforce_ultimate.router import router as workforce_ultimate_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(platform.router)
api_router.include_router(tenants.router)
api_router.include_router(users.router)
api_router.include_router(control_plane_router)

# Extended domain routers carry their own canonical /api/v2/... prefixes.
extended_router = APIRouter()
extended_router.include_router(master_data_router)
extended_router.include_router(finance_router)
extended_router.include_router(finance_workflows_router)
extended_router.include_router(finance_advanced_router)
extended_router.include_router(finance_completion_router)
extended_router.include_router(finance_final_router)
extended_router.include_router(foundation_completion_router)
extended_router.include_router(foundation_final_router)
extended_router.include_router(crm_sales_router)
extended_router.include_router(crm_final_router)
extended_router.include_router(crm_completion_router)
extended_router.include_router(commerce_final_router)
extended_router.include_router(commerce_completion_router)
extended_router.include_router(workforce_final_router)
extended_router.include_router(workforce_completion_router)
extended_router.include_router(workforce_ultimate_router)
extended_router.include_router(payroll_tax_final_router)
extended_router.include_router(payroll_tax_completion_router)
extended_router.include_router(bg08_final_router)
extended_router.include_router(bg08_completion_router)
extended_router.include_router(bg09_router)
extended_router.include_router(bg10_router)
extended_router.include_router(bg11_router)
extended_router.include_router(bg13_ops_router)
