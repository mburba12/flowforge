import pytest
from pydantic import ValidationError

from flowforge.finance_advanced.schemas import AssetCreate, PaymentBatchCreate


def test_invalid_payment_kind():
    with pytest.raises(ValidationError):
        PaymentBatchCreate(
            batch_number="B", kind="real_wire", currency_code="USD", total_amount=1, item_count=1
        )


def test_asset_cost_positive():
    with pytest.raises(ValidationError):
        AssetCreate(
            asset_number="A",
            name="A",
            acquisition_date="2026-01-01",
            cost=0,
            useful_life_periods=12,
        )
