from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from .governance import validate_upload

router = APIRouter(prefix="/api/v4/ai", tags=["phase4f-ai"])


class UploadInspection(BaseModel):
    filename: str
    size_bytes: int


@router.post("/uploads/inspect")
async def inspect(body: UploadInspection) -> dict[str, object]:
    try:
        extension = validate_upload(body.filename, body.size_bytes)
    except ValueError as error:
        raise HTTPException(422, str(error)) from error
    return {"accepted": True, "extension": extension, "executable_content": False}
