from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import StrEnum


class Health(StrEnum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class ConnectorHealth:
    last_success: datetime | None
    authentication_ok: bool
    webhook_lag_seconds: int
    error_rate: float


def assess_health(
    snapshot: ConnectorHealth, stale_after: timedelta = timedelta(minutes=30)
) -> Health:
    if not snapshot.authentication_ok or snapshot.error_rate >= 0.25:
        return Health.FAILED
    if (
        snapshot.last_success is None
        or datetime.now(UTC) - snapshot.last_success > stale_after
        or snapshot.webhook_lag_seconds > 300
    ):
        return Health.DEGRADED
    return Health.HEALTHY


@dataclass(frozen=True, slots=True)
class SecretReference:
    tenant_id: str
    vault_uri: str
    secret_name: str
    version: str | None

    def validate(self) -> None:
        if not self.vault_uri.startswith("https://") or ".vault.azure.net" not in self.vault_uri:
            raise ValueError("Azure Key Vault URI required")
        if not self.secret_name:
            raise ValueError("Secret name required")
