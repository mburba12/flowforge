from decimal import Decimal
from uuid import uuid4

import pytest
from pydantic import ValidationError

from flowforge.phase2b.schemas import JournalCreate, JournalLineCreate


def test_line_requires_one_side() -> None:
    with pytest.raises(ValidationError):
        JournalLineCreate(
            account_id=uuid4(), debit=Decimal("10"), credit=Decimal("10"), currency_code="USD"
        )


def test_journal_must_balance() -> None:
    with pytest.raises(ValidationError):
        JournalCreate(
            ledger_id=uuid4(),
            period_id=uuid4(),
            journal_date="2026-01-01",
            description="bad",
            lines=[
                JournalLineCreate(account_id=uuid4(), debit=Decimal("10"), currency_code="USD"),
                JournalLineCreate(account_id=uuid4(), credit=Decimal("9"), currency_code="USD"),
            ],
        )
