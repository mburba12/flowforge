from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class UnifiedTrackingEvent:
    event_id: str
    status_code: str
    description: str
    occurred_at: str


class LogisticsProvider(Protocol):
    code: str

    async def connect(self, authorization_code: str) -> tuple[str, str]: ...
    async def tracking(
        self, account_id: str, cursor: str | None
    ) -> tuple[list[UnifiedTrackingEvent], str | None]: ...
    async def verify_webhook(self, payload: bytes, signature: str) -> bool: ...
