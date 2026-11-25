from fastapi import APIRouter

from .catalog import provider_codes
from .routes import router as routes

router = APIRouter()
router.include_router(routes)


@router.get("/phase4c/stage3/status", tags=["phase4c-commerce"])
async def status() -> dict[str, object]:
    return {
        "phase": "4C-stage3",
        "status": "implemented",
        "providers": provider_codes(),
        "production_credentials": False,
        "write_back": False,
        "listing_mutations": False,
        "fulfillment_mutations": False,
    }
