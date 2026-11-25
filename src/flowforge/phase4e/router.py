from fastapi import APIRouter

from .routes import router as reconciliation_routes

router = APIRouter()
router.include_router(reconciliation_routes)


@router.get("/phase4/4e/status", tags=["phase4-4e"])
async def status() -> dict[str, object]:
    return {
        "phase": "4E",
        "status": "implemented",
        "engines": (
            "commerce_to_cash",
            "procure_to_pay",
            "payroll_to_funding",
            "inventory_atp",
        ),
        "source_mutation": False,
        "production_writes": False,
    }
