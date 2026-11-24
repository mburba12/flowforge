from dataclasses import dataclass
from datetime import datetime, timedelta
from uuid import UUID, uuid4

from .clock import utcnow
from .errors import AuthenticationError
from .security import digest, opaque_token


@dataclass(slots=True)
class Invitation:
    id: UUID
    tenant_id: UUID
    email: str
    role: str
    token_digest: str
    expires_at: datetime
    accepted_at: datetime | None = None
    revoked_at: datetime | None = None


class InvitationService:
    def issue(
        self, tenant_id: UUID, email: str, role: str, hours: int = 72
    ) -> tuple[Invitation, str]:
        raw = opaque_token()
        return Invitation(
            uuid4(), tenant_id, email.lower(), role, digest(raw), utcnow() + timedelta(hours=hours)
        ), raw

    def accept(self, i: Invitation, raw: str, email: str) -> None:
        if (
            i.accepted_at
            or i.revoked_at
            or utcnow() >= i.expires_at
            or i.email != email.lower()
            or i.token_digest != digest(raw)
        ):
            raise AuthenticationError("Invitation invalid")
        i.accepted_at = utcnow()
