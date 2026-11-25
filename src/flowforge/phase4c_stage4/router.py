from fastapi import APIRouter

from .catalog import provider_codes
from .routes import router as routes

router = APIRouter()
router.include_router(routes)


@router.get("/phase4c/stage4/status", tags=["phase4c-logistics"])
async def status() -> dict[str, object]:
    return {
        "phase": "4C-stage4",
        "status": "implemented",
        "providers": provider_codes(),
        "production_credentials": False,
        "label_purchase": False,
        "pickup_booking": False,
        "fulfillment_write_back": False,
        "returns_write_back": False,
    }
