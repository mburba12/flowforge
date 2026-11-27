import pytest
from pydantic import ValidationError

from flowforge.bg08_completion.schemas import AmendmentCreate


def test_amendment_type():
    with pytest.raises(ValidationError):
        AmendmentCreate(amendment_type="x", effective_date="2026-01-01", new_quantity=1)
