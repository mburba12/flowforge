from dataclasses import dataclass, field
from hashlib import sha256
from pathlib import Path
from uuid import UUID, uuid4


class DocumentError(Exception):
    pass


@dataclass(slots=True)
class DocumentVersion:
    id: UUID
    number: int
    checksum: str
    size: int
    content_type: str
    storage_key: str


@dataclass(slots=True)
class Document:
    id: UUID
    tenant_id: UUID
    filename: str
    versions: list[DocumentVersion] = field(default_factory=list)
    legal_hold: bool = False
    archived: bool = False


class LocalStorage:
    def __init__(self, root: Path):
        self.root = root

    def put(self, tenant_id: UUID, key: str, data: bytes) -> str:
        path = self.root / str(tenant_id) / key
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return str(path)

    def get(self, tenant_id: UUID, key: str) -> bytes:
        return (self.root / str(tenant_id) / key).read_bytes()


class DocumentService:
    def __init__(
        self,
        storage: LocalStorage,
        max_bytes: int = 25 * 1024 * 1024,
        allowed: set[str] | None = None,
    ):
        self.storage = storage
        self.max = max_bytes
        self.allowed = allowed or {
            "application/pdf",
            "text/plain",
            "text/csv",
            "image/png",
            "image/jpeg",
        }

    def upload(
        self,
        tenant_id: UUID,
        filename: str,
        content_type: str,
        data: bytes,
        document: Document | None = None,
    ) -> Document:
        if not data or len(data) > self.max:
            raise DocumentError("Invalid file size")
        if content_type not in self.allowed:
            raise DocumentError("Unsupported content type")
        doc = document or Document(uuid4(), tenant_id, filename)
        if doc.tenant_id != tenant_id:
            raise DocumentError("Tenant mismatch")
        checksum = sha256(data).hexdigest()
        number = len(doc.versions) + 1
        key = f"documents/{doc.id}/v{number}/{filename}"
        self.storage.put(tenant_id, key, data)
        doc.versions.append(
            DocumentVersion(uuid4(), number, checksum, len(data), content_type, key)
        )
        return doc

    def delete(self, doc: Document) -> None:
        if doc.legal_hold:
            raise DocumentError("Legal hold prevents deletion")
        doc.archived = True
