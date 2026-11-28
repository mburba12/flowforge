from fastapi import APIRouter

router = APIRouter(prefix="/api/part2a/finance", tags=["part2a-banking-ledger"])


@router.get("/status")
async def status() -> dict[str, str]:
    return {"status": "ready"}
