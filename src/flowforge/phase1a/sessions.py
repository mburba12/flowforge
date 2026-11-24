from dataclasses import dataclass
from datetime import datetime
from uuid import UUID, uuid4

from .clock import utcnow
from .errors import AuthenticationError, TokenReplayError
from .security import digest, opaque_token


@dataclass(slots=True)
class Session:
    id: UUID
    user_id: UUID
    tenant_id: UUID
    refresh_digest: str
    created_at: datetime
    revoked_at: datetime | None = None
    generation: int = 0


class SessionStore:
    def __init__(self) -> None:
        self.items: dict[UUID, Session] = {}

    def create(self, user_id: UUID, tenant_id: UUID) -> tuple[Session, str]:
        raw = opaque_token()
        s = Session(uuid4(), user_id, tenant_id, digest(raw), utcnow())
        self.items[s.id] = s
        return s, raw

    def rotate(self, session_id: UUID, raw: str) -> str:
        s = self.items.get(session_id)
        if s is None or s.revoked_at:
            raise AuthenticationError("Session revoked or missing")
        if s.refresh_digest != digest(raw):
            s.revoked_at = utcnow()
            raise TokenReplayError("Refresh-token replay detected")
        new = opaque_token()
        s.refresh_digest = digest(new)
        s.generation += 1
        return new

    def revoke(self, session_id: UUID) -> None:
        if session_id in self.items:
            self.items[session_id].revoked_at = utcnow()

    def revoke_all(self, user_id: UUID) -> int:
        n = 0
        for s in self.items.values():
            if s.user_id == user_id and s.revoked_at is None:
                s.revoked_at = utcnow()
                n += 1
        return n
