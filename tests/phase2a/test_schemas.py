from uuid import uuid4

import pytest
from pydantic import ValidationError

from flowforge.phase2a.schemas import MergeRequest, PaymentTermCreate


def test_merge_distinct() -> None:
    x = uuid4()
    with pytest.raises(ValidationError):
        MergeRequest(source_party_id=x, target_party_id=x, reason="duplicate records")


def test_payment_terms() -> None:
    assert PaymentTermCreate(code="NET30", name="Net 30", due_days=30).due_days == 30
