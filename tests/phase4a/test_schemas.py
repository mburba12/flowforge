from datetime import date
from decimal import Decimal

import pytest
from pydantic import ValidationError

from flowforge.phase4a.schemas import CompensationCreate


def test_compensation_dates() -> None:
    with pytest.raises(ValidationError):
        CompensationCreate(
            compensation_type="salary",
            amount=Decimal("50000"),
            currency_code="USD",
            effective_from=date(2026, 2, 1),
            effective_to=date(2026, 1, 1),
        )
