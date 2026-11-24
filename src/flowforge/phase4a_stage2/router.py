from fastapi import APIRouter

from .routes import router as routes

router = APIRouter()
router.include_router(routes)


@router.get("/phase4a/stage2/status", tags=["phase4a-time"])
async def status() -> dict[str, object]:
    return {
        "phase": "4A-stage2",
        "status": "implemented",
        "capabilities": [
            "schedules",
            "time_entries",
            "time_approval",
            "leave",
            "pay_groups",
            "pay_periods",
        ],
    }
