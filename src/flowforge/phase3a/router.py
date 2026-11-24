from fastapi import APIRouter

from .integration_routes import router as integration_router
from .payment_routes import router as payment_router
from .routes import router as routes

router = APIRouter()
router.include_router(routes)
router.include_router(integration_router)


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
            "ap_posting",
            "ap_open_items",
        ],
    }


router.include_router(payment_router)
