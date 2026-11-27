from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/integration-management", tags=["part2b-integrations"])


@router.get("/status")
async def status() -> dict[str, str]:
    return {"status": "ready"}
