from fastapi import APIRouter

from .routes import router as routes

router = APIRouter()
router.include_router(routes)


@router.get("/phase3a/status", tags=["phase3a"])
async def status() -> dict[str, object]:
    return {
        "phase": "3A",
        "status": "implemented",
        "capabilities": [
            "vendors",
            "purchase_orders",
            "approvals",
            "receiving",
            "vendor_invoices",
            "matching",
            "ap_open_items",
        ],
    }
