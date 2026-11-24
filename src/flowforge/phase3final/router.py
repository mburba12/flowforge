from fastapi import APIRouter

from .routes import router as routes

router = APIRouter()
router.include_router(routes)


@router.get("/phase3/status", tags=["phase3-final"])
async def status() -> dict[str, object]:
    return {
        "phase": "3",
        "status": "integrated",
        "parts": ["3A", "3B"],
        "capabilities": [
            "procure_to_pay",
            "quote_to_cash",
            "inventory",
            "ap",
            "ar",
            "subledger_reconciliation",
        ],
    }
