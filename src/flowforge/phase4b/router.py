from fastapi import APIRouter

from .routes import router as routes

router = APIRouter()
router.include_router(routes)


@router.get("/phase4b/status", tags=["phase4b-tax"])
async def status() -> dict[str, object]:
    return {
        "phase": "4B",
        "status": "implemented",
        "capabilities": [
            "jurisdictions",
            "effective_rules",
            "worker_elections",
            "employee_tax",
            "employer_tax",
            "calculation_evidence",
        ],
    }
