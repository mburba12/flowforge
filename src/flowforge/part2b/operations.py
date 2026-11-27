from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/operations", tags=["part2b-operations"])


@router.get("/status")
async def status() -> dict[str, str]:
    return {"status": "ready"}
