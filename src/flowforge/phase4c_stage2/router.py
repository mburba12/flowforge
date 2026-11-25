from fastapi import APIRouter

from .routes import router as routes

router = APIRouter()
router.include_router(routes)


@router.get("/phase4c/stage2/status", tags=["phase4c-payments"])
async def status() -> dict[str, object]:
    return {
        "phase": "4C-stage2",
        "status": "implemented",
        "providers": ["stripe_sandbox", "square_sandbox"],
        "production_credentials": False,
        "money_movement": False,
    }
