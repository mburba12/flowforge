from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/copilot-management", tags=["part2b-copilot"])


@router.get("/status")
async def status() -> dict[str, str]:
    return {"status": "ready"}
