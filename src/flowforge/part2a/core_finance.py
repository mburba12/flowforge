from fastapi import APIRouter

router = APIRouter(prefix="/api/part2a/core", tags=["part2a-core-finance"])


@router.get("/status")
async def status() -> dict[str, str]:
    return {"status": "ready"}
