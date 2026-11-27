from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/administration", tags=["part2b-administration"])


@router.get("/status")
async def status() -> dict[str, str]:
    return {"status": "ready"}
