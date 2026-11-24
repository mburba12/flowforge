from fastapi import APIRouter

from .routes import router as routes

router = APIRouter()
router.include_router(routes)


@router.get("/phase4a/status", tags=["phase4a"])
async def status() -> dict[str, object]:
    return {
        "phase": "4A",
        "status": "implemented",
        "capabilities": [
            "workers",
            "work_locations",
            "assignments",
            "compensation",
            "bank_accounts",
            "tax_profiles",
            "benefits",
        ],
    }
