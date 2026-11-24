from decimal import Decimal
from uuid import uuid4

import pytest
from pydantic import ValidationError

from flowforge.phase3a.schemas import InvoiceCreate, InvoiceLineCreate, POLineCreate


def test_positive_po_quantity():
    with pytest.raises(ValidationError):
        POLineCreate(
            description="x", quantity=Decimal("0"), unit_price=1, expense_account_id=uuid4()
        )


def test_due_date():
    with pytest.raises(ValidationError):
        InvoiceCreate(
            vendor_id=uuid4(),
            invoice_number="1",
            invoice_date="2026-02-01",
            due_date="2026-01-01",
            currency_code="USD",
            lines=[
                InvoiceLineCreate(description="x", quantity=1, unit_price=1, account_id=uuid4())
            ],
        )
