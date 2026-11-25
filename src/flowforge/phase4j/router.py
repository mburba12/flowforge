from fastapi import APIRouter

router = APIRouter()


@router.get("/phase4/4j/status", tags=["phase4-4j"])
async def status() -> dict[str, object]:
    return {
        "phase": "4J",
        "status": "implemented",
        "release_candidate": False,
        "final_tag_allowed": False,
        "failure_injection_required": True,
        "production_writes": False,
    }
