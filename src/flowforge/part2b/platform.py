from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/platform-services", tags=["part2b-platform"])


@router.get("/status")
async def status() -> dict[str, str]:
    return {"status": "ready"}
