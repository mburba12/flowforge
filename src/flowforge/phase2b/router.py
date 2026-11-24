from fastapi import APIRouter

from .routes import router as routes

router = APIRouter()
router.include_router(routes)


@router.get("/phase2b/status", tags=["phase2b"])
async def status() -> dict[str, object]:
    return {
        "phase": "2B",
        "status": "implemented",
        "capabilities": [
            "currencies",
            "calendars",
            "periods",
            "ledgers",
            "accounts",
            "journals",
            "posting",
            "trial_balance",
        ],
    }
