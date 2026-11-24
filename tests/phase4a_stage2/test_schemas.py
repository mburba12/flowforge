from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest
from pydantic import ValidationError

from flowforge.phase4a_stage2.schemas import PayPeriodCreate, TimeEntryCreate


def test_daily_hours_limit() -> None:
    with pytest.raises(ValidationError):
        TimeEntryCreate(
            worker_id=uuid4(),
            work_location_id=uuid4(),
            work_date=date.today(),
            regular_hours=Decimal("20"),
            overtime_hours=Decimal("5"),
        )


def test_pay_date_after_period() -> None:
    with pytest.raises(ValidationError):
        PayPeriodCreate(
            pay_group_id=uuid4(),
            period_code="P1",
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 15),
            pay_date=date(2026, 1, 14),
        )
