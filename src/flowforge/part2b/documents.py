from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/document-management", tags=["part2b-documents"])


@router.get("/status")
async def status() -> dict[str, str]:
    return {"status": "ready"}
