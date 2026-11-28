"""Uploads: any section can hold files (invoices, receipts, contracts, statements...)."""

import hashlib
import re
from datetime import datetime
from typing import Annotated, Any
from urllib.parse import quote
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Response, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from flowforge.core.config import settings
from flowforge.core.security import Principal, current_principal
from flowforge.db.session import get_tenant_db
from flowforge.platform.services import record_change

from .models import Attachment

router = APIRouter(prefix="/api/v1/files", tags=["files"])
P = Annotated[Principal, Depends(current_principal)]
D = Annotated[AsyncSession, Depends(get_tenant_db)]

# Extension -> content type served on download. Active content (HTML, SVG, scripts) is
# refused so a download can never run in the browser.
ALLOWED: dict[str, str] = {
    "pdf": "application/pdf",
    "png": "image/png",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "gif": "image/gif",
    "webp": "image/webp",
    "heic": "image/heic",
    "tif": "image/tiff",
    "tiff": "image/tiff",
    "csv": "text/csv",
    "txt": "text/plain",
    "ofx": "application/x-ofx",
    "qfx": "application/x-ofx",
    "xml": "application/xml",
    "json": "application/json",
    "xls": "application/vnd.ms-excel",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "doc": "application/msword",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "eml": "message/rfc822",
    "zip": "application/zip",
}
_SIGNATURES = {
    "pdf": (b"%PDF",),
    "png": (b"\x89PNG",),
    "jpg": (b"\xff\xd8\xff",),
    "jpeg": (b"\xff\xd8\xff",),
    "gif": (b"GIF8",),
    "xlsx": (b"PK",),
    "docx": (b"PK",),
    "zip": (b"PK",),
}
_SECTION = re.compile(r"^[a-z0-9][a-z0-9-]{0,59}$")


def file_extension(filename: str) -> str:
    return filename.rsplit(".", 1)[-1].lower() if "." in filename else ""


def check_upload(filename: str, data: bytes) -> str:
    """Validate an uploaded file; returns the content type it is stored and served as."""
    ext = file_extension(filename)
    if ext not in ALLOWED:
        raise ValueError(
            "This file type is not accepted. Upload a PDF, image, spreadsheet, document, "
            "CSV or bank statement (OFX/QFX)."
        )
    if not data:
        raise ValueError("The file is empty")
    if len(data) > settings.upload_max_bytes:
        raise ValueError(f"Files can be at most {settings.upload_max_bytes // (1024 * 1024)} MB")
    signatures = _SIGNATURES.get(ext)
    if signatures and not data.startswith(signatures):
        raise ValueError(f"The file does not look like a .{ext} file")
    return ALLOWED[ext]


def clean_filename(filename: str) -> str:
    name = filename.replace("\\", "/").rsplit("/", 1)[-1].strip()
    name = re.sub(r"[\x00-\x1f\x7f]", "", name)
    return (name or "upload")[:255]


def public(a: Attachment) -> dict[str, Any]:
    return {
        "id": str(a.id),
        "section": a.section,
        "record_type": a.record_type,
        "record_id": a.record_id,
        "filename": a.filename,
        "content_type": a.content_type,
        "size_bytes": a.size_bytes,
        "note": a.note,
        "uploaded_by": str(a.uploaded_by),
        "created_at": a.created_at.isoformat() if isinstance(a.created_at, datetime) else None,
    }


async def store_file(
    db: AsyncSession,
    principal: Principal,
    *,
    section: str,
    filename: str,
    data: bytes,
    record_type: str | None = None,
    record_id: str | None = None,
    note: str | None = None,
) -> Attachment:
    if not _SECTION.match(section):
        raise ValueError("Unknown section")
    filename = clean_filename(filename)
    content_type = check_upload(filename, data)
    attachment = Attachment(
        tenant_id=principal.tenant_id,
        section=section,
        record_type=(record_type or None) and record_type[:60],
        record_id=(record_id or None) and record_id[:100],
        filename=filename,
        content_type=content_type,
        size_bytes=len(data),
        checksum=hashlib.sha256(data).hexdigest(),
        note=(note or None) and note[:500],
        content=data,
        uploaded_by=principal.user_id,
    )
    db.add(attachment)
    await db.flush()
    await record_change(
        db, principal.tenant_id, principal.user_id, "uploaded", "attachment", str(attachment.id)
    )
    return attachment


@router.post("", status_code=201)
async def upload_file(
    db: D,
    p: P,
    file: Annotated[UploadFile, File(description="The file to upload")],
    section: Annotated[str, Form(description="Section the file belongs to, e.g. payables")],
    record_type: Annotated[str | None, Form()] = None,
    record_id: Annotated[str | None, Form()] = None,
    note: Annotated[str | None, Form(max_length=500)] = None,
) -> dict[str, Any]:
    data = await file.read(settings.upload_max_bytes + 1)
    attachment = await store_file(
        db,
        p,
        section=section,
        filename=file.filename or "upload",
        data=data,
        record_type=record_type,
        record_id=record_id,
        note=note,
    )
    await db.commit()
    return public(attachment)


@router.get("")
async def list_files(
    db: D,
    p: P,
    section: str | None = None,
    record_type: str | None = None,
    record_id: str | None = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 200,
) -> list[dict[str, Any]]:
    q = select(Attachment).where(
        Attachment.tenant_id == p.tenant_id, Attachment.is_deleted.is_(False)
    )
    if section:
        q = q.where(Attachment.section == section)
    if record_type:
        q = q.where(Attachment.record_type == record_type)
    if record_id:
        q = q.where(Attachment.record_id == record_id)
    rows = await db.scalars(q.order_by(Attachment.created_at.desc()).limit(limit))
    return [public(a) for a in rows]


async def _get(db: AsyncSession, p: Principal, file_id: UUID) -> Attachment:
    attachment = await db.scalar(
        select(Attachment).where(
            Attachment.id == file_id,
            Attachment.tenant_id == p.tenant_id,
            Attachment.is_deleted.is_(False),
        )
    )
    if attachment is None:
        raise HTTPException(404, "File not found")
    return attachment


@router.get("/{file_id}/content")
async def download_file(db: D, p: P, file_id: UUID) -> Response:
    attachment = await _get(db, p, file_id)
    data = await db.scalar(select(Attachment.content).where(Attachment.id == attachment.id))
    inline = attachment.content_type in ("application/pdf", "image/png", "image/jpeg")
    disposition = "inline" if inline else "attachment"
    return Response(
        content=data or b"",
        media_type=attachment.content_type,
        headers={
            "Content-Disposition": f"{disposition}; filename*=UTF-8''{quote(attachment.filename)}",
            "X-Content-Type-Options": "nosniff",
            "Content-Security-Policy": "default-src 'none'; img-src 'self'",
            "Cache-Control": "private, no-store",
        },
    )


@router.delete("/{file_id}", status_code=204)
async def delete_file(db: D, p: P, file_id: UUID) -> Response:
    attachment = await _get(db, p, file_id)
    attachment.is_deleted = True
    await record_change(db, p.tenant_id, p.user_id, "deleted", "attachment", str(attachment.id))
    await db.commit()
    return Response(status_code=204)
