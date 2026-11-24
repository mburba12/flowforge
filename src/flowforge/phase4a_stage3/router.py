from fastapi import APIRouter

from .routes import router as routes

router = APIRouter()
router.include_router(routes)


@router.get("/phase4a/stage3/status", tags=["phase4a-payroll"])
async def status() -> dict[str, object]:
    return {
        "phase": "4A-stage3",
        "status": "implemented",
        "capabilities": [
            "gross_to_net",
            "earnings",
            "deductions",
            "employee_taxes",
            "employer_taxes",
            "approval",
            "posting",
            "payments",
            "reconciliation",
        ],
    }
