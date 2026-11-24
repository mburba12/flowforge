from fastapi import APIRouter

from .routes import router as routes

router = APIRouter()
router.include_router(routes)


@router.get("/phase4b/stage2/status", tags=["phase4b-filing"])
async def status() -> dict[str, object]:
    return {
        "phase": "4B-stage2",
        "status": "implemented",
        "capabilities": [
            "liabilities",
            "returns",
            "approval",
            "remittance",
            "notices",
            "reconciliation",
        ],
    }
