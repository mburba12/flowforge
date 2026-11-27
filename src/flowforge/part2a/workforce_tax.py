from fastapi import APIRouter

router = APIRouter(prefix="/api/part2a/workforce", tags=["part2a-workforce-tax"])


@router.get("/status")
async def status() -> dict[str, str]:
    return {"status": "ready"}
