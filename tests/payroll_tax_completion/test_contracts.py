import pytest
from pydantic import ValidationError

from flowforge.payroll_tax_completion.schemas import GarnishmentCreate


def test_garnishment_type():
    with pytest.raises(ValidationError):
        GarnishmentCreate(
            worker_id="00000000-0000-0000-0000-000000000001",
            authority="A",
            case_reference="C",
            amount_type="x",
            amount=1,
        )
