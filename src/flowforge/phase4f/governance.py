from dataclasses import dataclass
from hashlib import sha256
from pathlib import PurePath

ALLOWED_EXTENSIONS = {
    ".pdf",
    ".docx",
    ".xlsx",
    ".csv",
    ".txt",
    ".json",
    ".xml",
    ".png",
    ".jpg",
    ".jpeg",
    ".tiff",
    ".eml",
    ".msg",
    ".edi",
    ".zip",
}
MAX_ARCHIVE_BYTES = 100 * 1024 * 1024


@dataclass(frozen=True, slots=True)
class AiAuthorization:
    tenant_id: str
    user_id: str
    permissions: frozenset[str]
    allowed_modules: frozenset[str]
    allowed_record_ids: frozenset[str]


@dataclass(frozen=True, slots=True)
class Citation:
    record_id: str
    module: str
    freshness: str


@dataclass(frozen=True, slots=True)
class GroundedAnswer:
    answer: str
    citations: tuple[Citation, ...]
    calculation_method: str
    limitations: tuple[str, ...]
    proposed_action: str | None = None


def authorize_record(
    context: AiAuthorization, module: str, record_id: str, permission: str = "read"
) -> bool:
    return (
        permission in context.permissions
        and module in context.allowed_modules
        and record_id in context.allowed_record_ids
    )


def validate_upload(filename: str, size_bytes: int) -> str:
    extension = PurePath(filename).suffix.casefold()
    if extension not in ALLOWED_EXTENSIONS:
        raise ValueError("Unsupported file type")
    if size_bytes <= 0 or size_bytes > MAX_ARCHIVE_BYTES:
        raise ValueError("Invalid file size")
    return extension


def digest_content(content: bytes) -> str:
    return sha256(content).hexdigest()


def require_grounding(answer: GroundedAnswer) -> None:
    if not answer.citations:
        raise ValueError("Material AI answer requires citations")
    if any(not citation.record_id for citation in answer.citations):
        raise ValueError("Citation record ID is required")
