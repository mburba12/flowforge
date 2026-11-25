from fastapi import APIRouter

from .routes import router as routes

router = APIRouter()
router.include_router(routes)


@router.get("/phase4c/status", tags=["phase4c-banking"])
async def status() -> dict[str, object]:
    return {
        "phase": "4C-stage1",
        "status": "implemented",
        "capabilities": [
            "link_sessions",
            "token_exchange",
            "connected_accounts",
            "masked_accounts",
            "gl_mapping",
            "balance_snapshots",
            "transaction_sync",
            "manual_import",
        ],
    }
