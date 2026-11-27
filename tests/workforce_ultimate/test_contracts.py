import pytest
from pydantic import ValidationError

from flowforge.workforce_ultimate.schemas import ClockCreate


def test_clock_event_type():
    with pytest.raises(ValidationError):
        ClockCreate(
            worker_id="00000000-0000-0000-0000-000000000001",
            event_type="x",
            occurred_at="2026-01-01T00:00:00Z",
            timezone="UTC",
            idempotency_key="12345678",
        )
