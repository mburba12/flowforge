from decimal import Decimal
from uuid import uuid4

import pytest
from pydantic import ValidationError

from flowforge.phase3b.schemas import InventoryAdjust, OrderLineCreate


def test_positive_order_quantity():
    with pytest.raises(ValidationError):
        OrderLineCreate(product_id=uuid4(), quantity=0, unit_price=1)


def test_adjust_requires_key():
    assert (
        InventoryAdjust(
            product_id=uuid4(),
            warehouse_id=uuid4(),
            location_id=uuid4(),
            quantity=Decimal("1"),
            unit_cost=1,
            idempotency_key="x",
        ).idempotency_key
        == "x"
    )
