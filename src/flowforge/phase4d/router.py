from fastapi import APIRouter

from .routes import router as entity_routes

router = APIRouter()
router.include_router(entity_routes)


@router.get("/phase4/4d/status", tags=["phase4-4d"])
async def status() -> dict[str, object]:
    return {
        "phase": "4D",
        "status": "implemented",
        "table_count": 10,
        "automatic_merge": False,
        "production_writes": False,
    }
