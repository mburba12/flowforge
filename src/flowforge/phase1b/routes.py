from fastapi import APIRouter

from .operations import HealthService

router = APIRouter(prefix="/phase1b", tags=["phase1b"])


@router.get("/health")
async def health() -> dict[str, object]:
    h = HealthService().readiness(True, True)
    return {"phase": "1B", "status": h.status, "database": h.database, "storage": h.storage}
