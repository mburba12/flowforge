from fastapi import APIRouter

from .catalog import provider_codes
from .routes import router as routes

router = APIRouter()
router.include_router(routes)


@router.get("/phase4c/stage6/status", tags=["phase4c-workforce"])
async def status() -> dict[str, object]:
    return {
        "phase": "4C-stage6",
        "status": "implemented",
        "providers": provider_codes(),
        "production_credentials": False,
        "payroll_submission": False,
        "direct_deposit_initiation": False,
        "termination_write_back": False,
        "benefit_enrollment_write_back": False,
    }
