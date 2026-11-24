from fastapi import APIRouter

from .routes import router as phase2a_router

router = APIRouter()
router.include_router(phase2a_router)


@router.get("/phase2a/status", tags=["phase2a"])
async def status() -> dict[str, object]:
    return {
        "phase": "2A",
        "status": "implemented",
        "domains": [
            "parties",
            "organizations",
            "people",
            "roles",
            "contacts",
            "addresses",
            "identifiers",
            "relationships",
            "payment_terms",
            "organization_units",
            "duplicates",
            "merges",
        ],
    }
