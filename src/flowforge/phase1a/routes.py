from fastapi import APIRouter

router = APIRouter(prefix="/phase1a", tags=["phase1a"])


@router.get("/status")
async def status() -> dict[str, object]:
    return {
        "phase": "1A",
        "implemented": True,
        "capabilities": [
            "sessions",
            "rbac",
            "tenancy",
            "invitations",
            "mfa-recovery",
            "audit-chain",
            "workflow",
            "outbox",
        ],
    }
