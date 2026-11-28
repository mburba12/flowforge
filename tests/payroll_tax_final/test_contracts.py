import pytest
from pydantic import ValidationError

from flowforge.payroll_tax_final.schemas import ImportCreate


def test_import_records_nonnegative():
    with pytest.raises(ValidationError):
        ImportCreate(
            provider_code="x",
            source_reference="x",
            period_start="2026-01-01",
            period_end="2026-01-31",
            records=-1,
            idempotency_key="12345678",
        )
