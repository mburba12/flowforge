"""Usage-based billing (metering, monthly invoices, automatic card charges) and per-user
screen preferences."""

from fastapi import APIRouter

from .routes import prefs_router
from .routes import router as billing_router

router = APIRouter()
router.include_router(billing_router)
router.include_router(prefs_router)
