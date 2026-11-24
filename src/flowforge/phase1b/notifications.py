from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID, uuid4


class Channel(StrEnum):
    EMAIL = "email"
    SMS = "sms"
    IN_APP = "in_app"


@dataclass(slots=True)
class Preferences:
    email: bool = True
    sms: bool = False
    in_app: bool = True


@dataclass(slots=True)
class Notification:
    id: UUID
    tenant_id: UUID
    user_id: UUID
    channel: Channel
    subject: str
    body: str
    attempts: int = 0
    status: str = "queued"


class NotificationService:
    def create(
        self,
        tenant_id: UUID,
        user_id: UUID,
        channel: Channel,
        subject: str,
        body: str,
        prefs: Preferences,
    ) -> Notification:
        enabled = {
            Channel.EMAIL: prefs.email,
            Channel.SMS: prefs.sms,
            Channel.IN_APP: prefs.in_app,
        }[channel]
        return Notification(
            uuid4(),
            tenant_id,
            user_id,
            channel,
            subject,
            body,
            status="queued" if enabled else "suppressed",
        )

    def delivered(self, n: Notification) -> None:
        n.status = "delivered"

    def failed(self, n: Notification, max_attempts: int = 3) -> None:
        n.attempts += 1
        n.status = "dead" if n.attempts >= max_attempts else "queued"
