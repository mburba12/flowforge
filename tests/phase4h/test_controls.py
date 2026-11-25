from datetime import UTC, datetime, timedelta

import pytest

from flowforge.phase4h.controls import (
    ConnectorHealth,
    Health,
    SecretReference,
    assess_health,
)


def test_health() -> None:
    assert assess_health(ConnectorHealth(datetime.now(UTC), True, 0, 0.0)) == Health.HEALTHY


def test_failed_auth() -> None:
    assert assess_health(ConnectorHealth(datetime.now(UTC), False, 0, 0.0)) == Health.FAILED


def test_stale() -> None:
    assert (
        assess_health(ConnectorHealth(datetime.now(UTC) - timedelta(hours=1), True, 0, 0.0))
        == Health.DEGRADED
    )


def test_vault() -> None:
    SecretReference("t", "https://x.vault.azure.net", "s", None).validate()
    with pytest.raises(ValueError):
        SecretReference("t", "file://x", "s", None).validate()
