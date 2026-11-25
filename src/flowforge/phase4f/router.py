from fastapi import APIRouter

from .routes import router as ai_routes

router = APIRouter()
router.include_router(ai_routes)


@router.get("/phase4/4f/status", tags=["phase4-4f"])
async def status() -> dict[str, object]:
    return {
        "phase": "4F",
        "status": "implemented",
        "copilot_grounding": True,
        "citations_required": True,
        "silent_actions": False,
        "production_copilot_configured": False,
        "production_writes": False,
    }
