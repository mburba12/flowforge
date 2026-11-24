from fastapi import APIRouter

from .routes import router as routes

router = APIRouter()
router.include_router(routes)


@router.get("/phase3b/status", tags=["phase3b"])
async def status() -> dict[str, object]:
    return {
        "phase": "3B",
        "status": "implemented",
        "capabilities": [
            "customers",
            "products",
            "warehouses",
            "inventory",
            "orders",
            "reservations",
            "shipping",
            "cogs",
            "customer_invoices",
            "ar_open_items",
            "receipts",
        ],
    }
