from fastapi import APIRouter

from .catalog import provider_codes
from .routes import router as routes

router = APIRouter()
router.include_router(routes)


@router.get("/phase4c/stage5/status", tags=["phase4c-finance"])
async def status() -> dict[str, object]:
    return {
        "phase": "4C-stage5",
        "status": "implemented",
        "providers": provider_codes(),
        "production_credentials": False,
        "outbound_journal_posting": False,
        "bill_approval": False,
        "payment_initiation": False,
        "treasury_transfer_initiation": False,
    }
