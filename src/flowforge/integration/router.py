from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from flowforge.db.session import get_db
from flowforge.phase1a.routes import router as phase1a_router
from flowforge.phase1b.routes import router as phase1b_router

router = APIRouter()
router.include_router(phase1a_router)
router.include_router(phase1b_router)

DatabaseSession = Annotated[AsyncSession, Depends(get_db)]


@router.get("/phase1/status", tags=["phase1"])
async def phase1_status(db: DatabaseSession) -> dict[str, object]:
    await db.execute(text("SELECT 1"))

    return {
        "phase": "1",
        "status": "integrated",
        "database": True,
        "parts": ["1A", "1B"],
    }
